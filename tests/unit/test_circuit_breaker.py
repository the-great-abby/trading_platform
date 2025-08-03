#!/usr/bin/env python3
"""
Tests for Circuit Breaker Pattern
Comprehensive test suite for fault tolerance and cascading failure prevention
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from src.utils.circuit_breaker import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerManager,
    get_circuit_breaker_manager,
    circuit_breaker,
    CircuitBreakerConfigs
)


class TestCircuitState:
    """Test CircuitState enum"""
    
    def test_circuit_state_values(self):
        """Test circuit state enum values"""
        assert CircuitState.CLOSED.value == "CLOSED"
        assert CircuitState.OPEN.value == "OPEN"
        assert CircuitState.HALF_OPEN.value == "HALF_OPEN"
    
    def test_circuit_state_membership(self):
        """Test circuit state enum membership"""
        assert CircuitState.CLOSED in CircuitState
        assert CircuitState.OPEN in CircuitState
        assert CircuitState.HALF_OPEN in CircuitState


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass"""
    
    def test_circuit_breaker_config_defaults(self):
        """Test circuit breaker config default values"""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.expected_exception == Exception
        assert config.success_threshold == 2
    
    def test_circuit_breaker_config_custom_values(self):
        """Test circuit breaker config with custom values"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            expected_exception=ValueError,
            success_threshold=3
        )
        
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120
        assert config.expected_exception == ValueError
        assert config.success_threshold == 3


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,  # 1 second for faster tests
            success_threshold=2
        )
        self.circuit_breaker = CircuitBreaker("test_circuit", self.config)
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization"""
        assert self.circuit_breaker.name == "test_circuit"
        assert self.circuit_breaker.config == self.config
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0
        assert self.circuit_breaker.last_failure_time is None
    
    def test_circuit_breaker_stats_initialization(self):
        """Test circuit breaker statistics initialization"""
        stats = self.circuit_breaker.stats
        
        assert stats['total_requests'] == 0
        assert stats['successful_requests'] == 0
        assert stats['failed_requests'] == 0
        assert stats['circuit_opens'] == 0
        assert stats['circuit_closes'] == 0
        assert stats['fast_failures'] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_call(self):
        """Test successful function call"""
        async def successful_func():
            return "success"
        
        result = await self.circuit_breaker.call(successful_func)
        
        assert result == "success"
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.stats['successful_requests'] == 1
        assert self.circuit_breaker.stats['total_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failed_call(self):
        """Test failed function call"""
        async def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError, match="test error"):
            await self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 1
        assert self.circuit_breaker.stats['failed_requests'] == 1
        assert self.circuit_breaker.stats['total_requests'] == 1
        assert self.circuit_breaker.last_failure_time is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold"""
        async def failing_func():
            raise ValueError("test error")
        
        # Fail multiple times to reach threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == CircuitState.OPEN
        assert self.circuit_breaker.stats['circuit_opens'] == 1
        assert self.circuit_breaker.stats['failed_requests'] == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fast_failure_when_open(self):
        """Test circuit breaker fails fast when open"""
        # First, open the circuit
        async def failing_func():
            raise ValueError("test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == CircuitState.OPEN
        
        # Now try to call a function - should fail fast
        async def successful_func():
            return "success"
        
        with pytest.raises(CircuitBreakerOpenError):
            await self.circuit_breaker.call(successful_func)
        
        assert self.circuit_breaker.stats['fast_failures'] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker transitions to half-open after timeout"""
        # Open the circuit
        async def failing_func():
            raise ValueError("test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)  # Slightly more than 1 second timeout
        
        # Try to call a function - should transition to half-open
        async def successful_func():
            return "success"
        
        result = await self.circuit_breaker.call(successful_func)
        
        assert result == "success"
        assert self.circuit_breaker.state == CircuitState.HALF_OPEN
        assert self.circuit_breaker.success_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_success_threshold(self):
        """Test circuit breaker closes after success threshold in half-open state"""
        # Open the circuit
        async def failing_func():
            raise ValueError("test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Succeed multiple times to reach threshold
        async def successful_func():
            return "success"
        
        for _ in range(2):
            result = await self.circuit_breaker.call(successful_func)
            assert result == "success"
        
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.stats['circuit_closes'] == 1
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reopens_on_failure_in_half_open(self):
        """Test circuit breaker reopens on failure in half-open state"""
        # Open the circuit
        async def failing_func():
            raise ValueError("test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Fail again - should reopen
        with pytest.raises(ValueError):
            await self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == CircuitState.OPEN
        assert self.circuit_breaker.stats['circuit_opens'] == 2
    
    def test_should_attempt_reset(self):
        """Test should attempt reset logic"""
        # Initially should not attempt reset
        assert not self.circuit_breaker._should_attempt_reset()
        
        # Set a recent failure time
        self.circuit_breaker.last_failure_time = datetime.now()
        assert not self.circuit_breaker._should_attempt_reset()
        
        # Set an old failure time
        self.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=2)
        assert self.circuit_breaker._should_attempt_reset()
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        stats = self.circuit_breaker.get_stats()
        
        assert 'state' in stats
        assert 'failure_count' in stats
        assert 'success_count' in stats
        assert 'success_rate' in stats
        assert 'last_failure_time' in stats
        assert 'last_state_change' in stats
        assert 'time_in_state' in stats
        assert stats['state'] == 'CLOSED'
        assert stats['success_rate'] == 0.0  # No requests yet
    
    def test_manual_reset(self):
        """Test manual reset functionality"""
        # Set to open state
        self.circuit_breaker._set_open()
        assert self.circuit_breaker.state == CircuitState.OPEN
        
        # Manually reset
        self.circuit_breaker.reset()
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0
    
    @pytest.mark.asyncio
    async def test_unexpected_exception_does_not_count_as_failure(self):
        """Test that unexpected exceptions don't count as failures"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            expected_exception=ValueError
        )
        cb = CircuitBreaker("test", config)
        
        async def func_raising_type_error():
            raise TypeError("unexpected error")
        
        # This should not count as a failure
        with pytest.raises(TypeError):
            await cb.call(func_raising_type_error)
        
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager class"""
    
    def setup_method(self):
        """Setup test method"""
        self.manager = CircuitBreakerManager()
    
    def test_circuit_breaker_manager_initialization(self):
        """Test circuit breaker manager initialization"""
        assert self.manager.circuit_breakers == {}
    
    def test_get_circuit_breaker_creates_new(self):
        """Test getting a new circuit breaker"""
        cb = self.manager.get_circuit_breaker("test_circuit")
        
        assert isinstance(cb, CircuitBreaker)
        assert cb.name == "test_circuit"
        assert "test_circuit" in self.manager.circuit_breakers
    
    def test_get_circuit_breaker_returns_existing(self):
        """Test getting an existing circuit breaker"""
        cb1 = self.manager.get_circuit_breaker("test_circuit")
        cb2 = self.manager.get_circuit_breaker("test_circuit")
        
        assert cb1 is cb2  # Same instance
    
    def test_get_circuit_breaker_with_config(self):
        """Test getting circuit breaker with custom config"""
        config = CircuitBreakerConfig(failure_threshold=10)
        cb = self.manager.get_circuit_breaker("test_circuit", config)
        
        assert cb.config.failure_threshold == 10
    
    def test_get_all_stats(self):
        """Test getting statistics for all circuit breakers"""
        # Create multiple circuit breakers
        cb1 = self.manager.get_circuit_breaker("circuit1")
        cb2 = self.manager.get_circuit_breaker("circuit2")
        
        stats = self.manager.get_all_stats()
        
        assert "circuit1" in stats
        assert "circuit2" in stats
        assert stats["circuit1"]["state"] == "CLOSED"
        assert stats["circuit2"]["state"] == "CLOSED"
    
    def test_reset_all(self):
        """Test resetting all circuit breakers"""
        # Create circuit breakers and open them
        cb1 = self.manager.get_circuit_breaker("circuit1")
        cb2 = self.manager.get_circuit_breaker("circuit2")
        
        cb1._set_open()
        cb2._set_open()
        
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.OPEN
        
        # Reset all
        self.manager.reset_all()
        
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED


class TestGlobalCircuitBreakerManager:
    """Test global circuit breaker manager functionality"""
    
    def test_get_circuit_breaker_manager_singleton(self):
        """Test that get_circuit_breaker_manager returns singleton"""
        manager1 = get_circuit_breaker_manager()
        manager2 = get_circuit_breaker_manager()
        
        assert manager1 is manager2
    
    def test_global_manager_functionality(self):
        """Test global manager functionality"""
        manager = get_circuit_breaker_manager()
        cb = manager.get_circuit_breaker("global_test")
        
        assert isinstance(cb, CircuitBreaker)
        assert cb.name == "global_test"


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker decorator with success"""
        @circuit_breaker("decorator_test")
        async def test_func():
            return "decorated_success"
        
        result = await test_func()
        
        assert result == "decorated_success"
        
        # Check that circuit breaker was created
        manager = get_circuit_breaker_manager()
        cb = manager.get_circuit_breaker("decorator_test")
        assert cb.stats['successful_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker decorator with failure"""
        @circuit_breaker("decorator_failure_test")
        async def test_func():
            raise ValueError("decorated_failure")
        
        with pytest.raises(ValueError, match="decorated_failure"):
            await test_func()
        
        # Check that circuit breaker was created
        manager = get_circuit_breaker_manager()
        cb = manager.get_circuit_breaker("decorator_failure_test")
        assert cb.stats['failed_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_with_config(self):
        """Test circuit breaker decorator with custom config"""
        config = CircuitBreakerConfig(failure_threshold=1)
        
        @circuit_breaker("decorator_config_test", config)
        async def test_func():
            raise ValueError("test")
        
        # First failure should open circuit
        with pytest.raises(ValueError):
            await test_func()
        
        # Second call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()


class TestCircuitBreakerConfigs:
    """Test predefined circuit breaker configurations"""
    
    def test_conservative_config(self):
        """Test conservative configuration"""
        config = CircuitBreakerConfigs.CONSERVATIVE
        
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 120
        assert config.success_threshold == 3
    
    def test_balanced_config(self):
        """Test balanced configuration"""
        config = CircuitBreakerConfigs.BALANCED
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.success_threshold == 2
    
    def test_aggressive_config(self):
        """Test aggressive configuration"""
        config = CircuitBreakerConfigs.AGGRESSIVE
        
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 30
        assert config.success_threshold == 1
    
    def test_market_data_config(self):
        """Test market data configuration"""
        config = CircuitBreakerConfigs.MARKET_DATA
        
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 30
        assert config.success_threshold == 1
    
    def test_trading_config(self):
        """Test trading configuration"""
        config = CircuitBreakerConfigs.TRADING
        
        assert config.failure_threshold == 2
        assert config.recovery_timeout == 300
        assert config.success_threshold == 5


class TestCircuitBreakerEdgeCases:
    """Test circuit breaker edge cases"""
    
    def test_circuit_breaker_with_zero_failure_threshold(self):
        """Test circuit breaker with zero failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=0)
        cb = CircuitBreaker("test", config)
        
        assert cb.config.failure_threshold == 0
    
    def test_circuit_breaker_with_zero_success_threshold(self):
        """Test circuit breaker with zero success threshold"""
        config = CircuitBreakerConfig(success_threshold=0)
        cb = CircuitBreaker("test", config)
        
        assert cb.config.success_threshold == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_very_short_timeout(self):
        """Test circuit breaker with very short recovery timeout"""
        config = CircuitBreakerConfig(
            failure_threshold=2,  # Low threshold to open quickly
            recovery_timeout=0.1  # Very short timeout
        )
        cb = CircuitBreaker("test", config)
        
        # Open the circuit
        async def failing_func():
            raise ValueError("test")
        
        for _ in range(2):  # Only need 2 failures with this config
            with pytest.raises(ValueError):
                await cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery
        await asyncio.sleep(0.2)
        
        # Should be able to attempt reset
        assert cb._should_attempt_reset()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_access(self):
        """Test circuit breaker with concurrent access"""
        cb = CircuitBreaker("concurrent_test")
        
        async def test_func():
            return "success"
        
        # Run multiple concurrent calls
        tasks = [cb.call(test_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all(result == "success" for result in results)
        assert cb.stats['successful_requests'] == 10


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_complete_circuit_breaker_cycle(self):
        """Test complete circuit breaker cycle: closed -> open -> half-open -> closed"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # Very short for testing
            success_threshold=2
        )
        cb = CircuitBreaker("cycle_test", config)
        
        # Start in closed state
        assert cb.state == CircuitState.CLOSED
        
        # Fail to open circuit
        async def failing_func():
            raise ValueError("test")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Succeed to close circuit
        async def successful_func():
            return "success"
        
        for _ in range(2):
            result = await cb.call(successful_func)
            assert result == "success"
        
        assert cb.state == CircuitState.CLOSED
        assert cb.stats['circuit_opens'] == 1
        assert cb.stats['circuit_closes'] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_circuit_breakers_independence(self):
        """Test that multiple circuit breakers operate independently"""
        cb1 = CircuitBreaker("independent1")
        cb2 = CircuitBreaker("independent2")
        
        # Open first circuit breaker
        async def failing_func():
            raise ValueError("test")
        
        for _ in range(5):
            with pytest.raises(ValueError):
                await cb1.call(failing_func)
        
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.CLOSED
        
        # Second circuit breaker should still work
        async def successful_func():
            return "success"
        
        result = await cb2.call(successful_func)
        assert result == "success" 