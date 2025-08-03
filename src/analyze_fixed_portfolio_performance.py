#!/usr/bin/env python3
"""
Fixed Portfolio Performance Analysis - 2 Year Period
Analyzes backtest results with the fixed database storage
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.database.backtest_results_service import BacktestResultsService
from src.utils.config import get_config
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


async def analyze_fixed_portfolio_performance():
    """Analyze portfolio performance with fixed database storage"""
    
    print("📊 FIXED PORTFOLIO PERFORMANCE ANALYSIS - 2 YEAR PERIOD")
    print("=" * 70)
    
    try:
        # Initialize service
        service = BacktestResultsService()
        print("✅ Database service initialized")
        
        # Get all backtest runs
        results = service.get_backtest_runs()
        print(f"📈 Found {len(results)} total backtest runs in database")
        
        if not results:
            print("❌ No backtest results found in database")
            print("💡 Run some backtests first to see performance data")
            return
        
        # Filter for 2-year period (approximately 2023-2025)
        two_year_results = []
        for result in results:
            if result['start_date'] and result['end_date']:
                # Check if this is approximately a 2-year period
                start_date = datetime.strptime(result['start_date'], "%Y-%m-%d").date()
                end_date = datetime.strptime(result['end_date'], "%Y-%m-%d").date()
                days_diff = (end_date - start_date).days
                
                # Consider runs with 600-800 days as 2-year periods
                if 600 <= days_diff <= 800:
                    two_year_results.append(result)
        
        print(f"📅 Found {len(two_year_results)} backtest runs covering ~2-year periods")
        
        if not two_year_results:
            print("❌ No 2-year period backtest runs found")
            print("💡 Run comprehensive backtests to see 2-year performance")
            return
        
        # Analyze performance by strategy
        strategy_performance = {}
        total_trades = 0
        total_return = 0.0
        
        for result in two_year_results:
            strategy = result['strategy_name']
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    'runs': 0,
                    'total_return': 0.0,
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                }
            
            strategy_performance[strategy]['runs'] += 1
            strategy_performance[strategy]['total_return'] += result['total_return_pct']
            strategy_performance[strategy]['total_trades'] += result['total_trades']
            strategy_performance[strategy]['win_rate'] += result['win_rate']
            strategy_performance[strategy]['sharpe_ratio'] += result['sharpe_ratio']
            strategy_performance[strategy]['max_drawdown'] += result['max_drawdown_pct']
            
            total_trades += result['total_trades']
            total_return += result['total_return_pct']
        
        # Calculate averages
        for strategy in strategy_performance:
            runs = strategy_performance[strategy]['runs']
            if runs > 0:
                strategy_performance[strategy]['avg_return'] = strategy_performance[strategy]['total_return'] / runs
                strategy_performance[strategy]['avg_win_rate'] = strategy_performance[strategy]['win_rate'] / runs
                strategy_performance[strategy]['avg_sharpe'] = strategy_performance[strategy]['sharpe_ratio'] / runs
                strategy_performance[strategy]['avg_drawdown'] = strategy_performance[strategy]['max_drawdown'] / runs
        
        # Display results
        print(f"\n📊 PORTFOLIO PERFORMANCE SUMMARY (2-Year Period)")
        print(f"📈 Total Backtest Runs: {len(two_year_results)}")
        print(f"📈 Total Trades: {total_trades}")
        print(f"📈 Average Return: {total_return / len(two_year_results):.2f}%")
        print(f"📈 Strategies Tested: {len(strategy_performance)}")
        
        print(f"\n🏆 STRATEGY PERFORMANCE BREAKDOWN:")
        print("-" * 80)
        
        # Sort strategies by average return
        sorted_strategies = sorted(
            strategy_performance.items(), 
            key=lambda x: x[1]['avg_return'], 
            reverse=True
        )
        
        for strategy_name, performance in sorted_strategies:
            print(f"📊 {strategy_name}:")
            print(f"   Runs: {performance['runs']}")
            print(f"   Avg Return: {performance['avg_return']:.2f}%")
            print(f"   Avg Win Rate: {performance['avg_win_rate']:.2f}%")
            print(f"   Avg Sharpe: {performance['avg_sharpe']:.2f}")
            print(f"   Avg Max Drawdown: {performance['avg_drawdown']:.2f}%")
            print(f"   Total Trades: {performance['total_trades']}")
            print()
        
        # Show top performing strategies
        if sorted_strategies:
            best_strategy = sorted_strategies[0]
            print(f"🏆 BEST PERFORMING STRATEGY:")
            print(f"   {best_strategy[0]}: {best_strategy[1]['avg_return']:.2f}% return")
            
            worst_strategy = sorted_strategies[-1]
            print(f"📉 WORST PERFORMING STRATEGY:")
            print(f"   {worst_strategy[0]}: {worst_strategy[1]['avg_return']:.2f}% return")
        
        # Show recent runs
        print(f"\n🕒 RECENT BACKTEST RUNS:")
        print("-" * 80)
        
        recent_runs = sorted(two_year_results, key=lambda x: x['created_at'], reverse=True)[:5]
        for run in recent_runs:
            print(f"📊 {run['run_id']}")
            print(f"   Strategy: {run['strategy_name']}")
            print(f"   Period: {run['start_date']} to {run['end_date']}")
            print(f"   Return: {run['total_return_pct']:.2f}%")
            print(f"   Trades: {run['total_trades']}")
            print(f"   Win Rate: {run['win_rate']:.2f}%")
            print(f"   Sharpe: {run['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown: {run['max_drawdown_pct']:.2f}%")
            print()
        
        print("🎉 Portfolio performance analysis completed!")
        
    except Exception as e:
        print(f"❌ Error analyzing portfolio performance: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_fixed_portfolio_performance()) 