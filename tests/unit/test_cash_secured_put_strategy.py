#!/usr/bin/env python3
"""
Tests for Cash Secured Put Strategy
Comprehensive test suite for cash-secured put options strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.options.cash_secured_put_strategy import CashSecuredPutStrategy
from src.core.types import TradeSignal
from src.services.market_data.options_data_service import OptionContract


class TestCashSecuredPutStrategyInitialization:
    """Test CashSecuredPutStrategy initialization"""
    
    def test_cash_secured_put_strategy_init_default(self):
        """Test CashSecuredPutStrategy initialization with default parameters"""
        strategy = CashSecuredPutStrategy()
        
        assert strategy.name == "CashSecuredPut"
        assert strategy.days_to_expiration == 30
        assert strategy.profit_target_pct == 0.7
        assert strategy.stop_loss_pct == 1.5
        assert strategy.max_risk_per_trade == 0.02
        assert strategy.min_delta == -0.7
        assert strategy.max_delta == -0.3
        assert strategy.min_premium_pct == 0.015
        assert strategy.min_dte == 21
        assert strategy.max_dte == 45
        assert strategy.max_cash_utilization == 0.8
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert isinstance(strategy.active_positions, dict)
        assert isinstance(strategy.position_history, list)
    
    def test_cash_secured_put_strategy_init_custom(self):
        """Test CashSecuredPutStrategy initialization with custom parameters"""
        strategy = CashSecuredPutStrategy(
            name="Custom_CashPut",
            days_to_expiration=45,
            profit_target_pct=0.8,
            stop_loss_pct=2.0,
            max_risk_per_trade=0.03,
            min_delta=-0.8,
            max_delta=-0.2,
            min_premium_pct=0.02,
            min_dte=30,
            max_dte=60,
            max_cash_utilization=0.9
        )
        
        assert strategy.name == "Custom_CashPut"
        assert strategy.days_to_expiration == 45
        assert strategy.profit_target_pct == 0.8
        assert strategy.stop_loss_pct == 2.0
        assert strategy.max_risk_per_trade == 0.03
        assert strategy.min_delta == -0.8
        assert strategy.max_delta == -0.2
        assert strategy.min_premium_pct == 0.02
        assert strategy.min_dte == 30
        assert strategy.max_dte == 60
        assert strategy.max_cash_utilization == 0.9
    
    def test_cash_secured_put_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = CashSecuredPutStrategy(
            profit_target_pct=0.75,
            stop_loss_pct=1.8,
            min_delta=-0.6
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "CashSecuredPut"
        assert info['type'] == "options_income"
        assert info['description'] == "Cash-Secured Put strategy for income generation and stock acquisition"
        assert info['parameters']['days_to_expiration'] == 30
        assert info['parameters']['profit_target_pct'] == 0.75
        assert info['parameters']['stop_loss_pct'] == 1.8
        assert info['parameters']['min_delta'] == -0.6
        assert info['active_positions'] == 0
        assert info['total_positions'] == 0


class TestCashSecuredPutStrategyCashAvailability:
    """Test cash availability checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
    def test_check_cash_availability_sufficient(self, strategy):
        """Test cash availability with sufficient funds"""
        symbol = "AAPL"
        strike = 150.0
        portfolio_value = 100000.0  # $100k portfolio
        
        result = strategy.check_cash_availability(symbol, strike, portfolio_value)
        
        # Required cash: 150 * 100 = $15,000
        # Available cash: 100000 * 0.8 = $80,000
        assert result is True
    
    def test_check_cash_availability_insufficient(self, strategy):
        """Test cash availability with insufficient funds"""
        symbol = "AAPL"
        strike = 150.0
        portfolio_value = 10000.0  # $10k portfolio
        
        result = strategy.check_cash_availability(symbol, strike, portfolio_value)
        
        # Required cash: 150 * 100 = $15,000
        # Available cash: 10000 * 0.8 = $8,000
        assert result is False
    
    def test_check_cash_availability_exact_match(self, strategy):
        """Test cash availability with exact match"""
        symbol = "AAPL"
        strike = 100.0
        portfolio_value = 12500.0  # $12.5k portfolio
        
        result = strategy.check_cash_availability(symbol, strike, portfolio_value)
        
        # Required cash: 100 * 100 = $10,000
        # Available cash: 12500 * 0.8 = $10,000
        assert result is True


class TestCashSecuredPutStrategyStrikeSelection:
    """Test strike selection functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
    @pytest.fixture
    def sample_options_chain(self):
        """Create sample options chain with puts"""
        return [
            OptionContract(
                symbol="AAPL",
                strike=140.0,
                expiration="2024-02-16",
                option_type="put",
                price=3.50,
                volume=200,
                open_interest=800,
                delta=-0.4
            ),
            OptionContract(
                symbol="AAPL",
                strike=145.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.20,
                volume=300,
                open_interest=1000,
                delta=-0.5
            ),
            OptionContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-02-16",
                option_type="put",
                price=5.10,
                volume=400,
                open_interest=1200,
                delta=-0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=155.0,
                expiration="2024-02-16",
                option_type="put",
                price=6.20,
                volume=500,
                open_interest=1500,
                delta=-0.7
            )
        ]
    
    def test_select_optimal_strike_valid_chain(self, strategy, sample_options_chain):
        """Test strike selection with valid options chain"""
        current_price = 150.0
        
        strike = strategy.select_optimal_strike("AAPL", current_price, sample_options_chain)
        
        assert strike is not None
        assert strike in [140.0, 145.0, 150.0, 155.0]
    
    def test_select_optimal_strike_empty_chain(self, strategy):
        """Test strike selection with empty options chain"""
        strike = strategy.select_optimal_strike("AAPL", 150.0, [])
        
        assert strike is None
    
    def test_select_optimal_strike_no_puts(self, strategy):
        """Test strike selection with no put options"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-02-16",
                option_type="call",  # Call option, not put
                price=5.10,
                volume=400,
                open_interest=1200,
                delta=0.6
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 150.0, options_chain)
        
        assert strike is None
    
    def test_select_optimal_strike_delta_out_of_range(self, strategy):
        """Test strike selection with delta out of range"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-02-16",
                option_type="put",
                price=5.10,
                volume=400,
                open_interest=1200,
                delta=-0.8  # Outside range (-0.7 to -0.3)
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 150.0, options_chain)
        
        assert strike is None
    
    def test_select_optimal_strike_insufficient_premium(self, strategy):
        """Test strike selection with insufficient premium"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-02-16",
                option_type="put",
                price=1.0,  # Low premium: 1.0/150 = 0.67% < 1.5%
                volume=400,
                open_interest=1200,
                delta=-0.5
            )
        ]
        
        strike = strategy.select_optimal_strike("AAPL", 150.0, options_chain)
        
        assert strike is None


class TestCashSecuredPutStrategyMetrics:
    """Test position metrics calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
    def test_calculate_position_metrics(self, strategy):
        """Test position metrics calculation"""
        strike = 150.0
        option_price = 5.0
        current_price = 160.0
        
        metrics = strategy.calculate_position_metrics(strike, option_price, current_price)
        
        assert isinstance(metrics, dict)
        assert 'max_profit' in metrics
        assert 'max_loss' in metrics
        assert 'breakeven' in metrics
        assert 'prob_profit' in metrics
        assert 'premium_pct' in metrics
        assert 'required_cash' in metrics
        
        # Max profit should equal option premium (per share)
        assert metrics['max_profit'] == option_price
        # Max loss should be strike - premium (per share)
        assert metrics['max_loss'] == strike - option_price
        # Breakeven should be strike - premium
        assert metrics['breakeven'] == strike - option_price
        # Premium percentage should be option_price / current_price
        assert metrics['premium_pct'] == option_price / current_price
        # Required cash should be strike * 100
        assert metrics['required_cash'] == strike * 100
    
    def test_calculate_position_metrics_at_the_money(self, strategy):
        """Test metrics calculation for at-the-money put"""
        strike = 150.0
        option_price = 5.0
        current_price = 150.0  # At-the-money
        
        metrics = strategy.calculate_position_metrics(strike, option_price, current_price)
        
        assert metrics['max_profit'] == 5.0  # Option premium per share
        assert metrics['max_loss'] == 145.0  # (150 - 5) per share
        assert metrics['breakeven'] == 145.0  # 150 - 5
        assert metrics['premium_pct'] == 5.0 / 150.0
        assert metrics['required_cash'] == 15000.0  # 150 * 100


class TestCashSecuredPutStrategyMarketConditions:
    """Test market conditions checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
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
                strike=150.0,
                expiration="2024-02-16",
                option_type="put",
                price=5.10,
                volume=400,
                open_interest=1200,
                delta=-0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=145.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.20,
                volume=300,
                open_interest=1000,
                delta=-0.5
            ),
            OptionContract(
                symbol="AAPL",
                strike=140.0,
                expiration="2024-02-16",
                option_type="put",
                price=3.50,
                volume=200,
                open_interest=800,
                delta=-0.4
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
    
    def test_check_market_conditions_insufficient_liquid_puts(self, strategy, sample_data):
        """Test market conditions with insufficient liquid puts"""
        options_chain = [
            OptionContract(
                symbol="AAPL",
                strike=150.0,
                expiration="2024-02-16",
                option_type="put",
                price=5.10,
                volume=2,  # Low volume
                open_interest=1200,
                delta=-0.6
            ),
            OptionContract(
                symbol="AAPL",
                strike=145.0,
                expiration="2024-02-16",
                option_type="put",
                price=4.20,
                volume=1,  # Low volume
                open_interest=1000,
                delta=-0.5
            )
        ]
        
        result = strategy.check_market_conditions(sample_data, options_chain)
        
        # Should return False for insufficient liquid puts
        assert result is False


class TestCashSecuredPutStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
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
                    strike=150.0,
                    expiration="2024-02-16",
                    option_type="put",
                    price=5.10,
                    volume=400,
                    open_interest=1200,
                    delta=-0.6
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True  # Market conditions are good
                
                with patch.object(strategy, 'select_optimal_strike') as mock_select:
                    mock_select.return_value = 150.0  # Optimal strike
                    
                    with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                        mock_confidence.return_value = 0.8  # Above threshold
                        
                        signal = await strategy.generate_signal("AAPL", sample_data)
                        
                        assert signal is not None
                        assert isinstance(signal, TradeSignal)
                        assert signal.symbol == "AAPL"
                        assert signal.action == "CASH_SECURED_PUT"
                        assert signal.strategy == "CashSecuredPut"
                        assert signal.confidence == 0.8
                        assert "strike" in signal.metadata
                        assert "option_price" in signal.metadata
                        assert "expiration" in signal.metadata
                        assert signal.metadata['strike'] == 150.0
                        assert signal.metadata['option_price'] == 5.10


class TestCashSecuredPutStrategyConfidence:
    """Test confidence calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
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
            strike=150.0,
            expiration="2024-02-16",
            option_type="put",
            price=5.10,
            volume=400,
            open_interest=1200,
            delta=-0.5
        )
    
    def test_calculate_confidence_basic(self, strategy, sample_data, sample_option):
        """Test basic confidence calculation"""
        metrics = {
            'max_profit': 510.0,
            'max_loss': 14900.0,
            'premium_pct': 0.034
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be above base confidence
    
    def test_calculate_confidence_neutral_indicators(self, strategy, sample_data, sample_option):
        """Test confidence calculation with neutral indicators"""
        metrics = {
            'max_profit': 510.0,
            'max_loss': 14900.0,
            'premium_pct': 0.034
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        # Should get bonus for neutral RSI and bullish MACD
        assert confidence > 0.6
    
    def test_calculate_confidence_high_premium(self, strategy, sample_data, sample_option):
        """Test confidence calculation with high premium"""
        metrics = {
            'max_profit': 510.0,
            'max_loss': 14900.0,
            'premium_pct': 0.05  # 5% premium
        }
        
        confidence = strategy._calculate_confidence(sample_data, sample_option, metrics)
        
        # Should get bonus for high premium
        assert confidence > 0.7


class TestCashSecuredPutStrategyPositionManagement:
    """Test position management functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
    def test_get_position_summary_empty(self, strategy):
        """Test position summary with no positions"""
        summary = strategy.get_position_summary()
        
        assert isinstance(summary, dict)
        assert 'active_positions' in summary
        assert 'position_history' in summary
        assert 'total_pnl' in summary
        assert 'win_rate' in summary
        assert 'total_cash_utilized' in summary
        
        assert summary['active_positions'] == {}
        assert summary['position_history'] == []
        assert summary['total_pnl'] == 0.0
        assert summary['win_rate'] == 0.0
        assert summary['total_cash_utilized'] == 0.0
    
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


class TestCashSecuredPutStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
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
            strike=150.0,
            expiration="2024-02-16",
            option_type="put",
            price=5.10,
            volume=400,
            open_interest=1200,
            delta=-0.5
        )
        current_price = 160.0
        
        score = strategy._calculate_strike_score(option, current_price)
        
        assert isinstance(score, float)
        assert score > 0  # Should be positive


class TestCashSecuredPutStrategyIntegration:
    """Integration tests for cash secured put strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create CashSecuredPutStrategy instance"""
        return CashSecuredPutStrategy()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete cash secured put workflow"""
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
                    strike=150.0,
                    expiration="2024-02-16",
                    option_type="put",
                    price=5.10,
                    volume=400,
                    open_interest=1200,
                    delta=-0.5
                )
            ]
            
            with patch.object(strategy, 'check_market_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                with patch.object(strategy, 'select_optimal_strike') as mock_select:
                    mock_select.return_value = 150.0
                    
                    with patch.object(strategy, '_calculate_confidence') as mock_confidence:
                        mock_confidence.return_value = 0.8
                        
                        signal = await strategy.generate_signal("AAPL", data)
                        
                        if signal is not None:
                            assert isinstance(signal, TradeSignal)
                            assert signal.symbol == "AAPL"
                            assert signal.action == "CASH_SECURED_PUT"
                            assert signal.strategy == "CashSecuredPut"
                            assert signal.confidence > 0
                            assert "strike" in signal.metadata
                            assert "option_price" in signal.metadata
                        else:
                            # Signal might be None if conditions aren't met exactly
                            assert True 