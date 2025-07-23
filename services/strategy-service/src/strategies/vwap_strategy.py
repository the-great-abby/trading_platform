"""
VWAP (Volume Weighted Average Price) Strategy
==============================================
A strategy that trades relative to VWAP levels and identifies institutional activity.
VWAP is a key benchmark used by institutional traders for execution quality.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class VWAPStrategy(BaseStrategy):
    """
    VWAP Strategy
    
    Features:
    - Calculates VWAP for different timeframes
    - Identifies institutional buying/selling zones
    - Trades relative to VWAP levels
    - Volume profile analysis
    - Multiple timeframe confirmation
    """
    
    def __init__(self, 
                 name: str = "VWAP_Strategy",
                 vwap_period: int = 20,
                 volume_threshold: float = 1.5,
                 price_deviation_threshold: float = 0.02,
                 confidence_threshold: float = 0.6):
        super().__init__(name)
        self.vwap_period = vwap_period
        self.volume_threshold = volume_threshold
        self.price_deviation_threshold = price_deviation_threshold
        self.confidence_threshold = confidence_threshold
        
        # VWAP cache
        self.vwap_cache = {}
        
    def calculate_vwap(self, data: pd.DataFrame, period: int = None) -> pd.Series:
        """Calculate VWAP (Volume Weighted Average Price)"""
        if period is None:
            period = self.vwap_period
            
        if len(data) < period:
            return pd.Series([np.nan] * len(data), index=data.index)
        
        # Calculate typical price (HLC/3)
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        
        # Calculate volume-weighted average
        vwap = (typical_price * data['Volume']).rolling(window=period).sum() / \
               data['Volume'].rolling(window=period).sum()
        
        return vwap
    
    def calculate_vwap_bands(self, data: pd.DataFrame, std_dev: float = 1.0) -> Dict[str, pd.Series]:
        """Calculate VWAP bands (standard deviation bands)"""
        vwap = self.calculate_vwap(data)
        
        # Calculate standard deviation of price from VWAP
        price_deviation = (data['Close'] - vwap).rolling(window=self.vwap_period).std()
        
        upper_band = vwap + (price_deviation * std_dev)
        lower_band = vwap - (price_deviation * std_dev)
        
        return {
            'vwap': vwap,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'std_dev': price_deviation
        }
    
    def calculate_volume_profile(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume profile metrics"""
        if len(data) < 10:
            return {}
        
        # Volume metrics
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Price-volume relationship
        price_change = data['Close'].pct_change().iloc[-1]
        volume_price_correlation = data['Volume'].corr(data['Close'])
        
        # Institutional activity indicators
        large_volume_threshold = avg_volume * 2
        is_large_volume = current_volume > large_volume_threshold
        
        return {
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'volume_price_correlation': volume_price_correlation,
            'is_large_volume': is_large_volume,
            'avg_volume': avg_volume,
            'current_volume': current_volume
        }
    
    def identify_institutional_zones(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify potential institutional buying/selling zones"""
        vwap_bands = self.calculate_vwap_bands(data)
        volume_profile = self.calculate_volume_profile(data)
        
        current_price = data['Close'].iloc[-1]
        current_vwap = vwap_bands['vwap'].iloc[-1]
        upper_band = vwap_bands['upper_band'].iloc[-1]
        lower_band = vwap_bands['lower_band'].iloc[-1]
        
        # Determine zone
        if current_price > upper_band:
            zone = "above_upper_band"
            institutional_action = "potential_selling"
        elif current_price < lower_band:
            zone = "below_lower_band"
            institutional_action = "potential_buying"
        elif current_price > current_vwap:
            zone = "above_vwap"
            institutional_action = "neutral_bullish"
        else:
            zone = "below_vwap"
            institutional_action = "neutral_bearish"
        
        return {
            'zone': zone,
            'institutional_action': institutional_action,
            'distance_from_vwap': (current_price - current_vwap) / current_vwap,
            'volume_profile': volume_profile
        }
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate VWAP-based trading signal"""
        
        if len(data) < self.vwap_period + 10:
            return None
        
        # Calculate VWAP and bands
        vwap_bands = self.calculate_vwap_bands(data)
        institutional_zones = self.identify_institutional_zones(data)
        
        current_price = data['Close'].iloc[-1]
        current_vwap = vwap_bands['vwap'].iloc[-1]
        upper_band = vwap_bands['upper_band'].iloc[-1]
        lower_band = vwap_bands['lower_band'].iloc[-1]
        
        # Skip if VWAP is not available
        if pd.isna(current_vwap):
            return None
        
        # Calculate price deviation from VWAP
        price_deviation = (current_price - current_vwap) / current_vwap
        
        # Generate signals based on VWAP levels and volume
        signal = None
        confidence = 0.0
        action = None
        
        volume_profile = institutional_zones['volume_profile']
        zone = institutional_zones['zone']
        
        # BUY Signals
        if (zone == "below_lower_band" and 
            volume_profile.get('volume_ratio', 1.0) > self.volume_threshold):
            # Price below lower band with high volume - potential institutional buying
            action = "BUY"
            confidence = min(abs(price_deviation) * 10, 0.9)
            confidence *= min(volume_profile.get('volume_ratio', 1.0) / 2, 1.0)
            
        elif (zone == "below_vwap" and 
              abs(price_deviation) > self.price_deviation_threshold and
              volume_profile.get('volume_ratio', 1.0) > 1.2):
            # Price below VWAP with significant deviation and above-average volume
            action = "BUY"
            confidence = min(abs(price_deviation) * 8, 0.8)
            
        # SELL Signals
        elif (zone == "above_upper_band" and 
              volume_profile.get('volume_ratio', 1.0) > self.volume_threshold):
            # Price above upper band with high volume - potential institutional selling
            action = "SELL"
            confidence = min(abs(price_deviation) * 10, 0.9)
            confidence *= min(volume_profile.get('volume_ratio', 1.0) / 2, 1.0)
            
        elif (zone == "above_vwap" and 
              abs(price_deviation) > self.price_deviation_threshold and
              volume_profile.get('volume_ratio', 1.0) > 1.2):
            # Price above VWAP with significant deviation and above-average volume
            action = "SELL"
            confidence = min(abs(price_deviation) * 8, 0.8)
        
        # Generate signal if confidence meets threshold
        if action and confidence > self.confidence_threshold:
            signal = TradeSignal(
                symbol=symbol,
                action=action,
                quantity=self._calculate_quantity(current_price, confidence),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=confidence,
                metadata={
                    'vwap': current_vwap,
                    'price_deviation': price_deviation,
                    'zone': zone,
                    'institutional_action': institutional_zones['institutional_action'],
                    'volume_ratio': volume_profile.get('volume_ratio', 1.0),
                    'upper_band': upper_band,
                    'lower_band': lower_band,
                    'signal_type': 'vwap_trading',
                    'is_institutional_activity': volume_profile.get('is_large_volume', False)
                }
            )
            
            logger.info(f"VWAP signal: {symbol} {action} (confidence: {confidence:.2f}, "
                       f"zone: {zone}, volume_ratio: {volume_profile.get('volume_ratio', 1.0):.2f})")
        
        return signal
    
    def _calculate_quantity(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_size = 1000  # Base position size
        return (base_size * confidence) / price
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "vwap_period": self.vwap_period,
            "volume_threshold": self.volume_threshold,
            "price_deviation_threshold": self.price_deviation_threshold,
            "confidence_threshold": self.confidence_threshold
        } 