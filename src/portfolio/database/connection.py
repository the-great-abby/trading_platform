"""
Database Connection Configuration
Handles database connections and connection pooling for portfolio management
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages database connections and connection pooling"""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing database connection to: {self._mask_database_url()}")
            
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
                echo=False,
                future=True
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_connection()
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test database connection"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()
        
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def get_engine(self) -> AsyncEngine:
        """Get database engine"""
        if not self._initialized:
            await self.initialize()
        return self.engine
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
    
    async def execute_scalar(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a scalar query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.scalar()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Test basic connectivity
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                health_check_result = result.scalar()
            
            # Test connection pool status
            pool = self.engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000  # ms
            
            return {
                "status": "healthy",
                "health_check": health_check_result == 1,
                "response_time_ms": response_time,
                "pool_status": pool_status,
                "database_url": self._mask_database_url()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_url": self._mask_database_url()
            }
    
    def _mask_database_url(self) -> str:
        """Mask sensitive information in database URL for logging"""
        if not self.database_url:
            return "No database URL configured"
        
        # Simple masking - replace password with ***
        if "://" in self.database_url:
            parts = self.database_url.split("://")
            if "@" in parts[1]:
                protocol = parts[0]
                rest = parts[1].split("@")
                if ":" in rest[0]:
                    user_pass = rest[0].split(":")
                    user = user_pass[0]
                    masked_rest = f"{user}:***@{rest[1]}"
                else:
                    masked_rest = f"{rest[0]}:***@{rest[1]}"
                return f"{protocol}://{masked_rest}"
        
        return self.database_url
    
    async def close(self) -> None:
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
        self._initialized = False

# Global database connection manager instance
_db_manager: Optional[DatabaseConnectionManager] = None

def get_database_manager() -> DatabaseConnectionManager:
    """Get global database connection manager"""
    global _db_manager
    if _db_manager is None:
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://trading_user:trading_pass@localhost:5432/trading_bot")
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        
        _db_manager = DatabaseConnectionManager(database_url, pool_size, max_overflow)
    
    return _db_manager

async def initialize_database() -> None:
    """Initialize global database connection"""
    db_manager = get_database_manager()
    await db_manager.initialize()

async def get_database_session():
    """Get database session from global manager"""
    db_manager = get_database_manager()
    return db_manager.get_session()

async def close_database() -> None:
    """Close global database connection"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None

# Database configuration from environment
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "postgresql+asyncpg://trading_user:trading_pass@localhost:5432/trading_bot"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
    "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
}

# Repository factory functions
def create_portfolio_repository() -> 'PortfolioRepository':
    """Create portfolio repository with database connection"""
    from ..repositories.portfolio_repository import PortfolioRepository
    db_manager = get_database_manager()
    return PortfolioRepository(db_manager.database_url)

def create_optimization_repository() -> 'OptimizationRepository':
    """Create optimization repository with database connection"""
    from ..repositories.optimization_repository import OptimizationRepository
    db_manager = get_database_manager()
    return OptimizationRepository(db_manager.database_url)

def create_risk_repository() -> 'RiskRepository':
    """Create risk repository with database connection"""
    from ..repositories.risk_repository import RiskRepository
    db_manager = get_database_manager()
    return RiskRepository(db_manager.database_url)

# Database initialization context manager
class DatabaseContext:
    """Context manager for database operations"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    async def __aenter__(self):
        await self.db_manager.initialize()
        return self.db_manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db_manager.close()

# Utility functions for common database operations
async def execute_in_transaction(func, *args, **kwargs):
    """Execute function within a database transaction"""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        try:
            result = await func(session, *args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

async def bulk_insert(table_name: str, data: list, batch_size: int = 1000):
    """Perform bulk insert operation"""
    db_manager = get_database_manager()
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        # Create INSERT query for batch
        if batch:
            columns = list(batch[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            async with db_manager.get_session() as session:
                for row in batch:
                    await session.execute(text(query), row)
                await session.commit()
            
            logger.info(f"Inserted batch {i//batch_size + 1} of {len(data)//batch_size + 1}")

async def get_table_info(table_name: str) -> Dict[str, Any]:
    """Get table information"""
    db_manager = get_database_manager()
    
    # Get table schema
    schema_query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """
    
    columns = await db_manager.execute_query(schema_query, {"table_name": table_name})
    
    # Get table statistics
    stats_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
    row_count = await db_manager.execute_scalar(stats_query)
    
    return {
        "table_name": table_name,
        "columns": [
            {
                "name": col.column_name,
                "type": col.data_type,
                "nullable": col.is_nullable == "YES",
                "default": col.column_default
            }
            for col in columns
        ],
        "row_count": row_count
    }



