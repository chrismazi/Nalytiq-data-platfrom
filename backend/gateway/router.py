"""
Service Router Module

Routes requests to target services:
- Service resolution
- URL construction
- HTTP method mapping
- Header transformation
"""

import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

from registry.service_registry import get_service_registry
from registry.organization_registry import get_organization_registry

logger = logging.getLogger(__name__)


class ServiceRouter:
    """
    Routes requests to target X-Road services.
    
    Features:
    - Service endpoint resolution
    - Request forwarding
    - Response handling
    - Timeout management
    """
    
    DEFAULT_TIMEOUT = 30.0  # seconds
    
    def __init__(self):
        """Initialize service router"""
        self.service_registry = get_service_registry()
        self.org_registry = get_organization_registry()
        self._client: Optional[httpx.AsyncClient] = None
        logger.info("ServiceRouter initialized")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.DEFAULT_TIMEOUT),
                follow_redirects=True
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def resolve_service_url(
        self,
        organization_code: str,
        subsystem_code: str,
        service_code: str,
        service_version: str = None,
        path: str = "/"
    ) -> Optional[str]:
        """
        Resolve the full URL for a service.
        
        Args:
            organization_code: Target organization
            subsystem_code: Target subsystem
            service_code: Service code
            service_version: Optional version
            path: Request path within the service
            
        Returns:
            Full URL or None if not found
        """
        # Get service
        service = self.service_registry.get_service_by_code(
            organization_code=organization_code,
            subsystem_code=subsystem_code,
            service_code=service_code,
            version=service_version
        )
        
        if not service:
            logger.warning(f"Service not found: {organization_code}/{subsystem_code}/{service_code}")
            return None
        
        # Get subsystem for base URL
        subsystem = self.org_registry.get_subsystem_by_code(
            organization_code,
            subsystem_code
        )
        
        if not subsystem or not subsystem.get("api_base_url"):
            logger.warning(f"Subsystem or API base URL not found: {subsystem_code}")
            return None
        
        # Construct full URL
        base_url = subsystem["api_base_url"].rstrip("/")
        service_path = f"/{service_code}"
        if service_version:
            service_path += f"/{service_version}"
        
        full_path = path.lstrip("/") if path != "/" else ""
        
        return f"{base_url}{service_path}/{full_path}".rstrip("/")
    
    async def forward_request(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        body: Any = None,
        timeout: float = None
    ) -> Dict:
        """
        Forward a request to the target service.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            body: Request body
            timeout: Request timeout
            
        Returns:
            Response dictionary with status, headers, body
        """
        client = await self._get_client()
        start_time = datetime.utcnow()
        
        try:
            # Prepare headers
            request_headers = {
                "Content-Type": "application/json",
                "X-Request-Time": start_time.isoformat(),
                **(headers or {})
            }
            
            # Make request
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                json=body if body and method.upper() in ["POST", "PUT", "PATCH"] else None,
                params=body if body and method.upper() == "GET" else None,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse response
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
                "duration_ms": duration_ms
            }
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {url}")
            return {
                "success": False,
                "status_code": 504,
                "error": "Gateway Timeout",
                "message": f"Request to {url} timed out"
            }
            
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {url} - {e}")
            return {
                "success": False,
                "status_code": 503,
                "error": "Service Unavailable",
                "message": f"Could not connect to service at {url}"
            }
            
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return {
                "success": False,
                "status_code": 500,
                "error": "Internal Error",
                "message": str(e)
            }
    
    async def route_request(
        self,
        organization_code: str,
        subsystem_code: str,
        service_code: str,
        service_version: str = None,
        method: str = "GET",
        path: str = "/",
        headers: Dict[str, str] = None,
        body: Any = None
    ) -> Dict:
        """
        Route a request to the target service.
        
        This is the main routing method that combines resolution and forwarding.
        
        Args:
            organization_code: Target organization
            subsystem_code: Target subsystem
            service_code: Service code
            service_version: Optional version
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            
        Returns:
            Routing result
        """
        # Resolve URL
        url = self.resolve_service_url(
            organization_code=organization_code,
            subsystem_code=subsystem_code,
            service_code=service_code,
            service_version=service_version,
            path=path
        )
        
        if not url:
            return {
                "success": False,
                "status_code": 404,
                "error": "Service Not Found",
                "message": f"Could not resolve service: {organization_code}/{subsystem_code}/{service_code}"
            }
        
        # Forward request
        return await self.forward_request(
            url=url,
            method=method,
            headers=headers,
            body=body
        )
    
    def get_service_health(
        self,
        organization_code: str,
        subsystem_code: str,
        service_code: str
    ) -> Dict:
        """Get health status of a service"""
        service = self.service_registry.get_service_by_code(
            organization_code=organization_code,
            subsystem_code=subsystem_code,
            service_code=service_code
        )
        
        if not service:
            return {"status": "unknown", "message": "Service not found"}
        
        return service.get("health", {"status": "unknown"})


# Singleton instance
_service_router: Optional[ServiceRouter] = None


def get_service_router() -> ServiceRouter:
    """Get the global ServiceRouter instance"""
    global _service_router
    if _service_router is None:
        _service_router = ServiceRouter()
    return _service_router
