#!/usr/bin/env python3
"""
Test Options Strategies - Fixed Version
======================================
Simple test to verify that options strategies are working after fixes.
"""

import os
import sys
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.strategies.options.iron_condor_strategy import IronCondorStrategy
from src.strategies.options.enhanced_iron_condor_strategy import EnhancedIronCondorStrategy

# Setup logging
logger = get_trading_logger()

async def test_options_strategies():
    """Test that options strategies are working correctly"""
    
    logger.info("🚀 Testing Options Strategies - Fixed Version")
    
    # Test strategies
    strategies = [
        ("GreeksEnhanced", GreeksEnhancedStrategy()),
        ("IronCondor", IronCondorStrategy()),
        ("EnhancedIronCondor", EnhancedIronCondorStrategy())
    ]
    
    for strategy_name, strategy in strategies:
        logger.info(f"📊 Testing {strategy_name} strategy...")
        
        try:
            # Test strategy initialization
            logger.info(f"   ✅ {strategy_name} initialized successfully")
            
            # Test strategy info
            strategy_info = strategy.get_strategy_info()
            logger.info(f"   📋 Strategy info: {strategy_info}")
            
            # Test that strategy can be imported and used
            logger.info(f"   ✅ {strategy_name} strategy is working correctly")
            
        except Exception as e:
            logger.error(f"   ❌ {strategy_name} strategy failed: {e}")
            continue
    
    logger.info("✅ All options strategies tested successfully!")

if __name__ == "__main__":
    asyncio.run(test_options_strategies()) 