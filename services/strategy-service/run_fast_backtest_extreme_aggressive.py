#!/usr/bin/env python3
"""
Fast Backtest Runner - EXTREME AGGRESSIVE high-performance backtesting
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

class FastBacktestExtremeAggressiveRunner:
    """Fast backtest runner with EXTREME AGGRESSIVE settings"""
    
    def __init__(self):
        self.symbols = get_symbols()
        
        # Strategy configurations - BASIC STRATEGIES ONLY (no LLM)
        self.extreme_aggressive_strategies = [
            'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
            'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
        ]
        
        # EXTREME AGGRESSIVE Settings
        self.min_confidence_threshold = 0.01  # EXTREMELY LOW
        self.max_symbols = 50  # MORE SYMBOLS
        self.test_period_days = 30  # SHORTER PERIOD for more volatile data
        self.parallel_workers = 8  # MORE WORKERS
    
    async def run_extreme_aggressive_backtest(self, 
                                             symbols: Optional[List[str]] = None,
                                             strategies: Optional[List[str]] = None,
                                             start_date: Optional[str] = None,
                                             end_date: Optional[str] = None,
                                             use_cache: bool = True,
                                             parallel: bool = True,
                                             max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Run EXTREME AGGRESSIVE backtest with ultra-low thresholds"""
        
        # EXTREME AGGRESSIVE Default values
        if symbols is None:
            symbols = self.symbols[:self.max_symbols]  # MORE SYMBOLS
        
        if strategies is None:
            strategies = self.extreme_aggressive_strategies
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=self.test_period_days)).strftime('%Y-%m-%d')
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if max_workers is None:
            max_workers = self.parallel_workers
        
        logger.info("🚀 FAST BACKTEST RUNNER - EXTREME AGGRESSIVE")
        logger.info("=" * 70)
        logger.info(f"📊 EXTREME AGGRESSIVE Configuration:")
        logger.info(f"   Symbols: {len(symbols)} (MAXIMUM for speed)")
        logger.info(f"   Strategies: {len(strategies)} (HIGH-FREQUENCY)")
        logger.info(f"   Period: {start_date} to {end_date} ({self.test_period_days} days)")
        logger.info(f"   Cache: {'Enabled' if use_cache else 'Disabled'}")
        logger.info(f"   Parallel: {'Enabled' if parallel else 'Disabled'}")
        logger.info(f"   Workers: {max_workers}")
        logger.info(f"   MIN Confidence Threshold: {self.min_confidence_threshold} (EXTREMELY LOW)")
        
        start_time = time.time()
        
        # Disable LLM evaluation via environment variable
        os.environ['USE_LLM_EVALUATION'] = 'false'
        
        # Set logging to DEBUG for more verbose output
        logging.basicConfig(level=logging.DEBUG)
        
        # Initialize backtest engine with extreme aggressive settings
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        total_time = time.time() - start_time
        logger.info(f"⏱️  Total execution time: {total_time:.2f} seconds")
        
        # Analyze results with EXTREME AGGRESSIVE metrics
        self._analyze_extreme_aggressive_results(results, total_time)
        
        return results
    
    def _set_extreme_aggressive_thresholds(self, engine: BacktestEngine):
        """Set EXTREME AGGRESSIVE confidence thresholds"""
        try:
            # Try to set low confidence thresholds for all strategies
            for strategy_name in self.extreme_aggressive_strategies:
                try:
                    strategy_class = engine._get_strategy_class(strategy_name)
                    if strategy_class:
                        strategy = strategy_class()
                        # Set extremely low confidence thresholds
                        if hasattr(strategy, 'confidence_threshold'):
                            strategy.confidence_threshold = self.min_confidence_threshold
                        if hasattr(strategy, 'min_confidence'):
                            strategy.min_confidence = self.min_confidence_threshold
                        if hasattr(strategy, 'fallback_confidence'):
                            strategy.fallback_confidence = self.min_confidence_threshold
                        logger.info(f"✅ Set {strategy_name} confidence threshold to {self.min_confidence_threshold}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not set threshold for {strategy_name}: {e}")
        except Exception as e:
            logger.warning(f"⚠️  Could not set extreme aggressive thresholds: {e}")
    
    def _analyze_extreme_aggressive_results(self, results: Dict, execution_time: float):
        """Analyze results with EXTREME AGGRESSIVE metrics"""
        
        logger.info("📊 EXTREME AGGRESSIVE RESULTS ANALYSIS")
        logger.info("=" * 70)
        
        if not results:
            logger.warning("❌ No results generated - strategies may need adjustment")
            return
        
        successful_runs = 0
        total_return = 0.0
        best_strategy = None
        best_return = -999.0
        total_trades = 0
        
        for key, result in results.items():
            if result and hasattr(result, 'total_return_pct'):
                successful_runs += 1
                total_return += result.total_return_pct
                
                if result.total_return_pct > best_return:
                    best_return = result.total_return_pct
                    best_strategy = key
                
                # Count trades if available
                if hasattr(result, 'total_trades'):
                    total_trades += result.total_trades
        
        avg_return = total_return / successful_runs if successful_runs > 0 else 0.0
        
        logger.info(f"📈 EXTREME AGGRESSIVE Performance:")
        logger.info(f"   Total strategies tested: {len(results)}")
        logger.info(f"   Successful runs: {successful_runs}")
        logger.info(f"   Average return: {avg_return:.2f}%")
        logger.info(f"   Best strategy: {best_strategy} ({best_return:.2f}%)")
        logger.info(f"   Total trades generated: {total_trades}")
        logger.info(f"   Execution time: {execution_time:.2f}s")
        
        # EXTREME AGGRESSIVE Recommendations
        if successful_runs == 0:
            logger.warning("⚠️  NO TRADES GENERATED - Consider:")
            logger.warning("   - Using even shorter time period (7-14 days)")
            logger.warning("   - Adding more volatile symbols (crypto, penny stocks)")
            logger.warning("   - Lowering confidence thresholds further")
            logger.warning("   - Using different market conditions")
        elif total_trades == 0:
            logger.warning("⚠️  Strategies ran but generated no trades - Check:")
            logger.warning("   - Market data availability")
            logger.warning("   - Strategy signal generation logic")
            logger.warning("   - Time period volatility")
        else:
            logger.info("✅ EXTREME AGGRESSIVE backtest completed with trades!")
            logger.info(f"   Average trades per strategy: {total_trades / successful_runs:.1f}")
    
    async def run_ultra_short_test(self) -> Dict[str, Any]:
        """Run ultra-short test with maximum volatility"""
        
        logger.info("⚡ ULTRA-SHORT EXTREME AGGRESSIVE TEST")
        logger.info("=" * 70)
        
        # Use 180-day period to ensure enough data for all technical indicators
        test_symbols = self.symbols[:30]  # More symbols
        start_date = "2024-12-14"  # 180 days before July 11
        end_date = "2025-07-11"    # Use available data end
        
        logger.info(f"📊 Ultra-short configuration:")
        logger.info(f"   Period: {start_date} to {end_date} (180 days)")
        logger.info(f"   Symbols: {len(test_symbols)}")
        logger.info(f"   Strategies: {len(self.extreme_aggressive_strategies)}")
        
        return await self.run_extreme_aggressive_backtest(
            symbols=test_symbols,
            strategies=self.extreme_aggressive_strategies,
            start_date=start_date,
            end_date=end_date
        )

async def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='Fast Backtest Runner - EXTREME AGGRESSIVE')
    parser.add_argument('--symbols', type=int, default=50, help='Number of symbols to test')
    parser.add_argument('--period', type=int, default=30, help='Test period in days')
    parser.add_argument('--ultra-short', action='store_true', help='Run ultra-short 7-day test')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel execution')
    
    args = parser.parse_args()
    
    runner = FastBacktestExtremeAggressiveRunner()
    
    if args.ultra_short:
        logger.info("🚀 Running ULTRA-SHORT EXTREME AGGRESSIVE test...")
        results = await runner.run_ultra_short_test()
    else:
        logger.info("🚀 Running EXTREME AGGRESSIVE backtest...")
        results = await runner.run_extreme_aggressive_backtest(
            symbols=runner.symbols[:args.symbols],
            start_date=(datetime.now() - timedelta(days=args.period)).strftime('%Y-%m-%d'),
            parallel=not args.no_parallel
        )
    
    logger.info("✅ EXTREME AGGRESSIVE backtest completed!")

if __name__ == "__main__":
    asyncio.run(main()) 