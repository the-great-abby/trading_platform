#!/usr/bin/env python3
"""
Unified Trading Dashboard Service
Combines trading, performance, and health dashboards into a single service
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Trading Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory="templates")

# Configuration
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:11101")
ANALYTICS_API_URL = os.getenv("ANALYTICS_API_URL", "http://backtest-api:11101")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")

# Redis connection
redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Database connection
def get_database_connection():
    """Get database connection"""
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

class DashboardConfig:
    """Dashboard configuration"""
    REFRESH_INTERVAL = 30  # seconds
    MAX_RECENT_RUNS = 10
    DEFAULT_PERIOD = "1m"

class UnifiedTradingDashboard:
    """Unified dashboard manager"""
    
    def __init__(self):
        self.backtest_api_url = BACKTEST_API_URL
        self.analytics_api_url = ANALYTICS_API_URL
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from backtest API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/runs")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get system health status with Redis metrics"""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis": "connected" if redis_client else "disconnected"
        }
        
        if not redis_client:
            status["status"] = "degraded"
        
        # Add Redis metrics if available
        if redis_client:
            try:
                cache_stats = redis_client.info("memory")
                status["cache_memory"] = cache_stats.get("used_memory_human", "N/A")
                status["cache_keys"] = redis_client.dbsize()
                
                # Get recent logs (if stored in Redis)
                recent_logs = redis_client.lrange("system_logs", 0, 9)
                status["recent_logs"] = [log.decode() for log in recent_logs]
            except Exception as e:
                logger.error(f"Error getting Redis metrics: {e}")
                status["redis_error"] = str(e)
        
        return status
    
    async def get_recent_runs(self) -> Dict[str, Any]:
        """Get recent backtest runs"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/runs?limit={DashboardConfig.MAX_RECENT_RUNS}")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting recent runs: {e}")
            return {"error": str(e)}
    
    async def get_performance_metrics_detailed(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/stats")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting detailed performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_risk_analysis(self) -> Dict[str, Any]:
        """Get risk analysis data"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/runs")
                if response.status_code == 200:
                    runs = response.json()
                    # Calculate risk metrics from runs
                    risk_analysis = {
                        "total_runs": len(runs.get("runs", [])),
                        "successful_runs": len([r for r in runs.get("runs", []) if r.get("status") == "completed"]),
                        "failed_runs": len([r for r in runs.get("runs", []) if r.get("status") == "failed"]),
                        "avg_drawdown": 0.0,
                        "max_drawdown": 0.0,
                        "risk_score": "medium"
                    }
                    return risk_analysis
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting risk analysis: {e}")
            return {"error": str(e)}
    
    async def get_trade_analysis(self) -> Dict[str, Any]:
        """Get trade analysis data"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/runs")
                if response.status_code == 200:
                    runs = response.json()
                    # Calculate trade metrics from runs
                    trade_analysis = {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "avg_trade_duration": 0.0,
                        "best_trade": None,
                        "worst_trade": None
                    }
                    return trade_analysis
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting trade analysis: {e}")
            return {"error": str(e)}
    
    async def get_strategy_comparison(self) -> Dict[str, Any]:
        """Get strategy comparison data"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/compare")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting strategy comparison: {e}")
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "backtest_api": "unknown",
                "redis": "unknown",
                "database": "unknown"
            },
            "performance": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0
            },
            "cache": {
                "hit_rate": 0.0,
                "memory_usage": "N/A",
                "keys_count": 0
            }
        }
        
        # Check backtest API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.backtest_api_url}/health")
                status["services"]["backtest_api"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            status["services"]["backtest_api"] = "error"
            logger.error(f"Error checking backtest API: {e}")
        
        # Check Redis
        if redis_client:
            try:
                redis_client.ping()
                status["services"]["redis"] = "healthy"
                cache_stats = redis_client.info("memory")
                status["cache"]["memory_usage"] = cache_stats.get("used_memory_human", "N/A")
                status["cache"]["keys_count"] = redis_client.dbsize()
            except Exception as e:
                status["services"]["redis"] = "error"
                logger.error(f"Error checking Redis: {e}")
        else:
            status["services"]["redis"] = "disconnected"
        
        return status

# Initialize dashboard manager
dashboard_manager = UnifiedTradingDashboard()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unified-trading-dashboard"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "unified-trading-dashboard"}

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/trading", response_class=HTMLResponse)
async def trading_dashboard(request: Request):
    """Trading dashboard page"""
    return templates.TemplateResponse("trading.html", {"request": request})

@app.get("/performance", response_class=HTMLResponse)
async def performance_dashboard(request: Request):
    """Performance dashboard page"""
    return templates.TemplateResponse("performance.html", {"request": request})

@app.get("/health", response_class=HTMLResponse)
async def health_dashboard(request: Request):
    """Health dashboard page"""
    return templates.TemplateResponse("health.html", {"request": request})

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    return await dashboard_manager.get_performance_metrics()

@app.get("/api/health/status")
async def get_health_status():
    """Get health status with Redis metrics"""
    return await dashboard_manager.get_health_status()

@app.get("/api/health/metrics")
async def get_system_metrics():
    """Get system metrics from Redis"""
    metrics = {}
    if redis_client:
        try:
            cache_stats = redis_client.info("memory")
            metrics["cache_memory"] = cache_stats.get("used_memory_human", "N/A")
            metrics["cache_keys"] = redis_client.dbsize()
            metrics["cache_hit_rate"] = 0.0  # Would need to track this
            metrics["timestamp"] = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            metrics["error"] = str(e)
    else:
        metrics["error"] = "Redis not connected"
    
    return metrics

@app.get("/api/recent-runs")
async def get_recent_runs():
    """Get recent backtest runs"""
    return await dashboard_manager.get_recent_runs()

@app.get("/api/performance-metrics")
async def get_performance_metrics_detailed():
    """Get detailed performance metrics"""
    return await dashboard_manager.get_performance_metrics_detailed()

@app.get("/api/risk-analysis")
async def get_risk_analysis():
    """Get risk analysis data"""
    return await dashboard_manager.get_risk_analysis()

@app.get("/api/trade-analysis")
async def get_trade_analysis():
    """Get trade analysis data"""
    return await dashboard_manager.get_trade_analysis()

@app.get("/api/strategy-comparison")
async def get_strategy_comparison():
    """Get strategy comparison data"""
    return await dashboard_manager.get_strategy_comparison()

@app.get("/api/system-status")
async def get_system_status():
    """Get comprehensive system status"""
    return await dashboard_manager.get_system_status()

# Database-driven API endpoints
@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Get real portfolio summary from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get portfolio summary
            result = conn.execute(text("""
                SELECT 
                    COALESCE(SUM(quantity * current_price), 0) as total_value,
                    COALESCE(SUM(cash), 0) as total_cash,
                    COALESCE(SUM(unrealized_pnl), 0) as total_pnl,
                    COUNT(*) as num_positions
                FROM portfolio_positions
                WHERE active = true
            """))
            
            row = result.fetchone()
            if row:
                return {
                    "total_value": float(row.total_value or 0),
                    "total_cash": float(row.total_cash or 0),
                    "total_pnl": float(row.total_pnl or 0),
                    "num_positions": int(row.num_positions or 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "total_value": 0.0,
                    "total_cash": 0.0,
                    "total_pnl": 0.0,
                    "num_positions": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/trades/recent")
async def get_recent_trades():
    """Get recent trades from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent trades
            result = conn.execute(text("""
                SELECT 
                    bt.timestamp,
                    bt.symbol,
                    bt.action,
                    bt.quantity,
                    bt.price,
                    bt.value,
                    bt.pnl,
                    bt.confidence,
                    br.strategy_name,
                    br.backtest_name
                FROM backtest_trades bt
                JOIN backtest_runs br ON bt.run_id = br.run_id
                WHERE bt.symbol IS NOT NULL AND bt.symbol != '' AND LENGTH(TRIM(bt.symbol)) > 0
                ORDER BY bt.timestamp DESC
                LIMIT 50
            """))
            
            trades = []
            for row in result:
                trades.append({
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "symbol": row.symbol,
                    "action": row.action,
                    "quantity": int(row.quantity or 0),
                    "price": float(row.price or 0),
                    "value": float(row.value or 0),
                    "pnl": float(row.pnl or 0),
                    "confidence": float(row.confidence or 0),
                    "strategy": row.strategy_name,
                    "backtest": row.backtest_name
                })
            
            return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/strategy/events")
async def get_strategy_events():
    """Get recent strategy events from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get strategy events (if table exists)
            try:
                result = conn.execute(text("""
                    SELECT 
                        timestamp,
                        strategy_name,
                        symbol,
                        event_type,
                        action,
                        confidence,
                        metadata
                    FROM strategy_events
                    ORDER BY timestamp DESC
                    LIMIT 100
                """))
                
                events = []
                for row in result:
                    events.append({
                        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                        "strategy": row.strategy_name,
                        "symbol": row.symbol,
                        "event_type": row.event_type,
                        "action": row.action,
                        "confidence": float(row.confidence or 0),
                        "metadata": row.metadata if row.metadata else {}
                    })
                
                return {"events": events, "count": len(events)}
            except Exception as table_error:
                logger.warning(f"Strategy events table not found: {table_error}")
                return {"events": [], "count": 0, "note": "Strategy events table not available"}
    except Exception as e:
        logger.error(f"Error getting strategy events: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/positions/active")
async def get_active_positions():
    """Get active portfolio positions from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get active positions
            result = conn.execute(text("""
                SELECT 
                    symbol,
                    quantity,
                    avg_price,
                    current_price,
                    market_value,
                    unrealized_pnl,
                    unrealized_pnl_percent,
                    entry_date,
                    strategy,
                    holding_days
                FROM portfolio_positions
                WHERE active = true
                ORDER BY unrealized_pnl DESC
            """))
            
            positions = []
            for row in result:
                positions.append({
                    "symbol": row.symbol,
                    "quantity": int(row.quantity or 0),
                    "avg_price": float(row.avg_price or 0),
                    "current_price": float(row.current_price or 0),
                    "market_value": float(row.market_value or 0),
                    "unrealized_pnl": float(row.unrealized_pnl or 0),
                    "unrealized_pnl_percent": float(row.unrealized_pnl_percent or 0),
                    "entry_date": row.entry_date.isoformat() if row.entry_date else None,
                    "strategy": row.strategy,
                    "holding_days": int(row.holding_days or 0)
                })
            
            return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Error getting active positions: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80) 