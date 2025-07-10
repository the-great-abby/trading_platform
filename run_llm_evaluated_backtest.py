#!/usr/bin/env python3
"""
LLM-Evaluated Comprehensive Backtest
====================================
Runs comprehensive backtests with LLM trade evaluation:
- Standard strategies on all symbols
- LLM evaluates each trade signal before execution
- Tracks LLM performance vs original signals
- Provides detailed performance reports
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from src.backtesting.engine.backtest_engine import BacktestEngine
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
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class LLMEvaluatedBacktest:
    """
    Comprehensive backtest with LLM trade evaluation
    """
    
    def __init__(self):
        self.start_date_2year = datetime(2023, 7, 11)
        self.end_date = datetime(2025, 7, 10)
        self.options_start_date = datetime(2025, 5, 11)
        
        # All symbols for standard strategies
        self.all_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'COF', 'AXP',
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'OXY', 'HAL'
        ]
        
        # Options symbols for Greeks strategies
        self.options_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'COF', 'AXP'
        ]
    
    async def run_comprehensive_backtest(self):
        """Run comprehensive backtest with LLM evaluation"""
        
        logger.info("🚀 Starting LLM-Evaluated Comprehensive Backtest")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Full 2-year period: {self.start_date_2year.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Options period: {self.options_start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Total symbols: {len(self.all_symbols)}")
        logger.info(f"   Options symbols: {len(self.options_symbols)}")
        logger.info(f"   LLM Evaluation: ENABLED")
        
        # Initialize backtest engine with LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Run standard strategies
        logger.info("\n📈 PHASE 1: Standard Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        standard_strategies = [
            'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
            'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
        ]
        
        standard_results = await engine.run_backtest(
            symbols=self.all_symbols,
            start_date=self.start_date_2year.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=standard_strategies
        )
        
        # Run options strategies
        logger.info("\n📈 PHASE 2: Options Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        options_results = await engine.run_backtest(
            symbols=self.options_symbols,
            start_date=self.options_start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=['GreeksEnhanced']
        )
        
        # Generate comprehensive report
        await self._generate_comprehensive_report(engine, standard_results, options_results)
    
    async def _generate_comprehensive_report(self, engine: BacktestEngine, 
                                          standard_results: Dict, options_results: Dict):
        """Generate comprehensive performance report"""
        
        logger.info("\n📊 COMPREHENSIVE PERFORMANCE REPORT")
        logger.info("=" * 80)
        
        # Standard strategies performance
        logger.info("\n📈 STANDARD STRATEGIES PERFORMANCE (with LLM Evaluation)")
        logger.info("-" * 60)
        logger.info(f"{'Strategy':<20} {'Return %':<10} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 60)
        
        total_return = 0
        total_trades = 0
        profitable_strategies = 0
        
        for strategy_name, result in standard_results.items():
            if result:
                return_pct = result.total_return_pct
                trades = result.total_trades
                win_rate = result.win_rate * 100
                sharpe = result.sharpe_ratio
                max_dd = result.max_drawdown_pct
                
                logger.info(f"{strategy_name:<20} {return_pct:>8.2f}% {trades:>6} {win_rate:>10.1f}% {sharpe:>6.2f} {max_dd:>8.2f}%")
                
                total_return += return_pct
                total_trades += trades
                if return_pct > 0:
                    profitable_strategies += 1
        
        # Options strategies performance
        logger.info("\n📈 OPTIONS STRATEGIES PERFORMANCE (with LLM Evaluation)")
        logger.info("-" * 60)
        logger.info(f"{'Strategy':<20} {'Return %':<10} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 60)
        
        for strategy_name, result in options_results.items():
            if result:
                return_pct = result.total_return_pct
                trades = result.total_trades
                win_rate = result.win_rate * 100
                sharpe = result.sharpe_ratio
                max_dd = result.max_drawdown_pct
                
                logger.info(f"{strategy_name:<20} {return_pct:>8.2f}% {trades:>6} {win_rate:>10.1f}% {sharpe:>6.2f} {max_dd:>8.2f}%")
                
                total_return += return_pct
                total_trades += trades
                if return_pct > 0:
                    profitable_strategies += 1
        
        # LLM Performance Report
        llm_report = engine.trade_evaluator.get_performance_report()
        
        logger.info("\n🤖 LLM TRADE EVALUATION PERFORMANCE")
        logger.info("-" * 60)
        logger.info(f"   Total Signals Evaluated: {llm_report['llm_performance']['total_signals']}")
        logger.info(f"   LLM Approval Rate: {llm_report['evaluations_summary']['approval_rate']:.1f}%")
        logger.info(f"   LLM Accuracy: {llm_report['evaluations_summary']['accuracy']:.1f}%")
        logger.info(f"   Average Confidence: {llm_report['evaluations_summary']['average_confidence']:.2f}")
        logger.info(f"   Approved Trades: {llm_report['llm_performance']['llm_approved']}")
        logger.info(f"   Rejected Trades: {llm_report['llm_performance']['llm_rejected']}")
        logger.info(f"   Correct Approvals: {llm_report['llm_performance']['approved_correct']}")
        logger.info(f"   Incorrect Approvals: {llm_report['llm_performance']['approved_incorrect']}")
        logger.info(f"   Correct Rejections: {llm_report['llm_performance']['rejected_correct']}")
        logger.info(f"   Incorrect Rejections: {llm_report['llm_performance']['rejected_incorrect']}")
        
        # Overall Performance Summary
        logger.info("\n📊 OVERALL PERFORMANCE SUMMARY")
        logger.info("-" * 60)
        logger.info(f"   Total Strategies Tested: {len(standard_results) + len(options_results)}")
        logger.info(f"   Profitable Strategies: {profitable_strategies}")
        logger.info(f"   Average Return: {total_return / (len(standard_results) + len(options_results)):.2f}%")
        logger.info(f"   Total Trades Executed: {total_trades}")
        logger.info(f"   LLM-Enhanced Trading: ENABLED")
        
        # Account Performance Simulation
        initial_capital = 100000
        final_capital = initial_capital * (1 + total_return / 100)
        
        logger.info("\n💰 ACCOUNT PERFORMANCE SIMULATION")
        logger.info("-" * 60)
        logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"   Final Capital: ${final_capital:,.2f}")
        logger.info(f"   Total P&L: ${final_capital - initial_capital:,.2f}")
        logger.info(f"   Total Return: {total_return:.2f}%")
        logger.info(f"   LLM Contribution: Enhanced risk management and signal filtering")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ LLM-Evaluated Comprehensive Backtest Completed!")
        logger.info("=" * 80)

async def main():
    """Main execution function"""
    backtest = LLMEvaluatedBacktest()
    await backtest.run_comprehensive_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 