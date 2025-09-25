"""
Risk Integration Service
Connects the Enhanced Risk Management Service with the Trading System
"""

import asyncio
import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Risk Integration Service",
    version="1.0.0",
    description="Integrates Enhanced Risk Management Service with Trading System"
)

# Configuration
RISK_SERVICE_URL = "http://enhanced-risk-management-service.trading-system.svc.cluster.local:80"
STRATEGY_SERVICE_URL = "http://strategy-service.trading-system.svc.cluster.local:80"
MARKET_DATA_SERVICE_URL = "http://market-data-service.trading-system.svc.cluster.local:11084"

# Pydantic models
class PortfolioRiskRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio identifier")
    positions: List[Dict[str, Any]] = Field(..., description="Portfolio positions")
    portfolio_value: float = Field(..., description="Total portfolio value")
    cash_balance: float = Field(0.0, description="Cash balance")

class TradeRiskRequest(BaseModel):
    trade_id: str = Field(..., description="Trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Buy or Sell")
    quantity: float = Field(..., description="Trade quantity")
    price: float = Field(..., description="Trade price")
    portfolio_id: str = Field(..., description="Portfolio identifier")

class RiskIntegrationResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

# HTTP client
async def get_http_client():
    return httpx.AsyncClient(timeout=30.0)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "risk-integration-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Risk assessment integration
@app.post("/api/risk/assess-portfolio", response_model=RiskIntegrationResponse)
async def assess_portfolio_risk(request: PortfolioRiskRequest):
    """Assess portfolio risk using the enhanced risk management service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call the enhanced risk management service
            risk_response = await client.post(
                f"{RISK_SERVICE_URL}/api/v1/risk/assess",
                json={
                    "portfolio_id": request.portfolio_id,
                    "positions": request.positions,
                    "portfolio_value": request.portfolio_value,
                    "cash_balance": request.cash_balance
                }
            )
            
            if risk_response.status_code == 200:
                risk_data = risk_response.json()
                return RiskIntegrationResponse(
                    success=True,
                    data=risk_data,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return RiskIntegrationResponse(
                    success=False,
                    error=f"Risk assessment failed: {risk_response.status_code}",
                    timestamp=datetime.now().isoformat()
                )
                
    except Exception as e:
        logger.error(f"Portfolio risk assessment failed: {str(e)}")
        return RiskIntegrationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

# Trade risk validation
@app.post("/api/risk/validate-trade", response_model=RiskIntegrationResponse)
async def validate_trade_risk(request: TradeRiskRequest):
    """Validate trade against risk limits"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, get current portfolio risk
            portfolio_response = await client.post(
                f"{RISK_SERVICE_URL}/api/v1/risk/assess",
                json={
                    "portfolio_id": request.portfolio_id,
                    "positions": [],  # Would be populated with actual positions
                    "portfolio_value": 100000,  # Would be actual portfolio value
                    "cash_balance": 10000
                }
            )
            
            if portfolio_response.status_code == 200:
                portfolio_risk = portfolio_response.json()
                
                # Check if trade would violate risk limits
                trade_value = request.quantity * request.price
                current_var_95 = abs(portfolio_risk.get("risk_assessment", {}).get("risk_metrics", {}).get("var_95", 0))
                
                # Simple risk check: trade value should not exceed 5% of portfolio value
                max_trade_value = 100000 * 0.05  # 5% of portfolio
                
                if trade_value > max_trade_value:
                    return RiskIntegrationResponse(
                        success=False,
                        data={
                            "trade_approved": False,
                            "reason": "Trade value exceeds risk limits",
                            "trade_value": trade_value,
                            "max_allowed": max_trade_value,
                            "current_var_95": current_var_95
                        },
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    return RiskIntegrationResponse(
                        success=True,
                        data={
                            "trade_approved": True,
                            "trade_value": trade_value,
                            "max_allowed": max_trade_value,
                            "current_var_95": current_var_95,
                            "risk_assessment": portfolio_risk
                        },
                        timestamp=datetime.now().isoformat()
                    )
            else:
                return RiskIntegrationResponse(
                    success=False,
                    error="Failed to get portfolio risk assessment",
                    timestamp=datetime.now().isoformat()
                )
                
    except Exception as e:
        logger.error(f"Trade risk validation failed: {str(e)}")
        return RiskIntegrationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

# Stress testing integration
@app.post("/api/risk/stress-test-portfolio", response_model=RiskIntegrationResponse)
async def stress_test_portfolio(request: PortfolioRiskRequest):
    """Run stress tests on portfolio"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call the enhanced risk management service for stress testing
            stress_response = await client.post(
                f"{RISK_SERVICE_URL}/api/v1/risk/stress-test",
                json={
                    "portfolio_id": request.portfolio_id,
                    "scenarios": [
                        {"name": "Market Crash", "shock_return": -0.30},
                        {"name": "Interest Rate Shock", "shock_return": -0.05},
                        {"name": "Volatility Spike", "shock_return": -0.15}
                    ]
                }
            )
            
            if stress_response.status_code == 200:
                stress_data = stress_response.json()
                return RiskIntegrationResponse(
                    success=True,
                    data=stress_data,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return RiskIntegrationResponse(
                    success=False,
                    error=f"Stress testing failed: {stress_response.status_code}",
                    timestamp=datetime.now().isoformat()
                )
                
    except Exception as e:
        logger.error(f"Portfolio stress testing failed: {str(e)}")
        return RiskIntegrationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

# Risk monitoring integration
@app.get("/api/risk/monitor/{portfolio_id}", response_model=RiskIntegrationResponse)
async def monitor_portfolio_risk(portfolio_id: str):
    """Monitor portfolio risk in real-time"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get risk metrics
            metrics_response = await client.get(
                f"{RISK_SERVICE_URL}/api/v1/risk/{portfolio_id}/metrics"
            )
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                
                # Check risk limits
                risk_limits_response = await client.post(
                    f"{RISK_SERVICE_URL}/api/v1/risk/monitor?portfolio_id={portfolio_id}",
                    json={
                        "var_95_limit": 5000,
                        "var_99_limit": 8000,
                        "volatility_limit": 0.25,
                        "max_single_asset_weight": 0.20,
                        "max_correlation_limit": 0.70
                    }
                )
                
                if risk_limits_response.status_code == 200:
                    limits_data = risk_limits_response.json()
                    
                    return RiskIntegrationResponse(
                        success=True,
                        data={
                            "portfolio_id": portfolio_id,
                            "risk_metrics": metrics_data,
                            "risk_monitoring": limits_data,
                            "monitoring_timestamp": datetime.now().isoformat()
                        },
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    return RiskIntegrationResponse(
                        success=False,
                        error="Failed to get risk limits monitoring",
                        timestamp=datetime.now().isoformat()
                    )
            else:
                return RiskIntegrationResponse(
                    success=False,
                    error="Failed to get risk metrics",
                    timestamp=datetime.now().isoformat()
                )
                
    except Exception as e:
        logger.error(f"Portfolio risk monitoring failed: {str(e)}")
        return RiskIntegrationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

# Risk integration status
@app.get("/api/risk/integration-status", response_model=RiskIntegrationResponse)
async def get_integration_status():
    """Get status of risk integration with other services"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check enhanced risk management service
            risk_health = await client.get(f"{RISK_SERVICE_URL}/health")
            risk_status = "healthy" if risk_health.status_code == 200 else "unhealthy"
            
            # Check strategy service
            strategy_health = await client.get(f"{STRATEGY_SERVICE_URL}/health")
            strategy_status = "healthy" if strategy_health.status_code == 200 else "unhealthy"
            
            # Check market data service
            market_health = await client.get(f"{MARKET_DATA_SERVICE_URL}/health")
            market_status = "healthy" if market_health.status_code == 200 else "unhealthy"
            
            return RiskIntegrationResponse(
                success=True,
                data={
                    "integration_status": "operational",
                    "services": {
                        "enhanced_risk_management": risk_status,
                        "strategy_service": strategy_status,
                        "market_data_service": market_status
                    },
                    "capabilities": [
                        "Portfolio risk assessment",
                        "Trade risk validation",
                        "Stress testing",
                        "Real-time risk monitoring",
                        "Risk limit enforcement"
                    ],
                    "last_check": datetime.now().isoformat()
                },
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.error(f"Integration status check failed: {str(e)}")
        return RiskIntegrationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
