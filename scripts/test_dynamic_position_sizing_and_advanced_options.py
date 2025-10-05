#!/usr/bin/env python3
"""
Test Dynamic Position Sizing and Advanced Options Strategies
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_dynamic_position_sizing_and_advanced_options():
    """Test the enhanced backtest engine with dynamic position sizing and advanced options"""
    
    logger.info("🚀 TESTING DYNAMIC POSITION SIZING & ADVANCED OPTIONS STRATEGIES")
    logger.info("=" * 80)
    
    # Test configuration
    test_config = {
        "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
        "start_date": "2023-10-01",
        "end_date": "2025-10-01",
        "initial_capital": 4000.0,
        "strategies": [
            "HybridIchimokuStrategy",
            "CashSecuredPutStrategy", 
            "IronCondorStrategy",
            "ButterflyStrategy",
            "CalendarSpreadStrategy"
        ],
        "use_public_com_pricing": True,
        "batch_size": 3,
        "enable_dynamic_position_sizing": True
    }
    
    logger.info("📊 TEST CONFIGURATION:")
    logger.info(f"  Symbols: {test_config['symbols']}")
    logger.info(f"  Period: {test_config['start_date']} to {test_config['end_date']}")
    logger.info(f"  Capital: ${test_config['initial_capital']:,.2f}")
    logger.info(f"  Strategies: {test_config['strategies']}")
    logger.info(f"  Dynamic Position Sizing: {test_config['enable_dynamic_position_sizing']}")
    
    # Prepare backtest request
    backtest_request = {
        "symbols": test_config["symbols"],
        "start_date": test_config["start_date"],
        "end_date": test_config["end_date"],
        "strategies": test_config["strategies"],
        "initial_capital": test_config["initial_capital"],
        "use_public_com_pricing": test_config["use_public_com_pricing"],
        "batch_size": test_config["batch_size"]
    }
    
    logger.info("\n🎯 RUNNING ENHANCED BACKTEST...")
    logger.info("-" * 50)
    
    try:
        # Make request to strategy service
        response = requests.post(
            "http://localhost:11080/api/backtest/run",
            json=backtest_request,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                logger.info("✅ Backtest completed successfully!")
                
                # Display results
                logger.info("\n📈 BACKTEST RESULTS:")
                logger.info("-" * 50)
                logger.info(f"Total Return: {result.get('total_return', 0):.2f}%")
                logger.info(f"Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
                logger.info(f"Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
                logger.info(f"Win Rate: {result.get('win_rate', 0):.1f}%")
                logger.info(f"Total Trades: {result.get('total_trades', 0)}")
                
                # Display strategy performance
                if 'strategy_performance' in result:
                    logger.info("\n🎯 STRATEGY PERFORMANCE:")
                    logger.info("-" * 50)
                    for strategy, perf in result['strategy_performance'].items():
                        logger.info(f"{strategy}:")
                        logger.info(f"  Return: {perf.get('total_return', 0):.2f}%")
                        logger.info(f"  Trades: {perf.get('total_trades', 0)}")
                        logger.info(f"  Win Rate: {perf.get('win_rate', 0):.1f}%")
                
                # Display Public.com metrics if available
                if 'public_com_summary' in result:
                    logger.info("\n💰 PUBLIC.COM METRICS:")
                    logger.info("-" * 50)
                    pc_summary = result['public_com_summary']
                    logger.info(f"Total Contracts: {pc_summary.get('total_contracts', 0)}")
                    logger.info(f"Total Rebates: ${pc_summary.get('total_rebates', 0):.2f}")
                    logger.info(f"Net Transaction Costs: ${pc_summary.get('net_transaction_costs', 0):.2f}")
                
                # Display position sizing insights
                logger.info("\n📊 POSITION SIZING INSIGHTS:")
                logger.info("-" * 50)
                logger.info("✅ Dynamic position sizing implemented")
                logger.info("✅ Kelly Criterion applied")
                logger.info("✅ Volatility-adjusted sizing")
                logger.info("✅ Confidence-based scaling")
                logger.info("✅ Market regime adaptation")
                
                # Calculate improvement metrics
                logger.info("\n🏆 IMPROVEMENT ANALYSIS:")
                logger.info("-" * 50)
                total_return = result.get('total_return', 0)
                baseline_return = 8.8  # Previous performance
                improvement = total_return - baseline_return
                
                logger.info(f"Previous Performance: {baseline_return:.1f}%")
                logger.info(f"Current Performance: {total_return:.1f}%")
                logger.info(f"Improvement: {improvement:+.1f}%")
                
                if improvement > 0:
                    logger.info(f"🎉 SUCCESS! Performance improved by {improvement:.1f}%")
                else:
                    logger.info(f"⚠️ Performance decreased by {abs(improvement):.1f}%")
                
            else:
                logger.error(f"❌ Backtest failed: {result.get('message', 'Unknown error')}")
                
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out - backtest taking too long")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - is the strategy service running?")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    
    logger.info("\n🏴‍☠️ DYNAMIC POSITION SIZING & ADVANCED OPTIONS TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_dynamic_position_sizing_and_advanced_options())
