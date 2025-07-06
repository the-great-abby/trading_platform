"""
FastAPI web interface for the trading bot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn

from ..core.trading_engine import TradingEngine, TradingMode
from ..utils.config import Config
from .news_api import router as news_router


# Pydantic models for API
class StrategyConfig(BaseModel):
    name: str
    symbol: str
    parameters: Dict[str, Any]


class StrategyUpdate(BaseModel):
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class TradeSignal(BaseModel):
    symbol: str
    action: str
    quantity: float
    price: float
    timestamp: str
    strategy: str
    confidence: float


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    total_pnl: float
    total_pnl_percentage: float
    daily_pnl: float
    max_drawdown: float
    num_positions: int
    positions: List[Dict[str, Any]]


# Global trading engine instance
trading_engine: Optional[TradingEngine] = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="AlgoTrader API",
        description="API for algorithmic trading bot",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()

# Include news API router
app.include_router(news_router)


@app.on_event("startup")
async def startup_event():
    """Initialize trading engine on startup"""
    global trading_engine
    config = Config()
    trading_engine = TradingEngine(config)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AlgoTrader API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "trading_engine_running": trading_engine.is_running if trading_engine else False
    }


@app.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio():
    """Get portfolio summary"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    return trading_engine.portfolio.get_portfolio_summary()


@app.get("/performance")
async def get_performance():
    """Get performance metrics"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    return trading_engine.get_performance_summary()


@app.get("/strategies")
async def get_strategies():
    """Get list of registered strategies"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    strategies = []
    for name, strategy in trading_engine.strategies.items():
        strategies.append({
            "name": name,
            "strategy": strategy.get_strategy_info(),
            "is_active": strategy.is_active
        })
    
    return {"strategies": strategies}


@app.post("/strategies/register")
async def register_strategy(config: StrategyConfig):
    """Register a new trading strategy"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    # This would dynamically create and register strategies
    # For now, return a placeholder response
    return {
        "message": "Strategy registration endpoint",
        "config": config.dict()
    }


@app.put("/strategies/{strategy_name}/update")
async def update_strategy(strategy_name: str, update: StrategyUpdate):
    """Update strategy parameters or activation status"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    if strategy_name not in trading_engine.strategies:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
    
    strategy = trading_engine.strategies[strategy_name]
    
    # Update activation status
    if update.is_active is not None:
        if update.is_active:
            strategy.activate()
        else:
            strategy.deactivate()
    
    # Update parameters
    if update.parameters:
        strategy.config.update(update.parameters)
    
    return {
        "message": f"Strategy {strategy_name} updated",
        "strategy": strategy.get_strategy_info()
    }


@app.post("/strategies/{strategy_name}/activate")
async def activate_strategy(strategy_name: str):
    """Activate a strategy"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    if strategy_name not in trading_engine.strategies:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
    
    trading_engine.strategies[strategy_name].activate()
    return {"message": f"Strategy {strategy_name} activated"}


@app.post("/strategies/{strategy_name}/deactivate")
async def deactivate_strategy(strategy_name: str):
    """Deactivate a strategy"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    if strategy_name not in trading_engine.strategies:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
    
    trading_engine.strategies[strategy_name].deactivate()
    return {"message": f"Strategy {strategy_name} deactivated"}


@app.post("/engine/start")
async def start_engine():
    """Start the trading engine"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    if trading_engine.is_running:
        raise HTTPException(status_code=400, detail="Trading engine is already running")
    
    # Start engine in background
    import asyncio
    asyncio.create_task(trading_engine.start())
    
    return {"message": "Trading engine started"}


@app.post("/engine/stop")
async def stop_engine():
    """Stop the trading engine"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    if not trading_engine.is_running:
        raise HTTPException(status_code=400, detail="Trading engine is not running")
    
    await trading_engine.stop()
    return {"message": "Trading engine stopped"}


@app.get("/engine/status")
async def get_engine_status():
    """Get trading engine status"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    return {
        "is_running": trading_engine.is_running,
        "mode": trading_engine.mode.value,
        "total_trades": len(trading_engine.trade_history),
        "active_positions": len(trading_engine.active_positions)
    }


@app.post("/engine/mode")
async def set_trading_mode(mode: str):
    """Set trading mode"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    try:
        trading_mode = TradingMode(mode)
        trading_engine.set_mode(trading_mode)
        return {"message": f"Trading mode set to {mode}"}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid trading mode: {mode}")


@app.get("/trades")
async def get_trade_history(limit: int = 100):
    """Get trade history"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    trades = trading_engine.trade_history[-limit:] if trading_engine.trade_history else []
    return {"trades": trades, "total": len(trading_engine.trade_history)}


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 