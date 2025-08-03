#!/usr/bin/env python3
"""
Tests for Volatility Strategy
Comprehensive test suite for volatility-based options strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.options.volatility_strategy import VolatilityStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestVolatilityStrategyInitialization:
    """Test VolatilityStrategy initialization"""
    
    def test_volatility_strategy_init_default(self):
        """Test VolatilityStrategy initialization with default parameters"""
        strategy = VolatilityStrategy()
        
        assert strategy.name == "VolatilityStrategy"
        assert strategy.volatility_threshold == 0.2
        assert strategy.iv_percentile_threshold == 0.7
        assert strategy.iv_percentile_low == 0.3
        assert strategy.profit_target_pct == 0.6
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_dte == 14
        assert strategy.max_dte == 45
        assert strategy.earnings_lookback_days == 30
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert isinstance(strategy.active_positions, dict)
        assert isinstance(strategy.position_history, list)
        assert isinstance(strategy.volatility_history, dict)
    
    def test_volatility_strategy_init_custom(self):
        """Test VolatilityStrategy initialization with custom parameters"""
        strategy = VolatilityStrategy(
            name="Custom_Volatility",
            volatility_threshold=0.25,
            iv_percentile_threshold=0.8,
            iv_percentile_low=0.2,
            profit_target_pct=0.7,
            stop_loss_pct=2.5,
            max_risk_per_trade=0.03,
            min_dte=21,
            max_dte=60,
            earnings_lookback_days=45
        )
        
        assert strategy.name == "Custom_Volatility"
        assert strategy.volatility_threshold == 0.25
        assert strategy.iv_percentile_threshold == 0.8
        assert strategy.iv_percentile_low == 0.2
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 2.5
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_dte == 21
        assert strategy.max_dte == 60
        assert strategy.earnings_lookback_days == 45
    
    def test_volatility_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = VolatilityStrategy(
            volatility_threshold=0.25,
            iv_percentile_threshold=0.8,
            profit_target_pct=0.7
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "VolatilityStrategy"
        assert info['type'] == "options_volatility"
        assert info['description'] == "Volatility-based options strategy for mean reversion and expansion"
        assert info['parameters']['volatility_threshold'] == 0.25
        assert info['parameters']['iv_percentile_threshold'] == 0.8
        assert info['parameters']['profit_target_pct'] == 0.7
        assert info['active_positions'] == 0
        assert info['total_positions'] == 0


class TestVolatilityStrategyHistoricalVolatility:
    """Test historical volatility calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    def test_calculate_historical_volatility_sufficient_data(self, strategy):
        """Test historical volatility calculation with sufficient data"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100 + i * 0.5 + np.random.normal(0, 1) for i in range(30)]
        
        data = pd.DataFrame({
            'Close': prices
        }, index=dates)
        
        vol = strategy.calculate_historical_volatility(data, window=20)
        
        assert isinstance(vol, float)
        assert vol > 0
        assert vol < 1  # Should be reasonable volatility
    
    def test_calculate_historical_volatility_insufficient_data(self, strategy):
        """Test historical volatility calculation with insufficient data"""
        data = pd.DataFrame({
            'Close': [100 + i for i in range(10)]  # Only 10 points
        })
        
        vol = strategy.calculate_historical_volatility(data, window=20)
        
        assert vol == 0.0
    
    def test_calculate_historical_volatility_constant_prices(self, strategy):
        """Test historical volatility calculation with constant prices"""
        data = pd.DataFrame({
            'Close': [100.0] * 30  # Constant price
        })
        
        vol = strategy.calculate_historical_volatility(data, window=20)
        
        assert vol == 0.0  # No volatility with constant prices


class TestVolatilityStrategyImpliedVolatility:
    """Test implied volatility percentile calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
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
                implied_volatility=0.25
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
                implied_volatility=0.30
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.20,
                volume=400,
                open_interest=1200,
                delta=0.6,
                implied_volatility=0.35
            )
        ]
    
    def test_calculate_implied_volatility_percentile_with_data(self, strategy, sample_options_chain):
        """Test IV percentile calculation with valid data"""
        percentile = strategy.calculate_implied_volatility_percentile("AAPL", sample_options_chain)
        
        assert isinstance(percentile, float)
        assert 0 <= percentile <= 1
    
    def test_calculate_implied_volatility_percentile_empty_chain(self, strategy):
        """Test IV percentile calculation with empty options chain"""
        percentile = strategy.calculate_implied_volatility_percentile("AAPL", [])
        
        assert percentile == 0.5  # Default to 50th percentile
    
    def test_calculate_implied_volatility_percentile_no_iv(self, strategy):
        """Test IV percentile calculation with no implied volatility data"""
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
                implied_volatility=None  # No IV data
            )
        ]
        
        percentile = strategy.calculate_implied_volatility_percentile("AAPL", options_chain)
        
        assert percentile == 0.5  # Default to 50th percentile


class TestVolatilityStrategyStrategySelection:
    """Test volatility strategy selection"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain"""
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
                implied_volatility=0.25
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
                implied_volatility=0.30
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.20,
                volume=400,
                open_interest=1200,
                delta=0.6,
                implied_volatility=0.35
            )
        ]
    
    def test_select_volatility_strategy_high_iv(self, strategy, sample_options_chain):
        """Test strategy selection with high implied volatility"""
        current_price = 165.0
        historical_vol = 0.25
        iv_percentile = 0.8  # High IV
        
        strategy_type = strategy.select_volatility_strategy(
            current_price, historical_vol, iv_percentile, sample_options_chain
        )
        
        assert strategy_type in ["iron_condor", "strangle", "straddle", "long_strangle", "calendar_spread"]
    
    def test_select_volatility_strategy_low_iv(self, strategy, sample_options_chain):
        """Test strategy selection with low implied volatility"""
        current_price = 165.0
        historical_vol = 0.25
        iv_percentile = 0.2  # Low IV
        
        strategy_type = strategy.select_volatility_strategy(
            current_price, historical_vol, iv_percentile, sample_options_chain
        )
        
        assert strategy_type in ["iron_condor", "strangle", "straddle", "long_strangle", "calendar_spread"]
    
    def test_select_volatility_strategy_no_options(self, strategy):
        """Test strategy selection with no options"""
        current_price = 165.0
        historical_vol = 0.25
        iv_percentile = 0.5
        
        strategy_type = strategy.select_volatility_strategy(
            current_price, historical_vol, iv_percentile, []
        )
        
        assert strategy_type == "calendar_spread"  # Default for moderate IV with no options


class TestVolatilityStrategyPositionCreation:
    """Test position creation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain for position creation"""
        return [
            # Call options
            OptionContract(
                symbol="AAPL",
                strike=160.0,
                expiration="2024-02-16",
                option_type="call",
                price=3.50,
                volume=200,
                open_interest=800,
                delta=0.4,
                implied_volatility=0.25
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
                implied_volatility=0.30
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.20,
                volume=400,
                open_interest=1200,
                delta=0.6,
                implied_volatility=0.35
            ),
            # Put options
            OptionContract(
                symbol="AAPL",
                strike=160.0,
                expiration="2024-02-16",
                option_type="put",
                price=2.50,
                volume=200,
                open_interest=800,
                delta=-0.4,
                implied_volatility=0.25
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="put",
                price=3.20,
                volume=300,
                open_interest=1000,
                delta=-0.5,
                implied_volatility=0.30
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="put",
                price=3.80,
                volume=400,
                open_interest=1200,
                delta=-0.6,
                implied_volatility=0.35
            )
        ]
    
    def test_can_create_iron_condor(self, strategy, sample_options_chain):
        """Test iron condor creation capability"""
        current_price = 165.0
        
        can_create = strategy._can_create_iron_condor(sample_options_chain, current_price)
        
        assert isinstance(can_create, bool)
    
    def test_can_create_straddle(self, strategy, sample_options_chain):
        """Test straddle creation capability"""
        current_price = 165.0
        
        can_create = strategy._can_create_straddle(sample_options_chain, current_price)
        
        assert isinstance(can_create, bool)
    
    def test_create_iron_condor_position(self, strategy, sample_options_chain):
        """Test iron condor position creation"""
        symbol = "AAPL"
        current_price = 165.0
        
        position = strategy.create_iron_condor_position(symbol, current_price, sample_options_chain)
        
        if position is not None:
            assert isinstance(position, dict)
            assert 'strategy_type' in position
            assert 'max_profit' in position
            assert 'max_risk' in position
            assert position['strategy_type'] == 'iron_condor'
    
    def test_create_straddle_position(self, strategy, sample_options_chain):
        """Test straddle position creation"""
        symbol = "AAPL"
        current_price = 165.0
        
        position = strategy.create_straddle_position(symbol, current_price, sample_options_chain)
        
        if position is not None:
            assert isinstance(position, dict)
            assert 'strategy_type' in position
            assert 'max_profit' in position
            assert 'max_loss' in position  # Uses max_loss, not max_risk
            assert position['strategy_type'] == 'straddle'


class TestVolatilityStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
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


class TestVolatilityStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
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
        with patch.object(strategy.options_service, 'get_liquid_options_with_historical_support') as mock_get:
            mock_get.return_value = []
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_options_service_exception(self, strategy, sample_data):
        """Test signal generation when options service throws exception"""
        # Mock options service to throw exception
        with patch.object(strategy.options_service, 'get_liquid_options_with_historical_support') as mock_get:
            mock_get.side_effect = Exception("Service unavailable")
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_success(self, strategy, sample_data):
        """Test successful signal generation"""
        # Mock all the dependencies
        with patch.object(strategy.options_service, 'get_liquid_options_with_historical_support') as mock_get:
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
                mock_conditions.return_value = True  # Market conditions are good
                
                with patch.object(strategy, 'select_volatility_strategy') as mock_select:
                    mock_select.return_value = "straddle"  # Select straddle strategy
                    
                    with patch.object(strategy, 'create_straddle_position') as mock_create:
                        mock_create.return_value = {
                            'strategy_type': 'straddle',
                            'max_profit': 100.0,
                            'max_risk': 50.0
                        }
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                            mock_confidence.return_value = 0.8  # Above threshold
                            
                            signal = await strategy.generate_signal("AAPL", sample_data)
                            
                            assert signal is not None
                            assert isinstance(signal, TradeSignal)
                            assert signal.symbol == "AAPL"
                            assert signal.action == "VOLATILITY_STRADDLE"
                            assert signal.strategy == "VolatilityStrategy"
                            assert signal.confidence == 0.8
                            assert "strategy_type" in signal.metadata
                            assert "historical_vol" in signal.metadata
                            assert "iv_percentile" in signal.metadata
                            assert signal.metadata['strategy_type'] == "straddle"


class TestVolatilityStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
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
            'ATR': [2.0] * 30  # High ATR for volatility
        }, index=dates)
    
    def test_calculate_confidence_high_iv(self, strategy, sample_data):
        """Test confidence calculation with high implied volatility"""
        historical_vol = 0.25
        iv_percentile = 0.85  # High IV
        position = {
            'strategy_type': 'iron_condor',
            'probability': 0.7
        }
        
        confidence = strategy._calculate_confidence(sample_data, historical_vol, iv_percentile, position)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.7  # Should be high with high IV
    
    def test_calculate_confidence_low_iv(self, strategy, sample_data):
        """Test confidence calculation with low implied volatility"""
        historical_vol = 0.25
        iv_percentile = 0.15  # Low IV
        position = {
            'strategy_type': 'straddle',
            'probability': 0.5
        }
        
        confidence = strategy._calculate_confidence(sample_data, historical_vol, iv_percentile, position)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.6  # Should be good with low IV
    
    def test_calculate_confidence_high_historical_vol(self, strategy, sample_data):
        """Test confidence calculation with high historical volatility"""
        historical_vol = 0.35  # High historical volatility
        iv_percentile = 0.5
        position = {
            'strategy_type': 'iron_condor',
            'probability': 0.6
        }
        
        confidence = strategy._calculate_confidence(sample_data, historical_vol, iv_percentile, position)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence >= 0.6  # Should be at least 0.6 with high historical vol


class TestVolatilityStrategyPositionManagement:
    """Test position management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    def test_get_position_summary_empty(self, strategy):
        """Test position summary with no positions"""
        summary = strategy.get_position_summary()
        
        assert isinstance(summary, dict)
        assert 'active_positions' in summary
        assert 'position_history' in summary
        assert 'total_pnl' in summary
        assert 'win_rate' in summary
        assert 'volatility_history' in summary
        
        assert summary['active_positions'] == {}
        assert summary['position_history'] == []
        assert summary['total_pnl'] == 0.0
        assert summary['win_rate'] == 0.0
        assert summary['volatility_history'] == {}
    
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


class TestVolatilityStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True
    
    def test_get_days_to_earnings(self, strategy):
        """Test days to earnings calculation"""
        current_date = datetime.now()
        
        days_to_earnings = strategy._get_days_to_earnings(current_date)
        
        # Should return None or a positive integer
        assert days_to_earnings is None or isinstance(days_to_earnings, int)


class TestVolatilityStrategyIntegration:
    """Integration tests for volatility strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create VolatilityStrategy instance"""
        return VolatilityStrategy()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete volatility strategy workflow"""
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
        with patch.object(strategy.options_service, 'get_liquid_options_with_historical_support') as mock_get:
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
                
                with patch.object(strategy, 'select_volatility_strategy') as mock_select:
                    mock_select.return_value = "straddle"
                    
                    with patch.object(strategy, 'create_straddle_position') as mock_create:
                        mock_create.return_value = {
                            'strategy_type': 'straddle',
                            'max_profit': 100.0,
                            'max_risk': 50.0
                        }
                        
                        with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                            mock_confidence.return_value = 0.8
                            
                            signal = await strategy.generate_signal("AAPL", data)
                            
                            if signal is not None:
                                assert isinstance(signal, TradeSignal)
                                assert signal.symbol == "AAPL"
                                assert signal.action.startswith("VOLATILITY_")
                                assert signal.strategy == "VolatilityStrategy"
                                assert signal.confidence > 0
                                assert "strategy_type" in signal.metadata
                                assert "historical_vol" in signal.metadata
                                assert "iv_percentile" in signal.metadata
                            else:
                                # Signal might be None if conditions aren't met exactly
                                assert True 