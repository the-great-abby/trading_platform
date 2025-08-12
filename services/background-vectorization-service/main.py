#!/usr/bin/env python3
"""
Background Vectorization Service
Automatically vectorizes new market data, news, and earnings data for RAG search.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import aiohttp
import asyncpg

# Import our custom modules
from database.manager import DatabaseManager
from vectorizer.market_data_vectorizer import MarketDataVectorizer
from vectorizer.news_vectorizer import NewsVectorizer
from vectorizer.earnings_vectorizer import EarningsVectorizer
from scheduler.scheduler import VectorizationScheduler

# Import Phase 4 components
from integration.webhook_handler import router as webhook_router
from monitoring.alerting import alert_manager, performance_monitor, resource_monitor, integration_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Background Vectorization Service",
    description="Automatically vectorizes market data, news, and earnings for RAG search",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Phase 4 routers
app.include_router(webhook_router)

# Configuration
VECTOR_STORAGE_URL = os.environ.get("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
LLM_PROXY_URL = os.environ.get("LLM_PROXY_URL", "http://llm-proxy:12001")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb:5432/trading_bot")

# Vectorization configuration
VECTORIZATION_CONFIG = {
    "batch_size": int(os.environ.get("VECTORIZATION_BATCH_SIZE", "10")),
    "max_retries": int(os.environ.get("VECTORIZATION_MAX_RETRIES", "3")),
    "retry_delay": int(os.environ.get("VECTORIZATION_RETRY_DELAY", "60")),
    "market_data_interval": int(os.environ.get("MARKET_DATA_INTERVAL", "3600")),  # 1 hour
    "news_interval": int(os.environ.get("NEWS_INTERVAL", "1800")),  # 30 minutes
    "earnings_interval": int(os.environ.get("EARNINGS_INTERVAL", "7200")),  # 2 hours
    "enable_auto_vectorization": os.environ.get("ENABLE_AUTO_VECTORIZATION", "true").lower() == "true"
}

# Pydantic models
class VectorizationJob(BaseModel):
    job_id: str
    data_type: str  # "market_data", "news", "earnings"
    symbol: Optional[str] = None
    data: Dict[str, Any]
    priority: int = 1
    created_at: datetime = datetime.utcnow()

class VectorizationStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Global state
active_jobs: Dict[str, VectorizationJob] = {}
job_status: Dict[str, VectorizationStatus] = {}
vectorization_queue: asyncio.Queue = asyncio.Queue()

# Metrics tracking
vectorization_metrics = {
    "total_jobs_processed": 0,
    "successful_vectorizations": 0,
    "failed_vectorizations": 0,
    "avg_processing_time": 0.0,
    "last_updated": datetime.utcnow()
}

# Service instances
db_manager: Optional[DatabaseManager] = None
market_data_vectorizer: Optional[MarketDataVectorizer] = None
news_vectorizer: Optional[NewsVectorizer] = None
earnings_vectorizer: Optional[EarningsVectorizer] = None
scheduler: Optional[VectorizationScheduler] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the service on startup."""
    global db_manager, market_data_vectorizer, news_vectorizer, earnings_vectorizer, scheduler
    
    logger.info("Starting Background Vectorization Service...")
    
    try:
        # Initialize database manager
        logger.info("Initializing database manager...")
        db_manager = DatabaseManager(DATABASE_URL)
        await db_manager.initialize()
        logger.info("Database manager initialized successfully")
        
        # Initialize vectorizers
        logger.info("Initializing vectorizers...")
        market_data_vectorizer = MarketDataVectorizer(db_manager, VECTOR_STORAGE_URL)
        news_vectorizer = NewsVectorizer(db_manager, VECTOR_STORAGE_URL)
        earnings_vectorizer = EarningsVectorizer(db_manager, VECTOR_STORAGE_URL)
        logger.info("Vectorizers initialized successfully")
        
        # Initialize and start scheduler
        logger.info("Initializing scheduler...")
        scheduler = VectorizationScheduler(
            db_manager, 
            market_data_vectorizer, 
            news_vectorizer, 
            earnings_vectorizer
        )
        await scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Start background workers
        asyncio.create_task(vectorization_worker())
        asyncio.create_task(monitor_new_data())
        
        logger.info("Background Vectorization Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global scheduler
    
    logger.info("Shutting down Background Vectorization Service...")
    
    # Stop the scheduler
    if scheduler:
        await scheduler.stop()
        logger.info("Scheduler stopped")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard page."""
    try:
        with open("templates/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <body>
            <h1>🚀 Background Vectorization Service</h1>
            <p>Service is running! Use these endpoints:</p>
            <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/api/vectorization/status">/api/vectorization/status</a> - Service status</li>
                <li><a href="/api/docs">/api/docs</a> - API documentation</li>
            </ul>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "background-vectorization-service",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len(active_jobs),
        "queue_size": vectorization_queue.qsize(),
        "scheduler_running": scheduler.is_running if scheduler else False,
        "vectorizers_initialized": all([
            market_data_vectorizer is not None,
            news_vectorizer is not None,
            earnings_vectorizer is not None
        ]),
        "database_connected": db_manager is not None
    }

@app.get("/api/vectorization/status")
async def get_vectorization_status():
    """Get overall vectorization status."""
    return {
        "total_jobs": len(job_status),
        "active_jobs": len([j for j in job_status.values() if j.status == "processing"]),
        "completed_jobs": len([j for j in job_status.values() if j.status == "completed"]),
        "failed_jobs": len([j for j in job_status.values() if j.status == "failed"]),
        "queue_size": vectorization_queue.qsize()
    }

@app.get("/api/vectorization/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    return await scheduler.get_scheduler_status()

@app.get("/api/vectorization/metrics")
async def get_vectorization_metrics():
    """Get vectorization service metrics."""
    current_metrics = {
        **vectorization_metrics,
        "active_jobs": len(active_jobs),
        "queue_size": vectorization_queue.qsize(),
        "uptime": (datetime.utcnow() - vectorization_metrics["last_updated"]).total_seconds()
    }
    
    # Phase 4: Enhanced monitoring with alerting
    try:
        await performance_monitor.monitor_performance(current_metrics)
    except Exception as e:
        logger.error(f"Error in performance monitoring: {e}")
    
    return current_metrics

@app.get("/api/vectorization/config")
async def get_vectorization_config():
    """Get current vectorization configuration."""
    return {
        "config": VECTORIZATION_CONFIG,
        "environment": {
            "vector_storage_url": VECTOR_STORAGE_URL,
            "llm_proxy_url": LLM_PROXY_URL,
            "database_url": DATABASE_URL.replace(DATABASE_URL.split('@')[1], "***") if '@' in DATABASE_URL else "***"
        }
    }

@app.get("/api/vectorization/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific vectorization job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status[job_id]

@app.post("/api/vectorization/trigger")
async def trigger_vectorization(background_tasks: BackgroundTasks):
    """Manually trigger vectorization of all available data."""
    background_tasks.add_task(trigger_full_vectorization)
    return {"message": "Vectorization triggered", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/vectorization/jobs")
async def create_vectorization_job(job: VectorizationJob):
    """Create a new vectorization job."""
    try:
        # Add job to queue
        await queue_vectorization_job(job)
        
        # Update job status
        job_status[job.job_id] = VectorizationStatus(
            job_id=job.job_id,
            status="pending",
            progress=0.0
        )
        
        return {
            "message": "Job created successfully",
            "job_id": job.job_id,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"Error creating vectorization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vectorization/jobs/{job_id}")
async def cancel_vectorization_job(job_id: str):
    """Cancel a vectorization job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update job status
    job_status[job_id].status = "cancelled"
    
    # Remove from active jobs if present
    if job_id in active_jobs:
        del active_jobs[job_id]
    
    return {"message": "Job cancelled successfully", "job_id": job_id}

@app.post("/api/vectorization/batch")
async def create_batch_vectorization_jobs(jobs: List[VectorizationJob]):
    """Create multiple vectorization jobs at once."""
    try:
        created_jobs = []
        for job in jobs:
            # Add job to queue
            await queue_vectorization_job(job)
            
            # Update job status
            job_status[job.job_id] = VectorizationStatus(
                job_id=job.job_id,
                status="pending",
                progress=0.0
            )
            
            created_jobs.append({
                "job_id": job.job_id,
                "status": "pending"
            })
        
        return {
            "message": f"Created {len(created_jobs)} jobs successfully",
            "jobs": created_jobs
        }
    except Exception as e:
        logger.error(f"Error creating batch vectorization jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectorization/cleanup")
async def cleanup_old_jobs():
    """Clean up old completed and failed jobs."""
    try:
        # Find old jobs to clean up
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        jobs_to_cleanup = []
        
        for job_id, status in job_status.items():
            if status.completed_at and status.completed_at < cutoff_date:
                jobs_to_cleanup.append(job_id)
            elif status.status == "failed" and status.started_at and status.started_at < cutoff_date:
                jobs_to_cleanup.append(job_id)
        
        # Clean up old jobs
        for job_id in jobs_to_cleanup:
            del job_status[job_id]
            if job_id in active_jobs:
                del active_jobs[job_id]
        
        return {
            "message": f"Cleaned up {len(jobs_to_cleanup)} old jobs",
            "cleaned_jobs": jobs_to_cleanup
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectorization/jobs/{job_id}/retry")
async def retry_vectorization_job(job_id: str):
    """Retry a failed vectorization job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    if status.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    # Check retry limit
    if status.retry_count >= VECTORIZATION_CONFIG["max_retries"]:
        raise HTTPException(status_code=400, detail="Maximum retry limit reached")
    
    try:
        # Reset job status
        status.status = "pending"
        status.progress = 0.0
        status.message = None
        status.retry_count += 1
        
        # Re-queue the job
        if job_id in active_jobs:
            job = active_jobs[job_id]
            await queue_vectorization_job(job)
        
        return {
            "message": "Job queued for retry",
            "job_id": job_id,
            "retry_count": status.retry_count
        }
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts")
async def get_active_alerts():
    """Get all active alerts from the monitoring system."""
    try:
        active_alerts = alert_manager.get_active_alerts()
        return {
            "status": "success",
            "active_alerts_count": len(active_alerts),
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged,
                    "metadata": alert.metadata
                }
                for alert in active_alerts
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        alert_manager.acknowledge_alert(alert_id)
        return {
            "status": "success",
            "message": f"Alert {alert_id} acknowledged",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    try:
        alert_manager.resolve_alert(alert_id)
        return {
            "status": "success",
            "message": f"Alert {alert_id} resolved",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/performance/history")
async def get_performance_history():
    """Get performance metrics history."""
    try:
        return {
            "status": "success",
            "performance_history": performance_monitor.metrics_history,
            "last_check": performance_monitor.last_check.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs")
async def get_api_documentation():
    """Get comprehensive API documentation."""
    return {
        "service": "Background Vectorization Service",
        "version": "1.0.0",
        "description": "Automatically vectorizes market data, news, and earnings for RAG search",
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Service health check with detailed status"
            },
            "vectorization_status": {
                "method": "GET",
                "path": "/api/vectorization/status",
                "description": "Overall vectorization service status"
            },
            "scheduler_status": {
                "method": "GET",
                "path": "/api/vectorization/scheduler/status",
                "description": "Scheduler status and configuration"
            },
            "metrics": {
                "method": "GET",
                "path": "/api/vectorization/metrics",
                "description": "Service performance metrics"
            },
            "config": {
                "method": "GET",
                "path": "/api/vectorization/config",
                "description": "Current service configuration"
            },
            "job_status": {
                "method": "GET",
                "path": "/api/vectorization/jobs/{job_id}",
                "description": "Get status of a specific job"
            },
            "create_job": {
                "method": "POST",
                "path": "/api/vectorization/jobs",
                "description": "Create a new vectorization job"
            },
            "batch_jobs": {
                "method": "POST",
                "path": "/api/vectorization/batch",
                "description": "Create multiple vectorization jobs"
            },
            "cancel_job": {
                "method": "DELETE",
                "path": "/api/vectorization/jobs/{job_id}",
                "description": "Cancel a vectorization job"
            },
            "retry_job": {
                "method": "POST",
                "path": "/api/vectorization/jobs/{job_id}/retry",
                "description": "Retry a failed vectorization job"
            },
            "trigger_vectorization": {
                "method": "POST",
                "path": "/api/vectorization/trigger",
                "description": "Manually trigger vectorization of all available data"
            },
            "cleanup": {
                "method": "POST",
                "path": "/api/vectorization/cleanup",
                "description": "Clean up old completed and failed jobs"
            }
        },
        "data_types": ["market_data", "news", "earnings"],
        "features": [
            "Automatic periodic vectorization",
            "Job queue management",
            "Progress tracking",
            "Retry mechanism",
            "Performance metrics",
            "Configuration management",
            "Health monitoring"
        ],
        "phase4_features": [
            "Webhook integration with data services",
            "Enhanced monitoring and alerting",
            "Production scaling and autoscaling",
            "Automated cronjob scheduling",
            "Integration monitoring and health checks",
            "Production-grade deployment configuration"
        ]
    }

async def trigger_full_vectorization():
    """Trigger vectorization of all available data."""
    logger.info("Triggering full vectorization...")
    
    try:
        # Check for new market data
        await check_and_vectorize_market_data()
        
        # Check for new news data
        await check_and_vectorize_news_data()
        
        # Check for new earnings data
        await check_and_vectorize_earnings_data()
        
        logger.info("Full vectorization completed")
    except Exception as e:
        logger.error(f"Error during full vectorization: {e}")

async def check_and_vectorize_market_data():
    """Check for new market data and vectorize it."""
    logger.info("Checking for new market data...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get recent market data that hasn't been vectorized
        # Use correct table name 'historical_prices'
        query = """
        SELECT DISTINCT symbol, MAX(date) as latest_date
        FROM historical_prices 
        WHERE date >= NOW() - INTERVAL '7 days'
        GROUP BY symbol
        ORDER BY latest_date DESC
        LIMIT 50
        """
        
        rows = await conn.fetch(query)
        await conn.close()
        
        if not rows:
            logger.info("No new market data to vectorize")
            return
        
        logger.info(f"Found {len(rows)} symbols with recent market data")
        
        # Queue vectorization jobs
        for row in rows:
            job = VectorizationJob(
                job_id=f"market_data_{row['symbol']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="market_data",
                symbol=row['symbol'],
                data={"symbol": row['symbol'], "latest_date": row['latest_date'].isoformat()},
                priority=1
            )
            
            await queue_vectorization_job(job)
            
    except Exception as e:
        logger.error(f"Error checking market data: {e}")

async def check_and_vectorize_news_data():
    """Check for new news data and vectorize it."""
    logger.info("Checking for new news data...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get recent news that hasn't been vectorized
        query = """
        SELECT id, title, content, published_at, source
        FROM news_articles 
        WHERE published_at >= NOW() - INTERVAL '7 days'
        AND vectorized = false
        ORDER BY published_at DESC
        LIMIT 100
        """
        
        rows = await conn.fetch(query)
        await conn.close()
        
        if not rows:
            logger.info("No new news data to vectorize")
            return
        
        logger.info(f"Found {len(rows)} news articles to vectorize")
        
        # Queue vectorization jobs
        for row in rows:
            job = VectorizationJob(
                job_id=f"news_{row['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="news",
                data={
                    "id": row['id'],
                    "title": row['title'],
                    "content": row['content'],
                    "published_at": row['published_at'].isoformat(),
                    "source": row['source']
                },
                priority=2
            )
            
            await queue_vectorization_job(job)
            
    except Exception as e:
        logger.error(f"Error checking news data: {e}")

async def check_and_vectorize_earnings_data():
    """Check for new earnings data and vectorize it."""
    logger.info("Checking for new earnings data...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get recent earnings that haven't been vectorized
        query = """
        SELECT id, symbol, quarter, year, eps, revenue, report_date
        FROM earnings_reports 
        WHERE report_date >= NOW() - INTERVAL '90 days'
        AND vectorized = false
        ORDER BY report_date DESC
        LIMIT 50
        """
        
        rows = await conn.fetch(query)
        await conn.close()
        
        if not rows:
            logger.info("No new earnings data to vectorize")
            return
        
        logger.info(f"Found {len(rows)} earnings reports to vectorize")
        
        # Queue vectorization jobs
        for row in rows:
            job = VectorizationJob(
                job_id=f"earnings_{row['symbol']}_{row['quarter']}_{row['year']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="earnings",
                symbol=row['symbol'],
                data={
                    "id": row['id'],
                    "symbol": row['symbol'],
                    "quarter": row['quarter'],
                    "year": row['year'],
                    "eps": row['eps'],
                    "revenue": row['revenue'],
                    "report_date": row['report_date'].isoformat()
                },
                priority=3
            )
            
            await queue_vectorization_job(job)
            
    except Exception as e:
        logger.error(f"Error checking earnings data: {e}")

async def queue_vectorization_job(job: VectorizationJob):
    """Add a vectorization job to the queue."""
    active_jobs[job.job_id] = job
    job_status[job.job_id] = VectorizationStatus(
        job_id=job.job_id,
        status="pending"
    )
    
    await vectorization_queue.put(job)
    logger.info(f"Queued vectorization job: {job.job_id} ({job.data_type})")

async def vectorization_worker():
    """Background worker that processes vectorization jobs."""
    logger.info("Vectorization worker started")
    
    while True:
        try:
            # Get job from queue
            job = await vectorization_queue.get()
            start_time = datetime.utcnow()
            
            # Update status
            job_status[job.job_id].status = "processing"
            job_status[job.job_id].progress = 0.1
            job_status[job.job_id].started_at = start_time
            
            # Update progress to show job is being processed
            job_status[job.job_id].progress = 0.2
            
            logger.info(f"Processing vectorization job: {job.job_id}")
            
            # Process based on data type using our vectorizer classes
            success = False
            try:
                # Update progress to show vectorization is starting
                job_status[job.job_id].progress = 0.3
                
                if job.data_type == "market_data" and market_data_vectorizer:
                    job_status[job.job_id].progress = 0.4
                    success = await market_data_vectorizer.vectorize_market_data(job)
                elif job.data_type == "news" and news_vectorizer:
                    job_status[job.job_id].progress = 0.4
                    success = await news_vectorizer.vectorize_news_data(job)
                elif job.data_type == "earnings" and earnings_vectorizer:
                    job_status[job.job_id].progress = 0.4
                    success = await earnings_vectorizer.vectorize_earnings_data(job)
                else:
                    logger.warning(f"Unknown data type or vectorizer not initialized: {job.data_type}")
                    job_status[job.job_id].status = "failed"
                    job_status[job.job_id].message = f"Unknown data type: {job.data_type}"
                    continue
                
                # Update progress to show vectorization is complete
                job_status[job.job_id].progress = 0.8
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update metrics
                vectorization_metrics["total_jobs_processed"] += 1
                if success:
                    vectorization_metrics["successful_vectorizations"] += 1
                    # Mark job as completed
                    job_status[job.job_id].status = "completed"
                    job_status[job.job_id].progress = 1.0
                    job_status[job.job_id].completed_at = datetime.utcnow()
                    logger.info(f"Completed vectorization job: {job.job_id} in {processing_time:.2f}s")
                else:
                    vectorization_metrics["failed_vectorizations"] += 1
                    # Mark job as failed
                    job_status[job.job_id].status = "failed"
                    job_status[job.job_id].message = "Vectorization failed"
                    logger.error(f"Vectorization failed for job: {job.job_id} after {processing_time:.2f}s")
                
                # Update average processing time
                if vectorization_metrics["total_jobs_processed"] > 0:
                    current_avg = vectorization_metrics["avg_processing_time"]
                    new_avg = (current_avg * (vectorization_metrics["total_jobs_processed"] - 1) + processing_time) / vectorization_metrics["total_jobs_processed"]
                    vectorization_metrics["avg_processing_time"] = new_avg
                
                vectorization_metrics["last_updated"] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error processing job {job.job_id}: {e}")
                job_status[job.job_id].status = "failed"
                job_status[job.job_id].message = str(e)
            
            # Mark job as done in queue
            vectorization_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in vectorization worker: {e}")
            if 'job' in locals():
                job_status[job.job_id].status = "failed"
                job_status[job.job_id].message = str(e)

async def vectorize_market_data(job: VectorizationJob):
    """Vectorize market data for a specific symbol."""
    try:
        symbol = job.data['symbol']
        logger.info(f"Vectorizing market data for {symbol}")
        
        # Get detailed market data
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        SELECT date, open_price, high_price, low_price, close_price, volume
        FROM historical_prices 
        WHERE symbol = $1 
        AND date >= NOW() - INTERVAL '30 days'
        ORDER BY date DESC
        """
        
        rows = await conn.fetch(query, symbol)
        await conn.close()
        
        if not rows:
            logger.warning(f"No market data found for {symbol}")
            return
        
        # Create meaningful text description
        latest = rows[0]
        text_content = f"""
        {symbol} Stock Performance (Last 30 Days):
        Latest Close: ${latest['close_price']:.2f} on {latest['date'].strftime('%Y-%m-%d')}
        Daily Range: ${latest['low_price']:.2f} - ${latest['high_price']:.2f}
        Volume: {latest['volume']:,}
        
        Price Movement: {get_price_movement_description(rows)}
        Trading Activity: {get_volume_analysis(rows)}
        """
        
        # Send to vector storage
        await send_to_vector_storage(
            content=text_content,
            metadata={
                "type": "market_data",
                "symbol": symbol,
                "data_period": "30_days",
                "latest_date": latest['date'].isoformat(),
                "source": "background_vectorization_service"
            }
        )
        
        # Mark as vectorized in database
        await mark_market_data_vectorized(symbol)
        
        logger.info(f"Successfully vectorized market data for {symbol}")
        
    except Exception as e:
        logger.error(f"Error vectorizing market data for {job.data.get('symbol', 'unknown')}: {e}")
        raise

async def vectorize_news_data(job: VectorizationJob):
    """Vectorize news article data."""
    try:
        news_id = job.data['id']
        title = job.data['title']
        content = job.data['content']
        source = job.data['source']
        
        logger.info(f"Vectorizing news article: {title}")
        
        # Create enhanced text content
        text_content = f"""
        News Article: {title}
        Source: {source}
        Published: {job.data['published_at']}
        
        Content:
        {content[:2000]}{'...' if len(content) > 2000 else ''}
        """
        
        # Send to vector storage
        await send_to_vector_storage(
            content=text_content,
            metadata={
                "type": "news",
                "news_id": news_id,
                "title": title,
                "source": source,
                "published_at": job.data['published_at'],
                "source_service": "background_vectorization_service"
            }
        )
        
        # Mark as vectorized in database
        await mark_news_vectorized(news_id)
        
        logger.info(f"Successfully vectorized news article: {title}")
        
    except Exception as e:
        logger.error(f"Error vectorizing news article {job.data.get('id', 'unknown')}: {e}")
        raise

async def vectorize_earnings_data(job: VectorizationJob):
    """Vectorize earnings report data."""
    try:
        symbol = job.data['symbol']
        quarter = job.data['quarter']
        year = job.data['year']
        
        logger.info(f"Vectorizing earnings data for {symbol} Q{quarter} {year}")
        
        # Create meaningful text description
        text_content = f"""
        Earnings Report: {symbol} Q{quarter} {year}
        Report Date: {job.data['report_date']}
        
        Financial Results:
        - EPS: ${job.data['eps']:.2f}
        - Revenue: ${job.data['revenue']:,.0f}
        
        Analysis: {generate_earnings_analysis(job.data)}
        """
        
        # Send to vector storage
        await send_to_vector_storage(
            content=text_content,
            metadata={
                "type": "earnings",
                "symbol": symbol,
                "quarter": quarter,
                "year": year,
                "report_date": job.data['report_date'],
                "source_service": "background_vectorization_service"
            }
        )
        
        # Mark as vectorized in database
        await mark_earnings_vectorized(job.data['id'])
        
        logger.info(f"Successfully vectorized earnings data for {symbol} Q{quarter} {year}")
        
    except Exception as e:
        logger.error(f"Error vectorizing earnings data for {job.data.get('symbol', 'unknown')}: {e}")
        raise

async def send_to_vector_storage(content: str, metadata: Dict[str, Any]):
    """Send vectorized content to the vector storage service."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": content,
                "metadata": metadata,
                "embedding_type": "text"
            }
            
            async with session.post(
                f"{VECTOR_STORAGE_URL}/api/vectorize/text",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully sent to vector storage: {result.get('id', 'unknown')}")
                else:
                    error_text = await response.text()
                    logger.error(f"Vector storage error: {response.status} - {error_text}")
                    raise Exception(f"Vector storage error: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error sending to vector storage: {e}")
        raise

async def mark_market_data_vectorized(symbol: str):
    """Mark market data as vectorized in the database."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        UPDATE market_data 
        SET vectorized = true, vectorized_at = NOW()
        WHERE symbol = $1 AND date >= NOW() - INTERVAL '30 days'
        """
        await conn.execute(query, symbol)
        await conn.close()
    except Exception as e:
        logger.error(f"Error marking market data as vectorized: {e}")

async def mark_news_vectorized(news_id: int):
    """Mark news article as vectorized in the database."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        UPDATE news_articles 
        SET vectorized = true, vectorized_at = NOW()
        WHERE id = $1
        """
        await conn.execute(query, news_id)
        await conn.close()
    except Exception as e:
        logger.error(f"Error marking news as vectorized: {e}")

async def mark_earnings_vectorized(earnings_id: int):
    """Mark earnings report as vectorized in the database."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        UPDATE earnings_reports 
        SET vectorized = true, vectorized_at = NOW()
        WHERE id = $1
        """
        await conn.execute(query, earnings_id)
        await conn.close()
    except Exception as e:
        logger.error(f"Error marking earnings as vectorized: {e}")

async def monitor_new_data():
    """Background task to monitor for new data and trigger vectorization."""
    logger.info("Data monitoring started")
    
    while True:
        try:
            # Wait for 5 minutes before checking
            await asyncio.sleep(300)
            
            logger.info("Checking for new data to vectorize...")
            
            # Check for new market data
            await check_and_vectorize_market_data()
            
            # Check for new news data
            await check_and_vectorize_news_data()
            
            # Check for new earnings data
            await check_and_vectorize_earnings_data()
            
        except Exception as e:
            logger.error(f"Error in data monitoring: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

def get_price_movement_description(rows):
    """Generate a description of price movement from market data."""
    if len(rows) < 2:
        return "Insufficient data for analysis"
    
    first_close = rows[-1]['close_price']
    last_close = rows[0]['close_price']
    change = last_close - first_close
    change_pct = (change / first_close) * 100
    
    if change > 0:
        direction = "upward"
    elif change < 0:
        direction = "downward"
    else:
        direction = "sideways"
    
    return f"Price moved {direction} from ${first_close:.2f} to ${last_close:.2f} ({change:+.2f}, {change_pct:+.1f}%)"

def get_volume_analysis(rows):
    """Generate volume analysis from market data."""
    if len(rows) < 5:
        return "Insufficient data for volume analysis"
    
    avg_volume = sum(row['volume'] for row in rows) / len(rows)
    latest_volume = rows[0]['volume']
    
    if latest_volume > avg_volume * 1.5:
        return f"Above average volume ({latest_volume:,.0f} vs {avg_volume:,.0f} avg)"
    elif latest_volume < avg_volume * 0.5:
        return f"Below average volume ({latest_volume:,.0f} vs {avg_volume:,.0f} avg)"
    else:
        return f"Normal volume ({latest_volume:,.0f})"

def generate_earnings_analysis(data):
    """Generate analysis text for earnings data."""
    eps = data['eps']
    revenue = data['revenue']
    
    if eps > 0:
        eps_analysis = f"Positive EPS of ${eps:.2f}"
    else:
        eps_analysis = f"Negative EPS of ${eps:.2f}"
    
    revenue_analysis = f"Revenue of ${revenue:,.0f}"
    
    return f"{eps_analysis}, {revenue_analysis}"

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
