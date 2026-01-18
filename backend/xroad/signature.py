"""
Signature Service Module

Digital signature operations for X-Road messages:
- Message signing
- Signature verification
- Timestamp integration
"""

import logging
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Tuple, Any
import json

from pki.key_manager import KeyManager, get_key_manager

logger = logging.getLogger(__name__)


class SignatureService:
    """
    Digital signature service for X-Road messages.
    
    Provides:
    - Message signing
    - Signature verification
    - Hash computation
    """
    
    HASH_ALGORITHM = "SHA-256"
    SIGNATURE_ALGORITHM = "RSA-SHA256"
    
    def __init__(self, key_manager: KeyManager = None):
        """Initialize signature service"""
        self.key_manager = key_manager or get_key_manager()
        logger.info("SignatureService initialized")
    
    def compute_hash(self, data: Any) -> str:
        """
        Compute SHA-256 hash of data.
        
        Args:
            data: Data to hash (will be serialized to JSON if not bytes/str)
            
        Returns:
            Hex-encoded hash string
        """
        if isinstance(data, bytes):
            content = data
        elif isinstance(data, str):
            content = data.encode('utf-8')
        else:
            content = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
        
        return hashlib.sha256(content).hexdigest()
    
    def sign_message(
        self,
        message_hash: str,
        key_id: str = None,
        private_key_pem: str = None
    ) -> Dict:
        """
        Sign a message hash.
        
        Args:
            message_hash: Hash of the message to sign
            key_id: ID of the key to use (if stored)
            private_key_pem: Direct private key PEM (alternative to key_id)
            
        Returns:
            Signature details including base64 signature
        """
        try:
            timestamp = datetime.utcnow()
            
            # Load the private key
            if private_key_pem:
                private_key = self.key_manager.load_private_key(
                    private_key_pem.encode('utf-8')
                )
            elif key_id:
                private_key, _ = self.key_manager.load_key_pair(key_id)
            else:
                # Use a default/temporary signature (for development)
                logger.warning("No signing key provided, using simulated signature")
                combined = f"{message_hash}:{timestamp.isoformat()}"
                sig_hash = hashlib.sha256(combined.encode()).hexdigest()
                return {
                    "signature": base64.b64encode(sig_hash.encode()).decode('utf-8'),
                    "algorithm": self.SIGNATURE_ALGORITHM,
                    "hash_algorithm": self.HASH_ALGORITHM,
                    "timestamp": timestamp.isoformat(),
                    "simulated": True
                }
            
            # Create signature
            signature_bytes = self.key_manager.sign_data(
                private_key,
                message_hash.encode('utf-8')
            )
            
            return {
                "signature": base64.b64encode(signature_bytes).decode('utf-8'),
                "algorithm": self.SIGNATURE_ALGORITHM,
                "hash_algorithm": self.HASH_ALGORITHM,
                "timestamp": timestamp.isoformat(),
                "key_id": key_id,
                "simulated": False
            }
            
        except Exception as e:
            logger.error(f"Signing failed: {e}")
            raise
    
    def verify_signature(
        self,
        message_hash: str,
        signature_b64: str,
        public_key_pem: str = None,
        key_id: str = None
    ) -> Dict:
        """
        Verify a message signature.
        
        Args:
            message_hash: Hash that was signed
            signature_b64: Base64-encoded signature
            public_key_pem: Public key PEM for verification
            key_id: ID of the key to use (if stored)
            
        Returns:
            Verification result
        """
        try:
            # Load the public key
            if public_key_pem:
                public_key = self.key_manager.load_public_key(
                    public_key_pem.encode('utf-8')
                )
            elif key_id:
                _, public_key = self.key_manager.load_key_pair(key_id)
            else:
                # Cannot verify without key
                return {
                    "valid": False,
                    "error": "No public key provided for verification"
                }
            
            # Decode signature
            signature_bytes = base64.b64decode(signature_b64)
            
            # Verify
            is_valid = self.key_manager.verify_signature(
                public_key,
                message_hash.encode('utf-8'),
                signature_bytes
            )
            
            return {
                "valid": is_valid,
                "verified_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def create_signed_message(
        self,
        content: Any,
        key_id: str = None,
        private_key_pem: str = None
    ) -> Dict:
        """
        Create a signed message with hash and signature.
        
        Args:
            content: Message content
            key_id: Signing key ID
            private_key_pem: Direct private key PEM
            
        Returns:
            Signed message with content, hash, and signature
        """
        # Compute hash
        content_hash = self.compute_hash(content)
        
        # Sign
        signature_info = self.sign_message(
            content_hash,
            key_id=key_id,
            private_key_pem=private_key_pem
        )
        
        return {
            "content": content,
            "hash": content_hash,
            "hash_algorithm": self.HASH_ALGORITHM,
            "signature": signature_info["signature"],
            "signature_algorithm": signature_info["algorithm"],
            "signed_at": signature_info["timestamp"]
        }
    
    def verify_signed_message(
        self,
        signed_message: Dict,
        public_key_pem: str = None,
        key_id: str = None
    ) -> Dict:
        """
        Verify a signed message.
        
        Args:
            signed_message: Message with content, hash, and signature
            public_key_pem: Public key for verification
            key_id: Key ID for verification
            
        Returns:
            Verification result
        """
        # Recompute hash
        computed_hash = self.compute_hash(signed_message["content"])
        
        # Check if hash matches
        if computed_hash != signed_message.get("hash"):
            return {
                "valid": False,
                "error": "Content hash mismatch - message may have been modified"
            }
        
        # Verify signature
        return self.verify_signature(
            message_hash=computed_hash,
            signature_b64=signed_message["signature"],
            public_key_pem=public_key_pem,
            key_id=key_id
        )


# Singleton instance
_signature_service: Optional[SignatureService] = None


def get_signature_service() -> SignatureService:
    """Get the global SignatureService instance"""
    global _signature_service
    if _signature_service is None:
        _signature_service = SignatureService()
    return _signature_service
