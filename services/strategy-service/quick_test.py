#!/usr/bin/env python3
"""
Quick Strategy Test - Single strategy only
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add src to path
sys.path.append('/app/src')

from src.backtesting.engine.backtest_engine import BacktestEngine

async def quick_test():
    """Run a quick test of a single strategy"""
    
    print("🚀 QUICK STRATEGY TEST")
    print("=" * 40)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💾 Database-only mode: {os.getenv('DATABASE_ONLY', 'false')}")
    
    # Initialize backtest engine
    print("\n🔧 Initializing backtest engine...")
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    print("✅ Engine initialized")
    
    # Test single strategy on single symbol
    print("\n📊 Testing SMACrossover on AMD only...")
    start_time = time.time()
    
    try:
        results = await engine.run_backtest(
            symbols=['AMD'],  # Single symbol only
            start_date='2023-09-19',
            end_date='2023-12-19',  # Shorter time period
            strategies=['SMACrossover']  # Single strategy only
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
        else:
            print("❌ No results returned")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f} seconds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())


