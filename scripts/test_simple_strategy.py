#!/usr/bin/env python3
"""
Test Simple Strategy
Test the SimpleTestStrategy to verify the backtest engine works
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_simple_strategy():
    """Test the SimpleTestStrategy to verify the backtest engine works"""
    
    logger.info("🔍 TESTING SIMPLE STRATEGY")
    logger.info("=" * 80)
    
    # Test simple strategy that should always generate signals
    test_config = {
        "symbols": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",  # Short period for quick test
        "strategies": ["SimpleTestStrategy"],
        "initial_capital": 4000.0,
        "use_public_com_pricing": True,
        "batch_size": 1
    }
    
    logger.info("📊 SIMPLE STRATEGY TEST CONFIGURATION:")
    logger.info(f"  Symbol: {test_config['symbols']}")
    logger.info(f"  Period: {test_config['start_date']} to {test_config['end_date']}")
    logger.info(f"  Strategy: {test_config['strategies']}")
    logger.info(f"  Capital: ${test_config['initial_capital']:,.2f}")
    
    try:
        # Make request to strategy service
        logger.info("🚀 Making request to strategy service...")
        response = requests.post(
            "http://localhost:11080/api/backtest/run",
            json=test_config,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                # Get the first result from the results array
                if result.get("results") and len(result["results"]) > 0:
                    backtest_result = result["results"][0]
                    total_trades = backtest_result.get('total_trades', 0)
                    total_return = backtest_result.get('total_return', 0)
                    trades = backtest_result.get('trades', [])
                    
                    logger.info(f"✅ Backtest completed successfully!")
                    logger.info(f"   Total Trades: {total_trades}")
                    logger.info(f"   Total Return: {total_return:.2f}%")
                    logger.info(f"   Trades Generated: {len(trades)}")
                    
                    if trades:
                        logger.info(f"   First Trade: {trades[0]['action']} {trades[0]['quantity']} {trades[0]['symbol']} @ ${trades[0]['price']:.2f}")
                    
                    if total_trades > 0:
                        logger.info(f"🎉 SUCCESS! SimpleTestStrategy generated {total_trades} trades!")
                        logger.info("✅ This confirms the backtest engine is working correctly")
                        
                        # Display trade details
                        logger.info("📈 Trade Details:")
                        for i, trade in enumerate(trades[:5]):  # Show first 5 trades
                            logger.info(f"   Trade {i+1}: {trade.get('action')} {trade.get('quantity')} {trade.get('symbol')} @ ${trade.get('price', 0):.2f}")
                        
                        logger.info("\n🎯 NEXT STEPS:")
                        logger.info("-" * 50)
                        logger.info("1. ✅ Backtest engine is working")
                        logger.info("2. 🔧 Test real strategies (RSI, MACD, Bollinger Bands)")
                        logger.info("3. 🚀 Run 2-year backtest with working strategies")
                        
                    else:
                        logger.error(f"❌ FAILURE! SimpleTestStrategy generated 0 trades")
                        logger.error("This indicates a fundamental issue with the backtest engine")
                else:
                    logger.error("❌ No results returned from backtest")
                    
            else:
                logger.error(f"❌ Backtest failed: {result.get('message', 'Unknown error')}")
                
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    
    logger.info("\n🏴‍☠️ SIMPLE STRATEGY TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_simple_strategy())
