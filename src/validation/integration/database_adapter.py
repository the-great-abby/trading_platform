"""
Database adapter for external database connection

This service handles connections to external databases in separate Kubernetes
namespaces, providing abstraction for data persistence and retrieval.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..models.backtest_script import BacktestScript
from ..models.backtest_result import BacktestResult
from ..models.validation_report import ValidationReport
from ..models.test_configuration import TestConfiguration

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Database adapter for external database connections in separate Kubernetes namespaces.
    """
    
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.async_engine = None
        self.sync_engine = None
        self.async_session_factory = None
        self.sync_session_factory = None
        self._connection_pool = None
    
    def _build_connection_string(self) -> str:
        """Build database connection string from environment variables."""
        # Kubernetes service discovery format
        host = os.getenv('VALIDATION_DB_HOST', 'validation-db.trading-system.svc.cluster.local')
        port = os.getenv('VALIDATION_DB_PORT', '5432')
        database = os.getenv('VALIDATION_DB_NAME', 'validation_db')
        username = os.getenv('VALIDATION_DB_USER', 'validation_user')
        password = os.getenv('VALIDATION_DB_PASSWORD', '')
        
        # Connection string format for PostgreSQL
        connection_string = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        
        logger.info(f"Built connection string for host: {host}")
        return connection_string
    
    async def initialize(self) -> None:
        """Initialize database connections and create tables."""
        try:
            # Create async engine
            self.async_engine = create_async_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create sync engine for compatibility
            sync_connection_string = self.connection_string.replace('+asyncpg', '')
            self.sync_engine = create_engine(
                sync_connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create session factories
            self.async_session_factory = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_connection()
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Database adapter initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database adapter: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test database connection."""
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS backtest_scripts (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            function_name VARCHAR(255) NOT NULL,
            class_name VARCHAR(255),
            script_type VARCHAR(50) NOT NULL,
            parameters JSONB DEFAULT '{}',
            expected_outputs JSONB DEFAULT '{}',
            timeout_seconds INTEGER DEFAULT 300,
            dependencies TEXT[] DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_validated_at TIMESTAMP,
            validation_status VARCHAR(20) DEFAULT 'NEVER_RUN'
        );
        
        CREATE TABLE IF NOT EXISTS backtest_results (
            id VARCHAR(36) PRIMARY KEY,
            script_id VARCHAR(36) NOT NULL REFERENCES backtest_scripts(id) ON DELETE CASCADE,
            execution_id VARCHAR(36) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration_seconds REAL NOT NULL,
            status VARCHAR(20) NOT NULL,
            exit_code INTEGER DEFAULT 0,
            stdout TEXT DEFAULT '',
            stderr TEXT DEFAULT '',
            performance_metrics JSONB,
            trade_data JSONB DEFAULT '[]',
            validation_errors JSONB DEFAULT '[]',
            resource_usage JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS validation_reports (
            id VARCHAR(36) PRIMARY KEY,
            report_name VARCHAR(255) NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_scripts INTEGER NOT NULL,
            passed_scripts INTEGER NOT NULL,
            failed_scripts INTEGER NOT NULL,
            error_scripts INTEGER NOT NULL,
            execution_summary JSONB,
            consistency_results JSONB,
            performance_analysis JSONB,
            recommendations JSONB DEFAULT '[]',
            detailed_results JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS test_configurations (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            tolerances JSONB NOT NULL,
            timeouts JSONB NOT NULL,
            validation_rules JSONB NOT NULL,
            execution_settings JSONB NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_backtest_results_script_id ON backtest_results(script_id);
        CREATE INDEX IF NOT EXISTS idx_backtest_results_created_at ON backtest_results(created_at);
        CREATE INDEX IF NOT EXISTS idx_backtest_scripts_name ON backtest_scripts(name);
        CREATE INDEX IF NOT EXISTS idx_validation_reports_generated_at ON validation_reports(generated_at);
        """
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text(create_tables_sql))
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session context manager."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def save_backtest_script(self, script: BacktestScript) -> BacktestScript:
        """Save a backtest script to the database."""
        async with self.get_session() as session:
            try:
                script_data = script.to_dict()
                insert_sql = text("""
                    INSERT INTO backtest_scripts (
                        id, name, file_path, function_name, class_name, script_type,
                        parameters, expected_outputs, timeout_seconds, dependencies,
                        created_at, updated_at, last_validated_at, validation_status
                    ) VALUES (
                        :id, :name, :file_path, :function_name, :class_name, :script_type,
                        :parameters, :expected_outputs, :timeout_seconds, :dependencies,
                        :created_at, :updated_at, :last_validated_at, :validation_status
                    ) ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        file_path = EXCLUDED.file_path,
                        function_name = EXCLUDED.function_name,
                        class_name = EXCLUDED.class_name,
                        script_type = EXCLUDED.script_type,
                        parameters = EXCLUDED.parameters,
                        expected_outputs = EXCLUDED.expected_outputs,
                        timeout_seconds = EXCLUDED.timeout_seconds,
                        dependencies = EXCLUDED.dependencies,
                        updated_at = EXCLUDED.updated_at,
                        last_validated_at = EXCLUDED.last_validated_at,
                        validation_status = EXCLUDED.validation_status
                """)
                
                await session.execute(insert_sql, script_data)
                logger.info(f"Saved backtest script: {script.name}")
                return script
                
            except Exception as e:
                logger.error(f"Failed to save backtest script: {e}")
                raise
    
    async def save_backtest_result(self, result: BacktestResult) -> BacktestResult:
        """Save a backtest result to the database."""
        async with self.get_session() as session:
            try:
                result_data = result.to_dict()
                insert_sql = text("""
                    INSERT INTO backtest_results (
                        id, script_id, execution_id, start_time, end_time, duration_seconds,
                        status, exit_code, stdout, stderr, performance_metrics, trade_data,
                        validation_errors, resource_usage, created_at
                    ) VALUES (
                        :id, :script_id, :execution_id, :start_time, :end_time, :duration_seconds,
                        :status, :exit_code, :stdout, :stderr, :performance_metrics, :trade_data,
                        :validation_errors, :resource_usage, :created_at
                    )
                """)
                
                await session.execute(insert_sql, result_data)
                logger.info(f"Saved backtest result: {result.id}")
                return result
                
            except Exception as e:
                logger.error(f"Failed to save backtest result: {e}")
                raise
    
    async def save_validation_report(self, report: ValidationReport) -> ValidationReport:
        """Save a validation report to the database."""
        async with self.get_session() as session:
            try:
                report_data = report.to_dict()
                insert_sql = text("""
                    INSERT INTO validation_reports (
                        id, report_name, generated_at, total_scripts, passed_scripts,
                        failed_scripts, error_scripts, execution_summary, consistency_results,
                        performance_analysis, recommendations, detailed_results, created_at
                    ) VALUES (
                        :id, :report_name, :generated_at, :total_scripts, :passed_scripts,
                        :failed_scripts, :error_scripts, :execution_summary, :consistency_results,
                        :performance_analysis, :recommendations, :detailed_results, :created_at
                    )
                """)
                
                await session.execute(insert_sql, report_data)
                logger.info(f"Saved validation report: {report.report_name}")
                return report
                
            except Exception as e:
                logger.error(f"Failed to save validation report: {e}")
                raise
    
    async def save_test_configuration(self, config: TestConfiguration) -> TestConfiguration:
        """Save a test configuration to the database."""
        async with self.get_session() as session:
            try:
                config_data = config.to_dict()
                insert_sql = text("""
                    INSERT INTO test_configurations (
                        id, name, description, tolerances, timeouts, validation_rules,
                        execution_settings, is_default, created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :tolerances, :timeouts, :validation_rules,
                        :execution_settings, :is_default, :created_at, :updated_at
                    ) ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        tolerances = EXCLUDED.tolerances,
                        timeouts = EXCLUDED.timeouts,
                        validation_rules = EXCLUDED.validation_rules,
                        execution_settings = EXCLUDED.execution_settings,
                        is_default = EXCLUDED.is_default,
                        updated_at = EXCLUDED.updated_at
                """)
                
                await session.execute(insert_sql, config_data)
                logger.info(f"Saved test configuration: {config.name}")
                return config
                
            except Exception as e:
                logger.error(f"Failed to save test configuration: {e}")
                raise
    
    async def get_backtest_scripts(self, limit: int = 100, offset: int = 0) -> List[BacktestScript]:
        """Get backtest scripts from the database."""
        async with self.get_session() as session:
            try:
                select_sql = text("""
                    SELECT id, name, file_path, function_name, class_name, script_type,
                           parameters, expected_outputs, timeout_seconds, dependencies,
                           created_at, updated_at, last_validated_at, validation_status
                    FROM backtest_scripts
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(select_sql, {"limit": limit, "offset": offset})
                rows = result.fetchall()
                
                scripts = []
                for row in rows:
                    script_data = dict(row._mapping)
                    # Convert datetime strings back to datetime objects
                    for field in ['created_at', 'updated_at', 'last_validated_at']:
                        if script_data[field] and isinstance(script_data[field], str):
                            script_data[field] = datetime.fromisoformat(script_data[field])
                    
                    script = BacktestScript.from_dict(script_data)
                    scripts.append(script)
                
                return scripts
                
            except Exception as e:
                logger.error(f"Failed to get backtest scripts: {e}")
                raise
    
    async def get_backtest_results(self, script_id: Optional[str] = None, 
                                 limit: int = 100, offset: int = 0) -> List[BacktestResult]:
        """Get backtest results from the database."""
        async with self.get_session() as session:
            try:
                if script_id:
                    select_sql = text("""
                        SELECT * FROM backtest_results
                        WHERE script_id = :script_id
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """)
                    params = {"script_id": script_id, "limit": limit, "offset": offset}
                else:
                    select_sql = text("""
                        SELECT * FROM backtest_results
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """)
                    params = {"limit": limit, "offset": offset}
                
                result = await session.execute(select_sql, params)
                rows = result.fetchall()
                
                results = []
                for row in rows:
                    result_data = dict(row._mapping)
                    # Convert datetime strings back to datetime objects
                    for field in ['start_time', 'end_time', 'created_at']:
                        if result_data[field] and isinstance(result_data[field], str):
                            result_data[field] = datetime.fromisoformat(result_data[field])
                    
                    backtest_result = BacktestResult.from_dict(result_data)
                    results.append(backtest_result)
                
                return results
                
            except Exception as e:
                logger.error(f"Failed to get backtest results: {e}")
                raise
    
    async def get_test_configurations(self) -> List[TestConfiguration]:
        """Get test configurations from the database."""
        async with self.get_session() as session:
            try:
                select_sql = text("""
                    SELECT * FROM test_configurations
                    ORDER BY is_default DESC, created_at DESC
                """)
                
                result = await session.execute(select_sql)
                rows = result.fetchall()
                
                configurations = []
                for row in rows:
                    config_data = dict(row._mapping)
                    # Convert datetime strings back to datetime objects
                    for field in ['created_at', 'updated_at']:
                        if config_data[field] and isinstance(config_data[field], str):
                            config_data[field] = datetime.fromisoformat(config_data[field])
                    
                    config = TestConfiguration.from_dict(config_data)
                    configurations.append(config)
                
                return configurations
                
            except Exception as e:
                logger.error(f"Failed to get test configurations: {e}")
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.get_session() as session:
                # Check connection
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()
                
                # Check table counts
                tables = ['backtest_scripts', 'backtest_results', 'validation_reports', 'test_configurations']
                counts = {}
                
                for table in tables:
                    count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = count_result.fetchone()[0]
                
                return {
                    "status": "healthy",
                    "connection": "ok",
                    "tables": counts,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self) -> None:
        """Close database connections."""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
            
            if self.sync_engine:
                self.sync_engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'sync_engine') and self.sync_engine:
            self.sync_engine.dispose()

