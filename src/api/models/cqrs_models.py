"""
Pydantic models for CQRS API requests and responses
"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Union
from enum import Enum


# Enums
class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"


# Request Models
class PlaceOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    side: OrderSide = Field(..., description="Order side")
    quantity: int = Field(..., gt=0, description="Order quantity")
    order_type: OrderType = Field(..., description="Order type")
    price: Optional[Decimal] = Field(None, ge=0, description="Order price for limit orders")
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class CancelOrderRequest(BaseModel):
    order_id: str = Field(..., min_length=1, description="Order ID to cancel")
    reason: str = Field(..., min_length=1, description="Cancellation reason")


class CreateStrategyRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Strategy name")
    description: str = Field(..., description="Strategy description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")


class UpdatePortfolioRequest(BaseModel):
    portfolio_id: str = Field(..., min_length=1, description="Portfolio ID")
    name: Optional[str] = Field(None, description="Portfolio name")
    cash_balance: Optional[Decimal] = Field(None, ge=0, description="Cash balance")
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class UpdatePositionRequest(BaseModel):
    position_id: str = Field(..., min_length=1, description="Position ID")
    quantity: Optional[int] = Field(None, gt=0, description="Position quantity")
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")


class GetPortfolioRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")
    include_positions: bool = Field(False, description="Include positions")
    include_performance: bool = Field(False, description="Include performance metrics")


class GetPositionsRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    status: Optional[PositionStatus] = Field(None, description="Filter by status")


class GetMarketDataRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    start_date: Optional[date] = Field(None, description="Start date for historical data")
    end_date: Optional[date] = Field(None, description="End date for historical data")
    interval: str = Field("1d", description="Data interval")


class GetPerformanceRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    account_id: str = Field(..., min_length=1, description="Account ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    metrics: List[str] = Field(
        default=["total_return", "sharpe_ratio", "max_drawdown"],
        description="Performance metrics to calculate"
    )


class GetBacktestResultsRequest(BaseModel):
    strategy_id: str = Field(..., min_length=1, description="Strategy ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")


# Response Models
class OrderResponse(BaseModel):
    order_id: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Order side")
    quantity: int = Field(..., description="Order quantity")
    order_type: OrderType = Field(..., description="Order type")
    price: Optional[Decimal] = Field(None, description="Order price")
    status: OrderStatus = Field(..., description="Order status")
    user_id: str = Field(..., description="User ID")
    account_id: str = Field(..., description="Account ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PositionResponse(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., description="Position quantity")
    average_price: Decimal = Field(..., description="Average price")
    current_price: Decimal = Field(..., description="Current price")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L")
    realized_pnl: Decimal = Field(..., description="Realized P&L")
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class PortfolioResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    account_id: str = Field(..., description="Account ID")
    total_value: Decimal = Field(..., description="Total portfolio value")
    cash_balance: Decimal = Field(..., description="Cash balance")
    positions: List[PositionResponse] = Field(default_factory=list, description="Portfolio positions")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MarketDataResponse(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    current_price: Decimal = Field(..., description="Current price")
    price_change: Decimal = Field(..., description="Price change")
    price_change_pct: Decimal = Field(..., description="Price change percentage")
    volume: int = Field(..., description="Trading volume")
    last_updated: datetime = Field(..., description="Last update timestamp")
    historical_data: List[Dict[str, Any]] = Field(default_factory=list, description="Historical data")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PerformanceResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    account_id: str = Field(..., description="Account ID")
    total_return: Decimal = Field(..., description="Total return")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown")
    win_rate: Decimal = Field(..., description="Win rate")
    avg_trade_duration: timedelta = Field(..., description="Average trade duration")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            timedelta: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class BacktestResultsResponse(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID")
    total_return: Decimal = Field(..., description="Total return")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown")
    win_rate: Decimal = Field(..., description="Win rate")
    total_trades: int = Field(..., description="Total number of trades")
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="Trade details")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class StrategyResponse(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID")
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    status: str = Field(..., description="Strategy status")
    user_id: str = Field(..., description="User ID")
    account_id: str = Field(..., description="Account ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")


class EventSubscription(BaseModel):
    type: str = Field(..., description="Subscription type")
    event_types: List[str] = Field(..., description="Event types to subscribe to")
    user_id: Optional[str] = Field(None, description="User ID")
    account_id: Optional[str] = Field(None, description="Account ID")


class EventBroadcast(BaseModel):
    type: str = Field(..., description="Broadcast type")
    event_type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error Models
class ErrorDetail(BaseModel):
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Any = Field(None, description="Field value")


class APIError(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: List[ErrorDetail] = Field(..., description="Validation error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
