#!/usr/bin/env python3
"""
Comprehensive 2-Year Backtest with Options Integration
=====================================================
Runs comprehensive backtests using the full 2-year dataset:
- Standard strategies on all symbols for the full 2-year period
- Options/Greeks strategies for the last 60 days where options data is available
- Compares performance between standard and options-enhanced approaches
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.strategies.mean_reversion.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.momentum.momentum_strategy import MomentumStrategy
from src.strategies.breakout.sma_crossover import SMACrossoverStrategy
from src.strategies.breakout.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.strategies.advanced.trailing_stop_strategy import TrailingStopStrategy
from src.strategies.advanced.fibonacci_strategy import FibonacciStrategy
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.utils.config import get_config
from src.utils.enhanced_logging import get_trading_logger
from src.utils.trading_config import get_symbols, get_options_symbols

# Configure logging
logger = get_trading_logger()

class Comprehensive2YearBacktestRunner:
    """Runs comprehensive 2-year backtest with options integration"""
    
    def __init__(self):
        self.config = get_config()
        self.all_symbols = get_symbols()
        self.options_symbols = get_options_symbols()
        
        # Calculate date ranges
        self.end_date = datetime.now()
        self.start_date_2year = self.end_date - timedelta(days=2*365)  # Full 2 years
        self.start_date_60days = self.end_date - timedelta(days=60)    # Last 60 days for options
        
        logger.info(f"📊 Comprehensive 2-Year Backtest Configuration:")
        logger.info(f"   📅 Full 2-year period: {self.start_date_2year.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   📅 Options period (last 60 days): {self.start_date_60days.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   📈 Total symbols: {len(self.all_symbols)}")
        logger.info(f"   🎯 Options symbols: {len(self.options_symbols)}")
        
    async def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """Run comprehensive 2-year backtest with options integration"""
        
        logger.info("🚀 STARTING COMPREHENSIVE 2-YEAR BACKTEST")
        logger.info("=" * 80)
        
        # Phase 1: Standard strategies on all symbols for full 2-year period
        logger.info("📈 PHASE 1: Standard Strategies (Full 2-Year Period)")
        logger.info("-" * 60)
        
        standard_results = await self._run_standard_strategies()
        
        # Phase 2: Options/Greeks strategies for last 60 days
        logger.info("📊 PHASE 2: Options/Greeks Strategies (Last 60 Days)")
        logger.info("-" * 60)
        
        options_results = await self._run_options_strategies()
        
        # Phase 3: Compare and analyze results
        logger.info("📊 PHASE 3: Performance Analysis and Comparison")
        logger.info("-" * 60)
        
        comparison_results = self._compare_performance(standard_results, options_results)
        
        # Generate comprehensive report
        self._generate_comprehensive_report(standard_results, options_results, comparison_results)
        
        return {
            'standard_results': standard_results,
            'options_results': options_results,
            'comparison_results': comparison_results
        }
    
    async def _run_standard_strategies(self) -> Dict[str, Any]:
        """Run standard strategies on all symbols for full 2-year period"""
        
        # Define standard strategies (exact registry names)
        standard_strategies = [
            'BollingerBands',
            'MACD',
            'RSI',
            'MeanReversion',
            'Momentum',
            'SMACrossover',
            'VolatilityBreakout',
            'TrailingStop',
            'Fibonacci'
        ]
        
        logger.info(f"🎯 Running {len(standard_strategies)} standard strategies on {len(self.all_symbols)} symbols")
        logger.info(f"📅 Period: {self.start_date_2year.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=self.all_symbols,
            start_date=self.start_date_2year.strftime("%Y-%m-%d"),
            end_date=self.end_date.strftime("%Y-%m-%d"),
            strategies=standard_strategies
        )
        
        logger.info(f"✅ Standard strategies completed. Results for {len(results)} strategies")
        
        return results
    
    async def _run_options_strategies(self) -> Dict[str, Any]:
        """Run options/Greeks strategies for last 60 days"""
        
        # Define options strategies (exact registry name)
        options_strategies = [
            'GreeksEnhanced'
        ]
        
        logger.info(f"🎯 Running {len(options_strategies)} options strategies on {len(self.options_symbols)} symbols")
        logger.info(f"📅 Period: {self.start_date_60days.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest for options symbols only
        results = await engine.run_backtest(
            symbols=self.options_symbols,
            start_date=self.start_date_60days.strftime("%Y-%m-%d"),
            end_date=self.end_date.strftime("%Y-%m-%d"),
            strategies=options_strategies
        )
        
        logger.info(f"✅ Options strategies completed. Results for {len(results)} strategies")
        
        return results
    
    def _compare_performance(self, standard_results: Dict[str, Any], options_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance between standard and options strategies"""
        
        logger.info("📊 Comparing performance between standard and options strategies...")
        
        comparison = {
            'standard_performance': {},
            'options_performance': {},
            'performance_difference': {},
            'summary': {}
        }
        
        # Analyze standard strategy performance
        for strategy_name, result in standard_results.items():
            if hasattr(result, 'total_return_pct'):
                comparison['standard_performance'][strategy_name] = {
                    'return_pct': result.total_return_pct,
                    'trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown_pct': result.max_drawdown_pct
                }
        
        # Analyze options strategy performance
        for strategy_name, result in options_results.items():
            if hasattr(result, 'total_return_pct'):
                comparison['options_performance'][strategy_name] = {
                    'return_pct': result.total_return_pct,
                    'trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown_pct': result.max_drawdown_pct
                }
        
        # Calculate performance differences
        if comparison['standard_performance'] and comparison['options_performance']:
            # Compare best standard strategy vs options strategy
            best_standard = max(comparison['standard_performance'].items(), 
                              key=lambda x: x[1]['return_pct'])
            best_options = max(comparison['options_performance'].items(), 
                             key=lambda x: x[1]['return_pct'])
            
            comparison['performance_difference'] = {
                'best_standard': best_standard,
                'best_options': best_options,
                'return_difference': best_options[1]['return_pct'] - best_standard[1]['return_pct'],
                'risk_adjusted_difference': best_options[1]['sharpe_ratio'] - best_standard[1]['sharpe_ratio']
            }
        
        # Generate summary
        comparison['summary'] = {
            'total_standard_strategies': len(comparison['standard_performance']),
            'total_options_strategies': len(comparison['options_performance']),
            'avg_standard_return': sum(s['return_pct'] for s in comparison['standard_performance'].values()) / len(comparison['standard_performance']) if comparison['standard_performance'] else 0,
            'avg_options_return': sum(s['return_pct'] for s in comparison['options_performance'].values()) / len(comparison['options_performance']) if comparison['options_performance'] else 0
        }
        
        return comparison
    
    def _generate_comprehensive_report(self, standard_results: Dict[str, Any], options_results: Dict[str, Any], comparison_results: Dict[str, Any]):
        """Generate comprehensive performance report"""
        
        logger.info("\n" + "="*80)
        logger.info("📊 COMPREHENSIVE 2-YEAR BACKTEST REPORT")
        logger.info("="*80)
        
        # Standard strategies performance
        logger.info("\n📈 STANDARD STRATEGIES PERFORMANCE (2-Year Period)")
        logger.info("-" * 80)
        logger.info(f"{'Strategy':<25} {'Return %':<12} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 80)
        
        for strategy_name, result in standard_results.items():
            if hasattr(result, 'total_return_pct'):
                logger.info(f"{strategy_name:<25} {result.total_return_pct:>10.2f}% {result.total_trades:>6} {result.win_rate:>10.2f}% {result.sharpe_ratio:>6.2f} {result.max_drawdown_pct:>8.2f}%")
        
        # Options strategies performance
        logger.info("\n📊 OPTIONS STRATEGIES PERFORMANCE (60-Day Period)")
        logger.info("-" * 80)
        logger.info(f"{'Strategy':<25} {'Return %':<12} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 80)
        
        for strategy_name, result in options_results.items():
            if hasattr(result, 'total_return_pct'):
                logger.info(f"{strategy_name:<25} {result.total_return_pct:>10.2f}% {result.total_trades:>6} {result.win_rate:>10.2f}% {result.sharpe_ratio:>6.2f} {result.max_drawdown_pct:>8.2f}%")
        
        # Performance comparison
        if comparison_results.get('performance_difference'):
            diff = comparison_results['performance_difference']
            logger.info("\n🔍 PERFORMANCE COMPARISON")
            logger.info("-" * 50)
            logger.info(f"🏆 Best Standard Strategy: {diff['best_standard'][0]} ({diff['best_standard'][1]['return_pct']:.2f}%)")
            logger.info(f"🏆 Best Options Strategy: {diff['best_options'][0]} ({diff['best_options'][1]['return_pct']:.2f}%)")
            logger.info(f"📈 Return Difference: {diff['return_difference']:.2f}%")
            logger.info(f"📊 Risk-Adjusted Difference: {diff['risk_adjusted_difference']:.2f}")
        
        # Summary statistics
        summary = comparison_results.get('summary', {})
        logger.info("\n📊 SUMMARY STATISTICS")
        logger.info("-" * 50)
        logger.info(f"📈 Standard Strategies Tested: {summary.get('total_standard_strategies', 0)}")
        logger.info(f"📊 Options Strategies Tested: {summary.get('total_options_strategies', 0)}")
        logger.info(f"📈 Average Standard Return: {summary.get('avg_standard_return', 0):.2f}%")
        logger.info(f"📊 Average Options Return: {summary.get('avg_options_return', 0):.2f}%")
        
        logger.info("\n" + "="*80)
        logger.info("✅ COMPREHENSIVE 2-YEAR BACKTEST COMPLETED")
        logger.info("="*80)

async def main():
    """Main function to run the comprehensive 2-year backtest"""
    
    try:
        runner = Comprehensive2YearBacktestRunner()
        results = await runner.run_comprehensive_backtest()
        
        logger.info("🎉 Comprehensive 2-year backtest completed successfully!")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error running comprehensive backtest: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 