"""
Advanced Options Strategies
Iron Condor, Butterfly, Calendar Spread implementations
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class IronCondorStrategy(BaseStrategy):
    """
    Iron Condor Strategy
    
    Sells out-of-the-money call and put spreads simultaneously.
    Profits from low volatility and time decay.
    """
    
    def __init__(self, 
                 name: str = "IronCondorStrategy",
                 profit_target_pct: float = 0.5,
                 max_loss_pct: float = 2.0,
                 days_to_expiration: int = 30,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.profit_target_pct = profit_target_pct
        self.max_loss_pct = max_loss_pct
        self.days_to_expiration = days_to_expiration
        
        logger.info(f"🎯 IronCondorStrategy initialized:")
        logger.info(f"  - Profit Target: {profit_target_pct*100:.1f}%")
        logger.info(f"  - Max Loss: {max_loss_pct*100:.1f}%")
        logger.info(f"  - DTE: {days_to_expiration}")
    
    async def generate_signal(self, data: pd.DataFrame, current_date: datetime) -> Optional[TradeSignal]:
        """Generate Iron Condor signal based on volatility and trend"""
        if data.empty or len(data) < 20:
            return None
        
        symbol = data['symbol'].iloc[-1] if 'symbol' in data.columns else "UNKNOWN"
        current_price = data['Close'].iloc[-1]
        
        # Check for low volatility conditions (ideal for Iron Condor)
        volatility = data['Close'].pct_change().std() * np.sqrt(252)
        
        # Check for sideways movement (ideal for Iron Condor)
        price_range = (data['High'].max() - data['Low'].min()) / current_price
        
        # Iron Condor conditions (relaxed)
        if (volatility < 0.30 and  # Relaxed from 0.25
            price_range < 0.20 and  # Relaxed from 0.15
            'RSI' in data.columns and 30 < data['RSI'].iloc[-1] < 70):  # Relaxed RSI range
            
            confidence = min(0.9, 0.5 + (0.30 - volatility) * 2)  # Adjusted confidence calculation
            
            logger.info(f"🎯 Iron Condor BUY signal for {symbol}: volatility={volatility:.3f}, range={price_range:.3f}")
            
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                confidence=confidence,
                strategy=self.name,
                timestamp=current_date,
                metadata={
                    'strategy_type': 'iron_condor',
                    'volatility': volatility,
                    'price_range': price_range,
                    'profit_target': self.profit_target_pct,
                    'max_loss': self.max_loss_pct
                }
            )
        
        return None

class ButterflyStrategy(BaseStrategy):
    """
    Butterfly Strategy
    
    Combines bull and bear spreads with same expiration.
    Profits from low volatility and precise price targeting.
    """
    
    def __init__(self, 
                 name: str = "ButterflyStrategy",
                 profit_target_pct: float = 0.8,
                 max_loss_pct: float = 1.0,
                 days_to_expiration: int = 30,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.profit_target_pct = profit_target_pct
        self.max_loss_pct = max_loss_pct
        self.days_to_expiration = days_to_expiration
        
        logger.info(f"🦋 ButterflyStrategy initialized:")
        logger.info(f"  - Profit Target: {profit_target_pct*100:.1f}%")
        logger.info(f"  - Max Loss: {max_loss_pct*100:.1f}%")
        logger.info(f"  - DTE: {days_to_expiration}")
    
    async def generate_signal(self, data: pd.DataFrame, current_date: datetime) -> Optional[TradeSignal]:
        """Generate Butterfly signal based on price consolidation"""
        if data.empty or len(data) < 20:
            return None
        
        symbol = data['symbol'].iloc[-1] if 'symbol' in data.columns else "UNKNOWN"
        current_price = data['Close'].iloc[-1]
        
        # Check for consolidation pattern (ideal for Butterfly)
        recent_data = data.tail(10)
        price_consolidation = (recent_data['High'].max() - recent_data['Low'].min()) / current_price
        
        # Check for low volatility
        volatility = data['Close'].pct_change().std() * np.sqrt(252)
        
        # Butterfly conditions (relaxed)
        if (price_consolidation < 0.12 and  # Relaxed from 0.08
            volatility < 0.35 and  # Relaxed from 0.30
            'BollingerBands' in data.columns):  # Bollinger Bands available
            
            # Check if price is near Bollinger Band middle (relaxed)
            bb_middle = data['BollingerBands'].iloc[-1] if 'BollingerBands' in data.columns else current_price
            bb_position = abs(current_price - bb_middle) / current_price
            
            if bb_position < 0.08:  # Relaxed from 0.05
                confidence = min(0.9, 0.6 + (0.12 - price_consolidation) * 5)  # Adjusted confidence
                
                logger.info(f"🦋 Butterfly BUY signal for {symbol}: consolidation={price_consolidation:.3f}, volatility={volatility:.3f}")
                
                return TradeSignal(
                    symbol=symbol,
                    action="BUY",
                    confidence=confidence,
                    strategy=self.name,
                    timestamp=current_date,
                    metadata={
                        'strategy_type': 'butterfly',
                        'consolidation': price_consolidation,
                        'volatility': volatility,
                        'profit_target': self.profit_target_pct,
                        'max_loss': self.max_loss_pct
                    }
                )
        
        return None

class CalendarSpreadStrategy(BaseStrategy):
    """
    Calendar Spread Strategy
    
    Sells short-term option, buys long-term option with same strike.
    Profits from time decay differential.
    """
    
    def __init__(self, 
                 name: str = "CalendarSpreadStrategy",
                 profit_target_pct: float = 0.6,
                 max_loss_pct: float = 1.5,
                 short_dte: int = 14,
                 long_dte: int = 45,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.profit_target_pct = profit_target_pct
        self.max_loss_pct = max_loss_pct
        self.short_dte = short_dte
        self.long_dte = long_dte
        
        logger.info(f"📅 CalendarSpreadStrategy initialized:")
        logger.info(f"  - Profit Target: {profit_target_pct*100:.1f}%")
        logger.info(f"  - Max Loss: {max_loss_pct*100:.1f}%")
        logger.info(f"  - Short DTE: {short_dte}, Long DTE: {long_dte}")
    
    async def generate_signal(self, data: pd.DataFrame, current_date: datetime) -> Optional[TradeSignal]:
        """Generate Calendar Spread signal based on volatility and trend"""
        if data.empty or len(data) < 20:
            return None
        
        symbol = data['symbol'].iloc[-1] if 'symbol' in data.columns else "UNKNOWN"
        current_price = data['Close'].iloc[-1]
        
        # Check for moderate volatility (ideal for Calendar Spread)
        volatility = data['Close'].pct_change().std() * np.sqrt(252)
        
        # Check for trending market (Calendar Spread works well in trends)
        price_trend = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        
        # Calendar Spread conditions (relaxed)
        if (0.10 < volatility < 0.40 and  # Relaxed volatility range
            abs(price_trend) > 0.01 and  # Relaxed trend requirement
            'MACD' in data.columns):  # MACD available
            
            # Check MACD signal (relaxed)
            macd_signal = data['MACD_Signal'].iloc[-1] if 'MACD_Signal' in data.columns else 0
            macd_line = data['MACD'].iloc[-1] if 'MACD' in data.columns else 0
            
            if abs(macd_line - macd_signal) > 0.005:  # Relaxed MACD divergence
                confidence = min(0.9, 0.5 + abs(price_trend) * 10)  # Adjusted confidence
                
                logger.info(f"📅 Calendar Spread BUY signal for {symbol}: trend={price_trend:.3f}, volatility={volatility:.3f}")
                
                return TradeSignal(
                    symbol=symbol,
                    action="BUY",
                    confidence=confidence,
                    strategy=self.name,
                    timestamp=current_date,
                    metadata={
                        'strategy_type': 'calendar_spread',
                        'price_trend': price_trend,
                        'volatility': volatility,
                        'profit_target': self.profit_target_pct,
                        'max_loss': self.max_loss_pct,
                        'short_dte': self.short_dte,
                        'long_dte': self.long_dte
                    }
                )
        
        return None
