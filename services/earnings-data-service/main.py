#!/usr/bin/env python3
"""
Earnings Data Service

Fetches quarterly earnings reports from multiple providers:
- Polygon.io (primary)
- Alpha Vantage (fallback)
- Yahoo Finance (fallback)

Stores earnings data in PostgreSQL for vectorization and analysis.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import asyncpg
from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from pydantic import BaseModel
import json

# Add src to path for shared modules
sys.path.append('/app/src')

from src.services.earnings.polygon_earnings_service import PolygonEarningsService
from src.services.earnings.alpha_vantage_earnings_service import AlphaVantageEarningsService
from src.services.earnings.yahoo_finance_earnings_service import YahooFinanceEarningsService
from src.services.earnings.earnings_data_service import EarningsDataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    global earnings_data_service, polygon_service, alpha_vantage_service, yahoo_service
    
    try:
        # Initialize database service
        earnings_data_service = EarningsDataService(DATABASE_URL)
        await earnings_data_service.initialize()
        logger.info("✅ Earnings data service initialized")
        
        # Initialize API services
        if POLYGON_API_KEY:
            polygon_service = PolygonEarningsService(POLYGON_API_KEY)
            logger.info("✅ Polygon earnings service initialized")
        
        if ALPHA_VANTAGE_API_KEY:
            alpha_vantage_service = AlphaVantageEarningsService(ALPHA_VANTAGE_API_KEY)
            logger.info("✅ Alpha Vantage earnings service initialized")
        
        # Yahoo Finance doesn't require API key
        yahoo_service = YahooFinanceEarningsService()
        logger.info("✅ Yahoo Finance earnings service initialized")
        
        logger.info(f"🎯 Earnings data service ready with {sum([1 for s in [polygon_service, alpha_vantage_service, yahoo_service] if s])} providers")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize earnings data service: {e}")
        raise
    
    yield
    
    # Shutdown
    if earnings_data_service:
        await earnings_data_service.close()

app = FastAPI(title="Earnings Data Service", version="1.0.0", lifespan=lifespan)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Initialize services
earnings_data_service = None
polygon_service = None
alpha_vantage_service = None
yahoo_service = None

# Pydantic models
class EarningsFetchRequest(BaseModel):
    symbols: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include_estimates: bool = True
    include_guidance: bool = True

class EarningsResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection by executing a simple query
        if earnings_data_service and earnings_data_service.pool:
            async with earnings_data_service.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=500, detail="Service not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/earnings/status")
async def get_service_status():
    """Get status of all earnings data providers"""
    providers = []
    
    if polygon_service:
        providers.append({
            "name": "Polygon.io",
            "status": "active",
            "api_key": "configured" if POLYGON_API_KEY else "missing"
        })
    
    if alpha_vantage_service:
        providers.append({
            "name": "Alpha Vantage",
            "status": "active",
            "api_key": "configured" if ALPHA_VANTAGE_API_KEY else "missing"
        })
    
    if yahoo_service:
        providers.append({
            "name": "Yahoo Finance",
            "status": "active",
            "api_key": "not_required"
        })
    
    return {
        "status": "operational",
        "providers": providers,
        "database": "connected" if earnings_data_service else "disconnected"
    }

@app.post("/api/earnings/fetch", response_model=EarningsResponse)
async def fetch_earnings_data(request: EarningsFetchRequest, background_tasks: BackgroundTasks):
    """Fetch earnings data for specified symbols"""
    try:
        # Set default date range if not provided
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = request.start_date or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        logger.info(f"🎯 Fetching earnings data for {len(request.symbols)} symbols from {start_date} to {end_date}")
        
        # Add to background tasks
        background_tasks.add_task(
            fetch_earnings_background,
            request.symbols,
            start_date,
            end_date,
            request.include_estimates,
            request.include_guidance
        )
        
        return EarningsResponse(
            status="success",
            message=f"Started fetching earnings data for {len(request.symbols)} symbols",
            data={
                "symbols": request.symbols,
                "start_date": start_date,
                "end_date": end_date,
                "job_type": "background"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting earnings fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/earnings/symbols")
async def get_available_symbols():
    """Get list of symbols with earnings data"""
    try:
        symbols = await earnings_data_service.get_symbols_with_earnings()
        return {
            "status": "success",
            "count": len(symbols),
            "symbols": symbols
        }
    except Exception as e:
        logger.error(f"❌ Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/earnings/symbol/{symbol}")
async def get_earnings_for_symbol(symbol: str, limit: int = 10):
    """Get earnings data for a specific symbol"""
    try:
        earnings = await earnings_data_service.get_earnings_by_symbol(symbol.upper(), limit)
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "count": len(earnings),
            "earnings": earnings
        }
    except Exception as e:
        logger.error(f"❌ Error getting earnings for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/earnings/upcoming")
async def get_upcoming_earnings(days_ahead: int = 30):
    """Get upcoming earnings in the next N days"""
    try:
        upcoming = await earnings_data_service.get_upcoming_earnings(days_ahead)
        return {
            "status": "success",
            "days_ahead": days_ahead,
            "count": len(upcoming),
            "upcoming_earnings": upcoming
        }
    except Exception as e:
        logger.error(f"❌ Error getting upcoming earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_earnings_background(symbols: List[str], start_date: str, end_date: str, 
                                  include_estimates: bool, include_guidance: bool):
    """Background task to fetch earnings data"""
    logger.info(f"🔄 Starting background earnings fetch for {len(symbols)} symbols")
    
    total_fetched = 0
    total_stored = 0
    
    for i, symbol in enumerate(symbols):
        try:
            logger.info(f"📊 Processing {i+1}/{len(symbols)}: {symbol}")
            
            # Try providers in order of preference
            earnings_data = None
            
            # 1. Try Polygon first (most comprehensive)
            if polygon_service:
                try:
                    earnings_data = await polygon_service.fetch_earnings(
                        symbol, start_date, end_date, include_estimates, include_guidance
                    )
                    if earnings_data:
                        logger.info(f"✅ Polygon fetched {len(earnings_data)} earnings for {symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ Polygon failed for {symbol}: {e}")
            
            # 2. Try Alpha Vantage
            if not earnings_data and alpha_vantage_service:
                try:
                    earnings_data = await alpha_vantage_service.fetch_earnings(
                        symbol, start_date, end_date, include_estimates, include_guidance
                    )
                    if earnings_data:
                        logger.info(f"✅ Alpha Vantage fetched {len(earnings_data)} earnings for {symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ Alpha Vantage failed for {symbol}: {e}")
            
            # 3. Try Yahoo Finance
            if not earnings_data and yahoo_service:
                try:
                    earnings_data = await yahoo_service.fetch_earnings(
                        symbol, start_date, end_date, include_estimates, include_guidance
                    )
                    if earnings_data:
                        logger.info(f"✅ Yahoo Finance fetched {len(earnings_data)} earnings for {symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ Yahoo Finance failed for {symbol}: {e}")
            
            if earnings_data:
                # Store in database
                stored_count = await earnings_data_service.store_earnings_batch(symbol, earnings_data)
                total_fetched += len(earnings_data)
                total_stored += stored_count
                logger.info(f"💾 Stored {stored_count}/{len(earnings_data)} earnings for {symbol}")
            else:
                logger.warning(f"⚠️ No earnings data fetched for {symbol} from any provider")
            
            # Rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
            continue
    
    logger.info(f"🎉 Earnings fetch complete! Fetched: {total_fetched}, Stored: {total_stored}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
