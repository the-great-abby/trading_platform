"""
Trading Service - Internal microservice for trading operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Service", version="1.0.0")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading-service"}

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
    try:
        # Mock trade execution for now
        trade_id = f"trade_{hash(trade_request.symbol + trade_request.action)}"
        
        logger.info(f"Executing trade: {trade_request.symbol} {trade_request.action} {trade_request.quantity}")
        
        return TradeResponse(
            trade_id=trade_id,
            status="executed",
            message=f"Trade executed successfully for {trade_request.symbol}"
        )
    except Exception as e:
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
