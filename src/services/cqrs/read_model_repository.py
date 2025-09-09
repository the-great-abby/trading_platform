"""
CQRS Read Model Repository
Handles database operations for read models
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import asyncpg
from pydantic import BaseModel

from src.services.cqrs.read_models import (
    PortfolioReadModel, PositionReadModel, MarketDataReadModel,
    PerformanceReadModel, OrderReadModel, StrategyReadModel,
    AnalyticsReadModel
)

logger = logging.getLogger(__name__)


@dataclass
class QueryFilter:
    """Query filter for database operations"""
    field: str
    operator: str  # =, !=, >, <, >=, <=, IN, LIKE, etc.
    value: Any
    logical_operator: str = "AND"  # AND, OR


class ReadModelRepository:
    """Repository for read model database operations"""
    
    def __init__(self, db_conn: asyncpg.Connection):
        self.db_conn = db_conn
    
    async def create_tables(self):
        """Create read model tables if they don't exist"""
        try:
            with open('src/services/cqrs/read_model_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            await self.db_conn.execute(schema_sql)
            logger.info("Read model tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create read model tables: {e}")
            raise
    
    # Portfolio Operations
    async def get_portfolio(self, portfolio_id: str) -> Optional[PortfolioReadModel]:
        """Get portfolio by ID"""
        try:
            query = """
                SELECT * FROM portfolio_read_model 
                WHERE portfolio_id = $1
            """
            row = await self.db_conn.fetchrow(query, portfolio_id)
            
            if not row:
                return None
            
            return PortfolioReadModel(**dict(row))
        except Exception as e:
            logger.error(f"Failed to get portfolio {portfolio_id}: {e}")
            return None
    
    async def get_portfolios_by_user(self, user_id: str, account_id: Optional[str] = None) -> List[PortfolioReadModel]:
        """Get portfolios by user ID"""
        try:
            if account_id:
                query = """
                    SELECT * FROM portfolio_read_model 
                    WHERE user_id = $1 AND account_id = $2
                    ORDER BY last_updated DESC
                """
                rows = await self.db_conn.fetch(query, user_id, account_id)
            else:
                query = """
                    SELECT * FROM portfolio_read_model 
                    WHERE user_id = $1
                    ORDER BY last_updated DESC
                """
                rows = await self.db_conn.fetch(query, user_id)
            
            return [PortfolioReadModel(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get portfolios for user {user_id}: {e}")
            return []
    
    async def upsert_portfolio(self, portfolio: PortfolioReadModel) -> bool:
        """Insert or update portfolio"""
        try:
            query = """
                INSERT INTO portfolio_read_model (
                    portfolio_id, user_id, account_id, name, cash_balance,
                    total_value, total_cost, unrealized_pnl, realized_pnl,
                    total_return, total_return_percentage, position_count,
                    last_updated, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
                ON CONFLICT (portfolio_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    account_id = EXCLUDED.account_id,
                    name = EXCLUDED.name,
                    cash_balance = EXCLUDED.cash_balance,
                    total_value = EXCLUDED.total_value,
                    total_cost = EXCLUDED.total_cost,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    realized_pnl = EXCLUDED.realized_pnl,
                    total_return = EXCLUDED.total_return,
                    total_return_percentage = EXCLUDED.total_return_percentage,
                    position_count = EXCLUDED.position_count,
                    last_updated = EXCLUDED.last_updated,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            await self.db_conn.execute(
                query,
                portfolio.portfolio_id,
                portfolio.user_id,
                portfolio.account_id,
                portfolio.name,
                portfolio.cash_balance,
                portfolio.total_value,
                portfolio.total_cost,
                portfolio.unrealized_pnl,
                portfolio.realized_pnl,
                portfolio.total_return,
                portfolio.total_return_percentage,
                portfolio.position_count,
                portfolio.last_updated,
                portfolio.metadata
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert portfolio {portfolio.portfolio_id}: {e}")
            return False
    
    # Position Operations
    async def get_positions(self, portfolio_id: str, filters: Optional[List[QueryFilter]] = None) -> List[PositionReadModel]:
        """Get positions for a portfolio with optional filters"""
        try:
            query = "SELECT * FROM position_read_model WHERE portfolio_id = $1"
            params = [portfolio_id]
            
            if filters:
                for i, filter_obj in enumerate(filters, start=2):
                    if filter_obj.operator == "=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} = ${i}"
                    elif filter_obj.operator == "!=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} != ${i}"
                    elif filter_obj.operator == ">":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} > ${i}"
                    elif filter_obj.operator == "<":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} < ${i}"
                    elif filter_obj.operator == ">=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} >= ${i}"
                    elif filter_obj.operator == "<=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} <= ${i}"
                    elif filter_obj.operator == "IN":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} = ANY(${i})"
                    elif filter_obj.operator == "LIKE":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} ILIKE ${i}"
                    
                    params.append(filter_obj.value)
            
            query += " ORDER BY symbol"
            rows = await self.db_conn.fetch(query, *params)
            return [PositionReadModel(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get positions for portfolio {portfolio_id}: {e}")
            return []
    
    async def upsert_position(self, position: PositionReadModel) -> bool:
        """Insert or update position"""
        try:
            query = """
                INSERT INTO position_read_model (
                    position_id, portfolio_id, symbol, quantity, average_price,
                    current_price, market_value, cost_basis, unrealized_pnl,
                    realized_pnl, status, last_updated, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                ON CONFLICT (position_id) DO UPDATE SET
                    portfolio_id = EXCLUDED.portfolio_id,
                    symbol = EXCLUDED.symbol,
                    quantity = EXCLUDED.quantity,
                    average_price = EXCLUDED.average_price,
                    current_price = EXCLUDED.current_price,
                    market_value = EXCLUDED.market_value,
                    cost_basis = EXCLUDED.cost_basis,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    realized_pnl = EXCLUDED.realized_pnl,
                    status = EXCLUDED.status,
                    last_updated = EXCLUDED.last_updated,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            await self.db_conn.execute(
                query,
                position.position_id,
                position.portfolio_id,
                position.symbol,
                position.quantity,
                position.average_price,
                position.current_price,
                position.market_value,
                position.cost_basis,
                position.unrealized_pnl,
                position.realized_pnl,
                position.status,
                position.last_updated,
                position.metadata
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert position {position.position_id}: {e}")
            return False
    
    # Market Data Operations
    async def get_market_data(self, symbol: str) -> Optional[MarketDataReadModel]:
        """Get market data for a symbol"""
        try:
            query = "SELECT * FROM market_data_read_model WHERE symbol = $1"
            row = await self.db_conn.fetchrow(query, symbol)
            
            if not row:
                return None
            
            return MarketDataReadModel(**dict(row))
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
    
    async def get_market_data_batch(self, symbols: List[str]) -> List[MarketDataReadModel]:
        """Get market data for multiple symbols"""
        try:
            query = "SELECT * FROM market_data_read_model WHERE symbol = ANY($1)"
            rows = await self.db_conn.fetch(query, symbols)
            return [MarketDataReadModel(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get market data for symbols {symbols}: {e}")
            return []
    
    async def upsert_market_data(self, market_data: MarketDataReadModel) -> bool:
        """Insert or update market data"""
        try:
            query = """
                INSERT INTO market_data_read_model (
                    symbol, current_price, price_change, price_change_pct,
                    volume, high_52w, low_52w, market_cap, pe_ratio,
                    dividend_yield, last_updated, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    price_change = EXCLUDED.price_change,
                    price_change_pct = EXCLUDED.price_change_pct,
                    volume = EXCLUDED.volume,
                    high_52w = EXCLUDED.high_52w,
                    low_52w = EXCLUDED.low_52w,
                    market_cap = EXCLUDED.market_cap,
                    pe_ratio = EXCLUDED.pe_ratio,
                    dividend_yield = EXCLUDED.dividend_yield,
                    last_updated = EXCLUDED.last_updated,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            await self.db_conn.execute(
                query,
                market_data.symbol,
                market_data.current_price,
                market_data.price_change,
                market_data.price_change_pct,
                market_data.volume,
                market_data.high_52w,
                market_data.low_52w,
                market_data.market_cap,
                market_data.pe_ratio,
                market_data.dividend_yield,
                market_data.last_updated,
                market_data.metadata
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert market data for {market_data.symbol}: {e}")
            return False
    
    # Performance Operations
    async def get_performance(self, portfolio_id: str, strategy_id: Optional[str] = None) -> List[PerformanceReadModel]:
        """Get performance data for a portfolio or strategy"""
        try:
            if strategy_id:
                query = """
                    SELECT * FROM performance_read_model 
                    WHERE portfolio_id = $1 AND strategy_id = $2
                    ORDER BY period_end DESC
                """
                rows = await self.db_conn.fetch(query, portfolio_id, strategy_id)
            else:
                query = """
                    SELECT * FROM performance_read_model 
                    WHERE portfolio_id = $1
                    ORDER BY period_end DESC
                """
                rows = await self.db_conn.fetch(query, portfolio_id)
            
            return [PerformanceReadModel(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get performance for portfolio {portfolio_id}: {e}")
            return []
    
    async def upsert_performance(self, performance: PerformanceReadModel) -> bool:
        """Insert or update performance data"""
        try:
            query = """
                INSERT INTO performance_read_model (
                    performance_id, portfolio_id, strategy_id, period_start,
                    period_end, total_return, total_return_pct, sharpe_ratio,
                    max_drawdown, win_rate, total_trades, winning_trades,
                    losing_trades, average_win, average_loss, profit_factor,
                    last_updated, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                )
                ON CONFLICT (performance_id) DO UPDATE SET
                    portfolio_id = EXCLUDED.portfolio_id,
                    strategy_id = EXCLUDED.strategy_id,
                    period_start = EXCLUDED.period_start,
                    period_end = EXCLUDED.period_end,
                    total_return = EXCLUDED.total_return,
                    total_return_pct = EXCLUDED.total_return_pct,
                    sharpe_ratio = EXCLUDED.sharpe_ratio,
                    max_drawdown = EXCLUDED.max_drawdown,
                    win_rate = EXCLUDED.win_rate,
                    total_trades = EXCLUDED.total_trades,
                    winning_trades = EXCLUDED.winning_trades,
                    losing_trades = EXCLUDED.losing_trades,
                    average_win = EXCLUDED.average_win,
                    average_loss = EXCLUDED.average_loss,
                    profit_factor = EXCLUDED.profit_factor,
                    last_updated = EXCLUDED.last_updated,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            await self.db_conn.execute(
                query,
                performance.performance_id,
                performance.portfolio_id,
                performance.strategy_id,
                performance.period_start,
                performance.period_end,
                performance.total_return,
                performance.total_return_pct,
                performance.sharpe_ratio,
                performance.max_drawdown,
                performance.win_rate,
                performance.total_trades,
                performance.winning_trades,
                performance.losing_trades,
                performance.average_win,
                performance.average_loss,
                performance.profit_factor,
                performance.last_updated,
                performance.metadata
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert performance {performance.performance_id}: {e}")
            return False
    
    # Order Operations
    async def get_orders(self, portfolio_id: str, filters: Optional[List[QueryFilter]] = None) -> List[OrderReadModel]:
        """Get orders for a portfolio with optional filters"""
        try:
            query = "SELECT * FROM order_read_model WHERE portfolio_id = $1"
            params = [portfolio_id]
            
            if filters:
                for i, filter_obj in enumerate(filters, start=2):
                    if filter_obj.operator == "=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} = ${i}"
                    elif filter_obj.operator == "!=":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} != ${i}"
                    elif filter_obj.operator == "IN":
                        query += f" {filter_obj.logical_operator} {filter_obj.field} = ANY(${i})"
                    
                    params.append(filter_obj.value)
            
            query += " ORDER BY created_at DESC"
            rows = await self.db_conn.fetch(query, *params)
            return [OrderReadModel(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders for portfolio {portfolio_id}: {e}")
            return []
    
    async def upsert_order(self, order: OrderReadModel) -> bool:
        """Insert or update order"""
        try:
            query = """
                INSERT INTO order_read_model (
                    order_id, portfolio_id, symbol, side, quantity, order_type,
                    price, stop_price, status, filled_quantity, average_fill_price,
                    time_in_force, strategy_id, signal_id, created_at, updated_at,
                    filled_at, cancelled_at, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                )
                ON CONFLICT (order_id) DO UPDATE SET
                    portfolio_id = EXCLUDED.portfolio_id,
                    symbol = EXCLUDED.symbol,
                    side = EXCLUDED.side,
                    quantity = EXCLUDED.quantity,
                    order_type = EXCLUDED.order_type,
                    price = EXCLUDED.price,
                    stop_price = EXCLUDED.stop_price,
                    status = EXCLUDED.status,
                    filled_quantity = EXCLUDED.filled_quantity,
                    average_fill_price = EXCLUDED.average_fill_price,
                    time_in_force = EXCLUDED.time_in_force,
                    strategy_id = EXCLUDED.strategy_id,
                    signal_id = EXCLUDED.signal_id,
                    updated_at = EXCLUDED.updated_at,
                    filled_at = EXCLUDED.filled_at,
                    cancelled_at = EXCLUDED.cancelled_at,
                    metadata = EXCLUDED.metadata
            """
            
            await self.db_conn.execute(
                query,
                order.order_id,
                order.portfolio_id,
                order.symbol,
                order.side,
                order.quantity,
                order.order_type,
                order.price,
                order.stop_price,
                order.status,
                order.filled_quantity,
                order.average_fill_price,
                order.time_in_force,
                order.strategy_id,
                order.signal_id,
                order.created_at,
                order.updated_at,
                order.filled_at,
                order.cancelled_at,
                order.metadata
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert order {order.order_id}: {e}")
            return False
