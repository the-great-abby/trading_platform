#!/usr/bin/env python3
"""
Test Real Strategies
Test all the real strategies to see which ones are working
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

STRATEGY_SERVICE_URL = "http://localhost:11080/api/backtest/run"

def test_strategy(strategy_name, symbols, start_date, end_date, initial_capital):
    """Test a single strategy"""
    logger.info(f"🎯 TESTING STRATEGY: {strategy_name}")
    logger.info(f"--------------------------------------------------")
    
    payload = {
        "initial_capital": initial_capital,
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols,
        "strategies": [strategy_name],
        "data_source": "real",
        "use_public_com_pricing": True,
        "options_service_available": True
    }
    
    try:
        response = requests.post(STRATEGY_SERVICE_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("results"):
            backtest_result = result["results"][0]
            total_trades = backtest_result.get("total_trades", 0)
            total_return = backtest_result.get("total_return", 0.0)
            trades = backtest_result.get("trades", [])
            
            logger.info(f"✅ {strategy_name} completed successfully!")
            logger.info(f"   Total Trades: {total_trades}")
            logger.info(f"   Total Return: {total_return:.2f}%")
            logger.info(f"   Trades Generated: {len(trades)}")
            
            if trades:
                logger.info(f"   First Trade: {trades[0]['action']} {trades[0]['quantity']} {trades[0]['symbol']} @ ${trades[0]['price']:.2f}")
                logger.info(f"   Strategy: {trades[0]['strategy']}")
                logger.info(f"   Confidence: {trades[0]['confidence']:.2f}")
            
            if total_trades == 0:
                logger.warning(f"⚠️ {strategy_name} NOT generating signals")
                logger.info("   Possible issues:")
                logger.info("     - Strategy parameters too restrictive")
                logger.info("     - Market conditions not met")
                logger.info("     - Technical indicators not calculated")
                logger.info("     - Signal logic needs debugging")
            
            return {
                "strategy": strategy_name,
                "total_trades": total_trades,
                "total_return": total_return,
                "trades": trades,
                "working": total_trades > 0
            }
        else:
            logger.error(f"❌ Backtest failed for {strategy_name}: {result.get('message', 'Unknown error')}")
            return {
                "strategy": strategy_name,
                "total_trades": 0,
                "total_return": 0.0,
                "trades": [],
                "working": False,
                "error": result.get('message', 'Unknown error')
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed for {strategy_name}: {e}")
        return {
            "strategy": strategy_name,
            "total_trades": 0,
            "total_return": 0.0,
            "trades": [],
            "working": False,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error for {strategy_name}: {e}")
        return {
            "strategy": strategy_name,
            "total_trades": 0,
            "total_return": 0.0,
            "trades": [],
            "working": False,
            "error": f"JSON decode error: {e}"
        }

def main():
    logger.info("🔍 TESTING REAL STRATEGIES")
    logger.info("=" * 80)
    
    # Test configuration
    symbols_to_test = ["AAPL"]
    start_date = "2024-01-01"
    end_date = "2024-03-01"  # 2 months for more data
    initial_capital = 4000.0
    
    # Strategies to test
    strategies_to_test = [
        # Simple strategies (should work)
        "RSIStrategy",
        "MACDStrategy", 
        "BollingerBandsStrategy",
        
        # Complex strategies (may need debugging)
        "HybridIchimokuStrategy",
        "IchimokuStrategy",
        "CashSecuredPutStrategy",
        
        # Elliott Wave strategies
        "ElliottWaveImpulseStrategy",
        "ElliottWaveCorrectiveStrategy",
        "SimplifiedElliottWaveImpulseStrategy",
        "SimplifiedElliottWaveCorrectiveStrategy",
        "EnhancedElliottWaveImpulseStrategy",
        "EnhancedElliottWaveCorrectiveStrategy",
        
        # Advanced strategies
        "RegimeSwitchingStrategy",
        "IronCondorStrategy",
        "ButterflyStrategy",
        "CalendarSpreadStrategy",
        
        # Test strategy (should always work)
        "SimpleTestStrategy"
    ]
    
    logger.info(f"📊 TEST CONFIGURATION:")
    logger.info(f"  Symbol: {symbols_to_test}")
    logger.info(f"  Period: {start_date} to {end_date}")
    logger.info(f"  Capital: ${initial_capital:,.2f}")
    logger.info(f"  Strategies to test: {len(strategies_to_test)}")
    logger.info("")
    
    # Test each strategy
    results = []
    working_strategies = []
    non_working_strategies = []
    
    for strategy in strategies_to_test:
        result = test_strategy(strategy, symbols_to_test, start_date, end_date, initial_capital)
        results.append(result)
        
        if result["working"]:
            working_strategies.append(strategy)
        else:
            non_working_strategies.append(strategy)
        
        logger.info("")
    
    # Summary
    logger.info("🔍 STRATEGY TEST SUMMARY:")
    logger.info("=" * 80)
    logger.info(f"✅ Working Strategies: {len(working_strategies)}")
    for strategy in working_strategies:
        result = next(r for r in results if r["strategy"] == strategy)
        logger.info(f"   {strategy}: {result['total_trades']} trades, {result['total_return']:.2f}% return")
    
    logger.info("")
    logger.info(f"❌ Non-Working Strategies: {len(non_working_strategies)}")
    for strategy in non_working_strategies:
        result = next(r for r in results if r["strategy"] == strategy)
        error_msg = result.get("error", "No signals generated")
        logger.info(f"   {strategy}: {error_msg}")
    
    logger.info("")
    logger.info("🎯 NEXT STEPS:")
    logger.info("-" * 50)
    if working_strategies:
        logger.info("1. ✅ Some strategies are working - use these for backtests")
        logger.info("2. 🔧 Debug non-working strategies")
        logger.info("3. 🚀 Run 2-year backtest with working strategies")
    else:
        logger.info("1. 🔧 All strategies need debugging")
        logger.info("2. 🔍 Check strategy parameters and logic")
        logger.info("3. 🚀 Fix strategies before running backtests")
    
    logger.info("")
    logger.info("🏴‍☠️ REAL STRATEGY TEST COMPLETE!")

if __name__ == "__main__":
    main()

