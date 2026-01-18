"""
API Gateway Module

Central gateway orchestrating all X-Road service calls:
- Request validation and authentication
- Rate limiting
- Circuit breaking
- Request routing
- Response transformation
- Comprehensive logging
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from .router import ServiceRouter, get_service_router
from .rate_limiter import RateLimiter, get_rate_limiter
from .circuit_breaker import CircuitBreaker, get_circuit_breaker
from registry.access_rights import get_access_rights_manager
from registry.service_registry import get_service_registry
from audit.audit_logger import get_audit_logger, AuditEventType
from xroad.signature import get_signature_service

logger = logging.getLogger(__name__)


class APIGateway:
    """
    Central API Gateway for X-Road data exchange.
    
    Orchestrates:
    - Authentication & Authorization
    - Rate limiting
    - Circuit breaking
    - Request routing
    - Audit logging
    """
    
    def __init__(self):
        """Initialize API Gateway"""
        self.router = get_service_router()
        self.rate_limiter = get_rate_limiter()
        self.circuit_breaker = get_circuit_breaker()
        self.access_manager = get_access_rights_manager()
        self.service_registry = get_service_registry()
        self.audit_logger = get_audit_logger()
        self.signature_service = get_signature_service()
        
        logger.info("APIGateway initialized")
    
    async def process_request(
        self,
        client_org: str,
        client_subsystem: str,
        target_org: str,
        target_subsystem: str,
        service_code: str,
        service_version: str = "v1",
        method: str = "GET",
        path: str = "/",
        headers: Dict = None,
        body: Any = None,
        client_ip: str = None
    ) -> Dict:
        """
        Process an X-Road service request through the gateway.
        
        This is the main entry point for all service calls.
        
        Args:
            client_org: Client organization code
            client_subsystem: Client subsystem code
            target_org: Target organization code
            target_subsystem: Target subsystem code
            service_code: Target service code
            service_version: Service version
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            client_ip: Client IP address
            
        Returns:
            Gateway response with result or error
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        service_key = f"{target_org}/{target_subsystem}/{service_code}"
        
        logger.info(f"Gateway processing request {request_id}: {client_org} -> {service_key}")
        
        try:
            # Step 1: Rate limiting check
            rate_check = self.rate_limiter.check_rate_limit(client_org, service_key)
            if not rate_check["allowed"]:
                self._log_request(
                    request_id=request_id,
                    client_org=client_org,
                    service_key=service_key,
                    status="rate_limited",
                    error=rate_check["reason"]
                )
                return {
                    "success": False,
                    "request_id": request_id,
                    "status_code": 429,
                    "error": "Rate Limit Exceeded",
                    "message": rate_check["reason"],
                    "retry_after_seconds": rate_check.get("retry_after_seconds", 60)
                }
            
            # Step 2: Circuit breaker check
            circuit_check = self.circuit_breaker.can_execute(service_key)
            if not circuit_check["allowed"]:
                self._log_request(
                    request_id=request_id,
                    client_org=client_org,
                    service_key=service_key,
                    status="circuit_open",
                    error=circuit_check["reason"]
                )
                return {
                    "success": False,
                    "request_id": request_id,
                    "status_code": 503,
                    "error": "Service Unavailable",
                    "message": f"Circuit breaker is {circuit_check['state']}",
                    "retry_after_seconds": circuit_check.get("retry_after_seconds", 30)
                }
            
            # Step 3: Access rights check
            service = self.service_registry.get_service_by_code(
                organization_code=target_org,
                subsystem_code=target_subsystem,
                service_code=service_code,
                version=service_version
            )
            
            if not service:
                return {
                    "success": False,
                    "request_id": request_id,
                    "status_code": 404,
                    "error": "Service Not Found",
                    "message": f"Service {service_key} not found"
                }
            
            # Get client subsystem ID for access check
            from registry.organization_registry import get_organization_registry
            org_registry = get_organization_registry()
            client_subsystem_data = org_registry.get_subsystem_by_code(client_org, client_subsystem)
            
            if client_subsystem_data:
                access_check = self.access_manager.check_access(
                    service["id"],
                    client_subsystem_data["id"]
                )
                
                if not access_check["allowed"]:
                    self._log_request(
                        request_id=request_id,
                        client_org=client_org,
                        service_key=service_key,
                        status="access_denied",
                        error=access_check.get("reason")
                    )
                    
                    # Log to audit
                    self.audit_logger.log_access(
                        client_org=client_org,
                        service_code=service_code,
                        provider_org=target_org,
                        event_type=AuditEventType.ACCESS_DENIED,
                        details={"reason": access_check.get("reason")}
                    )
                    
                    return {
                        "success": False,
                        "request_id": request_id,
                        "status_code": 403,
                        "error": "Access Denied",
                        "message": f"No access rights for service {service_key}: {access_check.get('reason')}"
                    }
            
            # Step 4: Sign the request
            request_data = {
                "client_org": client_org,
                "client_subsystem": client_subsystem,
                "target_org": target_org,
                "target_subsystem": target_subsystem,
                "service_code": service_code,
                "method": method,
                "path": path,
                "body": body,
                "timestamp": start_time.isoformat()
            }
            request_hash = self.signature_service.compute_hash(request_data)
            
            # Step 5: Route the request
            result = await self.router.route_request(
                organization_code=target_org,
                subsystem_code=target_subsystem,
                service_code=service_code,
                service_version=service_version,
                method=method,
                path=path,
                headers={
                    "X-Road-Client": f"{client_org}/{client_subsystem}",
                    "X-Road-Request-Id": request_id,
                    "X-Road-Request-Hash": request_hash,
                    **(headers or {})
                },
                body=body
            )
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Step 6: Handle result and update circuit breaker
            if result.get("success"):
                self.circuit_breaker.record_success(service_key)
                
                # Log successful transaction
                self.audit_logger.log_transaction(
                    transaction_id=request_id,
                    client_org=client_org,
                    service_code=service_code,
                    status="success",
                    duration_ms=duration_ms,
                    request_id=request_id
                )
                
                return {
                    "success": True,
                    "request_id": request_id,
                    "status_code": result.get("status_code", 200),
                    "data": result.get("body"),
                    "headers": result.get("headers", {}),
                    "duration_ms": duration_ms,
                    "signature": {
                        "request_hash": request_hash,
                        "algorithm": "SHA-256"
                    }
                }
            else:
                self.circuit_breaker.record_failure(
                    service_key,
                    result.get("error")
                )
                
                # Log failed transaction
                self.audit_logger.log_transaction(
                    transaction_id=request_id,
                    client_org=client_org,
                    service_code=service_code,
                    status="failed",
                    duration_ms=duration_ms,
                    error=result.get("message"),
                    request_id=request_id
                )
                
                return {
                    "success": False,
                    "request_id": request_id,
                    "status_code": result.get("status_code", 500),
                    "error": result.get("error"),
                    "message": result.get("message"),
                    "duration_ms": duration_ms
                }
                
        except Exception as e:
            logger.error(f"Gateway error: {e}")
            
            # Record failure
            self.circuit_breaker.record_failure(service_key, str(e))
            
            # Log error
            self.audit_logger.log_error(
                error_message=str(e),
                error_type="gateway_error",
                resource_type="service",
                resource_id=service_key,
                details={
                    "request_id": request_id,
                    "client_org": client_org
                }
            )
            
            return {
                "success": False,
                "request_id": request_id,
                "status_code": 500,
                "error": "Gateway Error",
                "message": str(e)
            }
    
    def _log_request(
        self,
        request_id: str,
        client_org: str,
        service_key: str,
        status: str,
        error: str = None
    ):
        """Log request for debugging"""
        logger.info(
            f"Request {request_id}: {client_org} -> {service_key} = {status}"
            + (f" ({error})" if error else "")
        )
    
    def get_gateway_status(self) -> Dict:
        """Get gateway health and status"""
        open_circuits = self.circuit_breaker.get_open_circuits()
        
        return {
            "status": "operational" if len(open_circuits) == 0 else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "circuits": {
                "total": len(self.circuit_breaker._circuits),
                "open": len(open_circuits),
                "open_services": open_circuits
            },
            "rate_limiting": {
                "organizations_tracked": len(self.rate_limiter._org_buckets)
            }
        }
    
    def get_service_health(self, service_key: str) -> Dict:
        """Get health status for a specific service"""
        circuit_status = self.circuit_breaker.get_circuit_status(service_key)
        
        return {
            "service": service_key,
            "circuit": circuit_status,
            "available": circuit_status["state"] != "open"
        }
    
    async def cleanup(self):
        """Cleanup gateway resources"""
        await self.router.close()


# Singleton instance
_api_gateway: Optional[APIGateway] = None


def get_api_gateway() -> APIGateway:
    """Get the global APIGateway instance"""
    global _api_gateway
    if _api_gateway is None:
        _api_gateway = APIGateway()
    return _api_gateway
