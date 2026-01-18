"""
Key Manager Module

Handles cryptographic key operations:
- RSA key pair generation
- Key storage and retrieval
- Key serialization/deserialization
- Secure key handling
"""

import os
import logging
from typing import Tuple, Optional
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import hashlib
import base64

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Manages cryptographic keys for X-Road security.
    
    Provides:
    - RSA key pair generation (2048/4096 bit)
    - Key serialization (PEM format)
    - Key storage and retrieval
    - Key fingerprinting
    """
    
    DEFAULT_KEY_SIZE = 2048
    KEYS_DIR = os.path.join(os.path.dirname(__file__), '..', 'keys')
    
    def __init__(self, keys_directory: str = None):
        """Initialize key manager with optional custom keys directory"""
        self.keys_dir = keys_directory or self.KEYS_DIR
        os.makedirs(self.keys_dir, exist_ok=True)
        logger.info(f"KeyManager initialized with keys directory: {self.keys_dir}")
    
    def generate_key_pair(
        self, 
        key_size: int = DEFAULT_KEY_SIZE,
        public_exponent: int = 65537
    ) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Generate a new RSA key pair.
        
        Args:
            key_size: Size of the key in bits (2048 or 4096 recommended)
            public_exponent: Public exponent (65537 is standard)
            
        Returns:
            Tuple of (private_key, public_key)
        """
        if key_size < 2048:
            logger.warning(f"Key size {key_size} is below recommended minimum of 2048 bits")
        
        logger.info(f"Generating {key_size}-bit RSA key pair...")
        
        private_key = rsa.generate_private_key(
            public_exponent=public_exponent,
            key_size=key_size,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        
        logger.info("RSA key pair generated successfully")
        return private_key, public_key
    
    def serialize_private_key(
        self, 
        private_key: rsa.RSAPrivateKey,
        password: Optional[bytes] = None
    ) -> bytes:
        """
        Serialize private key to PEM format.
        
        Args:
            private_key: RSA private key object
            password: Optional password for encryption
            
        Returns:
            PEM-encoded private key bytes
        """
        if password:
            encryption = serialization.BestAvailableEncryption(password)
        else:
            encryption = serialization.NoEncryption()
        
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
        
        return pem
    
    def serialize_public_key(self, public_key: rsa.RSAPublicKey) -> bytes:
        """
        Serialize public key to PEM format.
        
        Args:
            public_key: RSA public key object
            
        Returns:
            PEM-encoded public key bytes
        """
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem
    
    def load_private_key(
        self, 
        pem_data: bytes,
        password: Optional[bytes] = None
    ) -> rsa.RSAPrivateKey:
        """
        Load private key from PEM data.
        
        Args:
            pem_data: PEM-encoded private key bytes
            password: Password if key is encrypted
            
        Returns:
            RSA private key object
        """
        private_key = serialization.load_pem_private_key(
            pem_data,
            password=password,
            backend=default_backend()
        )
        
        return private_key
    
    def load_public_key(self, pem_data: bytes) -> rsa.RSAPublicKey:
        """
        Load public key from PEM data.
        
        Args:
            pem_data: PEM-encoded public key bytes
            
        Returns:
            RSA public key object
        """
        public_key = serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
        
        return public_key
    
    def save_key_pair(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        public_key: rsa.RSAPublicKey,
        password: Optional[bytes] = None
    ) -> Tuple[str, str]:
        """
        Save key pair to files.
        
        Args:
            key_id: Unique identifier for the key pair
            private_key: RSA private key
            public_key: RSA public key
            password: Optional password for private key encryption
            
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        private_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        public_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        
        # Save private key
        private_pem = self.serialize_private_key(private_key, password)
        with open(private_path, 'wb') as f:
            f.write(private_pem)
        
        # Restrict private key file permissions (on Unix systems)
        try:
            os.chmod(private_path, 0o600)
        except Exception:
            pass  # Windows doesn't support chmod the same way
        
        # Save public key
        public_pem = self.serialize_public_key(public_key)
        with open(public_path, 'wb') as f:
            f.write(public_pem)
        
        logger.info(f"Key pair saved: {private_path}, {public_path}")
        return private_path, public_path
    
    def load_key_pair(
        self,
        key_id: str,
        password: Optional[bytes] = None
    ) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Load key pair from files.
        
        Args:
            key_id: Unique identifier for the key pair
            password: Password if private key is encrypted
            
        Returns:
            Tuple of (private_key, public_key)
        """
        private_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        public_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        
        with open(private_path, 'rb') as f:
            private_key = self.load_private_key(f.read(), password)
        
        with open(public_path, 'rb') as f:
            public_key = self.load_public_key(f.read())
        
        return private_key, public_key
    
    def get_key_fingerprint(self, public_key: rsa.RSAPublicKey) -> str:
        """
        Calculate SHA-256 fingerprint of a public key.
        
        Args:
            public_key: RSA public key
            
        Returns:
            Hex-encoded fingerprint string
        """
        der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        fingerprint = hashlib.sha256(der).hexdigest()
        
        # Format as colon-separated pairs for readability
        formatted = ':'.join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2))
        
        return formatted.upper()
    
    def sign_data(
        self,
        private_key: rsa.RSAPrivateKey,
        data: bytes
    ) -> bytes:
        """
        Sign data using RSA private key.
        
        Args:
            private_key: RSA private key for signing
            data: Data to sign
            
        Returns:
            Signature bytes
        """
        signature = private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return signature
    
    def verify_signature(
        self,
        public_key: rsa.RSAPublicKey,
        data: bytes,
        signature: bytes
    ) -> bool:
        """
        Verify a signature using RSA public key.
        
        Args:
            public_key: RSA public key for verification
            data: Original data that was signed
            signature: Signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
    
    def encrypt_data(
        self,
        public_key: rsa.RSAPublicKey,
        data: bytes
    ) -> bytes:
        """
        Encrypt data using RSA public key.
        
        Note: RSA encryption is limited to small data sizes.
        For larger data, use hybrid encryption (RSA + AES).
        
        Args:
            public_key: RSA public key for encryption
            data: Data to encrypt (max ~190 bytes for 2048-bit key)
            
        Returns:
            Encrypted data bytes
        """
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted
    
    def decrypt_data(
        self,
        private_key: rsa.RSAPrivateKey,
        encrypted_data: bytes
    ) -> bytes:
        """
        Decrypt data using RSA private key.
        
        Args:
            private_key: RSA private key for decryption
            encrypted_data: Data encrypted with corresponding public key
            
        Returns:
            Decrypted data bytes
        """
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted
    
    def key_exists(self, key_id: str) -> bool:
        """Check if a key pair exists for the given ID"""
        private_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        public_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        return os.path.exists(private_path) and os.path.exists(public_path)
    
    def delete_key_pair(self, key_id: str) -> bool:
        """
        Delete a key pair.
        
        Args:
            key_id: Unique identifier for the key pair
            
        Returns:
            True if deleted, False if not found
        """
        private_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        public_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        
        deleted = False
        
        if os.path.exists(private_path):
            os.remove(private_path)
            deleted = True
        
        if os.path.exists(public_path):
            os.remove(public_path)
            deleted = True
        
        if deleted:
            logger.info(f"Key pair deleted: {key_id}")
        
        return deleted


# Singleton instance for convenience
_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    """Get the global KeyManager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager
