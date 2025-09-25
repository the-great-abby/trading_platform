#!/usr/bin/env python3
"""
Quick Fix Test - Use correct date range
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add src to path
sys.path.append('/app/src')

from src.backtesting.engine.backtest_engine import BacktestEngine

async def quick_fix_test():
    """Test with correct date range"""
    
    print("🚀 QUICK FIX TEST - Correct Date Range")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Use the ACTUAL date range where we have data
    start_date = '2023-11-28'  # When our data actually starts
    end_date = '2024-09-19'    # When our data ends
    
    print(f"📈 Using ACTUAL data range: {start_date} to {end_date}")
    
    start_time = time.time()
    
    try:
        results = await engine.run_backtest(
            symbols=['AMD'],
            start_date=start_date,
            end_date=end_date,
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
            
            if elapsed < 10:
                print(f"\n🎉 SUCCESS! Backtest completed in {elapsed:.1f}s - much faster!")
            else:
                print(f"\n⚠️  Still slow at {elapsed:.1f}s")
                
        else:
            print("❌ No results returned")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f} seconds: {e}")

if __name__ == "__main__":
    asyncio.run(quick_fix_test())


