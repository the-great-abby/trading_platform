"""
Portfolio Optimization API endpoints
Exposes MPT, Black-Litterman, and Risk Parity optimization through REST APIs
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Import optimization services
import sys
sys.path.append('/Users/abby/code/trading/src')

from portfolio.optimization import (
    MPTOptimizer, BlackLittermanOptimizer, RiskParityOptimizer
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/optimization", tags=["optimization"])

# Pydantic models for optimization requests
class MPTOptimizationRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    optimization_type: str = Field("max_sharpe", description="Optimization type: max_sharpe, min_volatility, max_return")
    risk_free_rate: float = Field(0.02, description="Risk-free rate")
    target_return: Optional[float] = Field(None, description="Target return (for min_volatility optimization)")
    target_volatility: Optional[float] = Field(None, description="Target volatility (for max_return optimization)")
    max_weight: float = Field(0.30, description="Maximum weight per asset")
    min_weight: float = Field(0.01, description="Minimum weight per asset")

class BlackLittermanRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    market_views: List[Dict[str, Any]] = Field(..., description="Market views")
    confidence_level: float = Field(0.5, description="Confidence level")
    risk_aversion: float = Field(3.0, description="Risk aversion parameter")
    optimization_type: str = Field("max_sharpe", description="Optimization type")
    max_weight: float = Field(0.30, description="Maximum weight per asset")
    min_weight: float = Field(0.01, description="Minimum weight per asset")

class RiskParityRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    target_risk_contributions: Optional[Dict[str, float]] = Field(None, description="Target risk contributions by asset")
    max_weight: float = Field(0.30, description="Maximum weight per asset")
    min_weight: float = Field(0.01, description="Minimum weight per asset")

class EfficientFrontierRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    num_points: int = Field(20, description="Number of points on efficient frontier")
    risk_free_rate: float = Field(0.02, description="Risk-free rate")

# Optimization endpoints
@router.post("/mpt", response_model=Dict[str, Any])
async def optimize_mpt(request: MPTOptimizationRequest):
    """Optimize portfolio using Modern Portfolio Theory"""
    try:
        # Mock implementation for now
        optimization_result = {
            "optimization_id": f"mpt-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "optimization_type": request.optimization_type,
            "optimization_date": datetime.now().isoformat(),
            "optimal_weights": {
                "AAPL": 0.25,
                "MSFT": 0.20,
                "GOOGL": 0.15,
                "TSLA": 0.12,
                "NVDA": 0.10,
                "AMZN": 0.08,
                "META": 0.05,
                "NFLX": 0.03,
                "CRM": 0.02
            },
            "expected_return": 0.12,
            "expected_volatility": 0.18,
            "sharpe_ratio": 0.67,
            "risk_free_rate": request.risk_free_rate,
            "constraints": {
                "max_weight": request.max_weight,
                "min_weight": request.min_weight,
                "long_only": True
            },
            "optimization_status": "SUCCESS",
            "convergence_achieved": True,
            "iterations": 150
        }
        
        return {
            "success": True,
            "optimization": optimization_result,
            "message": "MPT optimization completed successfully"
        }
    except Exception as e:
        logger.error(f"Error in MPT optimization: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/black-litterman", response_model=Dict[str, Any])
async def optimize_black_litterman(request: BlackLittermanRequest):
    """Optimize portfolio using Black-Litterman model"""
    try:
        # Mock implementation for now
        optimization_result = {
            "optimization_id": f"bl-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "optimization_type": request.optimization_type,
            "optimization_date": datetime.now().isoformat(),
            "market_views": request.market_views,
            "confidence_level": request.confidence_level,
            "risk_aversion": request.risk_aversion,
            "optimal_weights": {
                "AAPL": 0.28,  # Slightly higher due to positive view
                "MSFT": 0.22,
                "GOOGL": 0.16,
                "TSLA": 0.10,  # Lower due to negative view
                "NVDA": 0.12,
                "AMZN": 0.06,
                "META": 0.04,
                "NFLX": 0.02
            },
            "expected_return": 0.13,  # Higher due to views
            "expected_volatility": 0.19,
            "sharpe_ratio": 0.68,
            "view_impact": {
                "AAPL": 0.03,  # Positive view impact
                "TSLA": -0.02   # Negative view impact
            },
            "constraints": {
                "max_weight": request.max_weight,
                "min_weight": request.min_weight,
                "long_only": True
            },
            "optimization_status": "SUCCESS",
            "convergence_achieved": True,
            "iterations": 180
        }
        
        return {
            "success": True,
            "optimization": optimization_result,
            "message": "Black-Litterman optimization completed successfully"
        }
    except Exception as e:
        logger.error(f"Error in Black-Litterman optimization: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/risk-parity", response_model=Dict[str, Any])
async def optimize_risk_parity(request: RiskParityRequest):
    """Optimize portfolio using Risk Parity approach"""
    try:
        # Mock implementation for now
        optimization_result = {
            "optimization_id": f"rp-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "optimization_date": datetime.now().isoformat(),
            "optimal_weights": {
                "AAPL": 0.18,  # Lower weight due to higher risk
                "MSFT": 0.20,
                "GOOGL": 0.16,
                "TSLA": 0.08,  # Much lower due to high volatility
                "NVDA": 0.12,
                "AMZN": 0.10,
                "META": 0.08,
                "NFLX": 0.06,
                "CRM": 0.02
            },
            "risk_contributions": {
                "AAPL": 0.125,  # Equal risk contribution
                "MSFT": 0.125,
                "GOOGL": 0.125,
                "TSLA": 0.125,
                "NVDA": 0.125,
                "AMZN": 0.125,
                "META": 0.125,
                "NFLX": 0.125
            },
            "expected_return": 0.11,
            "expected_volatility": 0.16,
            "sharpe_ratio": 0.69,
            "diversification_ratio": 2.8,
            "constraints": {
                "max_weight": request.max_weight,
                "min_weight": request.min_weight,
                "long_only": True
            },
            "optimization_status": "SUCCESS",
            "convergence_achieved": True,
            "iterations": 200
        }
        
        return {
            "success": True,
            "optimization": optimization_result,
            "message": "Risk Parity optimization completed successfully"
        }
    except Exception as e:
        logger.error(f"Error in Risk Parity optimization: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/efficient-frontier", response_model=Dict[str, Any])
async def generate_efficient_frontier(request: EfficientFrontierRequest):
    """Generate efficient frontier for portfolio"""
    try:
        # Mock implementation for now
        frontier_points = []
        
        for i in range(request.num_points):
            risk_level = 0.10 + (i / (request.num_points - 1)) * 0.20  # 10% to 30% volatility
            expected_return = 0.08 + (risk_level - 0.10) * 0.5  # Linear relationship
            
            frontier_points.append({
                "expected_return": expected_return,
                "expected_volatility": risk_level,
                "sharpe_ratio": (expected_return - request.risk_free_rate) / risk_level
            })
        
        efficient_frontier = {
            "frontier_id": f"ef-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "calculation_date": datetime.now().isoformat(),
            "risk_free_rate": request.risk_free_rate,
            "frontier_points": frontier_points,
            "max_sharpe_point": max(frontier_points, key=lambda x: x["sharpe_ratio"]),
            "min_volatility_point": min(frontier_points, key=lambda x: x["expected_volatility"]),
            "max_return_point": max(frontier_points, key=lambda x: x["expected_return"])
        }
        
        return {
            "success": True,
            "efficient_frontier": efficient_frontier,
            "message": "Efficient frontier generated successfully"
        }
    except Exception as e:
        logger.error(f"Error generating efficient frontier: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{portfolio_id}/results", response_model=List[Dict[str, Any]])
async def get_optimization_results(portfolio_id: str, limit: int = 10):
    """Get optimization results for portfolio"""
    try:
        # Mock implementation
        results = [
            {
                "optimization_id": f"opt-{portfolio_id}-1",
                "portfolio_id": portfolio_id,
                "optimization_type": "MPT_MAX_SHARPE",
                "optimization_date": datetime.now().isoformat(),
                "expected_return": 0.12,
                "expected_volatility": 0.18,
                "sharpe_ratio": 0.67,
                "status": "SUCCESS"
            },
            {
                "optimization_id": f"opt-{portfolio_id}-2",
                "portfolio_id": portfolio_id,
                "optimization_type": "BLACK_LITTERMAN",
                "optimization_date": datetime.now().isoformat(),
                "expected_return": 0.13,
                "expected_volatility": 0.19,
                "sharpe_ratio": 0.68,
                "status": "SUCCESS"
            }
        ]
        
        return results[:limit]
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{optimization_id}/details", response_model=Dict[str, Any])
async def get_optimization_details(optimization_id: str):
    """Get detailed optimization results"""
    try:
        # Mock implementation
        optimization_details = {
            "optimization_id": optimization_id,
            "portfolio_id": "mock-portfolio-123",
            "optimization_type": "MPT_MAX_SHARPE",
            "optimization_date": datetime.now().isoformat(),
            "optimal_weights": {
                "AAPL": 0.25,
                "MSFT": 0.20,
                "GOOGL": 0.15,
                "TSLA": 0.12,
                "NVDA": 0.10,
                "AMZN": 0.08,
                "META": 0.05,
                "NFLX": 0.03,
                "CRM": 0.02
            },
            "expected_return": 0.12,
            "expected_volatility": 0.18,
            "sharpe_ratio": 0.67,
            "risk_free_rate": 0.02,
            "constraints": {
                "max_weight": 0.30,
                "min_weight": 0.01,
                "long_only": True
            },
            "optimization_status": "SUCCESS",
            "convergence_achieved": True,
            "iterations": 150,
            "computation_time": 2.5
        }
        
        return optimization_details
    except Exception as e:
        logger.error(f"Error getting optimization details: {e}")
        raise HTTPException(status_code=500, detail=str(e))












