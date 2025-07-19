"""
Advanced Cache Manager with Intelligent Optimization
Multi-level caching with predictive loading and memory optimization
"""

import asyncio
import logging
import time
import hashlib
import json
import gc
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import weakref
import threading
from functools import wraps
import psutil
import numpy as np

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata"""
    data: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: int = 3600
    priority: float = 1.0  # Higher = more important
    cache_level: str = "l1"  # l1, l2, l3
    compression_ratio: float = 1.0
    hit_rate: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.created_at > self.ttl
    
    def access(self):
        """Record access"""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """Get age in seconds"""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """Get idle time in seconds"""
        return time.time() - self.accessed_at


@dataclass
class CacheStats:
    """Comprehensive cache statistics"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    compression_savings: float = 0.0
    memory_usage_mb: float = 0.0
    hit_rate: float = 0.0
    avg_access_time_ms: float = 0.0
    cache_efficiency: float = 0.0


class IntelligentEvictionPolicy:
    """Advanced cache eviction with multiple strategies"""
    
    def __init__(self):
        self.eviction_strategies = {
            'lru': self._lru_eviction,
            'lfu': self._lfu_eviction,
            'adaptive': self._adaptive_eviction,
            'size_based': self._size_based_eviction,
            'priority_based': self._priority_based_eviction
        }
    
    def _lru_eviction(self, entries: Dict[str, CacheEntry], max_entries: int) -> List[str]:
        """Least Recently Used eviction"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].accessed_at)
        return [key for key, _ in sorted_entries[:len(entries) - max_entries]]
    
    def _lfu_eviction(self, entries: Dict[str, CacheEntry], max_entries: int) -> List[str]:
        """Least Frequently Used eviction"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].access_count)
        return [key for key, _ in sorted_entries[:len(entries) - max_entries]]
    
    def _adaptive_eviction(self, entries: Dict[str, CacheEntry], max_entries: int) -> List[str]:
        """Adaptive eviction based on multiple factors"""
        # Calculate score based on access count, recency, and size
        scores = {}
        current_time = time.time()
        
        for key, entry in entries.items():
            # Normalize factors
            recency_score = 1.0 / (current_time - entry.accessed_at + 1)
            frequency_score = entry.access_count
            size_penalty = entry.size_bytes / 1024 / 1024  # MB
            
            # Combined score (higher = keep)
            score = (recency_score * 0.4 + frequency_score * 0.4 - size_penalty * 0.2)
            scores[key] = score
        
        # Sort by score and evict lowest
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k])
        return sorted_keys[:len(entries) - max_entries]
    
    def _size_based_eviction(self, entries: Dict[str, CacheEntry], max_size_bytes: int) -> List[str]:
        """Size-based eviction"""
        current_size = sum(entry.size_bytes for entry in entries.values())
        if current_size <= max_size_bytes:
            return []
        
        # Sort by size (largest first) and evict until under limit
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].size_bytes, reverse=True)
        evict_keys = []
        remaining_size = current_size
        
        for key, entry in sorted_entries:
            if remaining_size <= max_size_bytes:
                break
            evict_keys.append(key)
            remaining_size -= entry.size_bytes
        
        return evict_keys
    
    def _priority_based_eviction(self, entries: Dict[str, CacheEntry], max_entries: int) -> List[str]:
        """Priority-based eviction"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].priority)
        return [key for key, _ in sorted_entries[:len(entries) - max_entries]]


class PredictiveCache:
    """Predictive caching based on access patterns"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.access_patterns: List[str] = []
        self.pattern_weights: Dict[str, float] = {}
        self.prediction_threshold = 0.3
    
    def record_access(self, key: str):
        """Record cache access for pattern analysis"""
        self.access_patterns.append(key)
        
        # Keep only recent accesses
        if len(self.access_patterns) > self.window_size:
            self.access_patterns.pop(0)
    
    def predict_next_accesses(self, current_key: str, max_predictions: int = 5) -> List[str]:
        """Predict next likely cache accesses"""
        predictions = []
        
        # Find patterns where current_key appears
        for i, key in enumerate(self.access_patterns[:-1]):
            if key == current_key and i + 1 < len(self.access_patterns):
                next_key = self.access_patterns[i + 1]
                predictions.append(next_key)
        
        # Count and weight predictions
        prediction_counts = {}
        for pred in predictions:
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
        
        # Sort by frequency and return top predictions
        sorted_predictions = sorted(prediction_counts.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        return [key for key, count in sorted_predictions[:max_predictions] 
                if count >= len(predictions) * self.prediction_threshold]


class AdvancedCacheManager:
    """Advanced cache manager with intelligent optimization"""
    
    def __init__(self, redis_url: Optional[str] = None,
                 max_memory_mb: int = 1024,
                 compression_enabled: bool = True,
                 predictive_caching: bool = True):
        
        # Configuration
        self.redis_url = redis_url
        self.max_memory_mb = max_memory_mb
        self.compression_enabled = compression_enabled
        self.predictive_caching = predictive_caching
        
        # Cache storage
        self.l1_cache: Dict[str, CacheEntry] = OrderedDict()
        self.redis_client: Optional[Any] = None
        
        # Optimization components
        self.eviction_policy = IntelligentEvictionPolicy()
        self.predictive_cache = PredictiveCache() if predictive_caching else None
        
        # Statistics
        self.stats = CacheStats()
        self.access_times: List[float] = []
        
        # Memory monitoring
        self.memory_monitor_thread = None
        self.monitoring_enabled = True
        
        # Compression
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 1.0
        }
    
    async def initialize(self):
        """Initialize cache manager with optimizations"""
        try:
            # Initialize Redis if available
            if REDIS_AVAILABLE and self.redis_url:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                logger.info("✅ Redis cache connection established")
            else:
                logger.info("ℹ️  Using L1 cache only")
            
            # Start memory monitoring
            if self.monitoring_enabled:
                self._start_memory_monitoring()
            
            # Run initial optimization
            await self._optimize_cache()
            
            logger.info("✅ Advanced cache manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Cache manager initialization failed: {e}")
            raise
    
    def _start_memory_monitoring(self):
        """Start background memory monitoring"""
        def monitor_memory():
            while self.monitoring_enabled:
                try:
                    # Get memory usage
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    
                    # Update stats
                    self.stats.memory_usage_mb = memory_mb
                    
                    # Trigger eviction if memory usage is high
                    if memory_mb > self.max_memory_mb * 0.9:
                        asyncio.create_task(self._emergency_eviction())
                    
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.warning(f"Memory monitoring error: {e}")
                    time.sleep(30)
        
        self.memory_monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        self.memory_monitor_thread.start()
    
    async def _emergency_eviction(self):
        """Emergency eviction when memory usage is high"""
        logger.warning("🚨 High memory usage detected, triggering emergency eviction")
        
        # Evict 50% of cache entries
        evict_count = len(self.l1_cache) // 2
        if evict_count > 0:
            # Use adaptive eviction for emergency
            evict_keys = self.eviction_policy._adaptive_eviction(self.l1_cache, len(self.l1_cache) - evict_count)
            
            for key in evict_keys:
                if key in self.l1_cache:
                    del self.l1_cache[key]
                    self.stats.eviction_count += 1
            
            logger.info(f"🚨 Emergency eviction completed: {len(evict_keys)} entries removed")
    
    async def get(self, key: str, fetch_func: Optional[Callable] = None, 
                  ttl: int = 3600, priority: float = 1.0) -> Optional[Any]:
        """Get data from cache with intelligent fallback"""
        
        start_time = time.time()
        
        # L1 Cache check
        if entry := self.l1_cache.get(key):
            if not entry.is_expired():
                entry.access()
                self.stats.hit_count += 1
                
                # Record access for prediction
                if self.predictive_cache:
                    self.predictive_cache.record_access(key)
                
                # Update access time for statistics
                access_time = (time.time() - start_time) * 1000
                self.access_times.append(access_time)
                self.stats.avg_access_time_ms = np.mean(self.access_times[-100:])
                
                # Predictive caching
                if self.predictive_cache:
                    await self._predictive_preload(key)
                
                return entry.data
            else:
                del self.l1_cache[key]
        
        self.stats.miss_count += 1
        
        # L2 Cache check (Redis)
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    # Parse cached data
                    entry_data = json.loads(cached_data)
                    entry = CacheEntry(**entry_data)
                    
                    if not entry.is_expired():
                        # Promote to L1 cache
                        await self._set_l1(key, entry)
                        self.stats.hit_count += 1
                        return entry.data
                    else:
                        await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # L3 Fetch (Database/External)
        if fetch_func:
            try:
                data = await fetch_func()
                if data is not None:
                    await self.set(key, data, ttl, priority)
                    return data
            except Exception as e:
                logger.error(f"L3 fetch error: {e}")
        
        return None
    
    async def set(self, key: str, data: Any, ttl: int = 3600, priority: float = 1.0):
        """Set data in cache with optimization"""
        
        # Calculate size
        size_bytes = self._estimate_size(data)
        
        # Create cache entry
        entry = CacheEntry(
            data=data,
            created_at=time.time(),
            accessed_at=time.time(),
            ttl=ttl,
            priority=priority,
            size_bytes=size_bytes
        )
        
        # Store in L1 cache
        await self._set_l1(key, entry)
        
        # Store in L2 cache (Redis)
        if self.redis_client:
            try:
                entry_dict = {
                    'data': data,
                    'created_at': entry.created_at,
                    'accessed_at': entry.accessed_at,
                    'access_count': entry.access_count,
                    'size_bytes': entry.size_bytes,
                    'ttl': entry.ttl,
                    'priority': entry.priority,
                    'cache_level': entry.cache_level,
                    'compression_ratio': entry.compression_ratio,
                    'hit_rate': entry.hit_rate
                }
                await self.redis_client.setex(key, ttl, json.dumps(entry_dict))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
    
    async def _set_l1(self, key: str, entry: CacheEntry):
        """Set data in L1 cache with eviction"""
        
        # Check if we need to evict
        if len(self.l1_cache) >= 1000:  # Max L1 entries
            await self._evict_entries()
        
        # Check memory usage
        total_size = sum(e.size_bytes for e in self.l1_cache.values()) + entry.size_bytes
        if total_size > self.max_memory_mb * 1024 * 1024:
            await self._evict_entries()
        
        # Add to cache
        self.l1_cache[key] = entry
        self.stats.total_entries = len(self.l1_cache)
        self.stats.total_size_bytes = sum(e.size_bytes for e in self.l1_cache.values())
    
    async def _evict_entries(self):
        """Evict entries using intelligent policy"""
        if len(self.l1_cache) < 100:  # Don't evict if cache is small
            return
        
        # Use adaptive eviction
        evict_keys = self.eviction_policy._adaptive_eviction(self.l1_cache, len(self.l1_cache) - 100)
        
        for key in evict_keys:
            if key in self.l1_cache:
                del self.l1_cache[key]
                self.stats.eviction_count += 1
        
        logger.info(f"🗑️  Evicted {len(evict_keys)} cache entries")
    
    async def _predictive_preload(self, current_key: str):
        """Predictively preload likely-to-be-accessed data"""
        if not self.predictive_cache:
            return
        
        predictions = self.predictive_cache.predict_next_accesses(current_key)
        
        for predicted_key in predictions:
            # Check if already in cache
            if predicted_key not in self.l1_cache:
                # Try to preload from L2 cache
                if self.redis_client:
                    try:
                        cached_data = await self.redis_client.get(predicted_key)
                        if cached_data:
                            entry_data = json.loads(cached_data)
                            entry = CacheEntry(**entry_data)
                            if not entry.is_expired():
                                await self._set_l1(predicted_key, entry)
                                logger.debug(f"🔮 Preloaded: {predicted_key}")
                    except Exception as e:
                        logger.debug(f"Preload failed for {predicted_key}: {e}")
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate memory size of data"""
        try:
            if isinstance(data, (str, bytes)):
                return len(data)
            elif isinstance(data, (list, tuple)):
                return sum(self._estimate_size(item) for item in data)
            elif isinstance(data, dict):
                return sum(self._estimate_size(v) for v in data.values())
            elif hasattr(data, '__sizeof__'):
                return data.__sizeof__()
            else:
                return len(str(data))
        except Exception:
            return 1024  # Default estimate
    
    async def _optimize_cache(self):
        """Run cache optimization"""
        # Update hit rates
        total_accesses = self.stats.hit_count + self.stats.miss_count
        if total_accesses > 0:
            self.stats.hit_rate = self.stats.hit_count / total_accesses
        
        # Update cache efficiency
        if self.stats.total_size_bytes > 0:
            self.stats.cache_efficiency = self.stats.hit_count / (self.stats.total_size_bytes / 1024 / 1024)
        
        # Log optimization stats
        logger.info(f"📊 Cache optimization - Hit rate: {self.stats.hit_rate:.2%}")
        logger.info(f"   Memory usage: {self.stats.memory_usage_mb:.1f}MB")
        logger.info(f"   Cache efficiency: {self.stats.cache_efficiency:.2f}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        await self._optimize_cache()
        
        return {
            "total_entries": self.stats.total_entries,
            "total_size_mb": self.stats.total_size_bytes / 1024 / 1024,
            "hit_count": self.stats.hit_count,
            "miss_count": self.stats.miss_count,
            "hit_rate": self.stats.hit_rate,
            "eviction_count": self.stats.eviction_count,
            "memory_usage_mb": self.stats.memory_usage_mb,
            "avg_access_time_ms": self.stats.avg_access_time_ms,
            "cache_efficiency": self.stats.cache_efficiency,
            "compression_savings": self.compression_stats['compression_ratio']
        }
    
    async def clear_cache(self):
        """Clear all cache levels"""
        self.l1_cache.clear()
        
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
                logger.info("🗑️  Cleared all cache levels")
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
    
    async def close(self):
        """Cleanup cache manager"""
        self.monitoring_enabled = False
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("✅ Cache manager closed")


# Global cache manager instance
cache_manager = AdvancedCacheManager()


async def get_cache_manager() -> AdvancedCacheManager:
    """Get the global cache manager instance"""
    return cache_manager


def cached(ttl: int = 3600, priority: float = 1.0, key_prefix: str = ""):
    """Advanced caching decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [str(arg) for arg in args]
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            key_string = "|".join(key_parts)
            cache_key = f"{key_prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
            
            # Get cache manager
            cache_mgr = await get_cache_manager()
            
            # Try to get from cache
            cached_result = await cache_mgr.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_mgr.set(cache_key, result, ttl, priority)
            
            return result
        return wrapper
    return decorator 