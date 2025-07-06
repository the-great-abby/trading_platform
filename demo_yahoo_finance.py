#!/usr/bin/env python3
"""
Demo: Enhanced Yahoo Finance Market Data Service
Tests real market data retrieval with proper error handling and fallbacks
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.yahoo_finance_service import YahooFinanceService, get_market_data, get_live_prices


async def demo_yahoo_finance():
    """Demo the enhanced Yahoo Finance service"""
    
    print("🚀 Yahoo Finance Market Data Demo")
    print("=" * 50)
    
    # Initialize service
    service = YahooFinanceService(rate_limit_delay=0.2)  # 200ms delay between requests
    
    # Test symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    
    # Test 1: Get live prices
    print("\n📊 Test 1: Live Price Check")
    print("-" * 30)
    
    for symbol in symbols:
        price = service.get_live_price(symbol)
        if price:
            print(f"✅ {symbol}: ${price:.2f}")
        else:
            print(f"❌ {symbol}: No price data")
    
    # Test 2: Get symbol information
    print("\n📋 Test 2: Symbol Information")
    print("-" * 30)
    
    for symbol in symbols[:2]:  # Test first 2 symbols
        info = service.get_symbol_info(symbol)
        if info:
            print(f"✅ {symbol}: {info['name']}")
            print(f"   Sector: {info['sector']}")
            print(f"   Market Cap: ${info['market_cap']:,}" if info['market_cap'] else "   Market Cap: N/A")
            print(f"   P/E Ratio: {info['pe_ratio']:.2f}" if info['pe_ratio'] else "   P/E Ratio: N/A")
        else:
            print(f"❌ {symbol}: No info available")
    
    # Test 3: Get historical data
    print("\n📈 Test 3: Historical Data (Last 30 Days)")
    print("-" * 40)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Test single symbol first
    print(f"Fetching data for AAPL from {start_date} to {end_date}...")
    aapl_data = service.get_historical_data('AAPL', start_date, end_date)
    
    if aapl_data is not None and not aapl_data.empty:
        print(f"✅ AAPL: {len(aapl_data)} records")
        print(f"   Latest Close: ${aapl_data['CLOSE'].iloc[-1]:.2f}")
        print(f"   Date Range: {aapl_data.index[0].strftime('%Y-%m-%d')} to {aapl_data.index[-1].strftime('%Y-%m-%d')}")
        
        # Show sample data
        print("\n   Sample Data (Last 5 days):")
        sample_data = aapl_data.tail(5)[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']]
        print(sample_data.to_string())
    else:
        print("❌ AAPL: No historical data available")
    
    # Test 4: Get multiple symbols
    print("\n📊 Test 4: Multiple Symbols Batch Download")
    print("-" * 40)
    
    print(f"Downloading data for {len(symbols)} symbols...")
    market_data = service.get_multiple_symbols(symbols, start_date, end_date)
    
    print(f"✅ Successfully downloaded data for {len(market_data)}/{len(symbols)} symbols")
    
    for symbol, data in market_data.items():
        if data is not None and not data.empty:
            latest_price = data['CLOSE'].iloc[-1]
            price_change = ((latest_price - data['CLOSE'].iloc[0]) / data['CLOSE'].iloc[0]) * 100
            print(f"   {symbol}: ${latest_price:.2f} ({price_change:+.2f}%)")
    
    # Test 5: Market hours
    print("\n🕐 Test 5: Market Hours")
    print("-" * 20)
    
    market_hours = service.get_market_hours()
    print(f"Market State: {market_hours['market_state']}")
    print(f"Timezone: {market_hours['timezone']}")
    
    # Test 6: Symbol validation
    print("\n✅ Test 6: Symbol Validation")
    print("-" * 25)
    
    test_symbols = ['AAPL', 'INVALID', 'GOOGL', 'FAKE123']
    for symbol in test_symbols:
        is_valid = service.validate_symbol(symbol)
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"   {symbol}: {status}")
    
    # Test 7: Convenience functions
    print("\n🛠️  Test 7: Convenience Functions")
    print("-" * 30)
    
    # Test get_market_data function
    print("Testing get_market_data() convenience function...")
    convenience_data = get_market_data(['AAPL', 'MSFT'], start_date, end_date)
    print(f"✅ Downloaded {len(convenience_data)} symbols via convenience function")
    
    # Test get_live_prices function
    print("Testing get_live_prices() convenience function...")
    live_prices = get_live_prices(['AAPL', 'GOOGL', 'MSFT'])
    print(f"✅ Got live prices for {len(live_prices)} symbols")
    for symbol, price in live_prices.items():
        print(f"   {symbol}: ${price:.2f}")
    
    print("\n🎉 Yahoo Finance Demo Completed!")
    print("=" * 50)


async def demo_backtest_with_real_data():
    """Demo backtesting with real Yahoo Finance data"""
    
    print("\n🚀 Backtesting with Real Market Data Demo")
    print("=" * 50)
    
    from backtesting.backtest_engine import BacktestEngine
    
    # Initialize backtest engine with real data
    engine = BacktestEngine(use_real_data=True)
    
    # Test symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    # Test period (last 6 months)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    # Test strategies
    strategies = ['sma_crossover', 'rsi', 'macd']
    
    print(f"📊 Running backtest with real data:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Period: {start_date} to {end_date}")
    print(f"   Strategies: {', '.join(strategies)}")
    print(f"   Data Source: Real Yahoo Finance")
    
    # Run backtest
    results = await engine.run_backtest(symbols, start_date, end_date, strategies)
    
    if results:
        print("\n📈 Backtest Results:")
        print("-" * 20)
        
        for strategy_name, result in results.items():
            if result:
                print(f"\n{strategy_name.upper()}:")
                print(f"   Total Return: {result['total_return']:.2f}%")
                print(f"   Total Trades: {result['total_trades']}")
                print(f"   Win Rate: {result['win_rate']:.2%}")
                print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
                print(f"   Max Drawdown: ${result['max_drawdown']:.2f}")
                print(f"   Symbols Tested: {len(result['symbols'])}")
    else:
        print("❌ No backtest results available")
    
    print("\n🎉 Backtesting Demo Completed!")


if __name__ == "__main__":
    print("Starting Yahoo Finance Market Data Demo...")
    
    # Run demos
    asyncio.run(demo_yahoo_finance())
    asyncio.run(demo_backtest_with_real_data()) 