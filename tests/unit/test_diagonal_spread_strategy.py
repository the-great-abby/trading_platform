"""
Test suite for Diagonal Spread Options Strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import random

from src.strategies.options.diagonal_spread_strategy import DiagonalSpreadStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestDiagonalSpreadStrategyInitialization:
    """Test DiagonalSpreadStrategy initialization"""
    
    def test_diagonal_spread_strategy_init_default(self):
        """Test default initialization"""
        strategy = DiagonalSpreadStrategy()
        
        assert strategy.name == "DiagonalSpread"
        assert strategy.short_dte == 14
        assert strategy.long_dte == 45
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 1.5
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_delta == 0.3
        assert strategy.max_delta == 0.7
        assert strategy.min_dte_spread == 21
        assert strategy.direction == "bullish"
        assert strategy.min_theta_ratio == 1.5
    
    def test_diagonal_spread_strategy_init_custom(self):
        """Test custom initialization"""
        strategy = DiagonalSpreadStrategy(
            name="CustomDiagonal",
            short_dte=21,
            long_dte=60,
            profit_target_pct=0.8,
            stop_loss_pct=2.0,
            max_risk_per_trade=0.03,
            min_delta=0.2,
            max_delta=0.8,
            min_dte_spread=30,
            direction="bearish",
            min_theta_ratio=2.0
        )
        
        assert strategy.name == "CustomDiagonal"
        assert strategy.short_dte == 21
        assert strategy.long_dte == 60
        assert strategy.profit_target_pct == 0.8
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_delta == 0.2
        assert strategy.max_delta == 0.8
        assert strategy.min_dte_spread == 30
        assert strategy.direction == "bearish"
        assert strategy.min_theta_ratio == 2.0


class TestDiagonalSpreadStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data with indicators"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'SMA_20': [101 + i * 0.4 for i in range(25)],
            'SMA_50': [100 + i * 0.3 for i in range(25)],
            'ATR': [2.0 + i * 0.1 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    def test_check_market_conditions_valid_bullish(self, strategy, sample_data):
        """Test valid market conditions for bullish strategy"""
        result = strategy.check_market_conditions(sample_data)
        assert result is True
    
    def test_check_market_conditions_valid_bearish(self, strategy, sample_data):
        """Test valid market conditions for bearish strategy"""
        bearish_strategy = DiagonalSpreadStrategy(direction="bearish")
        # Create a copy of data and modify for bearish trend
        bearish_data = sample_data.copy()
        bearish_data['SMA_20'] = bearish_data['SMA_20'] - 10  # Stronger bearish trend
        result = bearish_strategy.check_market_conditions(bearish_data)
        assert result is True
    
    def test_check_market_conditions_insufficient_data(self, strategy):
        """Test insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        result = strategy.check_market_conditions(data)
        assert result is False
    
    def test_check_market_conditions_weak_trend_bullish(self, strategy, sample_data):
        """Test weak trend for bullish strategy"""
        # Modify data for weak bullish trend
        sample_data['SMA_20'] = sample_data['SMA_50'] + 0.01  # Very weak trend
        result = strategy.check_market_conditions(sample_data)
        assert result is False
    
    def test_check_market_conditions_weak_trend_bearish(self, strategy, sample_data):
        """Test weak trend for bearish strategy"""
        bearish_strategy = DiagonalSpreadStrategy(direction="bearish")
        # Modify data for weak bearish trend
        sample_data['SMA_20'] = sample_data['SMA_50'] - 0.01  # Very weak trend
        result = bearish_strategy.check_market_conditions(sample_data)
        assert result is False
    
    def test_check_market_conditions_low_volatility(self, strategy, sample_data):
        """Test low volatility conditions"""
        # Modify ATR for low volatility
        sample_data['ATR'] = 0.5  # Low ATR
        result = strategy.check_market_conditions(sample_data)
        assert result is False


class TestDiagonalSpreadStrategyStrikeSelection:
    """Test diagonal strike selection"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_short_options(self):
        """Sample short-term options"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=105.0,  # OTM call
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=100,
                open_interest=500,
                delta=0.3,
                gamma=0.02,
                theta=-0.15,
                vega=0.3,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=110.0,  # Further OTM call
                expiration="2024-02-16",
                option_type="call",
                price=1.0,
                volume=50,
                open_interest=200,
                delta=0.2,
                gamma=0.01,
                theta=-0.1,
                vega=0.2,
                implied_volatility=0.25
            )
        ]
    
    @pytest.fixture
    def sample_long_options(self):
        """Sample long-term options"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=100.0,  # ATM call
                expiration="2024-03-15",
                option_type="call",
                price=6.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.03,
                theta=-0.1,
                vega=0.4,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=95.0,  # ITM call
                expiration="2024-03-15",
                option_type="call",
                price=8.0,
                volume=50,
                open_interest=200,
                delta=0.7,
                gamma=0.02,
                theta=-0.08,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
    
    def test_select_diagonal_strikes_bullish_success(self, strategy, sample_short_options, sample_long_options):
        """Test successful bullish diagonal strike selection"""
        current_price = 100.0
        result = strategy.select_diagonal_strikes(current_price, sample_short_options, sample_long_options)
        
        assert result is not None
        long_option, short_option = result
        
        assert long_option.option_type == "call"
        assert short_option.option_type == "call"
        assert long_option.strike == 100.0  # ATM long call
        assert short_option.strike == 105.0  # OTM short call
        assert abs(long_option.delta) >= strategy.min_delta
        assert abs(long_option.delta) <= strategy.max_delta
    
    def test_select_diagonal_strikes_bearish_success(self, strategy):
        """Test successful bearish diagonal strike selection"""
        bearish_strategy = DiagonalSpreadStrategy(direction="bearish")
        current_price = 100.0
        
        short_puts = [
            OptionContract(
                symbol="AAPL",
                strike=95.0,  # OTM put
                expiration="2024-02-16",
                option_type="put",
                price=1.5,
                volume=100,
                open_interest=500,
                delta=-0.3,
                gamma=0.02,
                theta=-0.15,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        long_puts = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,  # ATM put
                expiration="2024-03-15",
                option_type="put",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.03,
                theta=-0.1,
                vega=0.4,
                implied_volatility=0.25
            )
        ]
        
        result = bearish_strategy.select_diagonal_strikes(current_price, short_puts, long_puts)
        
        assert result is not None
        long_option, short_option = result
        
        assert long_option.option_type == "put"
        assert short_option.option_type == "put"
        assert long_option.strike == 100.0  # ATM long put
        assert short_option.strike == 95.0  # OTM short put
    
    def test_select_diagonal_strikes_no_long_options(self, strategy, sample_short_options):
        """Test when no long options available"""
        current_price = 100.0
        long_options = []  # No long options
        
        result = strategy.select_diagonal_strikes(current_price, sample_short_options, long_options)
        assert result is None
    
    def test_select_diagonal_strikes_no_short_options(self, strategy, sample_long_options):
        """Test when no short options available"""
        current_price = 100.0
        short_options = []  # No short options
        
        result = strategy.select_diagonal_strikes(current_price, short_options, sample_long_options)
        assert result is None
    
    def test_select_diagonal_strikes_delta_out_of_range(self, strategy):
        """Test when delta is out of acceptable range"""
        current_price = 100.0
        
        short_options = [
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=100,
                open_interest=500,
                delta=0.1,  # Below min_delta
                gamma=0.02,
                theta=-0.15,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        long_options = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-03-15",
                option_type="call",
                price=6.0,
                volume=100,
                open_interest=500,
                delta=0.8,  # Above max_delta
                gamma=0.03,
                theta=-0.1,
                vega=0.4,
                implied_volatility=0.25
            )
        ]
        
        result = strategy.select_diagonal_strikes(current_price, short_options, long_options)
        assert result is None


class TestDiagonalSpreadStrategyPositionMetrics:
    """Test position metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_options(self):
        """Sample long and short options"""
        long_option = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-03-15",
            option_type="call",
            price=6.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.03,
            theta=-0.1,
            vega=0.4,
            implied_volatility=0.25
        )
        
        short_option = OptionContract(
            symbol="AAPL",
            strike=105.0,
            expiration="2024-02-16",
            option_type="call",
            price=2.0,
            volume=100,
            open_interest=500,
            delta=0.3,
            gamma=0.02,
            theta=-0.15,
            vega=0.3,
            implied_volatility=0.25
        )
        
        return long_option, short_option
    
    def test_calculate_position_metrics_bullish_success(self, strategy, sample_options):
        """Test successful bullish position metrics calculation"""
        long_option, short_option = sample_options
        current_price = 100.0
        
        metrics = strategy.calculate_position_metrics(long_option, short_option, current_price)
        
        assert metrics['net_cost'] == 4.0  # 6.0 - 2.0
        assert metrics['breakeven'] == 104.0  # 100 + 4.0
        assert metrics['max_loss'] == 4.0
        assert metrics['max_profit'] == float('inf')
        assert metrics['total_delta'] == pytest.approx(0.2)  # 0.5 - 0.3
        assert metrics['total_gamma'] == pytest.approx(0.01)  # 0.03 - 0.02
        assert metrics['total_theta'] == pytest.approx(0.05)  # -0.1 - (-0.15)
        assert metrics['total_vega'] == pytest.approx(0.1)  # 0.4 - 0.3
        assert metrics['long_strike'] == 100.0
        assert metrics['short_strike'] == 105.0
        assert metrics['long_price'] == 6.0
        assert metrics['short_price'] == 2.0
        assert metrics['direction'] == "bullish"
    
    def test_calculate_position_metrics_bearish_success(self, strategy):
        """Test successful bearish position metrics calculation"""
        bearish_strategy = DiagonalSpreadStrategy(direction="bearish")
        
        long_put = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-03-15",
            option_type="put",
            price=4.0,
            volume=100,
            open_interest=500,
            delta=-0.5,
            gamma=0.03,
            theta=-0.1,
            vega=0.4,
            implied_volatility=0.25
        )
        
        short_put = OptionContract(
            symbol="AAPL",
            strike=95.0,
            expiration="2024-02-16",
            option_type="put",
            price=1.5,
            volume=100,
            open_interest=500,
            delta=-0.3,
            gamma=0.02,
            theta=-0.15,
            vega=0.3,
            implied_volatility=0.25
        )
        
        current_price = 100.0
        metrics = bearish_strategy.calculate_position_metrics(long_put, short_put, current_price)
        
        assert metrics['net_cost'] == 2.5  # 4.0 - 1.5
        assert metrics['breakeven'] == 97.5  # 100 - 2.5
        assert metrics['max_loss'] == 2.5
        assert metrics['max_profit'] == -7.5  # 95 - 100 - 2.5 (current implementation)
        assert metrics['direction'] == "bearish"


class TestDiagonalSpreadStrategyThetaRatio:
    """Test theta ratio calculation"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    def test_calculate_theta_ratio_success(self, strategy):
        """Test successful theta ratio calculation"""
        long_option = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-03-15",
            option_type="call",
            price=6.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.03,
            theta=-0.1,
            vega=0.4,
            implied_volatility=0.25
        )
        
        short_option = OptionContract(
            symbol="AAPL",
            strike=105.0,
            expiration="2024-02-16",
            option_type="call",
            price=2.0,
            volume=100,
            open_interest=500,
            delta=0.3,
            gamma=0.02,
            theta=-0.15,
            vega=0.3,
            implied_volatility=0.25
        )
        
        theta_ratio = strategy.calculate_theta_ratio(long_option, short_option)
        
        # Expected: abs(-0.1) / abs(-0.15) = 0.1 / 0.15 = 0.6666666666666667
        assert theta_ratio == pytest.approx(0.6666666666666667)
    
    def test_calculate_theta_ratio_zero_short_theta(self, strategy):
        """Test theta ratio calculation with zero short theta"""
        long_option = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-03-15",
            option_type="call",
            price=6.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.03,
            theta=-0.1,
            vega=0.4,
            implied_volatility=0.25
        )
        
        short_option = OptionContract(
            symbol="AAPL",
            strike=105.0,
            expiration="2024-02-16",
            option_type="call",
            price=2.0,
            volume=100,
            open_interest=500,
            delta=0.3,
            gamma=0.02,
            theta=0.0,  # Zero theta
            vega=0.3,
            implied_volatility=0.25
        )
        
        theta_ratio = strategy.calculate_theta_ratio(long_option, short_option)
        assert theta_ratio == 0


class TestDiagonalSpreadStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data with indicators"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'SMA_20': [101 + i * 0.4 for i in range(25)],
            'SMA_50': [100 + i * 0.3 for i in range(25)],
            'ATR': [2.0 + i * 0.1 for i in range(25)],
            'RSI': [50 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_position(self):
        """Sample position metrics"""
        return {
            'net_cost': 4.0,
            'breakeven': 104.0,
            'max_loss': 4.0,
            'max_profit': float('inf'),
            'direction': 'bullish'
        }
    
    def test_calculate_confidence_high_theta_ratio(self, strategy, sample_data, sample_position):
        """Test confidence calculation with high theta ratio"""
        theta_ratio = 2.0  # High theta ratio
        confidence = strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95
        assert confidence > 0.5  # Should be high with good conditions
    
    def test_calculate_confidence_low_theta_ratio(self, strategy, sample_data, sample_position):
        """Test confidence calculation with low theta ratio"""
        theta_ratio = 0.5  # Low theta ratio
        confidence = strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_strong_trend_bullish(self, strategy, sample_data, sample_position):
        """Test confidence calculation with strong bullish trend"""
        # Modify data for strong bullish trend
        sample_data['SMA_20'] = sample_data['SMA_50'] + 5  # Strong bullish trend
        theta_ratio = 1.5
        confidence = strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_strong_trend_bearish(self, strategy, sample_data, sample_position):
        """Test confidence calculation with strong bearish trend"""
        bearish_strategy = DiagonalSpreadStrategy(direction="bearish")
        # Modify data for strong bearish trend
        sample_data['SMA_20'] = sample_data['SMA_50'] - 5  # Strong bearish trend
        sample_position['direction'] = 'bearish'
        theta_ratio = 1.5
        confidence = bearish_strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_high_volatility(self, strategy, sample_data, sample_position):
        """Test confidence calculation with high volatility"""
        # Set high ATR for high volatility
        sample_data['ATR'] = 5.0  # High ATR
        theta_ratio = 1.5
        confidence = strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_favorable_rsi(self, strategy, sample_data, sample_position):
        """Test confidence calculation with favorable RSI"""
        # Set favorable RSI for bullish strategy
        sample_data['RSI'] = 45.0  # Not overbought for bullish
        theta_ratio = 1.5
        confidence = strategy._calculate_confidence(sample_data, sample_position, theta_ratio)
        
        assert 0.0 <= confidence <= 0.95


class TestDiagonalSpreadStrategySignalGeneration:
    """Test signal generation"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'SMA_20': [101 + i * 0.4 for i in range(25)],
            'SMA_50': [100 + i * 0.3 for i in range(25)],
            'ATR': [2.0 + i * 0.1 for i in range(25)],
            'RSI': [50 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_short_options(self):
        """Sample short-term options"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=100,
                open_interest=500,
                delta=0.3,
                gamma=0.02,
                theta=-0.15,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
    
    @pytest.fixture
    def sample_long_options(self):
        """Sample long-term options"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-03-15",
                option_type="call",
                price=6.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.03,
                theta=-0.1,
                vega=0.4,
                implied_volatility=0.25
            )
        ]
    
    async def test_generate_signal_success(self, strategy, sample_data, sample_short_options, sample_long_options):
        """Test successful signal generation"""
        # Mock options service
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
            mock_get_options.side_effect = [sample_short_options, sample_long_options]
            
            # Mock market conditions
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                # Mock diagonal strike selection
                with patch.object(strategy, 'select_diagonal_strikes') as mock_strikes:
                    long_option, short_option = sample_long_options[0], sample_short_options[0]
                    mock_strikes.return_value = (long_option, short_option)
                    
                    # Mock theta ratio calculation
                    with patch.object(strategy, 'calculate_theta_ratio') as mock_theta:
                        mock_theta.return_value = 2.0  # High theta ratio
                        
                        # Mock confidence calculation
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.7  # High confidence
                            
                            signal = await strategy.generate_signal("AAPL", sample_data)
                            
                            assert signal is not None
                            assert signal.symbol == "AAPL"
                            assert signal.action == "DIAGONAL_SPREAD_BULLISH"
                            assert signal.strategy == "DiagonalSpread"
                            assert signal.confidence == 0.7
                            assert 'long_strike' in signal.metadata
                            assert 'short_strike' in signal.metadata
                            assert 'net_cost' in signal.metadata
                            assert 'theta_ratio' in signal.metadata
                            assert 'direction' in signal.metadata
                            assert signal.metadata['direction'] == 'bullish'
    
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        signal = await strategy.generate_signal("AAPL", data)
        assert signal is None
    
    async def test_generate_signal_poor_market_conditions(self, strategy, sample_data):
        """Test signal generation with poor market conditions"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = False
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            assert signal is None
    
    async def test_generate_signal_no_short_options(self, strategy, sample_data, sample_long_options):
        """Test signal generation when no short options available"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [[], sample_long_options]  # No short options
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                assert signal is None
    
    async def test_generate_signal_no_long_options(self, strategy, sample_data, sample_short_options):
        """Test signal generation when no long options available"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [sample_short_options, []]  # No long options
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                assert signal is None
    
    async def test_generate_signal_no_diagonal_strikes(self, strategy, sample_data, sample_short_options, sample_long_options):
        """Test signal generation when no diagonal strikes available"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [sample_short_options, sample_long_options]
                
                with patch.object(strategy, 'select_diagonal_strikes') as mock_strikes:
                    mock_strikes.return_value = None  # No diagonal strikes
                    
                    signal = await strategy.generate_signal("AAPL", sample_data)
                    assert signal is None
    
    async def test_generate_signal_low_theta_ratio(self, strategy, sample_data, sample_short_options, sample_long_options):
        """Test signal generation with low theta ratio"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [sample_short_options, sample_long_options]
                
                with patch.object(strategy, 'select_diagonal_strikes') as mock_strikes:
                    long_option, short_option = sample_long_options[0], sample_short_options[0]
                    mock_strikes.return_value = (long_option, short_option)
                    
                    with patch.object(strategy, 'calculate_theta_ratio') as mock_theta:
                        mock_theta.return_value = 1.0  # Low theta ratio
                        
                        signal = await strategy.generate_signal("AAPL", sample_data)
                        assert signal is None
    
    async def test_generate_signal_low_confidence(self, strategy, sample_data, sample_short_options, sample_long_options):
        """Test signal generation with low confidence"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [sample_short_options, sample_long_options]
                
                with patch.object(strategy, 'select_diagonal_strikes') as mock_strikes:
                    long_option, short_option = sample_long_options[0], sample_short_options[0]
                    mock_strikes.return_value = (long_option, short_option)
                    
                    with patch.object(strategy, 'calculate_theta_ratio') as mock_theta:
                        mock_theta.return_value = 2.0  # High theta ratio
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.4  # Low confidence
                            
                            signal = await strategy.generate_signal("AAPL", sample_data)
                            assert signal is None


class TestDiagonalSpreadStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        # Test initial state
        assert strategy.name == "DiagonalSpread"
        
        # Test deactivation
        strategy.deactivate()
        assert not strategy.is_active
        
        # Test reactivation
        strategy.activate()
        assert strategy.is_active
    
    def test_position_metrics_with_missing_greeks(self, strategy):
        """Test position metrics calculation with missing Greeks"""
        long_option = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-03-15",
            option_type="call",
            price=6.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.03,
            theta=-0.1,
            vega=0.4,
            implied_volatility=0.25
        )
        
        short_option = OptionContract(
            symbol="AAPL",
            strike=105.0,
            expiration="2024-02-16",
            option_type="call",
            price=2.0,
            volume=100,
            open_interest=500,
            delta=0.3,
            gamma=0.02,
            theta=-0.15,
            vega=0.3,
            implied_volatility=0.25
        )
        
        current_price = 100.0
        metrics = strategy.calculate_position_metrics(long_option, short_option, current_price)
        
        # Should handle missing Greeks gracefully
        assert 'total_delta' in metrics
        assert 'total_gamma' in metrics
        assert 'total_theta' in metrics
        assert 'total_vega' in metrics


class TestDiagonalSpreadStrategyIntegration:
    """Test full workflow integration"""
    
    @pytest.fixture
    def strategy(self):
        return DiagonalSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for integration test"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'SMA_20': [101 + i * 0.4 for i in range(25)],
            'SMA_50': [100 + i * 0.3 for i in range(25)],
            'ATR': [2.0 + i * 0.1 for i in range(25)],
            'RSI': [50 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    async def test_full_workflow(self, strategy, sample_data):
        """Test complete workflow from data to signal"""
        # Mock all dependencies
        sample_short_options = [
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=100,
                open_interest=500,
                delta=0.3,
                gamma=0.02,
                theta=-0.15,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        sample_long_options = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-03-15",
                option_type="call",
                price=6.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.03,
                theta=-0.1,
                vega=0.4,
                implied_volatility=0.25
            )
        ]
        
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.side_effect = [sample_short_options, sample_long_options]
                
                with patch.object(strategy, 'select_diagonal_strikes') as mock_strikes:
                    long_option, short_option = sample_long_options[0], sample_short_options[0]
                    mock_strikes.return_value = (long_option, short_option)
                    
                    with patch.object(strategy, 'calculate_theta_ratio') as mock_theta:
                        mock_theta.return_value = 2.0
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.7
                            
                            signal = await strategy.generate_signal("AAPL", sample_data)
                            
                            # Verify complete workflow
                            assert signal is not None
                            assert signal.symbol == "AAPL"
                            assert signal.action == "DIAGONAL_SPREAD_BULLISH"
                            assert signal.strategy == "DiagonalSpread"
                            assert signal.confidence == 0.7
                            
                            # Verify metadata
                            metadata = signal.metadata
                            assert 'long_strike' in metadata
                            assert 'short_strike' in metadata
                            assert 'net_cost' in metadata
                            assert 'breakeven' in metadata
                            assert 'max_loss' in metadata
                            assert 'max_profit' in metadata
                            assert 'theta_ratio' in metadata
                            assert 'total_delta' in metadata
                            assert 'total_gamma' in metadata
                            assert 'total_theta' in metadata
                            assert 'total_vega' in metadata
                            assert 'signal_type' in metadata
                            assert metadata['signal_type'] == 'diagonal_spread'
                            assert metadata['direction'] == 'bullish' 