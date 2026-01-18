"""
Service Registry Module

Manages X-Road services:
- Service registration
- Service discovery
- Service metadata management
- Service health monitoring
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from xroad.models import (
    Service, ServiceCreate, ServiceStatus, ServiceType
)

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Registry for X-Road services.
    
    Manages:
    - Service registration
    - Service discovery
    - Service metadata
    - Service versioning
    """
    
    REGISTRY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'services.json')
    
    def __init__(self):
        """Initialize service registry"""
        self._services: Dict[str, Dict] = {}
        self._load_data()
        logger.info("ServiceRegistry initialized")
    
    def _load_data(self):
        """Load registry data from file"""
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        
        if os.path.exists(self.REGISTRY_FILE):
            try:
                with open(self.REGISTRY_FILE, 'r') as f:
                    self._services = json.load(f)
                logger.info(f"Loaded {len(self._services)} services")
            except Exception as e:
                logger.warning(f"Failed to load services: {e}")
    
    def _save_data(self):
        """Save registry data to file"""
        try:
            with open(self.REGISTRY_FILE, 'w') as f:
                json.dump(self._services, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save services: {e}")
    
    def register_service(
        self,
        subsystem_id: str,
        subsystem_code: str,
        organization_code: str,
        service_data: ServiceCreate
    ) -> Dict:
        """
        Register a new service.
        
        Args:
            subsystem_id: ID of the subsystem
            subsystem_code: Code of the subsystem
            organization_code: Code of the organization
            service_data: Service creation data
            
        Returns:
            Created service data
            
        Raises:
            ValueError: If service already exists
        """
        # Check for duplicate
        for svc in self._services.values():
            if (svc["subsystem_id"] == subsystem_id and 
                svc["service_code"] == service_data.service_code and
                svc["service_version"] == service_data.service_version):
                raise ValueError(
                    f"Service '{service_data.service_code}' version '{service_data.service_version}' "
                    f"already exists in subsystem"
                )
        
        # Create service
        service_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        service = {
            "id": service_id,
            "subsystem_id": subsystem_id,
            "subsystem_code": subsystem_code,
            "organization_code": organization_code,
            "service_code": service_data.service_code,
            "service_version": service_data.service_version,
            "service_type": service_data.service_type.value,
            "title": service_data.title,
            "description": service_data.description,
            "openapi_spec": service_data.openapi_spec,
            "wsdl_url": service_data.wsdl_url,
            "status": ServiceStatus.ACTIVE.value,
            "rate_limit": service_data.rate_limit,
            "timeout_ms": service_data.timeout_ms,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "health": {
                "status": "unknown",
                "last_check": None,
                "success_rate": None
            }
        }
        
        self._services[service_id] = service
        self._save_data()
        
        logger.info(f"Service registered: {organization_code}/{subsystem_code}/{service_data.service_code}")
        return service
    
    def get_service(self, service_id: str) -> Optional[Dict]:
        """Get service by ID"""
        return self._services.get(service_id)
    
    def get_service_by_code(
        self,
        organization_code: str,
        subsystem_code: str,
        service_code: str,
        version: str = None
    ) -> Optional[Dict]:
        """
        Get service by identifying codes.
        
        Args:
            organization_code: Organization code
            subsystem_code: Subsystem code
            service_code: Service code
            version: Optional version (latest if not specified)
            
        Returns:
            Service data or None
        """
        matching = []
        
        for svc in self._services.values():
            if (svc["organization_code"] == organization_code and
                svc["subsystem_code"] == subsystem_code and
                svc["service_code"] == service_code):
                if version and svc["service_version"] != version:
                    continue
                matching.append(svc)
        
        if not matching:
            return None
        
        # Return specific version or latest
        if version:
            return matching[0]
        else:
            # Sort by version and return latest
            matching.sort(key=lambda x: x["service_version"], reverse=True)
            return matching[0]
    
    def update_service(
        self,
        service_id: str,
        title: str = None,
        description: str = None,
        openapi_spec: Dict = None,
        rate_limit: int = None,
        timeout_ms: int = None
    ) -> Optional[Dict]:
        """Update service details"""
        if service_id not in self._services:
            return None
        
        svc = self._services[service_id]
        
        if title is not None:
            svc["title"] = title
        if description is not None:
            svc["description"] = description
        if openapi_spec is not None:
            svc["openapi_spec"] = openapi_spec
        if rate_limit is not None:
            svc["rate_limit"] = rate_limit
        if timeout_ms is not None:
            svc["timeout_ms"] = timeout_ms
        
        svc["updated_at"] = datetime.utcnow().isoformat()
        
        self._services[service_id] = svc
        self._save_data()
        
        return svc
    
    def set_service_status(self, service_id: str, status: ServiceStatus) -> Optional[Dict]:
        """Set service status (active, deprecated, disabled)"""
        if service_id not in self._services:
            return None
        
        svc = self._services[service_id]
        svc["status"] = status.value
        svc["updated_at"] = datetime.utcnow().isoformat()
        
        self._services[service_id] = svc
        self._save_data()
        
        logger.info(f"Service status changed: {svc['service_code']} -> {status.value}")
        return svc
    
    def list_services(
        self,
        organization_code: str = None,
        subsystem_id: str = None,
        service_type: ServiceType = None,
        status: ServiceStatus = None,
        search: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List services with filters.
        
        Args:
            organization_code: Filter by organization
            subsystem_id: Filter by subsystem
            service_type: Filter by type (REST, SOAP)
            status: Filter by status
            search: Search in title or code
            limit: Maximum results
            offset: Skip first N results
            
        Returns:
            List of matching services
        """
        results = []
        
        for svc in self._services.values():
            # Apply filters
            if organization_code and svc["organization_code"] != organization_code:
                continue
            if subsystem_id and svc["subsystem_id"] != subsystem_id:
                continue
            if service_type and svc["service_type"] != service_type.value:
                continue
            if status and svc["status"] != status.value:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in svc["service_code"].lower() and
                    search_lower not in svc["title"].lower() and
                    search_lower not in (svc.get("description") or "").lower()):
                    continue
            
            results.append(svc)
        
        # Sort by organization, subsystem, service
        results.sort(key=lambda x: (x["organization_code"], x["subsystem_code"], x["service_code"]))
        
        return results[offset:offset + limit]
    
    def discover_services(
        self,
        category: str = None,
        keyword: str = None
    ) -> List[Dict]:
        """
        Discover available services (public discovery).
        
        Args:
            category: Filter by category tag
            keyword: Search keyword
            
        Returns:
            List of discoverable services
        """
        results = []
        
        for svc in self._services.values():
            # Only show active services
            if svc["status"] != ServiceStatus.ACTIVE.value:
                continue
            
            # Apply category filter (if we had categories)
            # Apply keyword filter
            if keyword:
                keyword_lower = keyword.lower()
                if (keyword_lower not in svc["service_code"].lower() and
                    keyword_lower not in svc["title"].lower() and
                    keyword_lower not in (svc.get("description") or "").lower()):
                    continue
            
            # Return limited info for discovery
            results.append({
                "organization_code": svc["organization_code"],
                "subsystem_code": svc["subsystem_code"],
                "service_code": svc["service_code"],
                "service_version": svc["service_version"],
                "service_type": svc["service_type"],
                "title": svc["title"],
                "description": svc["description"]
            })
        
        return results
    
    def update_health(
        self,
        service_id: str,
        status: str,
        success_rate: float = None
    ):
        """
        Update service health status.
        
        Args:
            service_id: Service ID
            status: Health status (healthy, unhealthy, unknown)
            success_rate: Request success rate (0-1)
        """
        if service_id not in self._services:
            return
        
        svc = self._services[service_id]
        svc["health"] = {
            "status": status,
            "last_check": datetime.utcnow().isoformat(),
            "success_rate": success_rate
        }
        
        self._services[service_id] = svc
        self._save_data()
    
    def delete_service(self, service_id: str) -> bool:
        """Delete a service"""
        if service_id not in self._services:
            return False
        
        svc = self._services[service_id]
        del self._services[service_id]
        self._save_data()
        
        logger.info(f"Service deleted: {svc['service_code']}")
        return True
    
    def get_statistics(self) -> Dict:
        """Get service registry statistics"""
        stats = {
            "total": len(self._services),
            "by_status": {},
            "by_type": {},
            "by_organization": {}
        }
        
        for svc in self._services.values():
            status = svc["status"]
            svc_type = svc["service_type"]
            org = svc["organization_code"]
            
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_type"][svc_type] = stats["by_type"].get(svc_type, 0) + 1
            stats["by_organization"][org] = stats["by_organization"].get(org, 0) + 1
        
        return stats


# Singleton instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global ServiceRegistry instance"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry
