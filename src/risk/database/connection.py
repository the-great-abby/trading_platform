"""
Database Connection Management

Provides database connection and session management for the comprehensive
risk management framework.
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import redis
from redis import Redis

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection and session management.
    
    Provides centralized database connection management with connection pooling,
    health monitoring, and session lifecycle management.
    """
    
    def __init__(self):
        """Initialize database manager."""
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.redis_client: Optional[Redis] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connections."""
        if self._initialized:
            return
        
        logger.info("Initializing database connections")
        
        try:
            # Initialize PostgreSQL connection
            self._initialize_postgresql()
            
            # Initialize Redis connection
            self._initialize_redis()
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {str(e)}")
            raise
    
    def _initialize_postgresql(self) -> None:
        """Initialize PostgreSQL connection."""
        # Get database configuration from environment variables
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "trading_risk")
        db_user = os.getenv("DB_USER", "risk_user")
        db_password = os.getenv("DB_PASSWORD", "risk_password")
        
        # Build connection string
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create engine with connection pooling
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"PostgreSQL connection initialized: {db_host}:{db_port}/{db_name}")
    
    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        # Get Redis configuration from environment variables
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        # Create Redis client
        redis_kwargs = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
        if redis_password:
            redis_kwargs["password"] = redis_password
        
        self.redis_client = redis.Redis(**redis_kwargs)
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info(f"Redis connection initialized: {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {str(e)}")
            self.redis_client = None
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup.
        
        Yields:
            Database session
        """
        if not self._initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_redis(self) -> Optional[Redis]:
        """
        Get Redis client.
        
        Returns:
            Redis client or None if not available
        """
        if not self._initialized:
            self.initialize()
        
        return self.redis_client
    
    def health_check(self) -> dict:
        """
        Perform database health check.
        
        Returns:
            Dictionary with health status
        """
        health_status = {
            "postgresql": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None}
        }
        
        # Check PostgreSQL
        try:
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(sa.text("SELECT 1"))
                health_status["postgresql"]["status"] = "healthy"
            else:
                health_status["postgresql"]["status"] = "not_initialized"
        except Exception as e:
            health_status["postgresql"]["status"] = "unhealthy"
            health_status["postgresql"]["error"] = str(e)
        
        # Check Redis
        try:
            if self.redis_client:
                self.redis_client.ping()
                health_status["redis"]["status"] = "healthy"
            else:
                health_status["redis"]["status"] = "not_initialized"
        except Exception as e:
            health_status["redis"]["status"] = "unhealthy"
            health_status["redis"]["error"] = str(e)
        
        return health_status
    
    def close(self) -> None:
        """Close database connections."""
        logger.info("Closing database connections")
        
        if self.engine:
            self.engine.dispose()
            self.engine = None
        
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
        
        self.SessionLocal = None
        self._initialized = False
        
        logger.info("Database connections closed")


# Global database manager instance
_db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    return _db_manager


def get_db_session() -> Session:
    """
    Get database session.
    
    Returns:
        Database session
    """
    db_manager = get_db_manager()
    return db_manager.SessionLocal()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup.
    
    Yields:
        Database session
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


def get_redis_client() -> Optional[Redis]:
    """
    Get Redis client.
    
    Returns:
        Redis client or None if not available
    """
    db_manager = get_db_manager()
    return db_manager.get_redis()


def initialize_database() -> None:
    """
    Initialize database connections.
    
    This function should be called at application startup.
    """
    db_manager = get_db_manager()
    db_manager.initialize()


def close_database() -> None:
    """
    Close database connections.
    
    This function should be called at application shutdown.
    """
    db_manager = get_db_manager()
    db_manager.close()


def health_check() -> dict:
    """
    Perform database health check.
    
    Returns:
        Dictionary with health status
    """
    db_manager = get_db_manager()
    return db_manager.health_check()


# Database metadata for table creation
metadata = MetaData()


def create_tables() -> None:
    """
    Create database tables.
    
    This function should be called after defining all models.
    """
    db_manager = get_db_manager()
    if not db_manager.engine:
        raise RuntimeError("Database not initialized")
    
    # Import all models to ensure they're registered
    from ..repositories.risk_metrics_repository import RiskMetricsDB
    from ..repositories.stress_test_repository import StressTestResultDB
    from ..repositories.correlation_analysis_repository import CorrelationAnalysisDB
    from ..repositories.compliance_report_repository import ComplianceReportDB
    from ..repositories.risk_limits_repository import RiskLimitsDB
    from ..repositories.risk_alert_repository import RiskAlertDB
    from ..repositories.risk_contributions_repository import RiskContributionsDB
    
    try:
        metadata.create_all(db_manager.engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def drop_tables() -> None:
    """
    Drop database tables.
    
    WARNING: This will delete all data!
    """
    db_manager = get_db_manager()
    if not db_manager.engine:
        raise RuntimeError("Database not initialized")
    
    try:
        metadata.drop_all(db_manager.engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise

