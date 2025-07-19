"""
Circuit Breaker Pattern - Prevents cascading failures and protects the system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Circuit is open, requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Number of failures before opening
    recovery_timeout: int = 60        # Seconds to wait before half-open
    expected_exception: type = Exception  # Exception type to count as failure
    success_threshold: int = 2        # Successes needed to close circuit


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'circuit_opens': 0,
            'circuit_closes': 0,
            'fast_failures': 0
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            Exception: Original function exception
        """
        self.stats['total_requests'] += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                self.stats['fast_failures'] += 1
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            if isinstance(e, self.config.expected_exception):
                self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful execution"""
        self.stats['successful_requests'] += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._set_closed()
    
    def _on_failure(self):
        """Handle failed execution"""
        self.stats['failed_requests'] += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self._set_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._set_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return False
        
        return datetime.now() - self.last_failure_time >= timedelta(seconds=self.config.recovery_timeout)
    
    def _set_open(self):
        """Set circuit to open state"""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            self.stats['circuit_opens'] += 1
            logger.warning(f"Circuit breaker '{self.name}' is now OPEN")
    
    def _set_half_open(self):
        """Set circuit to half-open state"""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = datetime.now()
            self.success_count = 0
            logger.info(f"Circuit breaker '{self.name}' is now HALF-OPEN")
    
    def _set_closed(self):
        """Set circuit to closed state"""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
            self.failure_count = 0
            self.success_count = 0
            self.stats['circuit_closes'] += 1
            logger.info(f"Circuit breaker '{self.name}' is now CLOSED")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_requests'] / max(total_requests, 1)) * 100
        
        return {
            **self.stats,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'success_rate': success_rate,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_state_change': self.last_state_change.isoformat(),
            'time_in_state': (datetime.now() - self.last_state_change).total_seconds()
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self._set_closed()
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {
            name: cb.get_stats() 
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_circuit_breaker_manager()
            cb = manager.get_circuit_breaker(name, config)
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Predefined configurations
class CircuitBreakerConfigs:
    """Predefined circuit breaker configurations"""
    
    # Conservative - Opens quickly, recovers slowly
    CONSERVATIVE = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120,
        success_threshold=3
    )
    
    # Balanced - Default settings
    BALANCED = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        success_threshold=2
    )
    
    # Aggressive - Opens slowly, recovers quickly
    AGGRESSIVE = CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=30,
        success_threshold=1
    )
    
    # Market data specific - High tolerance for temporary failures
    MARKET_DATA = CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=30,
        success_threshold=1
    )
    
    # Trading specific - Low tolerance for failures
    TRADING = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=300,
        success_threshold=5
    ) 