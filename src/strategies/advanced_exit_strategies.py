"""
Advanced Exit Strategies
=======================
Additional sophisticated exit strategies for enhanced trading performance:
- Momentum-based exits
- Volatility-based exits
- Correlation-based exits
- Machine learning exits
- Options-based exits
- Market regime exits
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from .exit_strategies import ExitSignal, ExitReason
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class MomentumExitStrategy:
    """Exit strategy based on momentum indicators and trend strength"""
    
    def __init__(self, 
                 momentum_period: int = 10,
                 trend_period: int = 20,
                 momentum_threshold: float = 0.02,
                 trend_strength_threshold: float = 0.05):
        self.momentum_period = momentum_period
        self.trend_period = trend_period
        self.momentum_threshold = momentum_threshold
        self.trend_strength_threshold = trend_strength_threshold
    
    def calculate_momentum(self, prices: pd.Series) -> pd.Series:
        """Calculate price momentum"""
        return prices.pct_change(periods=self.momentum_period)
    
    def calculate_trend_strength(self, prices: pd.Series) -> pd.Series:
        """Calculate trend strength using linear regression"""
        trend_strength = pd.Series(index=prices.index, dtype=float)
        
        for i in range(self.trend_period, len(prices)):
            window_prices = prices.iloc[i-self.trend_period:i+1]
            x = np.arange(len(window_prices))
            y = window_prices.values
            
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            r_squared = np.corrcoef(x, y)[0, 1] ** 2
            
            # Trend strength is slope * R-squared
            trend_strength.iloc[i] = slope * r_squared
        
        return trend_strength
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on momentum and trend strength"""
        
        if len(data) < self.trend_period:
            return None
        
        current_price = data['Close'].iloc[-1]
        momentum = self.calculate_momentum(data['Close']).iloc[-1]
        trend_strength = self.calculate_trend_strength(data['Close']).iloc[-1]
        
        # Exit conditions
        exit_signals = []
        
        # Momentum reversal
        if position_type == "LONG" and momentum < -self.momentum_threshold:
            exit_signals.append(("MOMENTUM_REVERSAL", 0.7))
        elif position_type == "SHORT" and momentum > self.momentum_threshold:
            exit_signals.append(("MOMENTUM_REVERSAL", 0.7))
        
        # Trend strength decline
        if abs(trend_strength) < self.trend_strength_threshold:
            exit_signals.append(("TREND_WEAKNESS", 0.6))
        
        # Price action confirmation
        price_change = (current_price - entry_price) / entry_price
        if position_type == "LONG" and price_change < -0.03:  # 3% loss
            exit_signals.append(("PRICE_DECLINE", 0.8))
        elif position_type == "SHORT" and price_change > 0.03:  # 3% loss
            exit_signals.append(("PRICE_RISE", 0.8))
        
        # Combine signals
        if len(exit_signals) >= 2:
            total_confidence = sum(conf for _, conf in exit_signals) / len(exit_signals)
            
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=min(total_confidence, 0.9),
                reason=ExitReason.MOMENTUM_LOSS,
                metadata={
                    'momentum': momentum,
                    'trend_strength': trend_strength,
                    'exit_signals': exit_signals,
                    'price_change': price_change
                }
            )
        
        return None

class VolatilityExitStrategy:
    """Exit strategy based on volatility regime changes"""
    
    def __init__(self, 
                 volatility_period: int = 20,
                 volatility_threshold: float = 0.03,
                 regime_change_threshold: float = 0.5):
        self.volatility_period = volatility_period
        self.volatility_threshold = volatility_threshold
        self.regime_change_threshold = regime_change_threshold
    
    def calculate_volatility(self, prices: pd.Series) -> pd.Series:
        """Calculate rolling volatility"""
        return prices.pct_change().rolling(window=self.volatility_period).std()
    
    def detect_volatility_regime_change(self, volatility: pd.Series) -> bool:
        """Detect significant volatility regime change"""
        if len(volatility) < 10:
            return False
        
        current_vol = volatility.iloc[-1]
        avg_vol = volatility.rolling(window=10).mean().iloc[-1]
        
        # Regime change if current volatility is significantly different
        return abs(current_vol - avg_vol) / avg_vol > self.regime_change_threshold
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on volatility regime changes"""
        
        if len(data) < self.volatility_period:
            return None
        
        current_price = data['Close'].iloc[-1]
        volatility = self.calculate_volatility(data['Close'])
        current_vol = volatility.iloc[-1]
        
        # Check for volatility regime change
        regime_change = self.detect_volatility_regime_change(volatility)
        
        # Exit conditions
        if regime_change:
            # High volatility regime - exit for risk management
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.8,
                reason=ExitReason.VOLUME_SPIKE,  # Using volume spike as proxy
                metadata={
                    'volatility_regime_change': True,
                    'current_volatility': current_vol,
                    'exit_reason': 'volatility_regime_change'
                }
            )
        
        # Extreme volatility exit
        if current_vol > self.volatility_threshold:
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.7,
                reason=ExitReason.VOLUME_SPIKE,
                metadata={
                    'extreme_volatility': True,
                    'volatility': current_vol,
                    'exit_reason': 'extreme_volatility'
                }
            )
        
        return None

class CorrelationExitStrategy:
    """Exit strategy based on correlation with market/sector indices"""
    
    def __init__(self, 
                 correlation_period: int = 30,
                 correlation_threshold: float = 0.7,
                 correlation_break_threshold: float = 0.3):
        self.correlation_period = correlation_period
        self.correlation_threshold = correlation_threshold
        self.correlation_break_threshold = correlation_break_threshold
    
    def calculate_correlation(self, prices: pd.Series, market_prices: pd.Series) -> float:
        """Calculate correlation with market"""
        if len(prices) < self.correlation_period or len(market_prices) < self.correlation_period:
            return 0.0
        
        # Use rolling correlation
        correlation = prices.rolling(window=self.correlation_period).corr(market_prices)
        return correlation.iloc[-1] if not pd.isna(correlation.iloc[-1]) else 0.0
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       market_data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on correlation breakdown"""
        
        if len(data) < self.correlation_period or len(market_data) < self.correlation_period:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Calculate correlation with market
        correlation = self.calculate_correlation(data['Close'], market_data['Close'])
        
        # Exit if correlation breaks down significantly
        if abs(correlation) < self.correlation_break_threshold:
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.7,
                reason=ExitReason.TREND_REVERSAL,
                metadata={
                    'correlation_breakdown': True,
                    'correlation': correlation,
                    'exit_reason': 'correlation_breakdown'
                }
            )
        
        # Exit if correlation becomes too high (stock following market too closely)
        if abs(correlation) > self.correlation_threshold:
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.6,
                reason=ExitReason.TREND_REVERSAL,
                metadata={
                    'high_correlation': True,
                    'correlation': correlation,
                    'exit_reason': 'high_correlation'
                }
            )
        
        return None

class MachineLearningExitStrategy:
    """Machine learning-based exit strategy"""
    
    def __init__(self, 
                 lookback_period: int = 60,
                 retrain_frequency: int = 30,
                 model_path: str = None):
        self.lookback_period = lookback_period
        self.retrain_frequency = retrain_frequency
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.last_retrain = None
        self.feature_columns = []
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML model"""
        features = pd.DataFrame()
        
        if len(data) < 20:
            return features
        
        # Technical indicators
        features['rsi'] = self._calculate_rsi(data['Close'])
        features['macd'] = self._calculate_macd(data['Close'])
        features['bb_position'] = self._calculate_bb_position(data['Close'])
        features['volume_ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()
        features['price_momentum'] = data['Close'].pct_change(5)
        features['volatility'] = data['Close'].pct_change().rolling(20).std()
        
        # Price action features
        features['price_change'] = (data['Close'] - data['Close'].shift(1)) / data['Close'].shift(1)
        features['high_low_ratio'] = (data['High'] - data['Low']) / data['Close']
        
        return features.dropna()
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        return macd - signal
    
    def _calculate_bb_position(self, prices: pd.Series) -> pd.Series:
        """Calculate Bollinger Band position"""
        sma = prices.rolling(window=20).mean()
        std = prices.rolling(window=20).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return (prices - lower) / (upper - lower)
    
    def train_model(self, historical_data: List[Tuple[pd.DataFrame, bool]]):
        """Train ML model on historical exit data"""
        if not historical_data:
            return
        
        features_list = []
        labels = []
        
        for data, should_exit in historical_data:
            features = self.create_features(data)
            if not features.empty:
                features_list.append(features.iloc[-1])
                labels.append(1 if should_exit else 0)
        
        if len(features_list) < 10:
            return
        
        # Prepare training data
        X = pd.DataFrame(features_list)
        y = np.array(labels)
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        
        self.last_retrain = datetime.now()
        logger.info(f"ML exit model trained on {len(X)} samples")
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get ML-based exit signal"""
        
        if self.model is None:
            return None
        
        # Create features
        features = self.create_features(data)
        if features.empty:
            return None
        
        # Get latest features
        latest_features = features.iloc[-1:][self.feature_columns]
        
        # Scale features
        features_scaled = self.scaler.transform(latest_features)
        
        # Get prediction
        exit_probability = self.model.predict_proba(features_scaled)[0][1]
        
        # Exit if probability is high
        if exit_probability > 0.7:
            current_price = data['Close'].iloc[-1]
            
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=exit_probability,
                reason=ExitReason.MULTI_SIGNAL,
                metadata={
                    'ml_exit_probability': exit_probability,
                    'exit_reason': 'ml_prediction'
                }
            )
        
        return None
    
    def save_model(self, filepath: str):
        """Save trained model"""
        if self.model is not None:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, filepath)
            logger.info(f"ML exit model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            logger.info(f"ML exit model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")

class OptionsBasedExitStrategy:
    """Exit strategy based on options market signals"""
    
    def __init__(self, 
                 put_call_ratio_threshold: float = 1.5,
                 implied_volatility_threshold: float = 0.4,
                 options_volume_threshold: float = 2.0):
        self.put_call_ratio_threshold = put_call_ratio_threshold
        self.implied_volatility_threshold = implied_volatility_threshold
        self.options_volume_threshold = options_volume_threshold
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       options_data: Dict[str, Any],
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on options market data"""
        
        if not options_data:
            return None
        
        current_price = data['Close'].iloc[-1]
        exit_signals = []
        
        # Put-Call ratio analysis
        put_call_ratio = options_data.get('put_call_ratio', 1.0)
        if put_call_ratio > self.put_call_ratio_threshold:
            # High put-call ratio indicates bearish sentiment
            if position_type == "LONG":
                exit_signals.append(("HIGH_PUT_CALL_RATIO", 0.7))
        
        # Implied volatility analysis
        implied_vol = options_data.get('implied_volatility', 0.3)
        if implied_vol > self.implied_volatility_threshold:
            # High IV indicates expected volatility
            exit_signals.append(("HIGH_IMPLIED_VOLATILITY", 0.6))
        
        # Options volume analysis
        options_volume_ratio = options_data.get('options_volume_ratio', 1.0)
        if options_volume_ratio > self.options_volume_threshold:
            # High options volume indicates institutional activity
            exit_signals.append(("HIGH_OPTIONS_VOLUME", 0.5))
        
        # Combine signals
        if len(exit_signals) >= 2:
            total_confidence = sum(conf for _, conf in exit_signals) / len(exit_signals)
            
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=min(total_confidence, 0.9),
                reason=ExitReason.VOLUME_SPIKE,
                metadata={
                    'options_signals': exit_signals,
                    'put_call_ratio': put_call_ratio,
                    'implied_volatility': implied_vol,
                    'options_volume_ratio': options_volume_ratio
                }
            )
        
        return None

class MarketRegimeExitStrategy:
    """Exit strategy based on market regime changes"""
    
    def __init__(self, 
                 regime_period: int = 50,
                 volatility_threshold: float = 0.03,
                 trend_threshold: float = 0.02):
        self.regime_period = regime_period
        self.volatility_threshold = volatility_threshold
        self.trend_threshold = trend_threshold
    
    def detect_market_regime(self, data: pd.DataFrame) -> str:
        """Detect current market regime"""
        if len(data) < self.regime_period:
            return "UNKNOWN"
        
        # Calculate market characteristics
        returns = data['Close'].pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1]
        trend = (data['Close'].iloc[-1] - data['Close'].iloc[-self.regime_period]) / data['Close'].iloc[-self.regime_period]
        
        # Classify regime
        if volatility > self.volatility_threshold:
            if trend > self.trend_threshold:
                return "HIGH_VOL_TRENDING_UP"
            elif trend < -self.trend_threshold:
                return "HIGH_VOL_TRENDING_DOWN"
            else:
                return "HIGH_VOL_SIDEWAYS"
        else:
            if trend > self.trend_threshold:
                return "LOW_VOL_TRENDING_UP"
            elif trend < -self.trend_threshold:
                return "LOW_VOL_TRENDING_DOWN"
            else:
                return "LOW_VOL_SIDEWAYS"
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on market regime changes"""
        
        current_regime = self.detect_market_regime(data)
        current_price = data['Close'].iloc[-1]
        
        # Exit conditions based on regime
        exit_conditions = {
            "HIGH_VOL_TRENDING_DOWN": position_type == "LONG",
            "HIGH_VOL_SIDEWAYS": True,  # Exit in high volatility sideways
            "LOW_VOL_TRENDING_UP": position_type == "SHORT",
            "LOW_VOL_TRENDING_DOWN": position_type == "LONG"
        }
        
        if exit_conditions.get(current_regime, False):
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.7,
                reason=ExitReason.TREND_REVERSAL,
                metadata={
                    'market_regime': current_regime,
                    'exit_reason': 'market_regime_change'
                }
            )
        
        return None 