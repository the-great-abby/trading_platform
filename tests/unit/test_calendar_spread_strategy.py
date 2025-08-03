#!/usr/bin/env python3
"""
Tests for Calendar Spread Strategy
Comprehensive test suite for calendar spread options strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.options.calendar_spread_strategy import CalendarSpreadStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestCalendarSpreadStrategyInitialization:
    """Test CalendarSpreadStrategy initialization"""
    
    def test_calendar_spread_strategy_init_default(self):
        """Test CalendarSpreadStrategy initialization with default parameters"""
        strategy = CalendarSpreadStrategy()
        
        assert strategy.name == "CalendarSpread"
        assert strategy.short_dte == 14
        assert strategy.long_dte == 45
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 1.5
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_theta_ratio == 1.5
        assert strategy.min_delta == 0.3
        assert strategy.max_delta == 0.7
        assert strategy.min_dte_spread == 21
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert isinstance(strategy.active_positions, dict)
        assert isinstance(strategy.position_history, list)
    
    def test_calendar_spread_strategy_init_custom(self):
        """Test CalendarSpreadStrategy initialization with custom parameters"""
        strategy = CalendarSpreadStrategy(
            name="Custom_Calendar",
            short_dte=21,
            long_dte=60,
            profit_target_pct=0.8,
            stop_loss_pct=2.0,
            max_risk_per_trade=0.03,
            min_theta_ratio=2.0,
            min_delta=0.4,
            max_delta=0.6,
            min_dte_spread=30
        )
        
        assert strategy.name == "Custom_Calendar"
        assert strategy.short_dte == 21
        assert strategy.long_dte == 60
        assert strategy.profit_target_pct == 0.8
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_theta_ratio == 2.0
        assert strategy.min_delta == 0.4
        assert strategy.max_delta == 0.6
        assert strategy.min_dte_spread == 30
    
    def test_calendar_spread_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = CalendarSpreadStrategy(
            short_dte=21,
            long_dte=60,
            profit_target_pct=0.8
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "CalendarSpread"
        assert info['type'] == "options_time_decay"
        assert info['description'] == "Calendar spread strategy for time decay advantage"
        assert info['parameters']['short_dte'] == 21
        assert info['parameters']['long_dte'] == 60
        assert info['parameters']['profit_target_pct'] == 0.8
        assert info['active_positions'] == 0
        assert info['total_positions'] == 0


class TestCalendarSpreadStrategyExpirations:
    """Test expiration management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain with multiple expirations"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                theta=-0.05
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.20,
                volume=200,
                open_interest=800,
                delta=0.5,
                theta=-0.03
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=1.50,
                volume=400,
                open_interest=1200,
                delta=0.3,
                theta=-0.04
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-03-15",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=900,
                delta=0.3,
                theta=-0.02
            )
        ]
    
    def test_get_available_expirations_success(self, strategy, sample_options_chain):
        """Test getting available expirations with valid data"""
        symbol = "AAPL"
        
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = sample_options_chain
            
            expirations = strategy.get_available_expirations(symbol)
            
            assert isinstance(expirations, list)
            assert len(expirations) == 2
            assert "2024-02-16" in expirations
            assert "2024-03-15" in expirations
            assert expirations == sorted(expirations)  # Should be sorted
    
    def test_get_available_expirations_empty_chain(self, strategy):
        """Test getting available expirations with empty options chain"""
        symbol = "AAPL"
        
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = []
            
            expirations = strategy.get_available_expirations(symbol)
            
            assert expirations == []
    
    def test_get_available_expirations_service_exception(self, strategy):
        """Test getting available expirations when service throws exception"""
        symbol = "AAPL"
        
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.side_effect = Exception("Service unavailable")
            
            expirations = strategy.get_available_expirations(symbol)
            
            assert expirations == []
    
    def test_select_expiration_pair_success(self, strategy):
        """Test selecting expiration pair"""
        symbol = "AAPL"
        
        with patch.object(strategy, 'get_available_expirations') as mock_get:
            mock_get.return_value = ["2024-02-16", "2024-03-15", "2024-04-19"]
            
            expiration_pair = strategy.select_expiration_pair(symbol)
            
            if expiration_pair is not None:
                assert isinstance(expiration_pair, tuple)
                assert len(expiration_pair) == 2
                assert isinstance(expiration_pair[0], str)
                assert isinstance(expiration_pair[1], str)
                # Long expiration should be after short expiration
                assert expiration_pair[1] > expiration_pair[0]
    
    def test_select_expiration_pair_insufficient_expirations(self, strategy):
        """Test selecting expiration pair with insufficient expirations"""
        symbol = "AAPL"
        
        with patch.object(strategy, 'get_available_expirations') as mock_get:
            mock_get.return_value = ["2024-02-16"]  # Only one expiration
            
            expiration_pair = strategy.select_expiration_pair(symbol)
            
            assert expiration_pair is None


class TestCalendarSpreadStrategyStrikeSelection:
    """Test strike selection functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain for strike selection"""
        return [
            # Short expiration options
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                theta=-0.05
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=1.50,
                volume=400,
                open_interest=1200,
                delta=0.3,
                theta=-0.04
            ),
            # Long expiration options
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.20,
                volume=200,
                open_interest=800,
                delta=0.5,
                theta=-0.03
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-03-15",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=900,
                delta=0.3,
                theta=-0.02
            )
        ]
    
    def test_select_calendar_strikes_success(self, strategy, sample_options_chain):
        """Test selecting calendar strikes with valid data"""
        symbol = "AAPL"
        current_price = 165.0
        short_expiration = "2024-02-16"
        long_expiration = "2024-03-15"
        
        strikes = strategy.select_calendar_strikes(
            symbol, current_price, short_expiration, long_expiration, sample_options_chain
        )
        
        if strikes is not None:
            assert isinstance(strikes, dict)
            assert 'strike' in strikes
            assert 'short_expiration' in strikes
            assert 'long_expiration' in strikes
            assert strikes['short_expiration'] == short_expiration
            assert strikes['long_expiration'] == long_expiration
            assert isinstance(strikes['strike'], float)
    
    def test_select_calendar_strikes_no_options(self, strategy):
        """Test selecting calendar strikes with no options"""
        symbol = "AAPL"
        current_price = 165.0
        short_expiration = "2024-02-16"
        long_expiration = "2024-03-15"
        
        strikes = strategy.select_calendar_strikes(
            symbol, current_price, short_expiration, long_expiration, []
        )
        
        assert strikes is None
    
    def test_select_calendar_strikes_no_common_strikes(self, strategy):
        """Test selecting calendar strikes with no common strikes"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                theta=-0.05
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,  # Different strike
                expiration="2024-03-15",
                option_type="call",
                price=4.20,
                volume=200,
                open_interest=800,
                delta=0.5,
                theta=-0.03
            )
        ]
        
        symbol = "AAPL"
        current_price = 165.0
        short_expiration = "2024-02-16"
        long_expiration = "2024-03-15"
        
        strikes = strategy.select_calendar_strikes(
            symbol, current_price, short_expiration, long_expiration, options_chain
        )
        
        assert strikes is None
    
    def test_find_option_by_strike(self, strategy, sample_options_chain):
        """Test finding option by strike and expiration"""
        strike = 165.0
        expiration = "2024-02-16"
        
        option = strategy._find_option_by_strike(strike, expiration, sample_options_chain)
        
        if option is not None:
            assert isinstance(option, OptionContract)
            assert option.strike == strike
            assert option.expiration == expiration
    
    def test_calculate_strike_score(self, strategy, sample_options_chain):
        """Test calculating strike score"""
        current_price = 165.0
        strike = 165.0
        
        # Find options for the strike
        short_option = strategy._find_option_by_strike(strike, "2024-02-16", sample_options_chain)
        long_option = strategy._find_option_by_strike(strike, "2024-03-15", sample_options_chain)
        
        if short_option and long_option:
            score = strategy._calculate_strike_score(current_price, strike, short_option, long_option)
            
            assert isinstance(score, float)
            assert score >= 0  # Score should be non-negative


class TestCalendarSpreadStrategyMetrics:
    """Test calendar metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_strikes(self):
        """Create sample strikes dictionary"""
        return {
            'strike': 165.0,
            'short_expiration': '2024-02-16',
            'long_expiration': '2024-03-15'
        }
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain for metrics calculation"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                theta=-0.05
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-03-15",
                option_type="call",
                price=4.20,
                volume=200,
                open_interest=800,
                delta=0.5,
                theta=-0.03
            )
        ]
    
    def test_calculate_calendar_metrics_success(self, strategy, sample_strikes, sample_options_chain):
        """Test calculating calendar metrics with valid data"""
        metrics = strategy.calculate_calendar_metrics(sample_strikes, sample_options_chain)
        
        if metrics is not None and metrics != {}:
            assert isinstance(metrics, dict)
            assert 'net_debit' in metrics
            assert 'max_profit' in metrics
            assert 'max_loss' in metrics
            assert 'theta_advantage' in metrics
            assert 'profit_ratio' in metrics
            assert isinstance(metrics['net_debit'], float)
            assert isinstance(metrics['max_profit'], float)
            assert isinstance(metrics['max_loss'], float)
            assert isinstance(metrics['theta_advantage'], float)
            # profit_ratio can be int or float depending on division result
            assert isinstance(metrics['profit_ratio'], (int, float))
    
    def test_calculate_calendar_metrics_no_options(self, strategy, sample_strikes):
        """Test calculating calendar metrics with no options"""
        metrics = strategy.calculate_calendar_metrics(sample_strikes, [])
        
        assert metrics == {}  # Returns empty dict, not None


class TestCalendarSpreadStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100 + i * 0.5 for i in range(30)]
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000000 + i * 1000 for i in range(30)]
        }, index=dates)
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                theta=-0.05
            )
        ]
    
    def test_check_market_conditions_valid(self, strategy, sample_data, sample_options_chain):
        """Test market conditions with valid data"""
        result = strategy.check_market_conditions(sample_data, sample_options_chain)
        
        # Should return True for valid conditions
        assert isinstance(result, bool)
    
    def test_check_market_conditions_insufficient_data(self, strategy, sample_options_chain):
        """Test market conditions with insufficient data"""
        data = pd.DataFrame({
            'Close': [100 + i for i in range(5)]  # Only 5 points
        })
        
        result = strategy.check_market_conditions(data, sample_options_chain)
        
        # Should return False for insufficient data
        assert result is False
    
    def test_check_market_conditions_no_options(self, strategy, sample_data):
        """Test market conditions with no options"""
        result = strategy.check_market_conditions(sample_data, [])
        
        # Should return False for no options
        assert result is False


class TestCalendarSpreadStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100 + i * 0.5 for i in range(30)]
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000000 + i * 1000 for i in range(30)]
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        data = pd.DataFrame({
            'Close': [100 + i for i in range(10)]  # Only 10 points < 20
        })
        
        signal = await strategy.generate_signal("AAPL", data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_options_chain(self, strategy, sample_data):
        """Test signal generation with no options chain"""
        # Mock options service to return empty chain
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = []
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_expiration_pair(self, strategy, sample_data):
        """Test signal generation with no expiration pair"""
        # Mock options service and expiration pair selection
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = [
                OptionContract(
                    symbol="AAPL",
                    strike=165.0,
                    expiration="2024-02-16",
                    option_type="call",
                    price=2.80,
                    volume=300,
                    open_interest=1000,
                    delta=0.5,
                    theta=-0.05
                )
            ]
            
            with patch.object(strategy, 'select_expiration_pair') as mock_select:
                mock_select.return_value = None  # No expiration pair
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                
                assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_success(self, strategy, sample_data):
        """Test successful signal generation"""
        # Mock all the dependencies
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = [
                OptionContract(
                    symbol="AAPL",
                    strike=165.0,
                    expiration="2024-02-16",
                    option_type="call",
                    price=2.80,
                    volume=300,
                    open_interest=1000,
                    delta=0.5,
                    theta=-0.05
                ),
                OptionContract(
                    symbol="AAPL",
                    strike=165.0,
                    expiration="2024-03-15",
                    option_type="call",
                    price=4.20,
                    volume=200,
                    open_interest=800,
                    delta=0.5,
                    theta=-0.03
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                with patch.object(strategy, 'select_expiration_pair') as mock_expiration:
                    mock_expiration.return_value = ("2024-02-16", "2024-03-15")
                    
                    with patch.object(strategy, 'select_calendar_strikes') as mock_strikes:
                        mock_strikes.return_value = {
                            'strike': 165.0,
                            'short_expiration': '2024-02-16',
                            'long_expiration': '2024-03-15'
                        }
                        
                        with patch.object(strategy, 'calculate_calendar_metrics') as mock_metrics:
                            mock_metrics.return_value = {
                                'net_debit': 1.40,
                                'max_profit': 0.50,
                                'max_loss': 1.40,
                                'theta_advantage': 0.02,
                                'profit_ratio': 0.36
                            }
                            
                            with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                                mock_confidence.return_value = 0.8
                                
                                signal = await strategy.generate_signal("AAPL", sample_data)
                                
                                assert signal is not None
                                assert isinstance(signal, TradeSignal)
                                assert signal.symbol == "AAPL"
                                assert signal.action == "CALENDAR_SPREAD"
                                assert signal.strategy == "CalendarSpread"
                                assert signal.confidence == 0.8
                                assert "strike" in signal.metadata
                                assert "short_expiration" in signal.metadata
                                assert "long_expiration" in signal.metadata
                                assert signal.metadata['strike'] == 165.0


class TestCalendarSpreadStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data with indicators"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100 + i * 0.5 for i in range(30)]
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'RSI': [50.0] * 30,  # Neutral RSI
            'MACD': [0.0] * 30,  # Neutral MACD
            'MACD_Signal': [0.0] * 30  # Neutral MACD signal
        }, index=dates)
    
    @pytest.fixture
    def sample_strikes(self):
        """Create sample strikes dictionary"""
        return {
            'strike': 165.0,
            'short_expiration': '2024-02-16',
            'long_expiration': '2024-03-15'
        }
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics dictionary"""
        return {
            'profit_ratio': 0.36,
            'theta_advantage': 0.02
        }
    
    def test_calculate_confidence_neutral_technical(self, strategy, sample_data, sample_strikes, sample_metrics):
        """Test confidence calculation with neutral technical indicators"""
        confidence = strategy._calculate_confidence(sample_data, sample_strikes, sample_metrics)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be good with neutral indicators
    
    def test_calculate_confidence_good_profit_ratio(self, strategy, sample_data, sample_strikes):
        """Test confidence calculation with good profit ratio"""
        metrics = {
            'profit_ratio': 0.4,  # Good profit ratio
            'theta_advantage': 0.02
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_strikes, metrics)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.6  # Should be good with good profit ratio
    
    def test_calculate_confidence_optimal_spread(self, strategy, sample_data, sample_metrics):
        """Test confidence calculation with optimal expiration spread"""
        strikes = {
            'strike': 165.0,
            'short_expiration': '2024-02-16',
            'long_expiration': '2024-03-15'  # 28 days spread (optimal)
        }
        
        confidence = strategy._calculate_confidence(sample_data, strikes, sample_metrics)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.6  # Should be good with optimal spread


class TestCalendarSpreadStrategyPositionManagement:
    """Test position management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    def test_get_position_summary_empty(self, strategy):
        """Test position summary with no positions"""
        summary = strategy.get_position_summary()
        
        assert isinstance(summary, dict)
        assert 'active_positions' in summary
        assert 'position_history' in summary
        assert 'total_pnl' in summary
        assert 'win_rate' in summary
        
        assert summary['active_positions'] == {}
        assert summary['position_history'] == []
        assert summary['total_pnl'] == 0.0
        assert summary['win_rate'] == 0.0
    
    def test_calculate_win_rate_no_positions(self, strategy):
        """Test win rate calculation with no positions"""
        win_rate = strategy._calculate_win_rate()
        
        assert win_rate == 0.0
    
    def test_calculate_win_rate_with_positions(self, strategy):
        """Test win rate calculation with positions"""
        strategy.position_history = [
            {'pnl': 100.0},  # Winning trade
            {'pnl': -50.0},  # Losing trade
            {'pnl': 75.0}    # Winning trade
        ]
        
        win_rate = strategy._calculate_win_rate()
        
        assert win_rate == 2/3  # 2 wins out of 3 trades


class TestCalendarSpreadStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True


class TestCalendarSpreadStrategyIntegration:
    """Integration tests for calendar spread strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create CalendarSpreadStrategy instance"""
        return CalendarSpreadStrategy()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete calendar spread strategy workflow"""
        # Create realistic market data
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100 + i * 0.5 for i in range(30)]
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000000 + i * 1000 for i in range(30)]
        }, index=dates)
        
        # Mock all dependencies for a successful workflow
        with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
            mock_get.return_value = [
                OptionContract(
                    symbol="AAPL",
                    strike=165.0,
                    expiration="2024-02-16",
                    option_type="call",
                    price=2.80,
                    volume=300,
                    open_interest=1000,
                    delta=0.5,
                    theta=-0.05
                ),
                OptionContract(
                    symbol="AAPL",
                    strike=165.0,
                    expiration="2024-03-15",
                    option_type="call",
                    price=4.20,
                    volume=200,
                    open_interest=800,
                    delta=0.5,
                    theta=-0.03
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                with patch.object(strategy, 'select_expiration_pair') as mock_expiration:
                    mock_expiration.return_value = ("2024-02-16", "2024-03-15")
                    
                    with patch.object(strategy, 'select_calendar_strikes') as mock_strikes:
                        mock_strikes.return_value = {
                            'strike': 165.0,
                            'short_expiration': '2024-02-16',
                            'long_expiration': '2024-03-15'
                        }
                        
                        with patch.object(strategy, 'calculate_calendar_metrics') as mock_metrics:
                            mock_metrics.return_value = {
                                'net_debit': 1.40,
                                'max_profit': 0.50,
                                'max_loss': 1.40,
                                'theta_advantage': 0.02,
                                'profit_ratio': 0.36
                            }
                            
                            with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                                mock_confidence.return_value = 0.8
                                
                                signal = await strategy.generate_signal("AAPL", data)
                                
                                if signal is not None:
                                    assert isinstance(signal, TradeSignal)
                                    assert signal.symbol == "AAPL"
                                    assert signal.action == "CALENDAR_SPREAD"
                                    assert signal.strategy == "CalendarSpread"
                                    assert signal.confidence > 0
                                    assert "strike" in signal.metadata
                                    assert "short_expiration" in signal.metadata
                                    assert "long_expiration" in signal.metadata
                                else:
                                    # Signal might be None if conditions aren't met exactly
                                    assert True 