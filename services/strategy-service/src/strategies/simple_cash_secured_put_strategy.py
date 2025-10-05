"""
Simple Cash Secured Put Strategy
===============================

A simplified version of the Cash Secured Put strategy that bypasses complex logic
and generates basic signals for testing purposes.
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)

class SimpleCashSecuredPutStrategy(BaseStrategy):
    """Simplified Cash Secured Put Strategy for testing"""
    
    def __init__(self, **kwargs):
        super().__init__("SimpleCashSecuredPut", kwargs)
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate simple cash secured put signal"""
        
        if len(data) < 5:  # Very low data requirement
            logger.info(f"🔍 SimpleCashSecuredPut DEBUG: Insufficient data for {symbol} ({len(data)} days)")
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Simple logic: Generate BUY signal every 5 days
        day_index = len(data) % 5
        if day_index == 0:  # Every 5th day
            logger.info(f"🔍 SimpleCashSecuredPut DEBUG: Generating BUY signal for {symbol} on day {len(data)}")
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=100,  # Fixed quantity
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.8,
                metadata={
                    "strategy_type": "simple_cash_secured_put",
                    "day_index": day_index,
                    "total_days": len(data)
                }
            )
        
        logger.info(f"🔍 SimpleCashSecuredPut DEBUG: No signal for {symbol} on day {len(data)} (day_index={day_index})")
        return None

