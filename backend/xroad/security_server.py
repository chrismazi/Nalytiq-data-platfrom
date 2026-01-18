"""
X-Road Security Server

The Security Server is the core component of X-Road that:
- Handles secure message exchange between organizations
- Signs and encrypts all messages
- Validates certificates and access rights
- Logs all transactions for audit

This implementation is adapted for R-NDIP (Rwanda National Data Intelligence Platform).
"""

import logging
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid
import json

from pki.key_manager import get_key_manager
from pki.certificate_manager import get_certificate_manager
from registry.organization_registry import get_organization_registry
from registry.service_registry import get_service_registry
from registry.access_rights import get_access_rights_manager

from .models import (
    XRoadRequest, XRoadResponse, XRoadClientId, XRoadServiceId,
    TransactionLog, TransactionStatus
)

logger = logging.getLogger(__name__)


class SecurityServer:
    """
    X-Road Security Server implementation.
    
    Responsibilities:
    - Message signing and verification
    - Client/server authentication
    - Access control enforcement
    - Transaction logging
    - Message routing
    """
    
    INSTANCE_ID = "RW"  # Rwanda instance
    SERVER_VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize Security Server"""
        self.key_manager = get_key_manager()
        self.cert_manager = get_certificate_manager()
        self.org_registry = get_organization_registry()
        self.service_registry = get_service_registry()
        self.access_manager = get_access_rights_manager()
        
        # Transaction log storage (will be moved to DB in production)
        self._transaction_logs: Dict[str, Dict] = {}
        
        logger.info(f"SecurityServer initialized - Instance: {self.INSTANCE_ID}")
    
    def process_request(
        self,
        request: XRoadRequest,
        client_certificate_pem: str = None
    ) -> XRoadResponse:
        """
        Process an incoming X-Road request.
        
        This is the main entry point for all X-Road message exchange.
        
        Args:
            request: The X-Road request
            client_certificate_pem: Optional client certificate for validation
            
        Returns:
            XRoadResponse with result or error
        """
        request_timestamp = datetime.utcnow()
        transaction_id = str(uuid.uuid4())
        
        logger.info(f"Processing request {request.request_id} from {request.client}")
        
        try:
            # Step 1: Validate client
            client_validation = self._validate_client(request.client, client_certificate_pem)
            if not client_validation["valid"]:
                return self._create_error_response(
                    request, 
                    400, 
                    "client_validation_failed",
                    client_validation.get("error", "Client validation failed"),
                    request_timestamp
                )
            
            # Step 2: Validate service exists
            service = self._resolve_service(request.service)
            if not service:
                return self._create_error_response(
                    request,
                    404,
                    "service_not_found",
                    f"Service not found: {request.service}",
                    request_timestamp
                )
            
            # Step 3: Check access rights
            access_check = self._check_access_rights(
                service["id"],
                client_validation.get("subsystem_id")
            )
            if not access_check["allowed"]:
                return self._create_error_response(
                    request,
                    403,
                    "access_denied",
                    f"Access denied: {access_check.get('reason', 'No access rights')}",
                    request_timestamp
                )
            
            # Step 4: Compute request hash
            request_hash = self._compute_message_hash(request)
            
            # Step 5: Sign request
            signature = self._sign_message(request_hash)
            
            # Step 6: Forward request to service provider
            # (In production, this would make an actual HTTP request to the target service)
            service_response = self._forward_request(request, service)
            
            # Step 7: Create response
            response_timestamp = datetime.utcnow()
            duration_ms = int((response_timestamp - request_timestamp).total_seconds() * 1000)
            
            response = XRoadResponse(
                request_id=request.request_id,
                status_code=service_response.get("status_code", 200),
                headers=service_response.get("headers", {}),
                body=service_response.get("body"),
                response_hash=self._compute_response_hash(service_response),
                signature=signature,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                duration_ms=duration_ms
            )
            
            # Step 8: Log transaction
            self._log_transaction(
                transaction_id=transaction_id,
                request=request,
                response=response,
                client_info=client_validation,
                service=service,
                status=TransactionStatus.SUCCESS
            )
            
            logger.info(f"Request {request.request_id} processed successfully in {duration_ms}ms")
            return response
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return self._create_error_response(
                request,
                500,
                "internal_error",
                str(e),
                request_timestamp
            )
    
    def _validate_client(
        self, 
        client_id: XRoadClientId,
        certificate_pem: str = None
    ) -> Dict:
        """
        Validate the client making the request.
        
        Args:
            client_id: Client identifier
            certificate_pem: Optional client certificate
            
        Returns:
            Validation result with org/subsystem info
        """
        # Look up organization
        org = self.org_registry.get_organization_by_code(client_id.member_code)
        if not org:
            return {
                "valid": False,
                "error": f"Organization not found: {client_id.member_code}"
            }
        
        # Check organization status
        if org["status"] != "active":
            return {
                "valid": False,
                "error": f"Organization is not active: {org['status']}"
            }
        
        # Look up subsystem
        subsystem = self.org_registry.get_subsystem_by_code(
            client_id.member_code,
            client_id.subsystem_code
        )
        if not subsystem:
            return {
                "valid": False,
                "error": f"Subsystem not found: {client_id.subsystem_code}"
            }
        
        # Validate certificate (if provided)
        if certificate_pem:
            cert_result = self.cert_manager.validate_certificate(certificate_pem)
            if not cert_result["valid"]:
                return {
                    "valid": False,
                    "error": f"Invalid certificate: {cert_result.get('error')}"
                }
        
        return {
            "valid": True,
            "organization_id": org["id"],
            "organization_code": org["code"],
            "organization_name": org["name"],
            "subsystem_id": subsystem["id"],
            "subsystem_code": subsystem["code"]
        }
    
    def _resolve_service(self, service_id: XRoadServiceId) -> Optional[Dict]:
        """
        Resolve service from service identifier.
        
        Args:
            service_id: X-Road service identifier
            
        Returns:
            Service data or None
        """
        service = self.service_registry.get_service_by_code(
            organization_code=service_id.member_code,
            subsystem_code=service_id.subsystem_code,
            service_code=service_id.service_code,
            version=service_id.service_version
        )
        
        return service
    
    def _check_access_rights(
        self,
        service_id: str,
        client_subsystem_id: str
    ) -> Dict:
        """
        Check if client has access to the service.
        
        Args:
            service_id: Service ID
            client_subsystem_id: Client subsystem ID
            
        Returns:
            Access check result
        """
        if not client_subsystem_id:
            return {
                "allowed": False,
                "reason": "client_subsystem_unknown"
            }
        
        return self.access_manager.check_access(service_id, client_subsystem_id)
    
    def _compute_message_hash(self, request: XRoadRequest) -> str:
        """
        Compute SHA-256 hash of the request message.
        
        Args:
            request: X-Road request
            
        Returns:
            Hex-encoded hash string
        """
        # Create canonical representation
        canonical = json.dumps({
            "request_id": request.request_id,
            "client": str(request.client),
            "service": str(request.service),
            "method": request.method,
            "path": request.path,
            "body": request.body,
            "timestamp": request.timestamp.isoformat()
        }, sort_keys=True)
        
        hash_value = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return hash_value
    
    def _compute_response_hash(self, response: Dict) -> str:
        """Compute hash of response"""
        canonical = json.dumps(response, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def _sign_message(self, message_hash: str) -> str:
        """
        Sign a message hash with the security server's key.
        
        Args:
            message_hash: Hash of the message
            
        Returns:
            Base64-encoded signature
        """
        try:
            # In production, load the security server's signing key
            # For now, return a placeholder
            # signature = self.key_manager.sign_data(private_key, message_hash.encode())
            # return base64.b64encode(signature).decode('utf-8')
            
            # Placeholder signature (simulated)
            combined = f"{message_hash}:{datetime.utcnow().isoformat()}"
            signature_hash = hashlib.sha256(combined.encode()).hexdigest()
            return base64.b64encode(signature_hash.encode()).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Signing failed: {e}")
            return ""
    
    def _forward_request(
        self,
        request: XRoadRequest,
        service: Dict
    ) -> Dict:
        """
        Forward request to the target service.
        
        In production, this would make an actual HTTP request.
        Currently returns a simulated response.
        
        Args:
            request: X-Road request
            service: Target service info
            
        Returns:
            Service response
        """
        # TODO: Implement actual HTTP forwarding
        # For now, return simulated response
        
        logger.info(f"Forwarding request to service: {service['service_code']}")
        
        # Simulated response
        return {
            "status_code": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Road-Service": service["service_code"],
                "X-Road-Version": service["service_version"]
            },
            "body": {
                "success": True,
                "message": f"Request processed by {service['title']}",
                "service": service["service_code"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_error_response(
        self,
        request: XRoadRequest,
        status_code: int,
        error_code: str,
        error_message: str,
        request_timestamp: datetime
    ) -> XRoadResponse:
        """Create an error response"""
        response_timestamp = datetime.utcnow()
        
        return XRoadResponse(
            request_id=request.request_id,
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body=None,
            request_timestamp=request_timestamp,
            response_timestamp=response_timestamp,
            duration_ms=int((response_timestamp - request_timestamp).total_seconds() * 1000),
            error_code=error_code,
            error_message=error_message
        )
    
    def _log_transaction(
        self,
        transaction_id: str,
        request: XRoadRequest,
        response: XRoadResponse,
        client_info: Dict,
        service: Dict,
        status: TransactionStatus
    ):
        """
        Log a transaction for audit purposes.
        
        Args:
            transaction_id: Unique transaction ID
            request: Original request
            response: Response sent
            client_info: Client validation info
            service: Service info
            status: Transaction status
        """
        log_entry = {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "client_org_id": client_info.get("organization_id"),
            "client_org_code": client_info.get("organization_code"),
            "client_subsystem_id": client_info.get("subsystem_id"),
            "client_subsystem_code": client_info.get("subsystem_code"),
            "service_org_id": service.get("organization_id"),
            "service_org_code": service.get("organization_code"),
            "service_id": service.get("id"),
            "service_code": service.get("service_code"),
            "service_version": service.get("service_version"),
            "request_method": request.method,
            "request_path": request.path,
            "request_size_bytes": len(json.dumps(request.body or {})),
            "request_timestamp": request.timestamp.isoformat(),
            "response_timestamp": response.response_timestamp.isoformat(),
            "response_size_bytes": len(json.dumps(response.body or {})),
            "response_status_code": response.status_code,
            "message_hash": self._compute_message_hash(request),
            "signature": response.signature,
            "timestamped_at": datetime.utcnow().isoformat(),
            "status": status.value,
            "error_message": response.error_message,
            "duration_ms": response.duration_ms
        }
        
        self._transaction_logs[transaction_id] = log_entry
        logger.debug(f"Transaction logged: {transaction_id}")
    
    def get_transaction_log(self, transaction_id: str) -> Optional[Dict]:
        """Get a transaction log entry"""
        return self._transaction_logs.get(transaction_id)
    
    def get_transaction_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        client_org_code: str = None,
        service_code: str = None,
        status: TransactionStatus = None,
        limit: int = 100
    ) -> list:
        """
        Query transaction logs with filters.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            client_org_code: Filter by client organization
            service_code: Filter by service
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of matching transaction logs
        """
        results = []
        
        for log in self._transaction_logs.values():
            # Apply filters
            if client_org_code and log.get("client_org_code") != client_org_code:
                continue
            if service_code and log.get("service_code") != service_code:
                continue
            if status and log.get("status") != status.value:
                continue
            
            if start_date:
                log_time = datetime.fromisoformat(log["request_timestamp"])
                if log_time < start_date:
                    continue
            
            if end_date:
                log_time = datetime.fromisoformat(log["request_timestamp"])
                if log_time > end_date:
                    continue
            
            results.append(log)
            
            if len(results) >= limit:
                break
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x["request_timestamp"], reverse=True)
        
        return results
    
    def get_server_status(self) -> Dict:
        """Get security server status"""
        return {
            "instance": self.INSTANCE_ID,
            "version": self.SERVER_VERSION,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_transactions": len(self._transaction_logs),
                "organizations_registered": len(self.org_registry.list_organizations()),
                "services_registered": len(self.service_registry.list_services())
            }
        }


# Singleton instance
_security_server: Optional[SecurityServer] = None


def get_security_server() -> SecurityServer:
    """Get the global SecurityServer instance"""
    global _security_server
    if _security_server is None:
        _security_server = SecurityServer()
    return _security_server
