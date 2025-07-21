"""
Enhanced Timeout Handler for LLM Proxy System
Provides comprehensive timeout handling with fallbacks and monitoring
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TimeoutStrategy(Enum):
    """Timeout handling strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_RETRY = "fixed_retry"
    HEALTH_CHECK = "health_check"
    RATE_LIMIT = "rate_limit"
    FALLBACK = "fallback"


@dataclass
class TimeoutConfig:
    """Timeout configuration for different components"""
    client_timeout: int = 30
    service_timeout: int = 30
    ollama_timeout: float = 120.0
    proxy_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_delay: float = 300.0
    health_check_interval: int = 60
    rate_limit_window: int = 60
    cache_ttl: int = 300


@dataclass
class TimeoutMetrics:
    """Timeout metrics tracking"""
    total_timeouts: int = 0
    timeout_by_component: Dict[str, int] = field(default_factory=lambda: {
        'client': 0, 'service': 0, 'ollama': 0, 'proxy': 0
    })
    retry_success_rate: float = 0.0
    fallback_usage: int = 0
    average_timeout_duration: float = 0.0
    last_timeout: Optional[datetime] = None


class EnhancedTimeoutHandler:
    """Enhanced timeout handler with comprehensive fallback strategies"""
    
    def __init__(self, config: TimeoutConfig = None):
        self.config = config or TimeoutConfig()
        self.metrics = TimeoutMetrics()
        self.fallback_handlers: Dict[str, Callable] = {}
        self.timeout_callbacks: Dict[str, Callable] = {}
        
        logger.info(f"Enhanced Timeout Handler initialized with config: {self.config}")
    
    def register_fallback_handler(self, operation: str, handler: Callable):
        """Register a fallback handler for a specific operation"""
        self.fallback_handlers[operation] = handler
        logger.info(f"Registered fallback handler for operation: {operation}")
    
    def register_timeout_callback(self, component: str, callback: Callable):
        """Register a timeout callback for a specific component"""
        self.timeout_callbacks[component] = callback
        logger.info(f"Registered timeout callback for component: {component}")
    
    async def handle_timeout(self, 
                           component: str, 
                           operation: str, 
                           request_data: Dict[str, Any],
                           strategy: TimeoutStrategy = TimeoutStrategy.EXPONENTIAL_BACKOFF) -> Dict[str, Any]:
        """Handle timeout with appropriate strategy"""
        
        start_time = time.time()
        self.metrics.total_timeouts += 1
        self.metrics.timeout_by_component[component] += 1
        self.metrics.last_timeout = datetime.utcnow()
        
        logger.warning(f"⏰ Timeout detected for {component}/{operation}")
        
        try:
            # Execute timeout callback if registered
            if component in self.timeout_callbacks:
                await self.timeout_callbacks[component](operation, request_data)
            
            # Apply timeout strategy
            if strategy == TimeoutStrategy.EXPONENTIAL_BACKOFF:
                result = await self._exponential_backoff_retry(component, operation, request_data)
            elif strategy == TimeoutStrategy.FIXED_RETRY:
                result = await self._fixed_retry(component, operation, request_data)
            elif strategy == TimeoutStrategy.HEALTH_CHECK:
                result = await self._health_check_retry(component, operation, request_data)
            elif strategy == TimeoutStrategy.RATE_LIMIT:
                result = await self._rate_limit_retry(component, operation, request_data)
            elif strategy == TimeoutStrategy.FALLBACK:
                result = await self._fallback_strategy(component, operation, request_data)
            else:
                result = await self._generic_fallback(component, operation, request_data)
            
            # Update metrics
            duration = time.time() - start_time
            self._update_timeout_metrics(duration)
            
            logger.info(f"✅ Timeout handled successfully for {component}/{operation} in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Timeout handling failed for {component}/{operation}: {e}")
            return await self._emergency_fallback(component, operation, request_data)
    
    async def _exponential_backoff_retry(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exponential backoff retry strategy"""
        for attempt in range(self.config.max_retries):
            delay = min(self.config.retry_delay * (2 ** attempt), self.config.max_delay)
            logger.info(f"🔄 Retrying {component}/{operation} in {delay:.1f}s (attempt {attempt + 1})")
            
            await asyncio.sleep(delay)
            
            try:
                # Attempt the operation again
                result = await self._execute_operation(component, operation, request_data)
                self.metrics.retry_success_rate = (self.metrics.retry_success_rate + 1) / 2
                return result
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                continue
        
        # All retries failed, use fallback
        return await self._fallback_strategy(component, operation, request_data)
    
    async def _fixed_retry(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fixed retry strategy"""
        for attempt in range(self.config.max_retries):
            logger.info(f"🔄 Fixed retry for {component}/{operation} (attempt {attempt + 1})")
            
            try:
                result = await self._execute_operation(component, operation, request_data)
                return result
            except Exception as e:
                logger.warning(f"Fixed retry attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
        
        return await self._fallback_strategy(component, operation, request_data)
    
    async def _health_check_retry(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Health check retry strategy"""
        logger.info(f"🏥 Performing health check for {component}")
        
        # Simulate health check
        await asyncio.sleep(self.config.health_check_interval)
        
        try:
            result = await self._execute_operation(component, operation, request_data)
            return result
        except Exception as e:
            logger.error(f"Health check retry failed: {e}")
            return await self._fallback_strategy(component, operation, request_data)
    
    async def _rate_limit_retry(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rate limit retry strategy"""
        logger.info(f"⏳ Rate limit retry for {component}, waiting {self.config.rate_limit_window}s")
        
        await asyncio.sleep(self.config.rate_limit_window)
        
        try:
            result = await self._execute_operation(component, operation, request_data)
            return result
        except Exception as e:
            logger.error(f"Rate limit retry failed: {e}")
            return await self._fallback_strategy(component, operation, request_data)
    
    async def _fallback_strategy(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy using registered handlers"""
        self.metrics.fallback_usage += 1
        
        if operation in self.fallback_handlers:
            logger.info(f"🔄 Using fallback handler for {operation}")
            try:
                result = await self.fallback_handlers[operation](request_data)
                return result
            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")
        
        return await self._generic_fallback(component, operation, request_data)
    
    async def _generic_fallback(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic fallback response"""
        logger.warning(f"🔄 Using generic fallback for {component}/{operation}")
        
        return {
            'success': False,
            'error': 'timeout_fallback',
            'component': component,
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'confidence': 0.5,  # Neutral confidence
                'reason': 'LLM timeout - using fallback analysis',
                'recommendation': 'HOLD'  # Conservative recommendation
            }
        }
    
    async def _emergency_fallback(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Emergency fallback when all strategies fail"""
        logger.error(f"🚨 Emergency fallback for {component}/{operation}")
        
        return {
            'success': False,
            'error': 'emergency_fallback',
            'component': component,
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'confidence': 0.0,  # No confidence
                'reason': 'LLM service unavailable',
                'recommendation': 'SKIP'  # Skip this analysis
            }
        }
    
    async def _execute_operation(self, component: str, operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual operation (to be implemented by specific handlers)"""
        # This would be implemented by the specific LLM client
        raise NotImplementedError(f"Operation execution not implemented for {component}/{operation}")
    
    def _update_timeout_metrics(self, duration: float):
        """Update timeout metrics"""
        current_avg = self.metrics.average_timeout_duration
        total_timeouts = self.metrics.total_timeouts
        self.metrics.average_timeout_duration = (
            (current_avg * (total_timeouts - 1) + duration) / total_timeouts
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current timeout metrics"""
        return {
            'total_timeouts': self.metrics.total_timeouts,
            'timeout_by_component': self.metrics.timeout_by_component.copy(),
            'retry_success_rate': self.metrics.retry_success_rate,
            'fallback_usage': self.metrics.fallback_usage,
            'average_timeout_duration': self.metrics.average_timeout_duration,
            'last_timeout': self.metrics.last_timeout.isoformat() if self.metrics.last_timeout else None
        }
    
    def reset_metrics(self):
        """Reset timeout metrics"""
        self.metrics = TimeoutMetrics()
        logger.info("Timeout metrics reset")


# Pre-configured timeout handlers for common operations
class TradingTimeoutHandler(EnhancedTimeoutHandler):
    """Trading-specific timeout handler with pre-configured fallbacks"""
    
    def __init__(self, config: TimeoutConfig = None):
        super().__init__(config)
        self._setup_trading_fallbacks()
    
    def _setup_trading_fallbacks(self):
        """Setup trading-specific fallback handlers"""
        
        # Sentiment analysis fallback
        self.register_fallback_handler('sentiment', self._sentiment_fallback)
        
        # Signal evaluation fallback
        self.register_fallback_handler('signal', self._signal_fallback)
        
        # Risk assessment fallback
        self.register_fallback_handler('risk', self._risk_fallback)
        
        # Market analysis fallback
        self.register_fallback_handler('market', self._market_fallback)
    
    async def _sentiment_fallback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for sentiment analysis"""
        return {
            'success': True,
            'sentiment': 'neutral',
            'confidence': 0.5,
            'reason': 'LLM timeout - using neutral sentiment',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _signal_fallback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for signal evaluation"""
        return {
            'success': True,
            'signal': 'HOLD',
            'confidence': 0.5,
            'reason': 'LLM timeout - using conservative signal',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _risk_fallback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for risk assessment"""
        return {
            'success': True,
            'risk_level': 'medium',
            'confidence': 0.5,
            'reason': 'LLM timeout - using medium risk assessment',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _market_fallback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for market analysis"""
        return {
            'success': True,
            'market_outlook': 'neutral',
            'confidence': 0.5,
            'reason': 'LLM timeout - using neutral market outlook',
            'timestamp': datetime.utcnow().isoformat()
        } 