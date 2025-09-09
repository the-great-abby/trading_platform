"""
CQRS Event Definitions
Defines all events for the trading system
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.cqrs.base import Event


# Base Event class for event sourcing
class BaseEvent(Event):
    """Base event class for event sourcing"""
    pass


# Order Events
class OrderCreatedEvent(BaseEvent):
    """Event when an order is created"""
    order_id: str
    symbol: str
    quantity: int
    order_type: str
    side: str
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    user_id: str
    account_id: str


class OrderUpdatedEvent(BaseEvent):
    """Event when an order is updated"""
    order_id: str
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None


class OrderFilledEvent(BaseEvent):
    """Event when an order is filled"""
    order_id: str
    filled_quantity: int
    fill_price: Decimal
    remaining_quantity: int


class OrderCancelledEvent(BaseEvent):
    """Event when an order is cancelled"""
    order_id: str
    reason: str
    cancelled_quantity: int


class OrderRejectedEvent(BaseEvent):
    """Event when an order is rejected"""
    order_id: str
    reason: str
    rejected_at: datetime


# Strategy Events
class StrategyCreatedEvent(BaseEvent):
    """Event when a strategy is created"""
    strategy_id: str
    name: str
    strategy_type: str
    parameters: Dict[str, Any]


class StrategyUpdatedEvent(BaseEvent):
    """Event when a strategy is updated"""
    strategy_id: str
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StrategyDeletedEvent(BaseEvent):
    """Event when a strategy is deleted"""
    strategy_id: str
    reason: Optional[str] = None


class StrategyStartedEvent(BaseEvent):
    """Event when a strategy is started"""
    strategy_id: str
    started_at: datetime


class StrategyStoppedEvent(BaseEvent):
    """Event when a strategy is stopped"""
    strategy_id: str
    stopped_at: datetime
    reason: Optional[str] = None


# Signal Events
class SignalCreatedEvent(BaseEvent):
    """Event when a signal is created"""
    signal_id: str
    symbol: str
    signal_type: str
    strength: float
    price: Decimal
    quantity: Optional[int] = None
    strategy_id: Optional[str] = None


class SignalUpdatedEvent(BaseEvent):
    """Event when a signal is updated"""
    signal_id: str
    signal_type: Optional[str] = None
    strength: Optional[float] = None
    price: Optional[Decimal] = None
    quantity: Optional[int] = None


class SignalDeletedEvent(BaseEvent):
    """Event when a signal is deleted"""
    signal_id: str
    reason: Optional[str] = None


class SignalExpiredEvent(BaseEvent):
    """Event when a signal expires"""
    signal_id: str
    symbol: str
    expired_at: datetime


# Portfolio Events
class PortfolioUpdatedEvent(BaseEvent):
    """Event when portfolio is updated"""
    portfolio_id: str
    user_id: str
    account_id: str
    name: str
    cash_balance: Decimal
    total_value: Decimal


class PositionUpdatedEvent(BaseEvent):
    """Event when a position is updated"""
    symbol: str
    quantity: int
    average_price: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None


class PositionOpenedEvent(BaseEvent):
    """Event when a position is opened"""
    portfolio_id: str
    symbol: str
    quantity: int
    price: Decimal
    market_value: Decimal


class PositionClosedEvent(BaseEvent):
    """Event when a position is closed"""
    portfolio_id: str
    symbol: str
    quantity: int
    price: Decimal
    market_value: Decimal


# Trade Events
class TradeExecutedEvent(BaseEvent):
    """Event when a trade is executed"""
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


# Backtest Events
class BacktestStartedEvent(BaseEvent):
    """Event when a backtest is started"""
    backtest_id: str
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    started_at: datetime


class BacktestCompletedEvent(BaseEvent):
    """Event when a backtest is completed"""
    backtest_id: str
    strategy_id: str
    final_capital: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    completed_at: datetime
    results: Dict[str, Any]


class BacktestFailedEvent(BaseEvent):
    """Event when a backtest fails"""
    backtest_id: str
    strategy_id: str
    error: str
    failed_at: datetime


# Risk Management Events
class RiskLimitExceededEvent(BaseEvent):
    """Event when a risk limit is exceeded"""
    portfolio_id: str
    limit_type: str
    current_value: Decimal
    limit_value: Decimal
    severity: str = "warning"


class RiskAlertTriggeredEvent(BaseEvent):
    """Event when a risk alert is triggered"""
    alert_id: str
    portfolio_id: str
    alert_type: str
    severity: str
    message: str
    current_value: Decimal
    limit_value: Decimal


class RiskAlertResolvedEvent(BaseEvent):
    """Event when a risk alert is resolved"""
    alert_id: str
    portfolio_id: str
    resolved_at: datetime
    resolution_notes: Optional[str] = None


# Market Data Events
class MarketDataUpdatedEvent(BaseEvent):
    """Event when market data is updated"""
    symbol: str
    price: Decimal
    volume: int
    timestamp: datetime
    indicators: Optional[Dict[str, Decimal]] = None


class MarketDataErrorEvent(BaseEvent):
    """Event when market data error occurs"""
    symbol: str
    error: str
    timestamp: datetime


# System Events
class SystemStartedEvent(BaseEvent):
    """Event when the system starts"""
    started_at: datetime
    version: str
    environment: str


class SystemStoppedEvent(BaseEvent):
    """Event when the system stops"""
    stopped_at: datetime
    reason: Optional[str] = None


class SystemErrorEvent(BaseEvent):
    """Event when a system error occurs"""
    error: str
    component: str
    timestamp: datetime
    severity: str = "error"


# Performance Events
class PerformanceCalculatedEvent(BaseEvent):
    """Event when performance is calculated"""
    portfolio_id: str
    period_start: datetime
    period_end: datetime
    total_return: Decimal
    total_return_percentage: Decimal
    calculated_at: datetime


class PerformanceAlertEvent(BaseEvent):
    """Event when performance alert is triggered"""
    portfolio_id: str
    alert_type: str
    current_value: Decimal
    threshold_value: Decimal
    message: str
    severity: str = "warning"


# Analytics Events
class AnalyticsCalculatedEvent(BaseEvent):
    """Event when analytics are calculated"""
    analysis_id: str
    portfolio_id: str
    analysis_type: str
    results: Dict[str, Any]
    calculated_at: datetime


class CorrelationCalculatedEvent(BaseEvent):
    """Event when correlation analysis is calculated"""
    analysis_id: str
    symbols: List[str]
    correlation_matrix: Dict[str, Dict[str, float]]
    calculated_at: datetime


# Notification Events
class NotificationSentEvent(BaseEvent):
    """Event when a notification is sent"""
    notification_id: str
    recipient: str
    notification_type: str
    message: str
    sent_at: datetime
    delivery_status: str = "sent"


class NotificationFailedEvent(BaseEvent):
    """Event when a notification fails"""
    notification_id: str
    recipient: str
    error: str
    failed_at: datetime


# Audit Events
class AuditEvent(BaseEvent):
    """Generic audit event"""
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class DataAccessEvent(BaseEvent):
    """Event when data is accessed"""
    user_id: Optional[str] = None
    resource_type: str
    resource_id: str
    action: str  # read, write, delete
    timestamp: datetime
    ip_address: Optional[str] = None
