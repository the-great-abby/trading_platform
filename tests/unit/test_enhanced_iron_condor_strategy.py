"""
Test suite for Enhanced Iron Condor Options Strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, date
import logging

from src.strategies.options.enhanced_iron_condor_strategy import EnhancedIronCondorStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestEnhancedIronCondorStrategyInitialization:
    """Test EnhancedIronCondorStrategy initialization"""
    
    def test_enhanced_iron_condor_strategy_init_default(self):
        """Test default initialization"""
        strategy = EnhancedIronCondorStrategy()
        
        assert strategy.name == "EnhancedIronCondor"
        assert strategy.days_to_expiration == 45
        assert strategy.profit_target_pct == 0.5
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.volatility_threshold == 0.3
        assert strategy.min_dte == 30
        assert strategy.max_dte == 60
        assert strategy.min_volume == 10
        assert strategy.min_open_interest == 50
        assert strategy.cache_lookback_days == 30
    
    def test_enhanced_iron_condor_strategy_init_custom(self):
        """Test custom initialization"""
        strategy = EnhancedIronCondorStrategy(
            name="CustomEnhancedIronCondor",
            days_to_expiration=60,
            profit_target_pct=0.6,
            stop_loss_pct=2.5,
            max_risk_per_trade=0.03,
            volatility_threshold=0.25,
            min_dte=45,
            max_dte=90,
            min_volume=20,
            min_open_interest=100,
            cache_lookback_days=45
        )
        
        assert strategy.name == "CustomEnhancedIronCondor"
        assert strategy.days_to_expiration == 60
        assert strategy.profit_target_pct == 0.6
        assert strategy.stop_loss_pct == 2.5
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.volatility_threshold == 0.25
        assert strategy.min_dte == 45
        assert strategy.max_dte == 90
        assert strategy.min_volume == 20
        assert strategy.min_open_interest == 100
        assert strategy.cache_lookback_days == 45


class TestEnhancedIronCondorStrategyCacheIntegration:
    """Test cache integration functionality"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    def test_get_cached_options_data_success(self, strategy):
        """Test successful cached options data retrieval"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # Mock cached data
            cached_data = [
                {'symbol': 'AAPL', 'strike': 100, 'expiration': '2024-03-15', 'option_type': 'call'},
                {'symbol': 'AAPL', 'strike': 105, 'expiration': '2024-03-15', 'option_type': 'call'}
            ]
            mock_instance.get_historical_options_data.return_value = cached_data
            
            result = strategy.get_cached_options_data('AAPL', date(2024, 1, 15))
            
            assert result == cached_data
            mock_instance.get_historical_options_data.assert_called_once_with('AAPL', date(2024, 1, 15))
    
    def test_get_cached_options_data_no_data(self, strategy):
        """Test when no cached data available"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.get_historical_options_data.return_value = None
            
            result = strategy.get_cached_options_data('AAPL', date(2024, 1, 15))
            
            assert result is None
    
    def test_get_cached_options_data_exception(self, strategy):
        """Test exception handling in cached data retrieval"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_service.side_effect = Exception("Database error")
            
            result = strategy.get_cached_options_data('AAPL', date(2024, 1, 15))
            
            assert result is None
    
    def test_get_available_expiration_dates_success(self, strategy):
        """Test successful expiration dates retrieval"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # Mock available dates and options data
            available_dates = [date(2024, 1, 15), date(2024, 1, 16)]
            mock_instance.get_available_historical_dates.return_value = available_dates
            
            options_data = [
                {'expiration': '2024-03-15'},
                {'expiration': '2024-04-19'},
                {'expiration': '2024-03-15'}  # Duplicate
            ]
            mock_instance.get_historical_options_data.return_value = options_data
            
            result = strategy.get_available_expiration_dates('AAPL')
            
            expected = ['2024-03-15', '2024-04-19']
            assert result == expected
    
    def test_get_available_expiration_dates_no_dates(self, strategy):
        """Test when no available dates"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.get_available_historical_dates.return_value = []
            
            result = strategy.get_available_expiration_dates('AAPL')
            
            assert result == []


class TestEnhancedIronCondorStrategyExpirationSelection:
    """Test expiration date selection"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    def test_find_optimal_expiration_success(self, strategy):
        """Test successful optimal expiration selection"""
        with patch.object(strategy, 'get_available_expiration_dates') as mock_get_dates:
            mock_get_dates.return_value = ['2024-02-15', '2024-03-15', '2024-04-19']
            
            # Mock datetime.now() to return a fixed date for consistent testing
            with patch('src.strategies.options.enhanced_iron_condor_strategy.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 15)
                mock_datetime.strptime = datetime.strptime
                
                # Target DTE is 45, so both Feb 15 and Mar 15 are equally close (14 days from target)
                # The algorithm will return the first one it encounters
                result = strategy.find_optimal_expiration('AAPL', 45)
                
                # Both dates are equally close to target, algorithm returns first encountered
                assert result in ['2024-02-15', '2024-03-15']
    
    def test_find_optimal_expiration_no_dates(self, strategy):
        """Test when no expiration dates available"""
        with patch.object(strategy, 'get_available_expiration_dates') as mock_get_dates:
            mock_get_dates.return_value = []
            
            result = strategy.find_optimal_expiration('AAPL', 45)
            
            assert result is None
    
    def test_find_optimal_expiration_invalid_date_format(self, strategy):
        """Test handling of invalid date format"""
        with patch.object(strategy, 'get_available_expiration_dates') as mock_get_dates:
            mock_get_dates.return_value = ['2024-02-15', 'invalid-date', '2024-04-19']
            
            result = strategy.find_optimal_expiration('AAPL', 45)
            
            # Should still find a valid date
            assert result in ['2024-02-15', '2024-04-19']


class TestEnhancedIronCondorStrategyOptionsChain:
    """Test options chain retrieval"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    def test_get_liquid_options_chain_success(self, strategy):
        """Test successful liquid options chain retrieval"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # Mock available dates and options data
            available_dates = [date(2024, 1, 15)]
            mock_instance.get_available_historical_dates.return_value = available_dates
            
            options_data = [
                {
                    'symbol': 'AAPL',
                    'strike': 100.0,
                    'expiration': '2024-03-15',
                    'option_type': 'call',
                    'price': 5.0,
                    'volume': 100,
                    'open_interest': 500,
                    'delta': 0.5,
                    'gamma': 0.02,
                    'theta': -0.1,
                    'vega': 0.3,
                    'implied_volatility': 0.25
                }
            ]
            mock_instance.get_historical_options_data.return_value = options_data
            
            result = strategy.get_liquid_options_chain('AAPL', '2024-03-15', 100.0)
            
            assert result is not None
            assert len(result) == 1
            assert isinstance(result[0], OptionContract)
            assert result[0].symbol == 'AAPL'
            assert result[0].strike == 100.0
    
    def test_get_liquid_options_chain_insufficient_liquidity(self, strategy):
        """Test when options don't meet liquidity requirements"""
        with patch('src.services.database.market_data_service.MarketDataService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            available_dates = [date(2024, 1, 15)]
            mock_instance.get_available_historical_dates.return_value = available_dates
            
            # Options with insufficient volume/open interest
            options_data = [
                {
                    'symbol': 'AAPL',
                    'strike': 100.0,
                    'expiration': '2024-03-15',
                    'option_type': 'call',
                    'price': 5.0,
                    'volume': 5,  # Below min_volume
                    'open_interest': 20,  # Below min_open_interest
                    'delta': 0.5,
                    'gamma': 0.02,
                    'theta': -0.1,
                    'vega': 0.3,
                    'implied_volatility': 0.25
                }
            ]
            mock_instance.get_historical_options_data.return_value = options_data
            
            result = strategy.get_liquid_options_chain('AAPL', '2024-03-15', 100.0)
            
            assert result == []


class TestEnhancedIronCondorStrategyImpliedVolatility:
    """Test implied volatility calculations"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain with Greeks"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-03-15",
                option_type="call",
                price=5.0,
                volume=150,
                open_interest=600,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.30
            )
        ]
    
    def test_calculate_implied_volatility_success(self, strategy, sample_options_chain):
        """Test successful implied volatility calculation"""
        iv = strategy.calculate_implied_volatility(sample_options_chain)
        
        # Weighted average: (0.25 * 100 + 0.30 * 150) / (100 + 150) = 0.28
        expected_iv = (0.25 * 100 + 0.30 * 150) / (100 + 150)
        assert abs(iv - expected_iv) < 0.01
    
    def test_calculate_implied_volatility_no_data(self, strategy):
        """Test implied volatility calculation with no data"""
        iv = strategy.calculate_implied_volatility([])
        assert iv == 0.0
    
    def test_calculate_implied_volatility_no_volume(self, strategy):
        """Test implied volatility calculation with no volume"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=100.0,
                expiration="2024-03-15",
                option_type="call",
                price=5.0,
                volume=0,  # No volume
                open_interest=500,
                delta=0.5,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        iv = strategy.calculate_implied_volatility(options_chain)
        assert iv == 0.25  # Should fall back to simple average


class TestEnhancedIronCondorStrategyStrikeSelection:
    """Test strike selection from cache"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain for strike selection"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=0.4,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
    
    def test_select_strikes_from_cache_success(self, strategy, sample_options_chain):
        """Test successful strike selection from cache"""
        with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
            mock_get_chain.return_value = sample_options_chain
            
            with patch.object(strategy, 'calculate_implied_volatility') as mock_calc_iv:
                mock_calc_iv.return_value = 0.25
                
                # Mock datetime to avoid date calculation issues
                with patch('src.strategies.options.enhanced_iron_condor_strategy.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 1, 1)
                    mock_datetime.strptime.return_value = datetime(2024, 3, 15)
                    
                    result = strategy.select_strikes_from_cache('AAPL', 100.0, '2024-03-15')
                    
                    assert result is not None
                    assert 'put_strike' in result
                    assert 'call_strike' in result
                    assert 'put_spread_width' in result
                    assert 'call_spread_width' in result
                    assert 'expected_move' in result
                    assert 'implied_volatility' in result
                    assert 'dte' in result
                    assert 'current_price' in result
                    assert result['current_price'] == 100.0
                    assert result['implied_volatility'] == 0.25
    
    def test_select_strikes_from_cache_no_options(self, strategy):
        """Test strike selection when no options available"""
        with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
            mock_get_chain.return_value = None
            
            result = strategy.select_strikes_from_cache('AAPL', 100.0, '2024-03-15')
            
            assert result is None
    
    def test_select_strikes_from_cache_no_puts(self, strategy):
        """Test strike selection when no put options available"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=0.4,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
        
        with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
            mock_get_chain.return_value = options_chain
            
            with patch.object(strategy, 'calculate_implied_volatility') as mock_calc_iv:
                mock_calc_iv.return_value = 0.25
                
                result = strategy.select_strikes_from_cache('AAPL', 100.0, '2024-03-15')
                
                assert result is None


class TestEnhancedIronCondorStrategyPositionMetrics:
    """Test position metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_strikes(self):
        """Sample strikes for position metrics"""
        return {
            'put_strike': 95.0,
            'call_strike': 105.0,
            'put_spread_width': 3.0,
            'call_spread_width': 3.0,
            'expected_move': 8.0,
            'implied_volatility': 0.25,
            'dte': 45,
            'current_price': 100.0
        }
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain for position metrics"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=0.4,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.25
            )
        ]
    
    def test_calculate_position_metrics_success(self, strategy, sample_strikes, sample_options_chain):
        """Test successful position metrics calculation"""
        metrics = strategy.calculate_position_metrics(sample_strikes, sample_options_chain)
        
        assert 'max_risk' in metrics
        assert 'max_profit' in metrics
        assert 'risk_reward_ratio' in metrics
        assert 'put_price' in metrics
        assert 'call_price' in metrics
        assert 'total_delta' in metrics
        assert 'total_gamma' in metrics
        assert 'total_theta' in metrics
        assert 'total_vega' in metrics
        assert 'implied_volatility' in metrics
        assert 'dte' in metrics
        assert metrics['put_price'] == 3.0
        assert metrics['call_price'] == 4.0
        assert metrics['implied_volatility'] == 0.25
        assert metrics['dte'] == 45
    
    def test_calculate_position_metrics_missing_prices(self, strategy, sample_strikes):
        """Test position metrics calculation with missing option prices"""
        # Options chain without matching strikes
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=90.0,  # Different strike
                expiration="2024-03-15",
                option_type="put",
                price=2.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.25
            )
        ]
        
        metrics = strategy.calculate_position_metrics(sample_strikes, options_chain)
        
        assert metrics == {}


class TestEnhancedIronCondorStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.35  # Above threshold
            )
        ]
    
    def test_check_market_conditions_valid(self, strategy, sample_data, sample_options_chain):
        """Test valid market conditions"""
        with patch.object(strategy, 'calculate_implied_volatility') as mock_calc_iv:
            mock_calc_iv.return_value = 0.35  # Above threshold
            
            result = strategy.check_market_conditions(sample_data, sample_options_chain)
            
            assert result is True
    
    def test_check_market_conditions_insufficient_data(self, strategy, sample_options_chain):
        """Test market conditions with insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        
        result = strategy.check_market_conditions(data, sample_options_chain)
        
        assert result is False
    
    def test_check_market_conditions_low_volatility(self, strategy, sample_data, sample_options_chain):
        """Test market conditions with low volatility"""
        with patch.object(strategy, 'calculate_implied_volatility') as mock_calc_iv:
            mock_calc_iv.return_value = 0.2  # Below threshold
            
            result = strategy.check_market_conditions(sample_data, sample_options_chain)
            
            assert result is False
    
    def test_check_market_conditions_strong_trend(self, strategy, sample_options_chain):
        """Test market conditions with strong trend"""
        # Create data with strong trend
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 2 for i in range(25)],  # Strong upward trend
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        
        with patch.object(strategy, 'calculate_implied_volatility') as mock_calc_iv:
            mock_calc_iv.return_value = 0.35
            
            result = strategy.check_market_conditions(data, sample_options_chain)
            
            assert result is False


class TestEnhancedIronCondorStrategySignalGeneration:
    """Test signal generation"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.35
            ),
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=0.4,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.35
            )
        ]
    
    @pytest.fixture
    def sample_strikes(self):
        """Sample strikes"""
        return {
            'put_strike': 95.0,
            'call_strike': 105.0,
            'put_spread_width': 3.0,
            'call_spread_width': 3.0,
            'expected_move': 8.0,
            'implied_volatility': 0.35,
            'dte': 45,
            'current_price': 100.0
        }
    
    async def test_generate_signal_success(self, strategy, sample_data, sample_options_chain, sample_strikes):
        """Test successful signal generation"""
        # Mock all dependencies
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = sample_options_chain
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_strikes_from_cache') as mock_strikes:
                        mock_strikes.return_value = sample_strikes
                        
                        with patch.object(strategy, 'calculate_position_metrics') as mock_metrics:
                            mock_metrics.return_value = {
                                'max_risk': 6.0,
                                'max_profit': 2.0,
                                'risk_reward_ratio': 0.33,
                                'put_price': 3.0,
                                'call_price': 4.0,
                                'total_delta': 0.0,
                                'total_gamma': 0.05,
                                'total_theta': -0.25,
                                'total_vega': 0.7,
                                'implied_volatility': 0.35,
                                'dte': 45
                            }
                            
                            with patch.object(strategy, '_calculate_enhanced_confidence') as mock_conf:
                                mock_conf.return_value = 0.7
                                
                                signal = await strategy.generate_signal("AAPL", sample_data)
                                
                                assert signal is not None
                                assert signal.symbol == "AAPL"
                                assert signal.action == "ENHANCED_IRON_CONDOR"
                                assert signal.strategy == "EnhancedIronCondor"
                                assert signal.confidence == 0.7
                                assert 'strikes' in signal.metadata
                                assert 'metrics' in signal.metadata
                                assert 'expiration' in signal.metadata
                                assert 'signal_type' in signal.metadata
                                assert signal.metadata['signal_type'] == 'enhanced_iron_condor'
    
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        data = pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 data points
        
        signal = await strategy.generate_signal("AAPL", data)
        
        assert signal is None
    
    async def test_generate_signal_no_expiration(self, strategy, sample_data):
        """Test signal generation when no expiration found"""
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = None
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    async def test_generate_signal_no_options_chain(self, strategy, sample_data):
        """Test signal generation when no options chain available"""
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = None
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                
                assert signal is None
    
    async def test_generate_signal_poor_market_conditions(self, strategy, sample_data, sample_options_chain):
        """Test signal generation with poor market conditions"""
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = sample_options_chain
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = False
                    
                    signal = await strategy.generate_signal("AAPL", sample_data)
                    
                    assert signal is None
    
    async def test_generate_signal_no_strikes(self, strategy, sample_data, sample_options_chain):
        """Test signal generation when no strikes available"""
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = sample_options_chain
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_strikes_from_cache') as mock_strikes:
                        mock_strikes.return_value = None
                        
                        signal = await strategy.generate_signal("AAPL", sample_data)
                        
                        assert signal is None
    
    async def test_generate_signal_low_risk_reward(self, strategy, sample_data, sample_options_chain, sample_strikes):
        """Test signal generation with low risk/reward ratio"""
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = sample_options_chain
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_strikes_from_cache') as mock_strikes:
                        mock_strikes.return_value = sample_strikes
                        
                        with patch.object(strategy, 'calculate_position_metrics') as mock_metrics:
                            mock_metrics.return_value = {
                                'max_risk': 6.0,
                                'max_profit': 1.0,
                                'risk_reward_ratio': 0.17,  # Below 0.3 threshold
                                'put_price': 3.0,
                                'call_price': 4.0,
                                'total_delta': 0.0,
                                'total_gamma': 0.05,
                                'total_theta': -0.25,
                                'total_vega': 0.7,
                                'implied_volatility': 0.35,
                                'dte': 45
                            }
                            
                            signal = await strategy.generate_signal("AAPL", sample_data)
                            
                            assert signal is None


class TestEnhancedIronCondorStrategyConfidence:
    """Test enhanced confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    @pytest.fixture
    def sample_options_chain(self):
        """Sample options chain"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.35
            )
        ]
    
    @pytest.fixture
    def sample_strikes(self):
        """Sample strikes"""
        return {
            'put_strike': 95.0,
            'call_strike': 105.0,
            'put_spread_width': 3.0,
            'call_spread_width': 3.0,
            'expected_move': 8.0,
            'implied_volatility': 0.35,
            'dte': 45,
            'current_price': 100.0
        }
    
    @pytest.fixture
    def sample_metrics(self):
        """Sample position metrics"""
        return {
            'max_risk': 6.0,
            'max_profit': 2.0,
            'risk_reward_ratio': 0.33,
            'put_price': 3.0,
            'call_price': 4.0,
            'total_delta': 0.0,
            'total_gamma': 0.05,
            'total_theta': -0.25,
            'total_vega': 0.7,
            'implied_volatility': 0.35,
            'dte': 45
        }
    
    def test_calculate_enhanced_confidence_optimal_conditions(self, strategy, sample_data, sample_options_chain, sample_strikes, sample_metrics):
        """Test confidence calculation with optimal conditions"""
        confidence = strategy._calculate_enhanced_confidence(sample_data, sample_options_chain, sample_strikes, sample_metrics)
        
        assert 0.0 <= confidence <= 0.9
        assert confidence > 0.5  # Should be high with optimal conditions
    
    def test_calculate_enhanced_confidence_high_volatility(self, strategy, sample_data, sample_options_chain, sample_strikes, sample_metrics):
        """Test confidence calculation with high volatility"""
        # Modify metrics for high volatility
        high_vol_metrics = sample_metrics.copy()
        high_vol_metrics['implied_volatility'] = 0.5  # High IV
        
        confidence = strategy._calculate_enhanced_confidence(sample_data, sample_options_chain, sample_strikes, high_vol_metrics)
        
        assert 0.0 <= confidence <= 0.9
    
    def test_calculate_enhanced_confidence_low_risk_reward(self, strategy, sample_data, sample_options_chain, sample_strikes, sample_metrics):
        """Test confidence calculation with low risk/reward ratio"""
        # Modify metrics for low risk/reward
        low_rr_metrics = sample_metrics.copy()
        low_rr_metrics['risk_reward_ratio'] = 0.1  # Low risk/reward
        
        confidence = strategy._calculate_enhanced_confidence(sample_data, sample_options_chain, sample_strikes, low_rr_metrics)
        
        assert 0.0 <= confidence <= 0.9


class TestEnhancedIronCondorStrategyInfo:
    """Test strategy information methods"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    def test_get_strategy_info(self, strategy):
        """Test strategy information retrieval"""
        info = strategy.get_strategy_info()
        
        assert info['name'] == "EnhancedIronCondor"
        assert info['days_to_expiration'] == 45
        assert info['profit_target_pct'] == 0.5
        assert info['stop_loss_pct'] == 2.0
        assert info['max_risk_per_trade'] == 0.02
        assert info['volatility_threshold'] == 0.3
        assert info['min_dte'] == 30
        assert info['max_dte'] == 60
        assert info['min_volume'] == 10
        assert info['min_open_interest'] == 50
        assert info['cache_lookback_days'] == 30
        assert 'features' in info
        assert len(info['features']) > 0
    
    def test_get_position_summary(self, strategy):
        """Test position summary retrieval"""
        summary = strategy.get_position_summary()
        
        assert 'active_positions' in summary
        assert 'total_positions' in summary
        assert 'cache_stats' in summary
        assert summary['active_positions'] == 0
        assert summary['total_positions'] == 0


class TestEnhancedIronCondorStrategyIntegration:
    """Test full workflow integration"""
    
    @pytest.fixture
    def strategy(self):
        return EnhancedIronCondorStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Sample market data for integration test"""
        dates = pd.date_range('2024-01-01', periods=25, freq='D')
        data = pd.DataFrame({
            'Close': [100 + i * 0.5 for i in range(25)],
            'Volume': [1000000 + i * 10000 for i in range(25)]
        }, index=dates)
        return data
    
    async def test_full_workflow(self, strategy, sample_data):
        """Test complete workflow from data to signal"""
        # Mock all dependencies
        sample_options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=95.0,
                expiration="2024-03-15",
                option_type="put",
                price=3.0,
                volume=100,
                open_interest=500,
                delta=-0.4,
                gamma=0.03,
                theta=-0.15,
                vega=0.4,
                implied_volatility=0.35
            ),
            OptionContract(
                symbol="AAPL",
                strike=105.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.0,
                volume=100,
                open_interest=500,
                delta=0.4,
                gamma=0.02,
                theta=-0.1,
                vega=0.3,
                implied_volatility=0.35
            )
        ]
        
        sample_strikes = {
            'put_strike': 95.0,
            'call_strike': 105.0,
            'put_spread_width': 3.0,
            'call_spread_width': 3.0,
            'expected_move': 8.0,
            'implied_volatility': 0.35,
            'dte': 45,
            'current_price': 100.0
        }
        
        sample_metrics = {
            'max_risk': 6.0,
            'max_profit': 2.0,
            'risk_reward_ratio': 0.33,
            'put_price': 3.0,
            'call_price': 4.0,
            'total_delta': 0.0,
            'total_gamma': 0.05,
            'total_theta': -0.25,
            'total_vega': 0.7,
            'implied_volatility': 0.35,
            'dte': 45
        }
        
        with patch.object(strategy, 'find_optimal_expiration') as mock_expiration:
            mock_expiration.return_value = '2024-03-15'
            
            with patch.object(strategy, 'get_liquid_options_chain') as mock_get_chain:
                mock_get_chain.return_value = sample_options_chain
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_strikes_from_cache') as mock_strikes:
                        mock_strikes.return_value = sample_strikes
                        
                        with patch.object(strategy, 'calculate_position_metrics') as mock_metrics:
                            mock_metrics.return_value = sample_metrics
                            
                            with patch.object(strategy, '_calculate_enhanced_confidence') as mock_conf:
                                mock_conf.return_value = 0.7
                                
                                signal = await strategy.generate_signal("AAPL", sample_data)
                                
                                # Verify complete workflow
                                assert signal is not None
                                assert signal.symbol == "AAPL"
                                assert signal.action == "ENHANCED_IRON_CONDOR"
                                assert signal.strategy == "EnhancedIronCondor"
                                assert signal.confidence == 0.7
                                
                                # Verify metadata
                                metadata = signal.metadata
                                assert 'strikes' in metadata
                                assert 'metrics' in metadata
                                assert 'expiration' in metadata
                                assert 'options_chain_size' in metadata
                                assert 'liquid_contracts' in metadata
                                assert 'signal_type' in metadata
                                assert metadata['signal_type'] == 'enhanced_iron_condor'
                                assert 'position_size' in metadata
                                assert 'profit_target' in metadata
                                assert 'stop_loss' in metadata 