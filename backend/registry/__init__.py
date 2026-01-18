"""
Registry Module

Organization and service registry for R-NDIP X-Road:
- Organization management
- Subsystem management
- Service registration
- Access rights management
"""

from .organization_registry import OrganizationRegistry, get_organization_registry
from .service_registry import ServiceRegistry, get_service_registry
from .access_rights import AccessRightsManager, get_access_rights_manager

__all__ = [
    'OrganizationRegistry',
    'get_organization_registry',
    'ServiceRegistry', 
    'get_service_registry',
    'AccessRightsManager',
    'get_access_rights_manager'
]
