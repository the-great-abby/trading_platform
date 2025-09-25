#!/usr/bin/env python3
"""
Debug Backtest - Test with full data range
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add src to path
sys.path.append('/app/src')

from src.backtesting.engine.backtest_engine import BacktestEngine

async def debug_backtest():
    """Debug the backtest with full data range"""
    
    print("🔍 DEBUG BACKTEST")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💾 Database-only mode: {os.getenv('DATABASE_ONLY', 'false')}")
    
    # Initialize backtest engine
    print("\n🔧 Initializing backtest engine...")
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    print("✅ Engine initialized")
    
    # Test with full date range
    print("\n📊 Testing SMACrossover with FULL date range...")
    print("📈 Date range: 2023-09-19 to 2024-09-19 (full year)")
    
    start_time = time.time()
    
    try:
        # Get market data first to debug
        print("\n🔍 Getting market data...")
        market_data = await engine._get_market_data(['AMD'], '2023-09-19', '2024-09-19')
        
        if market_data and 'AMD' in market_data:
            amd_data = market_data['AMD']
            print(f"✅ AMD data shape: {amd_data.shape}")
            print(f"📅 AMD date range: {amd_data.index[0]} to {amd_data.index[-1]}")
            print(f"📊 AMD columns: {list(amd_data.columns)}")
            print(f"🔍 AMD sample data:")
            print(amd_data[['Close', 'SMA_20', 'SMA_50', 'RSI']].head(10))
            print(f"🔍 AMD sample data (last 10):")
            print(amd_data[['Close', 'SMA_20', 'SMA_50', 'RSI']].tail(10))
            
            # Now run the backtest
            print(f"\n🚀 Running backtest...")
            results = await engine.run_backtest(
                symbols=['AMD'],
                start_date='2023-09-19',
                end_date='2024-09-19',
                strategies=['SMACrossover']
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  Completed in {elapsed:.1f} seconds")
            
            if results and 'SMACrossover' in results:
                result = results['SMACrossover']
                print("\n✅ RESULTS:")
                print(f"   Strategy: {result.strategy}")
                print(f"   Total Return: {result.total_return_pct:.2f}%")
                print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
                print(f"   Max Drawdown: {result.max_drawdown_pct:.2f}%")
                print(f"   Win Rate: {result.win_rate:.2f}")
                print(f"   Total Trades: {result.total_trades}")
                print(f"   Final Capital: ${result.final_capital:.2f}")
                
                if result.total_trades > 0:
                    print(f"\n📋 Trade Details:")
                    for i, trade in enumerate(result.trades[:5]):  # Show first 5 trades
                        print(f"   Trade {i+1}: {trade.action} {trade.quantity} shares at ${trade.price:.2f} on {trade.timestamp}")
                else:
                    print(f"\n⚠️  No trades generated - this might be the issue!")
                    
            else:
                print("❌ No results returned")
        else:
            print("❌ No market data retrieved")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f} seconds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_backtest())


