"""
Redis Client for Live Trading Service

Handles Redis operations for caching, session management, and real-time data.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for live trading operations."""
    
    def __init__(self, redis_url: str = None, db: int = 0, timeout: int = 5, max_connections: int = 10):
        """Initialize Redis client."""
        self.redis_url = redis_url or "redis://redis.redis.svc.cluster.local:6379"
        self.db = db
        self.timeout = timeout
        self.max_connections = max_connections
        self.redis: Optional[Redis] = None
        self.pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.pool = redis.ConnectionPool.from_url(
                self.redis_url,
                db=self.db,
                max_connections=self.max_connections,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
                retry_on_timeout=True
            )
            
            self.redis = Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        try:
            if self.redis:
                await self.redis.close()
            if self.pool:
                await self.pool.disconnect()
            logger.info("Disconnected from Redis")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await self.redis.set(key, value, ex=ex)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking Redis key existence {key}: {str(e)}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        try:
            result = await self.redis.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for Redis key {key}: {str(e)}")
            return -1
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """Set hash fields."""
        try:
            # Convert values to JSON strings if they're complex objects
            processed_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    processed_mapping[k] = json.dumps(v)
                else:
                    processed_mapping[k] = str(v)
            
            result = await self.redis.hset(name, mapping=processed_mapping)
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting Redis hash {name}: {str(e)}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value."""
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Error getting Redis hash field {name}.{key}: {str(e)}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        try:
            data = await self.redis.hgetall(name)
            result = {}
            
            for k, v in data.items():
                key = k.decode('utf-8') if isinstance(k, bytes) else k
                value = v.decode('utf-8') if isinstance(v, bytes) else v
                
                # Try to parse as JSON, fallback to string
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Redis hash {name}: {str(e)}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        try:
            return await self.redis.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Error deleting Redis hash fields {name}: {str(e)}")
            return 0
    
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to the left of a list."""
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(json.dumps(value))
                else:
                    processed_values.append(str(value))
            
            return await self.redis.lpush(name, *processed_values)
        except Exception as e:
            logger.error(f"Error pushing to Redis list {name}: {str(e)}")
            return 0
    
    async def rpop(self, name: str) -> Optional[Any]:
        """Pop value from the right of a list."""
        try:
            value = await self.redis.rpop(name)
            if value is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Error popping from Redis list {name}: {str(e)}")
            return None
    
    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """Get range of list values."""
        try:
            values = await self.redis.lrange(name, start, end)
            result = []
            
            for value in values:
                # Try to parse as JSON, fallback to string
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value.decode('utf-8') if isinstance(value, bytes) else value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Redis list range {name}: {str(e)}")
            return []
    
    async def sadd(self, name: str, *values: Any) -> int:
        """Add members to a set."""
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(json.dumps(value))
                else:
                    processed_values.append(str(value))
            
            return await self.redis.sadd(name, *processed_values)
        except Exception as e:
            logger.error(f"Error adding to Redis set {name}: {str(e)}")
            return 0
    
    async def smembers(self, name: str) -> set:
        """Get all members of a set."""
        try:
            members = await self.redis.smembers(name)
            result = set()
            
            for member in members:
                value = member.decode('utf-8') if isinstance(member, bytes) else member
                # Try to parse as JSON, fallback to string
                try:
                    result.add(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.add(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Redis set members {name}: {str(e)}")
            return set()
    
    async def srem(self, name: str, *values: Any) -> int:
        """Remove members from a set."""
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(json.dumps(value))
                else:
                    processed_values.append(str(value))
            
            return await self.redis.srem(name, *processed_values)
        except Exception as e:
            logger.error(f"Error removing from Redis set {name}: {str(e)}")
            return 0
    
    # Trading-specific methods
    
    async def cache_market_data(self, symbol: str, data: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache market data for a symbol."""
        key = f"market_data:{symbol}"
        return await self.set(key, data, ex=ttl)
    
    async def get_cached_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached market data for a symbol."""
        key = f"market_data:{symbol}"
        return await self.get(key)
    
    async def cache_account_balance(self, account_id: str, balance: Dict[str, Any], ttl: int = 60) -> bool:
        """Cache account balance."""
        key = f"account_balance:{account_id}"
        return await self.set(key, balance, ex=ttl)
    
    async def get_cached_account_balance(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get cached account balance."""
        key = f"account_balance:{account_id}"
        return await self.get(key)
    
    async def set_emergency_stop(self, account_id: str, reason: str, ttl: int = None) -> bool:
        """Set emergency stop flag."""
        key = f"emergency_stop:{account_id}"
        data = {
            "active": True,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.set(key, data, ex=ttl)
    
    async def clear_emergency_stop(self, account_id: str) -> bool:
        """Clear emergency stop flag."""
        key = f"emergency_stop:{account_id}"
        return await self.delete(key)
    
    async def is_emergency_stop_active(self, account_id: str) -> bool:
        """Check if emergency stop is active."""
        key = f"emergency_stop:{account_id}"
        return await self.exists(key)
    
    async def get_emergency_stop_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get emergency stop information."""
        key = f"emergency_stop:{account_id}"
        return await self.get(key)
    
    async def cache_position_data(self, account_id: str, positions: List[Dict[str, Any]], ttl: int = 30) -> bool:
        """Cache position data."""
        key = f"positions:{account_id}"
        return await self.set(key, positions, ex=ttl)
    
    async def get_cached_position_data(self, account_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached position data."""
        key = f"positions:{account_id}"
        return await self.get(key)
    
    async def add_trade_signal(self, account_id: str, signal: Dict[str, Any]) -> bool:
        """Add trade signal to queue."""
        key = f"trade_signals:{account_id}"
        signal["timestamp"] = datetime.utcnow().isoformat()
        return await self.lpush(key, signal) > 0
    
    async def get_trade_signals(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trade signals from queue."""
        key = f"trade_signals:{account_id}"
        return await self.lrange(key, 0, limit - 1)
    
    async def pop_trade_signal(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Pop trade signal from queue."""
        key = f"trade_signals:{account_id}"
        return await self.rpop(key)
    
    async def set_market_hours_status(self, status: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache market hours status."""
        key = "market_hours_status"
        return await self.set(key, status, ex=ttl)
    
    async def get_market_hours_status(self) -> Optional[Dict[str, Any]]:
        """Get cached market hours status."""
        key = "market_hours_status"
        return await self.get(key)
    
    async def increment_daily_trade_count(self, account_id: str) -> int:
        """Increment daily trade count."""
        key = f"daily_trades:{account_id}:{datetime.utcnow().date()}"
        return await self.redis.incr(key)
    
    async def get_daily_trade_count(self, account_id: str) -> int:
        """Get daily trade count."""
        key = f"daily_trades:{account_id}:{datetime.utcnow().date()}"
        count = await self.redis.get(key)
        return int(count) if count else 0
    
    async def set_daily_trade_count_ttl(self, account_id: str, ttl: int = 86400) -> bool:
        """Set TTL for daily trade count."""
        key = f"daily_trades:{account_id}:{datetime.utcnow().date()}"
        return await self.expire(key, ttl)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check."""
        try:
            start_time = datetime.utcnow()
            await self.redis.ping()
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection_pool": "active",
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
