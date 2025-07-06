"""
Tests for trading strategies
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy


@pytest.fixture
def sample_data():
    """Create sample market data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Open': [100 + i * 0.1 for i in range(100)],
        'High': [101 + i * 0.1 for i in range(100)],
        'Low': [99 + i * 0.1 for i in range(100)],
        'Close': [100.5 + i * 0.1 for i in range(100)],
        'Volume': [1000000 for _ in range(100)]
    }, index=dates)
    
    # Add technical indicators
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['RSI'] = 50 + (data['Close'] - data['Close'].rolling(14).mean()) / data['Close'].rolling(14).std() * 10
    
    return data


@pytest.mark.asyncio
async def test_sma_crossover_strategy(sample_data):
    """Test SMA crossover strategy"""
    strategy = SMACrossoverStrategy(short_window=20, long_window=50)
    
    # Test with sample data
    signal = await strategy.generate_signal("AAPL", sample_data)
    
    # Should return either a signal or None
    assert signal is None or hasattr(signal, 'action')


@pytest.mark.asyncio
async def test_rsi_strategy(sample_data):
    """Test RSI strategy"""
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    
    # Test with sample data
    signal = await strategy.generate_signal("MSFT", sample_data)
    
    # Should return either a signal or None
    assert signal is None or hasattr(signal, 'action')


def test_strategy_configuration():
    """Test strategy configuration"""
    sma_strategy = SMACrossoverStrategy(short_window=10, long_window=30)
    assert sma_strategy.short_window == 10
    assert sma_strategy.long_window == 30
    
    rsi_strategy = RSIStrategy(period=21, oversold=25, overbought=75)
    assert rsi_strategy.period == 21
    assert rsi_strategy.oversold == 25
    assert rsi_strategy.overbought == 75 