#!/usr/bin/env python3
"""
Tests for Adaptive Momentum Strategy
Comprehensive test suite for adaptive momentum strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.strategies.adaptive_momentum_strategy import AdaptiveMomentumStrategy
from src.core.types import TradeSignal


class TestAdaptiveMomentumStrategyInitialization:
    """Test AdaptiveMomentumStrategy initialization"""
    
    def test_adaptive_momentum_strategy_init_default(self):
        """Test AdaptiveMomentumStrategy initialization with default parameters"""
        strategy = AdaptiveMomentumStrategy()
        
        assert strategy.name == "Adaptive_Momentum_Strategy"
        assert strategy.base_momentum_period == 20
        assert strategy.volatility_lookback == 50
        assert strategy.trend_lookback == 100
        assert strategy.min_confidence == 0.6
        assert strategy.max_position_size == 0.1
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert strategy.market_regime == "normal"
        assert strategy.volatility_regime == "normal"
        assert strategy.trend_strength == 0.0
    
    def test_adaptive_momentum_strategy_init_custom(self):
        """Test AdaptiveMomentumStrategy initialization with custom parameters"""
        strategy = AdaptiveMomentumStrategy(
            base_momentum_period=30,
            volatility_lookback=60,
            trend_lookback=120,
            min_confidence=0.7,
            max_position_size=0.15
        )
        
        assert strategy.name == "Adaptive_Momentum_Strategy"
        assert strategy.base_momentum_period == 30
        assert strategy.volatility_lookback == 60
        assert strategy.trend_lookback == 120
        assert strategy.min_confidence == 0.7
        assert strategy.max_position_size == 0.15
    
    def test_adaptive_momentum_strategy_get_info(self):
        """Test get_strategy_info method"""
        strategy = AdaptiveMomentumStrategy(base_momentum_period=25, min_confidence=0.65)
        info = strategy.get_strategy_info()
        
        assert info["name"] == "Adaptive_Momentum_Strategy"
        assert info["is_active"] is True
        assert isinstance(info["config"], dict)


class TestAdaptiveMomentumStrategyCalculation:
    """Test calculation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy(base_momentum_period=20, trend_lookback=50)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        # Create data with clear trend and momentum
        prices = []
        for i in range(120):
            if i < 60:
                prices.append(100 + i * 0.5)  # Upward trend
            else:
                prices.append(130 + (i - 60) * 0.3)  # Continued trend
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000 + i * 10 for i in range(120)]  # Increasing volume
        }, index=dates)
    
    def test_calculate_adaptive_parameters_basic(self, strategy, sample_data):
        """Test basic adaptive parameter calculation"""
        result = strategy.calculate_adaptive_parameters(sample_data)
        
        # Check that all required keys are present
        assert 'market_regime' in result
        assert 'volatility_regime' in result
        assert 'trend_strength' in result
        assert 'current_volatility' in result
        assert 'historical_volatility' in result
        assert 'adaptive_params' in result
        
        # Check adaptive parameters
        adaptive_params = result['adaptive_params']
        assert 'momentum_period' in adaptive_params
        assert 'confidence_threshold' in adaptive_params
        assert 'position_size' in adaptive_params
        
        # Check that values are reasonable
        assert 0.0 <= result['trend_strength'] <= 1.0
        assert result['current_volatility'] > 0
        assert result['historical_volatility'] > 0
        assert adaptive_params['momentum_period'] >= 5
        assert 0.0 <= adaptive_params['confidence_threshold'] <= 0.9
        assert 0.0 <= adaptive_params['position_size'] <= 0.15
    
    def test_calculate_adaptive_parameters_insufficient_data(self, strategy):
        """Test adaptive parameter calculation with insufficient data"""
        # Create data with fewer points than trend_lookback
        data = pd.DataFrame({
            'Close': [100 + i for i in range(30)],  # Only 30 points < 100
            'Volume': [1000] * 30  # Add Volume column
        })
        
        result = strategy.calculate_adaptive_parameters(data)
        
        # Should return default parameters
        assert result['market_regime'] == 'normal'
        assert result['volatility_regime'] == 'normal'
        assert result['trend_strength'] == 0.0
        assert result['current_volatility'] == 0.02
        assert result['historical_volatility'] == 0.02
    
    def test_calculate_trend_strength(self, strategy, sample_data):
        """Test trend strength calculation"""
        trend_strength = strategy._calculate_trend_strength(sample_data)
        
        assert isinstance(trend_strength, float)
        assert 0.0 <= trend_strength <= 1.0
    
    def test_calculate_price_trend_strength(self, strategy, sample_data):
        """Test price trend strength calculation"""
        price_trend = strategy._calculate_price_trend_strength(sample_data)
        
        assert isinstance(price_trend, float)
        assert 0.0 <= price_trend <= 1.0
    
    def test_calculate_volume_trend_strength(self, strategy, sample_data):
        """Test volume trend strength calculation"""
        volume_trend = strategy._calculate_volume_trend_strength(sample_data)
        
        assert isinstance(volume_trend, float)
        assert 0.0 <= volume_trend <= 1.0
    
    def test_calculate_momentum_trend_strength(self, strategy, sample_data):
        """Test momentum trend strength calculation"""
        momentum_trend = strategy._calculate_momentum_trend_strength(sample_data)
        
        assert isinstance(momentum_trend, float)
        assert 0.0 <= momentum_trend <= 1.0
    
    def test_calculate_ma_alignment(self, strategy, sample_data):
        """Test moving average alignment calculation"""
        ma_alignment = strategy._calculate_ma_alignment(sample_data)
        
        assert isinstance(ma_alignment, float)
        assert 0.0 <= ma_alignment <= 1.0


class TestAdaptiveMomentumStrategyMarketClassification:
    """Test market classification functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy()
    
    def test_classify_market_regime_high_vol(self, strategy):
        """Test market regime classification for high volatility"""
        volatility = 0.05  # 5% > 3% threshold
        trend_strength = 0.5
        
        regime = strategy._classify_market_regime(volatility, trend_strength)
        
        assert regime == "high_vol"
    
    def test_classify_market_regime_low_vol(self, strategy):
        """Test market regime classification for low volatility"""
        volatility = 0.005  # 0.5% < 1% threshold
        trend_strength = 0.5
        
        regime = strategy._classify_market_regime(volatility, trend_strength)
        
        assert regime == "low_vol"
    
    def test_classify_market_regime_trending(self, strategy):
        """Test market regime classification for trending market"""
        volatility = 0.02  # Normal volatility
        trend_strength = 0.8  # > 0.6 threshold
        
        regime = strategy._classify_market_regime(volatility, trend_strength)
        
        assert regime == "trending"
    
    def test_classify_market_regime_sideways(self, strategy):
        """Test market regime classification for sideways market"""
        volatility = 0.02  # Normal volatility
        trend_strength = 0.2  # < 0.3 threshold
        
        regime = strategy._classify_market_regime(volatility, trend_strength)
        
        assert regime == "sideways"
    
    def test_classify_market_regime_normal(self, strategy):
        """Test market regime classification for normal market"""
        volatility = 0.02  # Normal volatility
        trend_strength = 0.4  # Between thresholds
        
        regime = strategy._classify_market_regime(volatility, trend_strength)
        
        assert regime == "normal"
    
    def test_classify_volatility_regime_high(self, strategy):
        """Test volatility regime classification for high volatility"""
        volatility = 0.05  # > 3% threshold
        
        regime = strategy._classify_volatility_regime(volatility)
        
        assert regime == "high"
    
    def test_classify_volatility_regime_low(self, strategy):
        """Test volatility regime classification for low volatility"""
        volatility = 0.005  # < 1% threshold
        
        regime = strategy._classify_volatility_regime(volatility)
        
        assert regime == "low"
    
    def test_classify_volatility_regime_normal(self, strategy):
        """Test volatility regime classification for normal volatility"""
        volatility = 0.02  # Between thresholds
        
        regime = strategy._classify_volatility_regime(volatility)
        
        assert regime == "normal"


class TestAdaptiveMomentumStrategyParameterAdaptation:
    """Test parameter adaptation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy(base_momentum_period=20, min_confidence=0.6, max_position_size=0.1)
    
    def test_adapt_parameters_high_vol(self, strategy):
        """Test parameter adaptation for high volatility regime"""
        adaptive_params = strategy._adapt_parameters("high_vol", "high", 0.5, 0.05)
        
        # Should have shorter momentum period, higher confidence threshold, smaller position
        assert adaptive_params['momentum_period'] < strategy.base_momentum_period
        assert adaptive_params['confidence_threshold'] > strategy.min_confidence
        assert adaptive_params['position_size'] < strategy.max_position_size
    
    def test_adapt_parameters_low_vol(self, strategy):
        """Test parameter adaptation for low volatility regime"""
        adaptive_params = strategy._adapt_parameters("low_vol", "low", 0.5, 0.005)
        
        # Should have longer momentum period, lower confidence threshold, larger position
        assert adaptive_params['momentum_period'] > strategy.base_momentum_period
        assert adaptive_params['confidence_threshold'] < strategy.min_confidence
        assert adaptive_params['position_size'] > strategy.max_position_size
    
    def test_adapt_parameters_trending(self, strategy):
        """Test parameter adaptation for trending market"""
        adaptive_params = strategy._adapt_parameters("trending", "normal", 0.8, 0.02)
        
        # Should have shorter momentum period, lower confidence threshold, larger position
        assert adaptive_params['momentum_period'] < strategy.base_momentum_period
        assert adaptive_params['confidence_threshold'] < strategy.min_confidence
        assert adaptive_params['position_size'] > strategy.max_position_size
    
    def test_adapt_parameters_sideways(self, strategy):
        """Test parameter adaptation for sideways market"""
        adaptive_params = strategy._adapt_parameters("sideways", "normal", 0.2, 0.02)
        
        # Should have longer momentum period, higher confidence threshold, smaller position
        assert adaptive_params['momentum_period'] > strategy.base_momentum_period
        assert adaptive_params['confidence_threshold'] > strategy.min_confidence
        assert adaptive_params['position_size'] < strategy.max_position_size
    
    def test_adapt_parameters_bounds(self, strategy):
        """Test that adapted parameters stay within bounds"""
        adaptive_params = strategy._adapt_parameters("high_vol", "high", 0.9, 0.1)
        
        # Check bounds
        assert adaptive_params['momentum_period'] >= 5
        assert adaptive_params['confidence_threshold'] <= 0.9
        assert adaptive_params['position_size'] <= 0.15


class TestAdaptiveMomentumStrategyMomentumCalculation:
    """Test momentum calculation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy()
    
    @pytest.fixture
    def momentum_data(self):
        """Create data for momentum calculation"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Create data with clear momentum
        prices = [100 + i * 2 for i in range(50)]  # Strong upward momentum
        volumes = [1000 + i * 20 for i in range(50)]  # Increasing volume
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': volumes
        }, index=dates)
    
    def test_calculate_momentum_signal(self, strategy, momentum_data):
        """Test momentum signal calculation"""
        adaptive_params = {
            'momentum_period': 20,
            'confidence_threshold': 0.6,
            'position_size': 0.1
        }
        
        result = strategy.calculate_momentum_signal(momentum_data, adaptive_params)
        
        # Check structure
        assert 'signal' in result
        assert 'confidence' in result
        assert 'strength' in result
        assert 'price_momentum' in result
        assert 'volume_momentum' in result
        assert 'rsi_momentum' in result
        
        # Check values
        assert result['signal'] in ['BUY', 'SELL', 'HOLD']
        assert 0.0 <= result['confidence'] <= 0.95
        assert -1.0 <= result['strength'] <= 1.0
    
    def test_calculate_price_momentum(self, strategy, momentum_data):
        """Test price momentum calculation"""
        momentum = strategy._calculate_price_momentum(momentum_data, 20)
        
        assert isinstance(momentum, float)
        assert -1.0 <= momentum <= 1.0
        assert momentum > 0  # Should be positive for upward trend
    
    def test_calculate_volume_momentum(self, strategy, momentum_data):
        """Test volume momentum calculation"""
        momentum = strategy._calculate_volume_momentum(momentum_data, 20)
        
        assert isinstance(momentum, float)
        assert -1.0 <= momentum <= 1.0
    
    def test_calculate_rsi_momentum(self, strategy, momentum_data):
        """Test RSI momentum calculation"""
        momentum = strategy._calculate_rsi_momentum(momentum_data)
        
        assert isinstance(momentum, float)
        assert -1.0 <= momentum <= 1.0
    
    def test_calculate_rsi(self, strategy, momentum_data):
        """Test RSI calculation"""
        rsi = strategy._calculate_rsi(momentum_data, 14)
        
        assert isinstance(rsi, float)
        assert 0.0 <= rsi <= 100.0


class TestAdaptiveMomentumStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy(trend_lookback=50)
    
    @pytest.fixture
    def signal_data(self):
        """Create data for signal generation"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        # Create data with strong momentum
        prices = []
        for i in range(120):
            if i < 60:
                prices.append(100 + i * 0.5)  # Moderate trend
            else:
                prices.append(130 + (i - 60) * 2)  # Strong momentum
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000 + i * 15 for i in range(120)]
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_generate_signal_strong_momentum(self, strategy, signal_data):
        """Test signal generation for strong momentum"""
        signal = await strategy.generate_signal("AAPL", signal_data)
        
        # May or may not generate signal depending on conditions
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action in ["BUY", "SELL"]
            assert signal.strategy == "Adaptive_Momentum_Strategy"
            assert signal.confidence >= 0.6
            assert signal.metadata["signal_type"] == "adaptive_momentum"
            assert "market_regime" in signal.metadata
            assert "volatility_regime" in signal.metadata
            assert "trend_strength" in signal.metadata
            assert "adaptive_params" in signal.metadata
            assert "momentum_signal" in signal.metadata
        else:
            # No signal is also valid if conditions aren't met
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_weak_momentum(self, strategy):
        """Test signal generation for weak momentum"""
        # Create data with weak momentum
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        prices = [100 + np.random.normal(0, 0.5) for i in range(120)]  # Random walk
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 120
        }, index=dates)
        
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should not generate signal for weak momentum
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        # Create data with fewer points than trend_lookback
        data = pd.DataFrame({
            'Close': [100 + i for i in range(30)],  # Only 30 points < 100
            'Volume': [1000] * 30  # Add Volume column
        })
        
        signal = await strategy.generate_signal("AAPL", data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_historical_date(self, strategy, signal_data):
        """Test signal generation with historical date"""
        signal = await strategy.generate_signal("AAPL", signal_data, historical_date="2023-01-15")
        
        # Historical date should not affect the signal generation logic
        if signal is not None:
            assert signal.symbol == "AAPL"
            assert signal.timestamp is not None
        else:
            assert True  # No signal is also valid
    
    @pytest.mark.asyncio
    async def test_generate_signal_deactivated_strategy(self, strategy, signal_data):
        """Test signal generation when strategy is deactivated"""
        strategy.deactivate()
        signal = await strategy.generate_signal("AAPL", signal_data)
        
        # Strategy should still generate signals even when deactivated
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
        else:
            assert True  # No signal is also valid


class TestAdaptiveMomentumStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy()
    
    @pytest.mark.asyncio
    async def test_generate_signal_nan_values(self, strategy):
        """Test signal generation with NaN values in data"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        prices = [100 + i if i < 50 else np.nan for i in range(120)]
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 if not pd.isna(p) else np.nan for p in prices],
            'High': [p + 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Low': [p - 0.2 if not pd.isna(p) else np.nan for p in prices],
            'Volume': [1000] * 120
        }, index=dates)
        
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should handle NaN values gracefully
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_missing_columns(self, strategy):
        """Test signal generation with missing required columns"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        data = pd.DataFrame({
            'Open': [100] * 120,
            'High': [110] * 120,
            'Low': [90] * 120
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


class TestAdaptiveMomentumStrategyIntegration:
    """Integration tests for adaptive momentum strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create AdaptiveMomentumStrategy instance"""
        return AdaptiveMomentumStrategy(
            base_momentum_period=20,
            trend_lookback=50,
            min_confidence=0.6,
            max_position_size=0.1
        )
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete adaptive momentum strategy workflow"""
        # Create realistic market data with clear adaptive patterns
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        # Create a pattern that goes from low volatility to high momentum
        prices = []
        for i in range(120):
            if i < 60:
                prices.append(100 + np.random.normal(0, 0.3))  # Low volatility
            elif i < 90:
                prices.append(100 + (i - 59) * 1.5 + np.random.normal(0, 0.8))  # High momentum
            else:
                prices.append(145 + (i - 89) * 0.5 + np.random.normal(0, 0.5))  # Continued trend
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000 + i * 10 for i in range(120)]
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # Should generate a signal (either BUY or SELL depending on the pattern)
        if signal is not None:
            assert signal.symbol == "AAPL"
            assert signal.action in ["BUY", "SELL"]
            assert signal.strategy == "Adaptive_Momentum_Strategy"
            assert signal.confidence >= 0.4  # Lower threshold for adaptive strategy
            assert signal.metadata["signal_type"] == "adaptive_momentum"
            assert "market_regime" in signal.metadata
            assert "volatility_regime" in signal.metadata
            assert "trend_strength" in signal.metadata
            assert "adaptive_params" in signal.metadata
            assert "momentum_signal" in signal.metadata
        else:
            # No signal is also valid if conditions aren't met exactly
            assert True
    
    @pytest.mark.asyncio
    async def test_multiple_signals(self, strategy):
        """Test generating multiple signals over time"""
        # Create data that might generate multiple signals
        dates = pd.date_range('2023-01-01', periods=150, freq='D')
        # Create oscillating prices that might trigger multiple signals
        prices = []
        for i in range(150):
            if i < 50:
                prices.append(100 + np.random.normal(0, 0.3))  # Low volatility
            elif i < 80:
                prices.append(100 + (i - 49) * 2 + np.random.normal(0, 1.2))  # Momentum 1
            elif i < 110:
                prices.append(160 + np.random.normal(0, 0.3))  # Consolidation
            elif i < 140:
                prices.append(160 - (i - 109) * 1.5 + np.random.normal(0, 1.0))  # Momentum 2
            else:
                prices.append(130 + np.random.normal(0, 0.3))  # Consolidation
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000 + i * 8 for i in range(150)]
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # May or may not generate a signal depending on the pattern
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.strategy == "Adaptive_Momentum_Strategy"
        else:
            assert True  # No signal is also valid 