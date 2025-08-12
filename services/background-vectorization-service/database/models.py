"""
Database models for the Background Vectorization Service
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class VectorizationJob(BaseModel):
    """Model for a vectorization job."""
    job_id: str
    data_type: str  # "market_data", "news", "earnings"
    symbol: Optional[str] = None
    data: Dict[str, Any]
    priority: int = 1
    created_at: datetime
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    progress: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

class VectorizationStatus(BaseModel):
    """Model for vectorization job status."""
    job_id: str
    status: str
    progress: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

class VectorizationMetrics(BaseModel):
    """Model for vectorization service metrics."""
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    queue_size: int
    avg_processing_time: Optional[float] = None
    success_rate: Optional[float] = None
    last_updated: datetime

class DatabaseSchema:
    """Database schema definitions for vectorization tracking."""
    
    CREATE_VECTORIZATION_JOBS_TABLE = """
    CREATE TABLE IF NOT EXISTS vectorization_jobs (
        job_id VARCHAR(255) PRIMARY KEY,
        data_type VARCHAR(50) NOT NULL,
        symbol VARCHAR(20),
        data JSONB NOT NULL,
        priority INTEGER DEFAULT 1,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        status VARCHAR(20) DEFAULT 'pending',
        progress FLOAT DEFAULT 0.0,
        message TEXT,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3
    );
    """
    
    CREATE_VECTORIZATION_LOGS_TABLE = """
    CREATE TABLE IF NOT EXISTS vectorization_logs (
        id SERIAL PRIMARY KEY,
        job_id VARCHAR(255) NOT NULL,
        level VARCHAR(20) NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        metadata JSONB,
        FOREIGN KEY (job_id) REFERENCES vectorization_jobs(job_id)
    );
    """
    
    CREATE_VECTORIZATION_METRICS_TABLE = """
    CREATE TABLE IF NOT EXISTS vectorization_metrics (
        id SERIAL PRIMARY KEY,
        metric_name VARCHAR(100) NOT NULL,
        metric_value FLOAT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        metadata JSONB
    );
    """
    
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_vectorization_jobs_status ON vectorization_jobs(status);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_jobs_data_type ON vectorization_jobs(data_type);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_jobs_symbol ON vectorization_jobs(symbol);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_jobs_created_at ON vectorization_jobs(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_logs_job_id ON vectorization_logs(job_id);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_logs_timestamp ON vectorization_logs(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_vectorization_metrics_name_timestamp ON vectorization_metrics(metric_name, timestamp);"
    ]

class DatabaseQueries:
    """Common database queries for vectorization operations."""
    
    INSERT_JOB = """
    INSERT INTO vectorization_jobs (
        job_id, data_type, symbol, data, priority, created_at
    ) VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (job_id) DO UPDATE SET
        status = EXCLUDED.status,
        progress = EXCLUDED.progress,
        message = EXCLUDED.message,
        started_at = EXCLUDED.started_at,
        completed_at = EXCLUDED.completed_at,
        retry_count = EXCLUDED.retry_count
    RETURNING job_id;
    """
    
    UPDATE_JOB_STATUS = """
    UPDATE vectorization_jobs 
    SET status = $2, progress = $3, message = $4, 
        started_at = $5, completed_at = $6, retry_count = $7
    WHERE job_id = $1;
    """
    
    GET_PENDING_JOBS = """
    SELECT job_id, data_type, symbol, data, priority, created_at
    FROM vectorization_jobs 
    WHERE status = 'pending' 
    ORDER BY priority DESC, created_at ASC
    LIMIT $1;
    """
    
    GET_JOB_STATUS = """
    SELECT job_id, status, progress, message, started_at, completed_at, retry_count
    FROM vectorization_jobs 
    WHERE job_id = $1;
    """
    
    GET_JOBS_BY_STATUS = """
    SELECT job_id, data_type, symbol, created_at, progress, message
    FROM vectorization_jobs 
    WHERE status = $1
    ORDER BY created_at DESC
    LIMIT $2;
    """
    
    GET_JOBS_BY_DATA_TYPE = """
    SELECT job_id, status, progress, created_at, completed_at
    FROM vectorization_jobs 
    WHERE data_type = $1
    ORDER BY created_at DESC
    LIMIT $2;
    """
    
    GET_JOBS_BY_SYMBOL = """
    SELECT job_id, data_type, status, progress, created_at, completed_at
    FROM vectorization_jobs 
    WHERE symbol = $1
    ORDER BY created_at DESC
    LIMIT $2;
    """
    
    INSERT_LOG = """
    INSERT INTO vectorization_logs (job_id, level, message, metadata)
    VALUES ($1, $2, $3, $4);
    """
    
    INSERT_METRIC = """
    INSERT INTO vectorization_metrics (metric_name, metric_value, metadata)
    VALUES ($1, $2, $3);
    """
    
    GET_METRICS_SUMMARY = """
    SELECT 
        COUNT(*) as total_jobs,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
        AVG(CASE WHEN completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (completed_at - created_at)) END) as avg_processing_time
    FROM vectorization_jobs;
    """
    
    CLEANUP_OLD_JOBS = """
    DELETE FROM vectorization_jobs 
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND status IN ('completed', 'failed');
    """
    
    CLEANUP_OLD_LOGS = """
    DELETE FROM vectorization_logs 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    """
    
    CLEANUP_OLD_METRICS = """
    DELETE FROM vectorization_metrics 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    """
