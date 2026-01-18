"""
Access Rights Manager Module

Manages service access rights between organizations:
- Access right grants
- Access validation
- Access revocation
- Access matrix visualization
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from xroad.models import AccessType

logger = logging.getLogger(__name__)


class AccessRightsManager:
    """
    Manages access rights for X-Road services.
    
    Controls which organizations can access which services.
    """
    
    RIGHTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'access_rights.json')
    
    def __init__(self):
        """Initialize access rights manager"""
        self._access_rights: Dict[str, Dict] = {}
        self._load_data()
        logger.info("AccessRightsManager initialized")
    
    def _load_data(self):
        """Load access rights from file"""
        os.makedirs(os.path.dirname(self.RIGHTS_FILE), exist_ok=True)
        
        if os.path.exists(self.RIGHTS_FILE):
            try:
                with open(self.RIGHTS_FILE, 'r') as f:
                    self._access_rights = json.load(f)
                logger.info(f"Loaded {len(self._access_rights)} access rights")
            except Exception as e:
                logger.warning(f"Failed to load access rights: {e}")
    
    def _save_data(self):
        """Save access rights to file"""
        try:
            with open(self.RIGHTS_FILE, 'w') as f:
                json.dump(self._access_rights, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save access rights: {e}")
    
    def grant_access(
        self,
        service_id: str,
        service_code: str,
        provider_org_code: str,
        client_subsystem_id: str,
        client_org_code: str,
        client_subsystem_code: str,
        granted_by: str,
        expires_at: datetime = None,
        access_type: AccessType = AccessType.ALLOW
    ) -> Dict:
        """
        Grant access to a service.
        
        Args:
            service_id: Service being accessed
            service_code: Service code (for reference)
            provider_org_code: Provider organization code
            client_subsystem_id: Client subsystem ID
            client_org_code: Client organization code
            client_subsystem_code: Client subsystem code
            granted_by: User granting access
            expires_at: Optional expiration date
            access_type: Allow or deny
            
        Returns:
            Access right record
        """
        # Check for existing access right
        for ar in self._access_rights.values():
            if (ar["service_id"] == service_id and 
                ar["client_subsystem_id"] == client_subsystem_id):
                # Update existing
                ar["access_type"] = access_type.value
                ar["expires_at"] = expires_at.isoformat() if expires_at else None
                ar["updated_at"] = datetime.utcnow().isoformat()
                ar["granted_by"] = granted_by
                self._save_data()
                
                logger.info(f"Access right updated: {client_org_code}/{client_subsystem_code} -> {service_code}")
                return ar
        
        # Create new access right
        ar_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        access_right = {
            "id": ar_id,
            "service_id": service_id,
            "service_code": service_code,
            "provider_org_code": provider_org_code,
            "client_subsystem_id": client_subsystem_id,
            "client_org_code": client_org_code,
            "client_subsystem_code": client_subsystem_code,
            "access_type": access_type.value,
            "granted_at": now.isoformat(),
            "granted_by": granted_by,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "updated_at": now.isoformat()
        }
        
        self._access_rights[ar_id] = access_right
        self._save_data()
        
        logger.info(f"Access granted: {client_org_code}/{client_subsystem_code} -> {service_code}")
        return access_right
    
    def revoke_access(self, access_right_id: str) -> bool:
        """
        Revoke an access right.
        
        Args:
            access_right_id: ID of access right to revoke
            
        Returns:
            True if revoked, False if not found
        """
        if access_right_id not in self._access_rights:
            return False
        
        ar = self._access_rights[access_right_id]
        del self._access_rights[access_right_id]
        self._save_data()
        
        logger.info(f"Access revoked: {ar['client_org_code']}/{ar['client_subsystem_code']} -> {ar['service_code']}")
        return True
    
    def check_access(
        self,
        service_id: str,
        client_subsystem_id: str
    ) -> Dict:
        """
        Check if a client has access to a service.
        
        Args:
            service_id: Service ID
            client_subsystem_id: Client subsystem ID
            
        Returns:
            Access check result with allowed/denied and details
        """
        now = datetime.utcnow()
        
        for ar in self._access_rights.values():
            if (ar["service_id"] == service_id and 
                ar["client_subsystem_id"] == client_subsystem_id):
                
                # Check expiration
                if ar["expires_at"]:
                    expires = datetime.fromisoformat(ar["expires_at"])
                    if expires < now:
                        return {
                            "allowed": False,
                            "reason": "access_expired",
                            "expired_at": ar["expires_at"]
                        }
                
                # Check access type
                if ar["access_type"] == AccessType.DENY.value:
                    return {
                        "allowed": False,
                        "reason": "explicitly_denied"
                    }
                
                return {
                    "allowed": True,
                    "access_right_id": ar["id"],
                    "granted_at": ar["granted_at"],
                    "expires_at": ar["expires_at"]
                }
        
        # No access right found
        return {
            "allowed": False,
            "reason": "no_access_right"
        }
    
    def get_service_access_rights(self, service_id: str) -> List[Dict]:
        """
        Get all access rights for a service.
        
        Args:
            service_id: Service ID
            
        Returns:
            List of access rights for the service
        """
        return [ar for ar in self._access_rights.values() if ar["service_id"] == service_id]
    
    def get_client_access_rights(self, client_subsystem_id: str) -> List[Dict]:
        """
        Get all access rights for a client subsystem.
        
        Args:
            client_subsystem_id: Client subsystem ID
            
        Returns:
            List of access rights for the client
        """
        return [ar for ar in self._access_rights.values() if ar["client_subsystem_id"] == client_subsystem_id]
    
    def get_organization_access_matrix(self, organization_code: str) -> Dict:
        """
        Get access matrix for an organization.
        
        Shows which of the organization's services are accessible by whom,
        and which services the organization has access to.
        
        Args:
            organization_code: Organization code
            
        Returns:
            Access matrix with provided and consumed services
        """
        matrix = {
            "organization_code": organization_code,
            "services_provided": [],  # Services this org provides access to
            "services_consumed": []   # Services this org has access to
        }
        
        for ar in self._access_rights.values():
            if ar["provider_org_code"] == organization_code:
                matrix["services_provided"].append({
                    "service_code": ar["service_code"],
                    "client_org": ar["client_org_code"],
                    "client_subsystem": ar["client_subsystem_code"],
                    "access_type": ar["access_type"],
                    "expires_at": ar["expires_at"]
                })
            
            if ar["client_org_code"] == organization_code:
                matrix["services_consumed"].append({
                    "service_code": ar["service_code"],
                    "provider_org": ar["provider_org_code"],
                    "access_type": ar["access_type"],
                    "expires_at": ar["expires_at"]
                })
        
        return matrix
    
    def cleanup_expired(self) -> int:
        """
        Remove expired access rights.
        
        Returns:
            Number of expired rights removed
        """
        now = datetime.utcnow()
        expired_ids = []
        
        for ar_id, ar in self._access_rights.items():
            if ar["expires_at"]:
                expires = datetime.fromisoformat(ar["expires_at"])
                if expires < now:
                    expired_ids.append(ar_id)
        
        for ar_id in expired_ids:
            del self._access_rights[ar_id]
        
        if expired_ids:
            self._save_data()
            logger.info(f"Cleaned up {len(expired_ids)} expired access rights")
        
        return len(expired_ids)
    
    def get_statistics(self) -> Dict:
        """Get access rights statistics"""
        stats = {
            "total": len(self._access_rights),
            "by_type": {
                "allow": 0,
                "deny": 0
            },
            "by_provider": {},
            "expiring_soon": 0
        }
        
        now = datetime.utcnow()
        
        for ar in self._access_rights.values():
            # By type
            access_type = ar["access_type"]
            stats["by_type"][access_type] = stats["by_type"].get(access_type, 0) + 1
            
            # By provider
            provider = ar["provider_org_code"]
            stats["by_provider"][provider] = stats["by_provider"].get(provider, 0) + 1
            
            # Expiring soon (within 30 days)
            if ar["expires_at"]:
                expires = datetime.fromisoformat(ar["expires_at"])
                days_remaining = (expires - now).days
                if 0 <= days_remaining <= 30:
                    stats["expiring_soon"] += 1
        
        return stats


# Singleton instance
_access_rights_manager: Optional[AccessRightsManager] = None


def get_access_rights_manager() -> AccessRightsManager:
    """Get the global AccessRightsManager instance"""
    global _access_rights_manager
    if _access_rights_manager is None:
        _access_rights_manager = AccessRightsManager()
    return _access_rights_manager
