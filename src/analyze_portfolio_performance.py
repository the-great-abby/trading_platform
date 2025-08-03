#!/usr/bin/env python3
"""
Portfolio Performance Analysis - 2 Year Period
Analyzes backtest results to show portfolio performance over the 2-year period
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


async def analyze_portfolio_performance():
    """Analyze portfolio performance over the 2-year period"""
    
    print("📊 PORTFOLIO PERFORMANCE ANALYSIS - 2 YEAR PERIOD")
    print("=" * 70)
    
    # Initialize services
    service = BacktestResultsService()
    
    # Get all backtest runs
    try:
        results = service.get_backtest_runs()
        print(f"📈 Found {len(results)} backtest runs in database")
        
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
                duration_days = (end_date - start_date).days
                if 600 <= duration_days <= 800:  # Roughly 2 years
                    two_year_results.append(result)
        
        print(f"📅 Found {len(two_year_results)} backtest runs covering ~2-year periods")
        
        if not two_year_results:
            print("❌ No 2-year period backtest results found")
            print("💡 Available periods:")
            for result in results[:5]:  # Show first 5
                if result['start_date'] and result['end_date']:
                    start_date = datetime.strptime(result['start_date'], "%Y-%m-%d").date()
                    end_date = datetime.strptime(result['end_date'], "%Y-%m-%d").date()
                    duration = (end_date - start_date).days
                    print(f"   {result['run_id']}: {result['start_date']} to {result['end_date']} ({duration} days)")
            return
        
        # Analyze performance by strategy
        strategy_performance = {}
        for result in two_year_results:
            strategy = result['strategy_name']
            if strategy not in strategy_performance:
                strategy_performance[strategy] = []
            strategy_performance[strategy].append(result)
        
        print(f"\n📊 PERFORMANCE BY STRATEGY (2-Year Period)")
        print("-" * 70)
        
        # Calculate aggregate metrics for each strategy
        strategy_summary = []
        for strategy, runs in strategy_performance.items():
            if not runs:
                continue
                
            # Calculate average metrics
            avg_return = sum(r['total_return_pct'] for r in runs) / len(runs)
            avg_sharpe = sum(r['sharpe_ratio'] for r in runs) / len(runs)
            avg_max_dd = sum(r['max_drawdown_pct'] for r in runs) / len(runs)
            avg_win_rate = sum(r['win_rate'] for r in runs) / len(runs)
            total_trades = sum(r['total_trades'] for r in runs)
            avg_trades = total_trades / len(runs)
            
            strategy_summary.append({
                'strategy': strategy,
                'runs': len(runs),
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'avg_max_dd': avg_max_dd,
                'avg_win_rate': avg_win_rate,
                'avg_trades': avg_trades,
                'total_trades': total_trades
            })
        
        # Sort by average return
        strategy_summary.sort(key=lambda x: x['avg_return'], reverse=True)
        
        # Display results
        print(f"{'Strategy':<25} {'Runs':<6} {'Avg Return %':<12} {'Avg Sharpe':<10} {'Avg Max DD %':<12} {'Avg Win Rate %':<15} {'Avg Trades':<10}")
        print("-" * 100)
        
        for summary in strategy_summary:
            print(f"{summary['strategy']:<25} {summary['runs']:<6} {summary['avg_return']:>10.2f}% "
                  f"{summary['avg_sharpe']:>8.3f} {summary['avg_max_dd']:>10.2f}% "
                  f"{summary['avg_win_rate']*100:>12.1f}% {summary['avg_trades']:>8.1f}")
        
        # Best performing strategy
        if strategy_summary:
            best = strategy_summary[0]
            print(f"\n🏆 BEST PERFORMING STRATEGY: {best['strategy']}")
            print(f"   📈 Average Return: {best['avg_return']:.2f}%")
            print(f"   📊 Average Sharpe Ratio: {best['avg_sharpe']:.3f}")
            print(f"   📉 Average Max Drawdown: {best['avg_max_dd']:.2f}%")
            print(f"   ✅ Average Win Rate: {best['avg_win_rate']*100:.1f}%")
            print(f"   🔄 Average Trades per Run: {best['avg_trades']:.1f}")
            print(f"   📊 Total Runs: {best['runs']}")
        
        # Portfolio-level analysis
        print(f"\n📊 PORTFOLIO-LEVEL ANALYSIS")
        print("-" * 50)
        
        # Calculate overall portfolio metrics
        all_returns = [r['total_return_pct'] for r in two_year_results]
        all_sharpes = [r['sharpe_ratio'] for r in two_year_results]
        all_drawdowns = [r['max_drawdown_pct'] for r in two_year_results]
        all_win_rates = [r['win_rate'] for r in two_year_results]
        
        print(f"📈 Overall Portfolio Performance (2-Year Period):")
        print(f"   📊 Total Backtest Runs: {len(two_year_results)}")
        print(f"   📈 Average Return: {sum(all_returns)/len(all_returns):.2f}%")
        print(f"   📊 Average Sharpe Ratio: {sum(all_sharpes)/len(all_sharpes):.3f}")
        print(f"   📉 Average Max Drawdown: {sum(all_drawdowns)/len(all_drawdowns):.2f}%")
        print(f"   ✅ Average Win Rate: {sum(all_win_rates)/len(all_win_rates)*100:.1f}%")
        print(f"   🔄 Total Trades Across All Runs: {sum(r['total_trades'] for r in two_year_results)}")
        
        # Risk analysis
        print(f"\n🔒 RISK ANALYSIS")
        print("-" * 30)
        
        positive_returns = [r for r in all_returns if r > 0]
        negative_returns = [r for r in all_returns if r < 0]
        
        print(f"   📈 Positive Return Runs: {len(positive_returns)} ({len(positive_returns)/len(all_returns)*100:.1f}%)")
        print(f"   📉 Negative Return Runs: {len(negative_returns)} ({len(negative_returns)/len(all_returns)*100:.1f}%)")
        
        if positive_returns:
            print(f"   🎯 Best Single Run: {max(all_returns):.2f}%")
        if negative_returns:
            print(f"   📉 Worst Single Run: {min(all_returns):.2f}%")
        
        # Market regime analysis (if we have date information)
        print(f"\n📅 TIME PERIOD ANALYSIS")
        print("-" * 30)
        
        for result in two_year_results[:5]:  # Show first 5
            if result['start_date'] and result['end_date']:
                start_date = datetime.strptime(result['start_date'], "%Y-%m-%d").date()
                end_date = datetime.strptime(result['end_date'], "%Y-%m-%d").date()
                duration = (end_date - start_date).days
                print(f"   {result['strategy_name']}: {result['start_date']} to {result['end_date']} "
                      f"({duration} days) - {result['total_return_pct']:.2f}% return")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 30)
        
        if strategy_summary:
            best_strategy = strategy_summary[0]
            print(f"   🎯 Best Strategy: {best_strategy['strategy']} ({best_strategy['avg_return']:.2f}% avg return)")
            
            # Find most consistent strategy (lowest drawdown)
            most_consistent = min(strategy_summary, key=lambda x: x['avg_max_dd'])
            print(f"   🔒 Most Consistent: {most_consistent['strategy']} ({most_consistent['avg_max_dd']:.2f}% avg max drawdown)")
            
            # Find highest Sharpe ratio
            best_risk_adjusted = max(strategy_summary, key=lambda x: x['avg_sharpe'])
            print(f"   📊 Best Risk-Adjusted: {best_risk_adjusted['strategy']} ({best_risk_adjusted['avg_sharpe']:.3f} avg Sharpe)")
        
        print(f"\n📈 Next Steps:")
        print(f"   1. Run more backtests with different parameters")
        print(f"   2. Test strategies on different market conditions")
        print(f"   3. Implement portfolio optimization")
        print(f"   4. Add real-time monitoring for live trading")
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio performance: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(analyze_portfolio_performance()) 