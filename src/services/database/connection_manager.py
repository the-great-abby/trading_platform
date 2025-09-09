"""
Database Connection Manager
Handles database connections and connection pooling
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections and connection pooling"""
    
    def __init__(self, database_url: str, min_connections: int = 5, max_connections: int = 20):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the database connection pool"""
        if self.pool is not None:
            return
        
        async with self._connection_lock:
            if self.pool is not None:
                return
            
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'trading-system-cqrs-api',
                        'timezone': 'UTC'
                    }
                )
                logger.info(f"Database connection pool initialized with {self.min_connections}-{self.max_connections} connections")
                
                # Test the connection
                async with self.pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                logger.info("Database connection test successful")
                
            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {e}")
                raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if self.pool is None:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return the result"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row from the database"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        """Fetch multiple rows from the database"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            if self.pool is None:
                return {"status": "disconnected", "error": "Pool not initialized"}
            
            async with self.get_connection() as conn:
                result = await conn.fetchrow("SELECT 1 as health_check, NOW() as timestamp")
                return {
                    "status": "healthy",
                    "pool_size": self.pool.get_size(),
                    "idle_connections": self.pool.get_idle_size(),
                    "timestamp": result["timestamp"].isoformat() if result else None
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None


async def get_connection_manager() -> DatabaseConnectionManager:
    """Get the global database connection manager"""
    global _connection_manager
    if _connection_manager is None:
        raise RuntimeError("Database connection manager not initialized")
    return _connection_manager


async def initialize_database(database_url: str, min_connections: int = 5, max_connections: int = 20) -> DatabaseConnectionManager:
    """Initialize the global database connection manager"""
    global _connection_manager
    _connection_manager = DatabaseConnectionManager(database_url, min_connections, max_connections)
    await _connection_manager.initialize()
    return _connection_manager


async def close_database():
    """Close the global database connection manager"""
    global _connection_manager
    if _connection_manager is not None:
        await _connection_manager.close()
        _connection_manager = None
