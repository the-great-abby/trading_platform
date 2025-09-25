#!/usr/bin/env python3
"""
Quick Real Data Test
===================

Quick test with real data to verify everything works before running full analysis.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the strategy service path
sys.path.append('/app/src')

# Import our fixed components
from src.backtesting.engine.backtest_engine import BacktestEngine

async def quick_test():
    """Run a quick test with real data."""
    
    print("🚀 QUICK REAL DATA TEST")
    print("=" * 30)
    print("📊 Testing with real historical data from TimescaleDB")
    print()
    
    # Use REAL data from database
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Test just one asset with one strategy first
    test_asset = "AAPL"
    test_strategy = "RSI"
    
    print(f"🔄 Testing {test_strategy} strategy on {test_asset}...")
    print(f"📅 Date range: 2023-09-19 to 2024-09-19")
    print()
    
    try:
        # Run backtest with real data
        results = await engine.run_backtest(
            symbols=[test_asset],
            start_date="2023-09-19",
            end_date="2024-09-19",
            strategies=[test_strategy]
        )
        
        if results and test_strategy in results and results[test_strategy] is not None:
            result = results[test_strategy]
            
            print("✅ SUCCESS! Real data backtest completed")
            print()
            print("📊 RESULTS:")
            print(f"   Asset: {test_asset}")
            print(f"   Strategy: {test_strategy}")
            print(f"   Total Return: {result.total_return:.1%}")
            print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"   Max Drawdown: {getattr(result, 'max_drawdown', 0):.1%}")
            print(f"   Total Trades: {result.total_trades}")
            print(f"   Win Rate: {getattr(result, 'win_rate', 0):.1%}")
            print(f"   Profit Factor: {getattr(result, 'profit_factor', 0):.2f}")
            print()
            
            # Calculate final value
            initial_capital = 2000.0
            final_value = initial_capital * (1 + result.total_return)
            profit = final_value - initial_capital
            
            print("💰 PERFORMANCE:")
            print(f"   Initial Capital: ${initial_capital:,.2f}")
            print(f"   Final Value: ${final_value:,.2f}")
            print(f"   Profit/Loss: ${profit:,.2f}")
            print()
            
            print("🎉 Real data backtest is working! Ready for full analysis.")
            
        else:
            print("❌ No results returned from backtest")
            
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
