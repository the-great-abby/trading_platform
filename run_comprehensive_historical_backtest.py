#!/usr/bin/env python3
"""
Comprehensive Historical Backtest
Tests the historical date functionality with a longer period and more symbols
"""

import asyncio
import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.utils.config import get_config
from src.utils.trading_config import get_symbols, get_options_symbols

logger = get_trading_logger()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run comprehensive historical backtest')
    parser.add_argument('--start-date', type=str, default=os.getenv('BACKTEST_START_DATE', '2023-01-01'),
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=os.getenv('BACKTEST_END_DATE', '2023-06-30'),
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--symbols', type=str, default=os.getenv('BACKTEST_SYMBOLS', 'AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,NFLX'),
                       help='Comma-separated list of symbols to test')
    parser.add_argument('--strategies', type=str, default=os.getenv('BACKTEST_STRATEGIES', 'GreeksEnhancedStrategy,BollingerBandsStrategy,MACDStrategy,RSIStrategy'),
                       help='Comma-separated list of strategies to test')
    parser.add_argument('--initial-capital', type=float, default=float(os.getenv('BACKTEST_INITIAL_CAPITAL', '100000.0')),
                       help='Initial capital for backtest')
    return parser.parse_args()

async def run_comprehensive_historical_backtest():
    """Run comprehensive backtest with historical date functionality"""
    
    # Parse command line arguments
    args = parse_arguments()
    
    print("🚀 COMPREHENSIVE HISTORICAL BACKTEST")
    print("=" * 60)
    print("Testing historical date functionality with multiple strategies")
    print("=" * 60)
    
    # Configuration from arguments
    initial_capital = args.initial_capital
    start_date = args.start_date
    end_date = args.end_date
    symbols = [s.strip() for s in args.symbols.split(',')]
    strategies = [s.strip() for s in args.strategies.split(',')]
    
    print(f"📊 Test Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {', '.join(symbols)}")
    print(f"   🎯 Strategies: {', '.join(strategies)}")
    print(f"   🗄️  Data Source: Real Market Data with Historical Dates")
    print()
    
    # Initialize backtest engine with real data and caching
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Run the backtest with multiple strategies
    print(f"🏃 Running comprehensive backtest with historical date functionality...")
    print(f"   This should show logs like:")
    print(f"   - [GreeksStrategy] Looking for options data for AAPL on historical date 2023-03-15")
    print(f"   - [GreeksStrategy] Historical expirations for AAPL on 2023-03-15: ['2023-04-21', '2023-05-19']")
    print()
    
    start_time = datetime.now()
    
    # Run the backtest with multiple strategies
    results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=strategies
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
    
    print("✅ Comprehensive historical backtest completed!")
    print("Check the logs above for historical date functionality messages.")

async def main():
    """Main function"""
    try:
        await run_comprehensive_historical_backtest()
    except Exception as e:
        logger.error(f"❌ Error in comprehensive historical backtest: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 