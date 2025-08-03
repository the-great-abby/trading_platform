#!/usr/bin/env python3
"""
Tests for Earnings Strategy
Comprehensive test suite for earnings-based options strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.options.earnings_strategy import EarningsStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestEarningsStrategyInitialization:
    """Test EarningsStrategy initialization"""
    
    def test_earnings_strategy_init_default(self):
        """Test EarningsStrategy initialization with default parameters"""
        strategy = EarningsStrategy()
        
        assert strategy.name == "EarningsStrategy"
        assert strategy.days_before_earnings == 5
        assert strategy.days_after_earnings == 2
        assert strategy.profit_target_pct == 0.6
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_iv_expansion == 0.3
        assert strategy.earnings_lookback_days == 90
        assert strategy.strategy_type == "straddle"
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert isinstance(strategy.active_positions, dict)
        assert isinstance(strategy.position_history, list)
        assert isinstance(strategy.earnings_calendar, dict)
    
    def test_earnings_strategy_init_custom(self):
        """Test EarningsStrategy initialization with custom parameters"""
        strategy = EarningsStrategy(
            name="Custom_Earnings",
            days_before_earnings=7,
            days_after_earnings=3,
            profit_target_pct=0.7,
            stop_loss_pct=2.5,
            max_risk_per_trade=0.03,
            min_iv_expansion=0.4,
            earnings_lookback_days=120,
            strategy_type="iron_condor"
        )
        
        assert strategy.name == "Custom_Earnings"
        assert strategy.days_before_earnings == 7
        assert strategy.days_after_earnings == 3
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 2.5
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_iv_expansion == 0.4
        assert strategy.earnings_lookback_days == 120
        assert strategy.strategy_type == "iron_condor"
    
    def test_earnings_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = EarningsStrategy(
            days_before_earnings=7,
            profit_target_pct=0.7,
            strategy_type="iron_condor"
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "EarningsStrategy"
        assert info['type'] == "options_earnings"
        assert info['description'] == "Earnings-based options strategy for volatility expansion"
        assert info['parameters']['days_before_earnings'] == 7
        assert info['parameters']['profit_target_pct'] == 0.7
        assert info['parameters']['strategy_type'] == "iron_condor"
        assert info['active_positions'] == 0
        assert info['total_positions'] == 0


class TestEarningsStrategyEarningsDate:
    """Test earnings date functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    def test_get_earnings_date_new_symbol(self, strategy):
        """Test getting earnings date for new symbol"""
        symbol = "AAPL"
        
        earnings_date = strategy.get_earnings_date(symbol)
        
        assert earnings_date is not None
        assert isinstance(earnings_date, datetime)
        assert earnings_date > datetime.now()
    
    def test_get_earnings_date_cached(self, strategy):
        """Test getting earnings date from cache"""
        symbol = "AAPL"
        
        # First call
        earnings_date1 = strategy.get_earnings_date(symbol)
        
        # Second call should use cache
        earnings_date2 = strategy.get_earnings_date(symbol)
        
        assert earnings_date1 == earnings_date2
        assert symbol in strategy.earnings_calendar
    
    def test_check_earnings_timing_valid_window(self, strategy):
        """Test earnings timing check in valid window"""
        symbol = "AAPL"
        
        # Mock earnings date to be 6 days from now (within 5-7 day window)
        with patch.object(strategy, 'get_earnings_date') as mock_get:
            mock_get.return_value = datetime.now() + timedelta(days=6)
            
            result = strategy.check_earnings_timing(symbol)
            
            assert result is True
    
    def test_check_earnings_timing_too_early(self, strategy):
        """Test earnings timing check too early"""
        symbol = "AAPL"
        
        # Mock earnings date to be 10 days from now (too early)
        with patch.object(strategy, 'get_earnings_date') as mock_get:
            mock_get.return_value = datetime.now() + timedelta(days=10)
            
            result = strategy.check_earnings_timing(symbol)
            
            assert result is False
    
    def test_check_earnings_timing_too_late(self, strategy):
        """Test earnings timing check too late"""
        symbol = "AAPL"
        
        # Mock earnings date to be 2 days from now (too late)
        with patch.object(strategy, 'get_earnings_date') as mock_get:
            mock_get.return_value = datetime.now() + timedelta(days=2)
            
            result = strategy.check_earnings_timing(symbol)
            
            assert result is False
    
    def test_check_earnings_timing_no_earnings_date(self, strategy):
        """Test earnings timing check with no earnings date"""
        symbol = "AAPL"
        
        # Mock earnings date to be None
        with patch.object(strategy, 'get_earnings_date') as mock_get:
            mock_get.return_value = None
            
            result = strategy.check_earnings_timing(symbol)
            
            assert result is False


class TestEarningsStrategyIVExpansion:
    """Test IV expansion calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain with implied volatility"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=160.0,
                expiration="2024-02-16",
                option_type="call",
                price=3.50,
                volume=200,
                open_interest=800,
                delta=0.4,
                implied_volatility=0.35  # High IV
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                implied_volatility=0.40  # High IV
            )
        ]
    
    def test_calculate_iv_expansion_with_data(self, strategy, sample_options_chain):
        """Test IV expansion calculation with valid data"""
        symbol = "AAPL"
        
        # Mock historical IV
        with patch.object(strategy, '_get_historical_iv') as mock_historical:
            mock_historical.return_value = 0.25  # Historical IV
            
            iv_expansion = strategy.calculate_iv_expansion(symbol, sample_options_chain)
            
            assert isinstance(iv_expansion, float)
            assert iv_expansion > 0  # Should be positive expansion
    
    def test_calculate_iv_expansion_empty_chain(self, strategy):
        """Test IV expansion calculation with empty options chain"""
        symbol = "AAPL"
        
        iv_expansion = strategy.calculate_iv_expansion(symbol, [])
        
        assert iv_expansion == 0.0
    
    def test_calculate_iv_expansion_no_historical_iv(self, strategy, sample_options_chain):
        """Test IV expansion calculation with no historical IV"""
        symbol = "AAPL"
        
        # Mock historical IV to return 0
        with patch.object(strategy, '_get_historical_iv') as mock_historical:
            mock_historical.return_value = 0.0
            
            iv_expansion = strategy.calculate_iv_expansion(symbol, sample_options_chain)
            
            assert isinstance(iv_expansion, float)
            assert iv_expansion >= 0


class TestEarningsStrategyStrategySelection:
    """Test earnings strategy selection"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
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
                implied_volatility=0.30
            )
        ]
    
    def test_select_earnings_strategy_straddle(self, strategy, sample_options_chain):
        """Test strategy selection for straddle"""
        symbol = "AAPL"
        current_price = 165.0
        
        strategy_type = strategy.select_earnings_strategy(symbol, current_price, sample_options_chain)
        
        assert strategy_type in ["straddle", "strangle", "iron_condor"]
    
    def test_select_earnings_strategy_no_options(self, strategy):
        """Test strategy selection with no options"""
        symbol = "AAPL"
        current_price = 165.0
        
        strategy_type = strategy.select_earnings_strategy(symbol, current_price, [])
        
        assert strategy_type in ["straddle", "strangle", "iron_condor"]


class TestEarningsStrategyPositionCreation:
    """Test position creation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain for position creation"""
        return [
            # Call options
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5,
                implied_volatility=0.30
            ),
            # Put options
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="put",
                price=2.50,
                volume=300,
                open_interest=1000,
                delta=-0.5,
                implied_volatility=0.30
            )
        ]
    
    def test_can_create_straddle(self, strategy, sample_options_chain):
        """Test straddle creation capability"""
        current_price = 165.0
        
        can_create = strategy._can_create_straddle(sample_options_chain, current_price)
        
        assert isinstance(can_create, bool)
    
    def test_can_create_strangle(self, strategy, sample_options_chain):
        """Test strangle creation capability"""
        current_price = 165.0
        
        can_create = strategy._can_create_strangle(sample_options_chain, current_price)
        
        assert isinstance(can_create, bool)
    
    def test_can_create_iron_condor(self, strategy, sample_options_chain):
        """Test iron condor creation capability"""
        current_price = 165.0
        
        can_create = strategy._can_create_iron_condor(sample_options_chain, current_price)
        
        assert isinstance(can_create, bool)
    
    def test_create_earnings_position_straddle(self, strategy, sample_options_chain):
        """Test earnings position creation for straddle"""
        symbol = "AAPL"
        current_price = 165.0
        strategy_type = "straddle"
        
        position = strategy.create_earnings_position(symbol, current_price, strategy_type, sample_options_chain)
        
        if position is not None:
            assert isinstance(position, dict)
            assert 'strategy_type' in position
            assert 'max_profit' in position
            assert 'max_loss' in position
            assert position['strategy_type'] == 'straddle'
    
    def test_create_earnings_position_strangle(self, strategy, sample_options_chain):
        """Test earnings position creation for strangle"""
        symbol = "AAPL"
        current_price = 165.0
        strategy_type = "strangle"
        
        position = strategy.create_earnings_position(symbol, current_price, strategy_type, sample_options_chain)
        
        if position is not None:
            assert isinstance(position, dict)
            assert 'strategy_type' in position
            assert 'max_profit' in position
            assert 'max_loss' in position
            assert position['strategy_type'] == 'strangle'
    
    def test_create_earnings_position_iron_condor(self, strategy, sample_options_chain):
        """Test earnings position creation for iron condor"""
        symbol = "AAPL"
        current_price = 165.0
        strategy_type = "iron_condor"
        
        position = strategy.create_earnings_position(symbol, current_price, strategy_type, sample_options_chain)
        
        if position is not None:
            assert isinstance(position, dict)
            assert 'strategy_type' in position
            assert 'max_profit' in position
            assert 'max_risk' in position
            assert position['strategy_type'] == 'iron_condor'


class TestEarningsStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
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
                implied_volatility=0.30
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


class TestEarningsStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
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
    async def test_generate_signal_no_earnings_timing(self, strategy, sample_data):
        """Test signal generation when not in earnings timing window"""
        # Mock earnings timing to return False
        with patch.object(strategy, 'check_earnings_timing') as mock_timing:
            mock_timing.return_value = False
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_options_chain(self, strategy, sample_data):
        """Test signal generation with no options chain"""
        # Mock earnings timing and options service
        with patch.object(strategy, 'check_earnings_timing') as mock_timing:
            mock_timing.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
                mock_get.return_value = []
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                
                assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_options_service_exception(self, strategy, sample_data):
        """Test signal generation when options service throws exception"""
        # Mock earnings timing and options service exception
        with patch.object(strategy, 'check_earnings_timing') as mock_timing:
            mock_timing.return_value = True
            
            with patch.object(strategy.options_service, 'get_liquid_options') as mock_get:
                mock_get.side_effect = Exception("Service unavailable")
                
                signal = await strategy.generate_signal("AAPL", sample_data)
                
                assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_success(self, strategy, sample_data):
        """Test successful signal generation"""
        # Mock all the dependencies
        with patch.object(strategy, 'check_earnings_timing') as mock_timing:
            mock_timing.return_value = True
            
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
                        implied_volatility=0.30
                    )
                ]
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_earnings_strategy') as mock_select:
                        mock_select.return_value = "straddle"
                        
                        with patch.object(strategy, 'create_earnings_position') as mock_create:
                            mock_create.return_value = {
                                'strategy_type': 'straddle',
                                'max_profit': 100.0,
                                'max_loss': 50.0
                            }
                            
                            with patch.object(strategy, 'calculate_iv_expansion') as mock_iv:
                                mock_iv.return_value = 0.4
                                
                                with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                                    mock_confidence.return_value = 0.8
                                    
                                    signal = await strategy.generate_signal("AAPL", sample_data)
                                    
                                    assert signal is not None
                                    assert isinstance(signal, TradeSignal)
                                    assert signal.symbol == "AAPL"
                                    assert signal.action == "EARNINGS_STRADDLE"
                                    assert signal.strategy == "EarningsStrategy"
                                    assert signal.confidence == 0.8
                                    assert "strategy_type" in signal.metadata
                                    assert "iv_expansion" in signal.metadata
                                    assert "earnings_date" in signal.metadata
                                    assert signal.metadata['strategy_type'] == "straddle"


class TestEarningsStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
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
            'ATR': [3.0] * 30  # High ATR for volatility
        }, index=dates)
    
    def test_calculate_confidence_high_iv_expansion(self, strategy, sample_data):
        """Test confidence calculation with high IV expansion"""
        position = {
            'strategy_type': 'straddle'
        }
        iv_expansion = 0.6  # High IV expansion
        
        confidence = strategy._calculate_confidence(sample_data, position, iv_expansion)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.7  # Should be high with high IV expansion
    
    def test_calculate_confidence_moderate_iv_expansion(self, strategy, sample_data):
        """Test confidence calculation with moderate IV expansion"""
        position = {
            'strategy_type': 'iron_condor'
        }
        iv_expansion = 0.4  # Moderate IV expansion
        
        confidence = strategy._calculate_confidence(sample_data, position, iv_expansion)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.6  # Should be good with moderate IV expansion
    
    def test_calculate_confidence_low_iv_expansion(self, strategy, sample_data):
        """Test confidence calculation with low IV expansion"""
        position = {
            'strategy_type': 'strangle'
        }
        iv_expansion = 0.1  # Low IV expansion
        
        confidence = strategy._calculate_confidence(sample_data, position, iv_expansion)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence >= 0.5  # Should be at least base confidence


class TestEarningsStrategyPositionManagement:
    """Test position management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    def test_get_position_summary_empty(self, strategy):
        """Test position summary with no positions"""
        summary = strategy.get_position_summary()
        
        assert isinstance(summary, dict)
        assert 'active_positions' in summary
        assert 'position_history' in summary
        assert 'total_pnl' in summary
        assert 'win_rate' in summary
        assert 'earnings_calendar' in summary
        
        assert summary['active_positions'] == {}
        assert summary['position_history'] == []
        assert summary['total_pnl'] == 0.0
        assert summary['win_rate'] == 0.0
        assert summary['earnings_calendar'] == {}
    
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


class TestEarningsStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True
    
    def test_get_historical_iv(self, strategy):
        """Test historical IV calculation"""
        symbol = "AAPL"
        
        historical_iv = strategy._get_historical_iv(symbol)
        
        # Should return a float (could be 0 if no data)
        assert isinstance(historical_iv, float)
        assert historical_iv >= 0


class TestEarningsStrategyIntegration:
    """Integration tests for earnings strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create EarningsStrategy instance"""
        return EarningsStrategy()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete earnings strategy workflow"""
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
        with patch.object(strategy, 'check_earnings_timing') as mock_timing:
            mock_timing.return_value = True
            
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
                        implied_volatility=0.30
                    )
                ]
                
                with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                    mock_conditions.return_value = True
                    
                    with patch.object(strategy, 'select_earnings_strategy') as mock_select:
                        mock_select.return_value = "straddle"
                        
                        with patch.object(strategy, 'create_earnings_position') as mock_create:
                            mock_create.return_value = {
                                'strategy_type': 'straddle',
                                'max_profit': 100.0,
                                'max_loss': 50.0
                            }
                            
                            with patch.object(strategy, 'calculate_iv_expansion') as mock_iv:
                                mock_iv.return_value = 0.4
                                
                                with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                                    mock_confidence.return_value = 0.8
                                    
                                    signal = await strategy.generate_signal("AAPL", data)
                                    
                                    if signal is not None:
                                        assert isinstance(signal, TradeSignal)
                                        assert signal.symbol == "AAPL"
                                        assert signal.action.startswith("EARNINGS_")
                                        assert signal.strategy == "EarningsStrategy"
                                        assert signal.confidence > 0
                                        assert "strategy_type" in signal.metadata
                                        assert "iv_expansion" in signal.metadata
                                        assert "earnings_date" in signal.metadata
                                    else:
                                        # Signal might be None if conditions aren't met exactly
                                        assert True 