"""
Error handling and retry logic for external database connectivity

This service provides robust error handling and retry mechanisms for
database connectivity and other external service interactions.
"""

import asyncio
import logging
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if datetime.now() < self.next_attempt_time:
                raise Exception(f"Circuit breaker is OPEN. Next attempt at {self.next_attempt_time}")
            else:
                self.state = CircuitBreakerState.HALF_OPEN
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
        self.next_attempt_time = None
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = datetime.now() + timedelta(seconds=self.config.recovery_timeout)
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryHandler:
    """
    Retry handler with configurable strategies and circuit breaker integration.
    """
    
    def __init__(self, retry_config: RetryConfig, circuit_breaker: Optional[CircuitBreaker] = None):
        self.retry_config = retry_config
        self.circuit_breaker = circuit_breaker
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic and optional circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                if self.circuit_breaker:
                    result = await self.circuit_breaker.call(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Function succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Don't retry on last attempt
                if attempt == self.retry_config.max_attempts - 1:
                    break
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"Function failed after {self.retry_config.max_attempts} attempts")
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if self.retry_config.strategy == RetryStrategy.FIXED:
            delay = self.retry_config.base_delay
        elif self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = self.retry_config.base_delay * (attempt + 1)
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.retry_config.base_delay * (self.retry_config.backoff_multiplier ** attempt)
        else:
            delay = self.retry_config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            import random
            jitter = random.uniform(0.0, delay * 0.1)
            delay += jitter
        
        return delay


class DatabaseRetryHandler:
    """
    Specialized retry handler for database operations.
    """
    
    def __init__(self):
        # Database-specific retry configuration
        self.retry_config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_multiplier=2.0,
            jitter=True
        )
        
        # Circuit breaker for database connectivity
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=60.0,
                expected_exception=Exception
            )
        )
        
        self.retry_handler = RetryHandler(self.retry_config, self.circuit_breaker)
    
    async def execute_query(self, query_func: Callable, *args, **kwargs) -> Any:
        """
        Execute database query with retry logic.
        
        Args:
            query_func: Database query function
            *args: Query arguments
            **kwargs: Query keyword arguments
            
        Returns:
            Query result
        """
        try:
            return await self.retry_handler.execute_with_retry(query_func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database query failed after retries: {e}")
            raise
    
    async def execute_transaction(self, transaction_func: Callable, *args, **kwargs) -> Any:
        """
        Execute database transaction with retry logic.
        
        Args:
            transaction_func: Database transaction function
            *args: Transaction arguments
            **kwargs: Transaction keyword arguments
            
        Returns:
            Transaction result
        """
        try:
            return await self.retry_handler.execute_with_retry(transaction_func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database transaction failed after retries: {e}")
            raise
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status information."""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "last_failure_time": self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None,
            "next_attempt_time": self.circuit_breaker.next_attempt_time.isoformat() if self.circuit_breaker.next_attempt_time else None
        }


class ErrorHandler:
    """
    Central error handling service for the validation framework.
    """
    
    def __init__(self):
        self.database_retry_handler = DatabaseRetryHandler()
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    async def handle_database_error(self, error: Exception, operation: str) -> None:
        """
        Handle database-related errors.
        
        Args:
            error: Exception that occurred
            operation: Database operation that failed
        """
        error_key = f"database_{operation}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "database",
            "operation": operation,
            "error": str(error),
            "error_class": type(error).__name__
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"Database error in {operation}: {error}")
    
    async def handle_validation_error(self, error: Exception, script_id: str) -> None:
        """
        Handle validation-related errors.
        
        Args:
            error: Exception that occurred
            script_id: ID of script that failed validation
        """
        error_key = f"validation_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "validation",
            "script_id": script_id,
            "error": str(error),
            "error_class": type(error).__name__
        }
        
        self.error_history.append(error_record)
        
        logger.error(f"Validation error for script {script_id}: {error}")
    
    async def handle_execution_error(self, error: Exception, script_id: str) -> None:
        """
        Handle script execution errors.
        
        Args:
            error: Exception that occurred
            script_id: ID of script that failed execution
        """
        error_key = f"execution_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "execution",
            "script_id": script_id,
            "error": str(error),
            "error_class": type(error).__name__
        }
        
        self.error_history.append(error_record)
        
        logger.error(f"Execution error for script {script_id}: {error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error statistics."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts,
            "recent_errors": self.error_history[-10:],  # Last 10 errors
            "circuit_breaker_status": self.database_retry_handler.get_circuit_breaker_status()
        }
    
    def clear_error_history(self) -> None:
        """Clear error history and counts."""
        self.error_counts.clear()
        self.error_history.clear()
        logger.info("Error history cleared")











