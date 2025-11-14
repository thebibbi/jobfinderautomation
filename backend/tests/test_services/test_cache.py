"""
Tests for Cache Service
"""
import pytest
from app.services.cache_service import CacheService, cached, CacheNamespace, CacheTTL


class TestCacheService:
    """Test cache service functionality"""

    def test_set_and_get(self):
        """Should set and get values"""
        cache = CacheService()

        # Set value
        success = cache.set("test", "key1", "value1", ttl_seconds=60)
        assert success == True

        # Get value
        value = cache.get("test", "key1")
        assert value == "value1"

    def test_get_nonexistent(self):
        """Should return None for nonexistent keys"""
        cache = CacheService()

        value = cache.get("test", "nonexistent")
        assert value is None

    def test_delete(self):
        """Should delete keys"""
        cache = CacheService()

        # Set and verify
        cache.set("test", "key1", "value1")
        assert cache.get("test", "key1") == "value1"

        # Delete
        deleted = cache.delete("test", "key1")
        assert deleted == True

        # Verify deleted
        assert cache.get("test", "key1") is None

    def test_exists(self):
        """Should check if key exists"""
        cache = CacheService()

        # Initially doesn't exist
        assert cache.exists("test", "key1") == False

        # After setting
        cache.set("test", "key1", "value1")
        assert cache.exists("test", "key1") == True

        # After deleting
        cache.delete("test", "key1")
        assert cache.exists("test", "key1") == False

    def test_increment(self):
        """Should increment counters"""
        cache = CacheService()

        # First increment (starts at 0)
        result = cache.increment("test", "counter")
        assert result == 1

        # Second increment
        result = cache.increment("test", "counter")
        assert result == 2

        # Increment by amount
        result = cache.increment("test", "counter", amount=5)
        assert result == 7

    def test_cache_stats(self):
        """Should track cache statistics"""
        cache = CacheService()

        initial_stats = cache.get_stats()

        # Perform operations
        cache.set("test", "key1", "value1")
        cache.get("test", "key1")  # Hit
        cache.get("test", "nonexistent")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] > initial_stats["hits"]
        assert stats["misses"] > initial_stats["misses"]
        assert stats["sets"] > initial_stats["sets"]
        assert stats["hit_rate_percent"] >= 0

    def test_delete_pattern(self):
        """Should delete keys by pattern"""
        cache = CacheService()

        # Set multiple keys
        cache.set("test", "user:1:profile", {"name": "Alice"})
        cache.set("test", "user:1:settings", {"theme": "dark"})
        cache.set("test", "user:2:profile", {"name": "Bob"})
        cache.set("test", "other:data", "something")

        # Delete user:1:* keys
        deleted = cache.delete_pattern("test", "user:1:*")
        assert deleted >= 2

        # Verify specific keys deleted
        assert cache.get("test", "user:1:profile") is None
        assert cache.get("test", "user:1:settings") is None

        # Verify other keys remain
        assert cache.get("test", "user:2:profile") is not None

    def test_clear_namespace(self):
        """Should clear entire namespace"""
        cache = CacheService()

        # Set keys in namespace
        cache.set("test_ns", "key1", "value1")
        cache.set("test_ns", "key2", "value2")
        cache.set("other_ns", "key1", "value1")

        # Clear test_ns
        deleted = cache.clear_namespace("test_ns")
        assert deleted >= 2

        # Verify namespace cleared
        assert cache.get("test_ns", "key1") is None
        assert cache.get("test_ns", "key2") is None

        # Other namespace unaffected
        assert cache.get("other_ns", "key1") is not None

    def test_serialization_json(self):
        """Should serialize/deserialize JSON-compatible data"""
        cache = CacheService()

        test_data = {
            "string": "hello",
            "number": 42,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }

        cache.set("test", "json_data", test_data)
        retrieved = cache.get("test", "json_data")

        assert retrieved == test_data

    def test_serialization_complex(self):
        """Should serialize/deserialize complex objects with pickle"""
        cache = CacheService()

        # Custom class
        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return isinstance(other, CustomObject) and self.value == other.value

        obj = CustomObject(42)

        cache.set("test", "custom_obj", obj)
        retrieved = cache.get("test", "custom_obj")

        assert retrieved == obj
        assert retrieved.value == 42


class TestCachedDecorator:
    """Test @cached decorator"""

    def test_cached_decorator_basic(self):
        """Should cache function results"""
        call_count = {"value": 0}

        @cached("test_decorator", ttl_seconds=60)
        def expensive_function(x):
            call_count["value"] += 1
            return x * 2

        # First call - execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count["value"] == 1

        # Second call - return cached
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count["value"] == 1  # Not incremented

        # Different args - execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count["value"] == 2

    def test_cached_decorator_with_kwargs(self):
        """Should handle keyword arguments"""
        @cached("test_kwargs", ttl_seconds=60)
        def function_with_kwargs(a, b=10):
            return a + b

        # First call
        result1 = function_with_kwargs(5, b=10)
        assert result1 == 15

        # Same args - cached
        result2 = function_with_kwargs(5, b=10)
        assert result2 == 15

        # Different kwargs - new execution
        result3 = function_with_kwargs(5, b=20)
        assert result3 == 25

    def test_cached_decorator_invalidate(self):
        """Should invalidate cache"""
        call_count = {"value": 0}

        @cached("test_invalidate", ttl_seconds=60)
        def cached_function(x):
            call_count["value"] += 1
            return x * 2

        # Cache result
        result1 = cached_function(5)
        assert result1 == 10
        assert call_count["value"] == 1

        # Invalidate
        cached_function.invalidate(5)

        # Should execute again
        result2 = cached_function(5)
        assert result2 == 10
        assert call_count["value"] == 2


class TestCacheNamespaces:
    """Test cache namespaces"""

    def test_namespace_isolation(self):
        """Should isolate keys by namespace"""
        cache = CacheService()

        # Set same key in different namespaces
        cache.set(CacheNamespace.JOB_ANALYSIS, "job:123", {"score": 85})
        cache.set(CacheNamespace.JOB_DETAILS, "job:123", {"title": "Engineer"})

        # Values should be different
        analysis = cache.get(CacheNamespace.JOB_ANALYSIS, "job:123")
        details = cache.get(CacheNamespace.JOB_DETAILS, "job:123")

        assert analysis["score"] == 85
        assert details["title"] == "Engineer"

    def test_all_namespaces_defined(self):
        """Should have all expected namespaces"""
        expected_namespaces = [
            "job_analysis",
            "job_details",
            "company_research",
            "skill_gap",
            "recommendations",
            "learning_resources",
            "analytics",
            "follow_up",
            "documents",
            "stats",
            "user_prefs"
        ]

        for namespace in expected_namespaces:
            assert hasattr(CacheNamespace, namespace.upper())


class TestCacheTTL:
    """Test TTL constants"""

    def test_ttl_values(self):
        """Should have reasonable TTL values"""
        assert CacheTTL.VERY_SHORT == 60
        assert CacheTTL.SHORT == 300
        assert CacheTTL.MEDIUM == 1800
        assert CacheTTL.LONG == 3600
        assert CacheTTL.VERY_LONG == 86400
        assert CacheTTL.WEEK == 604800

    def test_ttl_ordering(self):
        """TTL values should be ordered"""
        assert CacheTTL.VERY_SHORT < CacheTTL.SHORT
        assert CacheTTL.SHORT < CacheTTL.MEDIUM
        assert CacheTTL.MEDIUM < CacheTTL.LONG
        assert CacheTTL.LONG < CacheTTL.VERY_LONG
        assert CacheTTL.VERY_LONG < CacheTTL.WEEK


class TestCacheFallback:
    """Test cache fallback behavior"""

    def test_in_memory_fallback(self):
        """Should use in-memory cache when Redis unavailable"""
        cache = CacheService()

        # Should work regardless of Redis availability
        cache.set("test", "key1", "value1")
        value = cache.get("test", "key1")

        assert value == "value1"

    def test_error_handling(self):
        """Should handle errors gracefully"""
        cache = CacheService()

        # Getting from non-existent key should not raise
        value = cache.get("test", "nonexistent")
        assert value is None

        # Deleting non-existent key should not raise
        deleted = cache.delete("test", "nonexistent")
        assert deleted == False
