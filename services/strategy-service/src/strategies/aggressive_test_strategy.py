#!/usr/bin/env python3
"""
Aggressive Test Strategy
A strategy that always generates signals for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal


class AggressiveTestStrategy(BaseStrategy):
    """Aggressive test strategy that always generates signals"""
    
    def __init__(self, **kwargs):
        super().__init__("AggressiveTestStrategy", kwargs)
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal - always generates BUY signal"""
        if data.empty:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Always generate a BUY signal
        return TradeSignal(
            symbol=symbol,
            action="BUY",
            quantity=100,  # Fixed quantity
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=0.9,
            metadata={
                "signal_type": "aggressive_test",
                "data_points": len(data)
            }
        )
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size"""
        return 100

