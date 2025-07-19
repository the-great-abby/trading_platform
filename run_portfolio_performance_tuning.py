#!/usr/bin/env python3
"""
Portfolio Performance Tuning Script
Focuses on optimizing trading strategy returns and profitability
"""

import os
import sys
import logging
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Add src to path
sys.path.append('/app/src')

from src.utils.backtest_config import (
    BacktestConfig, BacktestMode, RiskProfile,
    get_backtest_config, get_preset_config
)
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import SYMBOLS
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.strategies.breakout.sma_crossover import SMACrossoverStrategy
from src.strategies.advanced.trailing_stop_strategy import TrailingStopStrategy
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.strategies.options.iron_condor_strategy import IronCondorStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PortfolioPerformanceOptimizer:
    """Optimizes portfolio performance through strategy tuning and risk management"""
    
    def __init__(self):
        self.optimization_results = {}
        self.best_configs = {}
        
    async def run_performance_analysis(self):
        """Run comprehensive performance analysis and optimization"""
        logger.info("🚀 Starting Portfolio Performance Tuning Analysis")
        
        # Set environment for optimal performance
        os.environ['USE_LLM_EVALUATION'] = 'false'
        os.environ['USE_DATABASE_ONLY'] = 'true'
        os.environ['FORCE_DATABASE_ONLY'] = 'true'  # Force database-only to avoid API rate limits
        os.environ['ENABLE_GREEKS_TESTING'] = 'true'  # Enable Greeks testing
        os.environ['USE_OPTIONS_DATA'] = 'true'  # Enable options data usage
        os.environ['GREEKS_CACHE_ENABLED'] = 'true'  # Enable Greeks data cache
        
        # Test configurations
        test_configs = {
            'Conservative Risk': {
                'name': 'Conservative Risk',
                'initial_capital': 100000,
                'max_risk_per_trade': 0.01,  # 1%
                'max_daily_trades': 5,
                'stop_loss_pct': 0.02,  # 2%
                'take_profit_pct': 0.04,  # 4%
                'confidence_threshold': 0.7,
                'position_sizing': 'fixed',
                'fixed_position_size': 0.05,  # 5% per trade
                'test_period_days': 60,  # Shorter period
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],  # Fewer symbols
                'database_only': True,  # Force database-only mode
                'strategies': ['BollingerBands', 'RSI', 'MACD']
            },
            'Moderate Risk': {
                'name': 'Moderate Risk',
                'initial_capital': 100000,
                'max_risk_per_trade': 0.02,  # 2%
                'max_daily_trades': 10,
                'stop_loss_pct': 0.03,  # 3%
                'take_profit_pct': 0.06,  # 6%
                'confidence_threshold': 0.6,
                'position_sizing': 'kelly',
                'test_period_days': 60,
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                'database_only': True,
                'strategies': ['BollingerBands', 'RSI', 'MACD', 'SMACrossover']
            },
            'Aggressive Risk': {
                'name': 'Aggressive Risk',
                'initial_capital': 100000,
                'max_risk_per_trade': 0.03,  # 3%
                'max_daily_trades': 15,
                'stop_loss_pct': 0.04,  # 4%
                'take_profit_pct': 0.08,  # 8%
                'confidence_threshold': 0.5,
                'position_sizing': 'volatility',
                'test_period_days': 60,
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                'database_only': True,
                'strategies': ['BollingerBands', 'RSI', 'MACD', 'SMACrossover', 'TrailingStop']
            }
        }
        
        for config_name, config_data in test_configs.items():
            logger.info(f"Testing {config_name} configuration")
            result = await self.run_optimization_test(config_data)
            self.optimization_results[config_name] = result
            
    async def test_risk_management_optimization(self):
        """Test different risk management approaches"""
        logger.info("📊 Testing Risk Management Optimization")
        
        risk_configs = [
            {
                'name': 'Conservative Risk',
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'max_position_size': 0.05,
                'max_daily_trades': 3
            },
            {
                'name': 'Balanced Risk',
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.06,
                'max_position_size': 0.08,
                'max_daily_trades': 5
            },
            {
                'name': 'Aggressive Risk',
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'max_position_size': 0.12,
                'max_daily_trades': 8
            }
        ]
        
        for config in risk_configs:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
            
    async def test_position_sizing_optimization(self):
        """Test different position sizing strategies"""
        logger.info("💰 Testing Position Sizing Optimization")
        
        sizing_configs = [
            {
                'name': 'Fixed Position Sizing',
                'position_sizing': 'fixed',
                'position_size': 0.05
            },
            {
                'name': 'Volatility-Based Sizing',
                'position_sizing': 'volatility',
                'volatility_lookback': 20
            },
            {
                'name': 'Kelly Criterion Sizing',
                'position_sizing': 'kelly',
                'kelly_fraction': 0.25
            }
        ]
        
        for config in sizing_configs:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
            
    async def test_strategy_combination_optimization(self):
        """Test different strategy combinations"""
        logger.info("🎯 Testing Strategy Combination Optimization")
        
        strategy_combinations = [
            {
                'name': 'Momentum Focus',
                'strategies': ['MACDStrategy', 'RSIStrategy'],
                'weights': [0.6, 0.4]
            },
            {
                'name': 'Mean Reversion Focus',
                'strategies': ['BollingerBandsStrategy', 'RSIStrategy'],
                'weights': [0.7, 0.3]
            },
            {
                'name': 'Balanced Portfolio',
                'strategies': ['MACDStrategy', 'BollingerBandsStrategy', 'RSIStrategy'],
                'weights': [0.4, 0.4, 0.2]
            },
            {
                'name': 'Breakout Focus',
                'strategies': ['SMACrossoverStrategy', 'TrailingStopStrategy'],
                'weights': [0.6, 0.4]
            },
            {
                'name': 'Options Greeks Focus',
                'strategies': ['GreeksEnhancedStrategy', 'IronCondorStrategy'],
                'weights': [0.7, 0.3]
            },
            {
                'name': 'Mixed Portfolio',
                'strategies': ['MACDStrategy', 'BollingerBandsStrategy', 'GreeksEnhancedStrategy'],
                'weights': [0.4, 0.3, 0.3]
            }
        ]
        
        for config in strategy_combinations:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
            
    async def test_market_regime_adaptation(self):
        """Test market regime detection and adaptation"""
        logger.info("📈 Testing Market Regime Adaptation")
        
        regime_configs = [
            {
                'name': 'Trend Following Regime',
                'regime_detection': True,
                'trend_threshold': 0.02,
                'momentum_weight': 0.8
            },
            {
                'name': 'Mean Reversion Regime',
                'regime_detection': True,
                'volatility_threshold': 0.15,
                'reversion_weight': 0.8
            },
            {
                'name': 'Adaptive Regime',
                'regime_detection': True,
                'adaptive_weights': True
            }
        ]
        
        for config in regime_configs:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
            
    async def test_dynamic_stop_loss_optimization(self):
        """Test dynamic stop loss strategies"""
        logger.info("🛡️ Testing Dynamic Stop Loss Optimization")
        
        stop_loss_configs = [
            {
                'name': 'Fixed Stop Loss',
                'stop_loss_type': 'fixed',
                'stop_loss_pct': 0.03
            },
            {
                'name': 'ATR-Based Stop Loss',
                'stop_loss_type': 'atr',
                'atr_multiplier': 2.0
            },
            {
                'name': 'Trailing Stop Loss',
                'stop_loss_type': 'trailing',
                'trailing_pct': 0.02
            },
            {
                'name': 'Volatility-Based Stop Loss',
                'stop_loss_type': 'volatility',
                'volatility_multiplier': 1.5
            }
        ]
        
        for config in stop_loss_configs:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
            
    async def test_greeks_optimization(self):
        """Test Greeks-based options strategies"""
        logger.info("🔄 Testing Greeks Optimization")
        
        greeks_configs = [
            {
                'name': 'Delta-Neutral Strategy',
                'greeks_focus': 'delta',
                'delta_threshold': 0.1,
                'position_sizing': 'delta_weighted'
            },
            {
                'name': 'Gamma Scalping',
                'greeks_focus': 'gamma',
                'gamma_threshold': 0.05,
                'position_sizing': 'gamma_weighted'
            },
            {
                'name': 'Theta Decay Strategy',
                'greeks_focus': 'theta',
                'theta_threshold': -0.02,
                'position_sizing': 'theta_weighted'
            },
            {
                'name': 'Vega Volatility Strategy',
                'greeks_focus': 'vega',
                'vega_threshold': 0.1,
                'position_sizing': 'vega_weighted'
            },
            {
                'name': 'Multi-Greeks Strategy',
                'greeks_focus': 'multi',
                'delta_threshold': 0.1,
                'gamma_threshold': 0.05,
                'theta_threshold': -0.02,
                'vega_threshold': 0.1,
                'position_sizing': 'multi_weighted'
            }
        ]
        
        for config in greeks_configs:
            logger.info(f"Testing {config['name']} configuration")
            result = await self.run_optimization_test(config)
            self.optimization_results[config['name']] = result
        
    async def run_optimization_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single optimization test"""
        try:
            # Create backtest configuration
            backtest_config = BacktestConfig(
                backtest_mode=BacktestMode.COMPREHENSIVE,
                risk_profile=RiskProfile.AGGRESSIVE,
                initial_capital=config.get('initial_capital', 1000),  # $1K for testing
                start_date=(datetime.now() - timedelta(days=config.get('test_period_days', 730))).strftime("%Y-%m-%d"),  # 2 years for comprehensive testing
                end_date=datetime.now().strftime("%Y-%m-%d"),
                symbols=config.get('symbols', SYMBOLS[:50]),  # Use more symbols for comprehensive testing
                max_daily_trades=config.get('max_daily_trades', 5),
                stop_loss_pct=config.get('stop_loss_pct', 0.03),
                take_profit_pct=config.get('take_profit_pct', 0.06),
                max_position_size=config.get('max_position_size', 0.08),
                use_real_data=not config.get('database_only', False), # Use real data if not in database-only mode
                use_cache=True # Always use cache for testing
            )
            
            # Initialize strategies based on config
            strategies = []
            if 'strategies' in config:
                strategy_classes = {
                    'MACDStrategy': MACDStrategy,
                    'BollingerBandsStrategy': BollingerBandsStrategy,
                    'RSIStrategy': RSIStrategy,
                    'SMACrossoverStrategy': SMACrossoverStrategy,
                    'TrailingStopStrategy': TrailingStopStrategy,
                    'GreeksEnhancedStrategy': GreeksEnhancedStrategy,
                    'IronCondorStrategy': IronCondorStrategy
                }
                
                for strategy_name in config['strategies']:
                    if strategy_name in strategy_classes:
                        strategy = strategy_classes[strategy_name]()
                        strategies.append(strategy)
            
            # Run backtest
            engine = BacktestEngine(use_real_data=backtest_config.use_real_data, use_cache=backtest_config.use_cache)
            result = await engine.run_backtest(
                symbols=backtest_config.symbols,
                start_date=backtest_config.start_date,
                end_date=backtest_config.end_date,
                strategies=config.get('strategies', [])  # Pass strategy names as strings
            )
            
            # Extract performance metrics
            performance_metrics = {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': result.get('sharpe_ratio', 0),
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0),
                'profit_factor': result.get('profit_factor', 0),
                'total_trades': result.get('total_trades', 0),
                'config': config
            }
            
            logger.info(f"✅ {config.get('name', 'Unknown')} ({config['initial_capital']}): Return={performance_metrics['total_return']:.2%}, "
                       f"Sharpe={performance_metrics['sharpe_ratio']:.2f}, "
                       f"Win Rate={performance_metrics['win_rate']:.2%}")
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"❌ Error testing {config.get('name', 'Unknown')}: {str(e)}")
            return {'error': str(e), 'config': config}
            
    async def generate_optimized_portfolio(self):
        """Generate the final optimized portfolio configuration"""
        logger.info("🎯 Generating Optimized Portfolio Configuration")
        
        # Find best performing configurations
        best_risk = max(self.optimization_results.items(), 
                       key=lambda x: x[1].get('total_return', 0) if 'total_return' in x[1] else 0)
        best_sizing = max(self.optimization_results.items(), 
                         key=lambda x: x[1].get('sharpe_ratio', 0) if 'sharpe_ratio' in x[1] else 0)
        best_strategy = max(self.optimization_results.items(), 
                           key=lambda x: x[1].get('profit_factor', 0) if 'profit_factor' in x[1] else 0)
        
        # Create optimized configuration
        optimized_config = {
            'name': 'Optimized Portfolio',
            'risk_management': best_risk[1]['config'],
            'position_sizing': best_sizing[1]['config'],
            'strategy_combination': best_strategy[1]['config'],
            'expected_performance': {
                'total_return': best_risk[1].get('total_return', 0),
                'sharpe_ratio': best_sizing[1].get('sharpe_ratio', 0),
                'profit_factor': best_strategy[1].get('profit_factor', 0)
            }
        }
        
        # Save optimized configuration
        with open('/app/optimized_portfolio_config.json', 'w') as f:
            json.dump(optimized_config, f, indent=2, default=str)
            
        logger.info(f"💎 Optimized Portfolio Configuration:")
        logger.info(f"   Risk Management: {best_risk[0]}")
        logger.info(f"   Position Sizing: {best_sizing[0]}")
        logger.info(f"   Strategy Combination: {best_strategy[0]}")
        logger.info(f"   Expected Return: {optimized_config['expected_performance']['total_return']:.2%}")
        logger.info(f"   Expected Sharpe: {optimized_config['expected_performance']['sharpe_ratio']:.2f}")
        
        return optimized_config

async def main():
    """Main execution function"""
    try:
        optimizer = PortfolioPerformanceOptimizer()
        await optimizer.run_performance_analysis()
        
        logger.info("✅ Portfolio Performance Tuning Complete!")
        
    except Exception as e:
        logger.error(f"❌ Error in portfolio performance tuning: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 