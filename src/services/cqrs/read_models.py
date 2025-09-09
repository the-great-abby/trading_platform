"""
CQRS Read Models
Optimized read models for efficient querying
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(str, Enum):
    """Position status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


class PerformanceMetric(BaseModel):
    """Performance metric model"""
    metric_name: str
    value: Decimal
    unit: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class RiskMetric(BaseModel):
    """Risk metric model"""
    metric_name: str
    value: Decimal
    limit: Optional[Decimal] = None
    status: str  # within_limits, warning, critical
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# Portfolio Read Models
class PortfolioReadModel(BaseModel):
    """Portfolio read model for optimized queries"""
    portfolio_id: str
    user_id: str
    account_id: str
    name: str
    cash_balance: Decimal
    total_value: Decimal
    total_cost: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    position_count: int
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PositionReadModel(BaseModel):
    """Position read model for optimized queries"""
    portfolio_id: str
    symbol: str
    quantity: int
    average_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    return_percentage: Decimal
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Market Data Read Models
class MarketDataReadModel(BaseModel):
    """Market data read model for optimized queries"""
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    adjusted_close: Optional[Decimal] = None
    indicators: Optional[Dict[str, Decimal]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MarketDataSummaryReadModel(BaseModel):
    """Market data summary read model"""
    symbol: str
    current_price: Decimal
    price_change: Decimal
    price_change_percentage: Decimal
    volume: int
    high_52_week: Decimal
    low_52_week: Decimal
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Performance Read Models
class PerformanceReadModel(BaseModel):
    """Performance read model for optimized queries"""
    portfolio_id: str
    period_start: datetime
    period_end: datetime
    total_return: Decimal
    total_return_percentage: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    max_drawdown_percentage: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: Decimal
    average_loss: Decimal
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class BacktestResultsReadModel(BaseModel):
    """Backtest results read model"""
    backtest_id: str
    strategy_id: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_capital: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    max_drawdown_percentage: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: Decimal
    average_loss: Decimal
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Order Read Models
class OrderReadModel(BaseModel):
    """Order read model for optimized queries"""
    order_id: str
    symbol: str
    quantity: int
    filled_quantity: int
    remaining_quantity: int
    order_type: str
    side: str
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    average_fill_price: Optional[Decimal] = None
    status: OrderStatus
    time_in_force: str
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class TradeReadModel(BaseModel):
    """Trade read model for optimized queries"""
    trade_id: str
    order_id: str
    symbol: str
    quantity: int
    price: Decimal
    side: str
    executed_at: datetime
    commission: Optional[Decimal] = None
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Strategy Read Models
class StrategyReadModel(BaseModel):
    """Strategy read model for optimized queries"""
    strategy_id: str
    name: str
    strategy_type: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    is_active: bool
    symbols: List[str]
    total_return: Optional[Decimal] = None
    total_return_percentage: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    win_rate: Optional[Decimal] = None
    total_trades: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Signal Read Models
class SignalReadModel(BaseModel):
    """Signal read model for optimized queries"""
    signal_id: str
    symbol: str
    signal_type: str
    strength: float
    price: Decimal
    quantity: Optional[int] = None
    strategy_id: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Trading History Read Models
class TradingHistoryReadModel(BaseModel):
    """Trading history read model"""
    history_id: str
    portfolio_id: str
    symbol: str
    action: str  # buy, sell, hold
    quantity: int
    price: Decimal
    timestamp: datetime
    order_id: Optional[str] = None
    trade_id: Optional[str] = None
    signal_id: Optional[str] = None
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Risk Management Read Models
class RiskLimitsReadModel(BaseModel):
    """Risk limits read model"""
    portfolio_id: str
    max_position_size: Decimal
    max_daily_loss: Decimal
    max_drawdown: Decimal
    stop_loss_percentage: float
    take_profit_percentage: float
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class RiskAlertReadModel(BaseModel):
    """Risk alert read model"""
    alert_id: str
    portfolio_id: str
    alert_type: str
    severity: str
    current_value: Decimal
    limit_value: Decimal
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# Analytics Read Models
class AnalyticsReadModel(BaseModel):
    """Analytics read model"""
    analysis_id: str
    portfolio_id: str
    analysis_type: str
    results: Dict[str, Any]
    parameters: Dict[str, Any]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class CorrelationReadModel(BaseModel):
    """Correlation analysis read model"""
    analysis_id: str
    symbols: List[str]
    correlation_matrix: Dict[str, Dict[str, float]]
    average_correlation: float
    max_correlation: float
    min_correlation: float
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
