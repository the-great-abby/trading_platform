#!/usr/bin/env python3
"""
API Gateway - Central entry point for all trading platform services
"""

import os
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Platform Gateway", version="1.0.0")

# Configuration
SERVICES = {
    "market_data": os.getenv("MARKET_DATA_URL", "http://localhost:8002"),
    "backtest_api": os.getenv("BACKTEST_API_URL", "http://localhost:8003"),
    "trading_dashboard": os.getenv("TRADING_DASHBOARD_URL", "http://localhost:8004"),
    "health_dashboard": os.getenv("HEALTH_DASHBOARD_URL", "http://localhost:8005"),
    "ai_analysis": os.getenv("AI_ANALYSIS_URL", "http://localhost:11085"),
    "llm_service": os.getenv("LLM_SERVICE_URL", "http://localhost:12001"),
    "central_hub": os.getenv("CENTRAL_HUB_URL", "http://localhost:11080")
}

# Mount static files for reports
if os.path.exists("reports/html"):
    app.mount("/reports", StaticFiles(directory="reports/html"), name="reports")

# Templates
templates = Jinja2Templates(directory="templates")

class ServiceHealth(BaseModel):
    service: str
    status: str
    response_time: float
    last_check: datetime

# Health check cache
health_cache: Dict[str, ServiceHealth] = {}

async def check_service_health(service_name: str, url: str) -> ServiceHealth:
    """Check health of a service"""
    import time
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health", timeout=5) as response:
                response_time = time.time() - start_time
                status = "healthy" if response.status == 200 else "unhealthy"
                return ServiceHealth(
                    service=service_name,
                    status=status,
                    response_time=response_time,
                    last_check=datetime.utcnow()
                )
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Health check failed for {service_name}: {e}")
        return ServiceHealth(
            service=service_name,
            status="unhealthy",
            response_time=response_time,
            last_check=datetime.utcnow()
        )

@app.get("/")
async def root():
    """Gateway root - redirect to central hub"""
    return RedirectResponse(url="/central-hub")

@app.get("/health")
async def health_check():
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "trading-gateway",
        "timestamp": datetime.utcnow(),
        "services": SERVICES
    }

@app.get("/api/services/health")
async def get_all_services_health():
    """Get health status of all services"""
    import asyncio
    
    # Check all services concurrently
    health_checks = []
    for service_name, url in SERVICES.items():
        health_checks.append(check_service_health(service_name, url))
    
    results = await asyncio.gather(*health_checks, return_exceptions=True)
    
    # Update cache
    for result in results:
        if isinstance(result, ServiceHealth):
            health_cache[result.service] = result
    
    return {
        "timestamp": datetime.utcnow(),
        "services": [result.dict() if isinstance(result, ServiceHealth) else 
                    {"service": "unknown", "status": "error", "response_time": 0, "last_check": datetime.utcnow()}
                    for result in results]
    }

# AI Analysis Integration
@app.get("/api/ai-analysis/health")
async def ai_analysis_health():
    """Check AI analysis service health"""
    return await check_service_health("ai_analysis", SERVICES["ai_analysis"])

@app.post("/api/ai-analysis/analyze/{symbol}")
async def analyze_stock(symbol: str, request: Request):
    """Analyze a single stock using AI"""
    try:
        body = await request.json()
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['ai_analysis']}/api/analyze/symbol/{symbol}"
            async with session.post(url, json=body) as response:
                result = await response.json()
                return result
    except Exception as e:
        logger.error(f"Error analyzing stock {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed for {symbol}")

@app.post("/api/ai-analysis/batch")
async def analyze_batch(request: Request):
    """Run batch analysis on multiple stocks"""
    try:
        body = await request.json()
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['ai_analysis']}/api/analyze/batch"
            async with session.post(url, json=body) as response:
                result = await response.json()
                return result
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Batch analysis failed")

@app.get("/api/ai-analysis/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get results of a batch analysis"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['ai_analysis']}/api/analysis/{analysis_id}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        else:
                    raise HTTPException(status_code=404, detail="Analysis not found")
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis results")

@app.get("/api/ai-analysis/recent")
async def get_recent_analyses(limit: int = 10):
    """Get recent analysis results"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['ai_analysis']}/api/analysis/recent?limit={limit}"
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting recent analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent analyses")

@app.get("/api/ai-analysis/daily")
async def get_daily_recommendations():
    """Get daily stock recommendations"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['ai_analysis']}/api/recommendations/daily"
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting daily recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily recommendations")

# Reports Integration
@app.get("/reports")
async def reports_dashboard():
    """Reports dashboard page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Platform - Reports Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-left: 4px solid #3498db;
            transition: transform 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .card p {
            color: #7f8c8d;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .btn.secondary {
            background: linear-gradient(135deg, #95a5a6, #7f8c8d);
        }
        
        .btn.success {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
        }
        
        .btn.warning {
            background: linear-gradient(135deg, #f39c12, #e67e22);
        }
        
        .status {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status.healthy {
            background: #d5f4e6;
            color: #27ae60;
        }
        
        .status.unhealthy {
            background: #fadbd8;
            color: #e74c3c;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Reports Dashboard</h1>
            <p>AI-Powered Trading Analysis & Reports</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>🤖 AI Analysis Reports</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Daily Recommendations</h3>
                        <p>Get AI-powered buy/sell recommendations for your watchlist stocks with confidence scoring and detailed analysis.</p>
                        <a href="/api/ai-analysis/daily" class="btn success">View Daily Recommendations</a>
                    </div>
                    
                    <div class="card">
                        <h3>Recent Analyses</h3>
                        <p>Browse recent AI analysis results and recommendations with detailed technical and sentiment analysis.</p>
                        <a href="/api/ai-analysis/recent" class="btn">View Recent Analyses</a>
                    </div>
                    
                    <div class="card">
                        <h3>Single Stock Analysis</h3>
                        <p>Analyze a specific stock with AI-powered insights including technical indicators and sentiment analysis.</p>
                        <a href="/api/ai-analysis/analyze/AAPL" class="btn secondary">Analyze AAPL</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Backtest Reports</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Backtest Results</h3>
                        <p>View comprehensive backtest reports with performance metrics, trade analysis, and equity curves.</p>
                        <a href="/reports/html/" class="btn">Browse Reports</a>
                    </div>
                    
                    <div class="card">
                        <h3>Performance Analysis</h3>
                        <p>Detailed performance analysis with risk metrics, drawdown analysis, and strategy comparison.</p>
                        <a href="/api/backtest/results" class="btn secondary">View Results</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔧 System Status</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Service Health</h3>
                        <p>Monitor the health and status of all trading platform services and components.</p>
                        <a href="/api/services/health" class="btn">Check Health</a>
                    </div>
                    
                    <div class="card">
                        <h3>Central Hub</h3>
                        <p>Access the centralized dashboard for all trading platform services and tools.</p>
                        <a href="/central-hub" class="btn warning">Go to Central Hub</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Trading Platform Gateway | AI-Powered Analysis & Reporting</p>
        </div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/central-hub")
async def central_hub():
    """Redirect to central hub dashboard"""
    return RedirectResponse(url=SERVICES["central_hub"])

# Legacy endpoints for backward compatibility
@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['market_data']}/api/market-data/{symbol}"
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market data for {symbol}")

@app.get("/api/backtest/results")
async def get_backtest_results():
    """Get backtest results"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SERVICES['backtest_api']}/api/results"
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtest results")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
