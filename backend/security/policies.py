"""
Security Policies Module

Configurable security policies for platform operations:
- Password policies
- Session management
- API security
- Network security
- Data classification
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import re
import hashlib
import secrets

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"               # Freely available
    INTERNAL = "internal"           # Organization internal
    CONFIDENTIAL = "confidential"   # Limited access
    RESTRICTED = "restricted"       # Highly restricted
    TOP_SECRET = "top_secret"       # Maximum protection


class SecurityLevel(str, Enum):
    """Security enforcement levels"""
    LENIENT = "lenient"
    STANDARD = "standard"
    STRICT = "strict"
    MAXIMUM = "maximum"


# Default security configurations
DEFAULT_PASSWORD_POLICY = {
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special": True,
    "special_characters": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "max_age_days": 90,
    "history_count": 5,  # Cannot reuse last 5 passwords
    "lockout_threshold": 5,
    "lockout_duration_minutes": 30
}

DEFAULT_SESSION_POLICY = {
    "max_session_duration_hours": 8,
    "idle_timeout_minutes": 30,
    "max_concurrent_sessions": 3,
    "require_mfa_for_sensitive": True,
    "session_binding": ["ip", "user_agent"]
}

DEFAULT_API_POLICY = {
    "rate_limit_per_minute": 100,
    "rate_limit_burst": 20,
    "require_https": True,
    "allowed_origins": ["*"],
    "max_request_size_mb": 10,
    "request_timeout_seconds": 30,
    "require_api_key": True,
    "api_key_rotation_days": 90
}


class SecurityPolicy:
    """
    Configurable security policy manager.
    
    Features:
    - Password strength validation
    - Session security policies
    - API security settings
    - Data classification rules
    - Security event logging
    """
    
    POLICY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_policies.json')
    
    def __init__(self):
        """Initialize SecurityPolicy"""
        self._password_policy = DEFAULT_PASSWORD_POLICY.copy()
        self._session_policy = DEFAULT_SESSION_POLICY.copy()
        self._api_policy = DEFAULT_API_POLICY.copy()
        self._classification_rules: Dict[str, Dict] = {}
        self._security_events: List[Dict] = []
        self._blocked_ips: Dict[str, Dict] = {}
        self._api_keys: Dict[str, Dict] = {}
        self._load_policies()
        logger.info("SecurityPolicy initialized")
    
    def _load_policies(self):
        """Load policies from file"""
        os.makedirs(os.path.dirname(self.POLICY_FILE), exist_ok=True)
        
        if os.path.exists(self.POLICY_FILE):
            try:
                with open(self.POLICY_FILE, 'r') as f:
                    data = json.load(f)
                    self._password_policy.update(data.get("password_policy", {}))
                    self._session_policy.update(data.get("session_policy", {}))
                    self._api_policy.update(data.get("api_policy", {}))
                    self._classification_rules = data.get("classification_rules", {})
                    self._blocked_ips = data.get("blocked_ips", {})
                    self._api_keys = data.get("api_keys", {})
            except Exception as e:
                logger.warning(f"Failed to load security policies: {e}")
    
    def _save_policies(self):
        """Save policies to file"""
        try:
            data = {
                "password_policy": self._password_policy,
                "session_policy": self._session_policy,
                "api_policy": self._api_policy,
                "classification_rules": self._classification_rules,
                "blocked_ips": self._blocked_ips,
                "api_keys": self._api_keys
            }
            with open(self.POLICY_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save security policies: {e}")
    
    # ==========================================
    # PASSWORD POLICIES
    # ==========================================
    
    def validate_password(self, password: str, username: str = None) -> Dict:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
            username: Optional username to check against
            
        Returns:
            Validation result with details
        """
        policy = self._password_policy
        issues = []
        
        # Length check
        if len(password) < policy["min_length"]:
            issues.append(f"Password must be at least {policy['min_length']} characters")
        
        # Uppercase check
        if policy["require_uppercase"] and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if policy["require_lowercase"] and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        # Digit check
        if policy["require_digits"] and not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        # Special character check
        if policy["require_special"]:
            special_chars = policy["special_characters"]
            if not any(c in special_chars for c in password):
                issues.append(f"Password must contain at least one special character ({special_chars})")
        
        # Username check
        if username and username.lower() in password.lower():
            issues.append("Password cannot contain username")
        
        # Common passwords check (simplified)
        common_patterns = ["password", "123456", "qwerty", "admin", "letmein"]
        for pattern in common_patterns:
            if pattern in password.lower():
                issues.append("Password contains common weak pattern")
                break
        
        # Calculate strength score
        score = 0
        if len(password) >= policy["min_length"]:
            score += 20
        if re.search(r'[A-Z]', password):
            score += 20
        if re.search(r'[a-z]', password):
            score += 20
        if re.search(r'\d', password):
            score += 20
        if any(c in policy["special_characters"] for c in password):
            score += 20
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength_score": score,
            "strength": "weak" if score < 40 else "medium" if score < 80 else "strong"
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return f"{salt}${hashed}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, stored_hash = hashed.split('$')
            computed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            ).hex()
            return secrets.compare_digest(computed, stored_hash)
        except:
            return False
    
    # ==========================================
    # SESSION POLICIES
    # ==========================================
    
    def validate_session(
        self,
        session_id: str,
        created_at: datetime,
        last_activity: datetime,
        ip_address: str = None,
        user_agent: str = None,
        stored_ip: str = None,
        stored_ua: str = None
    ) -> Dict:
        """
        Validate a session against policy.
        
        Returns:
            Session validity status
        """
        policy = self._session_policy
        now = datetime.utcnow()
        issues = []
        
        # Check session age
        max_duration = timedelta(hours=policy["max_session_duration_hours"])
        if now - created_at > max_duration:
            issues.append("Session has exceeded maximum duration")
        
        # Check idle timeout
        idle_timeout = timedelta(minutes=policy["idle_timeout_minutes"])
        if now - last_activity > idle_timeout:
            issues.append("Session has exceeded idle timeout")
        
        # Check session binding
        if "ip" in policy["session_binding"]:
            if stored_ip and ip_address and stored_ip != ip_address:
                issues.append("Session IP address mismatch")
        
        if "user_agent" in policy["session_binding"]:
            if stored_ua and user_agent and stored_ua != user_agent:
                issues.append("Session user agent mismatch")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expires_in_seconds": max(
                0,
                int((created_at + max_duration - now).total_seconds())
            )
        }
    
    # ==========================================
    # API SECURITY
    # ==========================================
    
    def generate_api_key(
        self,
        name: str,
        organization_code: str,
        permissions: List[str] = None,
        expires_days: int = None
    ) -> Dict:
        """Generate a new API key"""
        key_id = secrets.token_urlsafe(8)
        key_secret = secrets.token_urlsafe(32)
        
        expires_days = expires_days or self._api_policy["api_key_rotation_days"]
        
        key_data = {
            "id": key_id,
            "name": name,
            "organization_code": organization_code,
            "permissions": permissions or [],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
            "last_used": None,
            "usage_count": 0,
            "status": "active",
            "key_hash": self.hash_password(key_secret)
        }
        
        self._api_keys[key_id] = key_data
        self._save_policies()
        
        # Return full key only once
        return {
            "key_id": key_id,
            "api_key": f"{key_id}.{key_secret}",
            "expires_at": key_data["expires_at"],
            "message": "Save this API key securely - it cannot be retrieved again"
        }
    
    def validate_api_key(self, api_key: str) -> Dict:
        """Validate an API key"""
        try:
            key_id, key_secret = api_key.split('.', 1)
        except ValueError:
            return {"valid": False, "reason": "invalid_format"}
        
        if key_id not in self._api_keys:
            return {"valid": False, "reason": "key_not_found"}
        
        key_data = self._api_keys[key_id]
        
        # Check status
        if key_data["status"] != "active":
            return {"valid": False, "reason": f"key_{key_data['status']}"}
        
        # Check expiry
        expires = datetime.fromisoformat(key_data["expires_at"])
        if datetime.utcnow() > expires:
            key_data["status"] = "expired"
            self._save_policies()
            return {"valid": False, "reason": "key_expired"}
        
        # Verify key
        if not self.verify_password(key_secret, key_data["key_hash"]):
            return {"valid": False, "reason": "invalid_key"}
        
        # Update usage
        key_data["last_used"] = datetime.utcnow().isoformat()
        key_data["usage_count"] += 1
        self._save_policies()
        
        return {
            "valid": True,
            "key_id": key_id,
            "organization_code": key_data["organization_code"],
            "permissions": key_data["permissions"]
        }
    
    def revoke_api_key(self, key_id: str, reason: str = None) -> bool:
        """Revoke an API key"""
        if key_id not in self._api_keys:
            return False
        
        self._api_keys[key_id]["status"] = "revoked"
        self._api_keys[key_id]["revoked_at"] = datetime.utcnow().isoformat()
        self._api_keys[key_id]["revoke_reason"] = reason
        self._save_policies()
        
        logger.info(f"API key revoked: {key_id}")
        return True
    
    # ==========================================
    # IP BLOCKING
    # ==========================================
    
    def block_ip(
        self,
        ip_address: str,
        reason: str,
        duration_hours: int = 24,
        blocked_by: str = None
    ):
        """Block an IP address"""
        self._blocked_ips[ip_address] = {
            "blocked_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat(),
            "reason": reason,
            "blocked_by": blocked_by
        }
        self._save_policies()
        
        self._log_security_event(
            event_type="ip_blocked",
            ip_address=ip_address,
            details={"reason": reason, "duration_hours": duration_hours}
        )
    
    def is_ip_blocked(self, ip_address: str) -> Dict:
        """Check if an IP is blocked"""
        if ip_address not in self._blocked_ips:
            return {"blocked": False}
        
        block_info = self._blocked_ips[ip_address]
        expires = datetime.fromisoformat(block_info["expires_at"])
        
        if datetime.utcnow() > expires:
            del self._blocked_ips[ip_address]
            self._save_policies()
            return {"blocked": False}
        
        return {
            "blocked": True,
            "reason": block_info["reason"],
            "expires_at": block_info["expires_at"]
        }
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP address"""
        if ip_address in self._blocked_ips:
            del self._blocked_ips[ip_address]
            self._save_policies()
            return True
        return False
    
    # ==========================================
    # SECURITY EVENTS
    # ==========================================
    
    def _log_security_event(
        self,
        event_type: str,
        ip_address: str = None,
        user_id: str = None,
        details: Dict = None
    ):
        """Log a security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "ip_address": ip_address,
            "user_id": user_id,
            "details": details or {}
        }
        
        self._security_events.append(event)
        
        # Trim events
        if len(self._security_events) > 10000:
            self._security_events = self._security_events[-10000:]
    
    def get_security_events(
        self,
        event_type: str = None,
        ip_address: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get security events"""
        events = self._security_events
        
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        if ip_address:
            events = [e for e in events if e["ip_address"] == ip_address]
        
        return events[-limit:]
    
    # ==========================================
    # POLICY MANAGEMENT
    # ==========================================
    
    def update_password_policy(self, updates: Dict) -> Dict:
        """Update password policy"""
        allowed_keys = set(DEFAULT_PASSWORD_POLICY.keys())
        
        for key, value in updates.items():
            if key in allowed_keys:
                self._password_policy[key] = value
        
        self._save_policies()
        return self._password_policy
    
    def update_session_policy(self, updates: Dict) -> Dict:
        """Update session policy"""
        allowed_keys = set(DEFAULT_SESSION_POLICY.keys())
        
        for key, value in updates.items():
            if key in allowed_keys:
                self._session_policy[key] = value
        
        self._save_policies()
        return self._session_policy
    
    def update_api_policy(self, updates: Dict) -> Dict:
        """Update API policy"""
        allowed_keys = set(DEFAULT_API_POLICY.keys())
        
        for key, value in updates.items():
            if key in allowed_keys:
                self._api_policy[key] = value
        
        self._save_policies()
        return self._api_policy
    
    def get_all_policies(self) -> Dict:
        """Get all security policies"""
        return {
            "password_policy": self._password_policy,
            "session_policy": self._session_policy,
            "api_policy": self._api_policy,
            "blocked_ips_count": len(self._blocked_ips),
            "active_api_keys": sum(1 for k in self._api_keys.values() if k["status"] == "active")
        }


# Singleton instance
_security_policy: Optional[SecurityPolicy] = None


def get_security_policy() -> SecurityPolicy:
    """Get the global SecurityPolicy instance"""
    global _security_policy
    if _security_policy is None:
        _security_policy = SecurityPolicy()
    return _security_policy
