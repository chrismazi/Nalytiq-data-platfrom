"""
X-Road Core Module for Rwanda National Data Intelligence Platform (R-NDIP)

This module implements X-Road-like secure data exchange capabilities:
- Security Server: Message signing, encryption, validation
- Protocol Handler: REST/SOAP message processing
- Message Exchange: Secure data transfer between organizations

Based on the X-Road specification by NIIS (Nordic Institute for Interoperability Solutions)
Adapted for Rwanda's national data infrastructure needs.
"""

from .security_server import SecurityServer
from .protocol import XRoadProtocol, XRoadMessage, XRoadHeader
from .message_handler import MessageHandler
from .signature import SignatureService
from .encryption import EncryptionService

__all__ = [
    'SecurityServer',
    'XRoadProtocol',
    'XRoadMessage', 
    'XRoadHeader',
    'MessageHandler',
    'SignatureService',
    'EncryptionService'
]

__version__ = '1.0.0'
__author__ = 'NISR Rwanda / Chris Mazimpaka'
