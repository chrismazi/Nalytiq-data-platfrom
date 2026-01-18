"""
X-Road Data Models

Pydantic models for X-Road entities including:
- Organizations (Members)
- Subsystems
- Services
- Certificates
- Transactions
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
import uuid


# ============================================
# ENUMS
# ============================================

class MemberClass(str, Enum):
    """Classification of X-Road members"""
    GOV = "GOV"       # Government organizations
    COM = "COM"       # Commercial/Private sector
    NGO = "NGO"       # Non-governmental organizations
    EDU = "EDU"       # Educational institutions
    INT = "INT"       # International organizations


class OrganizationStatus(str, Enum):
    """Status of an organization in the X-Road network"""
    PENDING = "pending"           # Awaiting verification
    ACTIVE = "active"             # Fully operational
    SUSPENDED = "suspended"       # Temporarily disabled
    REVOKED = "revoked"           # Permanently disabled


class ServiceType(str, Enum):
    """Type of service exposed through X-Road"""
    REST = "REST"
    SOAP = "SOAP"
    GRAPHQL = "GRAPHQL"


class ServiceStatus(str, Enum):
    """Status of a registered service"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class CertificateType(str, Enum):
    """Types of X-Road certificates"""
    SIGNING = "signing"         # For digital signatures
    AUTH = "auth"               # For TLS client authentication
    TLS = "tls"                 # For TLS server
    ROOT_CA = "root_ca"         # Certificate Authority root


class CertificateStatus(str, Enum):
    """Status of a certificate"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class TransactionStatus(str, Enum):
    """Status of an X-Road transaction"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


class AccessType(str, Enum):
    """Access control type"""
    ALLOW = "allow"
    DENY = "deny"


# ============================================
# ORGANIZATION MODELS
# ============================================

class OrganizationCreate(BaseModel):
    """Model for creating a new organization"""
    code: str = Field(..., min_length=3, max_length=50, 
                      description="Unique organization code, e.g., RW-GOV-NISR")
    name: str = Field(..., min_length=3, max_length=255,
                      description="Full organization name")
    member_class: MemberClass = Field(..., description="Organization classification")
    contact_email: EmailStr = Field(..., description="Primary contact email")
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "code": "RW-GOV-NISR",
                "name": "National Institute of Statistics of Rwanda",
                "member_class": "GOV",
                "contact_email": "admin@statistics.gov.rw",
                "contact_phone": "+250788123456",
                "address": "KN 1 Rd, Kigali, Rwanda",
                "website": "https://statistics.gov.rw",
                "description": "National statistics authority of Rwanda"
            }
        }


class OrganizationUpdate(BaseModel):
    """Model for updating an organization"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None


class Organization(BaseModel):
    """Complete organization model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    member_class: MemberClass
    status: OrganizationStatus = OrganizationStatus.PENDING
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    certificate_id: Optional[str] = None
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# SUBSYSTEM MODELS
# ============================================

class SubsystemCreate(BaseModel):
    """Model for creating a subsystem within an organization"""
    code: str = Field(..., min_length=2, max_length=100,
                      description="Subsystem code, e.g., 'analytics', 'census'")
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    api_base_url: Optional[str] = Field(None, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "code": "analytics",
                "name": "Analytics Platform",
                "description": "Data analytics and ML platform",
                "api_base_url": "https://api.nisr.gov.rw/analytics"
            }
        }


class Subsystem(BaseModel):
    """Complete subsystem model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    code: str
    name: str
    description: Optional[str] = None
    api_base_url: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# SERVICE MODELS
# ============================================

class ServiceCreate(BaseModel):
    """Model for registering a new service"""
    service_code: str = Field(..., min_length=2, max_length=100,
                              description="Unique service identifier")
    service_version: str = Field(default="v1", max_length=20)
    service_type: ServiceType = ServiceType.REST
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    openapi_spec: Optional[Dict[str, Any]] = None
    wsdl_url: Optional[str] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000,
                                      description="Requests per minute limit")
    timeout_ms: int = Field(default=60000, ge=1000, le=300000)

    class Config:
        json_schema_extra = {
            "example": {
                "service_code": "population-stats",
                "service_version": "v1",
                "service_type": "REST",
                "title": "Population Statistics API",
                "description": "Real-time population statistics by district and province",
                "rate_limit": 100,
                "timeout_ms": 30000
            }
        }


class Service(BaseModel):
    """Complete service model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subsystem_id: str
    service_code: str
    service_version: str
    service_type: ServiceType
    title: str
    description: Optional[str] = None
    openapi_spec: Optional[Dict[str, Any]] = None
    wsdl_url: Optional[str] = None
    status: ServiceStatus = ServiceStatus.ACTIVE
    rate_limit: Optional[int] = None
    timeout_ms: int = 60000
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# ACCESS RIGHTS MODELS
# ============================================

class ServiceAccessRightCreate(BaseModel):
    """Model for granting service access"""
    client_subsystem_id: str = Field(..., description="Subsystem requesting access")
    access_type: AccessType = AccessType.ALLOW
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "client_subsystem_id": "uuid-of-client-subsystem",
                "access_type": "allow",
                "expires_at": "2027-01-01T00:00:00Z"
            }
        }


class ServiceAccessRight(BaseModel):
    """Complete access right model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    client_subsystem_id: str
    access_type: AccessType
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# CERTIFICATE MODELS
# ============================================

class CertificateCreate(BaseModel):
    """Model for requesting a certificate"""
    certificate_type: CertificateType
    common_name: str = Field(..., min_length=3, max_length=255)
    validity_days: int = Field(default=365, ge=30, le=3650)

    class Config:
        json_schema_extra = {
            "example": {
                "certificate_type": "signing",
                "common_name": "NISR Analytics Signing Certificate",
                "validity_days": 730
            }
        }


class Certificate(BaseModel):
    """Complete certificate model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    certificate_type: CertificateType
    subject: str
    issuer: str
    serial_number: str
    valid_from: datetime
    valid_until: datetime
    public_key: str
    fingerprint: str
    status: CertificateStatus = CertificateStatus.ACTIVE
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# TRANSACTION/AUDIT MODELS
# ============================================

class TransactionLog(BaseModel):
    """Model for X-Road transaction logging"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Client info
    client_org_id: str
    client_org_code: str
    client_subsystem_id: str
    client_subsystem_code: str
    
    # Service info
    service_org_id: str
    service_org_code: str
    service_id: str
    service_code: str
    service_version: str
    
    # Request details
    request_method: str
    request_path: str
    request_size_bytes: int
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Response details
    response_timestamp: Optional[datetime] = None
    response_size_bytes: Optional[int] = None
    response_status_code: Optional[int] = None
    
    # Security
    message_hash: Optional[str] = None
    signature: Optional[str] = None
    timestamped_at: Optional[datetime] = None
    
    # Metadata
    status: TransactionStatus = TransactionStatus.SUCCESS
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    client_ip: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================
# X-ROAD MESSAGE MODELS
# ============================================

class XRoadClientId(BaseModel):
    """X-Road client identifier"""
    instance: str = Field(default="RW", description="X-Road instance, e.g., RW for Rwanda")
    member_class: MemberClass
    member_code: str  # Organization code
    subsystem_code: str

    def __str__(self):
        return f"{self.instance}/{self.member_class.value}/{self.member_code}/{self.subsystem_code}"


class XRoadServiceId(BaseModel):
    """X-Road service identifier"""
    instance: str = Field(default="RW")
    member_class: MemberClass
    member_code: str
    subsystem_code: str
    service_code: str
    service_version: str = "v1"

    def __str__(self):
        return f"{self.instance}/{self.member_class.value}/{self.member_code}/{self.subsystem_code}/{self.service_code}/{self.service_version}"


class XRoadRequest(BaseModel):
    """X-Road request structure"""
    client: XRoadClientId
    service: XRoadServiceId
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_version: str = "4.0"
    request_hash: Optional[str] = None
    request_hash_algorithm: str = "SHA-256"
    
    # HTTP-like request
    method: str = "GET"
    path: str = "/"
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "client": {
                    "instance": "RW",
                    "member_class": "GOV",
                    "member_code": "RW-GOV-NISR",
                    "subsystem_code": "analytics"
                },
                "service": {
                    "instance": "RW",
                    "member_class": "GOV",
                    "member_code": "RW-GOV-MINECOFIN",
                    "subsystem_code": "budget",
                    "service_code": "budget-data",
                    "service_version": "v1"
                },
                "method": "GET",
                "path": "/budgets/2024"
            }
        }


class XRoadResponse(BaseModel):
    """X-Road response structure"""
    request_id: str
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    
    # Security
    response_hash: Optional[str] = None
    signature: Optional[str] = None
    
    # Timing
    request_timestamp: datetime
    response_timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    
    # Errors
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# ============================================
# SHARED DATASET MODELS (Federation)
# ============================================

class DataCategory(str, Enum):
    """Categories of shared data"""
    CENSUS = "census"
    HEALTH = "health"
    EDUCATION = "education"
    ECONOMIC = "economic"
    AGRICULTURE = "agriculture"
    ENVIRONMENT = "environment"
    INFRASTRUCTURE = "infrastructure"
    SOCIAL = "social"
    OTHER = "other"


class AccessLevel(str, Enum):
    """Data access levels"""
    PUBLIC = "public"           # Anyone can access
    RESTRICTED = "restricted"   # Requires approval
    CONFIDENTIAL = "confidential"  # Strict access control


class SharedDatasetCreate(BaseModel):
    """Model for sharing a dataset"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    data_category: DataCategory
    access_level: AccessLevel = AccessLevel.RESTRICTED
    schema_definition: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = Field(None, max_length=100)
    update_frequency: Optional[str] = None  # daily, weekly, monthly, yearly

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rwanda Census 2024",
                "description": "Complete population census data for Rwanda",
                "data_category": "census",
                "access_level": "restricted",
                "tags": ["population", "demographics", "2024"],
                "license": "CC-BY-4.0",
                "update_frequency": "yearly"
            }
        }


class SharedDataset(BaseModel):
    """Complete shared dataset model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_org_id: str
    owner_org_code: str
    name: str
    description: Optional[str] = None
    data_category: DataCategory
    access_level: AccessLevel
    schema_definition: Optional[Dict[str, Any]] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    last_updated: Optional[datetime] = None
    update_frequency: Optional[str] = None
    quality_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class DatasetAccessRequestCreate(BaseModel):
    """Model for requesting access to a dataset"""
    purpose: str = Field(..., min_length=10, max_length=2000,
                         description="Justification for data access")
    intended_use: Optional[str] = Field(None, max_length=1000)
    duration_days: int = Field(default=365, ge=1, le=3650)


class DatasetAccessRequest(BaseModel):
    """Complete dataset access request model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dataset_id: str
    requesting_org_id: str
    requesting_org_code: str
    purpose: str
    intended_use: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
