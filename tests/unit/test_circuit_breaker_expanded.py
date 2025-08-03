"""
Expanded unit tests for circuit breaker - covering untested functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.utils.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitBreakerManager,
    CircuitBreakerOpenError,
    CircuitBreakerConfigs,
    get_circuit_breaker_manager,
    circuit_breaker
)


class TestCircuitBreakerExpanded:
    """Expanded tests for CircuitBreaker covering untested functionality"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,
            success_threshold=2
        )
    
    @pytest.fixture
    def circuit_breaker(self, config):
        """Create circuit breaker instance"""
        return CircuitBreaker("test_cb", config)
    
    @pytest.mark.asyncio
    async def test_should_attempt_reset_no_failure(self, circuit_breaker):
        """Test _should_attempt_reset when no failure has occurred"""
        # No failure time set
        assert circuit_breaker._should_attempt_reset() is False
    
    @pytest.mark.asyncio
    async def test_should_attempt_reset_before_timeout(self, circuit_breaker):
        """Test _should_attempt_reset before recovery timeout"""
        # Set failure time to recent
        circuit_breaker.last_failure_time = datetime.now()
        assert circuit_breaker._should_attempt_reset() is False
    
    @pytest.mark.asyncio
    async def test_should_attempt_reset_after_timeout(self, circuit_breaker):
        """Test _should_attempt_reset after recovery timeout"""
        # Set failure time to old
        circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=2)
        assert circuit_breaker._should_attempt_reset() is True
    
    @pytest.mark.asyncio
    async def test_set_open_from_closed(self, circuit_breaker):
        """Test setting circuit to open from closed state"""
        assert circuit_breaker.state.value == "CLOSED"
        circuit_breaker._set_open()
        assert circuit_breaker.state.value == "OPEN"
        assert circuit_breaker.stats['circuit_opens'] == 1
    
    @pytest.mark.asyncio
    async def test_set_open_already_open(self, circuit_breaker):
        """Test setting circuit to open when already open"""
        circuit_breaker._set_open()
        initial_opens = circuit_breaker.stats['circuit_opens']
        circuit_breaker._set_open()  # Should not increment again
        assert circuit_breaker.stats['circuit_opens'] == initial_opens
    
    @pytest.mark.asyncio
    async def test_set_half_open(self, circuit_breaker):
        """Test setting circuit to half-open state"""
        circuit_breaker._set_half_open()
        assert circuit_breaker.state.value == "HALF_OPEN"
        assert circuit_breaker.success_count == 0
    
    @pytest.mark.asyncio
    async def test_set_closed(self, circuit_breaker):
        """Test setting circuit to closed state"""
        # First open it
        circuit_breaker._set_open()
        assert circuit_breaker.state.value == "OPEN"
        
        # Then close it
        circuit_breaker._set_closed()
        assert circuit_breaker.state.value == "CLOSED"
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.success_count == 0
        assert circuit_breaker.stats['circuit_closes'] == 1
    
    @pytest.mark.asyncio
    async def test_get_stats_basic(self, circuit_breaker):
        """Test getting basic statistics"""
        stats = circuit_breaker.get_stats()
        
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'failed_requests' in stats
        assert 'circuit_opens' in stats
        assert 'circuit_closes' in stats
        assert 'fast_failures' in stats
        assert 'state' in stats
        assert 'failure_count' in stats
        assert 'success_count' in stats
        assert 'success_rate' in stats
        assert 'last_failure_time' in stats
        assert 'last_state_change' in stats
        assert 'time_in_state' in stats
    
    @pytest.mark.asyncio
    async def test_get_stats_with_requests(self, circuit_breaker):
        """Test statistics with actual requests"""
        # Make some requests
        async def success_func():
            return "success"
        
        async def fail_func():
            raise ValueError("test error")
        
        # Successful request
        await circuit_breaker.call(success_func)
        
        # Failed request
        with pytest.raises(ValueError):
            await circuit_breaker.call(fail_func)
        
        stats = circuit_breaker.get_stats()
        
        assert stats['total_requests'] == 2
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 1
        assert stats['success_rate'] == 50.0
    
    @pytest.mark.asyncio
    async def test_reset_manual(self, circuit_breaker):
        """Test manual reset of circuit breaker"""
        # Open the circuit
        circuit_breaker._set_open()
        assert circuit_breaker.state.value == "OPEN"
        
        # Reset it
        circuit_breaker.reset()
        assert circuit_breaker.state.value == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_on_success_in_half_open(self, circuit_breaker):
        """Test successful execution in half-open state"""
        # Set to half-open
        circuit_breaker._set_half_open()
        circuit_breaker.success_count = 1  # One success already
        
        # Simulate another success
        circuit_breaker._on_success()
        
        # Should close the circuit and reset success_count
        assert circuit_breaker.state.value == "CLOSED"
        assert circuit_breaker.success_count == 0  # Implementation resets to 0
    
    @pytest.mark.asyncio
    async def test_on_failure_in_half_open(self, circuit_breaker):
        """Test failure in half-open state"""
        # Set to half-open
        circuit_breaker._set_half_open()
        
        # Simulate failure
        circuit_breaker._on_failure()
        
        # Should open the circuit
        assert circuit_breaker.state.value == "OPEN"
    
    @pytest.mark.asyncio
    async def test_on_failure_threshold_reached(self, circuit_breaker):
        """Test failure threshold being reached"""
        # Set failure count to threshold
        circuit_breaker.failure_count = 2  # One less than threshold (3)
        
        # Simulate failure
        circuit_breaker._on_failure()
        
        # Should open the circuit
        assert circuit_breaker.state.value == "OPEN"
        assert circuit_breaker.failure_count == 3


class TestCircuitBreakerManager:
    """Tests for CircuitBreakerManager"""
    
    @pytest.fixture
    def manager(self):
        """Create circuit breaker manager"""
        return CircuitBreakerManager()
    
    def test_get_circuit_breaker_new(self, manager):
        """Test getting a new circuit breaker"""
        cb = manager.get_circuit_breaker("test_cb")
        
        assert isinstance(cb, CircuitBreaker)
        assert cb.name == "test_cb"
        assert "test_cb" in manager.circuit_breakers
    
    def test_get_circuit_breaker_existing(self, manager):
        """Test getting an existing circuit breaker"""
        cb1 = manager.get_circuit_breaker("test_cb")
        cb2 = manager.get_circuit_breaker("test_cb")
        
        assert cb1 is cb2  # Same instance
    
    def test_get_circuit_breaker_with_config(self, manager):
        """Test getting circuit breaker with custom config"""
        config = CircuitBreakerConfig(failure_threshold=10)
        cb = manager.get_circuit_breaker("test_cb", config)
        
        assert cb.config.failure_threshold == 10
    
    def test_get_all_stats_empty(self, manager):
        """Test getting stats when no circuit breakers exist"""
        stats = manager.get_all_stats()
        assert stats == {}
    
    def test_get_all_stats_with_breakers(self, manager):
        """Test getting stats with multiple circuit breakers"""
        cb1 = manager.get_circuit_breaker("cb1")
        cb2 = manager.get_circuit_breaker("cb2")
        
        stats = manager.get_all_stats()
        
        assert "cb1" in stats
        assert "cb2" in stats
        assert isinstance(stats["cb1"], dict)
        assert isinstance(stats["cb2"], dict)


class TestCircuitBreakerConfigs:
    """Tests for predefined circuit breaker configurations"""
    
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


class TestCircuitBreakerDecorator:
    """Tests for circuit breaker decorator"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker decorator with successful function"""
        @circuit_breaker("test_decorator")
        async def success_func():
            return "success"
        
        result = await success_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker decorator with failing function"""
        @circuit_breaker("test_decorator_fail")
        async def fail_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await fail_func()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_with_config(self):
        """Test circuit breaker decorator with custom config"""
        config = CircuitBreakerConfig(failure_threshold=1)
        
        @circuit_breaker("test_decorator_config", config)
        async def fail_func():
            raise ValueError("test error")
        
        # First failure should open circuit
        with pytest.raises(ValueError):
            await fail_func()
        
        # Second call should fail fast
        with pytest.raises(Exception):  # Should be CircuitBreakerOpenError
            await fail_func()


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_async_function(self):
        """Test circuit breaker with async function"""
        cb = CircuitBreaker("test_async")
        
        async def async_func():
            return "async_result"
        
        result = await cb.call(async_func)
        assert result == "async_result"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Sync function support not implemented yet; see TODO in code")
    async def test_circuit_breaker_with_sync_function(self):
        """Test circuit breaker with sync function (potential improvement)"""
        # TODO: Implement support for sync functions in CircuitBreaker.call
        cb = CircuitBreaker("test_sync")
        def sync_func():
            return "sync_result"
        result = await cb.call(sync_func)
        assert result == "sync_result"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_arguments(self):
        """Test circuit breaker with function arguments"""
        cb = CircuitBreaker("test_args")
        
        async def func_with_args(a, b, c=None):
            return f"{a}_{b}_{c}"
        
        result = await cb.call(func_with_args, "x", "y", c="z")
        assert result == "x_y_z"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_cycle(self):
        """Test complete circuit breaker recovery cycle"""
        cb = CircuitBreaker("test_recovery", CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1,
            success_threshold=1
        ))
        
        # Function that fails twice then succeeds
        call_count = 0
        
        async def unreliable_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("temporary failure")
            return "success"
        
        # First two calls should fail
        with pytest.raises(ValueError):
            await cb.call(unreliable_func)
        with pytest.raises(ValueError):
            await cb.call(unreliable_func)
        
        # Circuit should be open
        assert cb.state.value == "OPEN"
        
        # Wait for recovery
        await asyncio.sleep(1.1)
        
        # Next call should succeed and close circuit
        result = await cb.call(unreliable_func)
        assert result == "success"
        assert cb.state.value == "CLOSED"


class TestCircuitBreakerErrorHandling:
    """Tests for circuit breaker error handling"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError is raised when circuit is open"""
        cb = CircuitBreaker("test_open_error", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60
        ))
        
        async def fail_func():
            raise ValueError("test error")
        
        # First call fails and opens circuit
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        # Second call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail_func)
    
    @pytest.mark.asyncio
    async def test_custom_exception_type(self):
        """Test circuit breaker with custom exception type"""
        cb = CircuitBreaker("test_custom_exception", CircuitBreakerConfig(
            failure_threshold=1,
            expected_exception=ConnectionError
        ))
        
        async def connection_error_func():
            raise ConnectionError("connection failed")
        
        async def value_error_func():
            raise ValueError("value error")
        
        # ConnectionError should count as failure
        with pytest.raises(ConnectionError):
            await cb.call(connection_error_func)
        
        assert cb.state.value == "OPEN"
        
        # Reset for next test
        cb.reset()
        
        # ValueError should not count as failure (different exception type)
        with pytest.raises(ValueError):
            await cb.call(value_error_func)
        
        assert cb.state.value == "CLOSED"  # Should still be closed 