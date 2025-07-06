#!/usr/bin/env python3
"""
Market Data Providers Demo
Tests all available market data providers and shows usage examples
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.market_data_provider import (
    get_market_data_manager,
    YahooFinanceService,
    AlphaVantageProvider,
    IEXCloudProvider,
    PolygonProvider
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_section(title: str):
    """Print a formatted section"""
    print(f"\n--- {title} ---")


async def test_provider_status():
    """Test the status of all providers"""
    print_header("Provider Status Check")
    
    manager = get_market_data_manager()
    status = manager.get_provider_status()
    
    print("Provider Status:")
    for provider, is_working in status.items():
        status_icon = "✅" if is_working else "❌"
        print(f"  {status_icon} {provider}: {'Working' if is_working else 'Failed'}")
    
    working_providers = sum(status.values())
    total_providers = len(status)
    print(f"\nSummary: {working_providers}/{total_providers} providers working")


async def test_individual_providers():
    """Test each provider individually"""
    print_header("Individual Provider Tests")
    
    symbols = ["AAPL", "GOOGL"]
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    providers = [
        ("Yahoo Finance", YahooFinanceService()),
        ("Alpha Vantage", AlphaVantageProvider()),
        ("IEX Cloud", IEXCloudProvider()),
        ("Polygon", PolygonProvider())
    ]
    
    for name, provider in providers:
        print_section(f"Testing {name}")
        
        try:
            # Test historical data
            print(f"  Getting historical data for {symbols[0]}...")
            data = provider.get_historical_data(symbols[0], start_date, end_date)
            
            if data is not None and not data.empty:
                print(f"  ✅ Success: {len(data)} records")
                print(f"  📊 Latest close: ${data['Close'].iloc[-1]:.2f}")
            else:
                print(f"  ❌ No data returned")
            
            # Test live price
            print(f"  Getting live price for {symbols[0]}...")
            price = provider.get_live_price(symbols[0])
            
            if price is not None:
                print(f"  ✅ Live price: ${price:.2f}")
            else:
                print(f"  ❌ No live price available")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


async def test_market_data_manager():
    """Test the market data manager with fallback"""
    print_header("Market Data Manager Test")
    
    symbols = ["AAPL", "GOOGL", "MSFT"]
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    manager = get_market_data_manager()
    
    print_section("Getting Historical Data")
    print(f"  Requesting data for {len(symbols)} symbols...")
    
    data = manager.get_multiple_symbols(symbols, start_date, end_date)
    
    print(f"  ✅ Successfully got data for {len(data)}/{len(symbols)} symbols")
    
    for symbol, df in data.items():
        if df is not None and not df.empty:
            latest_close = df['Close'].iloc[-1]
            print(f"  📊 {symbol}: ${latest_close:.2f} ({len(df)} records)")
        else:
            print(f"  ❌ {symbol}: No data")
    
    print_section("Getting Live Prices")
    prices = {}
    for symbol in symbols:
        price = manager.get_live_price(symbol)
        if price is not None:
            prices[symbol] = price
            print(f"  📈 {symbol}: ${price:.2f}")
        else:
            print(f"  ❌ {symbol}: No live price")
    
    if prices:
        avg_price = sum(prices.values()) / len(prices)
        print(f"  📊 Average price: ${avg_price:.2f}")


async def test_backtest_integration():
    """Test integration with backtesting system"""
    print_header("Backtesting Integration Test")
    
    try:
        from backtesting.backtest_engine import BacktestEngine
        
        print_section("Testing BacktestEngine with Real Data")
        
        # Test with real data
        engine = BacktestEngine(use_real_data=True)
        
        symbols = ["AAPL", "GOOGL"]
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        strategies = ["sma_crossover"]
        
        print(f"  Running backtest with real data...")
        print(f"  Symbols: {symbols}")
        print(f"  Period: {start_date} to {end_date}")
        print(f"  Strategies: {strategies}")
        
        results = await engine.run_backtest(symbols, start_date, end_date, strategies)
        
        if results:
            print(f"  ✅ Backtest completed successfully")
            for strategy, result in results.items():
                if result:
                    print(f"  📊 {strategy}: {result.total_return_pct:.2f}% return")
                else:
                    print(f"  ❌ {strategy}: No results")
        else:
            print(f"  ❌ Backtest failed")
            
    except ImportError as e:
        print(f"  ❌ Could not import BacktestEngine: {str(e)}")
    except Exception as e:
        print(f"  ❌ Backtest error: {str(e)}")


async def test_rate_limiting():
    """Test rate limiting behavior"""
    print_header("Rate Limiting Test")
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    
    print_section("Testing Multiple Rapid Requests")
    print(f"  Making {len(symbols)} rapid requests...")
    
    manager = get_market_data_manager()
    
    start_time = datetime.now()
    
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i}/{len(symbols)}: Getting {symbol}...")
        price = manager.get_live_price(symbol)
        if price:
            print(f"     ✅ ${price:.2f}")
        else:
            print(f"     ❌ Failed")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n  📊 Total time: {duration:.2f} seconds")
    print(f"  📊 Average time per request: {duration/len(symbols):.2f} seconds")


async def test_error_handling():
    """Test error handling with invalid symbols"""
    print_header("Error Handling Test")
    
    invalid_symbols = ["INVALID_SYMBOL", "XYZ123", "NONEXISTENT"]
    
    print_section("Testing Invalid Symbols")
    
    manager = get_market_data_manager()
    
    for symbol in invalid_symbols:
        print(f"  Testing invalid symbol: {symbol}")
        
        # Test historical data
        data = manager.get_historical_data(symbol, "2024-01-01", "2024-01-31")
        if data is None or data.empty:
            print(f"    ✅ Correctly handled invalid symbol (historical)")
        else:
            print(f"    ❌ Unexpectedly got data for invalid symbol")
        
        # Test live price
        price = manager.get_live_price(symbol)
        if price is None:
            print(f"    ✅ Correctly handled invalid symbol (live price)")
        else:
            print(f"    ❌ Unexpectedly got price for invalid symbol")


async def show_usage_examples():
    """Show usage examples"""
    print_header("Usage Examples")
    
    print_section("Basic Usage")
    print("""
# Get market data manager
manager = get_market_data_manager()

# Get historical data (automatically tries all providers)
data = manager.get_historical_data("AAPL", "2024-01-01", "2024-12-31")

# Get live price
price = manager.get_live_price("AAPL")

# Get multiple symbols
symbols = ["AAPL", "GOOGL", "MSFT"]
data = manager.get_multiple_symbols(symbols, "2024-01-01", "2024-12-31")
""")
    
    print_section("Provider-Specific Usage")
    print("""
# Use specific provider
yahoo = YahooFinanceService()
alpha = AlphaVantageProvider()
iex = IEXCloudProvider()
polygon = PolygonProvider()

# Get data from specific provider
data = yahoo.get_historical_data("AAPL", "2024-01-01", "2024-12-31")
""")
    
    print_section("Check Provider Status")
    print("""
manager = get_market_data_manager()
status = manager.get_provider_status()

for provider, is_working in status.items():
    print(f"{provider}: {'✅ Working' if is_working else '❌ Failed'}")
""")


async def main():
    """Main demo function"""
    print_header("Market Data Providers Demo")
    print("Testing all available market data providers...")
    
    try:
        # Test provider status
        await test_provider_status()
        
        # Test individual providers
        await test_individual_providers()
        
        # Test market data manager
        await test_market_data_manager()
        
        # Test backtesting integration
        await test_backtest_integration()
        
        # Test rate limiting
        await test_rate_limiting()
        
        # Test error handling
        await test_error_handling()
        
        # Show usage examples
        await show_usage_examples()
        
        print_header("Demo Complete")
        print("✅ All tests completed!")
        print("\nNext steps:")
        print("1. Get API keys for additional providers")
        print("2. Run backtests with real data")
        print("3. Monitor provider performance")
        print("4. Consider paid plans for production use")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 