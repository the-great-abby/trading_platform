"""
Trading commands for CQRS implementation
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from decimal import Decimal

from ...cqrs.base import Command


class PlaceOrderCommand(Command):
    """Command to place a new order"""
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    order_type: str = "market"  # "market" or "limit"
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "day"  # "day", "gtc", "ioc"
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CancelOrderCommand(Command):
    """Command to cancel an existing order"""
    order_id: str
    reason: Optional[str] = None


class UpdateOrderCommand(Command):
    """Command to update an existing order"""
    order_id: str
    quantity: Optional[int] = None
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None


class ExecuteStrategyCommand(Command):
    """Command to execute a trading strategy"""
    strategy_id: str
    symbols: list[str]
    parameters: Optional[Dict[str, Any]] = None


class UpdateStrategyCommand(Command):
    """Command to update a trading strategy"""
    strategy_id: str
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CreateStrategyCommand(Command):
    """Command to create a new trading strategy"""
    name: str
    strategy_type: str  # "SMA_CROSSOVER", "RSI", etc.
    symbols: list[str]
    parameters: Dict[str, Any]
    initial_capital: Decimal
    risk_limits: Optional[Dict[str, Any]] = None 