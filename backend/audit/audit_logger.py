"""
Audit Logger Module

Comprehensive audit logging for X-Road transactions:
- Transaction logging
- Security event logging
- Operation logging (CRUD, auth, etc.)
- Non-repudiation support
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
import uuid
import hashlib

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Transaction events
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth_login_success"
    AUTH_LOGIN_FAILED = "auth_login_failed"
    AUTH_LOGOUT = "auth_logout"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    
    # Organization events
    ORG_REGISTERED = "org_registered"
    ORG_VERIFIED = "org_verified"
    ORG_SUSPENDED = "org_suspended"
    ORG_UPDATED = "org_updated"
    
    # Service events
    SERVICE_REGISTERED = "service_registered"
    SERVICE_UPDATED = "service_updated"
    SERVICE_DISABLED = "service_disabled"
    
    # Access rights events
    ACCESS_GRANTED = "access_granted"
    ACCESS_REVOKED = "access_revoked"
    ACCESS_DENIED = "access_denied"
    
    # Certificate events
    CERT_ISSUED = "cert_issued"
    CERT_REVOKED = "cert_revoked"
    CERT_RENEWED = "cert_renewed"
    CERT_EXPIRED = "cert_expired"
    
    # Security events
    SECURITY_SIGNATURE_VERIFIED = "security_signature_verified"
    SECURITY_SIGNATURE_FAILED = "security_signature_failed"
    SECURITY_ENCRYPTION = "security_encryption"
    SECURITY_DECRYPTION = "security_decryption"
    
    # Data events
    DATA_ACCESSED = "data_accessed"
    DATA_SHARED = "data_shared"
    DATA_EXPORT = "data_export"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEntry:
    """Represents a single audit log entry"""
    
    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        actor_id: str = None,
        actor_type: str = None,  # user, organization, system
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        details: Dict = None,
        client_ip: str = None,
        request_id: str = None,
        transaction_id: str = None,
        organization_code: str = None
    ):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.severity = severity
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.details = details or {}
        self.client_ip = client_ip
        self.request_id = request_id
        self.transaction_id = transaction_id
        self.organization_code = organization_code
        
        # Compute hash for non-repudiation
        self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of the entry for integrity"""
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "client_ip": self.client_ip,
            "request_id": self.request_id,
            "transaction_id": self.transaction_id,
            "organization_code": self.organization_code,
            "hash": self.hash
        }


class AuditLogger:
    """
    Central audit logging service.
    
    Features:
    - Structured logging
    - Non-repudiation hashing
    - Query capabilities
    - Export for compliance
    """
    
    AUDIT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'audit_log.jsonl')
    
    def __init__(self):
        """Initialize audit logger"""
        self._entries: List[Dict] = []
        self._load_logs()
        logger.info("AuditLogger initialized")
    
    def _load_logs(self):
        """Load existing audit logs"""
        os.makedirs(os.path.dirname(self.AUDIT_FILE), exist_ok=True)
        
        if os.path.exists(self.AUDIT_FILE):
            try:
                with open(self.AUDIT_FILE, 'r') as f:
                    for line in f:
                        if line.strip():
                            self._entries.append(json.loads(line))
                logger.info(f"Loaded {len(self._entries)} audit entries")
            except Exception as e:
                logger.warning(f"Failed to load audit logs: {e}")
    
    def _save_entry(self, entry: Dict):
        """Append entry to audit log file"""
        try:
            with open(self.AUDIT_FILE, 'a') as f:
                f.write(json.dumps(entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save audit entry: {e}")
    
    def log(self, entry: AuditEntry) -> str:
        """
        Log an audit entry.
        
        Args:
            entry: AuditEntry to log
            
        Returns:
            Entry ID
        """
        entry_dict = entry.to_dict()
        self._entries.append(entry_dict)
        self._save_entry(entry_dict)
        
        # Also log to standard logger
        log_msg = f"[AUDIT] {entry.event_type.value}: {entry.action or ''}"
        if entry.severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif entry.severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        return entry.id
    
    def log_transaction(
        self,
        transaction_id: str,
        client_org: str,
        service_code: str,
        status: str,
        duration_ms: int = None,
        error: str = None,
        request_id: str = None
    ) -> str:
        """Log a transaction event"""
        event_type = (
            AuditEventType.TRANSACTION_COMPLETED if status == "success"
            else AuditEventType.TRANSACTION_FAILED
        )
        severity = AuditSeverity.INFO if status == "success" else AuditSeverity.ERROR
        
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            actor_id=client_org,
            actor_type="organization",
            resource_type="service",
            resource_id=service_code,
            action=f"Transaction {status}",
            transaction_id=transaction_id,
            request_id=request_id,
            organization_code=client_org,
            details={
                "duration_ms": duration_ms,
                "error": error
            }
        )
        
        return self.log(entry)
    
    def log_auth(
        self,
        user_id: str,
        event_type: AuditEventType,
        client_ip: str = None,
        details: Dict = None
    ) -> str:
        """Log an authentication event"""
        severity = (
            AuditSeverity.WARNING 
            if event_type == AuditEventType.AUTH_LOGIN_FAILED 
            else AuditSeverity.INFO
        )
        
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            actor_id=user_id,
            actor_type="user",
            action=event_type.value,
            client_ip=client_ip,
            details=details or {}
        )
        
        return self.log(entry)
    
    def log_organization(
        self,
        org_code: str,
        event_type: AuditEventType,
        actor_id: str = None,
        details: Dict = None
    ) -> str:
        """Log an organization event"""
        entry = AuditEntry(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            actor_id=actor_id,
            actor_type="user",
            resource_type="organization",
            resource_id=org_code,
            action=event_type.value,
            organization_code=org_code,
            details=details or {}
        )
        
        return self.log(entry)
    
    def log_access(
        self,
        client_org: str,
        service_code: str,
        provider_org: str,
        event_type: AuditEventType,
        actor_id: str = None,
        details: Dict = None
    ) -> str:
        """Log an access control event"""
        severity = (
            AuditSeverity.WARNING 
            if event_type == AuditEventType.ACCESS_DENIED 
            else AuditSeverity.INFO
        )
        
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_type="user",
            resource_type="service",
            resource_id=service_code,
            action=f"{client_org} -> {provider_org}/{service_code}",
            organization_code=client_org,
            details=details or {}
        )
        
        return self.log(entry)
    
    def log_security(
        self,
        event_type: AuditEventType,
        success: bool,
        organization_code: str = None,
        details: Dict = None
    ) -> str:
        """Log a security event"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            action=f"{'Success' if success else 'Failed'}: {event_type.value}",
            organization_code=organization_code,
            details=details or {}
        )
        
        return self.log(entry)
    
    def log_error(
        self,
        error_message: str,
        error_type: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None
    ) -> str:
        """Log a system error"""
        entry = AuditEntry(
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=AuditSeverity.ERROR,
            resource_type=resource_type,
            resource_id=resource_id,
            action=error_message,
            details={
                "error_type": error_type,
                **(details or {})
            }
        )
        
        return self.log(entry)
    
    def query(
        self,
        event_type: AuditEventType = None,
        severity: AuditSeverity = None,
        organization_code: str = None,
        actor_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Query audit logs with filters.
        
        Args:
            event_type: Filter by event type
            severity: Filter by severity
            organization_code: Filter by organization
            actor_id: Filter by actor
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Skip first N results
            
        Returns:
            List of matching audit entries
        """
        results = []
        
        for entry in self._entries:
            # Apply filters
            if event_type and entry.get("event_type") != event_type.value:
                continue
            if severity and entry.get("severity") != severity.value:
                continue
            if organization_code and entry.get("organization_code") != organization_code:
                continue
            if actor_id and entry.get("actor_id") != actor_id:
                continue
            
            if start_date:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time < start_date:
                    continue
            
            if end_date:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > end_date:
                    continue
            
            results.append(entry)
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results[offset:offset + limit]
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Get specific audit entry by ID"""
        for entry in self._entries:
            if entry.get("id") == entry_id:
                return entry
        return None
    
    def verify_integrity(self, entry_id: str) -> Dict:
        """
        Verify the integrity of an audit entry.
        
        Args:
            entry_id: Entry ID to verify
            
        Returns:
            Verification result
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return {"valid": False, "error": "Entry not found"}
        
        # Recompute hash
        data = {
            "id": entry["id"],
            "timestamp": entry["timestamp"],
            "event_type": entry["event_type"],
            "actor_id": entry.get("actor_id"),
            "resource_id": entry.get("resource_id"),
            "action": entry.get("action"),
            "details": entry.get("details", {})
        }
        canonical = json.dumps(data, sort_keys=True)
        computed_hash = hashlib.sha256(canonical.encode()).hexdigest()
        
        if computed_hash == entry.get("hash"):
            return {
                "valid": True,
                "message": "Entry integrity verified"
            }
        else:
            return {
                "valid": False,
                "error": "Hash mismatch - entry may have been tampered with"
            }
    
    def get_statistics(self) -> Dict:
        """Get audit log statistics"""
        stats = {
            "total_entries": len(self._entries),
            "by_event_type": {},
            "by_severity": {},
            "by_organization": {},
            "recent_errors": 0
        }
        
        recent_cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for entry in self._entries:
            # By event type
            et = entry.get("event_type", "unknown")
            stats["by_event_type"][et] = stats["by_event_type"].get(et, 0) + 1
            
            # By severity
            sev = entry.get("severity", "unknown")
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
            
            # By organization
            org = entry.get("organization_code")
            if org:
                stats["by_organization"][org] = stats["by_organization"].get(org, 0) + 1
            
            # Recent errors
            if entry.get("severity") in ["error", "critical"]:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= recent_cutoff:
                    stats["recent_errors"] += 1
        
        return stats
    
    def export_for_compliance(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_code: str = None
    ) -> List[Dict]:
        """
        Export audit logs for compliance reporting.
        
        Args:
            start_date: Start of period
            end_date: End of period
            organization_code: Optional organization filter
            
        Returns:
            List of audit entries for the period
        """
        return self.query(
            organization_code=organization_code,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Higher limit for exports
        )


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global AuditLogger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
