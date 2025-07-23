"""
Neural Network Strategy
=======================

A deep learning-based trading strategy that uses neural networks
for pattern recognition, feature extraction, and signal generation.
This strategy leverages modern deep learning techniques for enhanced
trading performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class TradingDataset(Dataset):
    """Dataset for trading data"""
    
    def __init__(self, data: pd.DataFrame, sequence_length: int = 50):
        self.data = data
        self.sequence_length = sequence_length
        self.features = self._extract_features()
        self.labels = self._create_labels()
    
    def _extract_features(self) -> np.ndarray:
        """Extract features from market data"""
        
        # Technical indicators as features
        features = []
        
        # Price features
        features.append(self.data['Close'].pct_change().values)
        features.append(self.data['High'].pct_change().values)
        features.append(self.data['Low'].pct_change().values)
        
        # Volume features
        features.append(self.data['Volume'].pct_change().values)
        features.append((self.data['Volume'] / self.data['Volume'].rolling(20).mean()).values)
        
        # Technical indicators
        features.append(self._calculate_rsi().values)
        features.append(self._calculate_macd().values)
        features.append(self._calculate_bollinger_position().values)
        
        # Combine features
        feature_matrix = np.column_stack(features)
        
        # Handle NaN values
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0)
        
        return feature_matrix
    
    def _create_labels(self) -> np.ndarray:
        """Create labels for supervised learning"""
        
        # Future returns as labels
        future_returns = self.data['Close'].pct_change().shift(-1).values
        
        # Convert to classification labels
        labels = np.zeros(len(future_returns))
        labels[future_returns > 0.01] = 1  # Buy signal
        labels[future_returns < -0.01] = 2  # Sell signal
        # 0 = Hold
        
        return labels
    
    def _calculate_rsi(self) -> pd.Series:
        """Calculate RSI"""
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self) -> pd.Series:
        """Calculate MACD"""
        exp1 = self.data['Close'].ewm(span=12).mean()
        exp2 = self.data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        return macd
    
    def _calculate_bollinger_position(self) -> pd.Series:
        """Calculate position within Bollinger Bands"""
        sma = self.data['Close'].rolling(window=20).mean()
        std_dev = self.data['Close'].rolling(window=20).std()
        upper_band = sma + (std_dev * 2)
        lower_band = sma - (std_dev * 2)
        
        position = (self.data['Close'] - lower_band) / (upper_band - lower_band)
        return position
    
    def __len__(self):
        return len(self.data) - self.sequence_length
    
    def __getitem__(self, idx):
        # Get sequence of features
        features = self.features[idx:idx + self.sequence_length]
        label = self.labels[idx + self.sequence_length - 1]
        
        return torch.FloatTensor(features), torch.LongTensor([label])

class LSTMTradingModel(nn.Module):
    """LSTM-based trading model"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, num_classes: int = 3):
        super(LSTMTradingModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4)
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, num_classes)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.3)
        
        # Activation functions
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)
        
        # Apply attention
        lstm_out = lstm_out.transpose(0, 1)  # (seq_len, batch, hidden_size)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        attn_out = attn_out.transpose(0, 1)  # (batch, seq_len, hidden_size)
        
        # Take the last output
        out = attn_out[:, -1, :]
        
        # Fully connected layers
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return self.softmax(out)

class NeuralNetworkStrategy(BaseStrategy):
    """
    Neural Network Strategy
    
    Features:
    - LSTM-based sequence modeling
    - Attention mechanism for feature importance
    - Multi-class classification (Buy/Sell/Hold)
    - Online learning and model updates
    - Feature engineering and normalization
    - Confidence scoring and risk management
    """
    
    def __init__(self, 
                 sequence_length: int = 50,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 learning_rate: float = 0.001,
                 batch_size: int = 32,
                 min_confidence: float = 0.6,
                 **kwargs):
        super().__init__(name="Neural_Network_Strategy", **kwargs)
        
        # Model parameters
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.min_confidence = min_confidence
        
        # Model state
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.is_trained = False
        
        # Training history
        self.training_history = []
        self.validation_accuracy = 0.0
        
        # Initialize model if PyTorch is available
        if TORCH_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the neural network model"""
        
        # Input size (number of features)
        input_size = 8  # Price, volume, RSI, MACD, Bollinger, etc.
        
        # Create model
        self.model = LSTMTradingModel(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            num_classes=3  # Buy, Sell, Hold
        )
        
        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Loss function
        self.criterion = nn.CrossEntropyLoss()
        
        logger.info("✅ Neural network model initialized")
    
    def train_model(self, data: pd.DataFrame) -> bool:
        """Train the neural network model"""
        
        if not TORCH_AVAILABLE:
            logger.warning("⚠️  PyTorch not available, skipping training")
            return False
        
        if len(data) < self.sequence_length * 2:
            logger.warning("⚠️  Insufficient data for training")
            return False
        
        try:
            # Create dataset
            dataset = TradingDataset(data, self.sequence_length)
            
            if len(dataset) < self.batch_size:
                logger.warning("⚠️  Dataset too small for training")
                return False
            
            # Create data loader
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
            
            # Training loop
            self.model.train()
            total_loss = 0.0
            correct_predictions = 0
            total_predictions = 0
            
            for batch_features, batch_labels in dataloader:
                # Forward pass
                outputs = self.model(batch_features)
                loss = self.criterion(outputs, batch_labels.squeeze())
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                # Statistics
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total_predictions += batch_labels.size(0)
                correct_predictions += (predicted == batch_labels.squeeze()).sum().item()
            
            # Calculate accuracy
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
            avg_loss = total_loss / len(dataloader)
            
            # Store training history
            self.training_history.append({
                'loss': avg_loss,
                'accuracy': accuracy,
                'timestamp': datetime.now()
            })
            
            self.validation_accuracy = accuracy
            self.is_trained = True
            
            logger.info(f"✅ Model trained - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            return False
    
    def predict_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Predict trading signal using the neural network"""
        
        if not TORCH_AVAILABLE or not self.is_trained:
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'Model not available'}
        
        if len(data) < self.sequence_length:
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'Insufficient data'}
        
        try:
            # Prepare input data
            dataset = TradingDataset(data, self.sequence_length)
            
            if len(dataset) == 0:
                return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'No valid sequences'}
            
            # Get the most recent sequence
            features, _ = dataset[-1]
            features = features.unsqueeze(0)  # Add batch dimension
            
            # Make prediction
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(features)
                probabilities = outputs.squeeze().numpy()
            
            # Get prediction and confidence
            predicted_class = np.argmax(probabilities)
            confidence = np.max(probabilities)
            
            # Map class to action
            action_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            action = action_map.get(predicted_class, 'HOLD')
            
            return {
                'action': action,
                'confidence': confidence,
                'probabilities': probabilities,
                'predicted_class': predicted_class,
                'reason': f'Neural network prediction (class {predicted_class})'
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': f'Prediction error: {e}'}
    
    def update_model(self, new_data: pd.DataFrame) -> bool:
        """Update the model with new data"""
        
        if not TORCH_AVAILABLE:
            return False
        
        # Retrain model with new data
        return self.train_model(new_data)
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        
        if not self.training_history:
            return {'accuracy': 0.0, 'loss': 0.0, 'training_samples': 0}
        
        latest = self.training_history[-1]
        
        return {
            'accuracy': latest['accuracy'],
            'loss': latest['loss'],
            'training_samples': len(self.training_history),
            'last_training': latest['timestamp'].isoformat(),
            'is_trained': self.is_trained
        }
    
    def _extract_features_for_prediction(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features for prediction"""
        
        if len(data) < self.sequence_length:
            return np.array([])
        
        # Get the most recent sequence
        recent_data = data.tail(self.sequence_length)
        
        # Create dataset for feature extraction
        dataset = TradingDataset(recent_data, self.sequence_length)
        
        if len(dataset) == 0:
            return np.array([])
        
        # Get features
        features, _ = dataset[-1]
        return features.numpy()
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate neural network trading signal"""
        
        if not TORCH_AVAILABLE:
            logger.warning("⚠️  PyTorch not available for neural network strategy")
            return None
        
        # Train model if not trained
        if not self.is_trained:
            logger.info("🔄 Training neural network model...")
            if not self.train_model(data):
                return None
        
        # Get prediction
        prediction = self.predict_signal(data)
        
        # Check confidence threshold
        if prediction['confidence'] < self.min_confidence:
            return None
        
        # Generate trade signal
        current_price = data['Close'].iloc[-1]
        position_size = 0.05 * prediction['confidence']  # 5% base position
        quantity = (position_size * 10000) / current_price  # $10k base position
        
        # Prepare metadata
        metadata = {
            'strategy_name': self.name,
            'model_performance': self.get_model_performance(),
            'prediction': prediction,
            'sequence_length': self.sequence_length,
            'model_architecture': f'LSTM-{self.hidden_size}-{self.num_layers}',
            'signal_type': 'neural_network'
        }
        
        return TradeSignal(
            symbol=symbol,
            action=prediction['action'],
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=prediction['confidence'],
            metadata=metadata
        ) 