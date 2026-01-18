"""
X-Road Protocol Handler

Handles X-Road message protocol:
- Message parsing and construction
- Protocol validation
- Header management
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import uuid
import json

from .models import XRoadRequest, XRoadResponse, XRoadClientId, XRoadServiceId, MemberClass

logger = logging.getLogger(__name__)


@dataclass
class XRoadHeader:
    """X-Road message header"""
    client: XRoadClientId
    service: XRoadServiceId
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_version: str = "4.0"
    issue: str = None  # Issue timestamp
    request_hash: str = None
    request_hash_algorithm: str = "SHA-256"
    
    def to_dict(self) -> Dict:
        return {
            "client": {
                "instance": self.client.instance,
                "member_class": self.client.member_class.value,
                "member_code": self.client.member_code,
                "subsystem_code": self.client.subsystem_code
            },
            "service": {
                "instance": self.service.instance,
                "member_class": self.service.member_class.value,
                "member_code": self.service.member_code,
                "subsystem_code": self.service.subsystem_code,
                "service_code": self.service.service_code,
                "service_version": self.service.service_version
            },
            "id": self.id,
            "protocol_version": self.protocol_version,
            "issue": self.issue,
            "request_hash": self.request_hash,
            "request_hash_algorithm": self.request_hash_algorithm
        }


@dataclass
class XRoadMessage:
    """Complete X-Road message"""
    header: XRoadHeader
    body: Any
    attachments: list = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "header": self.header.to_dict(),
            "body": self.body,
            "attachments": [str(a) for a in self.attachments]
        }


class XRoadProtocol:
    """
    X-Road Protocol Handler.
    
    Provides:
    - Message construction
    - Message validation
    - Protocol version handling
    """
    
    SUPPORTED_VERSIONS = ["4.0", "4.1"]
    DEFAULT_VERSION = "4.0"
    
    @staticmethod
    def create_request(
        client_org_code: str,
        client_subsystem: str,
        service_org_code: str,
        service_subsystem: str,
        service_code: str,
        service_version: str = "v1",
        method: str = "GET",
        path: str = "/",
        body: Any = None,
        headers: Dict = None,
        client_member_class: MemberClass = MemberClass.GOV,
        service_member_class: MemberClass = MemberClass.GOV
    ) -> XRoadRequest:
        """
        Create an X-Road request.
        
        Args:
            client_org_code: Client organization code
            client_subsystem: Client subsystem code
            service_org_code: Service provider organization code
            service_subsystem: Service provider subsystem code
            service_code: Service code
            service_version: Service version
            method: HTTP method
            path: Request path
            body: Request body
            headers: Additional headers
            client_member_class: Client member class
            service_member_class: Service member class
            
        Returns:
            Constructed XRoadRequest
        """
        client = XRoadClientId(
            instance="RW",
            member_class=client_member_class,
            member_code=client_org_code,
            subsystem_code=client_subsystem
        )
        
        service = XRoadServiceId(
            instance="RW",
            member_class=service_member_class,
            member_code=service_org_code,
            subsystem_code=service_subsystem,
            service_code=service_code,
            service_version=service_version
        )
        
        return XRoadRequest(
            client=client,
            service=service,
            request_id=str(uuid.uuid4()),
            protocol_version=XRoadProtocol.DEFAULT_VERSION,
            method=method,
            path=path,
            headers=headers or {},
            body=body,
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def validate_request(request: XRoadRequest) -> Dict:
        """
        Validate an X-Road request.
        
        Args:
            request: Request to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        # Check protocol version
        if request.protocol_version not in XRoadProtocol.SUPPORTED_VERSIONS:
            errors.append(f"Unsupported protocol version: {request.protocol_version}")
        
        # Check client identifier
        if not request.client.member_code:
            errors.append("Client member code is required")
        if not request.client.subsystem_code:
            errors.append("Client subsystem code is required")
        
        # Check service identifier
        if not request.service.member_code:
            errors.append("Service member code is required")
        if not request.service.subsystem_code:
            errors.append("Service subsystem code is required")
        if not request.service.service_code:
            errors.append("Service code is required")
        
        # Check method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if request.method.upper() not in valid_methods:
            errors.append(f"Invalid method: {request.method}")
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        return {"valid": True}
    
    @staticmethod
    def parse_request(data: Dict) -> Optional[XRoadRequest]:
        """
        Parse a dictionary into an XRoadRequest.
        
        Args:
            data: Request data dictionary
            
        Returns:
            Parsed XRoadRequest or None
        """
        try:
            client_data = data.get("client", {})
            service_data = data.get("service", {})
            
            client = XRoadClientId(
                instance=client_data.get("instance", "RW"),
                member_class=MemberClass(client_data.get("member_class", "GOV")),
                member_code=client_data.get("member_code"),
                subsystem_code=client_data.get("subsystem_code")
            )
            
            service = XRoadServiceId(
                instance=service_data.get("instance", "RW"),
                member_class=MemberClass(service_data.get("member_class", "GOV")),
                member_code=service_data.get("member_code"),
                subsystem_code=service_data.get("subsystem_code"),
                service_code=service_data.get("service_code"),
                service_version=service_data.get("service_version", "v1")
            )
            
            return XRoadRequest(
                client=client,
                service=service,
                request_id=data.get("request_id", str(uuid.uuid4())),
                protocol_version=data.get("protocol_version", XRoadProtocol.DEFAULT_VERSION),
                method=data.get("method", "GET"),
                path=data.get("path", "/"),
                headers=data.get("headers", {}),
                body=data.get("body"),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            return None
    
    @staticmethod
    def format_response(response: XRoadResponse) -> Dict:
        """
        Format an XRoadResponse to dictionary.
        
        Args:
            response: Response to format
            
        Returns:
            Dictionary representation
        """
        return {
            "request_id": response.request_id,
            "status_code": response.status_code,
            "headers": response.headers,
            "body": response.body,
            "response_hash": response.response_hash,
            "signature": response.signature,
            "request_timestamp": response.request_timestamp.isoformat(),
            "response_timestamp": response.response_timestamp.isoformat(),
            "duration_ms": response.duration_ms,
            "error_code": response.error_code,
            "error_message": response.error_message
        }
    
    @staticmethod
    def create_error_response(
        request_id: str,
        error_code: str,
        error_message: str,
        status_code: int = 400
    ) -> Dict:
        """
        Create an error response dictionary.
        
        Args:
            request_id: Original request ID
            error_code: Error code
            error_message: Human-readable error message
            status_code: HTTP status code
            
        Returns:
            Error response dictionary
        """
        now = datetime.utcnow()
        return {
            "request_id": request_id,
            "status_code": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": {
                "error": {
                    "code": error_code,
                    "message": error_message
                }
            },
            "request_timestamp": now.isoformat(),
            "response_timestamp": now.isoformat(),
            "duration_ms": 0,
            "error_code": error_code,
            "error_message": error_message
        }
