"""
Redis Client Integration
Connects RecoverySessionService to Redis for session state management
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as redis

from ...utils.trading_config import get_trade_recovery_config

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for session state management"""
    
    def __init__(self):
        """Initialize Redis client"""
        self.config = get_trade_recovery_config()
        self.redis_config = self.config['redis']
        
        self.client = None
        self.connected = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.from_url(
                self.redis_config['url'],
                db=self.redis_config['db'],
                socket_timeout=self.redis_config['timeout'],
                max_connections=self.redis_config['max_connections'],
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            self.connected = True
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")
    
    async def store_session(self, session_id: str, session_data: Dict[str, Any], 
                          ttl_seconds: int = 86400) -> bool:
        """
        Store recovery session in Redis
        
        Args:
            session_id: Session ID
            session_data: Session data to store
            ttl_seconds: Time to live in seconds (default 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                await self.initialize()
            
            key = f"recovery_session:{session_id}"
            data = json.dumps(session_data, default=str)
            
            await self.client.setex(key, ttl_seconds, data)
            logger.debug(f"Stored session {session_id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get recovery session from Redis
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            if not self.connected:
                await self.initialize()
            
            key = f"recovery_session:{session_id}"
            data = await self.client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete recovery session from Redis
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                await self.initialize()
            
            key = f"recovery_session:{session_id}"
            result = await self.client.delete(key)
            
            logger.debug(f"Deleted session {session_id} from Redis")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(self, account_id: str, status: Optional[str] = None, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recovery sessions for an account
        
        Args:
            account_id: Account ID
            status: Filter by status
            limit: Maximum number of sessions to return
            
        Returns:
            List of session data
        """
        try:
            if not self.connected:
                await self.initialize()
            
            # Get all session keys
            pattern = "recovery_session:*"
            keys = await self.client.keys(pattern)
            
            sessions = []
            for key in keys:
                data = await self.client.get(key)
                if data:
                    session_data = json.loads(data)
                    
                    # Filter by account and status
                    if session_data.get("account_id") == account_id:
                        if status is None or session_data.get("status") == status:
                            sessions.append(session_data)
            
            # Sort by started_at (newest first) and limit
            sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list sessions for account {account_id}: {e}")
            return []
    
    async def store_log(self, log_id: str, log_data: Dict[str, Any], 
                       ttl_seconds: int = 2592000) -> bool:  # 30 days default
        """
        Store recovery log in Redis
        
        Args:
            log_id: Log ID
            log_data: Log data to store
            ttl_seconds: Time to live in seconds (default 30 days)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                await self.initialize()
            
            key = f"recovery_log:{log_id}"
            data = json.dumps(log_data, default=str)
            
            await self.client.setex(key, ttl_seconds, data)
            logger.debug(f"Stored log {log_id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store log {log_id}: {e}")
            return False
    
    async def get_logs(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recovery logs for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of logs to return
            
        Returns:
            List of log data
        """
        try:
            if not self.connected:
                await self.initialize()
            
            # Get log IDs from session logs list
            session_logs_key = f"recovery_session_logs:{session_id}"
            log_ids = await self.client.lrange(session_logs_key, 0, limit - 1)
            
            logs = []
            for log_id in log_ids:
                log_data = await self.client.get(f"recovery_log:{log_id}")
                if log_data:
                    logs.append(json.loads(log_data))
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get logs for session {session_id}: {e}")
            return []
    
    async def add_log_to_session(self, session_id: str, log_id: str) -> bool:
        """
        Add log ID to session logs list
        
        Args:
            session_id: Session ID
            log_id: Log ID to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                await self.initialize()
            
            session_logs_key = f"recovery_session_logs:{session_id}"
            await self.client.lpush(session_logs_key, log_id)
            
            # Set expiration for the list (30 days)
            await self.client.expire(session_logs_key, 2592000)
            
            logger.debug(f"Added log {log_id} to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add log to session: {e}")
            return False
    
    async def set_session_lock(self, session_id: str, ttl_seconds: int = 300) -> bool:
        """
        Set a lock for a session to prevent concurrent modifications
        
        Args:
            session_id: Session ID
            ttl_seconds: Lock time to live in seconds (default 5 minutes)
            
        Returns:
            True if lock acquired, False if already locked
        """
        try:
            if not self.connected:
                await self.initialize()
            
            lock_key = f"recovery_session_lock:{session_id}"
            lock_value = f"locked_{datetime.utcnow().isoformat()}"
            
            # Try to set lock with NX (only if not exists) and EX (expiration)
            result = await self.client.set(lock_key, lock_value, nx=True, ex=ttl_seconds)
            
            if result:
                logger.debug(f"Acquired lock for session {session_id}")
                return True
            else:
                logger.debug(f"Session {session_id} is already locked")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set lock for session {session_id}: {e}")
            return False
    
    async def release_session_lock(self, session_id: str) -> bool:
        """
        Release a session lock
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                await self.initialize()
            
            lock_key = f"recovery_session_lock:{session_id}"
            result = await self.client.delete(lock_key)
            
            if result:
                logger.debug(f"Released lock for session {session_id}")
                return True
            else:
                logger.debug(f"No lock found for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to release lock for session {session_id}: {e}")
            return False
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get Redis session statistics
        
        Returns:
            Statistics about stored sessions
        """
        try:
            if not self.connected:
                await self.initialize()
            
            # Count session keys
            session_keys = await self.client.keys("recovery_session:*")
            log_keys = await self.client.keys("recovery_log:*")
            lock_keys = await self.client.keys("recovery_session_lock:*")
            
            return {
                "total_sessions": len(session_keys),
                "total_logs": len(log_keys),
                "active_locks": len(lock_keys),
                "redis_info": await self.client.info("memory")
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                "total_sessions": 0,
                "total_logs": 0,
                "active_locks": 0,
                "redis_info": {}
            }
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions and logs
        
        Returns:
            Number of cleaned up items
        """
        try:
            if not self.connected:
                await self.initialize()
            
            # Redis TTL will handle expiration automatically
            # This method is for manual cleanup if needed
            cleaned = 0
            
            # Check for sessions that should be cleaned up
            session_keys = await self.client.keys("recovery_session:*")
            for key in session_keys:
                ttl = await self.client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set default expiration
                    await self.client.expire(key, 86400)  # 24 hours
                    cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} sessions")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.connected = False
            logger.info("Redis connection closed")








