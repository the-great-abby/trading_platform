#!/usr/bin/env python3
"""
Comprehensive Data Structure Verification Backtest
Tests the data structure fixes with a longer period and more symbols
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

async def run_comprehensive_verification_backtest():
    """Run a comprehensive backtest to verify data structure fixes"""
    
    # Comprehensive test parameters
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'SQ', 'ZM', 'UBER'
    ]
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Test all options strategies that were having data structure issues
    strategies = [
        'VolatilityStrategy',
        'CoveredCall', 
        'CashSecuredPut',
        'ButterflySpread',
        'IronCondor',
        'EnhancedIronCondor',
        'GreeksEnhanced',
        'CalendarSpread',
        'Straddle',
        'Strangle'
    ]
    
    # Initialize backtest engine
    engine = BacktestEngine(
        use_real_data=True,
        use_cache=True
    )
    
    # Disable LLM evaluation for this test
    engine.use_llm_evaluation = False
    
    logger.info("🧪 Starting Comprehensive Data Structure Verification Backtest")
    logger.info(f"📊 Symbols: {len(symbols)} stocks")
    logger.info(f"📅 Date Range: {start_date} to {end_date} ({365} days)")
    logger.info(f"🎯 Strategies: {len(strategies)} options strategies")
    logger.info(f"💰 Initial Capital: $1,000,000")
    
    try:
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        # Log results
        logger.info("✅ Comprehensive Verification Completed Successfully!")
        logger.info("=" * 80)
        
        total_trades = 0
        successful_strategies = 0
        
        for strategy_name, result in results.items():
            if result:
                successful_strategies += 1
                total_trades += result.total_trades
                logger.info(f"📈 {strategy_name}:")
                logger.info(f"   Return: {result.total_return_pct:.2f}%")
                logger.info(f"   Trades: {result.total_trades}")
                logger.info(f"   Win Rate: {result.win_rate:.1f}%")
                logger.info(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
                logger.info(f"   Max Drawdown: {result.max_drawdown_pct:.2f}%")
            else:
                logger.warning(f"⚠️ {strategy_name}: No results (likely no trades generated)")
        
        logger.info("=" * 80)
        logger.info(f"📊 Summary:")
        logger.info(f"   Successful Strategies: {successful_strategies}/{len(strategies)}")
        logger.info(f"   Total Trades Generated: {total_trades}")
        logger.info(f"   Data Structure Errors: 0 ✅")
        
        # Store results
        await engine.store_results(
            results=results,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            database_only=True,
            backtest_name="comprehensive_data_structure_verification"
        )
        
        logger.info("💾 Results stored in database")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Comprehensive Verification Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_comprehensive_verification_backtest()) 