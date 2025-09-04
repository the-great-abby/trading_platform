#!/usr/bin/env python3
"""
Fast Backtest with Post-Processing LLM Evaluation
================================================
Runs comprehensive backtests quickly without LLM evaluation during execution,
then adds LLM analysis as a separate post-processing phase for selected trades.
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

class FastBacktestWithPostLLM:
    """
    Fast backtest with post-processing LLM evaluation
    """
    
    def __init__(self):
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
    
    async def run_fast_backtest(self):
        """Run fast backtest without LLM evaluation during execution"""
        
        logger.info("🚀 Starting Fast Backtest with Post-Processing LLM Evaluation")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Test Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Duration: {(self.end_date - self.start_date).days} days")
        logger.info(f"   All symbols: {len(self.all_symbols)}")
        logger.info(f"   Options symbols: {len(self.options_symbols)}")
        logger.info(f"   LLM Evaluation: DISABLED during execution")
        logger.info(f"   Post-Processing LLM: ENABLED")
        
        # Disable LLM evaluation completely during fast backtest
        os.environ['USE_LLM_EVALUATION'] = 'false'
        
        # Initialize backtest engine WITHOUT LLM evaluation for speed
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = False  # Disable LLM during execution
        
        # Phase 1: Core Strategies (Fast Execution)
        logger.info("\n📈 PHASE 1: Core Strategies (Fast Execution)")
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
        
        # Phase 2: Advanced Strategies (Fast Execution)
        logger.info("\n📈 PHASE 2: Advanced Strategies (Fast Execution)")
        logger.info("-" * 60)
        
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
        
        # Save all trades to CSV for LLM post-processing
        all_trades = []
        for result in list(core_results.values()) + list(advanced_results.values()):
            if result and hasattr(result, 'trades'):
                for trade in result.trades:
                    all_trades.append({
                        'strategy': getattr(trade, 'strategy', getattr(result, 'strategy_name', 'unknown')),
                        'symbol': trade.symbol,
                        'action': trade.action,
                        'entry_price': trade.price,  # BacktestTrade uses 'price'
                        'exit_price': trade.price,   # BacktestTrade uses 'price' for both entry/exit
                        'profit_loss': trade.pnl,    # BacktestTrade uses 'pnl'
                        'confidence': getattr(trade, 'confidence', 0.8),
                        'timestamp': getattr(trade, 'timestamp', None)
                    })
        if all_trades:
            df = pd.DataFrame(all_trades)
            df.to_csv('trades_for_llm.csv', index=False)
            logger.info(f"💾 Saved {len(all_trades)} trades to trades_for_llm.csv for LLM post-processing.")
        else:
            logger.warning("⚠️ No trades found to save for LLM post-processing.")
        
        # Phase 3: Post-Processing LLM Analysis
        await self._run_post_processing_llm_analysis(engine, core_results, advanced_results)
        
        # Generate comprehensive report
        await self._generate_comprehensive_report(engine, core_results, advanced_results)
    
    async def _run_post_processing_llm_analysis(self, engine: BacktestEngine, 
                                              core_results: Dict, advanced_results: Dict):
        """Run LLM analysis on selected trades after backtest completion"""
        
        logger.info("\n🤖 PHASE 3: Post-Processing LLM Analysis")
        logger.info("-" * 60)
        
        # Enable LLM evaluation for post-processing
        engine.use_llm_evaluation = True
        
        # Configure Ollama settings
        os.environ['OLLAMA_TIMEOUT'] = '120.0'
        os.environ['OLLAMA_MAX_RETRIES'] = '3'
        os.environ['OLLAMA_BASE_DELAY'] = '5.0'
        os.environ['OLLAMA_MAX_DELAY'] = '60.0'
        os.environ['OLLAMA_BASE_URL'] = 'http://192.168.0.18:11434'
        
        logger.info("🔗 Configuring Ollama for post-processing analysis...")
        logger.info(f"   Ollama URL: {os.environ['OLLAMA_BASE_URL']}")
        logger.info(f"   Timeout: {os.environ['OLLAMA_TIMEOUT']}s")
        
        # Analyze top performing strategies with LLM
        all_results = {**core_results, **advanced_results}
        top_strategies = self._get_top_performing_strategies(all_results, top_n=5)
        
        logger.info(f"📊 Analyzing top {len(top_strategies)} strategies with LLM:")
        for strategy_name in top_strategies:
            logger.info(f"   - {strategy_name}")
        
        # Run LLM analysis on top strategies
        llm_analysis_results = {}
        for strategy_name in top_strategies:
            logger.info(f"\n🤖 LLM Analysis: {strategy_name}")
            
            # Get strategy results and analyze with LLM
            strategy_result = all_results.get(strategy_name)
            if strategy_result and strategy_result.trades:
                # Analyze a sample of trades with LLM
                sample_trades = strategy_result.trades[:10]  # Analyze first 10 trades
                
                llm_approved = 0
                llm_rejected = 0
                
                for trade in sample_trades:
                    # Create trade signal for LLM evaluation
                    signal_data = {
                        'symbol': trade.symbol,
                        'action': trade.action,
                        'entry_price': trade.entry_price,
                        'exit_price': trade.exit_price,
                        'profit_loss': trade.profit_loss,
                        'strategy': strategy_name,
                        'confidence': 0.8  # Default confidence
                    }
                    
                    try:
                        # Evaluate with LLM
                        evaluation = engine.trade_evaluator.evaluate_trade_signal(signal_data)
                        if evaluation['approved']:
                            llm_approved += 1
                        else:
                            llm_rejected += 1
                    except Exception as e:
                        logger.warning(f"⚠️ LLM evaluation failed for {strategy_name}: {str(e)}")
                        llm_rejected += 1
                
                llm_analysis_results[strategy_name] = {
                    'total_analyzed': len(sample_trades),
                    'llm_approved': llm_approved,
                    'llm_rejected': llm_rejected,
                    'approval_rate': (llm_approved / len(sample_trades)) * 100 if sample_trades else 0
                }
                
                logger.info(f"   ✅ LLM Analysis Complete:")
                logger.info(f"      Analyzed: {len(sample_trades)} trades")
                logger.info(f"      Approved: {llm_approved}")
                logger.info(f"      Rejected: {llm_rejected}")
                logger.info(f"      Approval Rate: {llm_analysis_results[strategy_name]['approval_rate']:.1f}%")
        
        # Store LLM analysis results
        self.llm_analysis_results = llm_analysis_results
        
        logger.info("\n✅ Post-Processing LLM Analysis Complete!")
    
    def _get_top_performing_strategies(self, results: Dict, top_n: int = 5) -> List[str]:
        """Get top performing strategies based on return percentage"""
        
        # Filter out None results and sort by return percentage
        valid_results = {name: result for name, result in results.items() if result is not None}
        
        if not valid_results:
            return []
        
        # Sort by total return percentage (descending)
        sorted_strategies = sorted(
            valid_results.items(),
            key=lambda x: x[1].total_return_pct,
            reverse=True
        )
        
        # Return top N strategy names
        return [strategy_name for strategy_name, _ in sorted_strategies[:top_n]]
    
    async def _generate_comprehensive_report(self, engine: BacktestEngine, 
                                          core_results: Dict, advanced_results: Dict):
        """Generate comprehensive performance report"""
        
        logger.info("\n📊 COMPREHENSIVE PERFORMANCE REPORT")
        logger.info("=" * 80)
        
        # Core strategies performance
        logger.info("\n📈 CORE STRATEGIES PERFORMANCE (Fast Execution)")
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
        logger.info("\n📈 ADVANCED STRATEGIES PERFORMANCE (Fast Execution)")
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
        
        # Post-Processing LLM Analysis Report
        if hasattr(self, 'llm_analysis_results'):
            logger.info("\n🤖 POST-PROCESSING LLM ANALYSIS RESULTS")
            logger.info("-" * 60)
            logger.info(f"{'Strategy':<20} {'Analyzed':<10} {'Approved':<10} {'Rejected':<10} {'Approval %':<12}")
            logger.info("-" * 60)
            
            for strategy_name, analysis in self.llm_analysis_results.items():
                analyzed = analysis['total_analyzed']
                approved = analysis['llm_approved']
                rejected = analysis['llm_rejected']
                approval_rate = analysis['approval_rate']
                
                logger.info(f"{strategy_name:<20} {analyzed:>8} {approved:>8} {rejected:>8} {approval_rate:>10.1f}%")
        
        # Overall Performance Summary
        logger.info("\n📊 OVERALL PERFORMANCE SUMMARY")
        logger.info("-" * 60)
        logger.info(f"   Total Strategies Tested: {len(core_results) + len(advanced_results)}")
        logger.info(f"   Profitable Strategies: {profitable_strategies}")
        logger.info(f"   Average Return: {total_return / (len(core_results) + len(advanced_results)):.2f}%")
        logger.info(f"   Total Trades Executed: {total_trades}")
        logger.info(f"   Execution Mode: Fast (No LLM during execution)")
        logger.info(f"   Post-Processing LLM: ENABLED")
        
        # Account Performance Simulation
        initial_capital = 100000
        final_capital = initial_capital * (1 + total_return / 100)
        
        logger.info(f"\n💰 ACCOUNT PERFORMANCE SIMULATION")
        logger.info("-" * 60)
        logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"   Final Capital: ${final_capital:,.2f}")
        logger.info(f"   Total Return: {total_return:.2f}%")
        logger.info(f"   Profit/Loss: ${final_capital - initial_capital:,.2f}")
        
        logger.info("\n✅ Fast Backtest with Post-Processing LLM Analysis Complete!")

async def main():
    """Main execution function"""
    backtest = FastBacktestWithPostLLM()
    await backtest.run_fast_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 