"""
Portfolio Service - Internal microservice for portfolio management operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime
import requests
import sys

# Add the src directory to the path to import our services
sys.path.append('/app')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Portfolio Service", version="1.0.0")

class Position(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    total_pnl: float
    total_pnl_percentage: float
    daily_pnl: float
    max_drawdown: float
    num_positions: int
    positions: List[Position]

def get_current_price_from_market_data(symbol: str) -> Optional[float]:
    """Get current price from market data service"""
    try:
        market_data_url = os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data-service:8002")
        response = requests.get(f"{market_data_url}/market-data/current/{symbol}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("price")
        else:
            logger.warning(f"Failed to get price for {symbol}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "portfolio-service"}

@app.get("/status")
async def get_status():
    """Get portfolio service status"""
    return {
        "service": "portfolio-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get portfolio summary with real market data"""
    try:
        # Mock portfolio positions (in real system, this would come from database)
        mock_positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_price": 145.0
            },
            {
                "symbol": "GOOGL",
                "quantity": 50,
                "avg_price": 2800.0
            },
            {
                "symbol": "TSLA",
                "quantity": 200,
                "avg_price": 200.0
            }
        ]
        
        positions = []
        total_market_value = 0.0
        total_cost_basis = 0.0
        
        for pos in mock_positions:
            symbol = pos["symbol"]
            quantity = pos["quantity"]
            avg_price = pos["avg_price"]
            
            # Get real current price from market data service
            current_price = get_current_price_from_market_data(symbol)
            
            if current_price is None:
                # Fallback to mock price if market data service is unavailable
                current_price = avg_price * 1.05  # 5% gain as fallback
                logger.warning(f"Using fallback price for {symbol}")
            
            market_value = quantity * current_price
            cost_basis = quantity * avg_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_percent = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent
            )
            
            positions.append(position)
            total_market_value += market_value
            total_cost_basis += cost_basis
        
        # Mock cash balance
        cash = 50000.0
        total_value = total_market_value + cash
        total_pnl = total_market_value - total_cost_basis
        total_pnl_percentage = (total_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else 0
        
        logger.info(f"Portfolio summary calculated. Total value: ${total_value:,.2f}")
        
        return PortfolioSummary(
            total_value=total_value,
            cash=cash,
            total_pnl=total_pnl,
            total_pnl_percentage=total_pnl_percentage,
            daily_pnl=total_pnl * 0.1,  # Mock daily PnL
            max_drawdown=0.08,  # Mock max drawdown
            num_positions=len(positions),
            positions=positions
        )
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")

@app.get("/portfolio/positions")
async def get_positions():
    """Get all positions with real market data"""
    try:
        # Mock positions data (in real system, this would come from database)
        mock_positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_price": 145.0,
                "purchase_date": "2024-01-01"
            },
            {
                "symbol": "GOOGL",
                "quantity": 50,
                "avg_price": 2800.0,
                "purchase_date": "2024-01-15"
            }
        ]
        
        positions = []
        for pos in mock_positions:
            symbol = pos["symbol"]
            
            # Get real current price
            current_price = get_current_price_from_market_data(symbol)
            if current_price is None:
                current_price = pos["avg_price"] * 1.05  # Fallback
            
            market_value = pos["quantity"] * current_price
            cost_basis = pos["quantity"] * pos["avg_price"]
            unrealized_pnl = market_value - cost_basis
            
            position_data = {
                "symbol": symbol,
                "quantity": pos["quantity"],
                "avg_price": pos["avg_price"],
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0,
                "purchase_date": pos["purchase_date"],
                "last_updated": datetime.now().isoformat()
            }
            positions.append(position_data)
        
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")

@app.get("/portfolio/positions/{symbol}")
async def get_position(symbol: str):
    """Get specific position with real market data"""
    try:
        # Mock position data (in real system, this would come from database)
        mock_position = {
            "symbol": symbol,
            "quantity": 100,
            "avg_price": 145.0,
            "purchase_date": "2024-01-01",
            "trade_history": [
                {
                    "date": "2024-01-01",
                    "action": "buy",
                    "quantity": 50,
                    "price": 140.0
                },
                {
                    "date": "2024-01-15",
                    "action": "buy",
                    "quantity": 50,
                    "price": 150.0
                }
            ]
        }
        
        # Get real current price
        current_price = get_current_price_from_market_data(symbol)
        if current_price is None:
            current_price = mock_position["avg_price"] * 1.05  # Fallback
        
        market_value = mock_position["quantity"] * current_price
        cost_basis = mock_position["quantity"] * mock_position["avg_price"]
        unrealized_pnl = market_value - cost_basis
        
        position = {
            "symbol": symbol,
            "quantity": mock_position["quantity"],
            "avg_price": mock_position["avg_price"],
            "current_price": current_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0,
            "purchase_date": mock_position["purchase_date"],
            "last_updated": datetime.now().isoformat(),
            "trade_history": mock_position["trade_history"]
        }
        
        return position
    except Exception as e:
        logger.error(f"Failed to get position for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")

@app.get("/portfolio/performance")
async def get_performance(period: str = "1m"):
    """Get portfolio performance metrics"""
    try:
        # Mock performance data (in real system, this would be calculated from historical data)
        performance = {
            "period": period,
            "total_return": 0.125,
            "annualized_return": 0.15,
            "volatility": 0.16,
            "sharpe_ratio": 1.35,
            "max_drawdown": 0.08,
            "win_rate": 0.68,
            "profit_factor": 1.9,
            "total_trades": 52,
            "avg_trade_duration": "2.5 days",
            "best_trade": 0.08,
            "worst_trade": -0.04,
            "daily_returns": [
                {"date": "2024-01-01", "return": 0.02},
                {"date": "2024-01-02", "return": -0.01},
                {"date": "2024-01-03", "return": 0.015},
                {"date": "2024-01-04", "return": 0.008},
                {"date": "2024-01-05", "return": -0.005}
            ],
            "cumulative_returns": [
                {"date": "2024-01-01", "cumulative": 0.02},
                {"date": "2024-01-02", "cumulative": 0.0098},
                {"date": "2024-01-03", "cumulative": 0.025},
                {"date": "2024-01-04", "cumulative": 0.033},
                {"date": "2024-01-05", "cumulative": 0.028}
            ]
        }
        
        return performance
    except Exception as e:
        logger.error(f"Failed to get performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

@app.get("/portfolio/cash")
async def get_cash_balance():
    """Get cash balance"""
    try:
        return {
            "cash_balance": 50000.0,
            "available_cash": 45000.0,  # After reserves
            "reserved_cash": 5000.0,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cash balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cash balance: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
