#!/usr/bin/env python3
"""
Direct AdaptiveSectorWaveStrategy Backtest
Uses the AdaptiveSectorWaveStrategy with integrated Elliott Wave + Ichimoku
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set Polygon API key from Kubernetes secret
os.environ['POLYGON_API_KEY'] = POLYGON_API_KEY

# Set required database URL for market data manager
os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
os.environ['DATABASE_ONLY'] = 'false'  # Allow API fallback

# Disable AI services for faster backtesting
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'
os.environ['DISABLE_LLM_STRATEGIES'] = 'true'
os.environ['DISABLE_AI_STRATEGIES'] = 'true'
os.environ['ENABLE_LLM_EVALUATION'] = 'false'  # Disable LLM trade evaluation

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_adaptive_sector_wave_backtest():
    """Run backtest with AdaptiveSectorWaveStrategy (Elliott Wave + Ichimoku integrated)"""
    
    logger.info("🚀 Starting AdaptiveSectorWaveStrategy Backtest")
    logger.info("=" * 60)
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    engine.initial_capital = 4000.0  # $4,000 account
    
    # Initialize AdaptiveSectorWaveStrategy with integrated Elliott Wave + Ichimoku
    strategy = AdaptiveSectorWaveStrategy(
        sector_rotation_threshold=0.15,
        volatility_threshold=0.25,
        elliott_wave_min_confidence=0.05,  # Lowered to allow trades
        ichimoku_min_confidence=0.05,     # Lowered to allow trades
        lookback_period=50
    )
    
    # Define symbols to test (expanded set)
    symbols = ['SPY', 'QQQ', 'AAPL', 'AMD', 'INTC', 'PYPL', 'NFLX', 'NVDA', 'META', 'GOOG']
    
    # Date range for backtest (2024 for better options data coverage)
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info(f"📊 Strategy: {strategy.name}")
    logger.info(f"💰 Initial Capital: ${engine.initial_capital:,.2f}")
    logger.info(f"📈 Symbols: {', '.join(symbols)}")
    logger.info(f"📅 Date Range: {start_date} to {end_date}")
    logger.info(f"🎯 Elliott Wave Min Confidence: {strategy.elliott_wave_min_confidence}")
    logger.info(f"📊 Ichimoku Min Confidence: {strategy.ichimoku_min_confidence}")
    logger.info("=" * 60)
    
    try:
        # Run backtest
        start_time = datetime.now()
        results = await engine.run_backtest(
            strategies={'AdaptiveSectorWaveStrategy': strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Display results
        if results and 'AdaptiveSectorWaveStrategy' in results:
            result = results['AdaptiveSectorWaveStrategy']
            
            logger.info("=" * 60)
            logger.info("🎉 ADAPTIVE SECTOR WAVE BACKTEST COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📊 STRATEGY: {result.strategy}")
            logger.info(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
            logger.info(f"💰 Final Capital: ${result.final_capital:,.2f}")
            logger.info(f"📈 Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
            logger.info(f"📊 Total Trades: {result.total_trades}")
            logger.info(f"🎯 Win Rate: {result.win_rate:.2%}")
            logger.info(f"📈 Profit Factor: {result.profit_factor:.3f}")
            logger.info(f"📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info(f"⏱️ Execution Time: {execution_time:.1f} seconds")
            
            # Show trade details if we have trades
            if result.trades:
                logger.info("\n📋 TRADE DETAILS:")
                for i, trade in enumerate(result.trades[:10], 1):  # Show first 10 trades
                    logger.info(f"  {i}. {trade.symbol} {trade.action} {trade.quantity:.2f} @ ${trade.price:.2f} "
                              f"(Return: ${trade.pnl:.2f})")
                if len(result.trades) > 10:
                    logger.info(f"  ... and {len(result.trades) - 10} more trades")
            else:
                logger.info("\n⚠️ No trades generated - check confidence thresholds and symbol qualification")
                
        else:
            logger.error("❌ No results found")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_adaptive_sector_wave_backtest())
