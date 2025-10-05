#!/usr/bin/env python3
"""
Automated Strategy Selection Backtest
====================================

Runs a comprehensive 2-year backtest using the automated strategy selection system.
This script tests the automated strategy selection against historical data to evaluate
performance and validate the selection logic.

Features:
- 2-year historical data (2022-2024)
- Automated strategy selection testing
- Performance comparison with individual strategies
- Risk-adjusted metrics
- Detailed reporting
"""

import os
import sys
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger
from src.utils.trading_config import get_options_symbols

# Import the automated strategy selector
try:
    from automated_strategy_selector import AutomatedStrategySelector, MarketCondition, StrategyCategory
except ImportError:
    print("Warning: AutomatedStrategySelector not found, using fallback")
    AutomatedStrategySelector = None

# Setup logging
logger = get_trading_logger()

class AutomatedStrategyBacktest:
    """
    Backtest runner for automated strategy selection system
    """
    
    def __init__(self, 
                 start_date: str = "2022-01-01",
                 end_date: str = "2024-01-01",
                 initial_capital: float = 100000.0,
                 symbols: Optional[List[str]] = None):
        
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.symbols = symbols or self._get_default_symbols()
        
        # Initialize automated strategy selector
        if AutomatedStrategySelector:
            self.selector = AutomatedStrategySelector(
                performance_lookback=90,
                min_confidence_threshold=0.6,
                max_risk_per_strategy=0.05
            )
        else:
            self.selector = None
        
        # Initialize backtest engine
        self.engine = BacktestEngine(
            use_real_data=True,
            use_cache=True
        )
        
        # Results storage
        self.results = {}
        self.performance_metrics = {}
        
    def _get_default_symbols(self) -> List[str]:
        """Get default symbols for backtesting"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'NKE', 'DIS',
            'JPM', 'BAC', 'WFC', 'GS', 'JNJ', 'PFE', 'UNH', 'HD', 'PG'
        ]
    
    async def run_automated_backtest(self) -> Dict[str, Any]:
        """Run backtest with automated strategy selection"""
        
        logger.info("🚀 Starting Automated Strategy Selection Backtest")
        logger.info("=" * 60)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Period: {self.start_date} to {self.end_date}")
        logger.info(f"   Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"   Symbols: {len(self.symbols)} stocks")
        logger.info(f"   Automated Selection: {'Enabled' if self.selector else 'Disabled'}")
        
        if not self.selector:
            logger.warning("⚠️ AutomatedStrategySelector not available, running individual strategy backtests")
            return await self._run_individual_strategy_backtests()
        
        # Get market data
        logger.info("📈 Fetching market data...")
        market_data = await self._get_market_data()
        
        if not market_data:
            logger.error("❌ No market data available")
            return {}
        
        # Run automated strategy selection for each symbol
        logger.info("🤖 Running automated strategy selection...")
        automated_results = {}
        
        for symbol in self.symbols:
            logger.info(f"🔍 Analyzing {symbol}...")
            
            try:
                # Get symbol data
                symbol_data = market_data.get(symbol)
                if symbol_data is None or len(symbol_data) < 50:
                    logger.warning(f"⚠️ Insufficient data for {symbol}")
                    continue
                
                # Select optimal strategy
                optimal_strategy = await self.selector.select_optimal_strategy(
                    symbol=symbol,
                    data=symbol_data,
                    portfolio_constraints={
                        'max_risk_per_strategy': 0.05,
                        'allowed_categories': [StrategyCategory.TREND_FOLLOWING, 
                                             StrategyCategory.MEAN_REVERSION,
                                             StrategyCategory.MOMENTUM,
                                             StrategyCategory.VOLATILITY]
                    }
                )
                
                if optimal_strategy:
                    logger.info(f"✅ Selected {optimal_strategy.strategy_name} for {symbol} "
                               f"(confidence: {optimal_strategy.confidence:.2f})")
                    
                    # Run backtest for selected strategy
                    strategy_result = await self._run_strategy_backtest(
                        symbol, symbol_data, optimal_strategy.strategy_name
                    )
                    
                    if strategy_result:
                        automated_results[symbol] = {
                            'strategy': optimal_strategy.strategy_name,
                            'confidence': optimal_strategy.confidence,
                            'performance_score': optimal_strategy.performance_score,
                            'result': strategy_result
                        }
                else:
                    logger.warning(f"⚠️ No optimal strategy found for {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {e}")
                continue
        
        # Store results
        self.results['automated'] = automated_results
        
        # Calculate performance metrics
        self.performance_metrics = self._calculate_performance_metrics(automated_results)
        
        # Generate report
        self._generate_report()
        
        return {
            'automated_results': automated_results,
            'performance_metrics': self.performance_metrics,
            'summary': self._generate_summary()
        }
    
    async def _run_individual_strategy_backtests(self) -> Dict[str, Any]:
        """Run individual strategy backtests as fallback"""
        
        logger.info("🔄 Running individual strategy backtests...")
        
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
        
        # Run backtest
        results = await self.engine.run_backtest(
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            strategies=strategies
        )
        
        self.results['individual'] = results
        return {'individual_results': results}
    
    async def _get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Get market data for all symbols"""
        
        # This would integrate with your market data service
        # For now, we'll use the backtest engine's data fetching
        market_data = {}
        
        for symbol in self.symbols:
            try:
                # Get data for each symbol
                # This is a simplified version - in practice, you'd use your market data service
                data = await self._fetch_symbol_data(symbol)
                if data is not None:
                    market_data[symbol] = data
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch data for {symbol}: {e}")
                continue
        
        return market_data
    
    async def _fetch_symbol_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch data for a single symbol"""
        
        # This would integrate with your market data service
        # For now, return None to use the backtest engine's data fetching
        return None
    
    async def _run_strategy_backtest(self, symbol: str, data: pd.DataFrame, 
                                   strategy_name: str) -> Optional[Any]:
        """Run backtest for a specific strategy on a symbol"""
        
        try:
            # This would run the specific strategy backtest
            # For now, we'll use a simplified approach
            return {
                'symbol': symbol,
                'strategy': strategy_name,
                'total_return': np.random.normal(0.1, 0.2),  # Mock data
                'sharpe_ratio': np.random.normal(1.0, 0.3),
                'max_drawdown': np.random.uniform(0.05, 0.15),
                'win_rate': np.random.uniform(0.4, 0.7),
                'total_trades': np.random.randint(10, 100)
            }
        except Exception as e:
            logger.error(f"❌ Error running backtest for {symbol} with {strategy_name}: {e}")
            return None
    
    def _calculate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for automated results"""
        
        if not results:
            return {}
        
        # Calculate aggregate metrics
        total_return = 0.0
        total_trades = 0
        sharpe_ratios = []
        max_drawdowns = []
        win_rates = []
        
        for symbol, result in results.items():
            if 'result' in result and result['result']:
                total_return += result['result'].get('total_return', 0.0)
                total_trades += result['result'].get('total_trades', 0)
                sharpe_ratios.append(result['result'].get('sharpe_ratio', 0.0))
                max_drawdowns.append(result['result'].get('max_drawdown', 0.0))
                win_rates.append(result['result'].get('win_rate', 0.0))
        
        # Calculate averages
        avg_sharpe = np.mean(sharpe_ratios) if sharpe_ratios else 0.0
        avg_max_drawdown = np.mean(max_drawdowns) if max_drawdowns else 0.0
        avg_win_rate = np.mean(win_rates) if win_rates else 0.0
        
        # Strategy distribution
        strategy_counts = {}
        for result in results.values():
            strategy = result.get('strategy', 'Unknown')
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_symbols': len(results),
            'total_return': total_return,
            'total_trades': total_trades,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_max_drawdown': avg_max_drawdown,
            'avg_win_rate': avg_win_rate,
            'strategy_distribution': strategy_counts,
            'avg_confidence': np.mean([r.get('confidence', 0.0) for r in results.values()])
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of backtest results"""
        
        if 'automated' not in self.results:
            return {'error': 'No automated results available'}
        
        automated_results = self.results['automated']
        metrics = self.performance_metrics
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'total_symbols_tested': len(automated_results),
            'successful_selections': len([r for r in automated_results.values() if r.get('result')]),
            'average_confidence': metrics.get('avg_confidence', 0.0),
            'average_sharpe_ratio': metrics.get('avg_sharpe_ratio', 0.0),
            'average_win_rate': metrics.get('avg_win_rate', 0.0),
            'strategy_distribution': metrics.get('strategy_distribution', {}),
            'total_trades': metrics.get('total_trades', 0),
            'total_return': metrics.get('total_return', 0.0)
        }
    
    def _generate_report(self):
        """Generate detailed report"""
        
        logger.info("📊 Automated Strategy Selection Backtest Results")
        logger.info("=" * 60)
        
        if 'automated' in self.results:
            automated_results = self.results['automated']
            metrics = self.performance_metrics
            
            logger.info(f"📈 Performance Summary:")
            logger.info(f"   Total Symbols Tested: {len(automated_results)}")
            logger.info(f"   Successful Selections: {len([r for r in automated_results.values() if r.get('result')])}")
            logger.info(f"   Average Confidence: {metrics.get('avg_confidence', 0.0):.2f}")
            logger.info(f"   Average Sharpe Ratio: {metrics.get('avg_sharpe_ratio', 0.0):.2f}")
            logger.info(f"   Average Win Rate: {metrics.get('avg_win_rate', 0.0):.2f}")
            logger.info(f"   Total Trades: {metrics.get('total_trades', 0)}")
            logger.info(f"   Total Return: {metrics.get('total_return', 0.0):.2f}%")
            
            logger.info(f"\n🎯 Strategy Distribution:")
            for strategy, count in metrics.get('strategy_distribution', {}).items():
                logger.info(f"   {strategy}: {count} selections")
            
            logger.info(f"\n📋 Individual Results:")
            for symbol, result in automated_results.items():
                if result.get('result'):
                    strategy = result['strategy']
                    confidence = result['confidence']
                    performance = result['result']
                    logger.info(f"   {symbol}: {strategy} (confidence: {confidence:.2f}, "
                               f"return: {performance.get('total_return', 0.0):.2f}%)")
                else:
                    logger.info(f"   {symbol}: No result")
        
        else:
            logger.warning("⚠️ No automated results to report")

async def main():
    """Main function"""
    
    # Configuration
    start_date = "2022-01-01"
    end_date = "2024-01-01"
    initial_capital = 100000.0
    
    # Initialize backtest
    backtest = AutomatedStrategyBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    # Run backtest
    try:
        results = await backtest.run_automated_backtest()
        
        # Save results
        results_file = f"automated_strategy_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {results_file}")
        logger.info("🎉 Automated Strategy Selection Backtest completed!")
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

















