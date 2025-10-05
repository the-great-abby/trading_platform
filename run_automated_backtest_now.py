#!/usr/bin/env python3
"""
Quick Automated Strategy Selection Backtest
==========================================

Runs a quick backtest of the automated strategy selection system using your existing
backtest infrastructure. This script demonstrates the automated strategy selection
concept with a 2-year historical test.

Usage:
    python run_automated_backtest_now.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger

# Setup logging
logger = get_trading_logger()

async def run_automated_strategy_backtest():
    """Run automated strategy selection backtest"""
    
    logger.info("🚀 Starting Automated Strategy Selection Backtest")
    logger.info("=" * 60)
    
    # Configuration
    start_date = "2022-01-01"
    end_date = "2024-01-01"
    initial_capital = 100000.0
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    
    logger.info(f"📊 Configuration:")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"   Symbols: {', '.join(symbols)}")
    
    # Initialize backtest engine
    engine = BacktestEngine(
        use_real_data=True,
        use_cache=True
    )
    
    # Define strategies to test
    strategies = [
        'SMACrossoverStrategy',
        'RSIStrategy',
        'MACDStrategy',
        'BollingerBandsStrategy',
        'MeanReversionStrategy',
        'MomentumStrategy',
        'VolatilityBreakoutStrategy',
        'RegimeSwitchingStrategy'
    ]
    
    logger.info(f"🎯 Testing {len(strategies)} strategies:")
    for strategy in strategies:
        logger.info(f"   - {strategy}")
    
    # Run individual strategy backtests
    logger.info("\n🔄 Running individual strategy backtests...")
    individual_results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=strategies
    )
    
    # Analyze results and simulate automated selection
    logger.info("\n🤖 Simulating automated strategy selection...")
    automated_results = simulate_automated_selection(individual_results, symbols)
    
    # Generate report
    logger.info("\n📊 AUTOMATED STRATEGY SELECTION RESULTS")
    logger.info("=" * 60)
    
    if automated_results:
        logger.info(f"🎯 Automated Selection Performance:")
        logger.info(f"   Total Return: {automated_results['total_return']:.2f}%")
        logger.info(f"   Sharpe Ratio: {automated_results['sharpe_ratio']:.2f}")
        logger.info(f"   Max Drawdown: {automated_results['max_drawdown']:.2f}%")
        logger.info(f"   Win Rate: {automated_results['win_rate']:.2f}")
        logger.info(f"   Total Trades: {automated_results['total_trades']}")
        
        logger.info(f"\n📈 Strategy Selection Distribution:")
        for strategy, count in automated_results['strategy_distribution'].items():
            logger.info(f"   {strategy}: {count} selections")
        
        logger.info(f"\n🎯 Individual Symbol Results:")
        for symbol, result in automated_results['symbol_results'].items():
            logger.info(f"   {symbol}: {result['strategy']} ({result['return']:.2f}% return)")
        
        # Compare with best individual strategy
        if 'best_individual' in automated_results:
            best_name = automated_results['best_individual']['name']
            best_return = automated_results['best_individual']['return']
            improvement = automated_results['total_return'] - best_return
            
            logger.info(f"\n🏆 Comparison with Best Individual Strategy:")
            logger.info(f"   Best Individual: {best_name} ({best_return:.2f}%)")
            logger.info(f"   Automated: {automated_results['total_return']:.2f}%")
            logger.info(f"   Improvement: {improvement:.2f}%")
    
    # Save results
    results_file = f"automated_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(automated_results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to {results_file}")
    logger.info("🎉 Automated Strategy Selection Backtest completed!")

def simulate_automated_selection(individual_results: Dict[str, Any], symbols: List[str]) -> Dict[str, Any]:
    """Simulate automated strategy selection based on individual results"""
    
    if not individual_results:
        return {}
    
    # Strategy selection rules (simplified)
    strategy_rules = {
        'bull_market': ['SMACrossoverStrategy', 'MACDStrategy', 'MomentumStrategy'],
        'bear_market': ['SMACrossoverStrategy', 'MACDStrategy', 'MeanReversionStrategy'],
        'sideways': ['BollingerBandsStrategy', 'RSIStrategy', 'MeanReversionStrategy'],
        'volatile': ['VolatilityBreakoutStrategy', 'RegimeSwitchingStrategy']
    }
    
    # Analyze each symbol and select best strategy
    symbol_results = {}
    strategy_distribution = {}
    returns = []
    sharpe_ratios = []
    max_drawdowns = []
    win_rates = []
    total_trades = 0
    
    for symbol in symbols:
        # Determine market condition (simplified)
        market_condition = determine_market_condition(symbol, individual_results)
        
        # Get available strategies for this condition
        available_strategies = strategy_rules.get(market_condition, ['SMACrossoverStrategy'])
        
        # Select best performing strategy
        best_strategy = None
        best_return = -float('inf')
        
        for strategy_name in available_strategies:
            if strategy_name in individual_results:
                strategy_result = individual_results[strategy_name]
                if strategy_result and hasattr(strategy_result, 'symbols'):
                    symbol_result = getattr(strategy_result.symbols, symbol, None)
                    if symbol_result:
                        symbol_return = getattr(symbol_result, 'total_return_pct', 0.0)
                        if symbol_return > best_return:
                            best_return = symbol_return
                            best_strategy = strategy_name
        
        if best_strategy:
            # Get full performance metrics
            strategy_result = individual_results[best_strategy]
            symbol_result = getattr(strategy_result.symbols, symbol, None)
            
            if symbol_result:
                symbol_return = getattr(symbol_result, 'total_return_pct', 0.0)
                sharpe_ratio = getattr(symbol_result, 'sharpe_ratio', 0.0)
                max_drawdown = getattr(symbol_result, 'max_drawdown_pct', 0.0)
                win_rate = getattr(symbol_result, 'win_rate', 0.0)
                trades = getattr(symbol_result, 'total_trades', 0)
                
                symbol_results[symbol] = {
                    'strategy': best_strategy,
                    'return': symbol_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'trades': trades
                }
                
                # Update aggregates
                returns.append(symbol_return)
                sharpe_ratios.append(sharpe_ratio)
                max_drawdowns.append(max_drawdown)
                win_rates.append(win_rate)
                total_trades += trades
                
                # Update strategy distribution
                strategy_distribution[best_strategy] = strategy_distribution.get(best_strategy, 0) + 1
    
    # Calculate averages
    avg_return = sum(returns) / len(returns) if returns else 0.0
    avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0.0
    avg_drawdown = sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0.0
    avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
    
    # Find best individual strategy for comparison
    best_individual = None
    best_individual_return = -float('inf')
    
    for strategy_name, strategy_result in individual_results.items():
        if strategy_result and hasattr(strategy_result, 'total_return_pct'):
            strategy_return = getattr(strategy_result, 'total_return_pct', 0.0)
            if strategy_return > best_individual_return:
                best_individual_return = strategy_return
                best_individual = {
                    'name': strategy_name,
                    'return': strategy_return
                }
    
    return {
        'total_return': avg_return,
        'sharpe_ratio': avg_sharpe,
        'max_drawdown': avg_drawdown,
        'win_rate': avg_win_rate,
        'total_trades': total_trades,
        'strategy_distribution': strategy_distribution,
        'symbol_results': symbol_results,
        'best_individual': best_individual
    }

def determine_market_condition(symbol: str, individual_results: Dict[str, Any]) -> str:
    """Determine market condition for a symbol (simplified)"""
    
    # This is a simplified market condition determination
    # In practice, this would analyze technical indicators, volatility, etc.
    
    # For demonstration, we'll use a simple rule based on symbol performance
    if symbol in ['AAPL', 'MSFT', 'GOOGL']:
        return 'bull_market'
    elif symbol in ['TSLA', 'NVDA']:
        return 'volatile'
    else:
        return 'sideways'

async def main():
    """Main function"""
    try:
        await run_automated_strategy_backtest()
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

















