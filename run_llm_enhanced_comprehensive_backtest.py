#!/usr/bin/env python3
"""
LLM-Enhanced Comprehensive Backtest
==================================
Runs comprehensive backtests with LLM trade evaluation:
- All available strategies including Ichimoku, Fibonacci, and advanced strategies
- LLM evaluates each trade signal before execution
- Proper timeout settings for Ollama integration
- Tracks LLM performance vs original signals
- Provides detailed performance reports
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class LLMEnhancedComprehensiveBacktest:
    """
    Comprehensive backtest with LLM trade evaluation
    """
    
    def __init__(self):
        # Set proper LLM timeout settings
        os.environ['OLLAMA_TIMEOUT'] = '120.0'  # 2 minutes timeout
        os.environ['OLLAMA_MAX_RETRIES'] = '3'
        os.environ['OLLAMA_BASE_DELAY'] = '5.0'
        os.environ['OLLAMA_MAX_DELAY'] = '60.0'
        os.environ['USE_LLM_EVALUATION'] = 'true'
        
        # Use Kubernetes host IP for Ollama service
        os.environ['OLLAMA_BASE_URL'] = 'http://192.168.0.18:11434'
        logger.info(f"🔗 Ollama service configured to use: {os.environ['OLLAMA_BASE_URL']}")
        
        # Test period - 2 years for comprehensive testing
        self.start_date = datetime(2023, 7, 15)
        self.end_date = datetime(2025, 7, 14)
        
        # All symbols for comprehensive testing
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
        
        logger.info("🚀 Starting LLM-Enhanced Comprehensive Backtest")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Test Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Duration: {(self.end_date - self.start_date).days} days")
        logger.info(f"   All symbols: {len(self.all_symbols)}")
        logger.info(f"   Options symbols: {len(self.options_symbols)}")
        logger.info(f"   LLM Evaluation: ENABLED")
        logger.info(f"   LLM Timeout: {os.environ.get('OLLAMA_TIMEOUT', '120.0')}s")
        logger.info(f"   LLM Max Retries: {os.environ.get('OLLAMA_MAX_RETRIES', '3')}")
        
        # Initialize backtest engine with LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Phase 1: Core Strategies with LLM Evaluation
        logger.info("\n📈 PHASE 1: Core Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        core_strategies = [
            'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
            'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
        ]
        
        core_results = await engine.run_backtest(
            symbols=self.all_symbols,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=core_strategies
        )
        
        # Phase 2: Advanced Strategies with LLM Evaluation
        logger.info("\n📈 PHASE 2: Advanced Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        # Advanced strategies with LLM evaluation
        advanced_strategies = [
            'GreeksEnhanced', 'Ichimoku', 'IchimokuEnhanced', 'AdaptiveMomentum',
            'NeuralNetwork', 'QuantumMomentum', 'RegimeSwitching', 'IronCondor',
            'VWAP', 'PairsTrading', 'KalmanFilter', 'MLEnsemble',
            'EnhancedDayTrading', 'NewsEnhanced', 'SocialMediaSentiment'
        ]
        
        advanced_results = await engine.run_backtest(
            symbols=self.options_symbols,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=advanced_strategies
        )
        
        # Generate comprehensive report
        await self._generate_comprehensive_report(engine, core_results, advanced_results)
    
    async def _generate_comprehensive_report(self, engine: BacktestEngine, 
                                          core_results: Dict, advanced_results: Dict):
        """Generate comprehensive performance report"""
        
        logger.info("\n📊 COMPREHENSIVE PERFORMANCE REPORT")
        logger.info("=" * 80)
        
        # Core strategies performance
        logger.info("\n📈 CORE STRATEGIES PERFORMANCE (with LLM Evaluation)")
        logger.info("-" * 60)
        logger.info(f"{'Strategy':<20} {'Return %':<10} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 60)
        
        total_return = 0
        total_trades = 0
        profitable_strategies = 0
        
        for strategy_name, result in core_results.items():
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
        
        # Advanced strategies performance
        logger.info("\n📈 ADVANCED STRATEGIES PERFORMANCE (with LLM Evaluation)")
        logger.info("-" * 60)
        logger.info(f"{'Strategy':<20} {'Return %':<10} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 60)
        
        for strategy_name, result in advanced_results.items():
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
        try:
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
        except Exception as e:
            logger.warning(f"⚠️ Could not generate LLM report: {str(e)}")
        
        # Overall Performance Summary
        logger.info("\n📊 OVERALL PERFORMANCE SUMMARY")
        logger.info("-" * 60)
        logger.info(f"   Total Strategies Tested: {len(core_results) + len(advanced_results)}")
        logger.info(f"   Profitable Strategies: {profitable_strategies}")
        logger.info(f"   Average Return: {total_return / (len(core_results) + len(advanced_results)):.2f}%")
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
        
        # Strategy Recommendations
        logger.info("\n🎯 STRATEGY RECOMMENDATIONS")
        logger.info("-" * 60)
        
        # Find best performing strategies
        all_results = {**core_results, **advanced_results}
        if all_results:
            best_strategy = max(all_results.items(), key=lambda x: x[1].total_return_pct if x[1] else 0)
            worst_strategy = min(all_results.items(), key=lambda x: x[1].total_return_pct if x[1] else 0)
            
            if best_strategy[1]:
                logger.info(f"   🏆 Best Strategy: {best_strategy[0]} ({best_strategy[1].total_return_pct:.2f}%)")
            if worst_strategy[1]:
                logger.info(f"   📉 Worst Strategy: {worst_strategy[0]} ({worst_strategy[1].total_return_pct:.2f}%)")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ LLM-Enhanced Comprehensive Backtest Completed!")
        logger.info("=" * 80)

async def main():
    """Main execution function"""
    backtest = LLMEnhancedComprehensiveBacktest()
    await backtest.run_comprehensive_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 