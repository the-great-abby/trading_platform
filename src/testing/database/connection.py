#!/usr/bin/env python3
"""
Database connection management for Strategy Engine Testing Framework
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from ..config import get_config

logger = logging.getLogger(__name__)

# Global database instances
engine = None
async_session_maker = None


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def init_database() -> None:
    """Initialize database connection"""
    global engine, async_session_maker
    
    try:
        config = get_config()
        
        # Create async engine
        engine = create_async_engine(
            config.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=config.debug,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    if async_session_maker is None:
        await init_database()
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def close_database() -> None:
    """Close database connection"""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async for session in get_database():
        yield session













