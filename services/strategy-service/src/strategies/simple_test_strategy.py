#!/usr/bin/env python3
"""
Simple Test Strategy - Always generates signals
This will verify the backtest engine works correctly
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class SimpleTestStrategy(BaseStrategy):
    """
    Simple test strategy that always generates signals
    Used to verify the backtest engine works correctly
    """
    
    def __init__(self, name: str = "SimpleTestStrategy", **kwargs):
        super().__init__(name=name, **kwargs)
        self.signal_count = 0
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate a simple test signal"""
        
        if len(data) < 5:  # Minimal data requirement
            return None
        
        current_price = data['Close'].iloc[-1]
        self.signal_count += 1
        
        # Alternate between BUY and SELL signals
        action = "BUY" if self.signal_count % 2 == 1 else "SELL"
        
        logger.info(f"🔍 SIMPLE TEST - {symbol}: Generating {action} signal #{self.signal_count}")
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=100,  # Fixed quantity
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=0.8,
            metadata={
                "signal_count": self.signal_count,
                "test_strategy": True
            }
        )

