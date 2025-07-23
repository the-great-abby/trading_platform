"""
Kalman Filter Strategy
======================
A strategy that uses Kalman filtering for adaptive price prediction and trend estimation.
Continuously updates estimates based on new data and handles noisy market data effectively.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class KalmanFilter:
    """Kalman Filter implementation for price prediction"""
    
    def __init__(self, initial_state: float, initial_variance: float = 1.0):
        self.state = initial_state  # Current price estimate
        self.variance = initial_variance  # Current uncertainty
        
        # Process noise (how much we expect the state to change)
        self.process_noise = 0.01
        
        # Measurement noise (how noisy our observations are)
        self.measurement_noise = 0.1
        
    def predict(self) -> Tuple[float, float]:
        """Predict next state"""
        # State prediction (assume no change)
        predicted_state = self.state
        predicted_variance = self.variance + self.process_noise
        
        return predicted_state, predicted_variance
    
    def update(self, measurement: float) -> Tuple[float, float]:
        """Update state with new measurement"""
        # Predict
        predicted_state, predicted_variance = self.predict()
        
        # Calculate Kalman gain
        kalman_gain = predicted_variance / (predicted_variance + self.measurement_noise)
        
        # Update state
        self.state = predicted_state + kalman_gain * (measurement - predicted_state)
        self.variance = (1 - kalman_gain) * predicted_variance
        
        return self.state, self.variance
    
    def get_estimate(self) -> Tuple[float, float]:
        """Get current state estimate and uncertainty"""
        return self.state, self.variance

class KalmanFilterStrategy(BaseStrategy):
    """
    Kalman Filter Strategy
    
    Features:
    - Adaptive filtering for price prediction
    - Continuous state estimation
    - Handles noisy market data effectively
    - Multiple timeframe analysis
    - Trend detection and momentum estimation
    """
    
    def __init__(self, 
                 name: str = "KalmanFilter",
                 lookback_period: int = 50,
                 prediction_threshold: float = 0.02,
                 confidence_threshold: float = 0.6,
                 volatility_window: int = 20,
                 trend_strength_threshold: float = 0.5):
        super().__init__(name)
        self.lookback_period = lookback_period
        self.prediction_threshold = prediction_threshold
        self.confidence_threshold = confidence_threshold
        self.volatility_window = volatility_window
        self.trend_strength_threshold = trend_strength_threshold
        
        # Kalman filters for different timeframes
        self.kalman_filters = {}
        self.price_history = {}
        self.trend_estimates = {}
        
    def initialize_kalman_filter(self, symbol: str, initial_price: float):
        """Initialize Kalman filter for a symbol"""
        if symbol not in self.kalman_filters:
            self.kalman_filters[symbol] = KalmanFilter(initial_price)
            self.price_history[symbol] = []
            self.trend_estimates[symbol] = []
    
    def update_kalman_filter(self, symbol: str, current_price: float) -> Tuple[float, float]:
        """Update Kalman filter with new price data"""
        if symbol not in self.kalman_filters:
            self.initialize_kalman_filter(symbol, current_price)
        
        # Update filter
        estimated_price, uncertainty = self.kalman_filters[symbol].update(current_price)
        
        # Store price history
        self.price_history[symbol].append(current_price)
        if len(self.price_history[symbol]) > self.lookback_period:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_period:]
        
        # Calculate trend estimate
        if len(self.price_history[symbol]) >= 10:
            recent_prices = self.price_history[symbol][-10:]
            trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            self.trend_estimates[symbol].append(trend)
            if len(self.trend_estimates[symbol]) > 20:
                self.trend_estimates[symbol] = self.trend_estimates[symbol][-20:]
        
        return estimated_price, uncertainty
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
        
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns)
    
    def calculate_trend_strength(self, symbol: str) -> float:
        """Calculate trend strength based on recent estimates"""
        if symbol not in self.trend_estimates or len(self.trend_estimates[symbol]) < 5:
            return 0.0
        
        recent_trends = self.trend_estimates[symbol][-5:]
        trend_consistency = np.std(recent_trends)  # Lower std = more consistent trend
        trend_magnitude = abs(np.mean(recent_trends))
        
        # Trend strength is combination of consistency and magnitude
        trend_strength = trend_magnitude * (1 - trend_consistency)
        
        return min(trend_strength, 1.0)
    
    def predict_price_movement(self, symbol: str, current_price: float) -> Tuple[str, float, float]:
        """Predict price movement direction and confidence"""
        # Update Kalman filter
        estimated_price, uncertainty = self.update_kalman_filter(symbol, current_price)
        
        # Calculate prediction error
        prediction_error = abs(current_price - estimated_price) / current_price
        
        # Calculate volatility
        volatility = self.calculate_volatility(self.price_history[symbol])
        
        # Calculate trend strength
        trend_strength = self.calculate_trend_strength(symbol)
        
        # Determine signal direction
        price_diff = estimated_price - current_price
        price_diff_pct = price_diff / current_price
        
        if abs(price_diff_pct) < self.prediction_threshold:
            return "HOLD", 0.0, 0.0
        
        # Calculate confidence based on multiple factors
        confidence = 0.0
        
        # Base confidence from prediction error (lower error = higher confidence)
        error_confidence = max(0, 1 - prediction_error * 10)
        
        # Volatility adjustment (lower volatility = higher confidence)
        volatility_confidence = max(0, 1 - volatility * 5)
        
        # Trend strength contribution
        trend_confidence = trend_strength
        
        # Uncertainty adjustment (lower uncertainty = higher confidence)
        uncertainty_confidence = max(0, 1 - uncertainty / current_price)
        
        # Combine confidence factors
        confidence = (error_confidence * 0.3 + 
                     volatility_confidence * 0.2 + 
                     trend_confidence * 0.3 + 
                     uncertainty_confidence * 0.2)
        
        confidence = min(confidence, 0.95)
        
        # Determine action
        if price_diff_pct > self.prediction_threshold:
            action = "BUY"
        elif price_diff_pct < -self.prediction_threshold:
            action = "SELL"
        else:
            action = "HOLD"
        
        return action, confidence, price_diff_pct
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Kalman filter-based trading signal"""
        
        if len(data) < 10:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Predict price movement
        action, confidence, price_diff_pct = self.predict_price_movement(symbol, current_price)
        
        # Only generate signal if confidence meets threshold
        if confidence < self.confidence_threshold or action == "HOLD":
            return None
        
        # Get Kalman filter estimates
        estimated_price, uncertainty = self.kalman_filters[symbol].get_estimate()
        trend_strength = self.calculate_trend_strength(symbol)
        volatility = self.calculate_volatility(self.price_history[symbol])
        
        signal = TradeSignal(
            symbol=symbol,
            action=action,
            quantity=self._calculate_quantity(current_price, confidence),
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'estimated_price': estimated_price,
                'price_diff_pct': price_diff_pct,
                'uncertainty': uncertainty,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'prediction_threshold': self.prediction_threshold,
                'signal_type': 'kalman_filter',
                'price_history_length': len(self.price_history.get(symbol, [])),
                'trend_estimates_length': len(self.trend_estimates.get(symbol, []))
            }
        )
        
        logger.info(f"Kalman Filter signal: {symbol} {action} "
                   f"(confidence: {confidence:.3f}, price_diff: {price_diff_pct:.3f}, "
                   f"trend_strength: {trend_strength:.3f})")
        
        return signal
    
    def _calculate_quantity(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_size = 1000  # Base position size
        return (base_size * confidence) / price
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "lookback_period": self.lookback_period,
            "prediction_threshold": self.prediction_threshold,
            "confidence_threshold": self.confidence_threshold,
            "volatility_window": self.volatility_window,
            "trend_strength_threshold": self.trend_strength_threshold,
            "active_filters": len(self.kalman_filters)
        }
    
    def get_filter_stats(self, symbol: str) -> Dict[str, Any]:
        """Get Kalman filter statistics for a symbol"""
        if symbol not in self.kalman_filters:
            return {}
        
        estimated_price, uncertainty = self.kalman_filters[symbol].get_estimate()
        trend_strength = self.calculate_trend_strength(symbol)
        volatility = self.calculate_volatility(self.price_history.get(symbol, []))
        
        return {
            'estimated_price': estimated_price,
            'uncertainty': uncertainty,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'price_history_length': len(self.price_history.get(symbol, [])),
            'trend_estimates_length': len(self.trend_estimates.get(symbol, []))
        } 