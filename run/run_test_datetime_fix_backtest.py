#!/usr/bin/env python3
"""
Test Backtest - DateTime Fix Verification
Tests the datetime comparison fix in GreeksEnhanced strategy
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.append('/app/src')

from backtesting.engine.backtest_engine import BacktestEngine
from utils.config import get_config

async def main():
    """Run test backtest to verify datetime fix"""
    
    # Set environment variables for database-only mode
    os.environ['DATABASE_ONLY'] = 'true'
    os.environ['ENABLE_LLM_EVALUATION'] = 'false'
    
    # Get configuration
    config = get_config()
    
    logger.info("🚀 Starting Test Backtest - DateTime Fix Verification")
    logger.info("📊 Testing datetime comparison fix in GreeksEnhanced strategy")
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine()
        
        # Define backtest parameters - shorter period for testing
        symbols = ['SPY', 'QQQ']  # Fewer symbols for faster testing
        start_date = '2024-01-01'
        end_date = '2024-01-31'  # Shorter period
        risk_profile = 'aggressive'
        
        # Focus on GreeksEnhanced strategy to test the fix
        strategies = [
            'GreeksEnhanced',
            'BollingerBands'  # For comparison
        ]
        
        logger.info(f"📊 Test Backtest Parameters:")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Date Range: {start_date} to {end_date}")
        logger.info(f"   Risk Profile: {risk_profile}")
        logger.info(f"   Strategies: {strategies}")
        logger.info(f"   Database Only: True")
        logger.info(f"   LLM Evaluation: False")
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        # Store results
        await engine.store_results(
            results=results,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            database_only=True,
            backtest_name="test_datetime_fix"
        )
        
        # Print summary
        logger.info("✅ Test Backtest Completed!")
        logger.info("📊 Results Summary:")
        
        for strategy_name, result in results.items():
            logger.info(f"   {strategy_name}:")
            logger.info(f"     Total Return: {result.total_return_pct:.2f}%")
            logger.info(f"     Sharpe Ratio: {result.sharpe_ratio:.2f}")
            logger.info(f"     Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info(f"     Total Trades: {result.total_trades}")
            logger.info(f"     Win Rate: {result.win_rate:.1%}")
            logger.info(f"     Profit Factor: {result.profit_factor:.2f}")
            logger.info("")
        
        # Check if GreeksEnhanced ran without datetime errors
        if 'GreeksEnhanced' in results:
            logger.info("✅ SUCCESS: GreeksEnhanced strategy completed without datetime comparison errors!")
        else:
            logger.warning("⚠️ GreeksEnhanced strategy did not complete - may still have issues")
        
        # Find best performing strategy
        if results:
            best_strategy = max(results.items(), key=lambda x: x[1].total_return_pct)
            logger.info(f"🏆 Best Performing Strategy: {best_strategy[0]} ({best_strategy[1].total_return_pct:.2f}%)")
        
    except Exception as e:
        logger.error(f"❌ Test backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 