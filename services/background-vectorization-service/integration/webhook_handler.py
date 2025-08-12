#!/usr/bin/env python3
"""
Webhook Handler for Background Vectorization Service

Handles incoming webhooks from data ingestion services and triggers
automatic vectorization of new data.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration", tags=["integration"])

# Webhook event models
class MarketDataWebhook(BaseModel):
    """Market data webhook payload."""
    event_type: str = "market_data_update"
    symbol: str
    timestamp: datetime
    data_type: str = "market_data"
    data: Dict[str, Any]
    source: str = "market-data-service"
    priority: int = 1

class NewsDataWebhook(BaseModel):
    """News data webhook payload."""
    event_type: str = "news_update"
    timestamp: datetime
    data_type: str = "news"
    data: Dict[str, Any]
    source: str = "news-fetch-job"
    priority: int = 2

class EarningsDataWebhook(BaseModel):
    """Earnings data webhook payload."""
    event_type: str = "earnings_update"
    symbol: str
    timestamp: datetime
    data_type: str = "earnings"
    data: Dict[str, Any]
    source: str = "earnings-data-service"
    priority: int = 3

class DataIngestionWebhook(BaseModel):
    """Generic data ingestion webhook."""
    event_type: str
    timestamp: datetime
    data_type: str
    symbol: Optional[str] = None
    data: Dict[str, Any]
    source: str
    priority: int = 1

# Webhook handlers
@router.post("/webhook/market-data")
async def handle_market_data_webhook(
    webhook: MarketDataWebhook,
    background_tasks: BackgroundTasks
):
    """Handle market data webhook from market-data-service."""
    try:
        logger.info(f"Received market data webhook for {webhook.symbol}")
        
        # Create vectorization job
        job_data = {
            "job_id": f"webhook_market_{webhook.symbol}_{int(webhook.timestamp.timestamp())}",
            "data_type": "market_data",
            "symbol": webhook.symbol,
            "data": webhook.data,
            "priority": webhook.priority,
            "source": "webhook",
            "webhook_timestamp": webhook.timestamp.isoformat()
        }
        
        # Add to background tasks
        background_tasks.add_task(process_webhook_job, job_data)
        
        return {
            "status": "accepted",
            "message": f"Market data webhook processed for {webhook.symbol}",
            "job_id": job_data["job_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing market data webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/news")
async def handle_news_webhook(
    webhook: NewsDataWebhook,
    background_tasks: BackgroundTasks
):
    """Handle news data webhook from news-fetch-job."""
    try:
        logger.info(f"Received news webhook from {webhook.source}")
        
        # Create vectorization job
        job_data = {
            "job_id": f"webhook_news_{int(webhook.timestamp.timestamp())}",
            "data_type": "news",
            "data": webhook.data,
            "priority": webhook.priority,
            "source": "webhook",
            "webhook_timestamp": webhook.timestamp.isoformat()
        }
        
        # Add to background tasks
        background_tasks.add_task(process_webhook_job, job_data)
        
        return {
            "status": "accepted",
            "message": "News webhook processed",
            "job_id": job_data["job_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing news webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/earnings")
async def handle_earnings_webhook(
    webhook: EarningsDataWebhook,
    background_tasks: BackgroundTasks
):
    """Handle earnings data webhook from earnings-data-service."""
    try:
        logger.info(f"Received earnings webhook for {webhook.symbol}")
        
        # Create vectorization job
        job_data = {
            "job_id": f"webhook_earnings_{webhook.symbol}_{int(webhook.timestamp.timestamp())}",
            "data_type": "earnings",
            "symbol": webhook.symbol,
            "data": webhook.data,
            "priority": webhook.priority,
            "source": "webhook",
            "webhook_timestamp": webhook.timestamp.isoformat()
        }
        
        # Add to background tasks
        background_tasks.add_task(process_webhook_job, job_data)
        
        return {
            "status": "accepted",
            "message": f"Earnings webhook processed for {webhook.symbol}",
            "job_id": job_data["job_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing earnings webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/generic")
async def handle_generic_webhook(
    webhook: DataIngestionWebhook,
    background_tasks: BackgroundTasks
):
    """Handle generic data ingestion webhook."""
    try:
        logger.info(f"Received generic webhook: {webhook.event_type} from {webhook.source}")
        
        # Create vectorization job
        job_data = {
            "job_id": f"webhook_{webhook.data_type}_{int(webhook.timestamp.timestamp())}",
            "data_type": webhook.data_type,
            "symbol": webhook.symbol,
            "data": webhook.data,
            "priority": webhook.priority,
            "source": "webhook",
            "webhook_timestamp": webhook.timestamp.isoformat()
        }
        
        # Add to background tasks
        background_tasks.add_task(process_webhook_job, job_data)
        
        return {
            "status": "accepted",
            "message": f"Generic webhook processed: {webhook.event_type}",
            "job_id": job_data["job_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing generic webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_webhook_job(job_data: Dict[str, Any]):
    """Process webhook job in background."""
    try:
        # Import here to avoid circular imports
        from main import queue_vectorization_job, VectorizationJob
        
        # Create vectorization job
        job = VectorizationJob(**job_data)
        
        # Queue the job
        await queue_vectorization_job(job)
        
        logger.info(f"Webhook job queued successfully: {job_data['job_id']}")
        
    except Exception as e:
        logger.error(f"Error processing webhook job: {e}")

# Webhook status and management
@router.get("/webhooks/status")
async def get_webhook_status():
    """Get webhook integration status."""
    return {
        "status": "active",
        "webhooks": {
            "market_data": {
                "endpoint": "/api/integration/webhook/market-data",
                "status": "active",
                "description": "Market data updates from market-data-service"
            },
            "news": {
                "endpoint": "/api/integration/webhook/news",
                "status": "active",
                "description": "News updates from news-fetch-job"
            },
            "earnings": {
                "endpoint": "/api/integration/webhook/earnings",
                "status": "active",
                "description": "Earnings updates from earnings-data-service"
            },
            "generic": {
                "endpoint": "/api/integration/webhook/generic",
                "status": "active",
                "description": "Generic data ingestion webhooks"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/webhooks/test")
async def test_webhook_integration():
    """Test webhook integration with sample data."""
    try:
        # Test market data webhook
        test_market_data = {
            "event_type": "market_data_update",
            "symbol": "AAPL",
            "timestamp": datetime.utcnow(),
            "data_type": "market_data",
            "data": {"test": True, "symbol": "AAPL"},
            "source": "test",
            "priority": 1
        }
        
        # Test news webhook
        test_news_data = {
            "event_type": "news_update",
            "timestamp": datetime.utcnow(),
            "data_type": "news",
            "data": {"test": True, "title": "Test News", "content": "Test content"},
            "source": "test",
            "priority": 2
        }
        
        # Test earnings webhook
        test_earnings_data = {
            "event_type": "earnings_update",
            "symbol": "AAPL",
            "timestamp": datetime.utcnow(),
            "data_type": "earnings",
            "data": {"test": True, "symbol": "AAPL", "eps": 1.50},
            "source": "test",
            "priority": 3
        }
        
        # Process test webhooks
        await process_webhook_job({
            "job_id": f"test_market_{int(datetime.utcnow().timestamp())}",
            "data_type": "market_data",
            "symbol": "AAPL",
            "data": test_market_data["data"],
            "priority": 1,
            "source": "test"
        })
        
        await process_webhook_job({
            "job_id": f"test_news_{int(datetime.utcnow().timestamp())}",
            "data_type": "news",
            "data": test_news_data["data"],
            "priority": 2,
            "source": "test"
        })
        
        await process_webhook_job({
            "job_id": f"test_earnings_{int(datetime.utcnow().timestamp())}",
            "data_type": "earnings",
            "symbol": "AAPL",
            "data": test_earnings_data["data"],
            "priority": 3,
            "source": "test"
        })
        
        return {
            "status": "success",
            "message": "Webhook integration test completed",
            "test_jobs_created": 3,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing webhook integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
