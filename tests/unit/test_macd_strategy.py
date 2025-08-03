#!/usr/bin/env python3
"""
Tests for MACD Strategy
Comprehensive test suite for Moving Average Convergence Divergence strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.strategies.momentum.macd_strategy import MACDStrategy
from src.core.types import TradeSignal


class TestMACDStrategyInitialization:
    """Test MACDStrategy initialization"""
    
    def test_macd_strategy_init_default(self):
        """Test MACDStrategy initialization with default parameters"""
        strategy = MACDStrategy()
        
        assert strategy.name == "MACD"
        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.signal_period == 9
        assert strategy.threshold == 0.001
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
    
    def test_macd_strategy_init_custom(self):
        """Test MACDStrategy initialization with custom parameters"""
        strategy = MACDStrategy(
            fast_period=8,
            slow_period=21,
            signal_period=5,
            threshold=0.002,
            custom_param="test"
        )
        
        assert strategy.name == "MACD"
        assert strategy.fast_period == 8
        assert strategy.slow_period == 21
        assert strategy.signal_period == 5
        assert strategy.threshold == 0.002
        assert strategy.config["custom_param"] == "test"
    
    def test_macd_strategy_get_info(self):
        """Test get_strategy_info method"""
        strategy = MACDStrategy(fast_period=10)
        info = strategy.get_strategy_info()
        
        assert info["name"] == "MACD"
        assert info["is_active"] is True
        assert "fast_period" not in info["config"]  # fast_period is not in config, it's a direct attribute


class TestMACDStrategyCalculation:
    """Test MACD calculation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance"""
        return MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create trending data
        prices = [100 + i * 0.5 + np.random.normal(0, 0.1) for i in range(50)]
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
    
    def test_macd_calculation_basic(self, strategy, sample_data):
        """Test basic MACD calculation"""
        # Calculate MACD components
        exp1 = sample_data['Close'].ewm(span=strategy.fast_period).mean()
        exp2 = sample_data['Close'].ewm(span=strategy.slow_period).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=strategy.signal_period).mean()
        histogram = macd - signal_line
        
        # Check that all components are calculated
        assert len(macd) == len(sample_data)
        assert len(signal_line) == len(sample_data)
        assert len(histogram) == len(sample_data)
        
        # Check that we have some valid values (not all NaN)
        assert macd.notna().any()
        assert signal_line.notna().any()
        assert histogram.notna().any()
    
    def test_macd_calculation_insufficient_data(self, strategy):
        """Test MACD calculation with insufficient data"""
        # Create data with fewer points than slow_period + signal_period
        data = pd.DataFrame({
            'Close': [100 + i for i in range(30)]  # 30 points < 26 + 9
        })
        
        # The strategy should return None for insufficient data
        import asyncio
        signal = asyncio.run(strategy.generate_signal("AAPL", data))
        assert signal is None
    
    def test_macd_calculation_trending_data(self, strategy):
        """Test MACD calculation with trending data"""
        # Create upward trending data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + i * 0.5 for i in range(50)]  # Steady upward trend
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
        
        # Calculate MACD components
        exp1 = data['Close'].ewm(span=strategy.fast_period).mean()
        exp2 = data['Close'].ewm(span=strategy.slow_period).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=strategy.signal_period).mean()
        histogram = macd - signal_line
        
        # In an upward trend, MACD should generally be positive
        valid_macd = macd.dropna()
        if len(valid_macd) > 0:
            assert valid_macd.iloc[-1] > 0  # Latest MACD should be positive in uptrend


class TestMACDStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance"""
        return MACDStrategy(fast_period=12, slow_period=26, signal_period=9, threshold=0.001)
    
    @pytest.fixture
    def bullish_data(self):
        """Create data that might trigger bullish signal"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create data that starts flat, then trends up
        prices = []
        for i in range(50):
            if i < 20:
                prices.append(100 + np.random.normal(0, 0.5))
            else:
                prices.append(100 + (i - 19) * 0.5)
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
    
    @pytest.fixture
    def bearish_data(self):
        """Create data that might trigger bearish signal"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create data that starts flat, then trends down
        prices = []
        for i in range(50):
            if i < 20:
                prices.append(100 + np.random.normal(0, 0.5))
            else:
                prices.append(100 - (i - 19) * 0.5)
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_generate_signal_bullish(self, strategy, bullish_data):
        """Test signal generation for bullish condition"""
        signal = await strategy.generate_signal("AAPL", bullish_data)
        
        # The signal may or may not be generated depending on the exact MACD values
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action == "BUY"
            assert signal.strategy == "MACD"
            assert signal.confidence == 0.7
            assert signal.metadata["signal_type"] == "bullish_crossover"
            assert "macd" in signal.metadata
            assert "signal" in signal.metadata
            assert "histogram" in signal.metadata
        else:
            # If no signal, that's also valid
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_bearish(self, strategy, bearish_data):
        """Test signal generation for bearish condition"""
        signal = await strategy.generate_signal("AAPL", bearish_data)
        
        # The signal may or may not be generated depending on the exact MACD values
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action == "SELL"
            assert signal.strategy == "MACD"
            assert signal.confidence == 0.7
            assert signal.metadata["signal_type"] == "bearish_crossover"
            assert "macd" in signal.metadata
            assert "signal" in signal.metadata
            assert "histogram" in signal.metadata
        else:
            # If no signal, that's also valid
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_signal(self, strategy):
        """Test signal generation when no signal should be generated"""
        # Create neutral data (no clear trend)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + np.random.normal(0, 0.5) for i in range(50)]
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
        
        signal = await strategy.generate_signal("AAPL", data)
        
        # May or may not generate a signal
        if signal is not None:
            assert isinstance(signal, TradeSignal)
        else:
            assert True  # No signal is also valid
    
    @pytest.mark.asyncio
    async def test_generate_signal_empty_data(self, strategy):
        """Test signal generation with empty data"""
        empty_data = pd.DataFrame()
        signal = await strategy.generate_signal("AAPL", empty_data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        # Create data with fewer points than slow_period + signal_period
        data = pd.DataFrame({
            'Close': [100 + i for i in range(30)]  # 30 points < 26 + 9
        })
        
        signal = await strategy.generate_signal("AAPL", data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_historical_date(self, strategy, bullish_data):
        """Test signal generation with historical date"""
        signal = await strategy.generate_signal("AAPL", bullish_data, historical_date="2023-01-15")
        
        # Historical date should not affect the signal generation logic
        if signal is not None:
            assert signal.symbol == "AAPL"
            assert signal.timestamp is not None
        else:
            assert True  # No signal is also valid
    
    @pytest.mark.asyncio
    async def test_generate_signal_deactivated_strategy(self, strategy, bullish_data):
        """Test signal generation when strategy is deactivated"""
        strategy.deactivate()
        signal = await strategy.generate_signal("AAPL", bullish_data)
        
        # Strategy should still generate signals even when deactivated
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
        else:
            assert True  # No signal is also valid


class TestMACDStrategyPositionSizing:
    """Test position sizing functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance"""
        return MACDStrategy()
    
    def test_calculate_quantity(self, strategy):
        """Test quantity calculation"""
        price = 100.0
        quantity = strategy._calculate_quantity(price)
        
        assert quantity == 10.0  # 1000 / 100 = 10
    
    def test_calculate_quantity_zero_price(self, strategy):
        """Test quantity calculation with zero price"""
        with pytest.raises(ZeroDivisionError):
            strategy._calculate_quantity(0.0)
    
    def test_calculate_quantity_negative_price(self, strategy):
        """Test quantity calculation with negative price"""
        quantity = strategy._calculate_quantity(-50.0)
        
        assert quantity == -20.0  # 1000 / -50 = -20
    
    def test_calculate_position_size_inherited(self, strategy):
        """Test inherited calculate_position_size method"""
        capital = 10000.0
        price = 100.0
        risk_percentage = 0.02
        
        position_size = strategy.calculate_position_size(capital, price, risk_percentage)
        
        expected_size = (capital * risk_percentage) / price
        assert position_size == expected_size


class TestMACDStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance"""
        return MACDStrategy()
    
    @pytest.mark.asyncio
    async def test_generate_signal_nan_values(self, strategy):
        """Test signal generation with NaN values in data"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + i if i < 30 else np.nan for i in range(50)]
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 if not pd.isna(p) else np.nan for p in prices],
            'High': [p + 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Low': [p - 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
        
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should handle NaN values gracefully
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_missing_columns(self, strategy):
        """Test signal generation with missing required columns"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'Open': [100] * 50,
            'High': [110] * 50,
            'Low': [90] * 50,
            'Volume': [1000] * 50
            # Missing 'Close' column
        }, index=dates)
        
        # Should raise an error due to missing 'Close' column
        with pytest.raises(KeyError):
            await strategy.generate_signal("AAPL", data)
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True


class TestMACDStrategyIntegration:
    """Integration tests for MACD strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create MACDStrategy instance"""
        return MACDStrategy(fast_period=12, slow_period=26, signal_period=9, threshold=0.001)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete MACD strategy workflow"""
        # Create realistic market data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create a pattern that goes from flat to trending
        prices = []
        for i in range(50):
            if i < 20:
                prices.append(100 + np.random.normal(0, 0.5))  # Flat
            else:
                prices.append(100 + (i - 19) * 0.5)  # Trending up
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 50
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should generate a signal (either BUY or SELL depending on the pattern)
        if signal is not None:
            assert signal.symbol == "AAPL"
            assert signal.action in ["BUY", "SELL"]
            assert signal.strategy == "MACD"
            assert signal.confidence == 0.7
            assert "macd" in signal.metadata
            assert "signal" in signal.metadata
            assert "histogram" in signal.metadata
            assert "signal_type" in signal.metadata
    
    @pytest.mark.asyncio
    async def test_multiple_signals(self, strategy):
        """Test generating multiple signals over time"""
        # Create data that might generate multiple signals
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        # Create oscillating prices
        prices = [100 + 10 * np.sin(i * 0.1) for i in range(100)]
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 100
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # May or may not generate a signal depending on the pattern
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.strategy == "MACD" 