"""
Cache Management API

Endpoints for cache statistics, management, and monitoring.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

from ..services.cache_service import get_cache, CacheNamespace, CacheTTL


router = APIRouter()


class CacheStats(BaseModel):
    """Cache statistics"""
    hits: int
    misses: int
    sets: int
    deletes: int
    total_requests: int
    hit_rate_percent: float
    backend: str
    redis_available: bool
    redis_memory_used: Optional[str] = None
    redis_connected_clients: Optional[int] = None
    redis_total_commands: Optional[int] = None


class CacheSetRequest(BaseModel):
    """Request to set cache value"""
    namespace: str
    key: str
    value: any
    ttl_seconds: Optional[int] = 3600


class CacheGetRequest(BaseModel):
    """Request to get cache value"""
    namespace: str
    key: str


class CacheClearRequest(BaseModel):
    """Request to clear cache"""
    namespace: Optional[str] = None
    pattern: Optional[str] = None


@router.get("/stats", response_model=CacheStats)
def get_cache_stats():
    """Get cache statistics"""
    try:
        cache = get_cache()
        stats = cache.get_stats()

        return CacheStats(**stats)

    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def cache_health_check():
    """Check cache health"""
    try:
        cache = get_cache()

        return {
            "status": "healthy",
            "redis_available": cache.is_redis_available,
            "backend": "redis" if cache.is_redis_available else "memory"
        }

    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/set")
def set_cache_value(request: CacheSetRequest):
    """
    Manually set a cache value (for debugging/testing)
    """
    try:
        cache = get_cache()

        success = cache.set(
            namespace=request.namespace,
            key=request.key,
            value=request.value,
            ttl_seconds=request.ttl_seconds
        )

        if success:
            return {"message": "Value cached successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cache value")

    except Exception as e:
        logger.error(f"Error setting cache value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get")
def get_cache_value(request: CacheGetRequest):
    """
    Manually get a cache value (for debugging/testing)
    """
    try:
        cache = get_cache()

        value = cache.get(
            namespace=request.namespace,
            key=request.key
        )

        if value is not None:
            return {
                "found": True,
                "value": value
            }
        else:
            return {
                "found": False,
                "value": None
            }

    except Exception as e:
        logger.error(f"Error getting cache value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
def clear_cache(request: CacheClearRequest):
    """
    Clear cache by namespace or pattern
    """
    try:
        cache = get_cache()

        if request.namespace and request.pattern:
            # Clear specific pattern in namespace
            deleted = cache.delete_pattern(request.namespace, request.pattern)
            return {
                "message": f"Cleared {deleted} keys matching pattern",
                "keys_deleted": deleted
            }
        elif request.namespace:
            # Clear entire namespace
            deleted = cache.clear_namespace(request.namespace)
            return {
                "message": f"Cleared namespace: {request.namespace}",
                "keys_deleted": deleted
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide namespace and/or pattern"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-all")
def clear_all_cache():
    """
    Clear ALL cache (USE WITH CAUTION)
    """
    try:
        cache = get_cache()

        success = cache.clear_all()

        if success:
            logger.warning("All cache cleared via API")
            return {"message": "All cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")

    except Exception as e:
        logger.error(f"Error clearing all cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namespaces")
def get_cache_namespaces():
    """Get list of available cache namespaces"""
    return {
        "namespaces": [
            {
                "name": CacheNamespace.JOB_ANALYSIS,
                "description": "Job analysis results",
                "recommended_ttl": CacheTTL.LONG
            },
            {
                "name": CacheNamespace.JOB_DETAILS,
                "description": "Job details and metadata",
                "recommended_ttl": CacheTTL.MEDIUM
            },
            {
                "name": CacheNamespace.COMPANY_RESEARCH,
                "description": "Company research data",
                "recommended_ttl": CacheTTL.VERY_LONG
            },
            {
                "name": CacheNamespace.SKILL_GAP_ANALYSIS,
                "description": "Skill gap analysis results",
                "recommended_ttl": CacheTTL.LONG
            },
            {
                "name": CacheNamespace.RECOMMENDATIONS,
                "description": "Job recommendations",
                "recommended_ttl": CacheTTL.MEDIUM
            },
            {
                "name": CacheNamespace.LEARNING_RESOURCES,
                "description": "Learning resources",
                "recommended_ttl": CacheTTL.VERY_LONG
            },
            {
                "name": CacheNamespace.ANALYTICS,
                "description": "Analytics and metrics",
                "recommended_ttl": CacheTTL.SHORT
            },
            {
                "name": CacheNamespace.FOLLOW_UP,
                "description": "Follow-up schedules",
                "recommended_ttl": CacheTTL.MEDIUM
            },
            {
                "name": CacheNamespace.DOCUMENT_GENERATION,
                "description": "Generated documents",
                "recommended_ttl": CacheTTL.LONG
            },
            {
                "name": CacheNamespace.STATS,
                "description": "Statistics",
                "recommended_ttl": CacheTTL.SHORT
            },
            {
                "name": CacheNamespace.USER_PREFERENCES,
                "description": "User preferences",
                "recommended_ttl": CacheTTL.VERY_LONG
            }
        ]
    }


@router.post("/warm-up")
def warm_up_cache():
    """
    Warm up cache with frequently accessed data
    """
    try:
        logger.info("Starting cache warm-up...")

        # In a real implementation, this would pre-load frequently accessed data
        # For example:
        # - Recent job analyses
        # - Active recommendations
        # - Company research for top companies
        # - Common learning resources

        return {
            "message": "Cache warm-up initiated",
            "note": "This is a placeholder. Implement actual warm-up logic as needed."
        }

    except Exception as e:
        logger.error(f"Error warming up cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/{namespace}")
def list_namespace_keys(
    namespace: str,
    limit: int = 100
):
    """
    List keys in a namespace (for debugging)

    Note: This can be expensive for large namespaces
    """
    try:
        cache = get_cache()

        if cache.is_redis_available:
            # Get keys from Redis
            pattern = f"{namespace}:*"
            # Note: KEYS command can be slow, consider SCAN in production
            keys = cache._redis_client.keys(pattern)
            keys = [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys[:limit]]

            return {
                "namespace": namespace,
                "keys": keys,
                "total_shown": len(keys),
                "limited_to": limit
            }
        else:
            # In-memory cache
            prefix = f"{cache._generate_key(namespace, '')}"
            keys = [k for k in cache._memory_cache.keys() if k.startswith(prefix)][:limit]

            return {
                "namespace": namespace,
                "keys": keys,
                "total_shown": len(keys),
                "limited_to": limit
            }

    except Exception as e:
        logger.error(f"Error listing namespace keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
