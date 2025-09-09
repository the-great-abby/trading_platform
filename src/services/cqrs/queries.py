"""
CQRS Query Definitions
Defines all queries for the trading system
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from src.cqrs.base import Query


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class TimeRange(str, Enum):
    """Time range enumeration"""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


# Portfolio Queries
class GetPortfolioQuery(Query):
    """Query to get portfolio information"""
    portfolio_id: Optional[str] = None
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    include_positions: bool = True
    include_performance: bool = True
    include_metadata: bool = False


class GetPositionsQuery(Query):
    """Query to get position information"""
    portfolio_id: Optional[str] = None
    symbol: Optional[str] = None
    min_quantity: Optional[int] = None
    include_closed: bool = False
    sort_by: str = "symbol"
    sort_order: SortOrder = SortOrder.ASC
    limit: Optional[int] = None
    offset: Optional[int] = None


# Market Data Queries
class GetMarketDataQuery(Query):
    """Query to get market data"""
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_range: Optional[TimeRange] = None
    interval: str = "1d"  # 1m, 5m, 15m, 1h, 1d, 1w
    indicators: Optional[List[str]] = None
    include_volume: bool = True
    include_ohlc: bool = True


class GetMarketDataHistoryQuery(Query):
    """Query to get historical market data"""
    symbol: str
    start_date: datetime
    end_date: datetime
    interval: str = "1d"
    indicators: Optional[List[str]] = None
    limit: Optional[int] = None


# Performance Queries
class GetPerformanceQuery(Query):
    """Query to get performance metrics"""
    portfolio_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_range: Optional[TimeRange] = None
    include_benchmark: bool = False
    benchmark_symbol: Optional[str] = None
    include_risk_metrics: bool = True


class GetBacktestResultsQuery(Query):
    """Query to get backtest results"""
    backtest_id: Optional[str] = None
    strategy_id: Optional[str] = None
    include_trades: bool = True
    include_metrics: bool = True
    include_charts: bool = False
    limit: Optional[int] = None
    offset: Optional[int] = None


# Order Queries
class GetOrderQuery(Query):
    """Query to get order information"""
    order_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    symbol: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


class GetOrderHistoryQuery(Query):
    """Query to get order history"""
    portfolio_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_cancelled: bool = True
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


# Strategy Queries
class GetStrategyQuery(Query):
    """Query to get strategy information"""
    strategy_id: Optional[str] = None
    strategy_type: Optional[str] = None
    is_active: Optional[bool] = None
    include_performance: bool = True
    include_metadata: bool = False
    limit: Optional[int] = None
    offset: Optional[int] = None


class GetStrategyPerformanceQuery(Query):
    """Query to get strategy performance"""
    strategy_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_range: Optional[TimeRange] = None
    include_benchmark: bool = False
    benchmark_symbol: Optional[str] = None


# Signal Queries
class GetSignalQuery(Query):
    """Query to get signal information"""
    signal_id: Optional[str] = None
    symbol: Optional[str] = None
    signal_type: Optional[str] = None
    strategy_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_expired: bool = False
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


class GetActiveSignalsQuery(Query):
    """Query to get active signals"""
    symbol: Optional[str] = None
    strategy_id: Optional[str] = None
    signal_type: Optional[str] = None
    min_strength: Optional[float] = None
    sort_by: str = "strength"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None


# Trading History Queries
class GetTradingHistoryQuery(Query):
    """Query to get trading history"""
    portfolio_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_orders: bool = True
    include_trades: bool = True
    include_signals: bool = False
    sort_by: str = "timestamp"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


class GetTradeQuery(Query):
    """Query to get individual trade information"""
    trade_id: Optional[str] = None
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_metadata: bool = True
    sort_by: str = "executed_at"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


# Risk Management Queries
class GetRiskMetricsQuery(Query):
    """Query to get risk management metrics"""
    portfolio_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_limits: bool = True
    include_current_exposure: bool = True
    include_historical: bool = False


class GetRiskAlertsQuery(Query):
    """Query to get risk management alerts"""
    portfolio_id: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_resolved: bool = False
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: Optional[int] = None


# Analytics Queries
class GetAnalyticsQuery(Query):
    """Query to get analytics data"""
    portfolio_id: Optional[str] = None
    analysis_type: str  # performance, risk, correlation, etc.
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    include_charts: bool = False
    include_metadata: bool = True


class GetCorrelationQuery(Query):
    """Query to get correlation analysis"""
    symbols: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    correlation_type: str = "pearson"  # pearson, spearman, kendall
    include_heatmap: bool = False
    include_metadata: bool = True
