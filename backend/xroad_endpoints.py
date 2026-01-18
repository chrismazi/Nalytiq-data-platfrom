"""
X-Road API Endpoints

FastAPI router for X-Road functionality:
- Organization management
- Service registry
- Certificate operations
- Data exchange
- Audit logs
"""

from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from datetime import datetime
import logging

from xroad.models import (
    OrganizationCreate, OrganizationUpdate, Organization,
    SubsystemCreate, Subsystem,
    ServiceCreate, Service, ServiceStatus,
    ServiceAccessRightCreate,
    CertificateCreate,
    XRoadRequest
)
from xroad.protocol import XRoadProtocol
from xroad.message_handler import get_message_handler
from xroad.security_server import get_security_server
from registry.organization_registry import get_organization_registry
from registry.service_registry import get_service_registry
from registry.access_rights import get_access_rights_manager
from pki.certificate_manager import get_certificate_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/xroad", tags=["X-Road"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ============================================
# ORGANIZATION ENDPOINTS
# ============================================

@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def register_organization(org_data: OrganizationCreate):
    """
    Register a new organization in the X-Road network.
    
    The organization will be in 'pending' status until verified.
    """
    try:
        registry = get_organization_registry()
        org = registry.register_organization(org_data)
        return {
            "success": True,
            "message": "Organization registered successfully",
            "organization": org
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Organization registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/organizations")
async def list_organizations(
    status: Optional[str] = None,
    member_class: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List registered organizations with optional filters."""
    from xroad.models import OrganizationStatus, MemberClass
    
    registry = get_organization_registry()
    
    org_status = OrganizationStatus(status) if status else None
    org_class = MemberClass(member_class) if member_class else None
    
    organizations = registry.list_organizations(
        status=org_status,
        member_class=org_class,
        search=search,
        limit=limit,
        offset=offset
    )
    
    return {
        "organizations": organizations,
        "count": len(organizations),
        "limit": limit,
        "offset": offset
    }


@router.get("/organizations/{org_id}")
async def get_organization(org_id: str):
    """Get organization details by ID."""
    registry = get_organization_registry()
    org = registry.get_organization(org_id)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org


@router.get("/organizations/code/{org_code}")
async def get_organization_by_code(org_code: str):
    """Get organization by code (e.g., RW-GOV-NISR)."""
    registry = get_organization_registry()
    org = registry.get_organization_by_code(org_code)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org


@router.put("/organizations/{org_id}")
async def update_organization(org_id: str, update_data: OrganizationUpdate):
    """Update organization details."""
    registry = get_organization_registry()
    org = registry.update_organization(org_id, update_data)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "success": True,
        "message": "Organization updated",
        "organization": org
    }


@router.post("/organizations/{org_id}/verify")
async def verify_organization(org_id: str, verified_by: str = "admin"):
    """Verify an organization (activate it in the network)."""
    registry = get_organization_registry()
    cert_manager = get_certificate_manager()
    
    # Get organization
    org = registry.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Issue certificate
    try:
        cert = cert_manager.request_certificate(
            organization_id=org_id,
            organization_code=org["code"],
            organization_name=org["name"],
            certificate_type="signing"
        )
        
        # Verify organization
        org = registry.verify_organization(
            org_id=org_id,
            verified_by=verified_by,
            certificate_id=cert["id"]
        )
        
        return {
            "success": True,
            "message": "Organization verified and certificate issued",
            "organization": org,
            "certificate": {
                "id": cert["id"],
                "fingerprint": cert["fingerprint"],
                "valid_until": cert["valid_until"]
            }
        }
    except Exception as e:
        logger.error(f"Organization verification failed: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(org_id: str, reason: str = None):
    """Suspend an organization."""
    registry = get_organization_registry()
    org = registry.suspend_organization(org_id, reason)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "success": True,
        "message": "Organization suspended",
        "organization": org
    }


# ============================================
# SUBSYSTEM ENDPOINTS
# ============================================

@router.post("/organizations/{org_id}/subsystems", status_code=status.HTTP_201_CREATED)
async def create_subsystem(org_id: str, subsystem_data: SubsystemCreate):
    """Create a subsystem for an organization."""
    try:
        registry = get_organization_registry()
        subsystem = registry.create_subsystem(org_id, subsystem_data)
        return {
            "success": True,
            "message": "Subsystem created",
            "subsystem": subsystem
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/{org_id}/subsystems")
async def list_subsystems(org_id: str):
    """List subsystems for an organization."""
    registry = get_organization_registry()
    subsystems = registry.list_subsystems(org_id)
    return {
        "subsystems": subsystems,
        "count": len(subsystems)
    }


# ============================================
# SERVICE REGISTRY ENDPOINTS
# ============================================

@router.post("/subsystems/{subsystem_id}/services", status_code=status.HTTP_201_CREATED)
async def register_service(subsystem_id: str, service_data: ServiceCreate):
    """Register a new service in a subsystem."""
    org_registry = get_organization_registry()
    svc_registry = get_service_registry()
    
    # Get subsystem
    subsystem = org_registry.get_subsystem(subsystem_id)
    if not subsystem:
        raise HTTPException(status_code=404, detail="Subsystem not found")
    
    try:
        service = svc_registry.register_service(
            subsystem_id=subsystem_id,
            subsystem_code=subsystem["code"],
            organization_code=subsystem["organization_code"],
            service_data=service_data
        )
        return {
            "success": True,
            "message": "Service registered",
            "service": service
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/services")
async def list_services(
    organization_code: Optional[str] = None,
    service_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List registered services with filters."""
    from xroad.models import ServiceType, ServiceStatus
    
    registry = get_service_registry()
    
    svc_type = ServiceType(service_type) if service_type else None
    svc_status = ServiceStatus(status) if status else None
    
    services = registry.list_services(
        organization_code=organization_code,
        service_type=svc_type,
        status=svc_status,
        search=search,
        limit=limit,
        offset=offset
    )
    
    return {
        "services": services,
        "count": len(services),
        "limit": limit,
        "offset": offset
    }


@router.get("/services/discover")
async def discover_services(keyword: Optional[str] = None):
    """Discover available services (public API)."""
    registry = get_service_registry()
    services = registry.discover_services(keyword=keyword)
    return {
        "services": services,
        "count": len(services)
    }


@router.get("/services/{service_id}")
async def get_service(service_id: str):
    """Get service details."""
    registry = get_service_registry()
    service = registry.get_service(service_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service


# ============================================
# ACCESS RIGHTS ENDPOINTS
# ============================================

@router.post("/services/{service_id}/access-rights", status_code=status.HTTP_201_CREATED)
async def grant_access(
    service_id: str,
    access_data: ServiceAccessRightCreate,
    granted_by: str = "admin"
):
    """Grant access to a service for a client subsystem."""
    svc_registry = get_service_registry()
    org_registry = get_organization_registry()
    access_manager = get_access_rights_manager()
    
    # Get service
    service = svc_registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get client subsystem
    client_subsystem = org_registry.get_subsystem(access_data.client_subsystem_id)
    if not client_subsystem:
        raise HTTPException(status_code=404, detail="Client subsystem not found")
    
    access_right = access_manager.grant_access(
        service_id=service_id,
        service_code=service["service_code"],
        provider_org_code=service["organization_code"],
        client_subsystem_id=access_data.client_subsystem_id,
        client_org_code=client_subsystem["organization_code"],
        client_subsystem_code=client_subsystem["code"],
        granted_by=granted_by,
        expires_at=access_data.expires_at,
        access_type=access_data.access_type
    )
    
    return {
        "success": True,
        "message": "Access granted",
        "access_right": access_right
    }


@router.get("/services/{service_id}/access-rights")
async def get_service_access_rights(service_id: str):
    """Get all access rights for a service."""
    access_manager = get_access_rights_manager()
    rights = access_manager.get_service_access_rights(service_id)
    return {
        "access_rights": rights,
        "count": len(rights)
    }


@router.delete("/access-rights/{access_right_id}")
async def revoke_access(access_right_id: str):
    """Revoke an access right."""
    access_manager = get_access_rights_manager()
    
    if not access_manager.revoke_access(access_right_id):
        raise HTTPException(status_code=404, detail="Access right not found")
    
    return {
        "success": True,
        "message": "Access revoked"
    }


# ============================================
# DATA EXCHANGE ENDPOINTS
# ============================================

@router.post("/exchange")
async def exchange_data(request_data: dict = Body(...)):
    """
    Execute an X-Road data exchange request.
    
    This is the main endpoint for inter-organization data exchange.
    """
    handler = get_message_handler()
    response = handler.handle_request(request_data)
    
    if response.get("error_code"):
        raise HTTPException(
            status_code=response.get("status_code", 400),
            detail=response.get("error_message")
        )
    
    return response


@router.post("/exchange/call")
async def call_service(
    client_org: str,
    client_subsystem: str,
    target_org: str,
    target_subsystem: str,
    service_code: str,
    service_version: str = "v1",
    method: str = "GET",
    path: str = "/",
    body: dict = None
):
    """
    Simplified service call endpoint.
    
    Convenience endpoint for making X-Road service calls.
    """
    handler = get_message_handler()
    
    response = handler.create_service_call(
        client_org=client_org,
        client_subsystem=client_subsystem,
        target_org=target_org,
        target_subsystem=target_subsystem,
        service_code=service_code,
        service_version=service_version,
        method=method,
        path=path,
        body=body
    )
    
    return response


# ============================================
# CERTIFICATE ENDPOINTS
# ============================================

@router.get("/certificates")
async def list_certificates(
    organization_code: Optional[str] = None,
    status: Optional[str] = None
):
    """List certificates with filters."""
    cert_manager = get_certificate_manager()
    
    certs = cert_manager.get_organization_certificates(
        organization_code=organization_code,
        status=status
    )
    
    return {
        "certificates": certs,
        "count": len(certs)
    }


@router.get("/certificates/expiring")
async def get_expiring_certificates(days: int = 30):
    """Get certificates expiring within specified days."""
    cert_manager = get_certificate_manager()
    certs = cert_manager.get_expiring_certificates(days)
    
    return {
        "expiring_within_days": days,
        "certificates": certs,
        "count": len(certs)
    }


@router.post("/certificates/{cert_id}/renew")
async def renew_certificate(cert_id: str, validity_days: int = None):
    """Renew a certificate."""
    cert_manager = get_certificate_manager()
    
    new_cert = cert_manager.renew_certificate(cert_id, validity_days)
    
    if not new_cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {
        "success": True,
        "message": "Certificate renewed",
        "certificate": {
            "id": new_cert["id"],
            "fingerprint": new_cert["fingerprint"],
            "valid_until": new_cert["valid_until"]
        }
    }


# ============================================
# AUDIT & MONITORING ENDPOINTS
# ============================================

@router.get("/transactions")
async def get_transactions(
    client_org_code: Optional[str] = None,
    service_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get transaction logs."""
    from xroad.models import TransactionStatus
    
    server = get_security_server()
    
    tx_status = TransactionStatus(status) if status else None
    
    transactions = server.get_transaction_logs(
        client_org_code=client_org_code,
        service_code=service_code,
        status=tx_status,
        limit=limit
    )
    
    return {
        "transactions": transactions,
        "count": len(transactions)
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get a specific transaction log."""
    server = get_security_server()
    tx = server.get_transaction_log(transaction_id)
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return tx


@router.get("/status")
async def get_xroad_status():
    """Get X-Road security server status."""
    server = get_security_server()
    return server.get_server_status()


@router.get("/statistics")
async def get_statistics():
    """Get comprehensive X-Road statistics."""
    org_registry = get_organization_registry()
    svc_registry = get_service_registry()
    access_manager = get_access_rights_manager()
    cert_manager = get_certificate_manager()
    
    return {
        "organizations": org_registry.get_statistics(),
        "services": svc_registry.get_statistics(),
        "access_rights": access_manager.get_statistics(),
        "certificates": cert_manager.get_certificate_stats()
    }
