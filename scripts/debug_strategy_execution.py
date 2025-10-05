#!/usr/bin/env python3
"""
Debug Strategy Execution
Test a single strategy with detailed logging to see what's happening
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def debug_strategy_execution():
    """Debug why strategies aren't generating signals"""
    
    logger.info("🔍 DEBUGGING STRATEGY EXECUTION")
    logger.info("=" * 80)
    
    # Test RSI strategy with very simple configuration
    test_config = {
        "symbols": ["AAPL"],
        "start_date": "2023-06-01",  # Shorter period
        "end_date": "2023-08-01",   # 2 months
        "strategies": ["RSI"],
        "initial_capital": 4000.0,
        "use_public_com_pricing": True,
        "batch_size": 1
    }
    
    logger.info("📊 DEBUG CONFIGURATION:")
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
                total_trades = result.get('total_trades', 0)
                total_return = result.get('total_return', 0)
                
                logger.info(f"✅ Backtest completed successfully!")
                logger.info(f"   Total Trades: {total_trades}")
                logger.info(f"   Total Return: {total_return:.2f}%")
                
                # Display detailed results
                if 'strategy_performance' in result:
                    logger.info("📊 Strategy Performance Details:")
                    for strat_name, perf in result['strategy_performance'].items():
                        logger.info(f"   Strategy: {strat_name}")
                        logger.info(f"     Return: {perf.get('total_return', 0):.2f}%")
                        logger.info(f"     Trades: {perf.get('total_trades', 0)}")
                        logger.info(f"     Win Rate: {perf.get('win_rate', 0):.1f}%")
                        logger.info(f"     Sharpe: {perf.get('sharpe_ratio', 0):.3f}")
                
                # Display trade details if any
                if 'trades' in result and result['trades']:
                    logger.info("📈 Trade Details:")
                    for i, trade in enumerate(result['trades'][:5]):  # Show first 5 trades
                        logger.info(f"   Trade {i+1}: {trade.get('action')} {trade.get('symbol')} at ${trade.get('price', 0):.2f}")
                
                if total_trades == 0:
                    logger.warning("⚠️ NO TRADES GENERATED!")
                    logger.info("🔍 Possible issues:")
                    logger.info("   1. Strategy parameters too restrictive")
                    logger.info("   2. Market conditions not met")
                    logger.info("   3. Technical indicators not calculated properly")
                    logger.info("   4. Signal generation logic has bugs")
                    logger.info("   5. Data quality issues")
                    
                    # Check if we have market data
                    logger.info("\n📊 Data Analysis:")
                    logger.info("   - Check strategy service logs for detailed execution")
                    logger.info("   - Verify technical indicators are calculated")
                    logger.info("   - Check if RSI values are in expected ranges")
                    logger.info("   - Verify signal thresholds are reasonable")
                else:
                    logger.info(f"🎉 SUCCESS! Generated {total_trades} trades!")
                    
            else:
                logger.error(f"❌ Backtest failed: {result.get('message', 'Unknown error')}")
                
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    
    logger.info("\n🔍 DEBUGGING SUMMARY:")
    logger.info("-" * 50)
    logger.info("Check the logs above to identify the specific issue")
    logger.info("Next step: Examine strategy service logs for detailed execution info")
    
    logger.info("\n🏴‍☠️ STRATEGY EXECUTION DEBUG COMPLETE!")

if __name__ == "__main__":
    asyncio.run(debug_strategy_execution())

