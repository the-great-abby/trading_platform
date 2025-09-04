#!/usr/bin/env python3
"""
Test script for automatic index creation
"""

import asyncio
import logging
from src.utils.database_optimizer import DatabaseOptimizer
from src.services.database.market_data_service import MarketDataDatabaseService
from src.services.database.backtest_results_service import BacktestResultsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_index_creation():
    """Test automatic index creation"""
    logger.info("🧪 Testing automatic index creation...")
    
    # Use localhost for local testing
    database_url = "postgresql://trading_user:trading_pass@localhost:5432/trading_bot"
    
    # Test DatabaseOptimizer directly
    try:
        optimizer = DatabaseOptimizer(database_url)
        await optimizer.ensure_indexes()
        logger.info("✅ DatabaseOptimizer index creation test passed")
    except Exception as e:
        logger.error(f"❌ DatabaseOptimizer test failed: {e}")
    
    # Test MarketDataDatabaseService initialization
    try:
        market_data_service = MarketDataDatabaseService(database_url)
        logger.info("✅ MarketDataDatabaseService initialization test passed")
    except Exception as e:
        logger.error(f"❌ MarketDataDatabaseService test failed: {e}")
    
    # Test BacktestResultsService initialization
    try:
        backtest_service = BacktestResultsService(database_url)
        logger.info("✅ BacktestResultsService initialization test passed")
    except Exception as e:
        logger.error(f"❌ BacktestResultsService test failed: {e}")
    
    logger.info("🎉 Index creation tests completed!")

if __name__ == "__main__":
    asyncio.run(test_index_creation()) 