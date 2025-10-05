#!/usr/bin/env python3
"""
Debug Core Strategy Signal Generation
Test Elliott Wave, Ichimoku, and Cash Secured Put strategies individually
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def debug_core_strategy_signals():
    """Debug why core strategies aren't generating signals"""
    
    logger.info("🔍 DEBUGGING CORE STRATEGY SIGNAL GENERATION")
    logger.info("=" * 80)
    
    # Test each strategy individually with debug configuration
    strategies_to_test = [
        "HybridIchimokuStrategy",
        "CashSecuredPutStrategy", 
        "ElliottWaveImpulseStrategy",
        "ElliottWaveCorrectiveStrategy"
    ]
    
    test_config = {
        "symbols": ["AAPL"],  # Single symbol for focused testing
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",  # Short period for faster testing
        "initial_capital": 4000.0,
        "use_public_com_pricing": True,
        "batch_size": 1
    }
    
    logger.info("📊 DEBUG CONFIGURATION:")
    logger.info(f"  Symbol: {test_config['symbols']}")
    logger.info(f"  Period: {test_config['start_date']} to {test_config['end_date']}")
    logger.info(f"  Capital: ${test_config['initial_capital']:,.2f}")
    logger.info(f"  Strategies to test: {strategies_to_test}")
    
    for strategy in strategies_to_test:
        logger.info(f"\n🎯 TESTING STRATEGY: {strategy}")
        logger.info("-" * 50)
        
        # Prepare backtest request for single strategy
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
                timeout=120  # 2 minutes timeout
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
                        
                        # Display strategy performance
                        if 'strategy_performance' in result:
                            for strat_name, perf in result['strategy_performance'].items():
                                logger.info(f"   Strategy Performance:")
                                logger.info(f"     Return: {perf.get('total_return', 0):.2f}%")
                                logger.info(f"     Trades: {perf.get('total_trades', 0)}")
                                logger.info(f"     Win Rate: {perf.get('win_rate', 0):.1f}%")
                    else:
                        logger.warning(f"⚠️ {strategy} NOT generating signals")
                        logger.info("   Possible issues:")
                        logger.info("     - Strategy parameters too restrictive")
                        logger.info("     - Market conditions not met")
                        logger.info("     - Technical indicators not calculated")
                        logger.info("     - Signal logic needs debugging")
                else:
                    logger.error(f"❌ {strategy} failed: {result.get('message', 'Unknown error')}")
                    
            else:
                logger.error(f"❌ HTTP Error for {strategy}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {strategy} timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error for {strategy}")
        except Exception as e:
            logger.error(f"❌ Unexpected error for {strategy}: {e}")
    
    logger.info("\n🔍 DEBUGGING SUMMARY:")
    logger.info("-" * 50)
    logger.info("Strategies tested individually to identify signal generation issues")
    logger.info("Check logs above for specific problems with each strategy")
    
    logger.info("\n🎯 NEXT STEPS:")
    logger.info("-" * 50)
    logger.info("1. Identify which strategies are generating signals")
    logger.info("2. Debug strategies that aren't generating signals")
    logger.info("3. Relax parameters for non-working strategies")
    logger.info("4. Test with simpler strategies (RSI, MACD, Bollinger)")
    logger.info("5. Run comprehensive 2-year backtest")
    
    logger.info("\n🏴‍☠️ CORE STRATEGY DEBUG COMPLETE!")

if __name__ == "__main__":
    asyncio.run(debug_core_strategy_signals())

