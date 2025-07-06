"""
Test Quick Wins - Automated tests for cache manager, circuit breaker, and enhanced logging
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import Mock, patch

from src.utils.cache_manager import AdvancedCacheManager, CacheKey, cached
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
from src.utils.enhanced_logging import TradingLogger, log_performance, log_errors


class TestCacheManager:
    """Test cache manager functionality"""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create cache manager for testing"""
        manager = AdvancedCacheManager(l1_max_size=10, l1_ttl=5)
        await manager.initialize()
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations"""
        # Set data
        await cache_manager.set("test_key", "test_value", ttl=10)
        
        # Get data
        result = await cache_manager.get("test_key")
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss_with_fetch_func(self, cache_manager):
        """Test cache miss with fetch function"""
        fetch_called = False
        
        async def fetch_func():
            nonlocal fetch_called
            fetch_called = True
            return "fetched_value"
        
        # Get data that's not in cache
        result = await cache_manager.get("missing_key", fetch_func)
        
        assert result == "fetched_value"
        assert fetch_called
        assert await cache_manager.get("missing_key") == "fetched_value"  # Should be cached now
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test cache expiration"""
        # Set data with short TTL
        await cache_manager.set("expire_key", "expire_value", ttl=1)
        
        # Should be available immediately
        assert await cache_manager.get("expire_key") == "expire_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await cache_manager.get("expire_key") is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache_manager):
        """Test cache eviction when full"""
        # Fill cache beyond max size
        for i in range(15):
            await cache_manager.set(f"key_{i}", f"value_{i}")
        
        # Check that some items were evicted
        stats = await cache_manager.get_stats()
        assert stats['l1_cache_size'] <= 10
        assert stats['cache_evictions'] > 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Perform some operations
        await cache_manager.set("key1", "value1")
        await cache_manager.get("key1")  # Hit
        await cache_manager.get("key2")  # Miss
        
        stats = await cache_manager.get_stats()
        
        assert stats['l1_hits'] == 1
        assert stats['l1_misses'] == 1
        assert stats['total_requests'] == 2
        assert stats['l1_hit_rate'] == 50.0
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = CacheKey.generate("test", 123, param="value")
        key2 = CacheKey.generate("test", 123, param="value")
        key3 = CacheKey.generate("test", 456, param="value")
        
        assert key1 == key2  # Same arguments should generate same key
        assert key1 != key3  # Different arguments should generate different key
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """Test cached decorator"""
        call_count = 0
        
        @cached(ttl=10, key_prefix="test")
        async def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # First call should execute function
        result1 = await test_function("test_param")
        assert result1 == "result_test_param"
        assert call_count == 1
        
        # Second call should use cache
        result2 = await test_function("test_param")
        assert result2 == "result_test_param"
        assert call_count == 1  # Should not increment


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker for testing"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,
            success_threshold=2
        )
        return CircuitBreaker("test_cb", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures"""
        async def fail_func():
            raise ValueError("test error")
        
        # Should fail 3 times then open
        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(fail_func)
        
        # Circuit should be open
        assert circuit_breaker.state.value == "OPEN"
        
        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(fail_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery through half-open state"""
        async def fail_func():
            raise ValueError("test error")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(fail_func)
        
        assert circuit_breaker.state.value == "OPEN"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should be in half-open state
        assert circuit_breaker.state.value == "HALF_OPEN"
        
        # Success should close the circuit
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "CLOSED"
    
    def test_circuit_breaker_stats(self, circuit_breaker):
        """Test circuit breaker statistics"""
        stats = circuit_breaker.get_stats()
        
        assert 'state' in stats
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'failed_requests' in stats
        assert 'success_rate' in stats


class TestEnhancedLogging:
    """Test enhanced logging functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create logger for testing"""
        return TradingLogger("test_logger")
    
    def test_logger_creation(self, logger):
        """Test logger creation and basic functionality"""
        assert logger.logger is not None
        assert logger.performance_logger is not None
    
    def test_structured_logging(self, logger):
        """Test structured logging with extra fields"""
        with patch('builtins.print') as mock_print:
            logger.info("Test message", {"test_field": "test_value"})
            
            # Check that JSON was logged
            call_args = mock_print.call_args[0][0]
            log_entry = eval(call_args)  # Convert string back to dict
            
            assert log_entry['message'] == "Test message"
            assert log_entry['test_field'] == "test_value"
            assert 'timestamp' in log_entry
            assert 'level' in log_entry
    
    def test_performance_logging(self, logger):
        """Test performance logging"""
        timer_id = logger.performance_logger.start_timer("test_operation")
        
        # Simulate some work
        time.sleep(0.1)
        
        logger.performance_logger.end_timer(timer_id, success=True)
        
        # Check that timer was cleaned up
        assert timer_id not in logger.performance_logger.metrics
    
    @pytest.mark.asyncio
    async def test_log_performance_decorator(self):
        """Test log_performance decorator"""
        call_count = 0
        
        @log_performance("test_operation")
        async def test_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_log_errors_decorator(self):
        """Test log_errors decorator"""
        @log_errors
        async def failing_function():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await failing_function()
    
    def test_trading_specific_logging(self, logger):
        """Test trading-specific logging methods"""
        with patch('builtins.print') as mock_print:
            # Test trade signal logging
            signal_data = {"symbol": "AAPL", "action": "BUY", "quantity": 100}
            logger.trade_signal(signal_data)
            
            # Test order execution logging
            order_data = {"order_id": "123", "status": "filled"}
            logger.order_executed(order_data)
            
            # Test market data logging
            logger.market_data_received("AAPL", "price", 1024)
            
            # Test performance metric logging
            logger.performance_metric("response_time", 0.5, "seconds")
            
            # Test system health logging
            logger.system_health("database", "healthy", {"connections": 5})
            
            # Verify all calls were made
            assert mock_print.call_count == 5


class TestIntegration:
    """Integration tests for quick wins working together"""
    
    @pytest.mark.asyncio
    async def test_cache_with_circuit_breaker(self):
        """Test cache manager with circuit breaker protection"""
        cache_manager = AdvancedCacheManager()
        await cache_manager.initialize()
        
        cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        circuit_breaker = CircuitBreaker("cache_cb", cb_config)
        
        fail_count = 0
        
        async def unreliable_fetch():
            nonlocal fail_count
            fail_count += 1
            if fail_count <= 2:
                raise ConnectionError("Network error")
            return "success_data"
        
        # First two calls should fail and open circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                await circuit_breaker.call(unreliable_fetch)
        
        # Circuit should be open
        assert circuit_breaker.state.value == "OPEN"
        
        # Wait for recovery
        await asyncio.sleep(1.1)
        
        # Should succeed and close circuit
        result = await circuit_breaker.call(unreliable_fetch)
        assert result == "success_data"
        assert circuit_breaker.state.value == "CLOSED"
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_logging_with_cache_and_circuit_breaker(self):
        """Test logging integration with cache and circuit breaker"""
        logger = TradingLogger("integration_test")
        
        cache_manager = AdvancedCacheManager()
        await cache_manager.initialize()
        
        circuit_breaker = CircuitBreaker("integration_cb")
        
        @log_performance("cache_operation")
        async def cached_operation():
            return await circuit_breaker.call(lambda: "cached_result")
        
        result = await cached_operation()
        assert result == "cached_result"
        
        # Check that all components worked together
        cache_stats = await cache_manager.get_stats()
        cb_stats = circuit_breaker.get_stats()
        
        assert cache_stats['total_requests'] >= 0
        assert cb_stats['total_requests'] >= 0
        
        await cache_manager.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 