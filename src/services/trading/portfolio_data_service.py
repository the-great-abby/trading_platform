"""
Portfolio Data Service
Provides mock portfolio data for testing and development
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PortfolioDataService:
    """Service for managing portfolio data"""
    
    def __init__(self):
        self.mock_portfolios = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock portfolio data"""
        # Mock portfolio for test-user
        self.mock_portfolios["test-user"] = {
            "user_id": "test-user",
            "account_id": "test-account",
            "total_value": Decimal("100000.00"),
            "cash_balance": Decimal("50000.00"),
            "invested_value": Decimal("50000.00"),
            "total_pnl": Decimal("5000.00"),
            "total_pnl_percent": Decimal("5.0"),
            "positions": [
                {
                    "position_id": "pos_001",
                    "symbol": "AAPL",
                    "quantity": Decimal("100"),
                    "avg_price": Decimal("150.00"),
                    "current_price": Decimal("155.00"),
                    "market_value": Decimal("15500.00"),
                    "unrealized_pnl": Decimal("500.00"),
                    "unrealized_pnl_percent": Decimal("3.33"),
                    "status": "open",
                    "opened_at": datetime.now() - timedelta(days=30),
                    "portfolio_id": "portfolio_001"
                },
                {
                    "position_id": "pos_002",
                    "symbol": "TSLA",
                    "quantity": Decimal("50"),
                    "avg_price": Decimal("200.00"),
                    "current_price": Decimal("250.00"),
                    "market_value": Decimal("12500.00"),
                    "unrealized_pnl": Decimal("2500.00"),
                    "unrealized_pnl_percent": Decimal("25.0"),
                    "status": "open",
                    "opened_at": datetime.now() - timedelta(days=15),
                    "portfolio_id": "portfolio_001"
                },
                {
                    "position_id": "pos_003",
                    "symbol": "MSFT",
                    "quantity": Decimal("75"),
                    "avg_price": Decimal("300.00"),
                    "current_price": Decimal("295.00"),
                    "market_value": Decimal("22125.00"),
                    "unrealized_pnl": Decimal("-375.00"),
                    "unrealized_pnl_percent": Decimal("-1.67"),
                    "status": "open",
                    "opened_at": datetime.now() - timedelta(days=7),
                    "portfolio_id": "portfolio_001"
                }
            ],
            "recent_orders": [
                {
                    "order_id": "ORD_000001_20250907_160615",
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": Decimal("10"),
                    "order_type": "market",
                    "status": "filled",
                    "execution_price": Decimal("155.00"),
                    "created_at": datetime.now() - timedelta(minutes=30)
                },
                {
                    "order_id": "ORD_000002_20250907_160631",
                    "symbol": "TSLA",
                    "side": "sell",
                    "quantity": Decimal("5"),
                    "order_type": "limit",
                    "price": Decimal("250.00"),
                    "status": "filled",
                    "execution_price": Decimal("250.00"),
                    "created_at": datetime.now() - timedelta(minutes=25)
                }
            ],
            "performance_metrics": {
                "daily_pnl": Decimal("150.00"),
                "weekly_pnl": Decimal("1200.00"),
                "monthly_pnl": Decimal("5000.00"),
                "ytd_pnl": Decimal("15000.00"),
                "max_drawdown": Decimal("-2000.00"),
                "sharpe_ratio": Decimal("1.25"),
                "win_rate": Decimal("65.0")
            },
            "risk_metrics": {
                "portfolio_beta": Decimal("1.15"),
                "volatility": Decimal("18.5"),
                "var_95": Decimal("-5000.00"),
                "max_position_size": Decimal("15000.00"),
                "concentration_risk": Decimal("25.0")
            },
            "last_updated": datetime.now()
        }
        
        # Mock portfolio for demo-user
        self.mock_portfolios["demo-user"] = {
            "user_id": "demo-user",
            "account_id": "demo-account",
            "total_value": Decimal("250000.00"),
            "cash_balance": Decimal("100000.00"),
            "invested_value": Decimal("150000.00"),
            "total_pnl": Decimal("15000.00"),
            "total_pnl_percent": Decimal("6.0"),
            "positions": [
                {
                    "position_id": "pos_004",
                    "symbol": "GOOGL",
                    "quantity": Decimal("25"),
                    "avg_price": Decimal("2800.00"),
                    "current_price": Decimal("2900.00"),
                    "market_value": Decimal("72500.00"),
                    "unrealized_pnl": Decimal("2500.00"),
                    "unrealized_pnl_percent": Decimal("3.57"),
                    "status": "open",
                    "opened_at": datetime.now() - timedelta(days=45),
                    "portfolio_id": "portfolio_002"
                },
                {
                    "position_id": "pos_005",
                    "symbol": "NVDA",
                    "quantity": Decimal("100"),
                    "avg_price": Decimal("400.00"),
                    "current_price": Decimal("450.00"),
                    "market_value": Decimal("45000.00"),
                    "unrealized_pnl": Decimal("5000.00"),
                    "unrealized_pnl_percent": Decimal("12.5"),
                    "status": "open",
                    "opened_at": datetime.now() - timedelta(days=20),
                    "portfolio_id": "portfolio_002"
                }
            ],
            "recent_orders": [],
            "performance_metrics": {
                "daily_pnl": Decimal("300.00"),
                "weekly_pnl": Decimal("2500.00"),
                "monthly_pnl": Decimal("15000.00"),
                "ytd_pnl": Decimal("45000.00"),
                "max_drawdown": Decimal("-5000.00"),
                "sharpe_ratio": Decimal("1.45"),
                "win_rate": Decimal("72.0")
            },
            "risk_metrics": {
                "portfolio_beta": Decimal("1.25"),
                "volatility": Decimal("22.0"),
                "var_95": Decimal("-12000.00"),
                "max_position_size": Decimal("75000.00"),
                "concentration_risk": Decimal("30.0")
            },
            "last_updated": datetime.now()
        }
        
        logger.info("Mock portfolio data initialized")
    
    def get_portfolio(self, user_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio data for a user"""
        portfolio = self.mock_portfolios.get(user_id)
        if portfolio and portfolio["account_id"] == account_id:
            return portfolio.copy()  # Return a copy to avoid mutations
        return None
    
    def get_positions(self, user_id: str, account_id: str, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions for a user"""
        portfolio = self.get_portfolio(user_id, account_id)
        if not portfolio:
            return []
        
        positions = portfolio["positions"]
        if symbol:
            positions = [pos for pos in positions if pos["symbol"] == symbol]
        
        return positions
    
    def update_portfolio_value(self, user_id: str, account_id: str, new_value: Decimal):
        """Update portfolio total value"""
        portfolio = self.mock_portfolios.get(user_id)
        if portfolio and portfolio["account_id"] == account_id:
            old_value = portfolio["total_value"]
            portfolio["total_value"] = new_value
            portfolio["total_pnl"] = new_value - (old_value - portfolio["total_pnl"])
            portfolio["total_pnl_percent"] = (portfolio["total_pnl"] / (new_value - portfolio["total_pnl"])) * 100
            portfolio["last_updated"] = datetime.now()
            logger.info(f"Updated portfolio value for {user_id}: {old_value} -> {new_value}")
    
    def add_position(self, user_id: str, account_id: str, position: Dict[str, Any]):
        """Add a new position to the portfolio"""
        portfolio = self.mock_portfolios.get(user_id)
        if portfolio and portfolio["account_id"] == account_id:
            portfolio["positions"].append(position)
            # Recalculate portfolio values
            self._recalculate_portfolio_values(portfolio)
            portfolio["last_updated"] = datetime.now()
            logger.info(f"Added position {position['symbol']} to portfolio for {user_id}")
    
    def update_position(self, user_id: str, account_id: str, position_id: str, updates: Dict[str, Any]):
        """Update an existing position"""
        portfolio = self.mock_portfolios.get(user_id)
        if portfolio and portfolio["account_id"] == account_id:
            for i, pos in enumerate(portfolio["positions"]):
                if pos["position_id"] == position_id:
                    portfolio["positions"][i].update(updates)
                    # Recalculate portfolio values
                    self._recalculate_portfolio_values(portfolio)
                    portfolio["last_updated"] = datetime.now()
                    logger.info(f"Updated position {position_id} for {user_id}")
                    break
    
    def _recalculate_portfolio_values(self, portfolio: Dict[str, Any]):
        """Recalculate portfolio values based on positions"""
        total_invested = Decimal("0")
        total_market_value = Decimal("0")
        total_unrealized_pnl = Decimal("0")
        
        for position in portfolio["positions"]:
            if position["status"] == "open":
                total_invested += position["quantity"] * position["avg_price"]
                total_market_value += position["market_value"]
                total_unrealized_pnl += position["unrealized_pnl"]
        
        portfolio["invested_value"] = total_invested
        portfolio["total_value"] = portfolio["cash_balance"] + total_market_value
        portfolio["total_pnl"] = total_unrealized_pnl
        if total_invested > 0:
            portfolio["total_pnl_percent"] = (total_unrealized_pnl / total_invested) * 100
        else:
            portfolio["total_pnl_percent"] = Decimal("0")
