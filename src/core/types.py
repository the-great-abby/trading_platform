from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

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