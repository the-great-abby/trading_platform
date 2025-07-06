#!/usr/bin/env python3
"""
Quick Wins Demo - Containerized Version with Redis
Optimized for running in Docker containers with Redis L2 caching
"""

import asyncio
import time
import sys
import os
import json

# Add src to path (containerized environment)
sys.path.insert(0, '/app/src')

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
    """Demo the advanced cache manager with Redis"""
    print_header("🚀 Advanced Cache Manager Demo (with Redis L2)")
    
    # Create cache manager with Redis
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    cache_manager = AdvancedCacheManager(redis_url=redis_url, l1_max_size=5, l1_ttl=10)
    await cache_manager.initialize()
    
    print_section("Cache Configuration")
    print(f"   🔗 Redis URL: {redis_url}")
    print(f"   📦 L1 Cache Size: {cache_manager.l1_max_size}")
    print(f"   ⏰ L1 TTL: {cache_manager.l1_ttl}s")
    print(f"   🔌 Redis Connected: {cache_manager.redis_client is not None}")
    
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
    print(f"   🔗 L2 hit rate: {stats['l2_hit_rate']:.1f}%")
    print(f"   📦 L1 cache size: {stats['l1_cache_size']}/{stats['l1_cache_max_size']}")
    print(f"   🗑️  Evictions: {stats['cache_evictions']}")
    
    # Redis info
    if stats.get('redis_info'):
        print(f"   🔌 Redis clients: {stats['redis_info'].get('connected_clients', 0)}")
        print(f"   💾 Redis memory: {stats['redis_info'].get('used_memory_human', '0B')}")
        print(f"   🎯 Redis hits: {stats['redis_info'].get('keyspace_hits', 0)}")
        print(f"   ❌ Redis misses: {stats['redis_info'].get('keyspace_misses', 0)}")
    
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
    
    # Test Redis persistence across cache manager instances
    print_section("Redis Persistence Test")
    
    # Create a new cache manager instance
    cache_manager2 = AdvancedCacheManager(redis_url=redis_url)
    await cache_manager2.initialize()
    
    # Try to get data that was set by the first instance
    persistent_data = await cache_manager2.get("user_profile")
    if persistent_data:
        print(f"   ✅ Data persisted in Redis: {persistent_data}")
    else:
        print(f"   ❌ Data not found in Redis")
    
    await cache_manager.close()
    await cache_manager2.close()


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
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    cache_manager = AdvancedCacheManager(redis_url=redis_url)
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
    print(f"      L1 hit rate: {cache_stats['l1_hit_rate']:.1f}%")
    print(f"      L2 hit rate: {cache_stats['l2_hit_rate']:.1f}%")
    print(f"      Total requests: {cache_stats['total_requests']}")
    print(f"      Redis connected: {cache_stats['redis_connected']}")
    
    print("   🛡️ Circuit Breaker Statistics:")
    print(f"      State: {cb_stats['state']}")
    print(f"      Success rate: {cb_stats['success_rate']:.1f}%")
    print(f"      Total requests: {cb_stats['total_requests']}")
    
    # Log system health
    logger.system_health("integration_demo", "healthy", {
        "cache_hit_rate": cache_stats['l1_hit_rate'] + cache_stats['l2_hit_rate'],
        "circuit_breaker_state": cb_stats['state'],
        "total_operations": cache_stats['total_requests'] + cb_stats['total_requests'],
        "redis_connected": cache_stats['redis_connected']
    })
    
    await cache_manager.close()


async def demo_container_info():
    """Show container-specific information"""
    print_header("🐳 Container Environment Info")
    
    print_section("Environment Variables")
    print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"   PYTHONUNBUFFERED: {os.environ.get('PYTHONUNBUFFERED', 'Not set')}")
    print(f"   REDIS_URL: {os.environ.get('REDIS_URL', 'Not set')}")
    print(f"   Container ID: {os.environ.get('HOSTNAME', 'Unknown')}")
    
    print_section("File System")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Executable: {sys.executable}")
    print(f"   Python Version: {sys.version}")
    
    print_section("Quick Wins Files")
    quick_wins_files = [
        "src/utils/cache_manager.py",
        "src/utils/circuit_breaker.py", 
        "src/utils/enhanced_logging.py",
        "src/api/health_dashboard.py",
        "tests/test_quick_wins.py"
    ]
    
    for file_path in quick_wins_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")


async def main():
    """Run all demos"""
    print_header("🎉 Quick Wins Demo - Containerized Trading System with Redis")
    
    print("This demo showcases the quick wins implemented in a containerized environment:")
    print("1. 🚀 Advanced Cache Manager (L1: Memory, L2: Redis)")
    print("2. 🛡️ Circuit Breaker Pattern (fault tolerance)")
    print("3. 📝 Enhanced Logging (structured + performance tracking)")
    print("4. 🔗 Integration (all components working together)")
    print("5. 🐳 Container Environment (consistent deployment)")
    print("6. 🔗 Redis L2 Caching (persistent, distributed)")
    
    try:
        # Show container info first
        await demo_container_info()
        
        # Run individual demos
        await demo_cache_manager()
        await demo_circuit_breaker()
        await demo_enhanced_logging()
        await demo_integration()
        
        print_header("✅ Container Demo Complete!")
        print("🎯 Quick wins successfully implemented in containerized environment:")
        print("   • Enhanced caching with Redis L2 persistence")
        print("   • Circuit breaker protection for fault tolerance")
        print("   • Structured logging with performance tracking")
        print("   • System health monitoring capabilities")
        print("   • Comprehensive test coverage")
        print("   • Containerized deployment ready")
        print("   • Redis integration for distributed caching")
        
        print("\n📋 Next steps:")
        print("   • Integrate with existing trading system containers")
        print("   • Deploy health dashboard API container")
        print("   • Set up container orchestration (Kubernetes)")
        print("   • Monitor performance improvements")
        print("   • Scale Redis cluster for production")
        
        # Write completion status to logs
        with open("/app/logs/demo_completion.json", "w") as f:
            json.dump({
                "status": "completed",
                "timestamp": time.time(),
                "container_id": os.environ.get("HOSTNAME", "unknown"),
                "redis_url": os.environ.get("REDIS_URL", "not_set"),
                "quick_wins": [
                    "cache_manager_with_redis",
                    "circuit_breaker", 
                    "enhanced_logging",
                    "health_dashboard",
                    "automated_testing"
                ]
            }, f, indent=2)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Write error status to logs
        with open("/app/logs/demo_error.json", "w") as f:
            json.dump({
                "status": "failed",
                "timestamp": time.time(),
                "container_id": os.environ.get("HOSTNAME", "unknown"),
                "redis_url": os.environ.get("REDIS_URL", "not_set"),
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main()) 