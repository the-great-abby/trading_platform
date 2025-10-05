"""
Elliott Wave Strategy for Backtesting
Integrates with the Elliott Wave service to generate trading signals
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class ElliottWaveImpulseStrategy(BaseStrategy):
    """
    Elliott Wave Impulse Strategy
    
    Uses the Elliott Wave service to detect impulse patterns and generate signals
    """
    
    def __init__(self, 
                 name: str = "ElliottWaveImpulseStrategy",
                 elliott_service_url: str = "http://localhost:11082",
                 confidence_threshold: float = 0.6,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.elliott_service_url = elliott_service_url
        self.confidence_threshold = confidence_threshold
        self.pattern_cache = {}
        
    async def analyze_elliott_wave_pattern(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze Elliott Wave pattern using the service"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d')}"
            if cache_key in self.pattern_cache:
                return self.pattern_cache[cache_key]
            
            # Call Elliott Wave service
            url = f"{self.elliott_service_url}/elliott-wave/analyze/{symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache the result
            self.pattern_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing Elliott Wave pattern for {symbol}: {e}")
            return None
    
    def is_impulse_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """Check if the pattern is an impulse pattern"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return False
        
        pattern_type = pattern_data.get('pattern_type', '').lower()
        return 'impulse' in pattern_type or 'trending' in pattern_type
    
    def calculate_signal_confidence(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate signal confidence based on pattern strength"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return 0.0
        
        # Base confidence from pattern strength
        confidence = pattern_data.get('confidence', 0.0)
        
        # Boost confidence for impulse patterns
        if self.is_impulse_pattern(pattern_data):
            confidence *= 1.2
        
        return min(confidence, 1.0)
    
    def get_signal_direction(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """Determine signal direction based on pattern"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return None
        
        pattern_direction = pattern_data.get('direction', '').lower()
        
        if pattern_direction in ['bullish', 'up', 'rising']:
            return 'BUY'
        elif pattern_direction in ['bearish', 'down', 'falling']:
            return 'SELL'
        
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave impulse trading signal"""
        
        if len(data) < 50:  # Need sufficient data for Elliott Wave analysis
            return None
        
        # Analyze Elliott Wave pattern
        pattern_data = await self.analyze_elliott_wave_pattern(symbol)
        
        if not pattern_data:
            return None
        
        # Check if it's an impulse pattern
        if not self.is_impulse_pattern(pattern_data):
            return None
        
        # Calculate confidence
        confidence = self.calculate_signal_confidence(pattern_data)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Get signal direction
        action = self.get_signal_direction(pattern_data)
        
        if not action:
            return None
        
        # Calculate position size
        current_price = data['Close'].iloc[-1]
        quantity = self.calculate_position_size(current_price, confidence)
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_data.get('pattern_type', 'unknown'),
                'direction': pattern_data.get('direction', 'unknown'),
                'confidence': confidence,
                'analysis_time': pattern_data.get('analysis_time', 0)
            }
        )

class ElliottWaveCorrectiveStrategy(BaseStrategy):
    """
    Elliott Wave Corrective Strategy
    
    Uses the Elliott Wave service to detect corrective patterns and generate signals
    """
    
    def __init__(self, 
                 name: str = "ElliottWaveCorrectiveStrategy",
                 elliott_service_url: str = "http://localhost:11082",
                 confidence_threshold: float = 0.6,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.elliott_service_url = elliott_service_url
        self.confidence_threshold = confidence_threshold
        self.pattern_cache = {}
        
    async def analyze_elliott_wave_pattern(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze Elliott Wave pattern using the service"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d')}"
            if cache_key in self.pattern_cache:
                return self.pattern_cache[cache_key]
            
            # Call Elliott Wave service
            url = f"{self.elliott_service_url}/elliott-wave/analyze/{symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache the result
            self.pattern_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing Elliott Wave pattern for {symbol}: {e}")
            return None
    
    def is_corrective_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """Check if the pattern is a corrective pattern"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return False
        
        pattern_type = pattern_data.get('pattern_type', '').lower()
        return 'corrective' in pattern_type or 'sideways' in pattern_type or 'range' in pattern_type
    
    def calculate_signal_confidence(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate signal confidence based on pattern strength"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return 0.0
        
        # Base confidence from pattern strength
        confidence = pattern_data.get('confidence', 0.0)
        
        # Boost confidence for corrective patterns
        if self.is_corrective_pattern(pattern_data):
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def get_signal_direction(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """Determine signal direction based on corrective pattern"""
        if not pattern_data or not pattern_data.get('pattern_found', False):
            return None
        
        # For corrective patterns, we typically look for mean reversion
        pattern_direction = pattern_data.get('direction', '').lower()
        
        # Corrective patterns often signal reversals
        if pattern_direction in ['bullish', 'up', 'rising']:
            return 'SELL'  # Expect correction down
        elif pattern_direction in ['bearish', 'down', 'falling']:
            return 'BUY'   # Expect correction up
        
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave corrective trading signal"""
        
        if len(data) < 50:  # Need sufficient data for Elliott Wave analysis
            return None
        
        # Analyze Elliott Wave pattern
        pattern_data = await self.analyze_elliott_wave_pattern(symbol)
        
        if not pattern_data:
            return None
        
        # Check if it's a corrective pattern
        if not self.is_corrective_pattern(pattern_data):
            return None
        
        # Calculate confidence
        confidence = self.calculate_signal_confidence(pattern_data)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Get signal direction
        action = self.get_signal_direction(pattern_data)
        
        if not action:
            return None
        
        # Calculate position size
        current_price = data['Close'].iloc[-1]
        quantity = self.calculate_position_size(current_price, confidence)
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_data.get('pattern_type', 'unknown'),
                'direction': pattern_data.get('direction', 'unknown'),
                'confidence': confidence,
                'analysis_time': pattern_data.get('analysis_time', 0)
            }
        )
