#!/usr/bin/env python3
"""
Demo: Backtest Name Tracking

This script demonstrates the new backtest name tracking feature
that allows you to identify which backtest file was used for each run.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.database.backtest_results_service import BacktestResultsService
from src.utils.backtest_utils import get_backtest_name_from_script, format_backtest_name
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_backtest_with_name_tracking(symbols: List[str], start_date: str, end_date: str, backtest_name: Optional[str] = None):
    """
    Run a backtest with name tracking
    
    Args:
        symbols: List of symbols to test
        start_date: Start date for backtest
        end_date: End date for backtest
        backtest_name: Optional backtest name (will auto-detect if not provided)
    """
    logger.info(f"🚀 Running backtest with name tracking")
    
    # Get backtest name if not provided
    if backtest_name is None:
        backtest_name = get_backtest_name_from_script()
        logger.info(f"Auto-detected backtest name: {backtest_name}")
    
    # Create strategies
    strategies = {
        'MACD Strategy': MACDStrategy(),
        'Bollinger Bands Strategy': BollingerBandsStrategy()
    }
    
    # Create backtest engine
    engine = BacktestEngine()
    
    # Run backtest
    logger.info(f"Running backtest for {len(symbols)} symbols from {start_date} to {end_date}")
    logger.info(f"Backtest name: {backtest_name}")
    logger.info(f"Strategies: {list(strategies.keys())}")
    
    results = engine.run_backtest(
        strategies=strategies,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    # Store results with backtest name
    logger.info("Storing results with backtest name tracking...")
    engine.store_results(
        results=results,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        backtest_name=backtest_name
    )
    
    return results


def analyze_backtest_results_by_name():
    """
    Analyze backtest results grouped by backtest name
    """
    logger.info("📊 Analyzing backtest results by name")
    
    service = BacktestResultsService()
    all_runs = service.get_backtest_runs()
    
    # Group by backtest name
    backtest_groups = {}
    for run in all_runs:
        backtest_name = run.get('backtest_name', 'Unknown')
        if backtest_name not in backtest_groups:
            backtest_groups[backtest_name] = []
        backtest_groups[backtest_name].append(run)
    
    print("\n" + "="*80)
    print("BACKTEST NAME ANALYSIS")
    print("="*80)
    
    for backtest_name, runs in backtest_groups.items():
        if backtest_name == 'Unknown':
            continue
            
        formatted_name = format_backtest_name(backtest_name)
        print(f"\n📁 {formatted_name}:")
        print(f"   Total Runs: {len(runs)}")
        
        # Calculate statistics
        total_return_pct = sum(r['total_return_pct'] for r in runs)
        avg_return_pct = total_return_pct / len(runs) if runs else 0
        avg_win_rate = sum(r['win_rate'] for r in runs) / len(runs) if runs else 0
        avg_profit_factor = sum(r['profit_factor'] for r in runs) / len(runs) if runs else 0
        
        print(f"   Average Return: {avg_return_pct:.1f}%")
        print(f"   Average Win Rate: {avg_win_rate:.1%}")
        print(f"   Average Profit Factor: {avg_profit_factor:.2f}")
        
        # Show top performers
        top_runs = sorted(runs, key=lambda x: x['total_return_pct'], reverse=True)[:3]
        print(f"   Top Performers:")
        for i, run in enumerate(top_runs, 1):
            print(f"     {i}. {run['strategy_name']}: {run['total_return_pct']:.1f}% return, {run['win_rate']:.1%} win rate")
    
    print("\n" + "="*80)


def find_winning_strategies_by_backtest():
    """
    Find winning strategies grouped by backtest name
    """
    logger.info("🏆 Finding winning strategies by backtest")
    
    service = BacktestResultsService()
    all_runs = service.get_backtest_runs()
    
    # Define winning criteria
    min_return_pct = 10.0
    min_win_rate = 0.6
    min_profit_factor = 1.5
    
    winning_strategies = []
    for run in all_runs:
        if (run['total_return_pct'] >= min_return_pct and
            run['win_rate'] >= min_win_rate and
            run['profit_factor'] >= min_profit_factor):
            winning_strategies.append(run)
    
    # Group by backtest name
    backtest_winners = {}
    for strategy in winning_strategies:
        backtest_name = strategy.get('backtest_name', 'Unknown')
        if backtest_name not in backtest_winners:
            backtest_winners[backtest_name] = []
        backtest_winners[backtest_name].append(strategy)
    
    print(f"\n🏆 WINNING STRATEGIES (Return >= {min_return_pct}%, Win Rate >= {min_win_rate:.0%}, Profit Factor >= {min_profit_factor})")
    print("="*80)
    
    for backtest_name, strategies in backtest_winners.items():
        if backtest_name == 'Unknown':
            continue
            
        formatted_name = format_backtest_name(backtest_name)
        print(f"\n📁 {formatted_name}:")
        print(f"   Winning Strategies: {len(strategies)}")
        
        for strategy in strategies:
            print(f"   ✅ {strategy['strategy_name']}: {strategy['total_return_pct']:.1f}% return, {strategy['win_rate']:.1%} win rate, {strategy['profit_factor']:.2f} profit factor")


def demonstrate_backtest_name_utilities():
    """
    Demonstrate the backtest name utility functions
    """
    logger.info("🔧 Demonstrating backtest name utilities")
    
    print("\n" + "="*80)
    print("BACKTEST NAME UTILITIES DEMO")
    print("="*80)
    
    # Get current backtest name
    current_name = get_backtest_name_from_script()
    print(f"Current backtest name: {current_name}")
    
    # Format backtest names
    test_names = [
        "demo_strategy",
        "advanced_momentum_strategy", 
        "test_backtest_v1",
        "my_custom_strategy"
    ]
    
    print(f"\nFormatting examples:")
    for name in test_names:
        formatted = format_backtest_name(name)
        print(f"  '{name}' -> '{formatted}'")
    
    # Generate summary
    summary = f"Demo Strategy - MACD on AAPL, MSFT (2024-01-01 to 2024-12-31)"
    print(f"\nExample summary: {summary}")


def main():
    """Main demo function"""
    logger.info("🚀 Starting Backtest Name Tracking Demo")
    
    # Configuration
    symbols = ['AAPL', 'MSFT']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    print("\n" + "="*80)
    print("BACKTEST NAME TRACKING DEMO")
    print("="*80)
    
    # Step 1: Demonstrate utilities
    demonstrate_backtest_name_utilities()
    
    # Step 2: Run a backtest with name tracking
    print(f"\n📈 Step 2: Running backtest with name tracking")
    try:
        results = run_backtest_with_name_tracking(symbols, start_date, end_date)
        print(f"✅ Backtest completed successfully!")
        
        # Show results summary
        for strategy_name, result in results.items():
            print(f"  {strategy_name}: {result.total_return_pct:.1f}% return, {result.win_rate:.1%} win rate")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        print(f"⚠️ Backtest failed, but continuing with analysis...")
    
    # Step 3: Analyze existing results by backtest name
    print(f"\n📊 Step 3: Analyzing existing results by backtest name")
    analyze_backtest_results_by_name()
    
    # Step 4: Find winning strategies by backtest
    print(f"\n🏆 Step 4: Finding winning strategies by backtest")
    find_winning_strategies_by_backtest()
    
    print(f"\n✅ Backtest Name Tracking Demo completed!")
    print(f"\n💡 Key Benefits:")
    print(f"  • Track which backtest file was used for each run")
    print(f"  • Identify winning strategies across different backtests")
    print(f"  • Combine successful strategies for better performance")
    print(f"  • Analyze patterns in strategy performance")


if __name__ == "__main__":
    main() 