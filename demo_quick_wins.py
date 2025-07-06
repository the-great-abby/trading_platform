#!/usr/bin/env python3
"""
Quick Wins Demo - Showcase the implemented improvements
"""

import asyncio
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.cache_manager import AdvancedCacheManager, cached
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfigs
from utils.enhanced_logging import TradingLogger, log_performance, log_errors


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_section(title: str):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_cache_manager():
    """Demo the advanced cache manager"""
    print_header("🚀 Advanced Cache Manager Demo")
    
    # Create cache manager
    cache_manager = AdvancedCacheManager(l1_max_size=5, l1_ttl=10)
    await cache_manager.initialize()
    
    print_section("Basic Cache Operations")
    
    # Set and get data
    await cache_manager.set("user_profile", {"name": "John", "balance": 10000}, ttl=30)
    profile = await cache_manager.get("user_profile")
    print(f"✅ Retrieved user profile: {profile}")
    
    # Cache miss with fetch function
    print_section("Cache Miss with Fetch Function")
    
    async def fetch_market_data():
        print("   📥 Fetching market data from external API...")
        await asyncio.sleep(0.5)  # Simulate API call
        return {"AAPL": 150.25, "GOOGL": 2800.50}
    
    # First call - should fetch from external source
    data1 = await cache_manager.get("market_data", fetch_market_data)
    print(f"   ✅ First call result: {data1}")
    
    # Second call - should use cache
    data2 = await cache_manager.get("market_data")
    print(f"   ⚡ Second call (cached): {data2}")
    
    # Cache statistics
    print_section("Cache Statistics")
    stats = await cache_manager.get_stats()
    print(f"   📊 Total requests: {stats['total_requests']}")
    print(f"   🎯 L1 hit rate: {stats['l1_hit_rate']:.1f}%")
    print(f"   📦 Cache size: {stats['l1_cache_size']}/{stats['l1_cache_max_size']}")
    print(f"   🗑️  Evictions: {stats['cache_evictions']}")
    
    # Cache decorator demo
    print_section("Cache Decorator")
    
    @cached(ttl=30, key_prefix="expensive_calculation")
    async def expensive_calculation(param):
        print(f"   🔢 Computing expensive calculation for {param}...")
        await asyncio.sleep(1)  # Simulate expensive computation
        return f"result_{param}_{int(time.time())}"
    
    # First call - should compute
    result1 = await expensive_calculation("test_param")
    print(f"   ✅ First call: {result1}")
    
    # Second call - should use cache
    result2 = await expensive_calculation("test_param")
    print(f"   ⚡ Second call (cached): {result2}")
    
    await cache_manager.close()


async def demo_circuit_breaker():
    """Demo the circuit breaker pattern"""
    print_header("🛡️ Circuit Breaker Demo")
    
    # Create circuit breaker with conservative settings
    cb = CircuitBreaker("api_service", CircuitBreakerConfigs.CONSERVATIVE)
    
    print_section("Normal Operation (Closed State)")
    
    async def reliable_service():
        return "Service response"
    
    # Normal operation
    for i in range(3):
        result = await cb.call(reliable_service)
        print(f"   ✅ Call {i+1}: {result}")
    
    print_section("Failure Handling (Opening Circuit)")
    
    fail_count = 0
    
    async def unreliable_service():
        nonlocal fail_count
        fail_count += 1
        if fail_count <= 3:
            raise ConnectionError("Service temporarily unavailable")
        return "Service recovered"
    
    # Failures that open the circuit
    for i in range(3):
        try:
            await cb.call(unreliable_service)
        except ConnectionError as e:
            print(f"   ❌ Call {i+1}: {e}")
    
    print(f"   🔴 Circuit state: {cb.state.value}")
    
    print_section("Fast Failure (Open State)")
    
    # Next call should fail fast
    try:
        await cb.call(unreliable_service)
    except Exception as e:
        print(f"   ⚡ Fast failure: {e}")
    
    print_section("Recovery (Half-Open State)")
    
    # Wait for recovery timeout
    print("   ⏳ Waiting for recovery timeout...")
    await asyncio.sleep(2)
    
    print(f"   🟡 Circuit state: {cb.state.value}")
    
    # Try to recover
    try:
        result = await cb.call(unreliable_service)
        print(f"   ✅ Recovery successful: {result}")
        print(f"   🟢 Circuit state: {cb.state.value}")
    except Exception as e:
        print(f"   ❌ Recovery failed: {e}")
    
    print_section("Circuit Breaker Statistics")
    stats = cb.get_stats()
    print(f"   📊 Total requests: {stats['total_requests']}")
    print(f"   ✅ Successful: {stats['successful_requests']}")
    print(f"   ❌ Failed: {stats['failed_requests']}")
    print(f"   ⚡ Fast failures: {stats['fast_failures']}")
    print(f"   🔴 Circuit opens: {stats['circuit_opens']}")
    print(f"   🟢 Circuit closes: {stats['circuit_closes']}")
    print(f"   📈 Success rate: {stats['success_rate']:.1f}%")


async def demo_enhanced_logging():
    """Demo the enhanced logging system"""
    print_header("📝 Enhanced Logging Demo")
    
    # Create logger
    logger = TradingLogger("demo_logger")
    
    print_section("Structured Logging")
    
    # Basic logging with extra fields
    logger.info("User logged in", {
        "user_id": "12345",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0"
    })
    
    logger.warning("High memory usage detected", {
        "memory_usage": 85.5,
        "threshold": 80.0,
        "component": "cache_manager"
    })
    
    print_section("Trading-Specific Logging")
    
    # Trade signal logging
    logger.trade_signal({
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 100,
        "price": 150.25,
        "strategy": "SMA_CROSSOVER",
        "confidence": 0.85
    })
    
    # Order execution logging
    logger.order_executed({
        "order_id": "ORD_12345",
        "symbol": "AAPL",
        "status": "FILLED",
        "filled_quantity": 100,
        "filled_price": 150.25,
        "timestamp": time.time()
    })
    
    # Market data logging
    logger.market_data_received("AAPL", "price", 1024)
    
    # Performance metrics
    logger.performance_metric("api_response_time", 0.125, "seconds")
    logger.performance_metric("cache_hit_rate", 87.5, "percent")
    
    # System health
    logger.system_health("database", "healthy", {
        "connections": 5,
        "response_time": 0.05
    })
    
    print_section("Performance Logging Decorator")
    
    @log_performance("data_processing")
    async def process_data(data_size):
        print(f"   🔄 Processing {data_size} records...")
        await asyncio.sleep(0.5)  # Simulate processing
        return f"Processed {data_size} records"
    
    result = await process_data(1000)
    print(f"   ✅ {result}")
    
    print_section("Error Logging Decorator")
    
    @log_errors
    async def risky_operation():
        if time.time() % 2 == 0:
            raise ValueError("Random error occurred")
        return "Operation successful"
    
    for i in range(3):
        try:
            result = await risky_operation()
            print(f"   ✅ Attempt {i+1}: {result}")
        except ValueError as e:
            print(f"   ❌ Attempt {i+1}: {e}")
    
    print_section("Performance Tracking")
    
    # Start timing an operation
    timer_id = logger.performance_logger.start_timer("batch_processing")
    
    # Simulate work
    print("   🔄 Processing batch...")
    await asyncio.sleep(0.3)
    
    # End timing
    logger.performance_logger.end_timer(timer_id, success=True, extra_data={
        "records_processed": 500,
        "errors": 0
    })
    
    print("   ✅ Batch processing completed")


async def demo_integration():
    """Demo all quick wins working together"""
    print_header("🔗 Integration Demo - All Quick Wins Working Together")
    
    # Initialize all components
    cache_manager = AdvancedCacheManager()
    await cache_manager.initialize()
    
    cb = CircuitBreaker("integrated_service", CircuitBreakerConfigs.BALANCED)
    logger = TradingLogger("integration_demo")
    
    print_section("Integrated Data Fetching with Caching and Circuit Breaker")
    
    @log_performance("integrated_data_fetch")
    async def fetch_data_with_protection(symbol: str):
        """Fetch data with all protections"""
        
        # Try cache first
        cache_key = f"market_data_{symbol}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol}")
            return cached_data
        
        # If not in cache, fetch with circuit breaker protection
        async def fetch_from_api():
            logger.info(f"Fetching data for {symbol} from API")
            await asyncio.sleep(0.2)  # Simulate API call
            return {"symbol": symbol, "price": 150.25, "volume": 1000000}
        
        data = await cb.call(fetch_from_api)
        
        # Cache the result
        await cache_manager.set(cache_key, data, ttl=60)
        
        return data
    
    # Fetch data multiple times
    symbols = ["AAPL", "GOOGL", "MSFT"]
    
    for symbol in symbols:
        print(f"\n   📈 Fetching data for {symbol}...")
        
        # First fetch
        data1 = await fetch_data_with_protection(symbol)
        print(f"   ✅ First fetch: {data1}")
        
        # Second fetch (should use cache)
        data2 = await fetch_data_with_protection(symbol)
        print(f"   ⚡ Second fetch (cached): {data2}")
    
    print_section("System Statistics")
    
    # Get all statistics
    cache_stats = await cache_manager.get_stats()
    cb_stats = cb.get_stats()
    
    print("   📊 Cache Statistics:")
    print(f"      Hit rate: {cache_stats['l1_hit_rate']:.1f}%")
    print(f"      Total requests: {cache_stats['total_requests']}")
    
    print("   🛡️ Circuit Breaker Statistics:")
    print(f"      State: {cb_stats['state']}")
    print(f"      Success rate: {cb_stats['success_rate']:.1f}%")
    print(f"      Total requests: {cb_stats['total_requests']}")
    
    # Log system health
    logger.system_health("integration_demo", "healthy", {
        "cache_hit_rate": cache_stats['l1_hit_rate'],
        "circuit_breaker_state": cb_stats['state'],
        "total_operations": cache_stats['total_requests'] + cb_stats['total_requests']
    })
    
    await cache_manager.close()


async def main():
    """Run all demos"""
    print_header("🎉 Quick Wins Demo - Trading System Improvements")
    
    print("This demo showcases the quick wins implemented:")
    print("1. 🚀 Advanced Cache Manager (L1 in-memory cache)")
    print("2. 🛡️ Circuit Breaker Pattern (fault tolerance)")
    print("3. 📝 Enhanced Logging (structured + performance tracking)")
    print("4. 🔗 Integration (all components working together)")
    
    try:
        # Run individual demos
        await demo_cache_manager()
        await demo_circuit_breaker()
        await demo_enhanced_logging()
        await demo_integration()
        
        print_header("✅ Demo Complete!")
        print("🎯 Quick wins successfully implemented:")
        print("   • Enhanced caching with automatic fallback")
        print("   • Circuit breaker protection for fault tolerance")
        print("   • Structured logging with performance tracking")
        print("   • System health monitoring capabilities")
        print("   • Comprehensive test coverage")
        
        print("\n📋 Next steps:")
        print("   • Integrate with existing trading system")
        print("   • Add Redis for L2 caching")
        print("   • Deploy health dashboard API")
        print("   • Monitor performance improvements")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 