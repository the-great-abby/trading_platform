"""
Risk Service - Internal microservice for risk management operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Risk Service", version="1.0.0")

class RiskAssessmentRequest(BaseModel):
    portfolio_value: float
    positions: List[Dict[str, Any]]
    cash: float

class RiskAssessmentResponse(BaseModel):
    total_risk_score: float
    max_position_size: float
    recommended_cash_reserve: float
    risk_metrics: Dict[str, Any]

class PositionRiskRequest(BaseModel):
    symbol: str
    quantity: float
    price: float
    portfolio_value: float

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "risk-service"}

@app.get("/status")
async def get_status():
    """Get risk service status"""
    return {
        "service": "risk-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/risk/assess-portfolio", response_model=RiskAssessmentResponse)
async def assess_portfolio_risk(request: RiskAssessmentRequest):
    """Assess overall portfolio risk"""
    try:
        # Calculate basic risk metrics
        total_position_value = sum(pos.get('value', 0) for pos in request.positions)
        portfolio_value = request.portfolio_value
        
        # Calculate concentration risk
        concentration_risk = 0
        for position in request.positions:
            position_value = position.get('value', 0)
            if portfolio_value > 0:
                concentration = position_value / portfolio_value
                concentration_risk += concentration ** 2  # Herfindahl index
        
        # Calculate leverage
        leverage = total_position_value / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate cash ratio
        cash_ratio = request.cash / portfolio_value if portfolio_value > 0 else 0
        
        # Overall risk score (0-100, higher = more risky)
        risk_score = min(100, (
            concentration_risk * 50 +
            max(0, leverage - 1) * 30 +
            max(0, 0.1 - cash_ratio) * 20
        ))
        
        # Recommendations
        max_position_size = portfolio_value * 0.05  # 5% max per position
        recommended_cash_reserve = portfolio_value * 0.1  # 10% cash reserve
        
        logger.info(f"Portfolio risk assessment completed. Risk score: {risk_score}")
        
        return RiskAssessmentResponse(
            total_risk_score=risk_score,
            max_position_size=max_position_size,
            recommended_cash_reserve=recommended_cash_reserve,
            risk_metrics={
                "concentration_risk": concentration_risk,
                "leverage": leverage,
                "cash_ratio": cash_ratio,
                "total_position_value": total_position_value,
                "portfolio_value": portfolio_value
            }
        )
    except Exception as e:
        logger.error(f"Portfolio risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.post("/risk/check-position")
async def check_position_risk(request: PositionRiskRequest):
    """Check if a specific position meets risk requirements"""
    try:
        position_value = request.quantity * request.price
        position_ratio = position_value / request.portfolio_value if request.portfolio_value > 0 else 0
        
        # Risk limits
        max_position_ratio = 0.05  # 5% max per position
        max_position_value = request.portfolio_value * max_position_ratio
        
        is_acceptable = position_ratio <= max_position_ratio
        
        risk_level = "high" if position_ratio > 0.03 else "medium" if position_ratio > 0.01 else "low"
        
        return {
            "symbol": request.symbol,
            "position_value": position_value,
            "position_ratio": position_ratio,
            "max_allowed_ratio": max_position_ratio,
            "max_allowed_value": max_position_value,
            "is_acceptable": is_acceptable,
            "risk_level": risk_level,
            "recommendation": "reject" if not is_acceptable else "accept"
        }
    except Exception as e:
        logger.error(f"Position risk check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Position risk check failed: {str(e)}")

@app.get("/risk/limits")
async def get_risk_limits():
    """Get current risk limits"""
    return {
        "max_position_size_ratio": 0.05,  # 5% max per position
        "max_portfolio_leverage": 1.5,    # 150% max leverage
        "min_cash_reserve_ratio": 0.1,    # 10% min cash reserve
        "max_concentration_risk": 0.3,    # 30% max concentration
        "daily_loss_limit": 0.02,         # 2% daily loss limit
        "max_drawdown": 0.15              # 15% max drawdown
    }

@app.get("/risk/metrics")
async def get_risk_metrics():
    """Get current risk metrics"""
    # Mock risk metrics
    return {
        "current_risk_score": 25.5,
        "var_95": 0.015,  # 1.5% Value at Risk (95%)
        "var_99": 0.025,  # 2.5% Value at Risk (99%)
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.08,
        "volatility": 0.18,
        "beta": 1.1
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
