"""
Trading events for CQRS implementation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from ...cqrs.base import Event


class OrderPlacedEvent(Event):
    """Event when an order is placed"""
    order_id: str
    symbol: str
    side: str
    quantity: int
    order_type: str
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "day"
    strategy_id: Optional[str] = None
    user_id: str = None


class OrderCancelledEvent(Event):
    """Event when an order is cancelled"""
    order_id: str
    reason: Optional[str] = None
    user_id: str = None


class OrderUpdatedEvent(Event):
    """Event when an order is updated"""
    order_id: str
    quantity: Optional[int] = None
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None
    user_id: str = None


class OrderFilledEvent(Event):
    """Event when an order is filled"""
    order_id: str
    symbol: str
    side: str
    quantity: int
    fill_price: Decimal
    fill_time: datetime
    commission: Optional[Decimal] = None
    user_id: str = None


class OrderRejectedEvent(Event):
    """Event when an order is rejected"""
    order_id: str
    reason: str
    user_id: str = None


class StrategyCreatedEvent(Event):
    """Event when a strategy is created"""
    strategy_id: str
    name: str
    strategy_type: str
    symbols: list[str]
    parameters: Dict[str, Any]
    initial_capital: Decimal
    risk_limits: Optional[Dict[str, Any]] = None
    user_id: str = None


class StrategyUpdatedEvent(Event):
    """Event when a strategy is updated"""
    strategy_id: str
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    user_id: str = None


class StrategyExecutedEvent(Event):
    """Event when a strategy is executed"""
    strategy_id: str
    symbols: list[str]
    parameters: Optional[Dict[str, Any]] = None
    execution_time: datetime
    user_id: str = None


class SignalGeneratedEvent(Event):
    """Event when a trading signal is generated"""
    signal_id: str
    strategy_id: str
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    quantity: int
    price: Decimal
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    user_id: str = None


class TradeExecutedEvent(Event):
    """Event when a trade is executed"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: Decimal
    timestamp: datetime
    strategy_id: Optional[str] = None
    user_id: str = None 