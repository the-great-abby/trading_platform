#!/usr/bin/env python3
"""
Comprehensive 2-Year Backtest
Run a comprehensive backtest with multiple strategies over 2 years
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

STRATEGY_SERVICE_URL = "http://localhost:11080/api/backtest/run"

def run_comprehensive_backtest():
    """Run a comprehensive 2-year backtest with multiple strategies"""
    
    logger.info("🚀 COMPREHENSIVE 2-YEAR BACKTEST")
    logger.info("=" * 80)
    
    # Test configuration
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # Top 5 stocks
    start_date = "2023-01-01"
    end_date = "2025-01-01"  # 2 years
    initial_capital = 10000.0  # $10,000 starting capital
    
    # Strategies to test (prioritize working ones)
    strategies = [
        "SimpleTestStrategy",  # Always works
        "RSIStrategy",         # Should work with parameter fixes
        "MACDStrategy",        # Should work with parameter fixes
        "BollingerBandsStrategy",  # Should work with parameter fixes
        "IchimokuStrategy",    # Should work with parameter fixes
        "HybridIchimokuStrategy",  # Should work with parameter fixes
        "CashSecuredPutStrategy",  # Should work with parameter fixes
        "ElliottWaveImpulseStrategy",  # Should work with parameter fixes
        "ElliottWaveCorrectiveStrategy",  # Should work with parameter fixes
        "RegimeSwitchingStrategy",  # Should work with parameter fixes
        "IronCondorStrategy",  # Should work with parameter fixes
        "ButterflyStrategy",   # Should work with parameter fixes
        "CalendarSpreadStrategy"  # Should work with parameter fixes
    ]
    
    logger.info(f"📊 BACKTEST CONFIGURATION:")
    logger.info(f"  Symbols: {symbols}")
    logger.info(f"  Period: {start_date} to {end_date}")
    logger.info(f"  Capital: ${initial_capital:,.2f}")
    logger.info(f"  Strategies: {len(strategies)}")
    logger.info("")
    
    # Run backtest
    payload = {
        "initial_capital": initial_capital,
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols,
        "strategies": strategies,
        "data_source": "real",
        "use_public_com_pricing": True,
        "options_service_available": True,
        "batch_size": 5  # Process 5 symbols at a time
    }
    
    try:
        logger.info("🚀 Starting comprehensive backtest...")
        logger.info("⏳ This may take several minutes...")
        
        response = requests.post(STRATEGY_SERVICE_URL, json=payload, timeout=600)  # 10 minute timeout
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            logger.info("✅ Comprehensive backtest completed successfully!")
            logger.info("")
            
            # Analyze results
            results = result.get("results", [])
            logger.info(f"📊 BACKTEST RESULTS SUMMARY:")
            logger.info(f"  Total Strategies Tested: {len(results)}")
            logger.info("")
            
            working_strategies = []
            non_working_strategies = []
            
            for strategy_result in results:
                strategy_name = strategy_result.get("name", "Unknown")
                total_trades = strategy_result.get("total_trades", 0)
                total_return = strategy_result.get("total_return", 0.0)
                trades = strategy_result.get("trades", [])
                
                if total_trades > 0:
                    working_strategies.append({
                        "name": strategy_name,
                        "trades": total_trades,
                        "return": total_return,
                        "trade_count": len(trades)
                    })
                    logger.info(f"✅ {strategy_name}: {total_trades} trades, {total_return:.2f}% return")
                else:
                    non_working_strategies.append(strategy_name)
                    logger.info(f"❌ {strategy_name}: 0 trades")
            
            logger.info("")
            logger.info(f"📈 WORKING STRATEGIES: {len(working_strategies)}")
            for strategy in working_strategies:
                logger.info(f"   {strategy['name']}: {strategy['trades']} trades, {strategy['return']:.2f}% return")
            
            logger.info("")
            logger.info(f"❌ NON-WORKING STRATEGIES: {len(non_working_strategies)}")
            for strategy in non_working_strategies:
                logger.info(f"   {strategy}: 0 trades")
            
            logger.info("")
            logger.info("🎯 NEXT STEPS:")
            logger.info("-" * 50)
            if working_strategies:
                logger.info("1. ✅ Some strategies are working - use these for production")
                logger.info("2. 🔧 Fix non-working strategies by adjusting parameters")
                logger.info("3. 🚀 Run paper trading with working strategies")
                logger.info("4. 📊 Analyze performance and optimize")
            else:
                logger.info("1. 🔧 All strategies need parameter adjustments")
                logger.info("2. 🔍 Check strategy logic and thresholds")
                logger.info("3. 🚀 Fix strategies before running paper trading")
            
            logger.info("")
            logger.info("🏴‍☠️ COMPREHENSIVE BACKTEST COMPLETE!")
            
        else:
            logger.error(f"❌ Backtest failed: {result.get('message', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    run_comprehensive_backtest()

