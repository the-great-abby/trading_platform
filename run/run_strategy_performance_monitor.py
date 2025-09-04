#!/usr/bin/env python3
"""
Strategy Performance Monitor
===========================
Monitors strategy performance and generates reports.
Can be run as a single check or continuous monitoring.
"""

import asyncio
import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.append('src')

from src.services.database.backtest_results_service import BacktestResultsService
from src.services.database.market_data_service import MarketDataService
from src.utils.enhanced_logging import get_trading_logger
from src.utils.trading_config import get_symbols

logger = get_trading_logger()

class StrategyPerformanceMonitor:
    """Monitor strategy performance and generate reports"""
    
    def __init__(self):
        self.backtest_service = BacktestResultsService()
        self.market_data_service = MarketDataService()
        
    async def run_single_check(self):
        """Run a single performance check"""
        logger.info("🔍 Running single strategy performance check...")
        
        try:
            # Get recent backtest results
            recent_runs = self.backtest_service.get_backtest_runs(limit=20)
            
            if not recent_runs:
                logger.warning("⚠️ No recent backtest runs found")
                return
            
            logger.info(f"📊 Found {len(recent_runs)} recent backtest runs")
            
            # Analyze performance
            performance_summary = await self._analyze_performance(recent_runs)
            
            # Generate report
            await self._generate_performance_report(performance_summary)
            
            logger.info("✅ Strategy performance check completed")
            
        except Exception as e:
            logger.error(f"❌ Error in strategy performance check: {e}")
            raise
    
    async def _analyze_performance(self, recent_runs: List[Dict]) -> Dict[str, Any]:
        """Analyze performance of recent backtest runs"""
        
        logger.info("📈 Analyzing performance...")
        
        performance_summary = {
            'total_runs': len(recent_runs),
            'successful_runs': 0,
            'failed_runs': 0,
            'strategies': {},
            'average_returns': {},
            'best_performers': [],
            'worst_performers': []
        }
        
        for run in recent_runs:
            strategy_name = run.get('strategy_name', 'Unknown')
            total_return = run.get('total_return_pct', 0)
            sharpe_ratio = run.get('sharpe_ratio', 0)
            win_rate = run.get('win_rate', 0)
            
            # Track strategy performance
            if strategy_name not in performance_summary['strategies']:
                performance_summary['strategies'][strategy_name] = {
                    'runs': 0,
                    'total_return': 0,
                    'avg_return': 0,
                    'best_return': -999,
                    'worst_return': 999,
                    'avg_sharpe': 0,
                    'avg_win_rate': 0
                }
            
            strategy_stats = performance_summary['strategies'][strategy_name]
            strategy_stats['runs'] += 1
            strategy_stats['total_return'] += total_return
            
            if total_return > strategy_stats['best_return']:
                strategy_stats['best_return'] = total_return
            if total_return < strategy_stats['worst_return']:
                strategy_stats['worst_return'] = total_return
            
            strategy_stats['avg_sharpe'] += sharpe_ratio
            strategy_stats['avg_win_rate'] += win_rate
            
            # Track successful vs failed runs
            if total_return > 0:
                performance_summary['successful_runs'] += 1
            else:
                performance_summary['failed_runs'] += 1
        
        # Calculate averages
        for strategy_name, stats in performance_summary['strategies'].items():
            if stats['runs'] > 0:
                stats['avg_return'] = stats['total_return'] / stats['runs']
                stats['avg_sharpe'] = stats['avg_sharpe'] / stats['runs']
                stats['avg_win_rate'] = stats['avg_win_rate'] / stats['runs']
        
        # Find best and worst performers
        strategy_performance = [
            (name, stats['avg_return']) 
            for name, stats in performance_summary['strategies'].items()
            if stats['runs'] > 0
        ]
        
        strategy_performance.sort(key=lambda x: x[1], reverse=True)
        
        performance_summary['best_performers'] = strategy_performance[:5]
        performance_summary['worst_performers'] = strategy_performance[-5:]
        
        return performance_summary
    
    async def _generate_performance_report(self, performance_summary: Dict[str, Any]):
        """Generate performance report"""
        
        logger.info("📊 Generating performance report...")
        
        report = f"""
Strategy Performance Report
==========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
--------
Total Runs: {performance_summary['total_runs']}
Successful Runs: {performance_summary['successful_runs']}
Failed Runs: {performance_summary['failed_runs']}
Success Rate: {(performance_summary['successful_runs'] / performance_summary['total_runs'] * 100):.1f}%

Strategy Performance:
-------------------
"""
        
        for strategy_name, stats in performance_summary['strategies'].items():
            if stats['runs'] > 0:
                report += f"""
{strategy_name}:
  Runs: {stats['runs']}
  Average Return: {stats['avg_return']:.2f}%
  Best Return: {stats['best_return']:.2f}%
  Worst Return: {stats['worst_return']:.2f}%
  Average Sharpe: {stats['avg_sharpe']:.2f}
  Average Win Rate: {stats['avg_win_rate']:.2f}%
"""
        
        report += f"""
Top Performers:
--------------
"""
        for i, (strategy, return_pct) in enumerate(performance_summary['best_performers'], 1):
            report += f"{i}. {strategy}: {return_pct:.2f}%\n"
        
        report += f"""
Worst Performers:
----------------
"""
        for i, (strategy, return_pct) in enumerate(performance_summary['worst_performers'], 1):
            report += f"{i}. {strategy}: {return_pct:.2f}%\n"
        
        # Save report to file
        report_dir = "/app/performance_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(report_dir, f"strategy_performance_{timestamp}.txt")
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Performance report saved to: {report_file}")
        
        # Print summary to console
        print(report)
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        logger.info("🔄 Starting continuous strategy performance monitoring...")
        
        while True:
            try:
                await self.run_single_check()
                logger.info("⏰ Waiting 4 hours until next check...")
                await asyncio.sleep(4 * 60 * 60)  # 4 hours
            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Strategy Performance Monitor')
    parser.add_argument('--single-check', action='store_true', 
                       help='Run a single performance check')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = StrategyPerformanceMonitor()
    
    if args.single_check:
        await monitor.run_single_check()
    elif args.continuous:
        await monitor.run_continuous_monitoring()
    else:
        # Default to single check
        await monitor.run_single_check()

if __name__ == "__main__":
    asyncio.run(main()) 