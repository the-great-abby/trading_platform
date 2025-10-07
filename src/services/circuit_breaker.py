#!/usr/bin/env python3
"""
Enhanced Circuit Breaker Implementation
Provides robust circuit breaker functionality for service calls
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Enhanced circuit breaker with exponential backoff and health monitoring"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception,
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution"""
        self.total_calls += 1
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("🔄 Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record a successful call"""
        self.total_successes += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("✅ Circuit breaker CLOSED - service recovered")
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        self.total_failures += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"🚫 Circuit breaker OPEN - {self.failure_count} failures")
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("🚫 Circuit breaker OPEN - failure in half-open state")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure >= timedelta(seconds=self.recovery_timeout)
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection"""
        if not self.can_execute():
            raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise e
        except Exception as e:
            self.record_failure()
            raise e

class ServiceHealthMonitor:
    """Monitor service health and provide metrics"""
    
    def __init__(self):
        self.service_metrics = {}
        self.health_check_interval = 60  # seconds
        self.last_health_check = {}
    
    def record_success(self, service_name: str):
        """Record a successful service call"""
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'last_success': None,
                'last_failure': None,
                'average_response_time': 0.0
            }
        
        metrics = self.service_metrics[service_name]
        metrics['total_calls'] += 1
        metrics['successful_calls'] += 1
        metrics['last_success'] = datetime.now()
    
    def record_failure(self, service_name: str, error: str):
        """Record a failed service call"""
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'last_success': None,
                'last_failure': None,
                'average_response_time': 0.0
            }
        
        metrics = self.service_metrics[service_name]
        metrics['total_calls'] += 1
        metrics['failed_calls'] += 1
        metrics['last_failure'] = datetime.now()
        
        logger.warning(f"❌ Service {service_name} failed: {error}")
    
    def get_service_health(self, service_name: str) -> dict:
        """Get health metrics for a service"""
        if service_name not in self.service_metrics:
            return {'status': 'unknown', 'metrics': {}}
        
        metrics = self.service_metrics[service_name]
        success_rate = metrics['successful_calls'] / metrics['total_calls'] if metrics['total_calls'] > 0 else 0
        
        return {
            'status': 'healthy' if success_rate > 0.8 else 'unhealthy',
            'success_rate': success_rate,
            'metrics': metrics
        }
    
    def get_all_service_health(self) -> dict:
        """Get health metrics for all services"""
        return {service: self.get_service_health(service) for service in self.service_metrics.keys()}
