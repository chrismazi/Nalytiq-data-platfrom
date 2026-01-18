"""
Rate Limiting Middleware for FastAPI
Provides request rate limiting to prevent API abuse
Uses in-memory storage by default, Redis for production
"""
import time
import asyncio
from collections import defaultdict
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps
import logging

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max requests in 1 second
    enabled: bool = True


@dataclass
class RateLimitEntry:
    """Track request counts for a client"""
    minute_count: int = 0
    hour_count: int = 0
    second_count: int = 0
    minute_start: float = 0
    hour_start: float = 0
    second_start: float = 0


class InMemoryRateLimiter:
    """
    In-memory rate limiter for development and small deployments
    For production, use RedisRateLimiter
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.clients: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._cleanup_task = None
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier from request"""
        # Try to get real IP from headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Can also include user ID if authenticated
        # user_id = getattr(request.state, 'user_id', None)
        
        return client_ip
    
    def check_rate_limit(self, client_key: str) -> tuple[bool, Dict]:
        """
        Check if request is allowed
        Returns (allowed, headers_dict)
        """
        now = time.time()
        entry = self.clients[client_key]
        
        # Reset counters if windows have passed
        if now - entry.second_start >= 1:
            entry.second_count = 0
            entry.second_start = now
        
        if now - entry.minute_start >= 60:
            entry.minute_count = 0
            entry.minute_start = now
        
        if now - entry.hour_start >= 3600:
            entry.hour_count = 0
            entry.hour_start = now
        
        # Check limits
        if entry.second_count >= self.config.burst_limit:
            retry_after = 1 - (now - entry.second_start)
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(entry.second_start + 1)),
                "Retry-After": str(max(1, int(retry_after)))
            }
        
        if entry.minute_count >= self.config.requests_per_minute:
            retry_after = 60 - (now - entry.minute_start)
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(entry.minute_start + 60)),
                "Retry-After": str(max(1, int(retry_after)))
            }
        
        if entry.hour_count >= self.config.requests_per_hour:
            retry_after = 3600 - (now - entry.hour_start)
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_hour),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(entry.hour_start + 3600)),
                "Retry-After": str(max(1, int(retry_after)))
            }
        
        # Increment counters
        entry.second_count += 1
        entry.minute_count += 1
        entry.hour_count += 1
        
        # Calculate remaining
        remaining = min(
            self.config.burst_limit - entry.second_count,
            self.config.requests_per_minute - entry.minute_count
        )
        
        return True, {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(entry.minute_start + 60))
        }
    
    def cleanup_old_entries(self, max_age: int = 3600):
        """Remove old client entries to prevent memory bloat"""
        now = time.time()
        to_remove = []
        
        for key, entry in self.clients.items():
            if now - entry.hour_start > max_age:
                to_remove.append(key)
        
        for key in to_remove:
            del self.clients[key]
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old rate limit entries")


class RedisRateLimiter:
    """
    Redis-based rate limiter for production
    Provides distributed rate limiting across multiple server instances
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.redis_url = redis_url
        self._redis = None
    
    async def _get_redis(self):
        """Lazy connect to Redis"""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(self.redis_url)
            except ImportError:
                logger.warning("Redis not installed, falling back to in-memory rate limiting")
                return None
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                return None
        return self._redis
    
    async def check_rate_limit(self, client_key: str) -> tuple[bool, Dict]:
        """Check rate limit using Redis"""
        redis = await self._get_redis()
        if redis is None:
            # Fallback to allowing request if Redis unavailable
            return True, {}
        
        now = time.time()
        pipe = redis.pipeline()
        
        # Keys for different windows
        minute_key = f"rl:{client_key}:min:{int(now // 60)}"
        hour_key = f"rl:{client_key}:hour:{int(now // 3600)}"
        
        try:
            # Increment counters
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            
            results = await pipe.execute()
            minute_count = results[0]
            hour_count = results[2]
            
            # Check limits
            if minute_count > self.config.requests_per_minute:
                return False, {
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(60 - int(now % 60))
                }
            
            if hour_count > self.config.requests_per_hour:
                return False, {
                    "X-RateLimit-Limit": str(self.config.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(3600 - int(now % 3600))
                }
            
            remaining = self.config.requests_per_minute - minute_count
            
            return True, {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": str(max(0, remaining))
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return True, {}  # Allow on error


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting
    Add to app with: app.add_middleware(RateLimitMiddleware, config=config)
    """
    
    def __init__(self, app, config: RateLimitConfig = None, redis_url: str = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        
        # Use Redis in production, in-memory for development
        if redis_url:
            self.limiter = RedisRateLimiter(redis_url, self.config)
        else:
            self.limiter = InMemoryRateLimiter(self.config)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter"""
        if not self.config.enabled:
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        skip_paths = ['/api/docs', '/api/redoc', '/health', '/openapi.json']
        if any(request.url.path.startswith(p) for p in skip_paths):
            return await call_next(request)
        
        client_key = self._get_client_key(request)
        
        # Check rate limit
        if isinstance(self.limiter, RedisRateLimiter):
            allowed, headers = await self.limiter.check_rate_limit(client_key)
        else:
            allowed, headers = self.limiter.check_rate_limit(client_key)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_key}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def _get_client_key(self, request: Request) -> str:
        """Get client identifier"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Decorator for per-endpoint rate limiting
def rate_limit(requests_per_minute: int = 30, requests_per_hour: int = 500):
    """
    Decorator for per-endpoint rate limiting
    
    Usage:
        @app.get("/expensive-endpoint")
        @rate_limit(requests_per_minute=10)
        async def expensive_endpoint():
            ...
    """
    limiter = InMemoryRateLimiter(RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour
    ))
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_key = request.client.host if request.client else "unknown"
            allowed, headers = limiter.check_rate_limit(client_key)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for this endpoint",
                    headers=headers
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# Tiered rate limits for different user types
RATE_LIMITS = {
    'anonymous': RateLimitConfig(requests_per_minute=30, requests_per_hour=300),
    'authenticated': RateLimitConfig(requests_per_minute=60, requests_per_hour=1000),
    'analyst': RateLimitConfig(requests_per_minute=100, requests_per_hour=2000),
    'admin': RateLimitConfig(requests_per_minute=200, requests_per_hour=5000),
}


def get_rate_limit_config(user_role: Optional[str] = None) -> RateLimitConfig:
    """Get rate limit config based on user role"""
    if user_role and user_role in RATE_LIMITS:
        return RATE_LIMITS[user_role]
    return RATE_LIMITS.get('anonymous', RateLimitConfig())
