"""
Encryption Service Module

Encryption and decryption for X-Road messages:
- Symmetric encryption (AES)
- Asymmetric encryption (RSA)
- Hybrid encryption for large messages
"""

import logging
import os
import base64
from typing import Tuple, Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from pki.key_manager import KeyManager, get_key_manager

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Encryption service for X-Road messages.
    
    Provides:
    - AES symmetric encryption
    - RSA asymmetric encryption
    - Hybrid encryption (RSA + AES)
    """
    
    AES_KEY_SIZE = 256  # bits
    AES_BLOCK_SIZE = 128  # bits
    
    def __init__(self, key_manager: KeyManager = None):
        """Initialize encryption service"""
        self.key_manager = key_manager or get_key_manager()
        logger.info("EncryptionService initialized")
    
    def generate_aes_key(self) -> bytes:
        """
        Generate a random AES-256 key.
        
        Returns:
            32-byte AES key
        """
        return os.urandom(self.AES_KEY_SIZE // 8)
    
    def generate_iv(self) -> bytes:
        """
        Generate a random initialization vector.
        
        Returns:
            16-byte IV
        """
        return os.urandom(self.AES_BLOCK_SIZE // 8)
    
    def encrypt_aes(
        self,
        plaintext: bytes,
        key: bytes = None,
        iv: bytes = None
    ) -> Dict:
        """
        Encrypt data using AES-256-CBC.
        
        Args:
            plaintext: Data to encrypt
            key: AES key (generated if not provided)
            iv: Initialization vector (generated if not provided)
            
        Returns:
            Dictionary with ciphertext, key, and iv (base64-encoded)
        """
        if key is None:
            key = self.generate_aes_key()
        if iv is None:
            iv = self.generate_iv()
        
        # Pad the plaintext
        padder = padding.PKCS7(self.AES_BLOCK_SIZE).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "key": base64.b64encode(key).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "algorithm": "AES-256-CBC"
        }
    
    def decrypt_aes(
        self,
        ciphertext_b64: str,
        key_b64: str,
        iv_b64: str
    ) -> bytes:
        """
        Decrypt AES-256-CBC encrypted data.
        
        Args:
            ciphertext_b64: Base64-encoded ciphertext
            key_b64: Base64-encoded AES key
            iv_b64: Base64-encoded IV
            
        Returns:
            Decrypted plaintext
        """
        ciphertext = base64.b64decode(ciphertext_b64)
        key = base64.b64decode(key_b64)
        iv = base64.b64decode(iv_b64)
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(self.AES_BLOCK_SIZE).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        
        return plaintext
    
    def encrypt_hybrid(
        self,
        plaintext: bytes,
        recipient_public_key_pem: str
    ) -> Dict:
        """
        Encrypt data using hybrid encryption (RSA + AES).
        
        1. Generate random AES key
        2. Encrypt data with AES
        3. Encrypt AES key with recipient's RSA public key
        
        Args:
            plaintext: Data to encrypt
            recipient_public_key_pem: Recipient's RSA public key (PEM)
            
        Returns:
            Dictionary with encrypted data and encrypted key
        """
        # Generate AES key and encrypt data
        aes_key = self.generate_aes_key()
        iv = self.generate_iv()
        
        encrypted_data = self.encrypt_aes(plaintext, aes_key, iv)
        
        # Encrypt AES key with RSA
        public_key = self.key_manager.load_public_key(
            recipient_public_key_pem.encode('utf-8')
        )
        encrypted_key = self.key_manager.encrypt_data(public_key, aes_key)
        
        return {
            "ciphertext": encrypted_data["ciphertext"],
            "iv": encrypted_data["iv"],
            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
            "algorithm": "RSA-OAEP+AES-256-CBC"
        }
    
    def decrypt_hybrid(
        self,
        encrypted_data: Dict,
        recipient_private_key_pem: str
    ) -> bytes:
        """
        Decrypt hybrid-encrypted data.
        
        1. Decrypt AES key with RSA private key
        2. Decrypt data with AES key
        
        Args:
            encrypted_data: Dictionary with ciphertext, iv, and encrypted_key
            recipient_private_key_pem: Recipient's RSA private key (PEM)
            
        Returns:
            Decrypted plaintext
        """
        # Decrypt AES key with RSA
        private_key = self.key_manager.load_private_key(
            recipient_private_key_pem.encode('utf-8')
        )
        encrypted_key_bytes = base64.b64decode(encrypted_data["encrypted_key"])
        aes_key = self.key_manager.decrypt_data(private_key, encrypted_key_bytes)
        
        # Decrypt data with AES
        return self.decrypt_aes(
            encrypted_data["ciphertext"],
            base64.b64encode(aes_key).decode('utf-8'),
            encrypted_data["iv"]
        )
    
    def encrypt_message(
        self,
        message: str,
        recipient_public_key_pem: str
    ) -> Dict:
        """
        Encrypt a string message for a recipient.
        
        Args:
            message: Message to encrypt
            recipient_public_key_pem: Recipient's public key
            
        Returns:
            Encrypted message dictionary
        """
        plaintext = message.encode('utf-8')
        return self.encrypt_hybrid(plaintext, recipient_public_key_pem)
    
    def decrypt_message(
        self,
        encrypted_data: Dict,
        recipient_private_key_pem: str
    ) -> str:
        """
        Decrypt a string message.
        
        Args:
            encrypted_data: Encrypted message dictionary
            recipient_private_key_pem: Recipient's private key
            
        Returns:
            Decrypted message string
        """
        plaintext = self.decrypt_hybrid(encrypted_data, recipient_private_key_pem)
        return plaintext.decode('utf-8')


# Singleton instance
_encryption_service: EncryptionService = None


def get_encryption_service() -> EncryptionService:
    """Get the global EncryptionService instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
