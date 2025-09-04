#!/usr/bin/env python3
"""
Fast Backtest Runner - Simple high-performance backtesting
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import get_symbols
logger = logging.getLogger(__name__)

class FastBacktestRunner:
    """Fast backtest runner with optimized performance"""
    
    def __init__(self):
        self.symbols = get_symbols()
        
        # Strategy groups for different performance profiles
        self.fast_strategies = [
            'MACD', 'RSI', 'BollingerBands', 'SMACrossover', 
            'Momentum', 'MeanReversion'
        ]
        
        self.medium_strategies = [
            'VolatilityBreakout', 'GreeksEnhanced'
        ]
        
        self.all_strategies = self.fast_strategies + self.medium_strategies
    
    async def run_fast_backtest(self, 
                               symbols: Optional[List[str]] = None,
                               strategies: Optional[List[str]] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               use_cache: bool = True,
                               parallel: bool = True,
                               max_workers: Optional[int] = None) -> Dict[str, Any]:
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
        
        logger.info("🚀 FAST BACKTEST RUNNER")
        logger.info("=" * 60)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Symbols: {len(symbols)} (limited for speed)")
        logger.info(f"   Strategies: {len(strategies)}")
        logger.info(f"   Period: {start_date} to {end_date}")
        logger.info(f"   Cache: {'Enabled' if use_cache else 'Disabled'}")
        logger.info(f"   Parallel: {'Enabled' if parallel else 'Disabled'}")
        
        start_time = time.time()
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=use_cache)
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        total_time = time.time() - start_time
        logger.info(f"⏱️  Total execution time: {total_time:.2f} seconds")
        
        return results
    
    async def run_quick_comparison(self) -> Dict[str, Any]:
        """Run quick comparison of fast vs medium strategies"""
        
        logger.info("⚡ QUICK STRATEGY COMPARISON")
        logger.info("=" * 60)
        
        # Test with limited symbols and short period
        test_symbols = self.symbols[:10]
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Test fast strategies
        logger.info("🏃 Testing fast strategies...")
        fast_start = time.time()
        fast_results = await self.run_fast_backtest(
            symbols=test_symbols,
            strategies=self.fast_strategies,
            start_date=start_date,
            end_date=end_date
        )
        fast_time = time.time() - fast_start
        
        # Test medium strategies
        logger.info("🏃 Testing medium strategies...")
        medium_start = time.time()
        medium_results = await self.run_fast_backtest(
            symbols=test_symbols,
            strategies=self.medium_strategies,
            start_date=start_date,
            end_date=end_date
        )
        medium_time = time.time() - medium_start
        
        # Compare results
        self._compare_strategy_performance(fast_results, medium_results, fast_time, medium_time)
        
        return {
            'fast': fast_results,
            'medium': medium_results,
            'fast_time': fast_time,
            'medium_time': medium_time
        }
    
    def _compare_strategy_performance(self, fast_results: Dict, medium_results: Dict, fast_time: float, medium_time: float):
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
        logger.info(f"   Execution time: {fast_time:.2f}s")
        
        # Analyze medium strategies
        medium_stats = self._analyze_results(medium_results)
        logger.info("🏃 Medium Strategies:")
        logger.info(f"   Total strategies: {medium_stats['total_strategies']}")
        logger.info(f"   Successful runs: {medium_stats['successful_runs']}")
        logger.info(f"   Average return: {medium_stats['avg_return']:.2f}%")
        logger.info(f"   Best strategy: {medium_stats['best_strategy']}")
        logger.info(f"   Execution time: {medium_time:.2f}s")
        
        # Performance comparison
        if fast_time > 0 and medium_time > 0:
            speed_ratio = medium_time / fast_time
            logger.info(f"⚡ Speed ratio (medium/fast): {speed_ratio:.1f}x")
        
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
            use_cache=not args.no_cache
        )
        
        logger.info(f"✅ Fast backtest completed with {len(results)} results")

if __name__ == "__main__":
    asyncio.run(main()) 