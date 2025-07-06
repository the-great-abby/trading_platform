#!/usr/bin/env python3
"""
Quick Wins Integration Demo - Shows how to integrate Quick Wins with the main trading system
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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


async def demo_integrated_market_data():
    """Demo market data with Quick Wins integration"""
    print_header("🚀 Integrated Market Data with Quick Wins")
    
    # Initialize Quick Wins components
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    cache_manager = AdvancedCacheManager(redis_url=redis_url)
    await cache_manager.initialize()
    
    circuit_breaker = CircuitBreaker("market_data_api", CircuitBreakerConfigs.TRADING)
    logger = TradingLogger("integrated_market_data")
    
    print_section("Quick Wins Configuration")
    print(f"   🔗 Redis URL: {redis_url}")
    print(f"   🛡️ Circuit Breaker: {circuit_breaker.name}")
    print(f"   📝 Logger: {logger.name}")
    
    print_section("Cached Market Data Fetching")
    
    @cached(ttl=300, key_prefix="market_data")  # Cache for 5 minutes
    @log_performance("market_data_fetch")
    @log_errors
    async def fetch_market_data_with_protection(symbol: str):
        """Fetch market data with circuit breaker protection"""
        
        async def fetch_from_api():
            logger.info("Fetching market data", {
                "symbol": symbol,
                "provider": "integrated"
            })
            
            # Simulate API call with circuit breaker protection
            return await circuit_breaker.call(
                lambda: simulate_market_data_api(symbol)
            )
        
        # Try cache first, then fetch if needed
        cache_key = f"market_data:{symbol}"
        data = await cache_manager.get(cache_key, fetch_from_api)
        
        if data is not None:
            logger.info("Market data retrieved successfully", {
                "symbol": symbol,
                "cache_hit": True
            })
        
        return data
    
    async def simulate_market_data_api(symbol: str):
        """Simulate market data API call"""
        await asyncio.sleep(0.1)  # Simulate API delay
        return {
            "symbol": symbol,
            "price": 150.0 + hash(symbol) % 100,
            "timestamp": datetime.now().isoformat()
        }
    
    # Test with sample symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    for symbol in symbols:
        print(f"\n📊 Fetching data for {symbol}...")
        
        # First call - should fetch from API
        data1 = await fetch_market_data_with_protection(symbol)
        if data1 is not None:
            print(f"   ✅ First call: ${data1['price']:.2f}")
        
        # Second call - should use cache
        data2 = await fetch_market_data_with_protection(symbol)
        if data2 is not None:
            print(f"   ⚡ Second call (cached): ${data2['price']:.2f}")
    
    # Show statistics
    print_section("Performance Statistics")
    cache_stats = await cache_manager.get_stats()
    cb_stats = circuit_breaker.get_stats()
    
    print(f"   📊 Cache hit rate: {cache_stats['l1_hit_rate']:.1f}%")
    print(f"   🛡️ Circuit breaker success rate: {cb_stats['success_rate']:.1f}%")
    print(f"   ⚡ Fast failures: {cb_stats['fast_failures']}")
    
    await cache_manager.close()


async def demo_integrated_backtesting():
    """Demo backtesting with Quick Wins integration"""
    print_header("📈 Integrated Backtesting with Quick Wins")
    
    # Initialize Quick Wins components
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    cache_manager = AdvancedCacheManager(redis_url=redis_url)
    await cache_manager.initialize()
    
    logger = TradingLogger("integrated_backtesting")
    
    print_section("Cached Backtest Results")
    
    @cached(ttl=1800, key_prefix="backtest_results")  # Cache for 30 minutes
    @log_performance("backtest_execution")
    @log_errors
    async def run_cached_backtest(symbols: list, start_date: str, end_date: str):
        """Run backtest with caching"""
        
        logger.info("Starting cached backtest", {
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date
        })
        
        # Simulate backtest execution
        await asyncio.sleep(0.5)  # Simulate processing time
        
        results = {
            "sma_crossover": {"return": 5.2, "trades": 12},
            "rsi": {"return": -2.1, "trades": 8},
            "macd": {"return": 3.7, "trades": 15}
        }
        
        logger.info("Backtest completed", {
            "strategies_tested": len(results),
            "total_trades": sum(r["trades"] for r in results.values())
        })
        
        return results
    
    # Test parameters
    symbols = ['AAPL', 'GOOGL']
    end_date = datetime.now() - timedelta(days=60)
    start_date = (end_date - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    
    print(f"📊 Running backtest for {len(symbols)} symbols...")
    
    # First run - should execute full backtest
    results1 = await run_cached_backtest(symbols, start_date, end_date)
    print(f"   ✅ First run: {len(results1)} strategy results")
    
    # Second run - should use cache
    results2 = await run_cached_backtest(symbols, start_date, end_date)
    print(f"   ⚡ Second run (cached): {len(results2)} strategy results")
    
    # Show results summary
    print_section("Backtest Results Summary")
    for strategy_name, result in results1.items():
        print(f"   📈 {strategy_name}: {result['return']:.1f}% return, {result['trades']} trades")
    
    await cache_manager.close()


async def demo_health_monitoring():
    """Demo health monitoring integration"""
    print_header("🏥 Health Monitoring Integration")
    
    logger = TradingLogger("health_monitoring")
    
    print_section("System Health Check")
    
    # Check Redis connection
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        cache_manager = AdvancedCacheManager(redis_url=redis_url)
        await cache_manager.initialize()
        
        # Test Redis connection
        await cache_manager.set("health_check", {"timestamp": datetime.now().isoformat()}, ttl=60)
        health_data = await cache_manager.get("health_check")
        
        if health_data:
            logger.info("Redis health check passed", {"status": "healthy"})
            print("   ✅ Redis: Healthy")
        else:
            logger.warning("Redis health check failed", {"status": "unhealthy"})
            print("   ❌ Redis: Unhealthy")
        
        await cache_manager.close()
        
    except Exception as e:
        logger.error("Redis health check error", {"error": str(e)})
        print(f"   ❌ Redis: Error - {e}")
    
    print_section("Performance Metrics")
    
    # Log system performance
    logger.info("System performance snapshot", {
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        "redis_url": os.environ.get('REDIS_URL', 'not_set'),
        "log_level": os.environ.get('LOG_LEVEL', 'INFO')
    })


async def demo_trading_integration():
    """Demo how to integrate Quick Wins with trading operations"""
    print_header("💰 Trading Operations with Quick Wins")
    
    logger = TradingLogger("trading_operations")
    
    print_section("Cached Trading Signals")
    
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    cache_manager = AdvancedCacheManager(redis_url=redis_url)
    await cache_manager.initialize()
    
    circuit_breaker = CircuitBreaker("trading_api", CircuitBreakerConfigs.TRADING)
    
    @cached(ttl=60, key_prefix="trading_signals")  # Cache for 1 minute
    @log_performance("signal_generation")
    @log_errors
    async def generate_trading_signal(symbol: str, strategy: str):
        """Generate trading signal with caching and protection"""
        
        async def calculate_signal():
            logger.info("Generating trading signal", {
                "symbol": symbol,
                "strategy": strategy
            })
            
            # Simulate signal calculation
            await asyncio.sleep(0.1)
            
            # Simulate different signal types
            signals = {
                "AAPL": {"action": "BUY", "confidence": 0.85, "price": 150.25},
                "GOOGL": {"action": "SELL", "confidence": 0.72, "price": 2800.50},
                "MSFT": {"action": "HOLD", "confidence": 0.45, "price": 350.75}
            }
            
            return signals.get(symbol, {"action": "HOLD", "confidence": 0.5, "price": 100.0})
        
        # Use circuit breaker for protection
        signal = await circuit_breaker.call(calculate_signal)
        
        if signal:
            logger.trade_signal({
                "symbol": symbol,
                "action": signal["action"],
                "confidence": signal["confidence"],
                "strategy": strategy
            })
        
        return signal
    
    # Test signal generation
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    strategies = ['sma_crossover', 'rsi']
    
    for symbol in symbols:
        for strategy in strategies:
            print(f"\n📊 Generating {strategy} signal for {symbol}...")
            
            # First call
            signal1 = await generate_trading_signal(symbol, strategy)
            print(f"   ✅ First call: {signal1['action']} (confidence: {signal1['confidence']:.2f})")
            
            # Second call (cached)
            signal2 = await generate_trading_signal(symbol, strategy)
            print(f"   ⚡ Second call (cached): {signal2['action']} (confidence: {signal2['confidence']:.2f})")
    
    await cache_manager.close()


async def main():
    """Main demo function"""
    print_header("🎯 Quick Wins Integration Demo")
    print("This demo shows how to integrate Quick Wins with the main trading system")
    
    try:
        # Demo 1: Integrated Market Data
        await demo_integrated_market_data()
        
        # Demo 2: Integrated Backtesting
        await demo_integrated_backtesting()
        
        # Demo 3: Trading Operations
        await demo_trading_integration()
        
        # Demo 4: Health Monitoring
        await demo_health_monitoring()
        
        print_header("✅ Integration Demo Complete")
        print("The Quick Wins system is now integrated with your trading system!")
        print("\n🎯 Key Benefits:")
        print("   🚀 10-100x faster data access through caching")
        print("   🛡️ Automatic failure protection with circuit breakers")
        print("   📝 Comprehensive logging and monitoring")
        print("   🏥 Real-time health monitoring")
        print("   📊 Performance metrics and statistics")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 