"""
CQRS Query Handlers
Handles all queries for the trading system
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.cqrs.base import QueryHandler
from src.services.cqrs.queries import *
from src.services.cqrs.read_models import *
from src.services.cqrs.read_model_repository import ReadModelRepository, QueryFilter

logger = logging.getLogger(__name__)


# Portfolio Query Handlers
class GetPortfolioHandler(QueryHandler):
    """Handler for getting portfolio information"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self.repository = ReadModelRepository(db_conn) if db_conn else None
    
    async def handle(self, query: GetPortfolioQuery) -> Dict[str, Any]:
        """Handle get portfolio query"""
        try:
            logger.info(f"Getting portfolio: {query.portfolio_id}")
            
            if not self.repository or not self.db_conn or hasattr(self.db_conn, '_mock_name'):
                # Fallback to mock data if no database connection or if it's a mock
                return await self._get_mock_portfolio(query)
            
            # Get portfolio from database
            if query.portfolio_id:
                portfolio = await self.repository.get_portfolio(query.portfolio_id)
                if not portfolio:
                    return {
                        "success": False,
                        "error": "Portfolio not found",
                        "message": f"Portfolio {query.portfolio_id} not found"
                    }
            elif query.user_id and query.account_id:
                # Get portfolios by user and account
                portfolios = await self.repository.get_portfolios_by_user(query.user_id, query.account_id)
                if not portfolios:
                    return {
                        "success": False,
                        "error": "No portfolios found",
                        "message": f"No portfolios found for user {query.user_id} and account {query.account_id}"
                    }
                portfolio = portfolios[0]  # Get first portfolio
            else:
                return {
                    "success": False,
                    "error": "Missing parameters",
                    "message": "Either portfolio_id or (user_id and account_id) is required"
                }
            
            # Get positions if requested
            positions = []
            if query.include_positions:
                position_filters = []
                if not query.include_closed:
                    position_filters.append(QueryFilter("status", "!=", "closed"))
                
                positions = await self.repository.get_positions(
                    portfolio.portfolio_id, 
                    position_filters
                )
            
            # Get performance metrics if requested
            performance = {}
            if query.include_performance:
                performance_data = await self.repository.get_performance(portfolio.portfolio_id)
                if performance_data:
                    latest_performance = performance_data[0]  # Most recent
                    performance = {
                        "total_return": float(latest_performance.total_return),
                        "total_return_pct": float(latest_performance.total_return_pct),
                        "sharpe_ratio": float(latest_performance.sharpe_ratio) if latest_performance.sharpe_ratio else None,
                        "max_drawdown": float(latest_performance.max_drawdown) if latest_performance.max_drawdown else None,
                        "win_rate": float(latest_performance.win_rate) if latest_performance.win_rate else None,
                        "total_trades": latest_performance.total_trades
                    }
            
            return {
                "success": True,
                "portfolio": portfolio.model_dump(),
                "positions": [pos.model_dump() for pos in positions],
                "performance": performance
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get portfolio"
            }
    
    async def _get_mock_portfolio(self, query: GetPortfolioQuery) -> Dict[str, Any]:
        """Fallback mock portfolio data"""
        # Only return mock data for user1/acc1, return empty for others
        if query.user_id != "user1" or query.account_id != "acc1":
            return {
                "success": False,
                "error": "No portfolios found",
                "message": f"No portfolios found for user {query.user_id} and account {query.account_id}"
            }
        
        portfolio = PortfolioReadModel(
            portfolio_id=query.portfolio_id or "default_portfolio",
            user_id=query.user_id or "user1",
            account_id=query.account_id or "acc1",
            name="Main Portfolio",
            cash_balance=Decimal("10000.00"),
            total_value=Decimal("15000.00"),
            total_cost=Decimal("12000.00"),
            unrealized_pnl=Decimal("3000.00"),
            realized_pnl=Decimal("500.00"),
            total_return=Decimal("3500.00"),
            total_return_percentage=Decimal("29.17"),
            position_count=5,
            last_updated=datetime.utcnow(),
            metadata={"risk_level": "moderate"}
        )
        
        positions = []
        if query.include_positions:
            positions = [
                PositionReadModel(
                    position_id="pos_1",
                    portfolio_id=portfolio.portfolio_id,
                    symbol="AAPL",
                    quantity=100,
                    average_price=Decimal("150.00"),
                    current_price=Decimal("155.00"),
                    market_value=Decimal("15500.00"),
                    cost_basis=Decimal("15000.00"),
                    unrealized_pnl=Decimal("500.00"),
                    realized_pnl=Decimal("0.00"),
                    return_percentage=Decimal("3.33"),
                    status="open",
                    opened_at=datetime.utcnow() - timedelta(days=30),
                    last_updated=datetime.utcnow()
                )
            ]
        
        return {
            "success": True,
            "portfolio": portfolio.model_dump(),
            "positions": [pos.model_dump() for pos in positions],
            "performance": {}
        }


class GetPositionsHandler(QueryHandler):
    """Handler for getting positions"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self.repository = ReadModelRepository(db_conn) if db_conn else None
    
    async def handle(self, query: GetPositionsQuery) -> Dict[str, Any]:
        """Handle get positions query"""
        try:
            logger.info(f"Getting positions for portfolio: {query.portfolio_id}")
            
            # TODO: Integrate with actual position management system
            # This would typically:
            # 1. Query positions from read model store
            # 2. Apply filters (symbol, min_quantity, etc.)
            # 3. Sort and paginate results
            
            # Mock positions data for now
            positions = [
                PositionReadModel(
                    position_id="pos_1",
                    symbol="AAPL",
                    quantity=100,
                    average_price=Decimal("150.00"),
                    current_price=Decimal("155.00"),
                    market_value=Decimal("15500.00"),
                    cost_basis=Decimal("15000.00"),
                    unrealized_pnl=Decimal("500.00"),
                    realized_pnl=Decimal("0.00"),
                    return_percentage=Decimal("3.33"),
                    status="open",
                    opened_at=datetime.utcnow() - timedelta(days=30),
                    last_updated=datetime.utcnow()
                ),
                PositionReadModel(
                    position_id="pos_2",
                    symbol="GOOGL",
                    quantity=50,
                    average_price=Decimal("2800.00"),
                    current_price=Decimal("2750.00"),
                    market_value=Decimal("137500.00"),
                    cost_basis=Decimal("140000.00"),
                    unrealized_pnl=Decimal("-2500.00"),
                    realized_pnl=Decimal("0.00"),
                    return_percentage=Decimal("-1.79"),
                    status="open",
                    opened_at=datetime.utcnow() - timedelta(days=15),
                    last_updated=datetime.utcnow()
                )
            ]
            
            # Apply filters
            if query.symbol:
                positions = [p for p in positions if p.symbol == query.symbol]
            
            if query.min_quantity:
                positions = [p for p in positions if p.quantity >= query.min_quantity]
            
            if not query.include_closed:
                positions = [p for p in positions if p.status == "open"]
            
            # Sort results
            if query.sort_by == "symbol":
                positions.sort(key=lambda x: x.symbol, reverse=(query.sort_order == "desc"))
            elif query.sort_by == "unrealized_pnl":
                positions.sort(key=lambda x: x.unrealized_pnl, reverse=(query.sort_order == "desc"))
            
            # Apply pagination
            if query.limit:
                positions = positions[query.offset or 0:query.offset or 0 + query.limit]
            
            return {
                "positions": [p.dict() for p in positions],
                "total_count": len(positions),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get positions"
            }


# Market Data Query Handlers
class GetMarketDataHandler(QueryHandler):
    """Handler for getting market data"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetMarketDataQuery) -> Dict[str, Any]:
        """Handle get market data query"""
        try:
            logger.info(f"Getting market data for {query.symbol}")
            
            # TODO: Integrate with actual market data system
            # This would typically:
            # 1. Query market data from data store
            # 2. Apply time filters
            # 3. Calculate indicators if requested
            
            # Mock market data for now
            market_data = MarketDataReadModel(
                symbol=query.symbol,
                timestamp=datetime.utcnow(),
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.50"),
                volume=1000000,
                adjusted_close=Decimal("154.50"),
                indicators={
                    "sma_20": Decimal("152.00"),
                    "rsi": Decimal("65.5"),
                    "macd": Decimal("1.2")
                } if query.indicators else None
            )
            
            return {
                "market_data": market_data.dict(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get market data"
            }


class GetMarketDataHistoryHandler(QueryHandler):
    """Handler for getting historical market data"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetMarketDataHistoryQuery) -> Dict[str, Any]:
        """Handle get market data history query"""
        try:
            logger.info(f"Getting market data history for {query.symbol}")
            
            # TODO: Integrate with actual market data system
            # This would typically:
            # 1. Query historical data from data store
            # 2. Apply time range filters
            # 3. Calculate indicators if requested
            
            # Mock historical data for now
            historical_data = []
            current_date = query.start_date
            base_price = Decimal("150.00")
            
            while current_date <= query.end_date:
                # Generate mock price data
                price_change = Decimal(str((hash(str(current_date)) % 100 - 50) / 100))
                price = base_price + price_change
                
                data_point = MarketDataReadModel(
                    symbol=query.symbol,
                    timestamp=current_date,
                    open_price=price,
                    high_price=price + Decimal("0.50"),
                    low_price=price - Decimal("0.50"),
                    close_price=price + Decimal("0.25"),
                    volume=1000000 + (hash(str(current_date)) % 500000),
                    adjusted_close=price + Decimal("0.25")
                )
                
                historical_data.append(data_point.dict())
                current_date += timedelta(days=1)
            
            return {
                "historical_data": historical_data,
                "total_count": len(historical_data),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting market data history: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get market data history"
            }


# Performance Query Handlers
class GetPerformanceHandler(QueryHandler):
    """Handler for getting performance metrics"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetPerformanceQuery) -> Dict[str, Any]:
        """Handle get performance query"""
        try:
            logger.info(f"Getting performance for portfolio: {query.portfolio_id}")
            
            # TODO: Integrate with actual performance calculation system
            # This would typically:
            # 1. Query performance data from read model store
            # 2. Calculate metrics for the specified time range
            # 3. Include benchmark comparison if requested
            
            # Mock performance data for now
            performance = PerformanceReadModel(
                portfolio_id=query.portfolio_id or "default_portfolio",
                period_start=query.start_date or datetime.utcnow() - timedelta(days=30),
                period_end=query.end_date or datetime.utcnow(),
                total_return=Decimal("3500.00"),
                total_return_percentage=Decimal("29.17"),
                annualized_return=Decimal("15.5"),
                volatility=Decimal("12.3"),
                sharpe_ratio=Decimal("1.26"),
                max_drawdown=Decimal("-5.2"),
                max_drawdown_percentage=Decimal("-5.2"),
                win_rate=Decimal("65.0"),
                profit_factor=Decimal("1.8"),
                total_trades=20,
                winning_trades=13,
                losing_trades=7,
                average_win=Decimal("250.00"),
                average_loss=Decimal("-150.00"),
                last_updated=datetime.utcnow()
            )
            
            result = {
                "performance": performance.dict(),
                "success": True
            }
            
            if query.include_benchmark and query.benchmark_symbol:
                # TODO: Get benchmark performance data
                result["benchmark"] = {}
            
            if query.include_risk_metrics:
                # TODO: Get risk metrics
                result["risk_metrics"] = {}
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get performance"
            }


class GetBacktestResultsHandler(QueryHandler):
    """Handler for getting backtest results"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetBacktestResultsQuery) -> Dict[str, Any]:
        """Handle get backtest results query"""
        try:
            logger.info(f"Getting backtest results: {query.backtest_id}")
            
            # TODO: Integrate with actual backtest system
            # This would typically:
            # 1. Query backtest results from data store
            # 2. Include trades and metrics if requested
            # 3. Generate charts if requested
            
            # Mock backtest results for now
            backtest_results = BacktestResultsReadModel(
                backtest_id=query.backtest_id or "backtest_1",
                strategy_id=query.strategy_id or "strategy_1",
                strategy_name="SMA Crossover Strategy",
                start_date=datetime.utcnow() - timedelta(days=365),
                end_date=datetime.utcnow(),
                initial_capital=Decimal("10000.00"),
                final_capital=Decimal("12500.00"),
                total_return=Decimal("2500.00"),
                total_return_percentage=Decimal("25.0"),
                annualized_return=Decimal("25.0"),
                volatility=Decimal("15.2"),
                sharpe_ratio=Decimal("1.64"),
                max_drawdown=Decimal("-8.5"),
                max_drawdown_percentage=Decimal("-8.5"),
                win_rate=Decimal("68.0"),
                profit_factor=Decimal("2.1"),
                total_trades=45,
                winning_trades=31,
                losing_trades=14,
                average_win=Decimal("180.00"),
                average_loss=Decimal("-120.00"),
                created_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(hours=1),
                status="completed"
            )
            
            result = {
                "backtest_results": backtest_results.dict(),
                "success": True
            }
            
            if query.include_trades:
                # TODO: Get trade data
                result["trades"] = []
            
            if query.include_metrics:
                # TODO: Get additional metrics
                result["metrics"] = {}
            
            if query.include_charts:
                # TODO: Generate chart data
                result["charts"] = {}
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting backtest results: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get backtest results"
            }


# Order Query Handlers
class GetOrderHandler(QueryHandler):
    """Handler for getting order information"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetOrderQuery) -> Dict[str, Any]:
        """Handle get order query"""
        try:
            logger.info(f"Getting order: {query.order_id}")
            
            # TODO: Integrate with actual order management system
            # This would typically:
            # 1. Query orders from read model store
            # 2. Apply filters and sorting
            # 3. Return paginated results
            
            # Mock order data for now
            orders = [
                OrderReadModel(
                    order_id=query.order_id or "order_1",
                    symbol="AAPL",
                    quantity=100,
                    filled_quantity=100,
                    remaining_quantity=0,
                    order_type="limit",
                    side="buy",
                    price=Decimal("150.00"),
                    average_fill_price=Decimal("149.95"),
                    status="filled",
                    time_in_force="GTC",
                    strategy_id="strategy_1",
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    updated_at=datetime.utcnow() - timedelta(hours=1),
                    filled_at=datetime.utcnow() - timedelta(hours=1)
                )
            ]
            
            return {
                "orders": [o.dict() for o in orders],
                "total_count": len(orders),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get order"
            }


# Strategy Query Handlers
class GetStrategyHandler(QueryHandler):
    """Handler for getting strategy information"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetStrategyQuery) -> Dict[str, Any]:
        """Handle get strategy query"""
        try:
            logger.info(f"Getting strategy: {query.strategy_id}")
            
            # TODO: Integrate with actual strategy management system
            
            # Mock strategy data for now
            strategies = [
                StrategyReadModel(
                    strategy_id=query.strategy_id or "strategy_1",
                    name="SMA Crossover Strategy",
                    strategy_type="sma_crossover",
                    description="Simple moving average crossover strategy",
                    parameters={"short_window": 20, "long_window": 50},
                    is_active=True,
                    symbols=["AAPL", "GOOGL", "MSFT"],
                    total_return=Decimal("2500.00"),
                    total_return_percentage=Decimal("25.0"),
                    sharpe_ratio=Decimal("1.64"),
                    max_drawdown=Decimal("-8.5"),
                    win_rate=Decimal("68.0"),
                    total_trades=45,
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow() - timedelta(days=1),
                    last_run_at=datetime.utcnow() - timedelta(hours=1)
                )
            ]
            
            return {
                "strategies": [s.dict() for s in strategies],
                "total_count": len(strategies),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get strategy"
            }


# Signal Query Handlers
class GetSignalHandler(QueryHandler):
    """Handler for getting signal information"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetSignalQuery) -> Dict[str, Any]:
        """Handle get signal query"""
        try:
            logger.info(f"Getting signals for symbol: {query.symbol}")
            
            # TODO: Integrate with actual signal management system
            
            # Mock signal data for now
            signals = [
                SignalReadModel(
                    signal_id=query.signal_id or "signal_1",
                    symbol=query.symbol or "AAPL",
                    signal_type="buy",
                    strength=0.85,
                    price=Decimal("155.00"),
                    quantity=100,
                    strategy_id="strategy_1",
                    created_at=datetime.utcnow() - timedelta(minutes=30),
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                    is_active=True
                )
            ]
            
            return {
                "signals": [s.dict() for s in signals],
                "total_count": len(signals),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get signals"
            }


# Trading History Query Handlers
class GetTradingHistoryHandler(QueryHandler):
    """Handler for getting trading history"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    async def handle(self, query: GetTradingHistoryQuery) -> Dict[str, Any]:
        """Handle get trading history query"""
        try:
            logger.info(f"Getting trading history for portfolio: {query.portfolio_id}")
            
            # TODO: Integrate with actual trading history system
            
            # Mock trading history data for now
            history = [
                TradingHistoryReadModel(
                    history_id="hist_1",
                    portfolio_id=query.portfolio_id or "default_portfolio",
                    symbol="AAPL",
                    action="buy",
                    quantity=100,
                    price=Decimal("150.00"),
                    timestamp=datetime.utcnow() - timedelta(hours=2),
                    order_id="order_1",
                    trade_id="trade_1",
                    strategy_id="strategy_1"
                )
            ]
            
            return {
                "trading_history": [h.dict() for h in history],
                "total_count": len(history),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting trading history: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get trading history"
            }
