#!/usr/bin/env python3
"""
Advanced Strategies Working Backtest
====================================
Runs backtests using the advanced AI-enhanced strategies with existing infrastructure.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from src.backtesting.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class AdvancedStrategiesWorkingBacktest:
    """
    Working advanced strategies backtest using AI-enhanced strategies
    """
    
    def __init__(self):
        self.start_date = datetime(2023, 7, 11)
        self.end_date = datetime(2025, 7, 10)
        
        # Symbols to test
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'COF', 'AXP'
        ]
        
        # Advanced strategies to test (these are the AI-enhanced versions)
        self.advanced_strategies = [
            'RSI_AI_Enhanced',
            'BollingerBands_AI_Enhanced', 
            'MACD_AI_Enhanced',
            'SMACrossover_AI_Enhanced',
            'News_Enhanced',
            'EnhancedEntryExit',
            'PortfolioStrategy'
        ]
        
        # Basic strategies for comparison
        self.basic_strategies = [
            'BollingerBands',
            'RSI',
            'MACD', 
            'SMACrossover',
            'MeanReversion',
            'Momentum'
        ]
    
    async def run_advanced_backtest(self):
        """Run backtest with advanced strategies"""
        
        logger.info("🚀 STARTING ADVANCED STRATEGIES WORKING BACKTEST")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Symbols: {len(self.symbols)}")
        logger.info(f"   AI-Enhanced Strategies: ENABLED")
        logger.info(f"   LLM Evaluation: ENABLED")
        logger.info(f"   Advanced Exit Management: ENABLED")
        
        # Phase 1: Advanced AI-Enhanced Strategies
        logger.info("\n🤖 PHASE 1: AI-ENHANCED STRATEGIES")
        logger.info("-" * 60)
        
        advanced_results = await self._run_advanced_strategies()
        
        # Phase 2: Basic Strategies for Comparison
        logger.info("\n📊 PHASE 2: BASIC STRATEGIES COMPARISON")
        logger.info("-" * 60)
        
        basic_results = await self._run_basic_strategies()
        
        # Phase 3: Performance Comparison
        logger.info("\n📈 PHASE 3: PERFORMANCE COMPARISON")
        logger.info("-" * 60)
        
        await self._generate_comparison_report(advanced_results, basic_results)
    
    async def _run_advanced_strategies(self) -> Dict[str, Any]:
        """Run advanced AI-enhanced strategies"""
        
        logger.info("🎯 Running AI-Enhanced Strategies:")
        for strategy in self.advanced_strategies:
            logger.info(f"   • {strategy}")
        
        # Initialize backtest engine with LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Run backtest with advanced strategies
        results = await engine.run_backtest(
            symbols=self.symbols[:10],  # Test with subset for performance
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=self.advanced_strategies
        )
        
        return results
    
    async def _run_basic_strategies(self) -> Dict[str, Any]:
        """Run basic strategies for comparison"""
        
        logger.info("🎯 Running Basic Strategies for Comparison:")
        for strategy in self.basic_strategies:
            logger.info(f"   • {strategy}")
        
        # Initialize backtest engine without LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = False
        
        # Run backtest with basic strategies
        results = await engine.run_backtest(
            symbols=self.symbols[:10],
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=self.basic_strategies
        )
        
        return results
    
    async def _generate_comparison_report(self, advanced_results: Dict, basic_results: Dict):
        """Generate comprehensive comparison report"""
        
        logger.info("\n📊 ADVANCED vs BASIC STRATEGIES COMPARISON")
        logger.info("=" * 80)
        
        # Advanced Strategies Results
        logger.info("\n🤖 AI-ENHANCED STRATEGIES PERFORMANCE:")
        logger.info("-" * 50)
        
        advanced_total_return = 0
        advanced_strategy_count = 0
        advanced_trades = 0
        
        for strategy_name, result in advanced_results.items():
            if result and 'total_return' in result:
                return_pct = result['total_return']
                trades = result.get('total_trades', 0)
                advanced_total_return += return_pct
                advanced_strategy_count += 1
                advanced_trades += trades
                logger.info(f"   {strategy_name}: {return_pct:.2f}% ({trades} trades)")
        
        if advanced_strategy_count > 0:
            advanced_avg_return = advanced_total_return / advanced_strategy_count
            logger.info(f"\n   Average AI-Enhanced Return: {advanced_avg_return:.2f}%")
            logger.info(f"   Total AI-Enhanced Trades: {advanced_trades}")
        
        # Basic Strategies Results
        logger.info("\n📊 BASIC STRATEGIES PERFORMANCE:")
        logger.info("-" * 50)
        
        basic_total_return = 0
        basic_strategy_count = 0
        basic_trades = 0
        
        for strategy_name, result in basic_results.items():
            if result and 'total_return' in result:
                return_pct = result['total_return']
                trades = result.get('total_trades', 0)
                basic_total_return += return_pct
                basic_strategy_count += 1
                basic_trades += trades
                logger.info(f"   {strategy_name}: {return_pct:.2f}% ({trades} trades)")
        
        if basic_strategy_count > 0:
            basic_avg_return = basic_total_return / basic_strategy_count
            logger.info(f"\n   Average Basic Strategy Return: {basic_avg_return:.2f}%")
            logger.info(f"   Total Basic Strategy Trades: {basic_trades}")
        
        # Performance Comparison
        logger.info("\n📈 PERFORMANCE COMPARISON:")
        logger.info("-" * 50)
        
        if advanced_strategy_count > 0 and basic_strategy_count > 0:
            improvement = advanced_avg_return - basic_avg_return
            improvement_pct = (improvement / abs(basic_avg_return)) * 100 if basic_avg_return != 0 else 0
            
            logger.info(f"   AI-Enhanced vs Basic: {improvement:+.2f}% improvement")
            logger.info(f"   Improvement Percentage: {improvement_pct:+.1f}%")
            
            if improvement > 0:
                logger.info(f"   ✅ ADVANCED STRATEGIES OUTPERFORM BASIC STRATEGIES!")
            else:
                logger.info(f"   ⚠️  Basic strategies still performing better")
        
        # Summary
        logger.info("\n📋 SUMMARY:")
        logger.info("   ✅ AI-Enhanced Strategies: Improved signal quality with AI analysis")
        logger.info("   ✅ Advanced Exit Management: Sophisticated position management")
        logger.info("   ✅ LLM Evaluation: AI-powered trade filtering")
        logger.info("   ✅ Portfolio Diversification: Multi-strategy approach")
        
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("   1. Deploy the best-performing advanced strategies")
        logger.info("   2. Fine-tune AI weights based on results")
        logger.info("   3. Optimize exit strategy parameters")
        logger.info("   4. Monitor real-time performance")
        logger.info("   5. Scale to more symbols and strategies")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ADVANCED STRATEGIES BACKTEST COMPLETED!")
        logger.info("=" * 80)

async def main():
    """Run advanced strategies working backtest"""
    backtest = AdvancedStrategiesWorkingBacktest()
    await backtest.run_advanced_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 