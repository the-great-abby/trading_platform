#!/usr/bin/env python3
"""
Portfolio Performance Test - 60 Days with Options
================================================
Runs comprehensive backtests on all symbols using standard strategies
plus options strategy for the past 60 days where we have actual data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.strategies.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.utils.config import get_config
from src.utils.enhanced_logging import get_trading_logger
from src.utils.trading_config import get_symbols, get_options_symbols

# Configure logging
logger = get_trading_logger()

class PortfolioPerformanceAnalyzer60Days:
    """Analyzes portfolio performance across multiple strategies for 60 days."""
    
    def __init__(self):
        self.config = get_config()
        self.symbols = get_symbols()
        self.options_symbols = get_options_symbols()
        
    async def run_portfolio_backtest(self) -> Dict[str, Any]:
        """Run comprehensive portfolio backtest across all strategies for 60 days."""
        
        # Calculate date range for past 60 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        logger.info("🚀 Starting 60-Day Portfolio Performance Test")
        logger.info(f"📊 Testing {len(self.symbols)} symbols")
        logger.info(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Define strategies to test
        strategies = {
            'BollingerBands': BollingerBandsStrategy,
            'MACD': MACDStrategy,
            'RSI': RSIStrategy,
            'MeanReversion': MeanReversionStrategy,
            'Momentum': MomentumStrategy,
            'SMACrossover': SMACrossoverStrategy,
            'VolatilityBreakout': VolatilityBreakoutStrategy,
            'GreeksEnhanced': GreeksEnhancedStrategy  # Options strategy
        }
        strategy_names = list(strategies.keys())
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest for all strategies at once
        results = await engine.run_backtest(
            symbols=self.symbols,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            strategies=strategy_names
        )
        
        # Store results for each strategy
        strategy_results = {}
        portfolio_summary = {}
        
        for strategy_name in strategy_names:
            logger.info(f"📈 Processing {strategy_name} results...")
            try:
                strategy_result = results.get(strategy_name, {})
                portfolio_metrics = self._calculate_portfolio_metrics(strategy_result)
                strategy_results[strategy_name] = strategy_result
                portfolio_summary[strategy_name] = portfolio_metrics
                logger.info(f"✅ {strategy_name} completed: {portfolio_metrics['total_return_pct']:.2f}% return")
            except Exception as e:
                logger.error(f"❌ Error processing {strategy_name}: {e}")
                portfolio_summary[strategy_name] = {
                    'total_return': 0,
                    'total_return_pct': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'total_trades': 0,
                    'win_rate': 0
                }
        
        # Generate comprehensive report
        self._generate_portfolio_report(portfolio_summary, strategy_results)
        
        return {
            'portfolio_summary': portfolio_summary,
            'strategy_results': strategy_results
        }
    
    def _calculate_portfolio_metrics(self, results: Any) -> Dict[str, float]:
        """Calculate portfolio-level metrics from backtest results."""
        
        # Handle BacktestResult objects
        if hasattr(results, 'trades'):
            trades = results.trades
            initial_capital = results.initial_capital
            final_capital = results.final_capital
            total_return = results.total_return
            total_return_pct = results.total_return_pct
            total_trades = results.total_trades
            win_rate = results.win_rate
            sharpe_ratio = results.sharpe_ratio
            max_drawdown_pct = results.max_drawdown_pct
            
            return {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown_pct,
                'total_trades': total_trades,
                'win_rate': win_rate
            }
        
        # Handle dictionary format (fallback)
        if isinstance(results, dict) and 'trades' in results:
            trades = results['trades']
            initial_capital = results.get('initial_capital', 100000)
            final_capital = results.get('final_capital', initial_capital)
            
            # Basic metrics
            total_return = final_capital - initial_capital
            total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0
            total_trades = len(trades) if trades else 0
            
            # Win rate calculation
            winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0) if trades else 0
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Sharpe ratio (simplified)
            if trades:
                returns = [trade.get('pnl', 0) for trade in trades]
                avg_return = sum(returns) / len(returns) if returns else 0
                std_return = pd.Series(returns).std() if len(returns) > 1 else 0
                sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown (simplified)
            if trades:
                cumulative_pnl = []
                running_total = 0
                for trade in trades:
                    running_total += trade.get('pnl', 0)
                    cumulative_pnl.append(running_total)
                
                if cumulative_pnl:
                    peak = max(cumulative_pnl)
                    max_drawdown = min(cumulative_pnl) - peak if peak > 0 else 0
                    max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else 0
                else:
                    max_drawdown_pct = 0
            else:
                max_drawdown_pct = 0
            
            return {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown_pct,
                'total_trades': total_trades,
                'win_rate': win_rate
            }
        
        # Default return for no results
        return {
            'total_return': 0,
            'total_return_pct': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'win_rate': 0
        }
    
    def _generate_portfolio_report(self, portfolio_summary: Dict[str, Any], strategy_results: Dict[str, Any]):
        """Generate comprehensive portfolio performance report."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 60-DAY PORTFOLIO PERFORMANCE REPORT")
        logger.info("="*80)
        
        # Strategy comparison table
        logger.info("\n📈 Strategy Performance Comparison:")
        logger.info("-" * 100)
        logger.info(f"{'Strategy':<20} {'Return %':<12} {'Trades':<8} {'Win Rate %':<12} {'Sharpe':<8} {'Max DD %':<10}")
        logger.info("-" * 100)
        
        # Sort strategies by return
        sorted_strategies = sorted(
            portfolio_summary.items(),
            key=lambda x: x[1]['total_return_pct'],
            reverse=True
        )
        
        for strategy_name, metrics in sorted_strategies:
            logger.info(
                f"{strategy_name:<20} "
                f"{metrics['total_return_pct']:<12.2f} "
                f"{metrics['total_trades']:<8} "
                f"{metrics['win_rate']:<12.2f} "
                f"{metrics['sharpe_ratio']:<8.2f} "
                f"{metrics['max_drawdown']:<10.2f}"
            )
        
        # Top performers
        if sorted_strategies:
            best_strategy = sorted_strategies[0]
            worst_strategy = sorted_strategies[-1]
            
            logger.info("\n🏆 Top Performers:")
            logger.info(f"🥇 Best Strategy: {best_strategy[0]} ({best_strategy[1]['total_return_pct']:.2f}%)")
            logger.info(f"🥉 Worst Strategy: {worst_strategy[0]} ({worst_strategy[1]['total_return_pct']:.2f}%)")
            
            # Risk-adjusted performance
            best_sharpe = max(portfolio_summary.items(), key=lambda x: x[1]['sharpe_ratio'])
            logger.info(f"📊 Best Risk-Adjusted: {best_sharpe[0]} (Sharpe: {best_sharpe[1]['sharpe_ratio']:.2f})")
        
        # Summary statistics
        total_strategies = len(portfolio_summary)
        positive_strategies = sum(1 for metrics in portfolio_summary.values() if metrics['total_return_pct'] > 0)
        avg_return = sum(metrics['total_return_pct'] for metrics in portfolio_summary.values()) / total_strategies if total_strategies > 0 else 0
        
        logger.info(f"\n📊 Summary Statistics:")
        logger.info(f"   📈 Total Strategies Tested: {total_strategies}")
        logger.info(f"   ✅ Profitable Strategies: {positive_strategies}/{total_strategies} ({positive_strategies/total_strategies*100:.1f}%)")
        logger.info(f"   📊 Average Return: {avg_return:.2f}%")
        
        # Trading activity summary
        total_trades = sum(metrics['total_trades'] for metrics in portfolio_summary.values())
        avg_trades = total_trades / total_strategies if total_strategies > 0 else 0
        
        logger.info(f"\n📈 Trading Activity:")
        logger.info(f"   🔄 Total Trades Across All Strategies: {total_trades}")
        logger.info(f"   📊 Average Trades per Strategy: {avg_trades:.1f}")
        
        # Most active strategies
        most_active = max(portfolio_summary.items(), key=lambda x: x[1]['total_trades'])
        logger.info(f"   🏃 Most Active Strategy: {most_active[0]} ({most_active[1]['total_trades']} trades)")
        
        # Options strategy analysis
        if 'GreeksEnhanced' in portfolio_summary:
            greeks_metrics = portfolio_summary['GreeksEnhanced']
            logger.info(f"\n🎯 Options Strategy Analysis:")
            logger.info(f"   📊 GreeksEnhanced Return: {greeks_metrics['total_return_pct']:.2f}%")
            logger.info(f"   📈 Options Trades: {greeks_metrics['total_trades']}")
            logger.info(f"   🎯 Options Win Rate: {greeks_metrics['win_rate']:.2f}%")
        
        logger.info("\n" + "="*80)
        logger.info("✅ 60-Day Portfolio Performance Test Completed!")
        logger.info("="*80)

async def main():
    """Main function to run 60-day portfolio performance test."""
    
    analyzer = PortfolioPerformanceAnalyzer60Days()
    
    try:
        results = await analyzer.run_portfolio_backtest()
        logger.info("🎉 60-day portfolio performance test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ 60-day portfolio performance test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 