"""
Trading Service with Distributed Tracing - Example implementation
Shows how to integrate comprehensive observability into your trading system
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

# Import tracing utilities
from src.utils.tracing_middleware import setup_tracing_middleware, log_request
from src.utils.distributed_tracing import (
    trace_request, 
    trace_database_operation, 
    trace_external_api_call,
    trace_message_queue,
    distributed_tracer,
    set_attribute,
    add_event
)

# Import existing metrics
from trading_metrics import (
    trading_metrics, 
    record_trade_execution, 
    record_strategy_signal,
    update_portfolio_metrics,
    update_risk_metrics,
    record_request as record_metrics_request,
    record_error
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Service with Tracing", version="1.0.0")

# Setup tracing middleware
setup_tracing_middleware(app, service_name="trading-service")

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
    user_id: Optional[str] = None

class PortfolioRequest(BaseModel):
    user_id: str

class RiskRequest(BaseModel):
    symbol: str
    quantity: float
    action: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading-service"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/api/trade")
@trace_request(operation="create_trade")
async def create_trade(request: TradeRequest, http_request: Request):
    """Create a new trade with comprehensive tracing"""
    
    # Log request with context
    log_request(http_request, level="info")
    
    # Add trade-specific attributes to span
    set_attribute("trade.symbol", request.symbol)
    set_attribute("trade.action", request.action)
    set_attribute("trade.quantity", request.quantity)
    set_attribute("trade.strategy", request.strategy or "manual")
    
    try:
        # 1. Validate trade request
        with distributed_tracer.span("trade.validation") as span:
            span.set_attribute("trade.symbol", request.symbol)
            span.set_attribute("trade.quantity", request.quantity)
            
            if request.quantity <= 0:
                raise HTTPException(status_code=400, detail="Invalid quantity")
            
            if request.action not in ["buy", "sell"]:
                raise HTTPException(status_code=400, detail="Invalid action")
            
            add_event("trade.validation.success")
        
        # 2. Check risk limits
        with distributed_tracer.span("risk.check") as span:
            span.set_attribute("risk.symbol", request.symbol)
            span.set_attribute("risk.quantity", request.quantity)
            span.set_attribute("risk.action", request.action)
            
            # Simulate risk check
            risk_result = await check_risk_limits(request)
            span.set_attribute("risk.approved", risk_result["approved"])
            span.set_attribute("risk.exposure", risk_result["exposure"])
            
            if not risk_result["approved"]:
                add_event("risk.check.failed", {"reason": risk_result["reason"]})
                raise HTTPException(status_code=400, detail=f"Risk limit exceeded: {risk_result['reason']}")
            
            add_event("risk.check.approved")
        
        # 3. Get market data
        with distributed_tracer.span("market.data.fetch") as span:
            span.set_attribute("market.symbol", request.symbol)
            
            market_data = await get_market_data(request.symbol)
            span.set_attribute("market.price", market_data["price"])
            span.set_attribute("market.volume", market_data["volume"])
            
            add_event("market.data.fetched")
        
        # 4. Execute trade
        with distributed_tracer.span("trade.execution") as span:
            span.set_attribute("execution.symbol", request.symbol)
            span.set_attribute("execution.quantity", request.quantity)
            span.set_attribute("execution.price", request.price or market_data["price"])
            
            trade_result = await execute_trade(request, market_data)
            span.set_attribute("execution.success", trade_result["success"])
            span.set_attribute("execution.trade_id", trade_result["trade_id"])
            
            add_event("trade.executed", {"trade_id": trade_result["trade_id"]})
        
        # 5. Update portfolio
        with distributed_tracer.span("portfolio.update") as span:
            span.set_attribute("portfolio.user_id", request.user_id)
            span.set_attribute("portfolio.trade_id", trade_result["trade_id"])
            
            portfolio_update = await update_portfolio(request, trade_result)
            span.set_attribute("portfolio.new_value", portfolio_update["new_value"])
            span.set_attribute("portfolio.new_pnl", portfolio_update["new_pnl"])
            
            add_event("portfolio.updated")
        
        # 6. Record metrics
        record_trade_execution(request.symbol, request.action, request.quantity, trade_result["price"])
        record_metrics_request("POST", "/api/trade", 200, time.time())
        
        return {
            "success": True,
            "trade_id": trade_result["trade_id"],
            "executed_price": trade_result["price"],
            "portfolio_value": portfolio_update["new_value"],
            "pnl": portfolio_update["new_pnl"]
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        record_metrics_request("POST", "/api/trade", 400, time.time())
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Trade execution failed: {e}")
        record_error("trade_execution", str(e))
        record_metrics_request("POST", "/api/trade", 500, time.time())
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/portfolio/{user_id}")
@trace_database_operation(operation="get_portfolio", table="portfolios")
async def get_portfolio(user_id: str, http_request: Request):
    """Get portfolio with database tracing"""
    
    log_request(http_request, level="info")
    
    try:
        # Simulate database query
        portfolio_data = await query_portfolio_database(user_id)
        
        return {
            "user_id": user_id,
            "portfolio": portfolio_data,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Portfolio query failed: {e}")
        record_error("portfolio_query", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve portfolio")

@app.post("/api/risk/check")
@trace_request(operation="risk_check")
async def check_risk(request: RiskRequest, http_request: Request):
    """Check risk limits with tracing"""
    
    log_request(http_request, level="info")
    
    set_attribute("risk.symbol", request.symbol)
    set_attribute("risk.quantity", request.quantity)
    set_attribute("risk.action", request.action)
    
    try:
        risk_result = await check_risk_limits(request)
        
        return {
            "approved": risk_result["approved"],
            "exposure": risk_result["exposure"],
            "limit": risk_result["limit"],
            "reason": risk_result.get("reason")
        }
        
    except Exception as e:
        logger.error(f"Risk check failed: {e}")
        record_error("risk_check", str(e))
        raise HTTPException(status_code=500, detail="Risk check failed")

# Helper functions with tracing

@trace_external_api_call("market-data-service", "/api/price/{symbol}")
async def get_market_data(symbol: str) -> Dict[str, Any]:
    """Get market data with external API tracing"""
    # Simulate external API call
    await asyncio.sleep(0.1)  # Simulate network delay
    
    return {
        "symbol": symbol,
        "price": 150.0 + (hash(symbol) % 100),  # Mock price
        "volume": 1000000,
        "timestamp": time.time()
    }

@trace_database_operation(operation="check_risk", table="risk_limits")
async def check_risk_limits(request: RiskRequest) -> Dict[str, Any]:
    """Check risk limits with database tracing"""
    # Simulate database query
    await asyncio.sleep(0.05)  # Simulate DB query time
    
    current_exposure = 15000.0
    max_exposure = 20000.0
    
    new_exposure = current_exposure + (request.quantity * 150.0)  # Mock calculation
    
    return {
        "approved": new_exposure <= max_exposure,
        "exposure": new_exposure,
        "limit": max_exposure,
        "reason": "Exposure limit exceeded" if new_exposure > max_exposure else None
    }

@trace_message_queue(operation="publish", queue="trade-execution")
async def execute_trade(request: TradeRequest, market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute trade with message queue tracing"""
    # Simulate trade execution
    await asyncio.sleep(0.2)  # Simulate execution time
    
    trade_id = f"trade_{int(time.time() * 1000)}"
    executed_price = request.price or market_data["price"]
    
    return {
        "success": True,
        "trade_id": trade_id,
        "price": executed_price,
        "timestamp": time.time()
    }

@trace_database_operation(operation="update_portfolio", table="portfolios")
async def update_portfolio(request: TradeRequest, trade_result: Dict[str, Any]) -> Dict[str, Any]:
    """Update portfolio with database tracing"""
    # Simulate database update
    await asyncio.sleep(0.05)  # Simulate DB update time
    
    return {
        "new_value": 102500.0,  # Mock new value
        "new_pnl": 3000.0,      # Mock new P&L
        "timestamp": time.time()
    }

@trace_database_operation(operation="select", table="portfolios")
async def query_portfolio_database(user_id: str) -> Dict[str, Any]:
    """Query portfolio database with tracing"""
    # Simulate database query
    await asyncio.sleep(0.03)  # Simulate DB query time
    
    return {
        "value": 100000.0,
        "positions": 5,
        "pnl": 2500.0,
        "last_updated": time.time()
    }

if __name__ == "__main__":
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=11080)


