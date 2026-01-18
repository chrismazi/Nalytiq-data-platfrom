"""
Certificate Authority Module

Provides X.509 certificate generation and management:
- Root CA certificate generation
- Organization certificate issuance
- Certificate signing
- Certificate validation
- Certificate revocation

Implements a simplified CA suitable for R-NDIP X-Road deployment.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import uuid

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from .key_manager import KeyManager, get_key_manager

logger = logging.getLogger(__name__)


class CertificateAuthority:
    """
    Certificate Authority for R-NDIP X-Road.
    
    Provides:
    - Root CA certificate generation
    - Organization certificate issuance
    - Signing and authentication certificates
    - Certificate validation and revocation
    """
    
    # Certificate validity periods (in days)
    ROOT_CA_VALIDITY = 3650      # 10 years
    ORG_CERT_VALIDITY = 1095     # 3 years
    SIGNING_CERT_VALIDITY = 730  # 2 years
    AUTH_CERT_VALIDITY = 365     # 1 year
    
    # CA Configuration
    CA_COUNTRY = "RW"
    CA_STATE = "Kigali"
    CA_LOCALITY = "Kigali"
    CA_ORGANIZATION = "Rwanda National Data Infrastructure"
    CA_COMMON_NAME = "R-NDIP Root CA"
    
    CERTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'certificates')
    
    def __init__(self, key_manager: KeyManager = None, certs_directory: str = None):
        """Initialize Certificate Authority"""
        self.key_manager = key_manager or get_key_manager()
        self.certs_dir = certs_directory or self.CERTS_DIR
        os.makedirs(self.certs_dir, exist_ok=True)
        
        # Load or generate root CA
        self.root_private_key = None
        self.root_certificate = None
        self._initialize_root_ca()
        
        logger.info("CertificateAuthority initialized")
    
    def _initialize_root_ca(self):
        """Initialize or load the Root CA"""
        root_ca_key_path = os.path.join(self.certs_dir, "root_ca_private.pem")
        root_ca_cert_path = os.path.join(self.certs_dir, "root_ca_cert.pem")
        
        if os.path.exists(root_ca_key_path) and os.path.exists(root_ca_cert_path):
            # Load existing Root CA
            logger.info("Loading existing Root CA...")
            with open(root_ca_key_path, 'rb') as f:
                self.root_private_key = self.key_manager.load_private_key(f.read())
            with open(root_ca_cert_path, 'rb') as f:
                self.root_certificate = x509.load_pem_x509_certificate(
                    f.read(), default_backend()
                )
            logger.info("Root CA loaded successfully")
        else:
            # Generate new Root CA
            logger.info("Generating new Root CA...")
            self._generate_root_ca()
            logger.info("Root CA generated successfully")
    
    def _generate_root_ca(self):
        """Generate a new Root CA certificate"""
        # Generate key pair
        self.root_private_key, root_public_key = self.key_manager.generate_key_pair(
            key_size=4096  # Use stronger key for CA
        )
        
        # Build certificate subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.CA_COUNTRY),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.CA_STATE),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.CA_LOCALITY),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.CA_ORGANIZATION),
            x509.NameAttribute(NameOID.COMMON_NAME, self.CA_COMMON_NAME),
        ])
        
        # Generate certificate
        now = datetime.utcnow()
        self.root_certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(root_public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=self.ROOT_CA_VALIDITY))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=1),
                critical=True
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(root_public_key),
                critical=False
            )
            .sign(self.root_private_key, hashes.SHA256(), default_backend())
        )
        
        # Save Root CA files
        root_ca_key_path = os.path.join(self.certs_dir, "root_ca_private.pem")
        root_ca_cert_path = os.path.join(self.certs_dir, "root_ca_cert.pem")
        
        # Save private key
        key_pem = self.key_manager.serialize_private_key(self.root_private_key)
        with open(root_ca_key_path, 'wb') as f:
            f.write(key_pem)
        
        # Restrict permissions
        try:
            os.chmod(root_ca_key_path, 0o600)
        except Exception:
            pass
        
        # Save certificate
        cert_pem = self.root_certificate.public_bytes(serialization.Encoding.PEM)
        with open(root_ca_cert_path, 'wb') as f:
            f.write(cert_pem)
        
        logger.info(f"Root CA certificate saved to {root_ca_cert_path}")
    
    def issue_organization_certificate(
        self,
        org_code: str,
        org_name: str,
        common_name: str,
        validity_days: int = None
    ) -> Dict:
        """
        Issue a certificate for an organization.
        
        Args:
            org_code: Organization code (e.g., "RW-GOV-NISR")
            org_name: Full organization name
            common_name: Certificate common name
            validity_days: Certificate validity in days
            
        Returns:
            Dictionary with certificate details and PEM content
        """
        validity_days = validity_days or self.ORG_CERT_VALIDITY
        
        # Generate key pair for organization
        private_key, public_key = self.key_manager.generate_key_pair()
        
        # Build subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.CA_COUNTRY),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.CA_STATE),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org_name),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, org_code),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        # Build issuer (Root CA)
        issuer = self.root_certificate.subject
        
        # Generate certificate
        now = datetime.utcnow()
        serial_number = x509.random_serial_number()
        
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(serial_number)
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                    ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=False
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(public_key),
                critical=False
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(
                    self.root_certificate.public_key()
                ),
                critical=False
            )
            .sign(self.root_private_key, hashes.SHA256(), default_backend())
        )
        
        # Serialize
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        private_key_pem = self.key_manager.serialize_private_key(private_key).decode('utf-8')
        public_key_pem = self.key_manager.serialize_public_key(public_key).decode('utf-8')
        fingerprint = self.key_manager.get_key_fingerprint(public_key)
        
        # Save to files
        cert_id = str(uuid.uuid4())
        cert_dir = os.path.join(self.certs_dir, org_code)
        os.makedirs(cert_dir, exist_ok=True)
        
        cert_path = os.path.join(cert_dir, f"{cert_id}_cert.pem")
        key_path = os.path.join(cert_dir, f"{cert_id}_private.pem")
        
        with open(cert_path, 'w') as f:
            f.write(cert_pem)
        
        with open(key_path, 'w') as f:
            f.write(private_key_pem)
        
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            pass
        
        logger.info(f"Issued certificate for organization: {org_code}")
        
        return {
            "id": cert_id,
            "organization_code": org_code,
            "organization_name": org_name,
            "common_name": common_name,
            "serial_number": format(serial_number, 'x').upper(),
            "subject": str(subject),
            "issuer": str(issuer),
            "valid_from": now.isoformat(),
            "valid_until": (now + timedelta(days=validity_days)).isoformat(),
            "fingerprint": fingerprint,
            "certificate_pem": cert_pem,
            "private_key_pem": private_key_pem,
            "public_key_pem": public_key_pem,
            "certificate_path": cert_path,
            "private_key_path": key_path
        }
    
    def issue_signing_certificate(
        self,
        org_code: str,
        org_name: str,
        validity_days: int = None
    ) -> Dict:
        """
        Issue a digital signing certificate for an organization.
        
        Args:
            org_code: Organization code
            org_name: Full organization name
            validity_days: Certificate validity
            
        Returns:
            Certificate details dictionary
        """
        return self.issue_organization_certificate(
            org_code=org_code,
            org_name=org_name,
            common_name=f"{org_code} Signing Certificate",
            validity_days=validity_days or self.SIGNING_CERT_VALIDITY
        )
    
    def issue_authentication_certificate(
        self,
        org_code: str,
        org_name: str,
        validity_days: int = None
    ) -> Dict:
        """
        Issue a TLS client authentication certificate.
        
        Args:
            org_code: Organization code
            org_name: Full organization name
            validity_days: Certificate validity
            
        Returns:
            Certificate details dictionary
        """
        return self.issue_organization_certificate(
            org_code=org_code,
            org_name=org_name,
            common_name=f"{org_code} Authentication Certificate",
            validity_days=validity_days or self.AUTH_CERT_VALIDITY
        )
    
    def validate_certificate(self, cert_pem: str) -> Dict:
        """
        Validate a certificate against the Root CA.
        
        Args:
            cert_pem: PEM-encoded certificate string
            
        Returns:
            Validation result dictionary
        """
        try:
            certificate = x509.load_pem_x509_certificate(
                cert_pem.encode('utf-8'), 
                default_backend()
            )
            
            now = datetime.utcnow()
            
            # Check validity period
            if now < certificate.not_valid_before:
                return {
                    "valid": False,
                    "error": "Certificate is not yet valid",
                    "not_valid_before": certificate.not_valid_before.isoformat()
                }
            
            if now > certificate.not_valid_after:
                return {
                    "valid": False,
                    "error": "Certificate has expired",
                    "not_valid_after": certificate.not_valid_after.isoformat()
                }
            
            # Verify signature (simplified - checks if signed by our CA)
            try:
                self.root_certificate.public_key().verify(
                    certificate.signature,
                    certificate.tbs_certificate_bytes,
                    certificate.signature_algorithm_parameters
                )
            except Exception:
                return {
                    "valid": False,
                    "error": "Certificate signature verification failed"
                }
            
            return {
                "valid": True,
                "subject": str(certificate.subject),
                "issuer": str(certificate.issuer),
                "serial_number": format(certificate.serial_number, 'x').upper(),
                "not_valid_before": certificate.not_valid_before.isoformat(),
                "not_valid_after": certificate.not_valid_after.isoformat(),
                "days_remaining": (certificate.not_valid_after - now).days
            }
            
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_root_ca_certificate(self) -> str:
        """Get the Root CA certificate in PEM format"""
        return self.root_certificate.public_bytes(
            serialization.Encoding.PEM
        ).decode('utf-8')
    
    def get_root_ca_info(self) -> Dict:
        """Get information about the Root CA"""
        cert = self.root_certificate
        return {
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "serial_number": format(cert.serial_number, 'x').upper(),
            "not_valid_before": cert.not_valid_before.isoformat(),
            "not_valid_after": cert.not_valid_after.isoformat(),
            "is_ca": True
        }
    
    def list_issued_certificates(self) -> List[Dict]:
        """List all issued certificates"""
        certificates = []
        
        for org_dir in os.listdir(self.certs_dir):
            org_path = os.path.join(self.certs_dir, org_dir)
            if os.path.isdir(org_path) and org_dir != "__pycache__":
                for cert_file in os.listdir(org_path):
                    if cert_file.endswith("_cert.pem"):
                        cert_path = os.path.join(org_path, cert_file)
                        with open(cert_path, 'r') as f:
                            cert_pem = f.read()
                        
                        try:
                            cert = x509.load_pem_x509_certificate(
                                cert_pem.encode('utf-8'),
                                default_backend()
                            )
                            
                            certificates.append({
                                "organization_code": org_dir,
                                "subject": str(cert.subject),
                                "serial_number": format(cert.serial_number, 'x').upper(),
                                "not_valid_before": cert.not_valid_before.isoformat(),
                                "not_valid_after": cert.not_valid_after.isoformat(),
                                "file_path": cert_path
                            })
                        except Exception as e:
                            logger.warning(f"Failed to load certificate {cert_path}: {e}")
        
        return certificates


# Singleton instance
_certificate_authority: Optional[CertificateAuthority] = None


def get_certificate_authority() -> CertificateAuthority:
    """Get the global CertificateAuthority instance"""
    global _certificate_authority
    if _certificate_authority is None:
        _certificate_authority = CertificateAuthority()
    return _certificate_authority
