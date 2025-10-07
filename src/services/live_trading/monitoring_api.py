#!/usr/bin/env python3
"""
Live Trading Monitoring API
REST API for monitoring live trading positions and exit strategies
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .position_monitor import position_monitor
from .exit_strategy_service import exit_strategy_service

logger = logging.getLogger(__name__)

app = FastAPI(title="Live Trading Monitoring API", version="1.0.0")

class PositionSummary(BaseModel):
    """Position summary model"""
    symbol: str
    strategy: str
    pnl_pct: float
    holding_days: int
    risk_level: str

class MonitoringSummary(BaseModel):
    """Monitoring summary model"""
    total_positions: int
    high_risk_positions: int
    monitoring_active: bool
    last_update: str
    positions: List[PositionSummary]

class ExitStrategyConfig(BaseModel):
    """Exit strategy configuration model"""
    strategy_name: str
    strategies: List[Dict[str, Any]]

@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get monitoring system status"""
    return {
        "monitoring_active": position_monitor.is_monitoring,
        "monitored_positions": len(position_monitor.monitored_positions),
        "exit_strategies_configured": len(exit_strategy_service.exit_strategies),
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/monitoring/positions")
async def get_active_positions():
    """Get all active positions"""
    summary = await position_monitor.get_monitoring_summary()
    return summary

@app.get("/api/monitoring/positions/{symbol}")
async def get_position_by_symbol(symbol: str):
    """Get position by symbol"""
    for position in position_monitor.monitored_positions.values():
        if position.symbol == symbol:
            return position
    raise HTTPException(status_code=404, detail="Position not found")

@app.get("/api/exit-strategies")
async def get_exit_strategies():
    """Get all exit strategies"""
    return {
        "configured_strategies": exit_strategy_service.exit_strategies,
        "default_strategies": exit_strategy_service.default_strategies
    }

@app.get("/api/exit-strategies/{strategy_name}")
async def get_exit_strategies_for_strategy(strategy_name: str):
    """Get exit strategies for a specific trading strategy"""
    strategies = exit_strategy_service.get_exit_strategies(strategy_name)
    return {
        "strategy_name": strategy_name,
        "exit_strategies": [
            {
                "type": s.strategy_type.value,
                "parameters": s.parameters,
                "is_active": s.is_active,
                "priority": s.priority
            }
            for s in strategies
        ]
    }

@app.post("/api/exit-strategies/{strategy_name}")
async def set_exit_strategies_for_strategy(strategy_name: str, config: ExitStrategyConfig):
    """Set exit strategies for a specific trading strategy"""
    try:
        # Convert config to ExitStrategy objects
        strategies = []
        for strategy_data in config.strategies:
            strategy = ExitStrategy(
                strategy_type=ExitStrategyType(strategy_data['type']),
                parameters=strategy_data['parameters'],
                is_active=strategy_data.get('is_active', True),
                priority=strategy_data.get('priority', 1)
            )
            strategies.append(strategy)
        
        exit_strategy_service.set_exit_strategies(strategy_name, strategies)
        
        return {
            "message": f"Exit strategies set for {strategy_name}",
            "strategies_count": len(strategies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/monitoring/start")
async def start_monitoring():
    """Start position monitoring"""
    if not position_monitor.is_monitoring:
        asyncio.create_task(position_monitor.start_monitoring())
        return {"message": "Monitoring started"}
    else:
        return {"message": "Monitoring already active"}

@app.post("/api/monitoring/stop")
async def stop_monitoring():
    """Stop position monitoring"""
    await position_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}

@app.get("/api/monitoring/alerts")
async def get_monitoring_alerts():
    """Get monitoring alerts"""
    alerts = []
    
    # Check for high-risk positions
    high_risk_count = sum(1 for p in position_monitor.monitored_positions.values() if p.risk_level == "HIGH")
    if high_risk_count > 0:
        alerts.append({
            "type": "HIGH_RISK_POSITIONS",
            "message": f"{high_risk_count} high-risk positions detected",
            "severity": "HIGH",
            "timestamp": datetime.now().isoformat()
        })
    
    # Check for long-held positions
    long_held_count = sum(1 for p in position_monitor.monitored_positions.values() if p.holding_days > 20)
    if long_held_count > 0:
        alerts.append({
            "type": "LONG_HELD_POSITIONS",
            "message": f"{long_held_count} positions held for more than 20 days",
            "severity": "MEDIUM",
            "timestamp": datetime.now().isoformat()
        })
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11181)
