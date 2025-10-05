#!/usr/bin/env python3
"""
Test Simple Strategies First
Test RSI, MACD, Bollinger Bands to verify basic signal generation works
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_simple_strategies():
    """Test simple strategies to verify basic signal generation works"""
    
    logger.info("🔍 TESTING SIMPLE STRATEGIES FIRST")
    logger.info("=" * 80)
    
    # Test simple strategies that should work
    simple_strategies = [
        "RSI",
        "MACD", 
        "BollingerBands"
    ]
    
    test_config = {
        "symbols": ["AAPL"],
        "start_date": "2023-01-01",  # Longer period for more data
        "end_date": "2023-12-31",   # Full year
        "initial_capital": 4000.0,
        "use_public_com_pricing": True,
        "batch_size": 1
    }
    
    logger.info("📊 SIMPLE STRATEGY TEST CONFIGURATION:")
    logger.info(f"  Symbol: {test_config['symbols']}")
    logger.info(f"  Period: {test_config['start_date']} to {test_config['end_date']}")
    logger.info(f"  Capital: ${test_config['initial_capital']:,.2f}")
    logger.info(f"  Strategies: {simple_strategies}")
    
    for strategy in simple_strategies:
        logger.info(f"\n🎯 TESTING SIMPLE STRATEGY: {strategy}")
        logger.info("-" * 50)
        
        # Prepare backtest request
        backtest_request = {
            "symbols": test_config["symbols"],
            "start_date": test_config["start_date"],
            "end_date": test_config["end_date"],
            "strategies": [strategy],
            "initial_capital": test_config["initial_capital"],
            "use_public_com_pricing": test_config["use_public_com_pricing"],
            "batch_size": test_config["batch_size"]
        }
        
        try:
            # Make request to strategy service
            response = requests.post(
                "http://localhost:11080/api/backtest/run",
                json=backtest_request,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    total_trades = result.get('total_trades', 0)
                    total_return = result.get('total_return', 0)
                    
                    logger.info(f"✅ {strategy} completed successfully!")
                    logger.info(f"   Total Trades: {total_trades}")
                    logger.info(f"   Total Return: {total_return:.2f}%")
                    
                    if total_trades > 0:
                        logger.info(f"🎉 {strategy} IS GENERATING SIGNALS!")
                        
                        # Display detailed results
                        if 'strategy_performance' in result:
                            for strat_name, perf in result['strategy_performance'].items():
                                logger.info(f"   Detailed Performance:")
                                logger.info(f"     Return: {perf.get('total_return', 0):.2f}%")
                                logger.info(f"     Trades: {perf.get('total_trades', 0)}")
                                logger.info(f"     Win Rate: {perf.get('win_rate', 0):.1f}%")
                                logger.info(f"     Sharpe: {perf.get('sharpe_ratio', 0):.3f}")
                    else:
                        logger.warning(f"⚠️ {strategy} NOT generating signals")
                        logger.info("   This suggests a fundamental issue with:")
                        logger.info("     - Market data availability")
                        logger.info("     - Technical indicator calculation")
                        logger.info("     - Signal generation logic")
                else:
                    logger.error(f"❌ {strategy} failed: {result.get('message', 'Unknown error')}")
                    
            else:
                logger.error(f"❌ HTTP Error for {strategy}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing {strategy}: {e}")
    
    logger.info("\n🔍 SIMPLE STRATEGY TEST SUMMARY:")
    logger.info("-" * 50)
    logger.info("If simple strategies work, the issue is with complex strategies")
    logger.info("If simple strategies don't work, the issue is fundamental")
    
    logger.info("\n🎯 NEXT STEPS:")
    logger.info("-" * 50)
    logger.info("1. If simple strategies work: Fix complex strategy parameters")
    logger.info("2. If simple strategies don't work: Fix market data/indicators")
    logger.info("3. Test with longer time periods for more data")
    logger.info("4. Check API keys and data availability")
    
    logger.info("\n🏴‍☠️ SIMPLE STRATEGY TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_simple_strategies())

