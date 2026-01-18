"""
Caching Layer for Nalytiq Platform
Provides Redis-based caching with in-memory fallback
Caches analysis results, dataset metadata, and computed values
"""
import json
import hashlib
import pickle
import time
import asyncio
from typing import Any, Optional, Union, Callable
from functools import wraps
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_items: int = 1000
    enabled: bool = True
    prefix: str = "nalytiq:"


class InMemoryCache:
    """
    Simple in-memory cache with TTL support
    Used as fallback when Redis is unavailable
    """
    
    def __init__(self, max_items: int = 1000):
        self._cache: dict = {}
        self._expiry: dict = {}
        self.max_items = max_items
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()
        expired = [k for k, exp in self._expiry.items() if exp and exp < now]
        for key in expired:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache is full"""
        if len(self._cache) >= self.max_items:
            # Remove oldest 10% of entries
            num_to_remove = max(1, self.max_items // 10)
            keys_to_remove = list(self._cache.keys())[:num_to_remove]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self._cleanup_expired()
        
        if key not in self._cache:
            return None
        
        expiry = self._expiry.get(key)
        if expiry and time.time() > expiry:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return None
        
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        self._evict_if_needed()
        
        self._cache[key] = value
        if ttl:
            self._expiry[key] = time.time() + ttl
        else:
            self._expiry[key] = None
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None
    
    def clear(self) -> bool:
        """Clear all cache"""
        self._cache.clear()
        self._expiry.clear()
        return True
    
    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        if pattern == "*":
            return list(self._cache.keys())
        
        import fnmatch
        return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]


class RedisCache:
    """
    Redis-based cache for production
    Provides distributed caching across server instances
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "nalytiq:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None
        self._connected = False
    
    async def _connect(self):
        """Connect to Redis"""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(self.redis_url)
                self._connected = True
                logger.info("Connected to Redis cache")
            except ImportError:
                logger.warning("Redis package not installed")
                self._connected = False
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                self._connected = False
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        redis = await self._connect()
        if not redis:
            return None
        
        try:
            value = await redis.get(self._make_key(key))
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis"""
        redis = await self._connect()
        if not redis:
            return False
        
        try:
            serialized = pickle.dumps(value)
            await redis.setex(self._make_key(key), ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        redis = await self._connect()
        if not redis:
            return False
        
        try:
            await redis.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        redis = await self._connect()
        if not redis:
            return False
        
        try:
            return await redis.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        redis = await self._connect()
        if not redis:
            return 0
        
        try:
            keys = await redis.keys(self._make_key(pattern))
            if keys:
                return await redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
        
        return 0


class CacheManager:
    """
    Unified cache manager that uses Redis when available,
    falls back to in-memory cache
    """
    
    _instance = None
    
    def __new__(cls, config: CacheConfig = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: CacheConfig = None):
        if self._initialized:
            return
        
        self.config = config or CacheConfig()
        self.memory_cache = InMemoryCache(self.config.max_memory_items)
        self.redis_cache = RedisCache(self.config.redis_url, self.config.prefix)
        self._use_redis = True
        self._initialized = True
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({
            'args': [str(a) for a in args],
            'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
        }, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.config.enabled:
            return None
        
        # Try memory cache first (L1)
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try Redis (L2) if enabled
        if self._use_redis:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Populate L1 cache
                self.memory_cache.set(key, value, self.config.default_ttl)
                return value
        
        return None
    
    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous get (memory only)"""
        if not self.config.enabled:
            return None
        return self.memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self.config.enabled:
            return False
        
        ttl = ttl or self.config.default_ttl
        
        # Set in memory cache (L1)
        self.memory_cache.set(key, value, ttl)
        
        # Set in Redis (L2) if enabled
        if self._use_redis:
            await self.redis_cache.set(key, value, ttl)
        
        return True
    
    def set_sync(self, key: str, value: Any, ttl: int = None) -> bool:
        """Synchronous set (memory only)"""
        if not self.config.enabled:
            return False
        return self.memory_cache.set(key, value, ttl or self.config.default_ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        self.memory_cache.delete(key)
        if self._use_redis:
            await self.redis_cache.delete(key)
        return True
    
    async def invalidate_dataset(self, dataset_id: int):
        """Invalidate all cache entries for a dataset"""
        pattern = f"dataset:{dataset_id}:*"
        self.memory_cache.clear()  # Clear all for simplicity
        if self._use_redis:
            await self.redis_cache.clear_pattern(pattern)
    
    async def invalidate_analysis(self, analysis_id: int):
        """Invalidate cache entries for an analysis"""
        pattern = f"analysis:{analysis_id}:*"
        if self._use_redis:
            await self.redis_cache.clear_pattern(pattern)


# Global cache instance
_cache_manager = None


def get_cache() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Usage:
        @cached(ttl=1800, key_prefix="analysis")
        async def expensive_analysis(dataset_id: int, params: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            func_name = func.__name__
            key_parts = [key_prefix, func_name] if key_prefix else [func_name]
            key_parts.append(cache._generate_key(*args, **kwargs))
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            
            func_name = func.__name__
            key_parts = [key_prefix, func_name] if key_prefix else [func_name]
            key_parts.append(cache._generate_key(*args, **kwargs))
            cache_key = ":".join(key_parts)
            
            cached_value = cache.get_sync(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set_sync(cache_key, result, ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Cache key generators for common patterns
class CacheKeys:
    """Helper class for generating consistent cache keys"""
    
    @staticmethod
    def dataset_metadata(dataset_id: int) -> str:
        return f"dataset:{dataset_id}:metadata"
    
    @staticmethod
    def dataset_preview(dataset_id: int, rows: int = 100) -> str:
        return f"dataset:{dataset_id}:preview:{rows}"
    
    @staticmethod
    def dataset_columns(dataset_id: int) -> str:
        return f"dataset:{dataset_id}:columns"
    
    @staticmethod
    def dataset_stats(dataset_id: int) -> str:
        return f"dataset:{dataset_id}:stats"
    
    @staticmethod
    def analysis_result(analysis_id: int) -> str:
        return f"analysis:{analysis_id}:result"
    
    @staticmethod
    def model_info(model_id: int) -> str:
        return f"model:{model_id}:info"
    
    @staticmethod
    def user_session(user_id: int) -> str:
        return f"user:{user_id}:session"
    
    @staticmethod
    def grouped_stats(dataset_id: int, group_by: str, value: str, agg: str) -> str:
        return f"dataset:{dataset_id}:grouped:{group_by}:{value}:{agg}"
    
    @staticmethod
    def correlation_matrix(dataset_id: int) -> str:
        return f"dataset:{dataset_id}:correlation"
