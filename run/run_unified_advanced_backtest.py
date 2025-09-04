#!/usr/bin/env python3
"""
Unified Advanced Backtest Script
Combines all advanced features:
- Real market data from Polygon
- AI-enhanced strategies with LLM evaluation
- Advanced exit strategies
- Portfolio strategies
- Enhanced entry-exit management
- Greeks backtesting
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, '/app/src')

from src.services.market_data.market_data_provider import MarketDataProvider
from src.services.market_data.cached_market_data_manager import CachedMarketDataManager
from src.services.ai.ollama_service import OllamaService
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.strategies.portfolio_strategy import PortfolioStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.strategies.macd_ai_enhanced_strategy import MACDStrategy
from src.strategies.bollinger_bands_ai_enhanced_strategy import BollingerBandsStrategy
from src.strategies.mean_reversion.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.momentum.momentum_strategy import MomentumStrategy
from src.strategies.breakout.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.strategies.sma_crossover_ai_enhanced_strategy import SMACrossoverAIEnhancedStrategy
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.config import get_config
from src.utils.enhanced_logging import get_trading_logger

# Setup logging
logger = get_trading_logger()

class UnifiedAdvancedBacktest:
    def __init__(self):
        self.config = get_config()
        self.setup_services()
        self.results = {}
        
    def setup_services(self):
        """Setup all required services"""
        logger.info("Setting up services...")
        
        # Market data provider
        self.market_data_provider = MarketDataProvider()
        self.cached_manager = CachedMarketDataManager(self.market_data_provider)
        
        # AI service for LLM evaluation
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://192.168.65.3:11434')
        self.ollama_service = OllamaService(
            base_url=ollama_url,
            model=os.getenv('OLLAMA_MODEL', 'gemma3:1b'),
            timeout=float(os.getenv('OLLAMA_TIMEOUT', '300.0'))
        )
        
        # Backtest engine
        self.backtest_engine = BacktestEngine()
        
    def get_symbols(self) -> List[str]:
        """Get symbols for backtesting"""
        try:
            from src.utils.trading_config import get_symbols
            return get_symbols()
        except ImportError:
            # Fallback to default symbols
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    
    def create_advanced_strategies(self) -> Dict[str, Any]:
        """Create all advanced strategies with AI enhancement"""
        strategies = {}
        
        # Base strategies
        base_strategies = {
            'rsi': RSIStrategy(),
            'macd': MACDStrategy(),
            'bollinger': BollingerBandsStrategy(),
            'mean_reversion': MeanReversionStrategy(),
            'momentum': MomentumStrategy(),
            'volatility_breakout': VolatilityBreakoutStrategy(),
            'sma_crossover': SMACrossoverAIEnhancedStrategy(),
        }
        
        # Create AI-enhanced versions
        for name, strategy in base_strategies.items():
            enhanced_strategy = NewsEnhancedStrategy(
                base_strategy=strategy,
                ollama_service=self.ollama_service,
                use_llm_evaluation=True
            )
            strategies[f'ai_enhanced_{name}'] = enhanced_strategy
        
        # Portfolio strategy
        strategies['portfolio'] = PortfolioStrategy(
            strategies=list(base_strategies.values()),
            ollama_service=self.ollama_service
        )
        
        return strategies
    
    async def run_backtest_for_symbol(self, symbol: str, strategies: Dict[str, Any]) -> Dict[str, Any]:
        """Run backtest for a single symbol"""
        logger.info(f"Running backtest for {symbol}")
        
        try:
            # Get market data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 year of data
            
            data = await self.cached_manager.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval='1d'
            )
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                return {}
            
            results = {}
            
            # Run each strategy
            for strategy_name, strategy in strategies.items():
                try:
                    logger.info(f"Running {strategy_name} for {symbol}")
                    
                    # Run backtest
                    backtest_result = await self.backtest_engine.run_backtest(
                        strategy=strategy,
                        data=data,
                        initial_capital=100000,
                        commission=0.001
                    )
                    
                    # Add metadata
                    backtest_result['symbol'] = symbol
                    backtest_result['strategy'] = strategy_name
                    backtest_result['data_points'] = len(data)
                    backtest_result['start_date'] = data.index[0].strftime('%Y-%m-%d')
                    backtest_result['end_date'] = data.index[-1].strftime('%Y-%m-%d')
                    
                    results[strategy_name] = backtest_result
                    
                    logger.info(f"{strategy_name} for {symbol}: "
                              f"Return={backtest_result.get('total_return', 0):.2%}, "
                              f"Sharpe={backtest_result.get('sharpe_ratio', 0):.2f}")
                    
                except Exception as e:
                    logger.error(f"Error running {strategy_name} for {symbol}: {e}")
                    results[strategy_name] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error in backtest for {symbol}: {e}")
            return {}
    
    async def run_comprehensive_backtest(self):
        """Run comprehensive backtest across all symbols and strategies"""
        logger.info("Starting unified advanced backtest...")
        
        # Get symbols
        symbols = self.get_symbols()
        logger.info(f"Testing {len(symbols)} symbols: {symbols}")
        
        # Create strategies
        strategies = self.create_advanced_strategies()
        logger.info(f"Created {len(strategies)} strategies")
        
        # Run backtests
        all_results = {}
        
        for symbol in symbols:
            symbol_results = await self.run_backtest_for_symbol(symbol, strategies)
            all_results[symbol] = symbol_results
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(1)
        
        # Analyze results
        self.analyze_results(all_results)
        
        # Save results
        self.save_results(all_results)
        
        return all_results
    
    def analyze_results(self, results: Dict[str, Any]):
        """Analyze and log backtest results"""
        logger.info("=== BACKTEST RESULTS ANALYSIS ===")
        
        # Collect all strategy results
        strategy_summaries = {}
        
        for symbol, symbol_results in results.items():
            for strategy_name, strategy_result in symbol_results.items():
                if 'error' in strategy_result:
                    continue
                    
                if strategy_name not in strategy_summaries:
                    strategy_summaries[strategy_name] = []
                
                strategy_summaries[strategy_name].append({
                    'symbol': symbol,
                    'total_return': strategy_result.get('total_return', 0),
                    'sharpe_ratio': strategy_result.get('sharpe_ratio', 0),
                    'max_drawdown': strategy_result.get('max_drawdown', 0),
                    'win_rate': strategy_result.get('win_rate', 0)
                })
        
        # Log summary for each strategy
        for strategy_name, strategy_data in strategy_summaries.items():
            if not strategy_data:
                continue
                
            returns = [d['total_return'] for d in strategy_data]
            sharpe_ratios = [d['sharpe_ratio'] for d in strategy_data]
            
            logger.info(f"\n{strategy_name.upper()}:")
            logger.info(f"  Average Return: {np.mean(returns):.2%}")
            logger.info(f"  Average Sharpe: {np.mean(sharpe_ratios):.2f}")
            logger.info(f"  Best Performer: {max(strategy_data, key=lambda x: x['total_return'])['symbol']}")
            logger.info(f"  Worst Performer: {min(strategy_data, key=lambda x: x['total_return'])['symbol']}")
    
    def save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/app/backtest_results/unified_advanced_backtest_{timestamp}.json'
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main():
    """Main function"""
    logger.info("Starting Unified Advanced Backtest")
    
    try:
        backtest = UnifiedAdvancedBacktest()
        results = await backtest.run_comprehensive_backtest()
        
        logger.info("Unified Advanced Backtest completed successfully!")
        return results
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 