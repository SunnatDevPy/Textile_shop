"""Simple in-memory cache for API responses."""
import time
from typing import Any, Optional
from functools import wraps


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        timestamp = self._timestamps.get(key, 0)
        if time.time() > timestamp:
            # Expired
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds (default: 5 minutes)."""
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl

    def delete(self, key: str):
        """Delete key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._timestamps.clear()

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.delete(key)


# Global cache instance
cache = SimpleCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator
