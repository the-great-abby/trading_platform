"""
Trading Service - Internal microservice for trading operations
"""

import uvicorn
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging
from prometheus_client import generate_latest

# Import our metrics
from trading_metrics import (
    trading_metrics, 
    record_trade_execution, 
    record_strategy_signal,
    update_portfolio_metrics,
    update_risk_metrics,
    record_request,
    record_error
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Service", version="1.0.0")

# Mock data for demonstration
mock_portfolio = {
    "value": 100000.0,
    "positions": 5,
    "pnl": 2500.0
}

mock_risk = {
    "exposure": 15000.0,
    "position_limit": 20000.0
}

class TradeRequest(BaseModel):
    symbol: str
    action: str  # "buy" or "sell"
    quantity: float
    price: Optional[float] = None
    strategy: Optional[str] = None

class TradeResponse(BaseModel):
    trade_id: str
    status: str
    message: str

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to record request metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        record_error("http_error", "trading-service")
        
        record_request(
            method=request.method,
            endpoint=request.url.path,
            status=500,
            duration=duration
        )
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading-service"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/status")
async def get_status():
    """Get trading service status"""
    return {
        "service": "trading-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/trades/execute", response_model=TradeResponse)
async def execute_trade(trade_request: TradeRequest):
    """Execute a trade"""
    start_time = time.time()
    
    try:
        # Mock trade execution for now
        trade_id = f"trade_{hash(trade_request.symbol + trade_request.action)}"
        
        logger.info(f"Executing trade: {trade_request.symbol} {trade_request.action} {trade_request.quantity}")
        
        # Record strategy signal if provided
        if trade_request.strategy:
            record_strategy_signal(
                strategy=trade_request.strategy,
                signal_type="buy" if trade_request.action == "buy" else "sell",
                executed=True
            )
        
        # Record trade execution metrics
        duration = time.time() - start_time
        record_trade_execution(
            symbol=trade_request.symbol,
            action=trade_request.action,
            status="success",
            duration=duration
        )
        
        return TradeResponse(
            trade_id=trade_id,
            status="executed",
            message=f"Trade executed successfully for {trade_request.symbol}"
        )
    except Exception as e:
        duration = time.time() - start_time
        record_trade_execution(
            symbol=trade_request.symbol,
            action=trade_request.action,
            status="failed",
            duration=duration
        )
        record_error("trade_execution_error", "trading-service")
        
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@app.get("/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get trade details"""
    # Mock trade details
    return {
        "trade_id": trade_id,
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 100,
        "price": 150.0,
        "status": "executed",
        "timestamp": "2024-01-01T10:00:00Z"
    }

@app.get("/trades")
async def get_trades(limit: int = 100):
    """Get recent trades"""
    # Mock trade history
    return {
        "trades": [
            {
                "trade_id": "trade_1",
                "symbol": "AAPL",
                "action": "buy",
                "quantity": 100,
                "price": 150.0,
                "status": "executed",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        ],
        "total": 1
    }

@app.get("/portfolio")
async def get_portfolio():
    """Get portfolio metrics"""
    # Update portfolio metrics
    update_portfolio_metrics(
        portfolio_value=mock_portfolio["value"],
        positions_count=mock_portfolio["positions"],
        pnl=mock_portfolio["pnl"]
    )
    
    return mock_portfolio

@app.get("/risk")
async def get_risk():
    """Get risk metrics"""
    # Update risk metrics
    update_risk_metrics(
        exposure=mock_risk["exposure"],
        position_limit=mock_risk["position_limit"]
    )
    
    return mock_risk

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
