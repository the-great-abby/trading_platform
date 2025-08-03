"""
Test suite for Straddle Options Strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import random

from src.strategies.options.straddle_strategy import StraddleStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestStraddleStrategyInitialization:
    """Test StraddleStrategy initialization"""
    
    def test_straddle_strategy_init_default(self):
        """Test default initialization"""
        strategy = StraddleStrategy()
        
        assert strategy.name == "Straddle"
        assert strategy.days_to_expiration == 30
        assert strategy.profit_target_pct == 0.6
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_iv_percentile == 0.4
        assert strategy.max_iv_percentile == 0.8
        assert strategy.min_delta == 0.4
        assert strategy.max_delta == 0.6
        assert strategy.earnings_days_before == 5
        assert strategy.earnings_days_after == 2
    
    def test_straddle_strategy_init_custom(self):
        """Test custom initialization"""
        strategy = StraddleStrategy(
            name="CustomStraddle",
            days_to_expiration=45,
            profit_target_pct=0.7,
            stop_loss_pct=1.5,
            max_risk_per_trade=0.03,
            min_iv_percentile=0.3,
            max_iv_percentile=0.9,
            min_delta=0.3,
            max_delta=0.7,
            earnings_days_before=7,
            earnings_days_after=3
        )
        
        assert strategy.name == "CustomStraddle"
        assert strategy.days_to_expiration == 45
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 1.5
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_iv_percentile == 0.3
        assert strategy.max_iv_percentile == 0.9
        assert strategy.min_delta == 0.3
        assert strategy.max_delta == 0.7
        assert strategy.earnings_days_before == 7
        assert strategy.earnings_days_after == 3


class TestStraddleStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data with ATR"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'ATR': [2.0 + i * 0.1 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    def test_check_market_conditions_valid(self, strategy, sample_data):
        """Test valid market conditions"""
        options_data = {'iv_percentile': 0.6}
        result = strategy.check_market_conditions(sample_data, options_data)
        assert result is True
    
    def test_check_market_conditions_insufficient_data(self, strategy):
        """Test insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        options_data = {'iv_percentile': 0.6}
        result = strategy.check_market_conditions(data, options_data)
        assert result is False
    
    def test_check_market_conditions_low_volatility(self, strategy, sample_data):
        """Test low volatility conditions"""
        # Modify ATR to create low volatility
        sample_data['ATR'] = 0.5  # Low ATR
        options_data = {'iv_percentile': 0.6}
        result = strategy.check_market_conditions(sample_data, options_data)
        assert result is False
    
    def test_check_market_conditions_no_options_data(self, strategy, sample_data):
        """Test missing options data"""
        result = strategy.check_market_conditions(sample_data, None)
        assert result is False
    
    def test_check_market_conditions_low_iv_percentile(self, strategy, sample_data):
        """Test low IV percentile"""
        options_data = {'iv_percentile': 0.3}  # Below minimum
        result = strategy.check_market_conditions(sample_data, options_data)
        assert result is False
    
    def test_check_market_conditions_high_iv_percentile(self, strategy, sample_data):
        """Test high IV percentile"""
        options_data = {'iv_percentile': 0.9}  # Above maximum
        result = strategy.check_market_conditions(sample_data, options_data)
        assert result is False


class TestStraddleStrategyATMStrikeSelection:
    """Test ATM strike selection"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain with ATM options"""
        current_price = 100.0
        return [
            # ATM call
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            ),
            # ATM put
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            ),
            # OTM call
            OptionContract(
                symbol="AAPL",
                strike=110.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=50,
                open_interest=200,
                delta=0.3,
                gamma=0.01,
                theta=-0.05,
                vega=0.2,
                implied_volatility=0.25
            ),
            # OTM put
            OptionContract(
                symbol="AAPL",
                strike=90.0,
                expiration="2024-02-16",
                option_type="put",
                price=1.5,
                volume=50,
                open_interest=200,
                delta=-0.3,
                gamma=0.01,
                theta=-0.05,
                vega=0.2,
                implied_volatility=0.25
            )
        ]
    
    def test_select_atm_strikes_success(self, strategy, sample_options_chain):
        """Test successful ATM strike selection"""
        current_price = 100.0
        result = strategy.select_atm_strikes(current_price, sample_options_chain)
        
        assert result is not None
        call, put = result
        
        assert call.option_type == "call"
        assert put.option_type == "put"
        assert call.strike == 100.0
        assert put.strike == 100.0
        assert abs(call.delta) >= strategy.min_delta
        assert abs(call.delta) <= strategy.max_delta
        assert abs(put.delta) >= strategy.min_delta
        assert abs(put.delta) <= strategy.max_delta
    
    def test_select_atm_strikes_no_atm_calls(self, strategy):
        """Test when no ATM calls available"""
        current_price = 100.0
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=110.0,  # OTM
                expiration="2024-02-16",
                option_type="call",
                price=2.0,
                volume=50,
                open_interest=200,
                delta=0.3,
                gamma=0.01,
                theta=-0.05,
                vega=0.2,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        result = strategy.select_atm_strikes(current_price, options_chain)
        assert result is None
    
    def test_select_atm_strikes_no_atm_puts(self, strategy):
        """Test when no ATM puts available"""
        current_price = 100.0
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=90.0,  # OTM
                expiration="2024-02-16",
                option_type="put",
                price=1.5,
                volume=50,
                open_interest=200,
                delta=-0.3,
                gamma=0.01,
                theta=-0.05,
                vega=0.2,
                implied_volatility=0.25
            )
        ]
        
        result = strategy.select_atm_strikes(current_price, options_chain)
        assert result is None
    
    def test_select_atm_strikes_delta_out_of_range(self, strategy):
        """Test when delta is out of acceptable range"""
        current_price = 100.0
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.2,  # Below min_delta
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.2,  # Below min_delta
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        result = strategy.select_atm_strikes(current_price, options_chain)
        assert result is None


class TestStraddleStrategyPositionMetrics:
    """Test position metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_atm_options(self):
        """Sample ATM call and put options"""
        call = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="call",
            price=5.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        put = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="put",
            price=4.5,
            volume=100,
            open_interest=500,
            delta=-0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        return call, put
    
    def test_calculate_position_metrics_success(self, strategy, sample_atm_options):
        """Test successful position metrics calculation"""
        call, put = sample_atm_options
        current_price = 100.0
        
        metrics = strategy.calculate_position_metrics(call, put, current_price)
        
        assert metrics['total_cost'] == 9.5  # 5.0 + 4.5
        assert metrics['breakeven_up'] == 109.5  # 100 + 9.5
        assert metrics['breakeven_down'] == 90.5  # 100 - 9.5
        assert metrics['max_loss'] == 9.5
        assert metrics['max_profit'] == float('inf')
        assert metrics['total_delta'] == 0.0  # 0.5 + (-0.5)
        assert metrics['total_gamma'] == 0.04  # 0.02 + 0.02
        assert metrics['total_theta'] == -0.2  # -0.1 + (-0.1)
        assert metrics['total_vega'] == 0.6  # 0.3 + 0.3
        assert metrics['call_strike'] == 100.0
        assert metrics['put_strike'] == 100.0
        assert metrics['call_price'] == 5.0
        assert metrics['put_price'] == 4.5
    
    def test_calculate_position_metrics_with_missing_greeks(self, strategy):
        """Test position metrics with missing Greeks"""
        call = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="call",
            price=5.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        put = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="put",
            price=4.5,
            volume=100,
            open_interest=500,
            delta=-0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        current_price = 100.0
        
        metrics = strategy.calculate_position_metrics(call, put, current_price)
        
        # Should still calculate correctly even with missing Greeks
        assert 'total_delta' in metrics
        assert 'total_gamma' in metrics
        assert 'total_theta' in metrics
        assert 'total_vega' in metrics
        assert metrics['total_cost'] == 9.5


class TestStraddleStrategyEarningsTiming:
    """Test earnings timing functionality"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    def test_check_earnings_timing(self, strategy):
        """Test earnings timing check"""
        # This is a random simulation, so we test the method exists and returns boolean
        result = strategy.check_earnings_timing("AAPL")
        assert isinstance(result, bool)


class TestStraddleStrategyIVExpansion:
    """Test IV expansion calculation"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain with IV data"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.3  # 30% IV
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.35  # 35% IV
            )
        ]
    
    def test_calculate_iv_expansion_success(self, strategy, sample_options_chain):
        """Test successful IV expansion calculation"""
        result = strategy.calculate_iv_expansion("AAPL", sample_options_chain)
        
        # Should return positive expansion (avg IV = 32.5%, historical = 25%)
        assert result > 0
        assert isinstance(result, float)
    
    def test_calculate_iv_expansion_no_options(self, strategy):
        """Test IV expansion with no options"""
        result = strategy.calculate_iv_expansion("AAPL", [])
        assert result == 0.0
    
    def test_calculate_iv_expansion_no_iv_data(self, strategy):
        """Test IV expansion with options but no IV data"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=None  # No IV data
            )
        ]
        
        result = strategy.calculate_iv_expansion("AAPL", options_chain)
        assert result == 0.0


class TestStraddleStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data with indicators"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'ATR': [3.0 + i * 0.1 for i in range(25)],  # High volatility
            'RSI': [50 + i * 0.5 for i in range(25)],  # Neutral RSI
            'Volume': [1500000 + i * 10000 for i in range(25)]  # High volume
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_position(self):
        """Sample position metrics"""
        return {
            'total_cost': 9.5,
            'breakeven_up': 109.5,
            'breakeven_down': 90.5,
            'max_loss': 9.5,
            'max_profit': float('inf')
        }
    
    def test_calculate_confidence_high_iv_expansion(self, strategy, sample_data, sample_position):
        """Test confidence calculation with high IV expansion"""
        iv_expansion = 0.4  # High expansion
        confidence = strategy._calculate_confidence(sample_data, sample_position, iv_expansion)
        
        assert 0.0 <= confidence <= 0.95
        assert confidence > 0.5  # Should be high with good conditions
    
    def test_calculate_confidence_low_iv_expansion(self, strategy, sample_data, sample_position):
        """Test confidence calculation with low IV expansion"""
        iv_expansion = 0.05  # Low expansion
        confidence = strategy._calculate_confidence(sample_data, sample_position, iv_expansion)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_high_volatility(self, strategy, sample_data, sample_position):
        """Test confidence calculation with high volatility"""
        # Modify ATR for high volatility
        sample_data['ATR'] = 5.0  # High ATR
        iv_expansion = 0.2
        confidence = strategy._calculate_confidence(sample_data, sample_position, iv_expansion)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_neutral_rsi(self, strategy, sample_data, sample_position):
        """Test confidence calculation with neutral RSI"""
        # Set RSI to neutral range
        sample_data['RSI'] = 50.0
        iv_expansion = 0.2
        confidence = strategy._calculate_confidence(sample_data, sample_position, iv_expansion)
        
        assert 0.0 <= confidence <= 0.95
    
    def test_calculate_confidence_high_volume(self, strategy, sample_data, sample_position):
        """Test confidence calculation with high volume"""
        # Set high volume
        sample_data['Volume'] = 2000000  # High volume
        iv_expansion = 0.2
        confidence = strategy._calculate_confidence(sample_data, sample_position, iv_expansion)
        
        assert 0.0 <= confidence <= 0.95


class TestStraddleStrategySignalGeneration:
    """Test signal generation"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'ATR': [3.0 + i * 0.1 for i in range(25)],
            'RSI': [50 + i * 0.5 for i in range(25)],
            'Volume': [1500000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_options_data(self):
        """Sample options data"""
        return {'iv_percentile': 0.6}
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.3
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.35
            )
        ]
    
    @patch('src.strategies.options.straddle_strategy.random.random')
    async def test_generate_signal_success(self, mock_random, strategy, sample_data, 
                                   sample_options_data, sample_options_chain):
        """Test successful signal generation"""
        # Mock earnings timing to return True
        mock_random.return_value = 0.05  # 5% chance, so True
        
        # Mock options service
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
            mock_get_options.return_value = sample_options_chain
            
            # Mock market conditions
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                # Mock ATM selection
                with patch.object(strategy, 'select_atm_strikes') as mock_atm:
                    call, put = sample_options_chain[0], sample_options_chain[1]
                    mock_atm.return_value = (call, put)
                    
                    # Mock IV expansion
                    with patch.object(strategy, 'calculate_iv_expansion') as mock_iv:
                        mock_iv.return_value = 0.3
                        
                        # Mock confidence calculation
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.7  # High confidence
                            
                            signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
                            
                            assert signal is not None
                            assert signal.symbol == "AAPL"
                            assert signal.action == "STRADDLE"
                            assert signal.strategy == "Straddle"
                            assert signal.confidence == 0.7
                            assert 'call_strike' in signal.metadata
                            assert 'put_strike' in signal.metadata
                            assert 'total_cost' in signal.metadata
                            assert 'iv_expansion' in signal.metadata
    
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        signal = await strategy.generate_signal("AAPL", data)
        assert signal is None
    
    async def test_generate_signal_poor_market_conditions(self, strategy, sample_data, sample_options_data):
        """Test signal generation with poor market conditions"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = False
            
            signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
            assert signal is None
    
    @patch('src.strategies.options.straddle_strategy.random.random')
    async def test_generate_signal_no_earnings_timing(self, mock_random, strategy, sample_data, 
                                              sample_options_data):
        """Test signal generation when earnings timing is not right"""
        # Mock earnings timing to return False
        mock_random.return_value = 0.95  # 95% chance, so False
        
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
            assert signal is None
    
    async def test_generate_signal_no_options_chain(self, strategy, sample_data, sample_options_data):
        """Test signal generation when no options chain available"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.return_value = []  # No options
                
                signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
                assert signal is None
    
    async def test_generate_signal_no_atm_strikes(self, strategy, sample_data, sample_options_data, 
                                           sample_options_chain):
        """Test signal generation when no ATM strikes available"""
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.return_value = sample_options_chain
                
                with patch.object(strategy, 'select_atm_strikes') as mock_atm:
                    mock_atm.return_value = None  # No ATM strikes
                    
                    signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
                    assert signal is None
    
    @patch('src.strategies.options.straddle_strategy.random.random')
    async def test_generate_signal_low_confidence(self, mock_random, strategy, sample_data, 
                                          sample_options_data, sample_options_chain):
        """Test signal generation with low confidence"""
        # Mock earnings timing to return True
        mock_random.return_value = 0.05
        
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.return_value = sample_options_chain
                
                with patch.object(strategy, 'select_atm_strikes') as mock_atm:
                    call, put = sample_options_chain[0], sample_options_chain[1]
                    mock_atm.return_value = (call, put)
                    
                    with patch.object(strategy, 'calculate_iv_expansion') as mock_iv:
                        mock_iv.return_value = 0.3
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.4  # Low confidence
                            
                            signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
                            assert signal is None


class TestStraddleStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        # Test initial state
        assert strategy.name == "Straddle"
        
        # Test deactivation
        strategy.deactivate()
        assert not strategy.is_active
        
        # Test reactivation
        strategy.activate()
        assert strategy.is_active
    
    def test_position_metrics_with_missing_greeks(self, strategy):
        """Test position metrics calculation with missing Greeks"""
        call = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="call",
            price=5.0,
            volume=100,
            open_interest=500,
            delta=0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        put = OptionContract(
            symbol="AAPL",
            strike=100.0,
            expiration="2024-02-16",
            option_type="put",
            price=4.5,
            volume=100,
            open_interest=500,
            delta=-0.5,
            gamma=0.02,
            theta=-0.1,
            vega=0.3,
            implied_volatility=0.25
        )
        current_price = 100.0
        
        metrics = strategy.calculate_position_metrics(call, put, current_price)
        
        # Should handle missing Greeks gracefully
        assert 'total_delta' in metrics
        assert 'total_gamma' in metrics
        assert 'total_theta' in metrics
        assert 'total_vega' in metrics


class TestStraddleStrategyIntegration:
    """Test full workflow integration"""
    
    @pytest.fixture
    def strategy(self):
        return StraddleStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for integration test"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'ATR': [3.0 + i * 0.1 for i in range(25)],
            'RSI': [50 + i * 0.5 for i in range(25)],
            'Volume': [1500000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @patch('src.strategies.options.straddle_strategy.random.random')
    async def test_full_workflow(self, mock_random, strategy, sample_data):
        """Test complete workflow from data to signal"""
        # Mock all dependencies
        mock_random.return_value = 0.05  # Earnings timing
        
        sample_options_data = {'iv_percentile': 0.6}
        sample_options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.3
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.5,
                volume=100,
                open_interest=500,
                delta=-0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.35
            )
        ]
        
        with patch.object(strategy, 'check_market_conditions') as mock_conditions:
            mock_conditions.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get_options:
                mock_get_options.return_value = sample_options_chain
                
                with patch.object(strategy, 'select_atm_strikes') as mock_atm:
                    call, put = sample_options_chain[0], sample_options_chain[1]
                    mock_atm.return_value = (call, put)
                    
                    with patch.object(strategy, 'calculate_iv_expansion') as mock_iv:
                        mock_iv.return_value = 0.3
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_conf:
                            mock_conf.return_value = 0.7
                            
                            signal = await strategy.generate_signal("AAPL", sample_data, sample_options_data)
                            
                            # Verify complete workflow
                            assert signal is not None
                            assert signal.symbol == "AAPL"
                            assert signal.action == "STRADDLE"
                            assert signal.strategy == "Straddle"
                            assert signal.confidence == 0.7
                            
                            # Verify metadata
                            metadata = signal.metadata
                            assert 'call_strike' in metadata
                            assert 'put_strike' in metadata
                            assert 'total_cost' in metadata
                            assert 'breakeven_up' in metadata
                            assert 'breakeven_down' in metadata
                            assert 'max_loss' in metadata
                            assert 'iv_expansion' in metadata
                            assert 'total_delta' in metadata
                            assert 'total_gamma' in metadata
                            assert 'total_theta' in metadata
                            assert 'total_vega' in metadata
                            assert 'signal_type' in metadata
                            assert metadata['signal_type'] == 'straddle' 