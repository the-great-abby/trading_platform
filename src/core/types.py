from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"

@dataclass
class TradeSignal:
    """Trade signal data structure"""
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class Trade:
    """Trade execution data structure"""
    symbol: str
    action: str  # "BUY", "SELL"
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    pnl: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None 