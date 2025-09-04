"""
Advanced Cache Manager - Multi-level caching system
L1: In-memory cache (fastest)
L2: Redis cache (fast)
L3: Database/External source (persistent)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import hashlib
import os

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheKey:
    """Cache key generator with consistent hashing"""
    
    @staticmethod
    def generate(*args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        # Create a string representation of the arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        
        # Generate hash for consistent key length
        return hashlib.md5(key_string.encode()).hexdigest()


class CacheEntry:
    """Cache entry with metadata"""
    
    def __init__(self, data: Any, ttl: int = 3600, created_at: Optional[datetime] = None):
        self.data = data
        self.ttl = ttl
        self.created_at = created_at or datetime.now()
        self.access_count = 0
        self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def access(self):
        """Record access to cache entry"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'data': self.data,
            'ttl': self.ttl,
            'created_at': self.created_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        entry = cls(
            data=data['data'],
            ttl=data['ttl'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        entry.access_count = data['access_count']
        entry.last_accessed = datetime.fromisoformat(data['last_accessed'])
        return entry


class AdvancedCacheManager:
    """Multi-level cache manager with intelligent caching strategies"""
    
    def __init__(self, redis_url: Optional[str] = None, 
                 l1_max_size: int = 1000, l1_ttl: int = 300):
        # Get Redis URL from environment if not provided
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://redis.redis.svc.cluster.local:6379')
        self.redis_client: Optional[Any] = None
        
        # L1 Cache (In-memory)
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = l1_max_size
        self.l1_ttl = l1_ttl
        
        # Cache statistics
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'l3_fetches': 0,
            'cache_evictions': 0
        }
    
    async def initialize(self):
        """Initialize Redis connection if available"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using L1 cache only.")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info(f"Redis cache connection established: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using L1 cache only.")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")
    
    async def get(self, key: str, fetch_func=None, ttl: int = 3600) -> Optional[Any]:
        """
        Get data from cache with automatic fallback
        
        Args:
            key: Cache key
            fetch_func: Function to fetch data if not in cache
            ttl: Time to live in seconds
        """
        # L1 Cache check
        if entry := self.l1_cache.get(key):
            if not entry.is_expired:
                entry.access()
                self.stats['l1_hits'] += 1
                return entry.data
            else:
                del self.l1_cache[key]
        
        self.stats['l1_misses'] += 1
        
        # L2 Cache check (Redis)
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    entry = CacheEntry.from_dict(json.loads(cached_data))
                    if not entry.is_expired:
                        # Promote to L1 cache
                        await self._set_l1(key, entry)
                        self.stats['l2_hits'] += 1
                        return entry.data
                    else:
                        await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        self.stats['l2_misses'] += 1
        
        # L3 Fetch (Database/External)
        if fetch_func:
            try:
                data = await fetch_func()
                if data is not None:
                    await self.set(key, data, ttl)
                    self.stats['l3_fetches'] += 1
                    return data
            except Exception as e:
                logger.error(f"L3 fetch error: {e}")
        
        return None
    
    async def set(self, key: str, data: Any, ttl: int = 3600):
        """Set data in both L1 and L2 caches"""
        entry = CacheEntry(data, ttl)
        
        # Set in L1 cache
        await self._set_l1(key, entry)
        
        # Set in L2 cache (Redis)
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    key, 
                    ttl, 
                    json.dumps(entry.to_dict())
                )
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
    
    async def _set_l1(self, key: str, entry: CacheEntry):
        """Set data in L1 cache with eviction if needed"""
        # Evict if cache is full
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1()
        
        self.l1_cache[key] = entry
    
    async def _evict_l1(self):
        """Evict least recently used entry from L1 cache"""
        if not self.l1_cache:
            return
        
        # Find least recently used entry
        lru_key = min(
            self.l1_cache.keys(),
            key=lambda k: self.l1_cache[k].last_accessed
        )
        
        del self.l1_cache[lru_key]
        self.stats['cache_evictions'] += 1
    
    async def delete(self, key: str):
        """Delete data from all cache levels"""
        # Delete from L1
        if key in self.l1_cache:
            del self.l1_cache[key]
        
        # Delete from L2 (Redis)
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
    
    async def clear(self):
        """Clear all caches"""
        self.l1_cache.clear()
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = (self.stats['l1_hits'] + self.stats['l1_misses'] + 
                         self.stats['l2_hits'] + self.stats['l2_misses'])
        
        l1_hit_rate = (self.stats['l1_hits'] / max(total_requests, 1)) * 100
        l2_hit_rate = (self.stats['l2_hits'] / max(total_requests, 1)) * 100
        
        # Get Redis info if available
        redis_info = {}
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_info = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception as e:
                logger.warning(f"Could not get Redis info: {e}")
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'l1_hit_rate': l1_hit_rate,
            'l2_hit_rate': l2_hit_rate,
            'l1_cache_size': len(self.l1_cache),
            'l1_cache_max_size': self.l1_max_size,
            'redis_connected': self.redis_client is not None,
            'redis_info': redis_info
        }
    
    async def warm_cache(self, keys_and_fetch_funcs: List[tuple]):
        """Warm cache with frequently accessed data"""
        logger.info(f"Warming cache with {len(keys_and_fetch_funcs)} items")
        
        for key, fetch_func in keys_and_fetch_funcs:
            try:
                await self.get(key, fetch_func)
            except Exception as e:
                logger.error(f"Cache warming failed for {key}: {e}")


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for automatic caching of function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{CacheKey.generate(*args, **kwargs)}"
            
            # Get cache manager from function context or create new one
            cache_manager = getattr(func, '_cache_manager', None)
            if not cache_manager:
                cache_manager = AdvancedCacheManager()
                await cache_manager.initialize()
                func._cache_manager = cache_manager
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[AdvancedCacheManager] = None


async def get_cache_manager() -> AdvancedCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = AdvancedCacheManager()
        await _cache_manager.initialize()
    return _cache_manager


async def close_cache_manager():
    """Close global cache manager"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.close()
        _cache_manager = None 