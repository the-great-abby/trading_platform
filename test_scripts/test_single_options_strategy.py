#!/usr/bin/env python3
"""
Simple test for single options strategy
"""

import os
import sys
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.backtesting.engine.backtest_engine import BacktestEngine

# Setup logging
logger = get_trading_logger()

async def test_single_strategy():
    """Test a single options strategy"""
    
    logger.info("🚀 Testing single options strategy")
    
    # Simple configuration
    symbols = ['SPY']  # Just one symbol
    start_date = "2023-01-01"
    end_date = "2023-02-01"  # Short period
    strategies = ['EnhancedIronCondor']
    
    logger.info(f"📊 Test Configuration:")
    logger.info(f"   Symbol: {symbols[0]}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Strategy: {strategies[0]}")
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    try:
        logger.info("🔄 Starting backtest...")
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        if results and strategies[0] in results:
            result = results[strategies[0]]
            logger.info(f"✅ Test completed successfully!")
            logger.info(f"   Total Trades: {result.total_trades}")
            logger.info(f"   Total Return: {result.total_return_pct:.2f}%")
        else:
            logger.warning("⚠️  No results returned")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_single_strategy()) 