"""
Machine Learning Ensemble Strategy
=================================
A strategy that combines predictions from multiple ML models using weighted voting
for final trading decisions. Reduces overfitting and improves robustness.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class MLEnsembleStrategy(BaseStrategy):
    """
    Machine Learning Ensemble Strategy
    
    Features:
    - Multiple ML models (Random Forest, Gradient Boosting, Logistic Regression)
    - Ensemble voting with adaptive weights
    - Feature engineering from technical indicators
    - Model retraining based on performance
    - Confidence scoring from ensemble predictions
    """
    
    def __init__(self, 
                 name: str = "MLEnsemble",
                 lookback_period: int = 60,
                 prediction_horizon: int = 5,
                 min_confidence: float = 0.6,
                 retrain_frequency: int = 30,
                 model_weights: Dict[str, float] = None):
        super().__init__(name)
        self.lookback_period = lookback_period
        self.prediction_horizon = prediction_horizon
        self.min_confidence = min_confidence
        self.retrain_frequency = retrain_frequency
        self.model_weights = model_weights or {
            'random_forest': 0.4,
            'gradient_boosting': 0.35,
            'logistic_regression': 0.25
        }
        
        # ML models
        self.models = {}
        self.scaler = StandardScaler()
        self.last_retrain = None
        self.model_performance = {}
        self.feature_columns = []
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models"""
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        # Initialize performance tracking
        for model_name in self.models.keys():
            self.model_performance[model_name] = {
                'accuracy': 0.5,
                'recent_predictions': [],
                'last_update': None
            }
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features from technical indicators"""
        features = pd.DataFrame()
        
        if len(data) < 20:
            return features
        
        # Price-based features
        features['price_change_1d'] = data['Close'].pct_change(1)
        features['price_change_5d'] = data['Close'].pct_change(5)
        features['price_change_20d'] = data['Close'].pct_change(20)
        
        # Volume features
        features['volume_ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()
        features['volume_change'] = data['Volume'].pct_change()
        
        # Technical indicators
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        sma_20 = data['Close'].rolling(window=20).mean()
        std_20 = data['Close'].rolling(window=20).std()
        features['bb_upper'] = sma_20 + (std_20 * 2)
        features['bb_lower'] = sma_20 - (std_20 * 2)
        features['bb_position'] = (data['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        
        # Moving averages
        features['sma_20'] = data['Close'].rolling(window=20).mean()
        features['sma_50'] = data['Close'].rolling(window=50).mean()
        features['price_vs_sma20'] = data['Close'] / features['sma_20'] - 1
        features['price_vs_sma50'] = data['Close'] / features['sma_50'] - 1
        
        # Volatility
        features['volatility_20d'] = data['Close'].pct_change().rolling(window=20).std()
        
        # Remove NaN values
        features = features.dropna()
        
        return features
    
    def create_labels(self, data: pd.DataFrame) -> pd.Series:
        """Create binary labels for classification (1 for price increase, 0 for decrease)"""
        if len(data) < self.prediction_horizon + 1:
            return pd.Series()
        
        # Future price change
        future_returns = data['Close'].shift(-self.prediction_horizon) / data['Close'] - 1
        
        # Binary labels: 1 if price increases, 0 if decreases
        labels = (future_returns > 0).astype(int)
        
        return labels
    
    def should_retrain(self) -> bool:
        """Check if models should be retrained"""
        if self.last_retrain is None:
            return True
        
        days_since_retrain = (datetime.now() - self.last_retrain).days
        return days_since_retrain >= self.retrain_frequency
    
    async def train_models(self, market_data: Dict[str, pd.DataFrame]):
        """Train all ML models"""
        logger.info("Training ML ensemble models...")
        
        # Prepare training data
        all_features = []
        all_labels = []
        
        for symbol, data in market_data.items():
            if len(data) < self.lookback_period:
                continue
            
            features = self.create_features(data)
            labels = self.create_labels(data)
            
            if not features.empty and not labels.empty:
                # Align features and labels
                common_index = features.index.intersection(labels.index)
                if len(common_index) > 10:
                    all_features.append(features.loc[common_index])
                    all_labels.append(labels.loc[common_index])
        
        if not all_features:
            logger.warning("No sufficient data for training")
            return
        
        # Combine all data
        combined_features = pd.concat(all_features, axis=0)
        combined_labels = pd.concat(all_labels, axis=0)
        
        # Remove any remaining NaN values
        valid_mask = ~(combined_features.isna().any(axis=1) | combined_labels.isna())
        combined_features = combined_features[valid_mask]
        combined_labels = combined_labels[valid_mask]
        
        if len(combined_features) < 100:
            logger.warning("Insufficient data for training")
            return
        
        # Store feature columns
        self.feature_columns = combined_features.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            combined_features, combined_labels, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        for model_name, model in self.models.items():
            try:
                model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                train_score = model.score(X_train_scaled, y_train)
                test_score = model.score(X_test_scaled, y_test)
                
                # Update performance
                self.model_performance[model_name]['accuracy'] = test_score
                self.model_performance[model_name]['last_update'] = datetime.now()
                
                logger.info(f"Trained {model_name}: train_acc={train_score:.3f}, test_acc={test_score:.3f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
        
        self.last_retrain = datetime.now()
        logger.info("ML ensemble models training completed")
    
    def predict_ensemble(self, features: pd.DataFrame) -> Tuple[str, float]:
        """Get ensemble prediction and confidence"""
        if features.empty or len(features) < 1:
            return "HOLD", 0.0
        
        # Scale features
        features_scaled = self.scaler.transform(features.iloc[-1:])
        
        predictions = {}
        confidences = {}
        
        # Get predictions from each model
        for model_name, model in self.models.items():
            try:
                # Get prediction probability
                proba = model.predict_proba(features_scaled)[0]
                prediction = model.predict(features_scaled)[0]
                
                predictions[model_name] = prediction
                confidences[model_name] = max(proba)  # Confidence is max probability
                
            except Exception as e:
                logger.error(f"Error getting prediction from {model_name}: {e}")
                predictions[model_name] = 0
                confidences[model_name] = 0.5
        
        # Weighted voting
        weighted_votes = {'buy': 0.0, 'sell': 0.0}
        
        for model_name, prediction in predictions.items():
            weight = self.model_weights.get(model_name, 1.0)
            confidence = confidences.get(model_name, 0.5)
            
            if prediction == 1:  # Buy signal
                weighted_votes['buy'] += weight * confidence
            else:  # Sell signal
                weighted_votes['sell'] += weight * confidence
        
        # Determine final prediction
        if weighted_votes['buy'] > weighted_votes['sell']:
            action = "BUY"
            confidence = weighted_votes['buy'] / (weighted_votes['buy'] + weighted_votes['sell'])
        elif weighted_votes['sell'] > weighted_votes['buy']:
            action = "SELL"
            confidence = weighted_votes['sell'] / (weighted_votes['buy'] + weighted_votes['sell'])
        else:
            action = "HOLD"
            confidence = 0.5
        
        return action, confidence
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            market_data: Dict[str, pd.DataFrame] = None) -> Optional[TradeSignal]:
        """Generate ML ensemble trading signal"""
        
        if len(data) < self.lookback_period:
            return None
        
        # Retrain models if needed
        if self.should_retrain() and market_data:
            await self.train_models(market_data)
        
        # Create features
        features = self.create_features(data)
        
        if features.empty:
            return None
        
        # Get ensemble prediction
        action, confidence = self.predict_ensemble(features)
        
        # Only generate signal if confidence meets threshold
        if confidence < self.min_confidence or action == "HOLD":
            return None
        
        current_price = data['Close'].iloc[-1]
        
        signal = TradeSignal(
            symbol=symbol,
            action=action,
            quantity=self._calculate_quantity(current_price, confidence),
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'model_weights': self.model_weights,
                'model_performance': self.model_performance,
                'feature_count': len(self.feature_columns),
                'signal_type': 'ml_ensemble',
                'prediction_horizon': self.prediction_horizon,
                'last_retrain': self.last_retrain.isoformat() if self.last_retrain else None
            }
        )
        
        logger.info(f"ML Ensemble signal: {symbol} {action} (confidence: {confidence:.3f})")
        
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
            "prediction_horizon": self.prediction_horizon,
            "min_confidence": self.min_confidence,
            "model_weights": self.model_weights,
            "model_performance": self.model_performance,
            "last_retrain": self.last_retrain.isoformat() if self.last_retrain else None,
            "feature_count": len(self.feature_columns)
        }
    
    def save_models(self, filepath: str):
        """Save trained models to disk"""
        try:
            model_data = {
                'models': self.models,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'model_performance': self.model_performance,
                'model_weights': self.model_weights
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Models saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk"""
        try:
            if os.path.exists(filepath):
                model_data = joblib.load(filepath)
                self.models = model_data['models']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
                self.model_performance = model_data['model_performance']
                self.model_weights = model_data['model_weights']
                logger.info(f"Models loaded from {filepath}")
            else:
                logger.warning(f"Model file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading models: {e}") 