"""
Service-Based Elliott Wave Strategy

This strategy uses the actual Elliott Wave service for both live trading and backtesting.
It calls the Elliott Wave service API to get real pattern analysis.
"""

import pandas as pd
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.services.circuit_breaker import CircuitBreaker
from src.services.service_health_monitor import ServiceHealthMonitor

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


class ServiceBasedElliottWaveStrategy(BaseStrategy):
    """
    Elliott Wave Strategy that uses the actual Elliott Wave service
    
    This strategy calls the Elliott Wave service API to get real pattern analysis,
    making it suitable for both live trading and backtesting.
    """
    
    def __init__(self, 
                 name: str = "ServiceBasedElliottWaveStrategy",
                 service_url: str = "http://elliott-wave-service.trading-system.svc.cluster.local:8000",
                 confidence_threshold: float = 0.6,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        
        # Service resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
        self.service_health_monitor = ServiceHealthMonitor()
        self.service_url = service_url
        self.confidence_threshold = confidence_threshold
        
    async def _safe_service_call(self, service_name: str, call_func, *args, **kwargs):
        """Make a safe service call with circuit breaker protection"""
        try:
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.warning(f"🚫 Circuit breaker OPEN for {service_name}")
                return None
            
            # Make the call
            result = await call_func(*args, **kwargs)
            
            # Record success
            self.circuit_breaker.record_success()
            self.service_health_monitor.record_success(service_name)
            
            return result
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            self.service_health_monitor.record_failure(service_name, str(e))
            
            logger.error(f"❌ Service call failed for {service_name}: {e}")
            return None

    async def analyze_elliott_wave_pattern(self, symbol: str, historical_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze Elliott Wave pattern using the service"""
        try:
            if historical_date:
                # For backtesting - use the backtest endpoint
                url = f"{self.service_url}/elliott-wave/backtest/{symbol}"
                params = {
                    "historical_date": historical_date,
                    "timeframe": "1d"
                }
            else:
                # For live trading - use the regular endpoint
                url = f"{self.service_url}/elliott-wave/analyze/{symbol}"
                params = {
                    "timeframe": "1d"
                }
            
            logger.info(f"Calling Elliott Wave service: {url} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("pattern_found", False):
                logger.info(f"Elliott Wave pattern found for {symbol}: {result.get('pattern_type', 'unknown')} (confidence: {result.get('confidence', 0):.2f})")
                return result
            else:
                logger.debug(f"No Elliott Wave pattern found for {symbol}: {result.get('message', 'No pattern')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Elliott Wave service for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing Elliott Wave pattern for {symbol}: {e}")
            return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave trading signal using the service"""
        
        if len(data) < 20:  # Need sufficient data for analysis
            return None
        
        # Analyze Elliott Wave pattern using the service
        pattern_analysis = await self.analyze_elliott_wave_pattern(symbol, historical_date)
        
        if not pattern_analysis:
            return None
        
        # Check confidence threshold
        confidence = pattern_analysis.get('confidence', 0.0)
        if confidence < self.confidence_threshold:
            logger.debug(f"Confidence {confidence:.2f} below threshold {self.confidence_threshold} for {symbol}")
            return None
        
        # Determine signal direction based on pattern type
        pattern_type = pattern_analysis.get('pattern_type', '').lower()
        current_price = data['Close'].iloc[-1]
        
        # Map Elliott Wave patterns to trading signals
        if 'impulse' in pattern_type:
            # Impulse patterns suggest continuation of trend
            # For simplicity, we'll use the target price direction
            target_price = pattern_analysis.get('target_price', current_price)
            if target_price > current_price:
                action = 'BUY'
            else:
                action = 'SELL'
        elif 'corrective' in pattern_type:
            # Corrective patterns suggest reversal
            # For simplicity, we'll use the invalidation level direction
            invalidation_level = pattern_analysis.get('invalidation_level', current_price)
            if invalidation_level > current_price:
                action = 'SELL'  # Expecting downward correction
            else:
                action = 'BUY'   # Expecting upward correction
        else:
            # Unknown pattern type - skip
            logger.debug(f"Unknown pattern type: {pattern_type}")
            return None
        
        # Calculate position size with conservative risk management
        capital_allocation = 4000.0 * 0.95  # $3800 available (5% cash reserve)
        risk_percentage = min(0.20, confidence * 0.20)  # 20% max position size, scaled by confidence
        quantity = self.calculate_position_size(capital_allocation, current_price, risk_percentage)
        
        # Additional safety: limit maximum position size to 5% of capital
        max_shares = int(capital_allocation * 0.20 / current_price)  # 20% of capital max
        quantity = min(quantity, max_shares)
        
        # Ensure minimum viable position
        if quantity < 1:
            quantity = 1
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_type,
                'service_analysis': pattern_analysis,
                'target_price': pattern_analysis.get('target_price', 0.0),
                'invalidation_level': pattern_analysis.get('invalidation_level', 0.0),
                'fibonacci_levels': pattern_analysis.get('fibonacci_levels', []),
                'waves_count': len(pattern_analysis.get('waves', [])),
                'backtest_mode': historical_date is not None
            }
        )


class ServiceBasedElliottWaveImpulseStrategy(ServiceBasedElliottWaveStrategy):
    """
    Elliott Wave Impulse Strategy using the service
    
    Focuses specifically on impulse patterns for trend continuation trades.
    """
    
    def __init__(self, 
                 name: str = "ServiceBasedElliottWaveImpulseStrategy",
                 service_url: str = "http://elliott-wave-service.trading-system.svc.cluster.local:8000",
                 confidence_threshold: float = 0.7,  # Higher threshold for impulse patterns
                 **kwargs):
        super().__init__(name=name, service_url=service_url, confidence_threshold=confidence_threshold, **kwargs)
        
        # Service resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
        self.service_health_monitor = ServiceHealthMonitor()
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave impulse trading signal using the service"""
        
        if len(data) < 20:
            return None
        
        # Analyze Elliott Wave pattern using the service
        pattern_analysis = await self.analyze_elliott_wave_pattern(symbol, historical_date)
        
        if not pattern_analysis:
            return None
        
        # Only trade impulse patterns
        pattern_type = pattern_analysis.get('pattern_type', '').lower()
        if 'impulse' not in pattern_type:
            logger.debug(f"Not an impulse pattern for {symbol}: {pattern_type}")
            return None
        
        # Check confidence threshold
        confidence = pattern_analysis.get('confidence', 0.0)
        if confidence < self.confidence_threshold:
            logger.debug(f"Confidence {confidence:.2f} below threshold {self.confidence_threshold} for {symbol}")
            return None
        
        # Determine signal direction based on impulse pattern
        current_price = data['Close'].iloc[-1]
        target_price = pattern_analysis.get('target_price', current_price)
        
        if target_price > current_price:
            action = 'BUY'
        else:
            action = 'SELL'
        
        # Calculate position size with conservative risk management
        capital_allocation = 4000.0 * 0.95  # $3800 available (5% cash reserve)
        risk_percentage = min(0.003, confidence * 0.005)  # 0.3% max risk, scaled by confidence
        quantity = self.calculate_position_size(capital_allocation, current_price, risk_percentage)
        
        # Additional safety: limit maximum position size to 3% of capital
        max_shares = int(capital_allocation * 0.20 / current_price)  # 20% of capital max
        quantity = min(quantity, max_shares)
        
        # Ensure minimum viable position
        if quantity < 1:
            quantity = 1
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_type,
                'service_analysis': pattern_analysis,
                'target_price': target_price,
                'invalidation_level': pattern_analysis.get('invalidation_level', 0.0),
                'fibonacci_levels': pattern_analysis.get('fibonacci_levels', []),
                'waves_count': len(pattern_analysis.get('waves', [])),
                'backtest_mode': historical_date is not None,
                'impulse_pattern': True
            }
        )


class ServiceBasedElliottWaveCorrectiveStrategy(ServiceBasedElliottWaveStrategy):
    """
    Elliott Wave Corrective Strategy using the service
    
    Focuses specifically on corrective patterns for reversal trades.
    """
    
    def __init__(self, 
                 name: str = "ServiceBasedElliottWaveCorrectiveStrategy",
                 service_url: str = "http://elliott-wave-service.trading-system.svc.cluster.local:8000",
                 confidence_threshold: float = 0.6,  # Lower threshold for corrective patterns
                 **kwargs):
        super().__init__(name=name, service_url=service_url, confidence_threshold=confidence_threshold, **kwargs)
        
        # Service resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
        self.service_health_monitor = ServiceHealthMonitor()
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave corrective trading signal using the service"""
        
        if len(data) < 20:
            return None
        
        # Analyze Elliott Wave pattern using the service
        pattern_analysis = await self.analyze_elliott_wave_pattern(symbol, historical_date)
        
        if not pattern_analysis:
            return None
        
        # Only trade corrective patterns
        pattern_type = pattern_analysis.get('pattern_type', '').lower()
        if 'corrective' not in pattern_type:
            logger.debug(f"Not a corrective pattern for {symbol}: {pattern_type}")
            return None
        
        # Check confidence threshold
        confidence = pattern_analysis.get('confidence', 0.0)
        if confidence < self.confidence_threshold:
            logger.debug(f"Confidence {confidence:.2f} below threshold {self.confidence_threshold} for {symbol}")
            return None
        
        # Determine signal direction based on corrective pattern
        current_price = data['Close'].iloc[-1]
        invalidation_level = pattern_analysis.get('invalidation_level', current_price)
        
        # Corrective patterns suggest reversal
        if invalidation_level > current_price:
            action = 'SELL'  # Expecting downward correction
        else:
            action = 'BUY'   # Expecting upward correction
        
        # Calculate position size with conservative risk management
        capital_allocation = 4000.0 * 0.95  # $3800 available (5% cash reserve)
        risk_percentage = min(0.004, confidence * 0.008)  # 0.4% max risk, scaled by confidence
        quantity = self.calculate_position_size(capital_allocation, current_price, risk_percentage)
        
        # Additional safety: limit maximum position size to 4% of capital
        max_shares = int(capital_allocation * 0.04 / current_price)  # 4% of capital max
        quantity = min(quantity, max_shares)
        
        # Ensure minimum viable position
        if quantity < 1:
            quantity = 1
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_type,
                'service_analysis': pattern_analysis,
                'target_price': pattern_analysis.get('target_price', 0.0),
                'invalidation_level': invalidation_level,
                'fibonacci_levels': pattern_analysis.get('fibonacci_levels', []),
                'waves_count': len(pattern_analysis.get('waves', [])),
                'backtest_mode': historical_date is not None,
                'corrective_pattern': True
            }
        )
