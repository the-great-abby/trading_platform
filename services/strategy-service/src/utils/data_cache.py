"""
Data Cache Utility
=================

Centralized caching system for strategies to avoid database connection exhaustion.
Used by CashSecuredPutStrategy, Elliott Wave strategies, and other data-intensive strategies.
"""

import logging
from typing import Dict, Any, Optional, List, TypeVar, Callable
from datetime import datetime, timedelta
from functools import wraps
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DataCache:
    """
    Centralized data cache to prevent database connection exhaustion.
    
    Features:
    - Thread-safe caching
    - Configurable cache duration
    - Automatic cache invalidation
    - Support for different data types
    - Memory-efficient with size limits
    """
    
    def __init__(self, default_ttl_hours: int = 1, max_cache_size: int = 1000):
        self.default_ttl_hours = default_ttl_hours
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        if 'timestamp' not in cache_entry:
            return True
        
        age = datetime.now() - cache_entry['timestamp']
        ttl = timedelta(hours=cache_entry.get('ttl_hours', self.default_ttl_hours))
        return age > ttl
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            for key in expired_keys:
                del self._cache[key]
                logger.debug(f"Removed expired cache entry: {key}")
    
    def _enforce_size_limit(self):
        """Enforce cache size limit by removing oldest entries"""
        with self._lock:
            if len(self._cache) <= self.max_cache_size:
                return
            
            # Sort by timestamp and remove oldest
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].get('timestamp', datetime.min)
            )
            
            entries_to_remove = len(self._cache) - self.max_cache_size
            for key, _ in sorted_entries[:entries_to_remove]:
                del self._cache[key]
                logger.debug(f"Removed oldest cache entry: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cached data"""
        with self._lock:
            if key not in self._cache:
                return default
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return default
            
            logger.debug(f"Cache HIT: {key}")
            return entry['data']
    
    def set(self, key: str, data: Any, ttl_hours: Optional[int] = None) -> None:
        """Set cached data"""
        with self._lock:
            ttl_hours = ttl_hours or self.default_ttl_hours
            self._cache[key] = {
                'data': data,
                'timestamp': datetime.now(),
                'ttl_hours': ttl_hours
            }
            
            logger.debug(f"Cache SET: {key} (TTL: {ttl_hours}h)")
            
            # Cleanup if needed
            self._cleanup_expired()
            self._enforce_size_limit()
    
    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache INVALIDATED: {key}")
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all entries matching pattern"""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
                logger.debug(f"Cache INVALIDATED (pattern): {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.debug("Cache CLEARED")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if self._is_expired(entry)
            )
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'max_size': self.max_cache_size,
                'utilization_pct': (total_entries / self.max_cache_size) * 100
            }

# Global cache instance
_data_cache = DataCache()

def cached(prefix: str, ttl_hours: Optional[int] = None):
    """
    Decorator for caching function results
    
    Usage:
    @cached("options_data", ttl_hours=2)
    def get_options_data(symbol: str, date: str):
        # expensive operation
        return data
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = _data_cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = _data_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache MISS for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            _data_cache.set(cache_key, result, ttl_hours)
            
            return result
        
        return wrapper
    return decorator

def get_cache() -> DataCache:
    """Get the global cache instance"""
    return _data_cache

def cache_options_data(symbol: str, options_data: List[Any], ttl_hours: int = 1) -> None:
    """Cache options data for a symbol"""
    key = f"options|{symbol}"
    _data_cache.set(key, options_data, ttl_hours)

def get_cached_options_data(symbol: str) -> Optional[List[Any]]:
    """Get cached options data for a symbol"""
    key = f"options|{symbol}"
    return _data_cache.get(key)

def cache_elliott_wave_data(symbol: str, wave_data: Dict[str, Any], ttl_hours: int = 2) -> None:
    """Cache Elliott Wave analysis data for a symbol"""
    key = f"elliott_wave|{symbol}"
    _data_cache.set(key, wave_data, ttl_hours)

def get_cached_elliott_wave_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get cached Elliott Wave analysis data for a symbol"""
    key = f"elliott_wave|{symbol}"
    return _data_cache.get(key)

def cache_market_data(symbol: str, data_type: str, data: Any, ttl_hours: int = 1) -> None:
    """Cache market data for a symbol"""
    key = f"market_data|{symbol}|{data_type}"
    _data_cache.set(key, data, ttl_hours)

def get_cached_market_data(symbol: str, data_type: str) -> Optional[Any]:
    """Get cached market data for a symbol"""
    key = f"market_data|{symbol}|{data_type}"
    return _data_cache.get(key)

