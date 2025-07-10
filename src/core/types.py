from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

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