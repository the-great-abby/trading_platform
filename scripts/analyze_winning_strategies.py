#!/usr/bin/env python3
"""
Analyze Winning Strategies

This script analyzes backtest results to identify winning strategies
and helps combine them into more effective trading strategies.
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.database.backtest_results_service import BacktestResultsService
from src.utils.backtest_utils import format_backtest_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_winning_strategies(min_return_pct: float = 10.0, min_win_rate: float = 0.6, min_profit_factor: float = 1.5) -> List[Dict]:
    """
    Get winning strategies based on performance criteria
    
    Args:
        min_return_pct: Minimum total return percentage
        min_win_rate: Minimum win rate (0.0 to 1.0)
        min_profit_factor: Minimum profit factor
        
    Returns:
        List of winning strategy results
    """
    logger.info(f"Finding winning strategies with criteria:")
    logger.info(f"  Min Return: {min_return_pct}%")
    logger.info(f"  Min Win Rate: {min_win_rate:.1%}")
    logger.info(f"  Min Profit Factor: {min_profit_factor}")
    
    service = BacktestResultsService()
    all_runs = service.get_backtest_runs()
    
    winning_strategies = []
    
    for run in all_runs:
        # Check if this run meets our criteria
        if (run['total_return_pct'] >= min_return_pct and
            run['win_rate'] >= min_win_rate and
            run['profit_factor'] >= min_profit_factor):
            
            winning_strategies.append(run)
    
    logger.info(f"Found {len(winning_strategies)} winning strategies")
    return winning_strategies


def analyze_strategy_patterns(winning_strategies: List[Dict]) -> Dict:
    """
    Analyze patterns in winning strategies
    
    Args:
        winning_strategies: List of winning strategy results
        
    Returns:
        Analysis of strategy patterns
    """
    logger.info("Analyzing strategy patterns...")
    
    # Group by backtest name
    backtest_groups = {}
    for strategy in winning_strategies:
        backtest_name = strategy.get('backtest_name', 'Unknown')
        if backtest_name not in backtest_groups:
            backtest_groups[backtest_name] = []
        backtest_groups[backtest_name].append(strategy)
    
    # Group by strategy name
    strategy_groups = {}
    for strategy in winning_strategies:
        strategy_name = strategy['strategy_name']
        if strategy_name not in strategy_groups:
            strategy_groups[strategy_name] = []
        strategy_groups[strategy_name].append(strategy)
    
    # Calculate statistics
    analysis = {
        'total_winning_strategies': len(winning_strategies),
        'unique_backtests': len(backtest_groups),
        'unique_strategies': len(strategy_groups),
        'backtest_performance': {},
        'strategy_performance': {},
        'top_performers': []
    }
    
    # Analyze backtest performance
    for backtest_name, strategies in backtest_groups.items():
        avg_return = sum(s['total_return_pct'] for s in strategies) / len(strategies)
        avg_win_rate = sum(s['win_rate'] for s in strategies) / len(strategies)
        avg_profit_factor = sum(s['profit_factor'] for s in strategies) / len(strategies)
        
        analysis['backtest_performance'][backtest_name] = {
            'count': len(strategies),
            'avg_return_pct': avg_return,
            'avg_win_rate': avg_win_rate,
            'avg_profit_factor': avg_profit_factor,
            'strategies': [s['strategy_name'] for s in strategies]
        }
    
    # Analyze strategy performance
    for strategy_name, strategies in strategy_groups.items():
        avg_return = sum(s['total_return_pct'] for s in strategies) / len(strategies)
        avg_win_rate = sum(s['win_rate'] for s in strategies) / len(strategies)
        avg_profit_factor = sum(s['profit_factor'] for s in strategies) / len(strategies)
        
        analysis['strategy_performance'][strategy_name] = {
            'count': len(strategies),
            'avg_return_pct': avg_return,
            'avg_win_rate': avg_win_rate,
            'avg_profit_factor': avg_profit_factor,
            'backtests': [s.get('backtest_name', 'Unknown') for s in strategies]
        }
    
    # Find top performers
    top_performers = sorted(winning_strategies, 
                           key=lambda x: x['total_return_pct'], 
                           reverse=True)[:10]
    
    analysis['top_performers'] = top_performers
    
    return analysis


def generate_strategy_combination_suggestions(analysis: Dict) -> List[Dict]:
    """
    Generate suggestions for combining winning strategies
    
    Args:
        analysis: Strategy analysis results
        
    Returns:
        List of combination suggestions
    """
    logger.info("Generating strategy combination suggestions...")
    
    suggestions = []
    
    # Find strategies that work well across multiple backtests
    strategy_performance = analysis['strategy_performance']
    backtest_performance = analysis['backtest_performance']
    
    # Look for strategies with high consistency
    consistent_strategies = []
    for strategy_name, perf in strategy_performance.items():
        if perf['count'] >= 2 and perf['avg_return_pct'] >= 15.0:
            consistent_strategies.append({
                'strategy_name': strategy_name,
                'performance': perf
            })
    
    # Sort by average return
    consistent_strategies.sort(key=lambda x: x['performance']['avg_return_pct'], reverse=True)
    
    # Generate combination suggestions
    for i, strategy1 in enumerate(consistent_strategies[:5]):
        for strategy2 in consistent_strategies[i+1:6]:
            suggestion = {
                'combination_name': f"{strategy1['strategy_name']}_plus_{strategy2['strategy_name']}",
                'strategies': [strategy1['strategy_name'], strategy2['strategy_name']],
                'expected_return': (strategy1['performance']['avg_return_pct'] + strategy2['performance']['avg_return_pct']) / 2,
                'expected_win_rate': (strategy1['performance']['avg_win_rate'] + strategy2['performance']['avg_win_rate']) / 2,
                'rationale': f"Combining {strategy1['strategy_name']} (avg {strategy1['performance']['avg_return_pct']:.1f}% return) with {strategy2['strategy_name']} (avg {strategy2['performance']['avg_return_pct']:.1f}% return)"
            }
            suggestions.append(suggestion)
    
    # Look for backtests with multiple winning strategies
    for backtest_name, perf in backtest_performance.items():
        if perf['count'] >= 2:
            strategies = perf['strategies']
            if len(strategies) >= 2:
                suggestion = {
                    'combination_name': f"{format_backtest_name(backtest_name)}_multi_strategy",
                    'strategies': strategies,
                    'expected_return': perf['avg_return_pct'],
                    'expected_win_rate': perf['avg_win_rate'],
                    'rationale': f"Multiple winning strategies found in {format_backtest_name(backtest_name)} backtest"
                }
                suggestions.append(suggestion)
    
    return suggestions


def print_analysis_report(analysis: Dict, suggestions: List[Dict]):
    """
    Print a comprehensive analysis report
    
    Args:
        analysis: Strategy analysis results
        suggestions: Strategy combination suggestions
    """
    print("\n" + "="*80)
    print("WINNING STRATEGIES ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Winning Strategies: {analysis['total_winning_strategies']}")
    print(f"  Unique Backtests: {analysis['unique_backtests']}")
    print(f"  Unique Strategies: {analysis['unique_strategies']}")
    
    print(f"\n🏆 TOP PERFORMERS:")
    for i, performer in enumerate(analysis['top_performers'][:5], 1):
        backtest_name = performer.get('backtest_name', 'Unknown')
        formatted_name = format_backtest_name(backtest_name)
        print(f"  {i}. {performer['strategy_name']} ({formatted_name})")
        print(f"     Return: {performer['total_return_pct']:.1f}% | Win Rate: {performer['win_rate']:.1%} | Profit Factor: {performer['profit_factor']:.2f}")
    
    print(f"\n📈 BACKTEST PERFORMANCE:")
    for backtest_name, perf in analysis['backtest_performance'].items():
        formatted_name = format_backtest_name(backtest_name)
        print(f"  {formatted_name}:")
        print(f"    Winning Strategies: {perf['count']}")
        print(f"    Avg Return: {perf['avg_return_pct']:.1f}%")
        print(f"    Avg Win Rate: {perf['avg_win_rate']:.1%}")
        print(f"    Strategies: {', '.join(perf['strategies'])}")
    
    print(f"\n🎯 STRATEGY PERFORMANCE:")
    for strategy_name, perf in analysis['strategy_performance'].items():
        print(f"  {strategy_name}:")
        print(f"    Runs: {perf['count']}")
        print(f"    Avg Return: {perf['avg_return_pct']:.1f}%")
        print(f"    Avg Win Rate: {perf['avg_win_rate']:.1%}")
        print(f"    Backtests: {', '.join(perf['backtests'])}")
    
    print(f"\n💡 STRATEGY COMBINATION SUGGESTIONS:")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"  {i}. {suggestion['combination_name']}")
        print(f"     Expected Return: {suggestion['expected_return']:.1f}%")
        print(f"     Expected Win Rate: {suggestion['expected_win_rate']:.1%}")
        print(f"     Rationale: {suggestion['rationale']}")
        print(f"     Strategies: {', '.join(suggestion['strategies'])}")
    
    print("\n" + "="*80)


def main():
    """Main analysis function"""
    logger.info("🚀 Starting Winning Strategies Analysis")
    
    # Get winning strategies
    winning_strategies = get_winning_strategies(
        min_return_pct=10.0,
        min_win_rate=0.6,
        min_profit_factor=1.5
    )
    
    if not winning_strategies:
        logger.warning("No winning strategies found with current criteria")
        print("\n❌ No winning strategies found with current criteria.")
        print("Try lowering the minimum requirements:")
        print("  - Minimum return: 5.0%")
        print("  - Minimum win rate: 0.5")
        print("  - Minimum profit factor: 1.2")
        return
    
    # Analyze patterns
    analysis = analyze_strategy_patterns(winning_strategies)
    
    # Generate combination suggestions
    suggestions = generate_strategy_combination_suggestions(analysis)
    
    # Print report
    print_analysis_report(analysis, suggestions)
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"winning_strategies_analysis_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'analysis': analysis,
            'suggestions': suggestions,
            'winning_strategies': winning_strategies
        }, f, indent=2, default=str)
    
    logger.info(f"✅ Analysis complete! Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main() 