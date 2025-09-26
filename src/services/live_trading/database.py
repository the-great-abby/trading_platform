"""
Database configuration and session management.

Handles database connections and session management for the live trading system.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@timescaledb-service:5432/trading_db"
)

# Redis configuration
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis.redis.svc.cluster.local:6379"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for better async performance
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis client instance
redis_client = RedisClient(redis_url=REDIS_URL)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database tables and Redis connection."""
    try:
        # Initialize database tables
        from .models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
        
        # Initialize Redis connection
        await redis_client.connect()
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Database/Redis initialization error: {str(e)}")
        raise


async def close_database():
    """Close database and Redis connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
        
        await redis_client.disconnect()
        logger.info("Redis connections closed")
        
    except Exception as e:
        logger.error(f"Error closing database/Redis: {str(e)}")


async def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    return redis_client
