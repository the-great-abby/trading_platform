#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/src')
from src.backtesting.engine.backtest_engine import BacktestEngine
import asyncio

async def run_test():
    print('🚀 Testing backtest with DATABASE_ONLY=true...')
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    results = await engine.run_backtest(
        symbols=['AMD'],
        start_date='2023-09-19',
        end_date='2024-09-19',
        strategies=['SMACrossover']
    )
    
    if results and 'SMACrossover' in results:
        result = results['SMACrossover']
        print('✅ Backtest Results:')
        print(f'   Strategy: {result.strategy}')
        print(f'   Total Return: {result.total_return_pct:.2f}%')
        print(f'   Sharpe Ratio: {result.sharpe_ratio:.2f}')
        print(f'   Max Drawdown: {result.max_drawdown_pct:.2f}%')
        print(f'   Win Rate: {result.win_rate:.2f}')
        print(f'   Total Trades: {result.total_trades}')
        print(f'   Initial Capital: ${result.initial_capital:.2f}')
        print(f'   Final Capital: ${result.final_capital:.2f}')
    else:
        print('❌ No results returned')

if __name__ == "__main__":
    asyncio.run(run_test())
