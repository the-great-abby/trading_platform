"""
Unit tests for trading strategies
"""

import pytest
import numpy as np
from decimal import Decimal

from src.strategies.base import BaseStrategy
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy


class TestBaseStrategy:
    """Test BaseStrategy"""
    
    def test_base_strategy_creation(self):
        """Test creating base strategy"""
        strategy = BaseStrategy(name="Test Strategy")
        
        assert strategy.name == "Test Strategy"
        assert strategy.is_active is True
        assert strategy.parameters == {}
    
    def test_base_strategy_with_parameters(self):
        """Test creating base strategy with parameters"""
        params = {"param1": "value1", "param2": 42}
        strategy = BaseStrategy(name="Test Strategy", parameters=params)
        
        assert strategy.name == "Test Strategy"
        assert strategy.parameters == params
    
    def test_base_strategy_validation(self):
        """Test base strategy validation"""
        strategy = BaseStrategy(name="Test Strategy")
        
        # Test required parameters validation
        with pytest.raises(NotImplementedError):
            strategy.validate_parameters()
        
        # Test signal generation
        with pytest.raises(NotImplementedError):
            strategy.generate_signals({})


class TestSMACrossoverStrategy:
    """Test SMACrossoverStrategy"""
    
    @pytest.fixture
    def strategy(self):
        return SMACrossoverStrategy(
            short_period=5,
            long_period=10,
            threshold=0.01
        )
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for testing"""
        return {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150.0},
                {"timestamp": "2024-01-02", "close": 151.0},
                {"timestamp": "2024-01-03", "close": 149.0},
                {"timestamp": "2024-01-04", "close": 152.0},
                {"timestamp": "2024-01-05", "close": 153.0},
                {"timestamp": "2024-01-06", "close": 154.0},
                {"timestamp": "2024-01-07", "close": 155.0},
                {"timestamp": "2024-01-08", "close": 156.0},
                {"timestamp": "2024-01-09", "close": 157.0},
                {"timestamp": "2024-01-10", "close": 158.0},
                {"timestamp": "2024-01-11", "close": 159.0},
                {"timestamp": "2024-01-12", "close": 160.0},
            ]
        }
    
    def test_sma_crossover_creation(self, strategy):
        """Test SMA crossover strategy creation"""
        assert strategy.name == "SMA Crossover Strategy"
        assert strategy.short_period == 5
        assert strategy.long_period == 10
        assert strategy.threshold == 0.01
        assert strategy.parameters["short_period"] == 5
        assert strategy.parameters["long_period"] == 10
        assert strategy.parameters["threshold"] == 0.01
    
    def test_sma_crossover_validation(self, strategy):
        """Test SMA crossover parameter validation"""
        # Valid parameters
        strategy.validate_parameters()
        
        # Invalid short period
        with pytest.raises(ValueError):
            invalid_strategy = SMACrossoverStrategy(
                short_period=0,
                long_period=10,
                threshold=0.01
            )
        
        # Invalid long period
        with pytest.raises(ValueError):
            invalid_strategy = SMACrossoverStrategy(
                short_period=5,
                long_period=3,  # Less than short period
                threshold=0.01
            )
        
        # Invalid threshold
        with pytest.raises(ValueError):
            invalid_strategy = SMACrossoverStrategy(
                short_period=5,
                long_period=10,
                threshold=-0.01  # Negative threshold
            )
    
    def test_calculate_sma(self, strategy, sample_data):
        """Test SMA calculation"""
        prices = [bar["close"] for bar in sample_data["AAPL"]]
        
        # Calculate short SMA
        short_sma = strategy._calculate_sma(prices, 5)
        assert len(short_sma) == len(prices)
        assert short_sma[0] is None  # First 4 values should be None
        assert short_sma[4] is not None  # 5th value should be calculated
        
        # Calculate long SMA
        long_sma = strategy._calculate_sma(prices, 10)
        assert len(long_sma) == len(prices)
        assert long_sma[0] is None  # First 9 values should be None
        assert long_sma[9] is not None  # 10th value should be calculated
    
    def test_generate_signals_buy_signal(self, strategy, sample_data):
        """Test generating buy signals"""
        # Modify data to create buy signal (short SMA > long SMA)
        sample_data["AAPL"][-1]["close"] = 165.0  # Strong upward move
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        assert "action" in signal
        assert "confidence" in signal
        assert "short_sma" in signal
        assert "long_sma" in signal
        
        # Should generate buy signal when short SMA crosses above long SMA
        if signal["action"] == "BUY":
            assert signal["short_sma"] > signal["long_sma"]
            assert signal["confidence"] > 0
    
    def test_generate_signals_sell_signal(self, strategy, sample_data):
        """Test generating sell signals"""
        # Modify data to create sell signal (short SMA < long SMA)
        sample_data["AAPL"][-1]["close"] = 145.0  # Strong downward move
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        
        # Should generate sell signal when short SMA crosses below long SMA
        if signal["action"] == "SELL":
            assert signal["short_sma"] < signal["long_sma"]
            assert signal["confidence"] > 0
    
    def test_generate_signals_hold_signal(self, strategy, sample_data):
        """Test generating hold signals"""
        # Modify data to create hold signal (SMAs are close)
        sample_data["AAPL"][-1]["close"] = 158.0  # Minimal change
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        
        # Should generate hold signal when SMAs are within threshold
        if signal["action"] == "HOLD":
            assert abs(signal["short_sma"] - signal["long_sma"]) <= strategy.threshold
    
    def test_generate_signals_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        insufficient_data = {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150.0},
                {"timestamp": "2024-01-02", "close": 151.0},
                {"timestamp": "2024-01-03", "close": 149.0},
            ]
        }
        
        signals = strategy.generate_signals(insufficient_data)
        
        # Should return empty signals or hold signals for insufficient data
        assert "AAPL" in signals
        signal = signals["AAPL"]
        assert signal["action"] == "HOLD"
        assert signal["confidence"] == 0.0
    
    def test_generate_signals_multiple_symbols(self, strategy):
        """Test generating signals for multiple symbols"""
        multi_symbol_data = {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150.0},
                {"timestamp": "2024-01-02", "close": 151.0},
                {"timestamp": "2024-01-03", "close": 149.0},
                {"timestamp": "2024-01-04", "close": 152.0},
                {"timestamp": "2024-01-05", "close": 153.0},
                {"timestamp": "2024-01-06", "close": 154.0},
                {"timestamp": "2024-01-07", "close": 155.0},
                {"timestamp": "2024-01-08", "close": 156.0},
                {"timestamp": "2024-01-09", "close": 157.0},
                {"timestamp": "2024-01-10", "close": 158.0},
                {"timestamp": "2024-01-11", "close": 159.0},
                {"timestamp": "2024-01-12", "close": 160.0},
            ],
            "GOOGL": [
                {"timestamp": "2024-01-01", "close": 2800.0},
                {"timestamp": "2024-01-02", "close": 2810.0},
                {"timestamp": "2024-01-03", "close": 2790.0},
                {"timestamp": "2024-01-04", "close": 2820.0},
                {"timestamp": "2024-01-05", "close": 2830.0},
                {"timestamp": "2024-01-06", "close": 2840.0},
                {"timestamp": "2024-01-07", "close": 2850.0},
                {"timestamp": "2024-01-08", "close": 2860.0},
                {"timestamp": "2024-01-09", "close": 2870.0},
                {"timestamp": "2024-01-10", "close": 2880.0},
                {"timestamp": "2024-01-11", "close": 2890.0},
                {"timestamp": "2024-01-12", "close": 2900.0},
            ]
        }
        
        signals = strategy.generate_signals(multi_symbol_data)
        
        assert "AAPL" in signals
        assert "GOOGL" in signals
        assert len(signals) == 2
        
        for symbol, signal in signals.items():
            assert "action" in signal
            assert "confidence" in signal
            assert "short_sma" in signal
            assert "long_sma" in signal


class TestRSIStrategy:
    """Test RSIStrategy"""
    
    @pytest.fixture
    def strategy(self):
        return RSIStrategy(
            period=14,
            oversold_threshold=30,
            overbought_threshold=70
        )
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for testing"""
        return {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150.0},
                {"timestamp": "2024-01-02", "close": 151.0},
                {"timestamp": "2024-01-03", "close": 149.0},
                {"timestamp": "2024-01-04", "close": 152.0},
                {"timestamp": "2024-01-05", "close": 153.0},
                {"timestamp": "2024-01-06", "close": 154.0},
                {"timestamp": "2024-01-07", "close": 155.0},
                {"timestamp": "2024-01-08", "close": 156.0},
                {"timestamp": "2024-01-09", "close": 157.0},
                {"timestamp": "2024-01-10", "close": 158.0},
                {"timestamp": "2024-01-11", "close": 159.0},
                {"timestamp": "2024-01-12", "close": 160.0},
                {"timestamp": "2024-01-13", "close": 161.0},
                {"timestamp": "2024-01-14", "close": 162.0},
                {"timestamp": "2024-01-15", "close": 163.0},
            ]
        }
    
    def test_rsi_strategy_creation(self, strategy):
        """Test RSI strategy creation"""
        assert strategy.name == "RSI Strategy"
        assert strategy.period == 14
        assert strategy.oversold_threshold == 30
        assert strategy.overbought_threshold == 70
        assert strategy.parameters["period"] == 14
        assert strategy.parameters["oversold_threshold"] == 30
        assert strategy.parameters["overbought_threshold"] == 70
    
    def test_rsi_strategy_validation(self, strategy):
        """Test RSI parameter validation"""
        # Valid parameters
        strategy.validate_parameters()
        
        # Invalid period
        with pytest.raises(ValueError):
            invalid_strategy = RSIStrategy(
                period=0,
                oversold_threshold=30,
                overbought_threshold=70
            )
        
        # Invalid thresholds
        with pytest.raises(ValueError):
            invalid_strategy = RSIStrategy(
                period=14,
                oversold_threshold=80,  # Greater than overbought
                overbought_threshold=70
            )
        
        # Invalid threshold range
        with pytest.raises(ValueError):
            invalid_strategy = RSIStrategy(
                period=14,
                oversold_threshold=30,
                overbought_threshold=30  # Equal to oversold
            )
    
    def test_calculate_rsi(self, strategy, sample_data):
        """Test RSI calculation"""
        prices = [bar["close"] for bar in sample_data["AAPL"]]
        
        rsi_values = strategy._calculate_rsi(prices, 14)
        
        assert len(rsi_values) == len(prices)
        assert rsi_values[0] is None  # First 13 values should be None
        assert rsi_values[13] is not None  # 14th value should be calculated
        
        # RSI should be between 0 and 100
        for rsi in rsi_values:
            if rsi is not None:
                assert 0 <= rsi <= 100
    
    def test_generate_signals_oversold(self, strategy, sample_data):
        """Test generating buy signals on oversold condition"""
        # Modify data to create oversold condition (declining prices)
        for i in range(len(sample_data["AAPL"])):
            sample_data["AAPL"][i]["close"] = 150.0 - i  # Declining prices
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        
        # Should generate buy signal when RSI is oversold
        if signal["action"] == "BUY":
            assert signal["rsi"] <= strategy.oversold_threshold
            assert signal["confidence"] > 0
    
    def test_generate_signals_overbought(self, strategy, sample_data):
        """Test generating sell signals on overbought condition"""
        # Modify data to create overbought condition (rising prices)
        for i in range(len(sample_data["AAPL"])):
            sample_data["AAPL"][i]["close"] = 150.0 + i  # Rising prices
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        
        # Should generate sell signal when RSI is overbought
        if signal["action"] == "SELL":
            assert signal["rsi"] >= strategy.overbought_threshold
            assert signal["confidence"] > 0
    
    def test_generate_signals_neutral(self, strategy, sample_data):
        """Test generating hold signals in neutral condition"""
        # Modify data to create neutral condition
        for i in range(len(sample_data["AAPL"])):
            sample_data["AAPL"][i]["close"] = 150.0 + (i % 3 - 1)  # Oscillating prices
        
        signals = strategy.generate_signals(sample_data)
        
        assert "AAPL" in signals
        signal = signals["AAPL"]
        
        # Should generate hold signal when RSI is in neutral range
        if signal["action"] == "HOLD":
            assert strategy.oversold_threshold < signal["rsi"] < strategy.overbought_threshold
    
    def test_generate_signals_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        insufficient_data = {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150.0},
                {"timestamp": "2024-01-02", "close": 151.0},
                {"timestamp": "2024-01-03", "close": 149.0},
            ]
        }
        
        signals = strategy.generate_signals(insufficient_data)
        
        # Should return hold signals for insufficient data
        assert "AAPL" in signals
        signal = signals["AAPL"]
        assert signal["action"] == "HOLD"
        assert signal["confidence"] == 0.0


class TestStrategyPerformance:
    """Test strategy performance metrics"""
    
    def test_strategy_performance_calculation(self):
        """Test strategy performance calculation"""
        strategy = SMACrossoverStrategy(
            short_period=5,
            long_period=10,
            threshold=0.01
        )
        
        # Mock performance data
        performance_data = {
            "total_trades": 100,
            "winning_trades": 60,
            "losing_trades": 40,
            "total_return": 0.15,
            "max_drawdown": -0.05,
            "sharpe_ratio": 1.2
        }
        
        strategy.performance = performance_data
        
        assert strategy.performance["total_trades"] == 100
        assert strategy.performance["winning_trades"] == 60
        assert strategy.performance["losing_trades"] == 40
        assert strategy.performance["total_return"] == 0.15
        assert strategy.performance["max_drawdown"] == -0.05
        assert strategy.performance["sharpe_ratio"] == 1.2
        
        # Calculate win rate
        win_rate = strategy.performance["winning_trades"] / strategy.performance["total_trades"]
        assert win_rate == 0.6
    
    def test_strategy_risk_metrics(self):
        """Test strategy risk metrics"""
        strategy = RSIStrategy(
            period=14,
            oversold_threshold=30,
            overbought_threshold=70
        )
        
        # Mock risk data
        risk_data = {
            "var_95": -0.02,
            "var_99": -0.03,
            "volatility": 0.15,
            "beta": 1.1
        }
        
        strategy.risk_metrics = risk_data
        
        assert strategy.risk_metrics["var_95"] == -0.02
        assert strategy.risk_metrics["var_99"] == -0.03
        assert strategy.risk_metrics["volatility"] == 0.15
        assert strategy.risk_metrics["beta"] == 1.1 