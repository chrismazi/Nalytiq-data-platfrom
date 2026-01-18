"""
Role-Based Access Control (RBAC) Module

Granular permission management for X-Road operations:
- Role definitions with hierarchies
- Permission assignments
- Resource-based access control
- Dynamic policy evaluation
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Set
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions for X-Road operations"""
    
    # Organization Management
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_VERIFY = "org:verify"
    ORG_SUSPEND = "org:suspend"
    
    # Subsystem Management
    SUBSYSTEM_CREATE = "subsystem:create"
    SUBSYSTEM_READ = "subsystem:read"
    SUBSYSTEM_UPDATE = "subsystem:update"
    SUBSYSTEM_DELETE = "subsystem:delete"
    
    # Service Management
    SERVICE_REGISTER = "service:register"
    SERVICE_READ = "service:read"
    SERVICE_UPDATE = "service:update"
    SERVICE_DISABLE = "service:disable"
    SERVICE_DISCOVER = "service:discover"
    
    # Access Rights
    ACCESS_GRANT = "access:grant"
    ACCESS_REVOKE = "access:revoke"
    ACCESS_READ = "access:read"
    
    # Certificate Operations
    CERT_REQUEST = "cert:request"
    CERT_READ = "cert:read"
    CERT_REVOKE = "cert:revoke"
    CERT_RENEW = "cert:renew"
    
    # Data Exchange
    EXCHANGE_EXECUTE = "exchange:execute"
    EXCHANGE_READ_LOGS = "exchange:read_logs"
    
    # Federation & Catalog
    CATALOG_REGISTER = "catalog:register"
    CATALOG_READ = "catalog:read"
    CATALOG_UPDATE = "catalog:update"
    SHARING_REQUEST = "sharing:request"
    SHARING_APPROVE = "sharing:approve"
    SHARING_REVOKE = "sharing:revoke"
    QUERY_EXECUTE = "query:execute"
    
    # Audit & Compliance
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_MANAGE = "compliance:manage"
    
    # Administration
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_SECURITY = "admin:security"


class Role(str, Enum):
    """Pre-defined system roles"""
    
    # Platform-level roles
    SUPER_ADMIN = "super_admin"           # Full system access
    PLATFORM_ADMIN = "platform_admin"     # Platform management
    SECURITY_OFFICER = "security_officer" # Security & compliance
    AUDITOR = "auditor"                   # Read-only audit access
    
    # Organization-level roles
    ORG_ADMIN = "org_admin"               # Organization administrator
    ORG_MANAGER = "org_manager"           # Organization manager
    SERVICE_ADMIN = "service_admin"       # Service management
    DATA_STEWARD = "data_steward"         # Data catalog management
    
    # Operational roles
    API_CONSUMER = "api_consumer"         # Can call services
    DATA_ANALYST = "data_analyst"         # Query and analyze
    VIEWER = "viewer"                     # Read-only access


# Default role-permission mappings
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # All permissions
    
    Role.PLATFORM_ADMIN: {
        Permission.ORG_CREATE, Permission.ORG_READ, Permission.ORG_UPDATE,
        Permission.ORG_VERIFY, Permission.ORG_SUSPEND,
        Permission.SUBSYSTEM_CREATE, Permission.SUBSYSTEM_READ, Permission.SUBSYSTEM_UPDATE,
        Permission.SERVICE_REGISTER, Permission.SERVICE_READ, Permission.SERVICE_UPDATE,
        Permission.ACCESS_GRANT, Permission.ACCESS_REVOKE, Permission.ACCESS_READ,
        Permission.CERT_REQUEST, Permission.CERT_READ, Permission.CERT_REVOKE, Permission.CERT_RENEW,
        Permission.AUDIT_READ, Permission.ADMIN_USERS, Permission.ADMIN_ROLES,
    },
    
    Role.SECURITY_OFFICER: {
        Permission.ORG_READ, Permission.SERVICE_READ, Permission.ACCESS_READ,
        Permission.CERT_READ, Permission.CERT_REVOKE,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
        Permission.COMPLIANCE_READ, Permission.COMPLIANCE_MANAGE,
        Permission.ADMIN_SECURITY,
    },
    
    Role.AUDITOR: {
        Permission.ORG_READ, Permission.SERVICE_READ, Permission.ACCESS_READ,
        Permission.CERT_READ, Permission.EXCHANGE_READ_LOGS,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
        Permission.COMPLIANCE_READ,
    },
    
    Role.ORG_ADMIN: {
        Permission.ORG_READ, Permission.ORG_UPDATE,
        Permission.SUBSYSTEM_CREATE, Permission.SUBSYSTEM_READ, Permission.SUBSYSTEM_UPDATE, Permission.SUBSYSTEM_DELETE,
        Permission.SERVICE_REGISTER, Permission.SERVICE_READ, Permission.SERVICE_UPDATE, Permission.SERVICE_DISABLE,
        Permission.ACCESS_GRANT, Permission.ACCESS_REVOKE, Permission.ACCESS_READ,
        Permission.CERT_REQUEST, Permission.CERT_READ, Permission.CERT_RENEW,
        Permission.CATALOG_REGISTER, Permission.CATALOG_READ, Permission.CATALOG_UPDATE,
        Permission.SHARING_APPROVE, Permission.SHARING_REVOKE,
        Permission.AUDIT_READ,
    },
    
    Role.ORG_MANAGER: {
        Permission.ORG_READ,
        Permission.SUBSYSTEM_READ, Permission.SUBSYSTEM_UPDATE,
        Permission.SERVICE_READ, Permission.SERVICE_UPDATE,
        Permission.ACCESS_READ,
        Permission.CERT_READ,
        Permission.CATALOG_READ, Permission.CATALOG_UPDATE,
        Permission.SHARING_APPROVE,
    },
    
    Role.SERVICE_ADMIN: {
        Permission.SERVICE_REGISTER, Permission.SERVICE_READ, Permission.SERVICE_UPDATE, Permission.SERVICE_DISABLE,
        Permission.ACCESS_GRANT, Permission.ACCESS_REVOKE, Permission.ACCESS_READ,
    },
    
    Role.DATA_STEWARD: {
        Permission.CATALOG_REGISTER, Permission.CATALOG_READ, Permission.CATALOG_UPDATE,
        Permission.SHARING_REQUEST, Permission.SHARING_APPROVE, Permission.SHARING_REVOKE,
        Permission.QUERY_EXECUTE,
    },
    
    Role.API_CONSUMER: {
        Permission.SERVICE_DISCOVER, Permission.SERVICE_READ,
        Permission.EXCHANGE_EXECUTE,
        Permission.CATALOG_READ,
        Permission.SHARING_REQUEST,
    },
    
    Role.DATA_ANALYST: {
        Permission.SERVICE_DISCOVER, Permission.SERVICE_READ,
        Permission.CATALOG_READ,
        Permission.SHARING_REQUEST,
        Permission.QUERY_EXECUTE,
    },
    
    Role.VIEWER: {
        Permission.ORG_READ, Permission.SERVICE_READ, Permission.ACCESS_READ,
        Permission.CATALOG_READ,
    },
}


class RBACManager:
    """
    Role-Based Access Control Manager.
    
    Features:
    - Role assignments per user and organization
    - Permission evaluation
    - Custom role creation
    - Audit trail for access decisions
    """
    
    RBAC_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rbac.json')
    
    def __init__(self):
        """Initialize RBAC manager"""
        self._user_roles: Dict[str, Dict] = {}  # user_id -> {roles, org_roles}
        self._custom_roles: Dict[str, Set[str]] = {}  # role_name -> permissions
        self._access_log: List[Dict] = []
        self._load_data()
        logger.info("RBACManager initialized")
    
    def _load_data(self):
        """Load RBAC data from file"""
        os.makedirs(os.path.dirname(self.RBAC_FILE), exist_ok=True)
        
        if os.path.exists(self.RBAC_FILE):
            try:
                with open(self.RBAC_FILE, 'r') as f:
                    data = json.load(f)
                    self._user_roles = data.get("user_roles", {})
                    self._custom_roles = {
                        k: set(v) for k, v in data.get("custom_roles", {}).items()
                    }
                logger.info(f"Loaded RBAC data for {len(self._user_roles)} users")
            except Exception as e:
                logger.warning(f"Failed to load RBAC data: {e}")
    
    def _save_data(self):
        """Save RBAC data to file"""
        try:
            data = {
                "user_roles": self._user_roles,
                "custom_roles": {k: list(v) for k, v in self._custom_roles.items()}
            }
            with open(self.RBAC_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save RBAC data: {e}")
    
    def assign_role(
        self,
        user_id: str,
        role: str,
        organization_code: str = None,
        assigned_by: str = None
    ) -> Dict:
        """
        Assign a role to a user.
        
        Args:
            user_id: User identifier
            role: Role to assign (from Role enum or custom)
            organization_code: Optional org scope (None = platform-wide)
            assigned_by: Who assigned the role
            
        Returns:
            Assignment result
        """
        if user_id not in self._user_roles:
            self._user_roles[user_id] = {
                "platform_roles": [],
                "org_roles": {},  # org_code -> [roles]
                "created_at": datetime.utcnow().isoformat()
            }
        
        user_data = self._user_roles[user_id]
        
        if organization_code:
            # Organization-scoped role
            if organization_code not in user_data["org_roles"]:
                user_data["org_roles"][organization_code] = []
            
            if role not in user_data["org_roles"][organization_code]:
                user_data["org_roles"][organization_code].append(role)
        else:
            # Platform-wide role
            if role not in user_data["platform_roles"]:
                user_data["platform_roles"].append(role)
        
        user_data["updated_at"] = datetime.utcnow().isoformat()
        user_data["updated_by"] = assigned_by
        
        self._save_data()
        
        logger.info(f"Role '{role}' assigned to user '{user_id}'" + 
                   (f" for org '{organization_code}'" if organization_code else ""))
        
        return {
            "success": True,
            "user_id": user_id,
            "role": role,
            "organization_code": organization_code,
            "assigned_at": user_data["updated_at"]
        }
    
    def revoke_role(
        self,
        user_id: str,
        role: str,
        organization_code: str = None,
        revoked_by: str = None
    ) -> bool:
        """Revoke a role from a user"""
        if user_id not in self._user_roles:
            return False
        
        user_data = self._user_roles[user_id]
        
        if organization_code:
            if organization_code in user_data["org_roles"]:
                if role in user_data["org_roles"][organization_code]:
                    user_data["org_roles"][organization_code].remove(role)
                    self._save_data()
                    return True
        else:
            if role in user_data["platform_roles"]:
                user_data["platform_roles"].remove(role)
                self._save_data()
                return True
        
        return False
    
    def get_user_roles(self, user_id: str, organization_code: str = None) -> List[str]:
        """Get all roles for a user"""
        if user_id not in self._user_roles:
            return []
        
        user_data = self._user_roles[user_id]
        roles = list(user_data.get("platform_roles", []))
        
        if organization_code and organization_code in user_data.get("org_roles", {}):
            roles.extend(user_data["org_roles"][organization_code])
        
        return list(set(roles))
    
    def get_user_permissions(
        self,
        user_id: str,
        organization_code: str = None
    ) -> Set[str]:
        """Get all permissions for a user based on their roles"""
        roles = self.get_user_roles(user_id, organization_code)
        permissions = set()
        
        for role_name in roles:
            # Check built-in roles
            try:
                role = Role(role_name)
                if role in ROLE_PERMISSIONS:
                    permissions.update(p.value for p in ROLE_PERMISSIONS[role])
            except ValueError:
                # Check custom roles
                if role_name in self._custom_roles:
                    permissions.update(self._custom_roles[role_name])
        
        return permissions
    
    def check_permission(
        self,
        user_id: str,
        permission: str,
        organization_code: str = None,
        resource_id: str = None
    ) -> Dict:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User identifier
            permission: Permission to check
            organization_code: Optional org context
            resource_id: Optional resource identifier
            
        Returns:
            Access decision with details
        """
        start_time = datetime.utcnow()
        
        user_permissions = self.get_user_permissions(user_id, organization_code)
        has_permission = permission in user_permissions
        
        # Log access decision
        decision = {
            "user_id": user_id,
            "permission": permission,
            "organization_code": organization_code,
            "resource_id": resource_id,
            "granted": has_permission,
            "timestamp": start_time.isoformat(),
            "roles": self.get_user_roles(user_id, organization_code)
        }
        
        self._access_log.append(decision)
        
        # Trim log
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-10000:]
        
        return {
            "allowed": has_permission,
            "permission": permission,
            "user_id": user_id,
            "roles": decision["roles"],
            "reason": "permission_granted" if has_permission else "permission_denied"
        }
    
    def create_custom_role(
        self,
        role_name: str,
        permissions: List[str],
        description: str = None,
        created_by: str = None
    ) -> Dict:
        """Create a custom role with specific permissions"""
        if role_name in [r.value for r in Role]:
            raise ValueError(f"Cannot override built-in role: {role_name}")
        
        self._custom_roles[role_name] = set(permissions)
        self._save_data()
        
        logger.info(f"Custom role '{role_name}' created with {len(permissions)} permissions")
        
        return {
            "success": True,
            "role_name": role_name,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_all_roles(self) -> Dict:
        """Get all available roles"""
        built_in = {
            role.value: {
                "type": "built_in",
                "permissions": [p.value for p in ROLE_PERMISSIONS.get(role, set())]
            }
            for role in Role
        }
        
        custom = {
            name: {
                "type": "custom",
                "permissions": list(perms)
            }
            for name, perms in self._custom_roles.items()
        }
        
        return {**built_in, **custom}
    
    def get_access_log(
        self,
        user_id: str = None,
        permission: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get access decision log"""
        log = self._access_log
        
        if user_id:
            log = [l for l in log if l["user_id"] == user_id]
        if permission:
            log = [l for l in log if l["permission"] == permission]
        
        return log[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get RBAC statistics"""
        total_users = len(self._user_roles)
        total_custom_roles = len(self._custom_roles)
        
        role_counts = {}
        for user_data in self._user_roles.values():
            for role in user_data.get("platform_roles", []):
                role_counts[role] = role_counts.get(role, 0) + 1
            for org_roles in user_data.get("org_roles", {}).values():
                for role in org_roles:
                    role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "total_users_with_roles": total_users,
            "total_custom_roles": total_custom_roles,
            "role_assignments": role_counts,
            "access_decisions_logged": len(self._access_log)
        }


# Singleton instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get the global RBACManager instance"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager
