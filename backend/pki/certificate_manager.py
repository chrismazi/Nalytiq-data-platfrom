"""
Certificate Manager Module

High-level certificate management operations:
- Certificate storage and retrieval
- Certificate status tracking
- Certificate renewal
- Integration with database
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import json

from .certificate_authority import CertificateAuthority, get_certificate_authority

logger = logging.getLogger(__name__)


class CertificateManager:
    """
    Manages certificates for X-Road organizations.
    
    Provides:
    - Certificate lifecycle management
    - Database integration for certificate records
    - Certificate status tracking
    - Expiration monitoring
    """
    
    # Certificate database file (will be replaced with proper DB in production)
    CERT_DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'certificates', 'cert_registry.json')
    
    def __init__(self, ca: CertificateAuthority = None):
        """Initialize Certificate Manager"""
        self.ca = ca or get_certificate_authority()
        self._cert_registry: Dict[str, Dict] = {}
        self._load_registry()
        logger.info("CertificateManager initialized")
    
    def _load_registry(self):
        """Load certificate registry from file"""
        if os.path.exists(self.CERT_DB_FILE):
            try:
                with open(self.CERT_DB_FILE, 'r') as f:
                    self._cert_registry = json.load(f)
                logger.info(f"Loaded {len(self._cert_registry)} certificates from registry")
            except Exception as e:
                logger.warning(f"Failed to load certificate registry: {e}")
                self._cert_registry = {}
        else:
            self._cert_registry = {}
    
    def _save_registry(self):
        """Save certificate registry to file"""
        try:
            os.makedirs(os.path.dirname(self.CERT_DB_FILE), exist_ok=True)
            with open(self.CERT_DB_FILE, 'w') as f:
                json.dump(self._cert_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save certificate registry: {e}")
    
    def request_certificate(
        self,
        organization_id: str,
        organization_code: str,
        organization_name: str,
        certificate_type: str = "signing",
        validity_days: int = None
    ) -> Dict:
        """
        Request a new certificate for an organization.
        
        Args:
            organization_id: Database ID of the organization
            organization_code: Organization code (e.g., RW-GOV-NISR)
            organization_name: Full organization name
            certificate_type: Type of certificate (signing, auth, tls)
            validity_days: Custom validity period
            
        Returns:
            Certificate details including PEM content
        """
        logger.info(f"Processing certificate request for {organization_code}")
        
        # Issue certificate based on type
        if certificate_type == "signing":
            cert_data = self.ca.issue_signing_certificate(
                org_code=organization_code,
                org_name=organization_name,
                validity_days=validity_days
            )
        elif certificate_type == "auth":
            cert_data = self.ca.issue_authentication_certificate(
                org_code=organization_code,
                org_name=organization_name,
                validity_days=validity_days
            )
        else:
            cert_data = self.ca.issue_organization_certificate(
                org_code=organization_code,
                org_name=organization_name,
                common_name=f"{organization_code} {certificate_type.upper()} Certificate",
                validity_days=validity_days
            )
        
        # Create registry entry
        registry_entry = {
            "id": cert_data["id"],
            "organization_id": organization_id,
            "organization_code": organization_code,
            "organization_name": organization_name,
            "certificate_type": certificate_type,
            "serial_number": cert_data["serial_number"],
            "subject": cert_data["subject"],
            "issuer": cert_data["issuer"],
            "valid_from": cert_data["valid_from"],
            "valid_until": cert_data["valid_until"],
            "fingerprint": cert_data["fingerprint"],
            "certificate_path": cert_data["certificate_path"],
            "private_key_path": cert_data["private_key_path"],
            "status": "active",
            "issued_at": datetime.utcnow().isoformat(),
            "revoked_at": None,
            "revocation_reason": None
        }
        
        # Store in registry
        self._cert_registry[cert_data["id"]] = registry_entry
        self._save_registry()
        
        # Return certificate data (including PEM for initial download)
        return {
            **registry_entry,
            "certificate_pem": cert_data["certificate_pem"],
            "private_key_pem": cert_data["private_key_pem"],
            "public_key_pem": cert_data["public_key_pem"]
        }
    
    def get_certificate(self, certificate_id: str) -> Optional[Dict]:
        """Get certificate by ID"""
        entry = self._cert_registry.get(certificate_id)
        if entry:
            # Load PEM content
            try:
                with open(entry["certificate_path"], 'r') as f:
                    entry["certificate_pem"] = f.read()
            except Exception:
                entry["certificate_pem"] = None
        return entry
    
    def get_organization_certificates(
        self, 
        organization_id: str = None,
        organization_code: str = None,
        status: str = None
    ) -> List[Dict]:
        """
        Get all certificates for an organization.
        
        Args:
            organization_id: Filter by organization ID
            organization_code: Filter by organization code
            status: Filter by status (active, revoked, expired)
            
        Returns:
            List of certificate entries
        """
        results = []
        
        for cert_id, entry in self._cert_registry.items():
            # Apply filters
            if organization_id and entry.get("organization_id") != organization_id:
                continue
            if organization_code and entry.get("organization_code") != organization_code:
                continue
            if status and entry.get("status") != status:
                continue
            
            # Check for expiration
            valid_until = datetime.fromisoformat(entry["valid_until"])
            if valid_until < datetime.utcnow() and entry["status"] == "active":
                entry["status"] = "expired"
                self._cert_registry[cert_id] = entry
            
            results.append(entry)
        
        return results
    
    def revoke_certificate(
        self, 
        certificate_id: str, 
        reason: str = "unspecified"
    ) -> bool:
        """
        Revoke a certificate.
        
        Args:
            certificate_id: ID of certificate to revoke
            reason: Reason for revocation
            
        Returns:
            True if revoked, False if not found
        """
        if certificate_id not in self._cert_registry:
            return False
        
        entry = self._cert_registry[certificate_id]
        entry["status"] = "revoked"
        entry["revoked_at"] = datetime.utcnow().isoformat()
        entry["revocation_reason"] = reason
        
        self._cert_registry[certificate_id] = entry
        self._save_registry()
        
        logger.info(f"Certificate {certificate_id} revoked: {reason}")
        return True
    
    def validate_certificate(self, certificate_pem: str) -> Dict:
        """
        Validate a certificate.
        
        Args:
            certificate_pem: PEM-encoded certificate
            
        Returns:
            Validation result
        """
        return self.ca.validate_certificate(certificate_pem)
    
    def get_expiring_certificates(self, days: int = 30) -> List[Dict]:
        """
        Get certificates expiring within specified days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of expiring certificates
        """
        expiring = []
        threshold = datetime.utcnow() + timedelta(days=days)
        
        for cert_id, entry in self._cert_registry.items():
            if entry.get("status") != "active":
                continue
            
            valid_until = datetime.fromisoformat(entry["valid_until"])
            if valid_until <= threshold:
                days_remaining = (valid_until - datetime.utcnow()).days
                entry["days_remaining"] = days_remaining
                expiring.append(entry)
        
        return sorted(expiring, key=lambda x: x["days_remaining"])
    
    def renew_certificate(
        self, 
        certificate_id: str,
        validity_days: int = None
    ) -> Optional[Dict]:
        """
        Renew a certificate by issuing a new one.
        
        Args:
            certificate_id: ID of certificate to renew
            validity_days: Validity period for new certificate
            
        Returns:
            New certificate data or None if not found
        """
        old_entry = self._cert_registry.get(certificate_id)
        if not old_entry:
            return None
        
        # Issue new certificate
        new_cert = self.request_certificate(
            organization_id=old_entry["organization_id"],
            organization_code=old_entry["organization_code"],
            organization_name=old_entry["organization_name"],
            certificate_type=old_entry["certificate_type"],
            validity_days=validity_days
        )
        
        # Mark old certificate as superseded
        old_entry["status"] = "superseded"
        old_entry["superseded_by"] = new_cert["id"]
        self._cert_registry[certificate_id] = old_entry
        self._save_registry()
        
        logger.info(f"Certificate {certificate_id} renewed -> {new_cert['id']}")
        return new_cert
    
    def get_certificate_stats(self) -> Dict:
        """Get statistics about certificates"""
        stats = {
            "total": len(self._cert_registry),
            "active": 0,
            "revoked": 0,
            "expired": 0,
            "by_type": {},
            "by_organization": {}
        }
        
        for entry in self._cert_registry.values():
            # Status counts
            status = entry.get("status", "unknown")
            if status in stats:
                stats[status] += 1
            
            # By type
            cert_type = entry.get("certificate_type", "unknown")
            stats["by_type"][cert_type] = stats["by_type"].get(cert_type, 0) + 1
            
            # By organization
            org_code = entry.get("organization_code", "unknown")
            stats["by_organization"][org_code] = stats["by_organization"].get(org_code, 0) + 1
        
        return stats


# Singleton instance
_certificate_manager: Optional[CertificateManager] = None


def get_certificate_manager() -> CertificateManager:
    """Get the global CertificateManager instance"""
    global _certificate_manager
    if _certificate_manager is None:
        _certificate_manager = CertificateManager()
    return _certificate_manager
