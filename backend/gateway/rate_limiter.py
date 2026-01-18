"""
Rate Limiter Module

Per-organization rate limiting for X-Road services:
- Token bucket algorithm
- Configurable limits per organization
- Sliding window tracking
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False if rate limited
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def get_status(self) -> Dict:
        """Get bucket status"""
        with self._lock:
            self._refill()
            return {
                "tokens_available": int(self.tokens),
                "capacity": self.capacity,
                "refill_rate": self.refill_rate
            }


class RateLimiter:
    """
    Rate limiter for X-Road services.
    
    Features:
    - Per-organization limits
    - Per-service limits
    - Sliding window tracking
    - Configurable quotas
    """
    
    # Default limits
    DEFAULT_ORG_REQUESTS_PER_MINUTE = 1000
    DEFAULT_SERVICE_REQUESTS_PER_MINUTE = 100
    DEFAULT_BURST_MULTIPLIER = 2
    
    def __init__(self):
        """Initialize rate limiter"""
        self._org_buckets: Dict[str, TokenBucket] = {}
        self._service_buckets: Dict[str, TokenBucket] = {}
        self._org_limits: Dict[str, int] = {}
        self._service_limits: Dict[str, int] = {}
        self._request_counts: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        
        logger.info("RateLimiter initialized")
    
    def set_org_limit(self, organization_code: str, requests_per_minute: int):
        """
        Set rate limit for an organization.
        
        Args:
            organization_code: Organization code
            requests_per_minute: Allowed requests per minute
        """
        with self._lock:
            self._org_limits[organization_code] = requests_per_minute
            
            # Create new bucket with updated limit
            capacity = requests_per_minute * self.DEFAULT_BURST_MULTIPLIER
            refill_rate = requests_per_minute / 60.0
            self._org_buckets[organization_code] = TokenBucket(capacity, refill_rate)
            
        logger.info(f"Rate limit set for {organization_code}: {requests_per_minute}/min")
    
    def set_service_limit(self, service_key: str, requests_per_minute: int):
        """
        Set rate limit for a service.
        
        Args:
            service_key: Service identifier (org/subsystem/service)
            requests_per_minute: Allowed requests per minute
        """
        with self._lock:
            self._service_limits[service_key] = requests_per_minute
            
            capacity = requests_per_minute * self.DEFAULT_BURST_MULTIPLIER
            refill_rate = requests_per_minute / 60.0
            self._service_limits[service_key] = TokenBucket(capacity, refill_rate)
    
    def _get_org_bucket(self, organization_code: str) -> TokenBucket:
        """Get or create organization bucket"""
        if organization_code not in self._org_buckets:
            limit = self._org_limits.get(
                organization_code, 
                self.DEFAULT_ORG_REQUESTS_PER_MINUTE
            )
            capacity = limit * self.DEFAULT_BURST_MULTIPLIER
            refill_rate = limit / 60.0
            self._org_buckets[organization_code] = TokenBucket(capacity, refill_rate)
        
        return self._org_buckets[organization_code]
    
    def _get_service_bucket(self, service_key: str) -> TokenBucket:
        """Get or create service bucket"""
        if service_key not in self._service_buckets:
            limit = self._service_limits.get(
                service_key,
                self.DEFAULT_SERVICE_REQUESTS_PER_MINUTE
            )
            capacity = limit * self.DEFAULT_BURST_MULTIPLIER
            refill_rate = limit / 60.0
            self._service_buckets[service_key] = TokenBucket(capacity, refill_rate)
        
        return self._service_buckets[service_key]
    
    def check_rate_limit(
        self,
        organization_code: str,
        service_key: str = None
    ) -> Dict:
        """
        Check if request is within rate limits.
        
        Args:
            organization_code: Client organization
            service_key: Optional service identifier
            
        Returns:
            Rate limit check result
        """
        # Check organization limit
        org_bucket = self._get_org_bucket(organization_code)
        if not org_bucket.acquire():
            return {
                "allowed": False,
                "reason": "organization_rate_limit_exceeded",
                "retry_after_seconds": 60 / org_bucket.refill_rate,
                "limit_type": "organization"
            }
        
        # Check service limit if provided
        if service_key:
            service_bucket = self._get_service_bucket(service_key)
            if not service_bucket.acquire():
                # Return the org token since we won't use it
                org_bucket.tokens = min(org_bucket.capacity, org_bucket.tokens + 1)
                
                return {
                    "allowed": False,
                    "reason": "service_rate_limit_exceeded",
                    "retry_after_seconds": 60 / service_bucket.refill_rate,
                    "limit_type": "service"
                }
        
        # Track the request
        self._track_request(organization_code, service_key)
        
        return {
            "allowed": True,
            "remaining_org_tokens": int(org_bucket.tokens)
        }
    
    def _track_request(self, organization_code: str, service_key: str = None):
        """Track request for analytics"""
        now = datetime.utcnow()
        
        with self._lock:
            # Track org requests
            self._request_counts[f"org:{organization_code}"].append(now)
            
            # Track service requests
            if service_key:
                self._request_counts[f"service:{service_key}"].append(now)
            
            # Clean old entries (older than 1 hour)
            cutoff = now - timedelta(hours=1)
            for key in list(self._request_counts.keys()):
                self._request_counts[key] = [
                    t for t in self._request_counts[key] if t > cutoff
                ]
    
    def get_org_usage(self, organization_code: str, minutes: int = 60) -> Dict:
        """
        Get usage statistics for an organization.
        
        Args:
            organization_code: Organization code
            minutes: Time window in minutes
            
        Returns:
            Usage statistics
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        key = f"org:{organization_code}"
        
        with self._lock:
            requests = [t for t in self._request_counts.get(key, []) if t > cutoff]
        
        bucket = self._get_org_bucket(organization_code)
        status = bucket.get_status()
        
        limit = self._org_limits.get(
            organization_code,
            self.DEFAULT_ORG_REQUESTS_PER_MINUTE
        )
        
        return {
            "organization_code": organization_code,
            "requests_in_window": len(requests),
            "window_minutes": minutes,
            "limit_per_minute": limit,
            "tokens_available": status["tokens_available"],
            "bucket_capacity": status["capacity"]
        }
    
    def get_all_usage(self) -> Dict:
        """Get usage statistics for all organizations"""
        usage = {}
        
        for key in self._org_buckets.keys():
            usage[key] = self.get_org_usage(key)
        
        return usage
    
    def reset_org_limit(self, organization_code: str):
        """Reset rate limit for an organization (refill bucket)"""
        with self._lock:
            if organization_code in self._org_buckets:
                bucket = self._org_buckets[organization_code]
                bucket.tokens = bucket.capacity
                logger.info(f"Rate limit reset for {organization_code}")


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global RateLimiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
