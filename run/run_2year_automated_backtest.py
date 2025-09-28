#!/usr/bin/env python3
"""
2-Year Automated Strategy Selection Backtest
===========================================

Runs a comprehensive 2-year backtest (2022-2024) using the automated strategy selection system.
This script integrates with your existing backtest infrastructure to test the automated
strategy selection against historical data.

Usage:
    python run_2year_automated_backtest.py
    python run_2year_automated_backtest.py --symbols AAPL MSFT GOOGL
    python run_2year_automated_backtest.py --start-date 2022-01-01 --end-date 2024-01-01
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger
from src.utils.trading_config import get_options_symbols

# Setup logging
logger = get_trading_logger()

class TwoYearAutomatedBacktest:
    """
    2-Year Automated Strategy Selection Backtest
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
        
        # Initialize backtest engine
        self.engine = BacktestEngine(
            use_real_data=True,
            use_cache=True
        )
        
        # Strategy selection logic (simplified version)
        self.strategy_selection_rules = self._initialize_strategy_rules()
        
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
    
    def _initialize_strategy_rules(self) -> Dict[str, Dict]:
        """Initialize strategy selection rules based on market conditions"""
        
        return {
            # Market condition detection rules
            'market_conditions': {
                'bull_trending': {
                    'indicators': ['SMA_20 > SMA_50', 'MACD > MACD_Signal', 'RSI > 50'],
                    'strategies': ['SMACrossoverStrategy', 'MACDStrategy', 'MomentumStrategy'],
                    'priority': 1
                },
                'bear_trending': {
                    'indicators': ['SMA_20 < SMA_50', 'MACD < MACD_Signal', 'RSI < 50'],
                    'strategies': ['SMACrossoverStrategy', 'MACDStrategy', 'MeanReversionStrategy'],
                    'priority': 2
                },
                'sideways_range': {
                    'indicators': ['abs(SMA_20 - SMA_50) / SMA_50 < 0.02', 'RSI between 30-70'],
                    'strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MeanReversionStrategy'],
                    'priority': 3
                },
                'high_volatility': {
                    'indicators': ['ATR / Close > 0.03', 'Volume > 1.5 * Volume_SMA'],
                    'strategies': ['VolatilityBreakoutStrategy', 'VWAPStrategy'],
                    'priority': 4
                },
                'low_volatility': {
                    'indicators': ['ATR / Close < 0.01', 'Volume < 0.8 * Volume_SMA'],
                    'strategies': ['VolatilityBreakoutStrategy', 'MomentumStrategy'],
                    'priority': 5
                }
            },
            
            # Strategy performance weights
            'strategy_weights': {
                'SMACrossoverStrategy': 0.25,
                'RSIStrategy': 0.20,
                'MACDStrategy': 0.20,
                'BollingerBandsStrategy': 0.15,
                'MeanReversionStrategy': 0.10,
                'MomentumStrategy': 0.10
            },
            
            # Risk management
            'risk_management': {
                'max_risk_per_strategy': 0.05,
                'min_confidence_threshold': 0.6,
                'max_correlation': 0.7
            }
        }
    
    async def run_automated_backtest(self) -> Dict[str, Any]:
        """Run 2-year automated strategy selection backtest"""
        
        logger.info("🚀 Starting 2-Year Automated Strategy Selection Backtest")
        logger.info("=" * 70)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Period: {self.start_date} to {self.end_date}")
        logger.info(f"   Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"   Symbols: {len(self.symbols)} stocks")
        logger.info(f"   Strategy Selection: Automated based on market conditions")
        
        # Step 1: Run individual strategy backtests
        logger.info("\n🔄 Step 1: Running individual strategy backtests...")
        individual_results = await self._run_individual_strategies()
        
        # Step 2: Analyze market conditions for each symbol
        logger.info("\n🔍 Step 2: Analyzing market conditions...")
        market_analysis = await self._analyze_market_conditions(individual_results)
        
        # Step 3: Select optimal strategies based on conditions
        logger.info("\n🎯 Step 3: Selecting optimal strategies...")
        optimal_strategies = self._select_optimal_strategies(market_analysis)
        
        # Step 4: Calculate automated performance
        logger.info("\n📈 Step 4: Calculating automated performance...")
        automated_performance = self._calculate_automated_performance(
            individual_results, optimal_strategies
        )
        
        # Step 5: Generate comparison report
        logger.info("\n📊 Step 5: Generating comparison report...")
        comparison_report = self._generate_comparison_report(
            individual_results, automated_performance
        )
        
        # Store results
        self.results = {
            'individual_strategies': individual_results,
            'market_analysis': market_analysis,
            'optimal_strategies': optimal_strategies,
            'automated_performance': automated_performance,
            'comparison_report': comparison_report
        }
        
        # Generate final report
        self._generate_final_report()
        
        return self.results
    
    async def _run_individual_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Run backtests for individual strategies"""
        
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
        
        logger.info(f"   Testing {len(strategies)} individual strategies...")
        
        # Run backtest
        results = await self.engine.run_backtest(
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            strategies=strategies
        )
        
        logger.info(f"   ✅ Completed individual strategy backtests")
        return results
    
    async def _analyze_market_conditions(self, individual_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze market conditions for each symbol"""
        
        market_analysis = {}
        
        for symbol in self.symbols:
            # This would integrate with your market data service
            # For now, we'll use a simplified analysis based on strategy performance
            
            symbol_analysis = {
                'symbol': symbol,
                'market_condition': 'sideways_range',  # Default
                'confidence': 0.6,
                'indicators': {
                    'trend_strength': 0.02,
                    'volatility_level': 0.02,
                    'momentum': 0.0,
                    'volume_profile': 1.0
                },
                'strategy_performance': {}
            }
            
            # Analyze strategy performance for this symbol
            for strategy_name, strategy_results in individual_results.items():
                if strategy_results and hasattr(strategy_results, 'symbols'):
                    symbol_result = getattr(strategy_results.symbols, symbol, None)
                    if symbol_result:
                        symbol_analysis['strategy_performance'][strategy_name] = {
                            'total_return': getattr(symbol_result, 'total_return_pct', 0.0),
                            'sharpe_ratio': getattr(symbol_result, 'sharpe_ratio', 0.0),
                            'max_drawdown': getattr(symbol_result, 'max_drawdown_pct', 0.0),
                            'win_rate': getattr(symbol_result, 'win_rate', 0.0)
                        }
            
            market_analysis[symbol] = symbol_analysis
        
        logger.info(f"   ✅ Analyzed market conditions for {len(market_analysis)} symbols")
        return market_analysis
    
    def _select_optimal_strategies(self, market_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Select optimal strategy for each symbol based on market conditions"""
        
        optimal_strategies = {}
        
        for symbol, analysis in market_analysis.items():
            # Determine market condition
            market_condition = analysis['market_condition']
            
            # Get available strategies for this condition
            available_strategies = self.strategy_selection_rules['market_conditions'][market_condition]['strategies']
            
            # Select best performing strategy
            best_strategy = None
            best_score = -float('inf')
            
            for strategy_name in available_strategies:
                if strategy_name in analysis['strategy_performance']:
                    performance = analysis['strategy_performance'][strategy_name]
                    
                    # Calculate composite score
                    score = (
                        performance['total_return'] * 0.4 +
                        performance['sharpe_ratio'] * 0.3 +
                        performance['win_rate'] * 0.2 +
                        (1 - performance['max_drawdown']) * 0.1
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_strategy = strategy_name
            
            optimal_strategies[symbol] = best_strategy or 'SMACrossoverStrategy'  # Default
        
        logger.info(f"   ✅ Selected optimal strategies for {len(optimal_strategies)} symbols")
        return optimal_strategies
    
    def _calculate_automated_performance(self, individual_results: Dict[str, Dict[str, Any]], 
                                       optimal_strategies: Dict[str, str]) -> Dict[str, Any]:
        """Calculate performance of automated strategy selection"""
        
        automated_performance = {
            'total_return': 0.0,
            'total_trades': 0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'symbol_performance': {}
        }
        
        returns = []
        sharpe_ratios = []
        max_drawdowns = []
        win_rates = []
        
        for symbol, strategy_name in optimal_strategies.items():
            if strategy_name in individual_results:
                strategy_results = individual_results[strategy_name]
                if strategy_results and hasattr(strategy_results, 'symbols'):
                    symbol_result = getattr(strategy_results.symbols, symbol, None)
                    if symbol_result:
                        total_return = getattr(symbol_result, 'total_return_pct', 0.0)
                        sharpe_ratio = getattr(symbol_result, 'sharpe_ratio', 0.0)
                        max_drawdown = getattr(symbol_result, 'max_drawdown_pct', 0.0)
                        win_rate = getattr(symbol_result, 'win_rate', 0.0)
                        total_trades = getattr(symbol_result, 'total_trades', 0)
                        
                        automated_performance['symbol_performance'][symbol] = {
                            'strategy': strategy_name,
                            'total_return': total_return,
                            'sharpe_ratio': sharpe_ratio,
                            'max_drawdown': max_drawdown,
                            'win_rate': win_rate,
                            'total_trades': total_trades
                        }
                        
                        returns.append(total_return)
                        sharpe_ratios.append(sharpe_ratio)
                        max_drawdowns.append(max_drawdown)
                        win_rates.append(win_rate)
                        automated_performance['total_trades'] += total_trades
        
        # Calculate averages
        if returns:
            automated_performance['total_return'] = sum(returns) / len(returns)
            automated_performance['sharpe_ratio'] = sum(sharpe_ratios) / len(sharpe_ratios)
            automated_performance['max_drawdown'] = sum(max_drawdowns) / len(max_drawdowns)
            automated_performance['win_rate'] = sum(win_rates) / len(win_rates)
        
        logger.info(f"   ✅ Calculated automated performance metrics")
        return automated_performance
    
    def _generate_comparison_report(self, individual_results: Dict[str, Dict[str, Any]], 
                                  automated_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison report between individual strategies and automated selection"""
        
        # Calculate individual strategy averages
        individual_averages = {}
        
        for strategy_name, strategy_results in individual_results.items():
            if strategy_results:
                individual_averages[strategy_name] = {
                    'total_return': getattr(strategy_results, 'total_return_pct', 0.0),
                    'sharpe_ratio': getattr(strategy_results, 'sharpe_ratio', 0.0),
                    'max_drawdown': getattr(strategy_results, 'max_drawdown_pct', 0.0),
                    'win_rate': getattr(strategy_results, 'win_rate', 0.0),
                    'total_trades': getattr(strategy_results, 'total_trades', 0)
                }
        
        # Calculate best individual strategy
        best_individual = max(individual_averages.items(), 
                            key=lambda x: x[1]['total_return']) if individual_averages else None
        
        # Generate comparison
        comparison = {
            'automated_performance': automated_performance,
            'individual_averages': individual_averages,
            'best_individual_strategy': best_individual,
            'improvement_over_best': 0.0,
            'improvement_over_average': 0.0
        }
        
        if best_individual:
            best_return = best_individual[1]['total_return']
            automated_return = automated_performance['total_return']
            comparison['improvement_over_best'] = automated_return - best_return
        
        if individual_averages:
            avg_return = sum(s['total_return'] for s in individual_averages.values()) / len(individual_averages)
            automated_return = automated_performance['total_return']
            comparison['improvement_over_average'] = automated_return - avg_return
        
        logger.info(f"   ✅ Generated comparison report")
        return comparison
    
    def _generate_final_report(self):
        """Generate final comprehensive report"""
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 2-YEAR AUTOMATED STRATEGY SELECTION BACKTEST RESULTS")
        logger.info("=" * 70)
        
        if 'comparison_report' in self.results:
            report = self.results['comparison_report']
            automated = report['automated_performance']
            
            logger.info(f"\n🎯 AUTOMATED STRATEGY SELECTION PERFORMANCE:")
            logger.info(f"   Total Return: {automated['total_return']:.2f}%")
            logger.info(f"   Sharpe Ratio: {automated['sharpe_ratio']:.2f}")
            logger.info(f"   Max Drawdown: {automated['max_drawdown']:.2f}%")
            logger.info(f"   Win Rate: {automated['win_rate']:.2f}")
            logger.info(f"   Total Trades: {automated['total_trades']}")
            
            logger.info(f"\n📈 COMPARISON WITH INDIVIDUAL STRATEGIES:")
            logger.info(f"   Improvement over Best Individual: {report['improvement_over_best']:.2f}%")
            logger.info(f"   Improvement over Average: {report['improvement_over_average']:.2f}%")
            
            if report['best_individual_strategy']:
                best_name, best_perf = report['best_individual_strategy']
                logger.info(f"   Best Individual Strategy: {best_name} ({best_perf['total_return']:.2f}%)")
            
            logger.info(f"\n🎯 STRATEGY SELECTION DISTRIBUTION:")
            strategy_counts = {}
            for symbol, perf in automated['symbol_performance'].items():
                strategy = perf['strategy']
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            for strategy, count in strategy_counts.items():
                logger.info(f"   {strategy}: {count} selections")
        
        logger.info(f"\n💾 Results saved to automated_strategy_backtest_results.json")
        logger.info("🎉 2-Year Automated Strategy Selection Backtest completed!")

async def main():
    """Main function with command line argument parsing"""
    
    parser = argparse.ArgumentParser(description='Run 2-year automated strategy selection backtest')
    parser.add_argument('--symbols', nargs='+', default=None,
                       help='List of symbols to test (default: predefined list)')
    parser.add_argument('--start-date', default='2022-01-01', 
                       help='Start date (YYYY-MM-DD, default: 2022-01-01)')
    parser.add_argument('--end-date', default='2024-01-01', 
                       help='End date (YYYY-MM-DD, default: 2024-01-01)')
    parser.add_argument('--capital', type=float, default=100000.0,
                       help='Initial capital (default: 100000)')
    
    args = parser.parse_args()
    
    # Initialize backtest
    backtest = TwoYearAutomatedBacktest(
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.capital,
        symbols=args.symbols
    )
    
    # Run backtest
    try:
        results = await backtest.run_automated_backtest()
        
        # Save results
        results_file = "automated_strategy_backtest_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {results_file}")
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())








