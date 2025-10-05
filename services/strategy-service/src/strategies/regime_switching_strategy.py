"""
Regime Switching Strategy System
Handles dynamic strategy adaptation based on market conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

@dataclass
class RegimeDetection:
    """Regime detection result"""
    regime: MarketRegime
    confidence: float
    duration_days: int
    indicators: Dict[str, Any]
    timestamp: datetime

class RegimeSwitchingStrategy(BaseStrategy):
    """
    Regime Switching Strategy
    
    Dynamically switches between strategies based on detected market regimes.
    This addresses the challenge of strategy adaptation during regime changes.
    """
    
    def __init__(self, 
                 name: str = "RegimeSwitchingStrategy",
                 regime_detection_window: int = 20,
                 regime_confidence_threshold: float = 0.6,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.regime_detection_window = regime_detection_window
        self.regime_confidence_threshold = regime_confidence_threshold
        
        # Strategy weights for each regime
        self.strategy_weights = {
            MarketRegime.TRENDING_UP: {
                "ElliottWaveImpulseStrategy": 0.4,
                "MACD": 0.3,
                "RSI": 0.2,
                "BollingerBands": 0.1
            },
            MarketRegime.TRENDING_DOWN: {
                "ElliottWaveCorrectiveStrategy": 0.4,
                "RSI": 0.3,
                "MACD": 0.2,
                "BollingerBands": 0.1
            },
            MarketRegime.SIDEWAYS: {
                "BollingerBands": 0.4,
                "RSI": 0.3,
                "ElliottWaveCorrectiveStrategy": 0.2,
                "MACD": 0.1
            },
            MarketRegime.HIGH_VOLATILITY: {
                "ElliottWaveCorrectiveStrategy": 0.5,
                "RSI": 0.3,
                "BollingerBands": 0.2
            },
            MarketRegime.LOW_VOLATILITY: {
                "MACD": 0.4,
                "ElliottWaveImpulseStrategy": 0.3,
                "RSI": 0.2,
                "BollingerBands": 0.1
            }
        }
        
        self.regime_history: List[RegimeDetection] = []
        self.current_regime: Optional[RegimeDetection] = None
        
        logger.info(f"🌊 RegimeSwitchingStrategy initialized")
    
    def detect_market_regime(self, data: pd.DataFrame) -> Optional[RegimeDetection]:
        """Detect current market regime based on technical indicators"""
        if len(data) < self.regime_detection_window:
            return None
        
        recent_data = data.tail(self.regime_detection_window)
        indicators = self._calculate_regime_indicators(recent_data)
        regime_scores = self._score_regimes(indicators)
        
        best_regime = max(regime_scores.items(), key=lambda x: x[1])
        regime_type, confidence = best_regime
        
        if confidence < self.regime_confidence_threshold:
            return None
        
        duration_days = self._calculate_regime_duration(regime_type)
        
        return RegimeDetection(
            regime=regime_type,
            confidence=confidence,
            duration_days=duration_days,
            indicators=indicators,
            timestamp=datetime.now()
        )
    
    def _calculate_regime_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for regime detection"""
        price_change = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
        daily_returns = data['Close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        
        return {
            'price_trend': price_change,
            'volatility': volatility,
            'rsi_current': data['RSI'].iloc[-1] if 'RSI' in data.columns else 50.0,
            'macd_current': data['MACD'].iloc[-1] - data['MACD_Signal'].iloc[-1] if 'MACD' in data.columns else 0.0
        }
    
    def _score_regimes(self, indicators: Dict[str, Any]) -> Dict[MarketRegime, float]:
        """Score each regime based on indicators"""
        price_trend = indicators['price_trend']
        volatility = indicators['volatility']
        rsi_current = indicators['rsi_current']
        macd_current = indicators['macd_current']
        
        return {
            MarketRegime.TRENDING_UP: max(0, price_trend * 2) + max(0, macd_current * 10) + (1 if rsi_current > 50 else 0) * 0.2,
            MarketRegime.TRENDING_DOWN: max(0, -price_trend * 2) + max(0, -macd_current * 10) + (1 if rsi_current < 50 else 0) * 0.2,
            MarketRegime.SIDEWAYS: max(0, 0.1 - abs(price_trend)) + max(0, 0.1 - abs(macd_current)) + (1 if 40 < rsi_current < 60 else 0) * 0.3,
            MarketRegime.HIGH_VOLATILITY: max(0, volatility - 0.3) * 2,
            MarketRegime.LOW_VOLATILITY: max(0, 0.2 - volatility) * 2
        }
    
    def _calculate_regime_duration(self, regime_type: MarketRegime) -> int:
        """Calculate how long the current regime has been active"""
        if not self.regime_history:
            return 1
        
        duration = 1
        for detection in reversed(self.regime_history):
            if detection.regime == regime_type:
                duration += 1
            else:
                break
        
        return duration
    
    def get_active_strategies(self, regime: MarketRegime) -> Dict[str, float]:
        """Get active strategies and their weights for the given regime"""
        return self.strategy_weights.get(regime, {})
    
    async def generate_signal(self, data: pd.DataFrame, current_date: datetime) -> Optional[TradeSignal]:
        """Generate signal based on regime switching logic"""
        if data.empty:
            return None
        
        regime_detection = self.detect_market_regime(data)
        if not regime_detection:
            return None
        
        self.regime_history.append(regime_detection)
        self.current_regime = regime_detection
        
        if len(self.regime_history) > 50:
            self.regime_history = self.regime_history[-50:]
        
        active_strategies = self.get_active_strategies(regime_detection.regime)
        
        logger.info(f"🌊 Regime Switch: {regime_detection.regime.value} (confidence: {regime_detection.confidence:.2f})")
        
        return TradeSignal(
            symbol=data['symbol'].iloc[-1] if 'symbol' in data.columns else "REGIME",
            action="REGIME_SWITCH",
            confidence=regime_detection.confidence,
            strategy=self.name,
            timestamp=current_date,
            metadata={
                'regime': regime_detection.regime.value,
                'duration_days': regime_detection.duration_days,
                'active_strategies': active_strategies
            }
        )