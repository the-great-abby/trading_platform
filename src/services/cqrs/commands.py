"""
CQRS Command Definitions
Defines all commands for the trading system
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from src.cqrs.base import Command


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    SMA_CROSSOVER = "sma_crossover"
    RSI_MEAN_REVERSION = "rsi_mean_reversion"
    BOLLINGER_BANDS = "bollinger_bands"
    MACD = "macd"
    ICHIMOKU = "ichimoku"
    CUSTOM = "custom"


class SignalType(str, Enum):
    """Signal type enumeration"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ALERT = "alert"


# Order Management Commands
class PlaceOrderCommand(Command):
    """Command to place a new order"""
    symbol: str
    quantity: int
    order_type: OrderType
    side: OrderSide
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CancelOrderCommand(Command):
    """Command to cancel an existing order"""
    order_id: str
    reason: Optional[str] = None


class UpdateOrderCommand(Command):
    """Command to update an existing order"""
    order_id: str
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Strategy Management Commands
class CreateStrategyCommand(Command):
    """Command to create a new trading strategy"""
    name: str
    strategy_type: StrategyType
    description: Optional[str] = None
    parameters: Dict[str, Any]
    is_active: bool = True
    symbols: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class UpdateStrategyCommand(Command):
    """Command to update an existing strategy"""
    strategy_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    symbols: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DeleteStrategyCommand(Command):
    """Command to delete a strategy"""
    strategy_id: str
    reason: Optional[str] = None


# Signal Management Commands
class CreateSignalCommand(Command):
    """Command to create a new trading signal"""
    symbol: str
    signal_type: SignalType
    strength: float  # 0.0 to 1.0
    price: Decimal
    quantity: Optional[int] = None
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class UpdateSignalCommand(Command):
    """Command to update an existing signal"""
    signal_id: str
    signal_type: Optional[SignalType] = None
    strength: Optional[float] = None
    price: Optional[Decimal] = None
    quantity: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class DeleteSignalCommand(Command):
    """Command to delete a signal"""
    signal_id: str
    reason: Optional[str] = None


# Portfolio Management Commands
class UpdatePortfolioCommand(Command):
    """Command to update portfolio information"""
    portfolio_id: str
    cash_balance: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdatePositionCommand(Command):
    """Command to update position information"""
    symbol: str
    quantity: int
    average_price: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


# Backtest Commands
class StartBacktestCommand(Command):
    """Command to start a backtest"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    symbols: List[str]
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class StopBacktestCommand(Command):
    """Command to stop a running backtest"""
    backtest_id: str
    reason: Optional[str] = None


# Risk Management Commands
class UpdateRiskLimitsCommand(Command):
    """Command to update risk management limits"""
    portfolio_id: str
    max_position_size: Optional[Decimal] = None
    max_daily_loss: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    stop_loss_percentage: Optional[float] = None
    take_profit_percentage: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class TriggerRiskAlertCommand(Command):
    """Command to trigger a risk management alert"""
    portfolio_id: str
    alert_type: str
    current_value: Decimal
    limit_value: Decimal
    severity: str = "warning"  # warning, critical, emergency
    metadata: Optional[Dict[str, Any]] = None
