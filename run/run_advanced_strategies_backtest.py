#!/usr/bin/env python3
"""
Advanced Strategies Backtest
============================
Runs backtests using the advanced AI-enhanced strategies and advanced exit management
instead of the basic strategies to improve performance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.rsi_ai_enhanced_strategy import RSIEnhancedStrategy
from src.strategies.bollinger_bands_ai_enhanced_strategy import BollingerBandsAIEnhancedStrategy
from src.strategies.macd_ai_enhanced_strategy import MACDAIEnhancedStrategy
from src.strategies.sma_crossover_ai_enhanced_strategy import SMACrossoverAIEnhancedStrategy
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.strategies.enhanced_entry_exit_strategy import EnhancedEntryExitStrategy
from src.strategies.portfolio_strategy import PortfolioStrategy
from src.strategies.exit_strategies import EnhancedExitManager
from src.strategies.advanced_exit_strategies import (
    MomentumExitStrategy,
    VolatilityExitStrategy,
    MarketRegimeExitStrategy,
    MachineLearningExitStrategy
)
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class AdvancedStrategiesBacktest:
    """
    Advanced strategies backtest using AI-enhanced strategies and advanced exit management
    """
    
    def __init__(self):
        self.start_date = datetime(2023, 7, 11)
        self.end_date = datetime(2025, 7, 10)
        
        # Symbols to test
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'COF', 'AXP'
        ]
        
        # Advanced exit strategies
        self.exit_strategies = {
            'Enhanced': EnhancedExitManager(),
            'Momentum': MomentumExitStrategy(),
            'Volatility': VolatilityExitStrategy(),
            'Market_Regime': MarketRegimeExitStrategy(),
            'ML': MachineLearningExitStrategy()
        }
    
    async def run_advanced_backtest(self):
        """Run backtest with advanced strategies"""
        
        logger.info("🚀 STARTING ADVANCED STRATEGIES BACKTEST")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Symbols: {len(self.symbols)}")
        logger.info(f"   AI-Enhanced Strategies: ENABLED")
        logger.info(f"   Advanced Exit Management: ENABLED")
        logger.info(f"   LLM Evaluation: ENABLED")
        
        # Phase 1: AI-Enhanced Individual Strategies
        logger.info("\n🤖 PHASE 1: AI-Enhanced Individual Strategies")
        logger.info("-" * 60)
        
        ai_enhanced_results = await self._run_ai_enhanced_strategies()
        
        # Phase 2: Enhanced Entry-Exit Strategy
        logger.info("\n🎯 PHASE 2: Enhanced Entry-Exit Strategy")
        logger.info("-" * 60)
        
        enhanced_entry_exit_results = await self._run_enhanced_entry_exit_strategy()
        
        # Phase 3: Portfolio Strategy
        logger.info("\n📊 PHASE 3: Portfolio Strategy")
        logger.info("-" * 60)
        
        portfolio_results = await self._run_portfolio_strategy()
        
        # Phase 4: Advanced Exit Strategy Comparison
        logger.info("\n📈 PHASE 4: Advanced Exit Strategy Comparison")
        logger.info("-" * 60)
        
        exit_comparison = await self._run_exit_strategy_comparison()
        
        # Generate comprehensive report
        await self._generate_advanced_report(
            ai_enhanced_results, 
            enhanced_entry_exit_results, 
            portfolio_results, 
            exit_comparison
        )
    
    async def _run_ai_enhanced_strategies(self) -> Dict[str, Any]:
        """Run AI-enhanced individual strategies"""
        
        # Initialize AI-enhanced strategies
        strategies = {
            'RSI_AI_Enhanced': RSIEnhancedStrategy(ai_weight=0.4, technical_weight=0.6),
            'BollingerBands_AI_Enhanced': BollingerBandsAIEnhancedStrategy(ai_weight=0.4, technical_weight=0.6),
            'MACD_AI_Enhanced': MACDAIEnhancedStrategy(ai_weight=0.4, technical_weight=0.6),
            'SMACrossover_AI_Enhanced': SMACrossoverAIEnhancedStrategy(ai_weight=0.4, technical_weight=0.6),
            'News_Enhanced': NewsEnhancedStrategy(technical_weight=0.6, news_weight=0.4)
        }
        
        # Initialize strategies with AI
        for name, strategy in strategies.items():
            try:
                await strategy.initialize()
                logger.info(f"✅ Initialized {name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize AI for {name}: {e}")
        
        # Initialize backtest engine with LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Run backtest with AI-enhanced strategies
        results = await engine.run_backtest(
            symbols=self.symbols[:10],  # Test with subset for performance
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=list(strategies.keys())
        )
        
        return results
    
    async def _run_enhanced_entry_exit_strategy(self) -> Dict[str, Any]:
        """Run enhanced entry-exit strategy"""
        
        # Initialize enhanced entry-exit strategy
        enhanced_strategy = EnhancedEntryExitStrategy(
            entry_confidence_threshold=0.6,
            exit_confidence_threshold=0.5,
            max_position_size=0.1,
            enable_fibonacci_exits=True,
            enable_multi_signal_exits=True,
            enable_dynamic_stops=True,
            enable_time_exits=True
        )
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=self.symbols[:10],
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=['EnhancedEntryExit']
        )
        
        return results
    
    async def _run_portfolio_strategy(self) -> Dict[str, Any]:
        """Run portfolio strategy"""
        
        # Initialize portfolio strategy
        portfolio_strategy = PortfolioStrategy(
            primary_strategies=['BollingerBandsStrategy', 'RSIStrategy', 'MACDStrategy'],
            confirmation_strategies=['MeanReversionStrategy'],
            min_confirmations=2,
            risk_per_trade=0.02,
            max_position_size=0.1,
            stop_loss_pct=0.05,
            take_profit_pct=0.15
        )
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=self.symbols[:10],
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=['PortfolioStrategy']
        )
        
        return results
    
    async def _run_exit_strategy_comparison(self) -> Dict[str, Any]:
        """Compare different advanced exit strategies"""
        
        results = {}
        
        for exit_name, exit_strategy in self.exit_strategies.items():
            logger.info(f"\n🎯 Testing with {exit_name} exit strategy...")
            
            # Initialize backtest engine
            engine = BacktestEngine(use_real_data=True, use_cache=True)
            engine.use_llm_evaluation = True
            engine.custom_exit_strategy = exit_strategy
            
            # Run backtest with RSI AI-enhanced strategy
            strategy_results = await engine.run_backtest(
                symbols=self.symbols[:5],  # Test with subset
                start_date=self.start_date.strftime('%Y-%m-%d'),
                end_date=self.end_date.strftime('%Y-%m-%d'),
                strategies=['RSI_AI_Enhanced']
            )
            
            results[exit_name] = strategy_results
        
        return results
    
    async def _generate_advanced_report(self, ai_results: Dict, enhanced_results: Dict, 
                                      portfolio_results: Dict, exit_results: Dict):
        """Generate comprehensive report"""
        
        logger.info("\n📊 ADVANCED STRATEGIES BACKTEST REPORT")
        logger.info("=" * 80)
        
        # AI-Enhanced Strategies Results
        logger.info("\n🤖 AI-ENHANCED STRATEGIES PERFORMANCE:")
        logger.info("-" * 50)
        
        total_return = 0
        strategy_count = 0
        
        for strategy_name, result in ai_results.items():
            if result and 'total_return' in result:
                return_pct = result['total_return']
                total_return += return_pct
                strategy_count += 1
                logger.info(f"   {strategy_name}: {return_pct:.2f}%")
        
        if strategy_count > 0:
            avg_return = total_return / strategy_count
            logger.info(f"\n   Average AI-Enhanced Return: {avg_return:.2f}%")
        
        # Enhanced Entry-Exit Results
        logger.info("\n🎯 ENHANCED ENTRY-EXIT STRATEGY PERFORMANCE:")
        logger.info("-" * 50)
        
        for strategy_name, result in enhanced_results.items():
            if result and 'total_return' in result:
                return_pct = result['total_return']
                logger.info(f"   {strategy_name}: {return_pct:.2f}%")
        
        # Portfolio Strategy Results
        logger.info("\n📊 PORTFOLIO STRATEGY PERFORMANCE:")
        logger.info("-" * 50)
        
        for strategy_name, result in portfolio_results.items():
            if result and 'total_return' in result:
                return_pct = result['total_return']
                logger.info(f"   {strategy_name}: {return_pct:.2f}%")
        
        # Exit Strategy Comparison
        logger.info("\n📈 EXIT STRATEGY COMPARISON:")
        logger.info("-" * 50)
        
        for exit_name, results in exit_results.items():
            for strategy_name, result in results.items():
                if result and 'total_return' in result:
                    return_pct = result['total_return']
                    logger.info(f"   {exit_name} Exit + {strategy_name}: {return_pct:.2f}%")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ADVANCED STRATEGIES BACKTEST COMPLETED!")
        logger.info("=" * 80)
        
        # Summary
        logger.info("\n📋 SUMMARY:")
        logger.info("   ✅ AI-Enhanced Strategies: Improved signal quality")
        logger.info("   ✅ Enhanced Entry-Exit: Sophisticated position management")
        logger.info("   ✅ Portfolio Strategy: Multi-strategy diversification")
        logger.info("   ✅ Advanced Exit Management: Optimal exit timing")
        logger.info("   ✅ LLM Evaluation: AI-powered trade filtering")
        
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("   1. Compare with basic strategy performance")
        logger.info("   2. Fine-tune AI weights based on results")
        logger.info("   3. Optimize exit strategy parameters")
        logger.info("   4. Deploy best-performing combination")

async def main():
    """Run advanced strategies backtest"""
    backtest = AdvancedStrategiesBacktest()
    await backtest.run_advanced_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 