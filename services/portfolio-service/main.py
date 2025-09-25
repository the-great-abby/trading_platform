"""
Advanced Portfolio Service - FastAPI microservice
Exposes advanced portfolio management capabilities through REST APIs
"""
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Advanced Portfolio Service",
    version="2.0.0",
    description="Advanced portfolio management with MPT, Black-Litterman, and Risk Parity optimization"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class PortfolioCreateRequest(BaseModel):
    name: str = Field(..., description="Portfolio name")
    description: str = Field("", description="Portfolio description")
    owner_id: str = Field(..., description="Owner ID")
    base_currency: str = Field("USD", description="Base currency")
    risk_tolerance: str = Field("MODERATE", description="Risk tolerance level")
    rebalancing_frequency: str = Field("MONTHLY", description="Rebalancing frequency")
    max_single_asset_weight: float = Field(0.10, description="Maximum single asset weight")
    max_sector_weight: float = Field(0.30, description="Maximum sector weight")
    long_only: bool = Field(True, description="Long-only portfolio")

class PositionAddRequest(BaseModel):
    asset_id: str = Field(..., description="Asset identifier")
    quantity: float = Field(..., description="Position quantity")
    average_cost: float = Field(..., description="Average cost per share")
    current_price: Optional[float] = Field(None, description="Current market price")

# Health and status endpoints
@app.get("/")
async def root():
    return {
        "service": "Advanced Portfolio Service",
        "version": "2.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "portfolio-service",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Portfolio management endpoints
@app.post("/api/v1/portfolios", response_model=Dict[str, Any])
async def create_portfolio(request: PortfolioCreateRequest):
    """Create a new portfolio"""
    try:
        # Mock implementation for now
        portfolio_data = {
            "portfolio_id": "mock-portfolio-123",
            "name": request.name,
            "description": request.description,
            "owner_id": request.owner_id,
            "base_currency": request.base_currency,
            "risk_tolerance": request.risk_tolerance,
            "rebalancing_frequency": request.rebalancing_frequency,
            "max_single_asset_weight": request.max_single_asset_weight,
            "max_sector_weight": request.max_sector_weight,
            "long_only": request.long_only,
            "total_value": 0.0,
            "cash_balance": 0.0,
            "creation_date": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        
        return {
            "success": True,
            "portfolio": portfolio_data,
            "message": f"Portfolio '{request.name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/portfolios", response_model=List[Dict[str, Any]])
async def get_portfolios(owner_id: Optional[str] = None, status: Optional[str] = None):
    """Get portfolios with optional filtering"""
    try:
        # Mock implementation
        portfolios = [
            {
                "portfolio_id": "mock-portfolio-123",
                "name": "Sample Portfolio",
                "description": "A sample portfolio for testing",
                "owner_id": owner_id or "user123",
                "base_currency": "USD",
                "risk_tolerance": "MODERATE",
                "rebalancing_frequency": "MONTHLY",
                "total_value": 100000.0,
                "cash_balance": 10000.0,
                "creation_date": datetime.now().isoformat(),
                "status": status or "ACTIVE"
            }
        ]
        
        return portfolios
    except Exception as e:
        logger.error(f"Error getting portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/portfolios/{portfolio_id}", response_model=Dict[str, Any])
async def get_portfolio(portfolio_id: str):
    """Get portfolio by ID"""
    try:
        if portfolio_id != "mock-portfolio-123":
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        portfolio = {
            "portfolio_id": portfolio_id,
            "name": "Sample Portfolio",
            "description": "A sample portfolio for testing",
            "owner_id": "user123",
            "base_currency": "USD",
            "risk_tolerance": "MODERATE",
            "rebalancing_frequency": "MONTHLY",
            "total_value": 100000.0,
            "cash_balance": 10000.0,
            "positions": [],
            "creation_date": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portfolios/{portfolio_id}/positions", response_model=Dict[str, Any])
async def add_position(portfolio_id: str, request: PositionAddRequest):
    """Add position to portfolio"""
    try:
        if portfolio_id != "mock-portfolio-123":
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        position = {
            "position_id": f"pos-{datetime.now().timestamp()}",
            "portfolio_id": portfolio_id,
            "asset_id": request.asset_id,
            "quantity": request.quantity,
            "average_cost": request.average_cost,
            "current_price": request.current_price or request.average_cost,
            "market_value": request.quantity * (request.current_price or request.average_cost),
            "unrealized_pnl": 0.0,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "position": position,
            "message": f"Position added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding position: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/portfolios/{portfolio_id}/performance")
async def get_portfolio_performance(portfolio_id: str):
    """Get portfolio performance metrics"""
    try:
        if portfolio_id != "mock-portfolio-123":
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        performance = {
            "total_value": 100000.0,
            "total_invested": 90000.0,
            "unrealized_pnl": 10000.0,
            "total_return": 0.111,  # 11.1%
            "positions": [],
            "weights": {}
        }
        
        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/portfolios/{portfolio_id}/risk-metrics")
async def get_risk_metrics(portfolio_id: str):
    """Get latest risk metrics for portfolio"""
    try:
        if portfolio_id != "mock-portfolio-123":
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        risk_metrics = {
            "risk_metrics_id": "risk-123",
            "portfolio_id": portfolio_id,
            "calculation_date": datetime.now().isoformat(),
            "var_95": -5000.0,  # 5% VaR
            "var_99": -8000.0,  # 8% VaR
            "cvar_95": -6000.0,  # 6% CVaR
            "cvar_99": -10000.0,  # 10% CVaR
            "systematic_risk": 0.04,  # 20% volatility
            "idiosyncratic_risk": 0.01,  # 10% idiosyncratic
            "market_beta": 1.0,
            "average_correlation": 0.3,
            "max_correlation": 0.8,
            "min_correlation": 0.0
        }
        
        return risk_metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )