#!/usr/bin/env python3
"""
Debug script to test strategy signal generation
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.utils.enhanced_logging import get_trading_logger

# Configure logging
logger = get_trading_logger()

async def test_strategy_signals():
    """Test if strategies can generate signals with sample data"""
    
    # Create sample data with 120 days to ensure enough data for indicators
    dates = pd.date_range(start='2024-09-01', end='2024-12-31', freq='D')
    sample_data = pd.DataFrame({
        'Close': [100 + i * 0.5 + (i % 7 - 3) * 3 for i in range(len(dates))],  # More volatile pattern
        'Open': [100 + i * 0.5 for i in range(len(dates))],
        'High': [102 + i * 0.5 for i in range(len(dates))],
        'Low': [98 + i * 0.5 for i in range(len(dates))],
        'Volume': [1000000 + i * 10000 for i in range(len(dates))]
    }, index=dates)
    
    logger.info(f"📊 Sample data shape: {sample_data.shape}")
    logger.info(f"📊 Sample data columns: {list(sample_data.columns)}")
    logger.info(f"📊 Sample data head:\n{sample_data.head()}")
    logger.info(f"📊 Sample data tail:\n{sample_data.tail()}")
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=False, use_cache=False)
    
    # Add technical indicators
    data_with_indicators = engine._add_technical_indicators(sample_data)
    logger.info(f"📊 Data with indicators shape: {data_with_indicators.shape}")
    logger.info(f"📊 Data with indicators columns: {list(data_with_indicators.columns)}")
    logger.info(f"📊 Data with indicators head:\n{data_with_indicators.head()}")
    logger.info(f"📊 Data with indicators tail:\n{data_with_indicators.tail()}")
    
    if data_with_indicators.empty:
        logger.error("❌ Data is empty after adding indicators! This is the root cause of no signals.")
        return
    
    # Test Bollinger Bands strategy
    strategy = BollingerBandsStrategy()
    logger.info(f"🔍 Testing {strategy.name}")
    
    signals_generated = 0
    for i in range(50, len(data_with_indicators)):  # Start from 50 to have enough data
        current_data = data_with_indicators.iloc[:i+1]
        current_date = data_with_indicators.index[i]
        historical_date = current_date.strftime("%Y-%m-%d")
        
        logger.info(f"🔍 Testing signal generation for {historical_date} with {len(current_data)} data points")
        logger.info(f"🔍 Current price: {current_data['Close'].iloc[-1]:.2f}")
        logger.info(f"🔍 Current RSI: {current_data['RSI'].iloc[-1]:.2f}")
        logger.info(f"🔍 Current BB Upper: {current_data['BB_Upper'].iloc[-1]:.2f}")
        logger.info(f"🔍 Current BB Lower: {current_data['BB_Lower'].iloc[-1]:.2f}")
        
        signal = await strategy.generate_signal("AAPL", current_data, historical_date)
        
        if signal:
            signals_generated += 1
            logger.info(f"✅ Signal {signals_generated}: {signal.action} at {historical_date}")
            logger.info(f"✅ Signal details: {signal}")
        else:
            logger.info(f"❌ No signal for {historical_date}")
    
    logger.info(f"📊 Total signals generated: {signals_generated}")

if __name__ == "__main__":
    asyncio.run(test_strategy_signals()) 