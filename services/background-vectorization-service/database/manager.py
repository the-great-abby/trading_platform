"""
Database manager for the Background Vectorization Service
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
import asyncpg
from datetime import datetime

from .models import DatabaseSchema, DatabaseQueries, VectorizationJob, VectorizationStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the database connection pool and create tables."""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Create tables
            await self._create_tables()
            
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database manager closed")
    
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database manager not initialized")
        return await self.pool.acquire()
    
    async def _create_tables(self):
        """Create necessary database tables."""
        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute(DatabaseSchema.CREATE_VECTORIZATION_JOBS_TABLE)
            await conn.execute(DatabaseSchema.CREATE_VECTORIZATION_LOGS_TABLE)
            await conn.execute(DatabaseSchema.CREATE_VECTORIZATION_METRICS_TABLE)
            
            # Create indexes
            for index_sql in DatabaseSchema.CREATE_INDEXES:
                await conn.execute(index_sql)
            
            logger.info("Database tables and indexes created")
    
    async def insert_job(self, job: VectorizationJob) -> str:
        """Insert a new vectorization job."""
        async with self.pool.acquire() as conn:
            job_id = await conn.fetchval(
                DatabaseQueries.INSERT_JOB,
                job.job_id,
                job.data_type,
                job.symbol,
                job.data,
                job.priority,
                job.created_at
            )
            logger.info(f"Inserted job: {job_id}")
            return job_id
    
    async def update_job_status(self, job_id: str, status: str, progress: float = 0.0, 
                               message: Optional[str] = None, started_at: Optional[datetime] = None,
                               completed_at: Optional[datetime] = None, retry_count: int = 0):
        """Update the status of a vectorization job."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                DatabaseQueries.UPDATE_JOB_STATUS,
                job_id, status, progress, message, started_at, completed_at, retry_count
            )
            logger.debug(f"Updated job {job_id} status to {status}")
    
    async def get_job_status(self, job_id: str) -> Optional[VectorizationStatus]:
        """Get the status of a specific job."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(DatabaseQueries.GET_JOB_STATUS, job_id)
            
            if row:
                return VectorizationStatus(
                    job_id=row['job_id'],
                    status=row['status'],
                    progress=row['progress'],
                    message=row['message'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    retry_count=row['retry_count']
                )
            return None
    
    async def get_pending_jobs(self, limit: int = 10) -> List[VectorizationJob]:
        """Get pending jobs ordered by priority and creation time."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(DatabaseQueries.GET_PENDING_JOBS, limit)
            
            jobs = []
            for row in rows:
                job = VectorizationJob(
                    job_id=row['job_id'],
                    data_type=row['data_type'],
                    symbol=row['symbol'],
                    data=row['data'],
                    priority=row['priority'],
                    created_at=row['created_at']
                )
                jobs.append(job)
            
            return jobs
    
    async def get_jobs_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs by status."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(DatabaseQueries.GET_JOBS_BY_STATUS, status, limit)
            
            jobs = []
            for row in rows:
                jobs.append({
                    'job_id': row['job_id'],
                    'data_type': row['data_type'],
                    'symbol': row['symbol'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'progress': row['progress'],
                    'message': row['message']
                })
            
            return jobs
    
    async def get_jobs_by_data_type(self, data_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs by data type."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(DatabaseQueries.GET_JOBS_BY_DATA_TYPE, data_type, limit)
            
            jobs = []
            for row in rows:
                jobs.append({
                    'job_id': row['job_id'],
                    'status': row['status'],
                    'progress': row['progress'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None
                })
            
            return jobs
    
    async def get_jobs_by_symbol(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs by symbol."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(DatabaseQueries.GET_JOBS_BY_SYMBOL, symbol, limit)
            
            jobs = []
            for row in rows:
                jobs.append({
                    'job_id': row['job_id'],
                    'data_type': row['data_type'],
                    'status': row['status'],
                    'progress': row['progress'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None
                })
            
            return jobs
    
    async def insert_log(self, job_id: str, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Insert a log entry for a job."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                DatabaseQueries.INSERT_LOG,
                job_id, level, message, metadata or {}
            )
    
    async def insert_metric(self, metric_name: str, metric_value: float, metadata: Optional[Dict[str, Any]] = None):
        """Insert a metric value."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                DatabaseQueries.INSERT_METRIC,
                metric_name, metric_value, metadata or {}
            )
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of vectorization metrics."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(DatabaseQueries.GET_METRICS_SUMMARY)
            
            if row:
                total_jobs = row['total_jobs'] or 0
                completed_jobs = row['completed_jobs'] or 0
                failed_jobs = row['failed_jobs'] or 0
                
                success_rate = None
                if total_jobs > 0:
                    success_rate = (completed_jobs / total_jobs) * 100
                
                return {
                    'total_jobs': total_jobs,
                    'pending_jobs': row['pending_jobs'] or 0,
                    'processing_jobs': row['processing_jobs'] or 0,
                    'completed_jobs': completed_jobs,
                    'failed_jobs': failed_jobs,
                    'avg_processing_time': row['avg_processing_time'],
                    'success_rate': success_rate
                }
            
            return {
                'total_jobs': 0,
                'pending_jobs': 0,
                'processing_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'avg_processing_time': None,
                'success_rate': None
            }
    
    async def cleanup_old_data(self):
        """Clean up old jobs, logs, and metrics."""
        async with self.pool.acquire() as conn:
            try:
                # Clean up old jobs
                deleted_jobs = await conn.execute(DatabaseQueries.CLEANUP_OLD_JOBS)
                logger.info(f"Cleaned up old jobs: {deleted_jobs}")
                
                # Clean up old logs
                deleted_logs = await conn.execute(DatabaseQueries.CLEANUP_OLD_LOGS)
                logger.info(f"Cleaned up old logs: {deleted_logs}")
                
                # Clean up old metrics
                deleted_metrics = await conn.execute(DatabaseQueries.CLEANUP_OLD_METRICS)
                logger.info(f"Cleaned up old metrics: {deleted_metrics}")
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
