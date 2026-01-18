"""
Message Handler Module

Handles incoming and outgoing X-Road messages:
- Message routing
- Protocol translation
- Error handling
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json

from .models import XRoadRequest, XRoadResponse
from .protocol import XRoadProtocol
from .security_server import get_security_server

logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Handles X-Road message processing.
    
    Provides:
    - High-level message processing API
    - HTTP request/response translation
    - Error handling
    """
    
    def __init__(self):
        """Initialize message handler"""
        self.security_server = get_security_server()
        self.protocol = XRoadProtocol()
        logger.info("MessageHandler initialized")
    
    def handle_request(
        self,
        request_data: Dict,
        client_certificate: str = None
    ) -> Dict:
        """
        Handle an incoming X-Road request.
        
        Args:
            request_data: Request data dictionary
            client_certificate: Optional client certificate
            
        Returns:
            Response dictionary
        """
        try:
            # Parse request
            request = XRoadProtocol.parse_request(request_data)
            if not request:
                return XRoadProtocol.create_error_response(
                    request_id=request_data.get("request_id", "unknown"),
                    error_code="invalid_request",
                    error_message="Failed to parse request"
                )
            
            # Validate request
            validation = XRoadProtocol.validate_request(request)
            if not validation["valid"]:
                return XRoadProtocol.create_error_response(
                    request_id=request.request_id,
                    error_code="validation_failed",
                    error_message="; ".join(validation.get("errors", ["Validation failed"]))
                )
            
            # Process through security server
            response = self.security_server.process_request(
                request,
                client_certificate
            )
            
            # Format response
            return XRoadProtocol.format_response(response)
            
        except Exception as e:
            logger.error(f"Message handling failed: {e}")
            return XRoadProtocol.create_error_response(
                request_id=request_data.get("request_id", "unknown"),
                error_code="internal_error",
                error_message=str(e),
                status_code=500
            )
    
    def create_service_call(
        self,
        client_org: str,
        client_subsystem: str,
        target_org: str,
        target_subsystem: str,
        service_code: str,
        service_version: str = "v1",
        method: str = "GET",
        path: str = "/",
        body: Any = None,
        headers: Dict = None
    ) -> Dict:
        """
        Create and execute a service call.
        
        Convenience method for making X-Road service calls.
        
        Args:
            client_org: Calling organization code
            client_subsystem: Calling subsystem code
            target_org: Target organization code
            target_subsystem: Target subsystem code
            service_code: Service to call
            service_version: Service version
            method: HTTP method
            path: Request path
            body: Request body
            headers: Additional headers
            
        Returns:
            Response dictionary
        """
        # Create request
        request = XRoadProtocol.create_request(
            client_org_code=client_org,
            client_subsystem=client_subsystem,
            service_org_code=target_org,
            service_subsystem=target_subsystem,
            service_code=service_code,
            service_version=service_version,
            method=method,
            path=path,
            body=body,
            headers=headers
        )
        
        # Process request
        response = self.security_server.process_request(request)
        
        return XRoadProtocol.format_response(response)
    
    def get_available_services(
        self,
        organization_code: str = None,
        keyword: str = None
    ) -> list:
        """
        Get available services for discovery.
        
        Args:
            organization_code: Filter by organization
            keyword: Search keyword
            
        Returns:
            List of available services
        """
        from registry.service_registry import get_service_registry
        
        registry = get_service_registry()
        return registry.discover_services(keyword=keyword)
    
    def get_transaction_history(
        self,
        organization_code: str = None,
        limit: int = 50
    ) -> list:
        """
        Get transaction history.
        
        Args:
            organization_code: Filter by organization
            limit: Maximum results
            
        Returns:
            List of recent transactions
        """
        return self.security_server.get_transaction_logs(
            client_org_code=organization_code,
            limit=limit
        )


# Singleton instance
_message_handler: Optional[MessageHandler] = None


def get_message_handler() -> MessageHandler:
    """Get the global MessageHandler instance"""
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler()
    return _message_handler
