"""
Security API Endpoints

FastAPI router for security operations:
- Role-Based Access Control
- Privacy protection
- Compliance management
- Security policies
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from security.rbac import get_rbac_manager, Permission, Role
from security.privacy import get_privacy_guard, PIIType, MaskingStrategy
from security.compliance import (
    get_compliance_manager, 
    ComplianceRegulation, 
    ConsentType, 
    DataRetentionCategory
)
from security.policies import get_security_policy, DataClassification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/security", tags=["Security & Compliance"])


# ============================================
# PYDANTIC MODELS
# ============================================

class RoleAssignment(BaseModel):
    role: str = Field(..., description="Role to assign")
    organization_code: Optional[str] = Field(None, description="Organization scope")


class CustomRole(BaseModel):
    role_name: str = Field(..., description="Custom role name")
    permissions: List[str] = Field(..., description="List of permissions")
    description: Optional[str] = Field(None, description="Role description")


class PrivacyPolicy(BaseModel):
    column_name: str = Field(..., description="Column to protect")
    pii_types: List[str] = Field(..., description="Types of PII")
    strategy: str = Field("redact", description="Masking strategy")
    config: Optional[Dict] = Field(None, description="Strategy config")


class ConsentRecord(BaseModel):
    consent_type: str = Field(..., description="Type of consent")
    purpose: str = Field(..., description="Purpose of processing")
    granted: bool = Field(..., description="Whether consent granted")
    expiry_days: int = Field(365, description="Consent validity days")


class BreachReport(BaseModel):
    description: str = Field(..., description="Breach description")
    severity: str = Field(..., description="low, medium, high, critical")
    affected_datasets: List[str] = Field(..., description="Affected dataset IDs")
    affected_subjects_count: int = Field(..., description="Number of affected subjects")
    data_categories_affected: List[str] = Field(..., description="Types of data affected")


class PasswordValidation(BaseModel):
    password: str = Field(..., description="Password to validate")
    username: Optional[str] = Field(None, description="Username to check against")


class APIKeyRequest(BaseModel):
    name: str = Field(..., description="Key name/description")
    organization_code: str = Field(..., description="Organization")
    permissions: Optional[List[str]] = Field(None, description="Key permissions")
    expires_days: Optional[int] = Field(None, description="Expiry in days")


# ============================================
# RBAC ENDPOINTS
# ============================================

@router.post("/rbac/users/{user_id}/roles")
async def assign_role(
    user_id: str,
    assignment: RoleAssignment,
    assigned_by: str = Query(None)
):
    """Assign a role to a user"""
    rbac = get_rbac_manager()
    
    result = rbac.assign_role(
        user_id=user_id,
        role=assignment.role,
        organization_code=assignment.organization_code,
        assigned_by=assigned_by
    )
    
    return result


@router.delete("/rbac/users/{user_id}/roles/{role}")
async def revoke_role(
    user_id: str,
    role: str,
    organization_code: Optional[str] = None,
    revoked_by: str = Query(None)
):
    """Revoke a role from a user"""
    rbac = get_rbac_manager()
    
    if not rbac.revoke_role(user_id, role, organization_code, revoked_by):
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    return {"success": True, "message": f"Role '{role}' revoked from user '{user_id}'"}


@router.get("/rbac/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    organization_code: Optional[str] = None
):
    """Get all roles for a user"""
    rbac = get_rbac_manager()
    roles = rbac.get_user_roles(user_id, organization_code)
    permissions = rbac.get_user_permissions(user_id, organization_code)
    
    return {
        "user_id": user_id,
        "roles": roles,
        "permissions": list(permissions)
    }


@router.get("/rbac/check")
async def check_permission(
    user_id: str,
    permission: str,
    organization_code: Optional[str] = None,
    resource_id: Optional[str] = None
):
    """Check if user has a specific permission"""
    rbac = get_rbac_manager()
    
    return rbac.check_permission(
        user_id=user_id,
        permission=permission,
        organization_code=organization_code,
        resource_id=resource_id
    )


@router.post("/rbac/roles/custom")
async def create_custom_role(
    role: CustomRole,
    created_by: str = Query(None)
):
    """Create a custom role with specific permissions"""
    rbac = get_rbac_manager()
    
    try:
        return rbac.create_custom_role(
            role_name=role.role_name,
            permissions=role.permissions,
            description=role.description,
            created_by=created_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rbac/roles")
async def list_all_roles():
    """List all available roles (built-in and custom)"""
    rbac = get_rbac_manager()
    return rbac.get_all_roles()


@router.get("/rbac/permissions")
async def list_all_permissions():
    """List all available permissions"""
    return {
        "permissions": [
            {"code": p.value, "category": p.value.split(":")[0]}
            for p in Permission
        ]
    }


@router.get("/rbac/statistics")
async def get_rbac_statistics():
    """Get RBAC statistics"""
    rbac = get_rbac_manager()
    return rbac.get_statistics()


# ============================================
# PRIVACY ENDPOINTS
# ============================================

@router.post("/privacy/scan/{dataset_id}")
async def scan_dataset_for_pii(dataset_id: str, schema: Dict = Body(...)):
    """Scan a dataset schema for potential PII"""
    privacy = get_privacy_guard()
    detected = privacy.scan_schema(schema)
    
    return {
        "dataset_id": dataset_id,
        "pii_detected": detected,
        "columns_with_pii": len(detected)
    }


@router.post("/privacy/policies/{dataset_id}")
async def set_privacy_policy(
    dataset_id: str,
    policy: PrivacyPolicy
):
    """Set privacy policy for a dataset column"""
    privacy = get_privacy_guard()
    
    try:
        pii_types = [PIIType(t) for t in policy.pii_types]
        strategy = MaskingStrategy(policy.strategy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {e}")
    
    privacy.set_policy(
        dataset_id=dataset_id,
        column_name=policy.column_name,
        pii_types=pii_types,
        strategy=strategy,
        config=policy.config
    )
    
    return {
        "success": True,
        "message": f"Privacy policy set for {dataset_id}.{policy.column_name}"
    }


@router.post("/privacy/auto-configure/{dataset_id}")
async def auto_configure_privacy(
    dataset_id: str,
    schema: Dict = Body(...),
    default_strategy: str = "redact"
):
    """Auto-configure privacy policies based on schema scan"""
    privacy = get_privacy_guard()
    
    try:
        strategy = MaskingStrategy(default_strategy)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {default_strategy}")
    
    return privacy.auto_configure_policies(dataset_id, schema, strategy)


@router.get("/privacy/policies/{dataset_id}")
async def get_dataset_privacy_policies(dataset_id: str):
    """Get all privacy policies for a dataset"""
    privacy = get_privacy_guard()
    return {
        "dataset_id": dataset_id,
        "policies": privacy.get_dataset_policies(dataset_id)
    }


@router.get("/privacy/report")
async def get_privacy_report(dataset_id: Optional[str] = None):
    """Get privacy operations report"""
    privacy = get_privacy_guard()
    return privacy.get_privacy_report(dataset_id)


# ============================================
# COMPLIANCE ENDPOINTS
# ============================================

@router.post("/compliance/consent/{subject_id}")
async def record_consent(
    subject_id: str,
    consent: ConsentRecord,
    organization_code: str = Query(None),
    collected_by: str = Query(None)
):
    """Record consent from a data subject"""
    compliance = get_compliance_manager()
    
    try:
        consent_type = ConsentType(consent.consent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid consent type: {consent.consent_type}")
    
    return compliance.record_consent(
        subject_id=subject_id,
        consent_type=consent_type,
        purpose=consent.purpose,
        granted=consent.granted,
        expiry_days=consent.expiry_days,
        organization_code=organization_code,
        collected_by=collected_by
    )


@router.post("/compliance/consent/{subject_id}/{consent_id}/withdraw")
async def withdraw_consent(
    subject_id: str,
    consent_id: str,
    reason: Optional[str] = None
):
    """Withdraw a previously granted consent"""
    compliance = get_compliance_manager()
    
    if not compliance.withdraw_consent(subject_id, consent_id, reason):
        raise HTTPException(status_code=404, detail="Consent not found")
    
    return {"success": True, "message": "Consent withdrawn"}


@router.get("/compliance/consent/check")
async def check_consent(
    subject_id: str,
    consent_type: str,
    organization_code: Optional[str] = None
):
    """Check if valid consent exists"""
    compliance = get_compliance_manager()
    
    try:
        ct = ConsentType(consent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid consent type: {consent_type}")
    
    return compliance.check_consent(subject_id, ct, organization_code)


@router.get("/compliance/consent/{subject_id}")
async def get_subject_consents(subject_id: str):
    """Get all consent records for a subject"""
    compliance = get_compliance_manager()
    return {
        "subject_id": subject_id,
        "consents": compliance.get_subject_consents(subject_id)
    }


@router.post("/compliance/retention/{dataset_id}")
async def set_retention_policy(
    dataset_id: str,
    category: str,
    regulation: str,
    justification: Optional[str] = None
):
    """Set data retention policy for a dataset"""
    compliance = get_compliance_manager()
    
    try:
        cat = DataRetentionCategory(category)
        reg = ComplianceRegulation(regulation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return compliance.set_retention_policy(dataset_id, cat, reg, justification)


@router.post("/compliance/breach")
async def report_breach(
    breach: BreachReport,
    detected_by: str,
    organization_code: Optional[str] = None
):
    """Report a data breach incident"""
    compliance = get_compliance_manager()
    
    return compliance.report_breach(
        description=breach.description,
        severity=breach.severity,
        affected_datasets=breach.affected_datasets,
        affected_subjects_count=breach.affected_subjects_count,
        data_categories_affected=breach.data_categories_affected,
        detected_by=detected_by,
        organization_code=organization_code
    )


@router.get("/compliance/report")
async def generate_compliance_report(
    regulation: Optional[str] = None,
    organization_code: Optional[str] = None,
    days: int = 30
):
    """Generate a compliance report"""
    compliance = get_compliance_manager()
    
    reg = None
    if regulation:
        try:
            reg = ComplianceRegulation(regulation)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid regulation: {regulation}")
    
    end_date = datetime.utcnow()
    start_date = end_date - __import__('datetime').timedelta(days=days)
    
    return compliance.generate_compliance_report(
        regulation=reg,
        organization_code=organization_code,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/compliance/statistics")
async def get_compliance_statistics():
    """Get compliance statistics"""
    compliance = get_compliance_manager()
    return compliance.get_statistics()


# ============================================
# SECURITY POLICY ENDPOINTS
# ============================================

@router.post("/policies/password/validate")
async def validate_password(validation: PasswordValidation):
    """Validate a password against security policy"""
    policy = get_security_policy()
    return policy.validate_password(validation.password, validation.username)


@router.post("/policies/api-keys")
async def generate_api_key(request: APIKeyRequest):
    """Generate a new API key"""
    policy = get_security_policy()
    
    return policy.generate_api_key(
        name=request.name,
        organization_code=request.organization_code,
        permissions=request.permissions,
        expires_days=request.expires_days
    )


@router.post("/policies/api-keys/validate")
async def validate_api_key(api_key: str = Body(..., embed=True)):
    """Validate an API key"""
    policy = get_security_policy()
    return policy.validate_api_key(api_key)


@router.delete("/policies/api-keys/{key_id}")
async def revoke_api_key(key_id: str, reason: Optional[str] = None):
    """Revoke an API key"""
    policy = get_security_policy()
    
    if not policy.revoke_api_key(key_id, reason):
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "message": "API key revoked"}


@router.post("/policies/ip/block")
async def block_ip(
    ip_address: str,
    reason: str,
    duration_hours: int = 24,
    blocked_by: Optional[str] = None
):
    """Block an IP address"""
    policy = get_security_policy()
    policy.block_ip(ip_address, reason, duration_hours, blocked_by)
    
    return {"success": True, "message": f"IP {ip_address} blocked for {duration_hours} hours"}


@router.get("/policies/ip/check/{ip_address}")
async def check_ip_blocked(ip_address: str):
    """Check if an IP is blocked"""
    policy = get_security_policy()
    return policy.is_ip_blocked(ip_address)


@router.delete("/policies/ip/block/{ip_address}")
async def unblock_ip(ip_address: str):
    """Unblock an IP address"""
    policy = get_security_policy()
    
    if not policy.unblock_ip(ip_address):
        raise HTTPException(status_code=404, detail="IP not in block list")
    
    return {"success": True, "message": f"IP {ip_address} unblocked"}


@router.get("/policies")
async def get_all_policies():
    """Get all security policies"""
    policy = get_security_policy()
    return policy.get_all_policies()


@router.put("/policies/password")
async def update_password_policy(updates: Dict = Body(...)):
    """Update password policy"""
    policy = get_security_policy()
    return policy.update_password_policy(updates)


@router.put("/policies/session")
async def update_session_policy(updates: Dict = Body(...)):
    """Update session policy"""
    policy = get_security_policy()
    return policy.update_session_policy(updates)


@router.put("/policies/api")
async def update_api_policy(updates: Dict = Body(...)):
    """Update API policy"""
    policy = get_security_policy()
    return policy.update_api_policy(updates)


@router.get("/policies/events")
async def get_security_events(
    event_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    limit: int = 100
):
    """Get security events"""
    policy = get_security_policy()
    return {
        "events": policy.get_security_events(event_type, ip_address, limit)
    }
