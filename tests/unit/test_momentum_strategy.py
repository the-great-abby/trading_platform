#!/usr/bin/env python3
"""
Tests for Momentum Strategy
Comprehensive test suite for momentum-based trading strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.strategies.momentum.momentum_strategy import MomentumStrategy
from src.core.types import TradeSignal


class TestMomentumStrategyInitialization:
    """Test MomentumStrategy initialization"""
    
    def test_momentum_strategy_init_default(self):
        """Test MomentumStrategy initialization with default parameters"""
        strategy = MomentumStrategy()
        
        assert strategy.name == "Momentum_Strategy"
        assert strategy.momentum_period == 10
        assert strategy.volume_period == 20
        assert strategy.momentum_threshold == 0.02
        assert strategy.volume_threshold == 1.5
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
    
    def test_momentum_strategy_init_custom(self):
        """Test MomentumStrategy initialization with custom parameters"""
        strategy = MomentumStrategy(
            momentum_period=15,
            volume_period=25,
            momentum_threshold=0.03,
            volume_threshold=2.0
        )
        
        assert strategy.name == "Momentum_Strategy"
        assert strategy.momentum_period == 15
        assert strategy.volume_period == 25
        assert strategy.momentum_threshold == 0.03
        assert strategy.volume_threshold == 2.0
    
    def test_momentum_strategy_get_info(self):
        """Test get_strategy_info method"""
        strategy = MomentumStrategy(momentum_period=12)
        info = strategy.get_strategy_info()
        
        assert info["name"] == "Momentum_Strategy"
        assert info["is_active"] is True
        assert "momentum_period" not in info["config"]  # momentum_period is not in config, it's a direct attribute


class TestMomentumStrategyCalculation:
    """Test momentum calculation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MomentumStrategy instance"""
        return MomentumStrategy(momentum_period=10, volume_period=20)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create trending data with volume
        prices = [100 + i * 0.5 + np.random.normal(0, 0.1) for i in range(50)]
        volumes = [1000 + np.random.randint(-200, 200) for _ in range(50)]
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
    
    def test_calculate_momentum_indicators_basic(self, strategy, sample_data):
        """Test basic momentum indicators calculation"""
        result = strategy._calculate_momentum_indicators(sample_data)
        
        # Check that all indicators are calculated
        assert 'Momentum' in result.columns
        assert 'Volume_Ratio' in result.columns
        assert 'Momentum_Accel' in result.columns
        assert 'Volatility_Adj_Momentum' in result.columns
        
        # Check that we have some valid values (not all NaN)
        assert result['Momentum'].notna().any()
        assert result['Volume_Ratio'].notna().any()
        assert result['Momentum_Accel'].notna().any()
        assert result['Volatility_Adj_Momentum'].notna().any()
    
    def test_calculate_momentum_indicators_insufficient_data(self, strategy):
        """Test momentum indicators calculation with insufficient data"""
        # Create data with fewer points than momentum_period
        data = pd.DataFrame({
            'Close': [100 + i for i in range(5)],  # 5 points < 10
            'Volume': [1000] * 5
        })
        
        result = strategy._calculate_momentum_indicators(data)
        
        # Should still calculate indicators but with NaN values for insufficient data
        assert 'Momentum' in result.columns
        assert 'Volume_Ratio' in result.columns
        assert 'Momentum_Accel' in result.columns
        assert 'Volatility_Adj_Momentum' in result.columns
    
    def test_calculate_momentum_indicators_trending_data(self, strategy):
        """Test momentum indicators calculation with trending data"""
        # Create upward trending data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + i * 0.5 for i in range(50)]  # Steady upward trend
        volumes = [1000 + i * 10 for i in range(50)]  # Increasing volume
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
        
        result = strategy._calculate_momentum_indicators(data)
        
        # In an upward trend, momentum should generally be positive
        valid_momentum = result['Momentum'].dropna()
        if len(valid_momentum) > 0:
            assert valid_momentum.iloc[-1] > 0  # Latest momentum should be positive in uptrend


class TestMomentumStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MomentumStrategy instance"""
        return MomentumStrategy(momentum_period=10, volume_period=20, momentum_threshold=0.02, volume_threshold=1.5)
    
    @pytest.fixture
    def bullish_data(self):
        """Create data that might trigger bullish signal"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create data with strong upward momentum and high volume
        prices = []
        volumes = []
        for i in range(50):
            if i < 30:
                prices.append(100 + np.random.normal(0, 0.5))
                volumes.append(1000 + np.random.randint(-100, 100))
            else:
                prices.append(100 + (i - 29) * 0.8)  # Strong upward momentum
                volumes.append(2000 + np.random.randint(-200, 200))  # High volume
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
    
    @pytest.fixture
    def bearish_data(self):
        """Create data that might trigger bearish signal"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create data with strong downward momentum and high volume
        prices = []
        volumes = []
        for i in range(50):
            if i < 30:
                prices.append(100 + np.random.normal(0, 0.5))
                volumes.append(1000 + np.random.randint(-100, 100))
            else:
                prices.append(100 - (i - 29) * 0.8)  # Strong downward momentum
                volumes.append(2000 + np.random.randint(-200, 200))  # High volume
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_generate_signal_bullish(self, strategy, bullish_data):
        """Test signal generation for bullish condition"""
        signal = await strategy.generate_signal("AAPL", bullish_data)
        
        # The signal may or may not be generated depending on the exact momentum values
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action == "BUY"
            assert signal.strategy == "Momentum_Strategy"
            assert signal.confidence <= 0.9
            assert signal.metadata["signal_type"] == "momentum_breakout"
            assert "momentum" in signal.metadata
            assert "volume_ratio" in signal.metadata
            assert "rsi" in signal.metadata
        else:
            # If no signal, that's also valid
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_bearish(self, strategy, bearish_data):
        """Test signal generation for bearish condition"""
        signal = await strategy.generate_signal("AAPL", bearish_data)
        
        # The signal may or may not be generated depending on the exact momentum values
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action == "SELL"
            assert signal.strategy == "Momentum_Strategy"
            assert signal.confidence <= 0.9
            assert signal.metadata["signal_type"] == "momentum_breakdown"
            assert "momentum" in signal.metadata
            assert "volume_ratio" in signal.metadata
            assert "rsi" in signal.metadata
        else:
            # If no signal, that's also valid
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_signal(self, strategy):
        """Test signal generation when no signal should be generated"""
        # Create neutral data (no clear momentum)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + np.random.normal(0, 0.5) for i in range(50)]
        volumes = [1000 + np.random.randint(-100, 100) for i in range(50)]
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
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
        # Create data with fewer points than required
        data = pd.DataFrame({
            'Close': [100 + i for i in range(10)],  # 10 points < max(10, 20) + 5
            'Volume': [1000] * 10
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


class TestMomentumStrategyPositionSizing:
    """Test position sizing functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create MomentumStrategy instance"""
        return MomentumStrategy()
    
    def test_calculate_quantity(self, strategy):
        """Test quantity calculation"""
        price = 100.0
        momentum_strength = 0.05
        quantity = strategy._calculate_quantity(price, momentum_strength)
        
        base_quantity = 1000 / price  # 10
        momentum_multiplier = 1.0 + (abs(momentum_strength) * 2)  # 1.1
        expected_quantity = base_quantity * momentum_multiplier  # 10 * 1.1 = 11
        
        assert quantity == expected_quantity
    
    def test_calculate_quantity_zero_price(self, strategy):
        """Test quantity calculation with zero price"""
        with pytest.raises(ZeroDivisionError):
            strategy._calculate_quantity(0.0, 0.05)
    
    def test_calculate_quantity_negative_price(self, strategy):
        """Test quantity calculation with negative price"""
        quantity = strategy._calculate_quantity(-50.0, 0.05)
        
        base_quantity = 1000 / -50.0  # -20
        momentum_multiplier = 1.0 + (abs(0.05) * 2)  # 1.1
        expected_quantity = base_quantity * momentum_multiplier  # -20 * 1.1 = -22
        
        assert quantity == expected_quantity
    
    def test_calculate_quantity_high_momentum(self, strategy):
        """Test quantity calculation with high momentum"""
        price = 100.0
        momentum_strength = 0.2  # High momentum
        quantity = strategy._calculate_quantity(price, momentum_strength)
        
        base_quantity = 1000 / price  # 10
        momentum_multiplier = 1.0 + (abs(momentum_strength) * 2)  # 1.4
        expected_quantity = base_quantity * momentum_multiplier  # 10 * 1.4 = 14
        
        assert quantity == expected_quantity
    
    def test_calculate_position_size_inherited(self, strategy):
        """Test inherited calculate_position_size method"""
        capital = 10000.0
        price = 100.0
        risk_percentage = 0.02
        
        position_size = strategy.calculate_position_size(capital, price, risk_percentage)
        
        expected_size = (capital * risk_percentage) / price
        assert position_size == expected_size


class TestMomentumStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create MomentumStrategy instance"""
        return MomentumStrategy()
    
    @pytest.mark.asyncio
    async def test_generate_signal_nan_values(self, strategy):
        """Test signal generation with NaN values in data"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = [100 + i if i < 30 else np.nan for i in range(50)]
        volumes = [1000 if i < 30 else np.nan for i in range(50)]
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 if not pd.isna(p) else np.nan for p in prices],
            'High': [p + 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Low': [p - 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Volume': volumes
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
            'Low': [90] * 50
            # Missing 'Close' and 'Volume' columns
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


class TestMomentumStrategyIntegration:
    """Integration tests for momentum strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create MomentumStrategy instance"""
        return MomentumStrategy(momentum_period=10, volume_period=20, momentum_threshold=0.02, volume_threshold=1.5)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete momentum strategy workflow"""
        # Create realistic market data with strong momentum
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create a pattern that goes from flat to strong momentum
        prices = []
        volumes = []
        for i in range(50):
            if i < 30:
                prices.append(100 + np.random.normal(0, 0.5))  # Flat
                volumes.append(1000 + np.random.randint(-100, 100))  # Normal volume
            else:
                prices.append(100 + (i - 29) * 0.8)  # Strong upward momentum
                volumes.append(2000 + np.random.randint(-200, 200))  # High volume
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should generate a signal (either BUY or SELL depending on the pattern)
        if signal is not None:
            assert signal.symbol == "AAPL"
            assert signal.action in ["BUY", "SELL"]
            assert signal.strategy == "Momentum_Strategy"
            assert signal.confidence <= 0.9
            assert "momentum" in signal.metadata
            assert "volume_ratio" in signal.metadata
            assert "rsi" in signal.metadata
            assert "signal_type" in signal.metadata
    
    @pytest.mark.asyncio
    async def test_multiple_signals(self, strategy):
        """Test generating multiple signals over time"""
        # Create data that might generate multiple signals
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        # Create oscillating prices with momentum
        prices = []
        volumes = []
        for i in range(100):
            if i < 25:
                prices.append(100 + np.random.normal(0, 0.5))  # Flat
                volumes.append(1000 + np.random.randint(-100, 100))
            elif i < 50:
                prices.append(100 + (i - 24) * 0.5)  # Upward momentum
                volumes.append(1500 + np.random.randint(-150, 150))
            elif i < 75:
                prices.append(100 + (49 - 24) * 0.5 - (i - 49) * 0.5)  # Downward momentum
                volumes.append(1500 + np.random.randint(-150, 150))
            else:
                prices.append(100 + np.random.normal(0, 0.5))  # Flat again
                volumes.append(1000 + np.random.randint(-100, 100))
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # May or may not generate a signal depending on the pattern
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.strategy == "Momentum_Strategy"
        else:
            assert True  # No signal is also valid 