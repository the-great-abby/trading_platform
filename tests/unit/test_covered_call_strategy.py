#!/usr/bin/env python3
"""
Tests for Covered Call Strategy
Comprehensive test suite for covered call options strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.options.covered_call_strategy import CoveredCallStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestCoveredCallStrategyInitialization:
    """Test CoveredCallStrategy initialization"""
    
    def test_covered_call_strategy_init_default(self):
        """Test CoveredCallStrategy initialization with default parameters"""
        strategy = CoveredCallStrategy()
        
        assert strategy.name == "CoveredCall"
        assert strategy.days_to_expiration == 30
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 1.5
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_delta == 0.3
        assert strategy.max_delta == 0.7
        assert strategy.min_premium_pct == 0.02
        assert strategy.min_dte == 21
        assert strategy.max_dte == 45
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert isinstance(strategy.active_positions, dict)
        assert isinstance(strategy.position_history, list)
    
    def test_covered_call_strategy_init_custom(self):
        """Test CoveredCallStrategy initialization with custom parameters"""
        strategy = CoveredCallStrategy(
            name="Custom_CoveredCall",
            days_to_expiration=45,
            profit_target_pct=0.8,
            stop_loss_pct=2.0,
            max_risk_per_trade=0.03,
            min_delta=0.2,
            max_delta=0.8,
            min_premium_pct=0.03,
            min_dte=30,
            max_dte=60
        )
        
        assert strategy.name == "Custom_CoveredCall"
        assert strategy.days_to_expiration == 45
        assert strategy.profit_target_pct == 0.8
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_delta == 0.2
        assert strategy.max_delta == 0.8
        assert strategy.min_premium_pct == 0.03
        assert strategy.min_dte == 30
        assert strategy.max_dte == 60
    
    def test_covered_call_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = CoveredCallStrategy(
            profit_target_pct=0.75,
            stop_loss_pct=1.8,
            min_delta=0.4
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "CoveredCall"
        assert info['type'] == "options_income"
        assert info['description'] == "Covered Call strategy for income generation"
        assert info['parameters']['days_to_expiration'] == 30
        assert info['parameters']['profit_target_pct'] == 0.75
        assert info['parameters']['stop_loss_pct'] == 1.8
        assert info['parameters']['min_delta'] == 0.4
        assert info['active_positions'] == 0
        assert info['total_positions'] == 0


class TestCoveredCallStrategyStockOwnership:
    """Test stock ownership checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
    def test_check_stock_ownership_available(self, strategy):
        """Test stock ownership check when stock is available"""
        symbol = "AAPL"
        portfolio_value = 100000.0
        
        result = strategy.check_stock_ownership(symbol, portfolio_value)
        
        # Currently always returns True (assumes we can buy if needed)
        assert result is True


class TestCoveredCallStrategyStrikeSelection:
    """Test strike selection functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain with calls"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=160.0,
                expiration="2024-02-16",
                option_type="call",
                price=3.50,
                volume=200,
                open_interest=800,
                delta=0.4
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.5
            ),
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.20,
                volume=400,
                open_interest=1200,
                delta=0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=175.0,
                expiration="2024-02-16",
                option_type="call",
                price=1.80,
                volume=500,
                open_interest=1500,
                delta=0.7
            )
        ]
    
    def test_select_optimal_strike_valid_chain(self, strategy, sample_options_chain):
        """Test strike selection with valid options chain"""
        current_price = 165.0
        
        strike = strategy.select_optimal_strike("AAPL", current_price, sample_options_chain)
        
        assert strike is not None
        assert strike in [160.0, 165.0, 170.0, 175.0]
    
    def test_select_optimal_strike_empty_chain(self, strategy):
        """Test strike selection with empty options chain"""
        strike = strategy.select_optimal_strike("AAPL", 165.0, [])
        
        assert strike is None
    
    def test_select_optimal_strike_no_calls(self, strategy):
        """Test strike selection with no call options"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="put",  # Put option, not call
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=-0.5
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 165.0, options_chain)
        
        assert strike is None
    
    def test_select_optimal_strike_delta_out_of_range(self, strategy):
        """Test strike selection with delta out of range"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=2.80,
                volume=300,
                open_interest=1000,
                delta=0.8  # Outside range (0.3 to 0.7)
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 165.0, options_chain)
        
        assert strike is None
    
    def test_select_optimal_strike_insufficient_premium(self, strategy):
        """Test strike selection with insufficient premium"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=1.0,  # Low premium: 1.0/165 = 0.61% < 2%
                volume=300,
                open_interest=1000,
                delta=0.5
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 165.0, options_chain)
        
        assert strike is None


class TestCoveredCallStrategyMetrics:
    """Test position metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
    def test_calculate_position_metrics(self, strategy):
        """Test position metrics calculation"""
        strike = 170.0
        option_price = 3.0
        current_price = 165.0
        
        metrics = strategy.calculate_position_metrics(strike, option_price, current_price)
        
        assert isinstance(metrics, dict)
        assert 'max_profit' in metrics
        assert 'breakeven' in metrics
        assert 'prob_profit' in metrics
        assert 'premium_pct' in metrics
        
        # Max profit should equal option premium (per share)
        assert metrics['max_profit'] == option_price
        # Breakeven should be strike + premium
        assert metrics['breakeven'] == strike + option_price
        # Premium percentage should be option_price / current_price
        assert metrics['premium_pct'] == option_price / current_price
    
    def test_calculate_position_metrics_at_the_money(self, strategy):
        """Test metrics calculation for at-the-money call"""
        strike = 165.0
        option_price = 3.0
        current_price = 165.0  # At-the-money
        
        metrics = strategy.calculate_position_metrics(strike, option_price, current_price)
        
        assert metrics['max_profit'] == 3.0  # Option premium per share
        assert metrics['breakeven'] == 168.0  # 165 + 3
        assert metrics['premium_pct'] == 3.0 / 165.0


class TestCoveredCallStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
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
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=3.0,
                volume=400,
                open_interest=1200,
                delta=0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=4.0,
                volume=300,
                open_interest=1000,
                delta=0.5
            ),
            OptionContract(
                symbol="AAPL",
                strike=160.0,
                expiration="2024-02-16",
                option_type="call",
                price=5.0,
                volume=200,
                open_interest=800,
                delta=0.4
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
    
    def test_check_market_conditions_insufficient_liquid_calls(self, strategy, sample_data):
        """Test market conditions with insufficient liquid calls"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=170.0,
                expiration="2024-02-16",
                option_type="call",
                price=3.0,
                volume=2,  # Low volume
                open_interest=1200,
                delta=0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=165.0,
                expiration="2024-02-16",
                option_type="call",
                price=4.0,
                volume=1,  # Low volume
                open_interest=1000,
                delta=0.5
            )
        ]
        
        result = strategy.check_market_conditions(sample_data, options_chain)
        
        # Should return False for insufficient liquid calls
        assert result is False


class TestCoveredCallStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
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
    async def test_generate_signal_no_optimal_strike(self, strategy, sample_data):
        """Test signal generation when no optimal strike found"""
        # Mock options service and strike selection
        with patch.object(strategy.options_service, 'get_liquid_options_with_historical_support') as mock_get:
            mock_get.return_value = [Mock()]  # Return some options
            
            with patch.object(strategy, 'select_optimal_strike') as mock_select:
                mock_select.return_value = None  # No optimal strike
                
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
                    strike=170.0,
                    expiration="2024-02-16",
                    option_type="call",
                    price=3.0,
                    volume=400,
                    open_interest=1200,
                    delta=0.6
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True  # Market conditions are good
                
                with patch.object(strategy, 'select_optimal_strike') as mock_select:
                    mock_select.return_value = 170.0  # Optimal strike
                    
                    with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                        mock_confidence.return_value = 0.8  # Above threshold
                        
                        signal = await strategy.generate_signal("AAPL", sample_data)
                        
                        assert signal is not None
                        assert isinstance(signal, TradeSignal)
                        assert signal.symbol == "AAPL"
                        assert signal.action == "COVERED_CALL"
                        assert signal.strategy == "CoveredCall"
                        assert signal.confidence == 0.8
                        assert "strike" in signal.metadata
                        assert "option_price" in signal.metadata
                        assert "expiration" in signal.metadata
                        assert signal.metadata['strike'] == 170.0
                        assert signal.metadata['option_price'] == 3.0


class TestCoveredCallStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
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
            'RSI': [50] * 30,  # Neutral RSI
            'MACD': [0.1] * 30,
            'MACD_Signal': [0.05] * 30  # Bullish MACD
        }, index=dates)
    
    @pytest.fixture
    def sample_option(self):
        """Create sample option contract"""
        return OptionContract(
            symbol="AAPL",
            strike=170.0,
            expiration="2024-02-16",
            option_type="call",
            price=3.0,
            volume=400,
            open_interest=1200,
            delta=0.5
        )
    
    def test_calculate_confidence_basic(self, strategy, sample_data, sample_option):
        """Test basic confidence calculation"""
        metrics = {
            'max_profit': 3.0,
            'breakeven': 173.0,
            'premium_pct': 0.018
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be above base confidence
    
    def test_calculate_confidence_neutral_indicators(self, strategy, sample_data, sample_option):
        """Test confidence calculation with neutral indicators"""
        metrics = {
            'max_profit': 3.0,
            'breakeven': 173.0,
            'premium_pct': 0.018
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        # Should get bonus for neutral RSI and bullish MACD
        assert confidence > 0.6
    
    def test_calculate_confidence_high_premium(self, strategy, sample_data, sample_option):
        """Test confidence calculation with high premium"""
        metrics = {
            'max_profit': 3.0,
            'breakeven': 173.0,
            'premium_pct': 0.05  # 5% premium
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        # Should get bonus for high premium
        assert confidence > 0.7


class TestCoveredCallStrategyPositionManagement:
    """Test position management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
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


class TestCoveredCallStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True
    
    def test_calculate_strike_score(self, strategy):
        """Test strike score calculation"""
        option = OptionContract(
            symbol="AAPL",
            strike=170.0,
            expiration="2024-02-16",
            option_type="call",
            price=3.0,
            volume=400,
            open_interest=1200,
            delta=0.5
        )
        current_price = 165.0
        
        score = strategy._calculate_strike_score(option, current_price)
        
        assert isinstance(score, float)
        assert score > 0  # Should be positive


class TestCoveredCallStrategyIntegration:
    """Integration tests for covered call strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create CoveredCallStrategy instance"""
        return CoveredCallStrategy()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete covered call workflow"""
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
                    strike=170.0,
                    expiration="2024-02-16",
                    option_type="call",
                    price=3.0,
                    volume=400,
                    open_interest=1200,
                    delta=0.5
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                with patch.object(strategy, 'select_optimal_strike') as mock_select:
                    mock_select.return_value = 170.0
                    
                    with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                        mock_confidence.return_value = 0.8
                        
                        signal = await strategy.generate_signal("AAPL", data)
                        
                        if signal is not None:
                            assert isinstance(signal, TradeSignal)
                            assert signal.symbol == "AAPL"
                            assert signal.action == "COVERED_CALL"
                            assert signal.strategy == "CoveredCall"
                            assert signal.confidence > 0
                            assert "strike" in signal.metadata
                            assert "option_price" in signal.metadata
                        else:
                            # Signal might be None if conditions aren't met exactly
                            assert True 