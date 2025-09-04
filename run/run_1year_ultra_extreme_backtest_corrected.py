#!/usr/bin/env python3
"""
1-Year Ultra Extreme Backtest Runner (Corrected Strategy Names)

- Uses all non-LLM strategies with ultra extreme settings
- 1-year period from current date
- Uses centralized options symbols
- Uses exact strategy names from BacktestEngine strategy_map
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the backtest engine
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import get_options_symbols

# Robust logging setup
try:
    from src.utils.enhanced_logging import get_trading_logger
    logger = get_trading_logger()
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("1year_ultra_extreme_backtest")

# All non-LLM strategies using exact names from BacktestEngine strategy_map
ULTRA_EXTREME_STRATEGIES = [
    'SMACrossover',  # from breakout/sma_crossover.py
    'RSI',  # from momentum/rsi_strategy.py
    'MACD',  # from momentum/macd_strategy.py
    'BollingerBands',  # from mean_reversion/bollinger_bands_strategy.py
    'MeanReversion',  # from mean_reversion/mean_reversion_strategy.py
    'Momentum',  # from momentum/momentum_strategy.py
    'VolatilityBreakout',  # from breakout/volatility_breakout_strategy.py
    'TrailingStop',  # from advanced/trailing_stop_strategy.py
    'Fibonacci',  # from advanced/fibonacci_strategy.py
    'GreeksEnhanced',  # from options/greeks_enhanced_strategy.py
    'IronCondor',  # from options/iron_condor_strategy.py
    'EnhancedIronCondor',  # from options/enhanced_iron_condor_strategy.py
    'VWAP',  # from vwap_strategy.py
    'PairsTrading',  # from pairs_trading_strategy.py
    'KalmanFilter',  # from kalman_filter_strategy.py
    'RegimeSwitching',  # from regime_switching_strategy.py
    'CoveredCall',  # from options/covered_call_strategy.py
    'CashSecuredPut',  # from options/cash_secured_put_strategy.py
    'ButterflySpread',  # from options/butterfly_spread_strategy.py
    'CalendarSpread',  # from options/calendar_spread_strategy.py
    'Earnings',  # from options/earnings_strategy.py
    'AdaptiveMomentum',  # from adaptive_momentum_strategy.py
    'EnhancedDayTrading',  # from enhanced_day_trading_strategy.py
    'NewsEnhanced'  # from news_enhanced_strategy.py
]

async def main():
    """Main backtest function for 1-year ultra extreme backtest"""
    try:
        # Calculate 1-year period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Get options symbols
        symbols = get_options_symbols()
        
        logger.info("🚀 Starting 1-Year Ultra Extreme Backtest (Corrected Strategy Names)")
        logger.info(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"💰 Initial Capital: $100,000 (BacktestEngine default)")
        logger.info(f"📊 Symbols: {len(symbols)} options symbols")
        logger.info(f"🎯 Strategies: {len(ULTRA_EXTREME_STRATEGIES)} non-LLM strategies")
        
        # Log all strategies being used
        for i, strategy in enumerate(ULTRA_EXTREME_STRATEGIES, 1):
            logger.info(f"   {i:2d}. {strategy}")

        # Initialize backtest engine with ultra extreme settings
        engine = BacktestEngine(
            use_real_data=True,
            use_cache=True
        )

        # Run backtest
        logger.info("🔄 Running ultra extreme backtest...")
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            strategies=ULTRA_EXTREME_STRATEGIES
        )

        # Log detailed results
        logger.info("📈 Ultra Extreme Backtest Results:")
        if results:
            total_trades = 0
            total_return = 0.0
            successful_strategies = 0
            
            for strategy_name, result in results.items():
                if result and hasattr(result, 'total_trades'):
                    trades = getattr(result, 'total_trades', 0)
                    return_pct = getattr(result, 'total_return_pct', 0.0)
                    total_trades += trades
                    total_return += return_pct
                    successful_strategies += 1
                    
                    logger.info(f"  {strategy_name}: {return_pct:.2f}% return, {trades} trades")
                else:
                    logger.info(f"  {strategy_name}: No result or failed")
            
            logger.info(f"📊 Summary: {successful_strategies} strategies, {total_trades} total trades, {total_return:.2f}% total return")
        else:
            logger.warning("⚠️ No results returned from backtest engine.")

        logger.info("🎉 1-Year Ultra Extreme Backtest completed!")

    except Exception as e:
        logger.error(f"❌ Backtest failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 