"""
Database Models for Production

SQLAlchemy ORM models for all platform entities.
Includes proper indexing, constraints, and relationships.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

Base = declarative_base()


# ============================================
# ENUMS
# ============================================

class OrganizationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class ServiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class AccessLevel(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class ConsentStatus(str, enum.Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    DENIED = "denied"


# ============================================
# USER & AUTH MODELS
# ============================================

class User(Base):
    """Platform user"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    last_login = Column(DateTime)
    password_changed_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    role_assignments = relationship("UserRoleAssignment", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )


class UserSession(Base):
    """User session for tracking logins"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    token_hash = Column(String(255), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=True)
    
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_info = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="sessions")


# ============================================
# RBAC MODELS
# ============================================

class Role(Base):
    """System roles"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    permissions = Column(JSON, default=list)  # List of permission strings
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    assignments = relationship("UserRoleAssignment", back_populates="role")


class UserRoleAssignment(Base):
    """User role assignments (can be scoped to organization)"""
    __tablename__ = "user_role_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="role_assignments")
    role = relationship("Role", back_populates="assignments")
    
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "organization_id", name="uq_user_role_org"),
        Index("ix_role_assignments_user", "user_id"),
    )


# ============================================
# X-ROAD MODELS
# ============================================

class Organization(Base):
    """X-Road member organization"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    member_class = Column(String(50), default="GOV")
    member_type = Column(String(50))
    description = Column(Text)
    
    status = Column(SQLEnum(OrganizationStatus), default=OrganizationStatus.PENDING)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Contact info
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    website = Column(String(255))
    address = Column(Text)
    
    # Technical info
    security_server_url = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    subsystems = relationship("Subsystem", back_populates="organization")
    services = relationship("Service", back_populates="organization")
    certificates = relationship("Certificate", back_populates="organization")
    datasets = relationship("Dataset", back_populates="organization")


class Subsystem(Base):
    """Organization subsystem"""
    __tablename__ = "subsystems"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    code = Column(String(50), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="subsystems")
    services = relationship("Service", back_populates="subsystem")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_org_subsystem"),
    )


class Service(Base):
    """X-Road service"""
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    subsystem_id = Column(UUID(as_uuid=True), ForeignKey("subsystems.id"), nullable=True)
    
    code = Column(String(100), nullable=False)
    name = Column(String(255))
    version = Column(String(20), default="v1")
    description = Column(Text)
    
    status = Column(SQLEnum(ServiceStatus), default=ServiceStatus.DRAFT)
    
    # Service details
    service_type = Column(String(50))  # REST, SOAP, etc.
    endpoint_url = Column(String(500))
    openapi_url = Column(String(500))
    wsdl_url = Column(String(500))
    
    # Rate limits
    rate_limit = Column(Integer, default=100)
    timeout_seconds = Column(Integer, default=30)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="services")
    subsystem = relationship("Subsystem", back_populates="services")
    access_rights = relationship("AccessRight", back_populates="service")
    
    __table_args__ = (
        Index("ix_services_org_code", "organization_id", "code"),
    )


class AccessRight(Base):
    """Service access rights"""
    __tablename__ = "access_rights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    client_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    client_subsystem_id = Column(UUID(as_uuid=True), ForeignKey("subsystems.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    service = relationship("Service", back_populates="access_rights")


class Certificate(Base):
    """X.509 certificates"""
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    certificate_type = Column(String(50))  # signing, authentication
    subject = Column(String(500))
    issuer = Column(String(500))
    serial_number = Column(String(100))
    fingerprint_sha256 = Column(String(64), unique=True)
    
    not_before = Column(DateTime)
    not_after = Column(DateTime)
    
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    
    certificate_pem = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="certificates")


# ============================================
# DATA FEDERATION MODELS
# ============================================

class Dataset(Base):
    """Federated dataset catalog"""
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    data_type = Column(String(50))  # statistics, registry, survey, etc.
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.INTERNAL)
    
    # Schema and metadata
    schema_definition = Column(JSON)
    tags = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    
    # Statistics
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    
    # Temporal coverage
    temporal_start = Column(DateTime, nullable=True)
    temporal_end = Column(DateTime, nullable=True)
    update_frequency = Column(String(50))  # daily, weekly, monthly, etc.
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)
    completeness = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="datasets")
    shares = relationship("DatasetShare", back_populates="dataset")
    
    __table_args__ = (
        Index("ix_datasets_org", "organization_id"),
        Index("ix_datasets_type_access", "data_type", "access_level"),
    )


class DatasetShare(Base):
    """Dataset sharing agreements"""
    __tablename__ = "dataset_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    requester_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    status = Column(String(50), default="pending")  # pending, approved, rejected, revoked
    
    purpose = Column(Text)
    justification = Column(Text)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    requested_by = Column(UUID(as_uuid=True), nullable=True)
    
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    
    dataset = relationship("Dataset", back_populates="shares")


# ============================================
# COMPLIANCE MODELS
# ============================================

class Consent(Base):
    """Data subject consent records"""
    __tablename__ = "consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(String(255), nullable=False, index=True)
    
    consent_type = Column(String(50), nullable=False)  # data_processing, data_sharing, etc.
    purpose = Column(Text, nullable=False)
    
    status = Column(SQLEnum(ConsentStatus), default=ConsentStatus.ACTIVE)
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    collected_at = Column(DateTime, default=datetime.utcnow)
    collected_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    withdrawn_at = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("ix_consents_subject_type", "subject_id", "consent_type"),
    )


class DataProcessingRecord(Base):
    """GDPR Article 30 processing records"""
    __tablename__ = "data_processing_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    activity_type = Column(String(100), nullable=False)
    purpose = Column(Text, nullable=False)
    legal_basis = Column(String(100))
    
    data_categories = Column(JSON, default=list)
    recipients = Column(JSON, default=list)
    
    cross_border_transfer = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)


class DataBreach(Base):
    """Data breach incidents"""
    __tablename__ = "data_breaches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    affected_datasets = Column(JSON, default=list)
    affected_subjects_count = Column(Integer, default=0)
    data_categories_affected = Column(JSON, default=list)
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    detected_by = Column(UUID(as_uuid=True), nullable=True)
    
    status = Column(String(50), default="open")
    notification_deadline = Column(DateTime)
    
    authority_notified = Column(Boolean, default=False)
    authority_notified_at = Column(DateTime, nullable=True)
    
    subjects_notified = Column(Boolean, default=False)
    
    remediation_steps = Column(JSON, default=list)
    closed_at = Column(DateTime, nullable=True)


# ============================================
# AUDIT MODELS
# ============================================

class AuditLog(Base):
    """Comprehensive audit logging"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Action
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    
    # Details
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_body = Column(JSON)
    
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Outcome
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Correlation
    correlation_id = Column(String(36), index=True)
    
    __table_args__ = (
        Index("ix_audit_timestamp_action", "timestamp", "action"),
        Index("ix_audit_user", "user_id", "timestamp"),
        Index("ix_audit_org", "organization_id", "timestamp"),
    )


# ============================================
# ML MODELS
# ============================================

class MLModel(Base):
    """Machine learning model registry"""
    __tablename__ = "ml_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    
    model_type = Column(String(100))  # regression, classification, clustering, etc.
    algorithm = Column(String(100))
    
    # Training info
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    trained_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow)
    training_duration_seconds = Column(Integer)
    
    # Metrics
    metrics = Column(JSON)
    hyperparameters = Column(JSON)
    feature_importance = Column(JSON)
    
    # Storage
    model_path = Column(String(500))
    model_size_bytes = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_production = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_version"),
    )


class MLPrediction(Base):
    """ML prediction logs"""
    __tablename__ = "ml_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=False)
    
    input_data = Column(JSON)
    prediction = Column(JSON)
    confidence = Column(Float)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    predicted_at = Column(DateTime, default=datetime.utcnow)
    prediction_time_ms = Column(Integer)
