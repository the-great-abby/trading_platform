#!/usr/bin/env python3
"""
Centralized Config Backtest Runner (Consolidated)

- Uses only implemented, compatible strategies (no LLM/AI/ML/experimental)
- Robust logging: falls back to standard logging if enhanced logging is unavailable
- Uses centralized config and symbol list
- Handles options data and errors gracefully
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.backtest_config import (
    BacktestConfig, BacktestMode, RiskProfile,
    get_backtest_config, load_config_from_env
)
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import get_options_symbols

# Robust logging setup
try:
    from src.utils.enhanced_logging import get_trading_logger
    logger = get_trading_logger()
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("centralized_backtest")

# Only use strategies that are implemented and compatible
WORKING_STRATEGIES = [
    'SMACrossoverStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerBandsStrategy',
    'MeanReversionStrategy',
    'MomentumStrategy',
    'VolatilityBreakoutStrategy',
    'TrailingStopStrategy',
    'FibonacciStrategy',
    'GreeksEnhancedStrategy',
    'IronCondorStrategy',
    'EnhancedIronCondorStrategy',
    'VWAPStrategy',
    'PairsTradingStrategy',
    'KalmanFilterStrategy',
    'RegimeSwitchingStrategy',
    'CoveredCallStrategy',
    'CashSecuredPutStrategy',
    'ButterflySpreadStrategy',
    'CalendarSpreadStrategy',
    'EarningsStrategy',
    # Add more only if confirmed working
]

async def main():
    """Main backtest function (consolidated)"""
    try:
        # Load configuration from environment variables
        config = load_config_from_env()
        # Override with ultra-aggressive settings for this run
        config.initial_capital = 1000.0
        config.risk_profile = RiskProfile.ULTRA_AGGRESSIVE
        config.symbols = get_options_symbols()  # Use options symbols
        config.start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        config.end_date = datetime.now().strftime("%Y-%m-%d")
        config.use_llm = False

        logger.info("🚀 Starting Centralized Config Backtest (Consolidated)")
        logger.info(f"📊 Configuration: {config}")
        logger.info(f"🎯 Using {len(WORKING_STRATEGIES)} strategies:")
        for s in WORKING_STRATEGIES:
            logger.info(f"   - {s}")

        # Initialize backtest engine
        engine = BacktestEngine(
            use_real_data=True,
            use_cache=True
        )

        # Run backtest
        logger.info("🔄 Running backtest...")
        results = await engine.run_backtest(
            symbols=config.symbols,
            start_date=config.start_date,
            end_date=config.end_date,
            strategies=WORKING_STRATEGIES
        )

        # Log results
        logger.info("📈 Backtest Results:")
        if results:
            for strategy_name, result in results.items():
                if result:
                    logger.info(f"  {strategy_name}: {getattr(result, 'total_return_pct', 0):.2f}% return, {getattr(result, 'total_trades', 0)} trades")
                else:
                    logger.info(f"  {strategy_name}: No result (strategy not found or failed)")
        else:
            logger.warning("⚠️ No results returned from backtest engine.")

        logger.info("🎉 Centralized Config Backtest completed!")

    except Exception as e:
        logger.error(f"❌ Backtest failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 