#!/usr/bin/env python3
"""
Fast Backtest Runner - High-performance backtesting with parallel processing
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.optimized_backtest_engine import OptimizedBacktestEngine, BacktestConfig
from src.utils.trading_config import get_symbols, get_config
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class FastBacktestRunner:
    """Fast backtest runner with optimized performance"""
    
    def __init__(self):
        self.config = get_config()
        self.symbols = get_symbols()
        
        # Strategy groups for different performance profiles
        self.fast_strategies = [
            'MACD', 'RSI', 'BollingerBands', 'SMACrossover', 
            'Momentum', 'MeanReversion'
        ]
        
        self.medium_strategies = [
            'VolatilityBreakout', 'Ichimoku', 'GreeksEnhanced'
        ]
        
        self.slow_strategies = [
            'AdaptiveMomentum', 'RegimeSwitching', 'QuantumMomentum', 'NeuralNetwork'
        ]
        
        self.all_strategies = self.fast_strategies + self.medium_strategies + self.slow_strategies
    
    async def run_fast_backtest(self, 
                               symbols: List[str] = None,
                               strategies: List[str] = None,
                               start_date: str = None,
                               end_date: str = None,
                               use_cache: bool = True,
                               parallel: bool = True,
                               max_workers: int = None) -> Dict[str, Any]:
        """Run fast backtest with optimized settings"""
        
        # Default values
        if symbols is None:
            symbols = self.symbols[:20]  # Limit to 20 symbols for speed
        
        if strategies is None:
            strategies = self.fast_strategies  # Use fast strategies by default
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if max_workers is None:
            max_workers = min(8, len(symbols))
        
        logger.info("🚀 FAST BACKTEST RUNNER")
        logger.info("=" * 60)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Symbols: {len(symbols)} (limited for speed)")
        logger.info(f"   Strategies: {len(strategies)}")
        logger.info(f"   Period: {start_date} to {end_date}")
        logger.info(f"   Parallel: {'Enabled' if parallel else 'Disabled'}")
        logger.info(f"   Cache: {'Enabled' if use_cache else 'Disabled'}")
        logger.info(f"   Max workers: {max_workers}")
        
        # Create optimized config
        backtest_config = BacktestConfig(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies,
            use_cache=use_cache,
            parallel_strategies=parallel,
            max_workers=max_workers,
            batch_size=5,  # Smaller batches for faster processing
            timeout_hours=2  # Shorter timeout
        )
        
        # Run optimized backtest
        engine = OptimizedBacktestEngine(backtest_config)
        results = await engine.run_optimized_backtest()
        
        return results
    
    async def run_quick_comparison(self) -> Dict[str, Any]:
        """Run quick comparison of fast vs slow strategies"""
        
        logger.info("⚡ QUICK STRATEGY COMPARISON")
        logger.info("=" * 60)
        
        # Test with limited symbols and short period
        test_symbols = self.symbols[:10]
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Test fast strategies
        logger.info("🏃 Testing fast strategies...")
        fast_results = await self.run_fast_backtest(
            symbols=test_symbols,
            strategies=self.fast_strategies,
            start_date=start_date,
            end_date=end_date
        )
        
        # Test medium strategies
        logger.info("🏃 Testing medium strategies...")
        medium_results = await self.run_fast_backtest(
            symbols=test_symbols,
            strategies=self.medium_strategies,
            start_date=start_date,
            end_date=end_date
        )
        
        # Compare results
        self._compare_strategy_performance(fast_results, medium_results)
        
        return {
            'fast': fast_results,
            'medium': medium_results
        }
    
    def _compare_strategy_performance(self, fast_results: Dict, medium_results: Dict):
        """Compare performance between strategy groups"""
        
        logger.info("📊 PERFORMANCE COMPARISON")
        logger.info("=" * 60)
        
        # Analyze fast strategies
        fast_stats = self._analyze_results(fast_results)
        logger.info("⚡ Fast Strategies:")
        logger.info(f"   Total strategies: {fast_stats['total_strategies']}")
        logger.info(f"   Successful runs: {fast_stats['successful_runs']}")
        logger.info(f"   Average return: {fast_stats['avg_return']:.2f}%")
        logger.info(f"   Best strategy: {fast_stats['best_strategy']}")
        
        # Analyze medium strategies
        medium_stats = self._analyze_results(medium_results)
        logger.info("🏃 Medium Strategies:")
        logger.info(f"   Total strategies: {medium_stats['total_strategies']}")
        logger.info(f"   Successful runs: {medium_stats['successful_runs']}")
        logger.info(f"   Average return: {medium_stats['avg_return']:.2f}%")
        logger.info(f"   Best strategy: {medium_stats['best_strategy']}")
        
        # Performance recommendation
        if fast_stats['avg_return'] > medium_stats['avg_return']:
            logger.info("✅ Fast strategies performed better - use for quick analysis")
        else:
            logger.info("🏃 Medium strategies performed better - consider for detailed analysis")
    
    def _analyze_results(self, results: Dict) -> Dict[str, Any]:
        """Analyze backtest results"""
        
        if not results:
            return {
                'total_strategies': 0,
                'successful_runs': 0,
                'avg_return': 0.0,
                'best_strategy': 'None'
            }
        
        successful_runs = 0
        total_return = 0.0
        best_strategy = None
        best_return = -999.0
        
        for key, result in results.items():
            if result and hasattr(result, 'total_return_pct'):
                successful_runs += 1
                total_return += result.total_return_pct
                
                if result.total_return_pct > best_return:
                    best_return = result.total_return_pct
                    best_strategy = key
        
        avg_return = total_return / successful_runs if successful_runs > 0 else 0.0
        
        return {
            'total_strategies': len(results),
            'successful_runs': successful_runs,
            'avg_return': avg_return,
            'best_strategy': best_strategy
        }

async def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='Fast Backtest Runner')
    parser.add_argument('--symbols', nargs='+', help='Symbols to test')
    parser.add_argument('--strategies', nargs='+', help='Strategies to test')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel processing')
    parser.add_argument('--max-workers', type=int, help='Maximum workers')
    parser.add_argument('--quick', action='store_true', help='Run quick comparison')
    parser.add_argument('--fast-only', action='store_true', help='Run only fast strategies')
    parser.add_argument('--medium-only', action='store_true', help='Run only medium strategies')
    
    args = parser.parse_args()
    
    runner = FastBacktestRunner()
    
    if args.quick:
        # Run quick comparison
        await runner.run_quick_comparison()
    else:
        # Determine strategies to run
        strategies = None
        if args.fast_only:
            strategies = runner.fast_strategies
        elif args.medium_only:
            strategies = runner.medium_strategies
        elif args.strategies:
            strategies = args.strategies
        
        # Run fast backtest
        results = await runner.run_fast_backtest(
            symbols=args.symbols,
            strategies=strategies,
            start_date=args.start_date,
            end_date=args.end_date,
            use_cache=not args.no_cache,
            parallel=not args.no_parallel,
            max_workers=args.max_workers
        )
        
        logger.info(f"✅ Fast backtest completed with {len(results)} results")

if __name__ == "__main__":
    asyncio.run(main()) 