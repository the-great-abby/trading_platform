#!/usr/bin/env python3
"""
Historical Greeks Backtest
Tests the historical date functionality for options data in backtesting
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.utils.config import get_config
from src.utils.trading_config import get_symbols, get_options_symbols

logger = get_trading_logger()

async def run_historical_greeks_backtest():
    """Run backtest with historical date functionality"""
    
    print("🚀 HISTORICAL GREEKS BACKTEST")
    print("=" * 60)
    print("Testing historical date functionality for options data")
    print("=" * 60)
    
    # Configuration
    initial_capital = 100000.0
    
    # Use a historical date range for testing
    start_date = "2023-07-06"  # Historical start date
    end_date = "2023-08-15"    # Historical end date (about 6 weeks)
    
    # Use a small set of options symbols for testing
    symbols = ['AAPL', 'MSFT', 'GOOGL']  # Focus on major options symbols
    
    print(f"📊 Test Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {', '.join(symbols)}")
    print(f"   🎯 Strategy: GreeksEnhancedStrategy")
    print(f"   🗄️  Data Source: Real Market Data with Historical Dates")
    print()
    
    # Initialize backtest engine with real data and caching
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Run the backtest with historical dates
    print(f"🏃 Running backtest with historical date functionality...")
    print(f"   This should show logs like:")
    print(f"   - [GreeksStrategy] Looking for options data for AAPL on historical date 2023-07-10")
    print(f"   - [GreeksStrategy] Historical expirations for AAPL on 2023-07-10: ['2023-08-18', '2023-09-15']")
    print()
    
    # Check what data is available first
    print("🔍 Checking data availability...")
    market_data_manager = engine.market_data_manager
    if market_data_manager:
        print(f"✅ Market data manager available: {type(market_data_manager).__name__}")
        
        # Check data for each symbol
        for symbol in symbols:
            try:
                data = market_data_manager.get_historical_data(symbol, start_date, end_date)
                if data is not None and not data.empty:
                    print(f"✅ Found {len(data)} data points for {symbol}")
                    print(f"   Date range: {data.index.min()} to {data.index.max()}")
                    print(f"   Latest price: ${data['Close'].iloc[-1]:.2f}")
                else:
                    print(f"❌ No data found for {symbol}")
            except Exception as e:
                print(f"❌ Error getting data for {symbol}: {e}")
    else:
        print("❌ No market data manager available")
    
    print()
    
    start_time = datetime.now()
    
    # Run the backtest
    results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=['GreeksEnhancedStrategy']
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"⏱️  Backtest completed in {duration}")
    print()
    
    # Display results
    if results:
        for strategy_name, result in results.items():
            print(f"📊 Results for {strategy_name}:")
            print(f"   💰 Initial Capital: ${result.initial_capital:,.2f}")
            print(f"   💰 Final Capital: ${result.final_capital:,.2f}")
            print(f"   📈 Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
            print(f"   📊 Total Trades: {result.total_trades}")
            print(f"   🎯 Win Rate: {result.win_rate:.2f}%")
            print(f"   📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
            print(f"   📊 Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print()
    else:
        print("❌ No results returned from backtest")
    
    print("✅ Historical Greeks backtest completed!")
    print("Check the logs above for historical date functionality messages.")

async def main():
    """Main function"""
    try:
        await run_historical_greeks_backtest()
    except Exception as e:
        logger.error(f"❌ Error in historical Greeks backtest: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 