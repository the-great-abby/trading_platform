"""
Strategy Service - Internal microservice for trading strategy operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Strategy Service", version="1.0.0")

class StrategyConfig(BaseModel):
    name: str
    symbol: str
    parameters: Dict[str, Any]

class StrategyStatus(BaseModel):
    name: str
    is_active: bool
    symbol: str
    parameters: Dict[str, Any]
    performance: Dict[str, Any]

class SignalRequest(BaseModel):
    strategy_name: str
    symbol: str
    market_data: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "strategy-service"}

@app.get("/status")
async def get_status():
    """Get strategy service status"""
    return {
        "service": "strategy-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/strategies")
async def get_strategies():
    """Get all available strategies"""
    try:
        strategies = [
            {
                "name": "sma_crossover",
                "display_name": "SMA Crossover",
                "description": "Simple Moving Average Crossover Strategy",
                "parameters": {
                    "short_window": 20,
                    "long_window": 50,
                    "min_volume": 1000000
                },
                "is_active": True
            },
            {
                "name": "rsi_strategy",
                "display_name": "RSI Strategy",
                "description": "Relative Strength Index Strategy",
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70
                },
                "is_active": True
            },
            {
                "name": "macd_strategy",
                "display_name": "MACD Strategy",
                "description": "Moving Average Convergence Divergence Strategy",
                "parameters": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "is_active": True
            },
            {
                "name": "bollinger_bands",
                "display_name": "Bollinger Bands Strategy",
                "description": "Bollinger Bands Mean Reversion Strategy",
                "parameters": {
                    "period": 20,
                    "std_dev": 2
                },
                "is_active": True
            },
            {
                "name": "news_enhanced",
                "display_name": "News Enhanced Strategy",
                "description": "Technical indicators enhanced with news sentiment",
                "parameters": {
                    "sentiment_threshold": 0.6,
                    "news_weight": 0.3,
                    "technical_weight": 0.7
                },
                "is_active": True
            }
        ]
        
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")

@app.get("/strategies/{strategy_name}")
async def get_strategy(strategy_name: str):
    """Get specific strategy details"""
    try:
        # Mock strategy details
        strategy = {
            "name": strategy_name,
            "display_name": strategy_name.replace("_", " ").title(),
            "description": f"Strategy for {strategy_name}",
            "parameters": {
                "period": 20,
                "threshold": 0.5
            },
            "is_active": True,
            "performance": {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.08,
                "win_rate": 0.65,
                "total_trades": 45
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return strategy
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")

@app.post("/strategies/{strategy_name}/activate")
async def activate_strategy(strategy_name: str):
    """Activate a strategy"""
    try:
        logger.info(f"Activating strategy: {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} activated successfully",
            "strategy_name": strategy_name,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to activate strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate strategy: {str(e)}")

@app.post("/strategies/{strategy_name}/deactivate")
async def deactivate_strategy(strategy_name: str):
    """Deactivate a strategy"""
    try:
        logger.info(f"Deactivating strategy: {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} deactivated successfully",
            "strategy_name": strategy_name,
            "status": "inactive",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to deactivate strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate strategy: {str(e)}")

@app.put("/strategies/{strategy_name}/config")
async def update_strategy_config(strategy_name: str, config: StrategyConfig):
    """Update strategy configuration"""
    try:
        logger.info(f"Updating strategy config for {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} configuration updated successfully",
            "strategy_name": strategy_name,
            "new_config": config.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update strategy config for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update strategy config: {str(e)}")

@app.post("/strategies/{strategy_name}/signal", response_model=Dict[str, Any])
async def generate_signal(strategy_name: str, request: SignalRequest):
    """Generate trading signal for a strategy"""
    try:
        # Mock signal generation
        import random
        
        signal_types = ["buy", "sell", "hold"]
        signal = random.choice(signal_types)
        
        if signal == "hold":
            return {
                "strategy_name": strategy_name,
                "symbol": request.symbol,
                "signal": "hold",
                "confidence": 0.0,
                "reason": "No clear signal",
                "timestamp": datetime.now().isoformat()
            }
        
        confidence = random.uniform(0.6, 0.95)
        price = request.market_data.get("close", 100.0)
        
        logger.info(f"Generated {signal} signal for {request.symbol} using {strategy_name}")
        
        return {
            "strategy_name": strategy_name,
            "symbol": request.symbol,
            "signal": signal,
            "confidence": confidence,
            "price": price,
            "quantity": 100 if signal == "buy" else 0,
            "reason": f"{strategy_name} strategy indicates {signal} signal",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to generate signal for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate signal: {str(e)}")

@app.get("/strategies/{strategy_name}/performance")
async def get_strategy_performance(strategy_name: str, period: str = "1m"):
    """Get strategy performance metrics"""
    try:
        # Mock performance data
        performance = {
            "strategy_name": strategy_name,
            "period": period,
            "total_return": 0.12,
            "annualized_return": 0.144,
            "volatility": 0.16,
            "sharpe_ratio": 1.1,
            "max_drawdown": 0.06,
            "win_rate": 0.68,
            "profit_factor": 1.9,
            "total_trades": 52,
            "avg_trade_duration": "2.5 days",
            "best_trade": 0.08,
            "worst_trade": -0.04
        }
        
        return performance
    except Exception as e:
        logger.error(f"Failed to get performance for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
