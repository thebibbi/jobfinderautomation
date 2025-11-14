"""
Advanced Caching Service with Redis

Provides intelligent caching for frequently accessed data with TTL management.
"""
import json
import hashlib
from typing import Any, Optional, Callable, List
from datetime import timedelta
from functools import wraps
from loguru import logger
import pickle

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Caching will be disabled.")

from ..config import settings


class CacheService:
    """
    Redis-based caching service with fallback to in-memory cache
    """

    def __init__(self):
        self._redis_client: Optional[Redis] = None
        self._memory_cache: dict = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }

        # Initialize Redis if available
        if REDIS_AVAILABLE and settings.REDIS_ENABLED:
            try:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                    decode_responses=False,  # We'll handle encoding
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self._redis_client.ping()
                logger.info(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self._redis_client = None
        else:
            logger.info("Redis disabled. Using in-memory cache.")

    @property
    def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        return self._redis_client is not None

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (faster, more readable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)

    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"{settings.REDIS_KEY_PREFIX}:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            namespace: Cache namespace (e.g., 'job_analysis', 'company_research')
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        cache_key = self._generate_key(namespace, key)

        try:
            if self._redis_client:
                # Redis cache
                data = self._redis_client.get(cache_key)
                if data:
                    self._cache_stats["hits"] += 1
                    logger.debug(f"Cache HIT: {cache_key}")
                    return self._deserialize(data)
                else:
                    self._cache_stats["misses"] += 1
                    logger.debug(f"Cache MISS: {cache_key}")
                    return None
            else:
                # In-memory cache
                if cache_key in self._memory_cache:
                    self._cache_stats["hits"] += 1
                    return self._memory_cache[cache_key]
                else:
                    self._cache_stats["misses"] += 1
                    return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._cache_stats["misses"] += 1
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        cache_key = self._generate_key(namespace, key)

        try:
            if self._redis_client:
                # Redis cache
                data = self._serialize(value)
                if ttl_seconds:
                    self._redis_client.setex(cache_key, ttl_seconds, data)
                else:
                    self._redis_client.set(cache_key, data)
                self._cache_stats["sets"] += 1
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl_seconds}s)")
                return True
            else:
                # In-memory cache (no TTL support in simple version)
                self._memory_cache[cache_key] = value
                self._cache_stats["sets"] += 1
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """Delete key from cache"""
        cache_key = self._generate_key(namespace, key)

        try:
            if self._redis_client:
                result = self._redis_client.delete(cache_key)
                self._cache_stats["deletes"] += 1
                return result > 0
            else:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    self._cache_stats["deletes"] += 1
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def delete_pattern(self, namespace: str, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            namespace: Cache namespace
            pattern: Key pattern (e.g., 'job:*', 'user:123:*')

        Returns:
            Number of keys deleted
        """
        full_pattern = self._generate_key(namespace, pattern)

        try:
            if self._redis_client:
                keys = self._redis_client.keys(full_pattern)
                if keys:
                    deleted = self._redis_client.delete(*keys)
                    self._cache_stats["deletes"] += deleted
                    logger.info(f"Deleted {deleted} keys matching {full_pattern}")
                    return deleted
                return 0
            else:
                # In-memory: match and delete
                matching_keys = [k for k in self._memory_cache.keys() if k.startswith(full_pattern.replace('*', ''))]
                for key in matching_keys:
                    del self._memory_cache[key]
                self._cache_stats["deletes"] += len(matching_keys)
                return len(matching_keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0

    def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(namespace, key)

        try:
            if self._redis_client:
                return self._redis_client.exists(cache_key) > 0
            else:
                return cache_key in self._memory_cache
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    def increment(self, namespace: str, key: str, amount: int = 1) -> int:
        """Increment counter"""
        cache_key = self._generate_key(namespace, key)

        try:
            if self._redis_client:
                return self._redis_client.incr(cache_key, amount)
            else:
                current = self._memory_cache.get(cache_key, 0)
                new_value = current + amount
                self._memory_cache[cache_key] = new_value
                return new_value
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        stats = {
            **self._cache_stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "backend": "redis" if self._redis_client else "memory",
            "redis_available": self.is_redis_available
        }

        if self._redis_client:
            try:
                info = self._redis_client.info()
                stats["redis_memory_used"] = info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
                stats["redis_total_commands"] = info.get("total_commands_processed", 0)
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")

        return stats

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        return self.delete_pattern(namespace, "*")

    def clear_all(self) -> bool:
        """Clear all cache (USE WITH CAUTION)"""
        try:
            if self._redis_client:
                self._redis_client.flushdb()
                logger.warning("Redis cache cleared (flushdb)")
                return True
            else:
                self._memory_cache.clear()
                logger.warning("In-memory cache cleared")
                return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


# Global cache instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


# Decorator for caching function results
def cached(
    namespace: str,
    ttl_seconds: int = 3600,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results

    Args:
        namespace: Cache namespace
        ttl_seconds: Time to live in seconds
        key_builder: Custom function to build cache key from args

    Example:
        @cached("job_analysis", ttl_seconds=3600)
        def analyze_job(job_id: int):
            # Expensive operation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash function name + args
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = ":".join(key_parts)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # Try to get from cache
            cached_value = cache.get(namespace, cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(namespace, cache_key, result, ttl_seconds)

            return result

        # Add cache invalidation method
        def invalidate(*args, **kwargs):
            cache = get_cache()
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = ":".join(key_parts)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()
            cache.delete(namespace, cache_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


# Common TTL values (in seconds)
class CacheTTL:
    """Standard TTL values for different data types"""
    VERY_SHORT = 60  # 1 minute
    SHORT = 300  # 5 minutes
    MEDIUM = 1800  # 30 minutes
    LONG = 3600  # 1 hour
    VERY_LONG = 86400  # 24 hours
    WEEK = 604800  # 7 days


# Cache namespaces
class CacheNamespace:
    """Standard cache namespaces"""
    JOB_ANALYSIS = "job_analysis"
    JOB_DETAILS = "job_details"
    COMPANY_RESEARCH = "company_research"
    SKILL_GAP_ANALYSIS = "skill_gap"
    RECOMMENDATIONS = "recommendations"
    LEARNING_RESOURCES = "learning_resources"
    ANALYTICS = "analytics"
    FOLLOW_UP = "follow_up"
    DOCUMENT_GENERATION = "documents"
    STATS = "stats"
    USER_PREFERENCES = "user_prefs"
