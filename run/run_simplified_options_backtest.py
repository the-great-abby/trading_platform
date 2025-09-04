#!/usr/bin/env python3
"""
Simplified Options Backtest Runner

This script runs a focused backtest using only strategies that are known to work
and avoids problematic strategies with data type issues.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.backtest_config import (
    BacktestConfig, BacktestMode, RiskProfile,
    get_backtest_config, load_config_from_env
)
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import get_options_symbols
from src.utils.enhanced_logging import setup_logging

# Import only working strategies
from src.strategies.kalman_filter_strategy import KalmanFilterStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.breakout.sma_crossover import SMACrossoverStrategy
from src.strategies.advanced.trailing_stop_strategy import TrailingStopStrategy
from src.strategies.advanced.fibonacci_strategy import FibonacciStrategy

async def main():
    """Main backtest function"""
    # Setup logging
    logger = setup_logging()
    logger.info("🚀 Starting Simplified Options Backtest")
    
    try:
        # Load configuration from environment
        config = load_config_from_env()
        
        # Override with ultra-aggressive settings for this run
        config.initial_capital = 1000.0
        config.risk_profile = RiskProfile.ULTRA_AGGRESSIVE
        config.symbols = get_options_symbols()  # Use options symbols
        config.start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        config.end_date = datetime.now().strftime("%Y-%m-%d")
        config.use_llm = False
        
        logger.info(f"📊 Backtest Configuration:")
        logger.info(f"   Symbols: {len(config.symbols)} symbols")
        logger.info(f"   Date Range: {config.start_date} to {config.end_date}")
        logger.info(f"   Initial Capital: ${config.initial_capital:,.2f}")
        logger.info(f"   Risk Profile: {config.risk_profile}")
        logger.info(f"   LLM Evaluation: {config.use_llm}")
        
        # Initialize strategies (only working ones)
        strategy_classes = {
            'KalmanFilterStrategy': KalmanFilterStrategy,
            'RSIStrategy': RSIStrategy,
            'BollingerBandsStrategy': BollingerBandsStrategy,
            'MACDStrategy': MACDStrategy,
            'SMACrossoverStrategy': SMACrossoverStrategy,
            'TrailingStopStrategy': TrailingStopStrategy,
            'FibonacciStrategy': FibonacciStrategy,
        }
        
        logger.info(f"🎯 Using {len(strategy_classes)} strategies:")
        for strategy_name in strategy_classes.keys():
            logger.info(f"   - {strategy_name}")
        
        # Initialize backtest engine
        logger.info("🔧 Initializing backtest engine...")
        engine = BacktestEngine(
            use_real_data=True,
            use_cache=True
        )
        
        # Run backtest
        logger.info("🔄 Running backtest...")
        results = await engine.run_backtest(
            symbols=config.symbols,
            start_date=config.start_date,
            end_date=config.end_date,
            strategies=list(strategy_classes.keys())
        )
        
        # Log results
        if results:
            logger.info("✅ Backtest completed successfully!")
            logger.info(f"📈 Results: {results}")
        else:
            logger.warning("⚠️ Backtest completed but no results returned")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 