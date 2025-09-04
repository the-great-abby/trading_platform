#!/usr/bin/env python3
"""
Test Data Structure Fix Backtest
Tests the fixes for data structure issues in options strategies
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test_data_structure_backtest():
    """Run a test backtest to verify data structure fixes"""
    
    # Test parameters
    symbols = ['AAPL', 'MSFT', 'GOOGL']  # Small set for testing
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Test strategies that were having data structure issues
    strategies = [
        'VolatilityStrategy',
        'CoveredCall', 
        'CashSecuredPut',
        'ButterflySpread'
    ]
    
    # Initialize backtest engine
    engine = BacktestEngine(
        use_real_data=True,
        use_cache=True
    )
    
    # Disable LLM evaluation for this test
    engine.use_llm_evaluation = False
    
    logger.info("🧪 Starting Data Structure Fix Test Backtest")
    logger.info(f"📊 Symbols: {symbols}")
    logger.info(f"📅 Date Range: {start_date} to {end_date}")
    logger.info(f"🎯 Strategies: {strategies}")
    
    try:
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        # Log results
        logger.info("✅ Data Structure Fix Test Completed Successfully!")
        
        for strategy_name, result in results.items():
            if result:
                logger.info(f"📈 {strategy_name}: {result.total_return_pct:.2f}% return, {result.total_trades} trades")
            else:
                logger.warning(f"⚠️ {strategy_name}: No results (likely no trades generated)")
        
        # Store results
        await engine.store_results(
            results=results,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            database_only=True,
            backtest_name="data_structure_fix_test"
        )
        
        logger.info("💾 Results stored in database")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Data Structure Fix Test Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_test_data_structure_backtest()) 