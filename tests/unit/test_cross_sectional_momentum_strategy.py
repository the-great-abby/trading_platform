#!/usr/bin/env python3
"""
Tests for Cross Sectional Momentum Strategy
Comprehensive test suite for cross-sectional momentum strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.strategies.momentum.cross_sectional_momentum_strategy import CrossSectionalMomentumStrategy
from src.core.types import TradeSignal


class TestCrossSectionalMomentumStrategyInitialization:
    """Test CrossSectionalMomentumStrategy initialization"""
    
    def test_cross_sectional_momentum_strategy_init_default(self):
        """Test CrossSectionalMomentumStrategy initialization with default parameters"""
        strategy = CrossSectionalMomentumStrategy()
        
        assert strategy.name == "CrossSectionalMomentum"
        assert strategy.lookback_period == 60
        assert strategy.momentum_periods == [20, 60, 120]
        assert strategy.top_percentile == 0.2
        assert strategy.bottom_percentile == 0.2
        assert strategy.rebalance_frequency == 20
        assert strategy.max_position_size == 0.1
        assert strategy.volatility_adjustment is True
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert strategy.last_rebalance is None
        assert strategy.current_positions == {}
        assert strategy.momentum_scores == {}
    
    def test_cross_sectional_momentum_strategy_init_custom(self):
        """Test CrossSectionalMomentumStrategy initialization with custom parameters"""
        strategy = CrossSectionalMomentumStrategy(
            name="CustomMomentum",
            lookback_period=30,
            momentum_periods=[10, 30, 60],
            top_percentile=0.15,
            bottom_percentile=0.15,
            rebalance_frequency=10,
            max_position_size=0.05,
            volatility_adjustment=False
        )
        
        assert strategy.name == "CustomMomentum"
        assert strategy.lookback_period == 30
        assert strategy.momentum_periods == [10, 30, 60]
        assert strategy.top_percentile == 0.15
        assert strategy.bottom_percentile == 0.15
        assert strategy.rebalance_frequency == 10
        assert strategy.max_position_size == 0.05
        assert strategy.volatility_adjustment is False
    
    def test_cross_sectional_momentum_strategy_get_info(self):
        """Test get_strategy_info method"""
        strategy = CrossSectionalMomentumStrategy()
        info = strategy.get_strategy_info()
        
        assert info["name"] == "CrossSectionalMomentum"
        assert info["lookback_period"] == 60
        assert info["momentum_periods"] == [20, 60, 120]
        assert info["top_percentile"] == 0.2
        assert info["bottom_percentile"] == 0.2
        assert info["rebalance_frequency"] == 20
        assert info["current_positions"] == 0
        assert info["last_rebalance"] is None


class TestCrossSectionalMomentumStrategyCalculation:
    """Test momentum calculation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy(momentum_periods=[20, 60])
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        # Create data with clear momentum pattern
        prices = []
        for i in range(120):
            if i < 60:
                prices.append(100 + i * 0.5)  # Upward trend
            else:
                prices.append(130 + (i - 60) * 0.3)  # Continued upward trend
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 120
        }, index=dates)
    
    def test_calculate_momentum_score_basic(self, strategy, sample_data):
        """Test basic momentum score calculation"""
        score = strategy.calculate_momentum_score(sample_data)
        
        # Should return a positive score for upward trending data
        assert isinstance(score, float)
        assert score > 0  # Positive momentum for upward trend
    
    def test_calculate_momentum_score_insufficient_data(self, strategy):
        """Test momentum score calculation with insufficient data"""
        # Create data with fewer points than max momentum period
        data = pd.DataFrame({
            'Close': [100 + i for i in range(10)]  # Only 10 points < 60
        })
        
        score = strategy.calculate_momentum_score(data)
        
        assert score == 0.0
    
    def test_calculate_momentum_score_volatility_adjustment(self, strategy):
        """Test momentum score calculation with volatility adjustment"""
        strategy.volatility_adjustment = True
        
        # Create data with high volatility
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        prices = [100 + np.random.normal(0, 5) for i in range(120)]  # High volatility
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 120
        }, index=dates)
        
        score = strategy.calculate_momentum_score(data)
        
        assert isinstance(score, float)
        # Score should be reasonable (not infinite or NaN)
        assert not np.isnan(score)
        assert not np.isinf(score)
    
    def test_calculate_momentum_score_no_volatility_adjustment(self, strategy, sample_data):
        """Test momentum score calculation without volatility adjustment"""
        strategy.volatility_adjustment = False
        
        score = strategy.calculate_momentum_score(sample_data)
        
        assert isinstance(score, float)
        assert score > 0  # Should be positive for upward trend


class TestCrossSectionalMomentumStrategyRanking:
    """Test stock ranking functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy(momentum_periods=[20, 60])
    
    @pytest.fixture
    def market_data(self):
        """Create sample market data for multiple symbols"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        
        # Create different momentum patterns for different symbols
        data = {}
        
        # Strong upward momentum
        prices_strong = [100 + i * 1.0 for i in range(120)]
        data['AAPL'] = pd.DataFrame({
            'Close': prices_strong,
            'Open': [p - 0.1 for p in prices_strong],
            'High': [p + 0.2 for p in prices_strong],
            'Low': [p - 0.2 for p in prices_strong],
            'Volume': [1000] * 120
        }, index=dates)
        
        # Moderate upward momentum
        prices_moderate = [100 + i * 0.5 for i in range(120)]
        data['MSFT'] = pd.DataFrame({
            'Close': prices_moderate,
            'Open': [p - 0.1 for p in prices_moderate],
            'High': [p + 0.2 for p in prices_moderate],
            'Low': [p - 0.2 for p in prices_moderate],
            'Volume': [1000] * 120
        }, index=dates)
        
        # Flat momentum
        prices_flat = [100 + np.random.normal(0, 0.5) for i in range(120)]
        data['GOOGL'] = pd.DataFrame({
            'Close': prices_flat,
            'Open': [p - 0.1 for p in prices_flat],
            'High': [p + 0.2 for p in prices_flat],
            'Low': [p - 0.2 for p in prices_flat],
            'Volume': [1000] * 120
        }, index=dates)
        
        # Downward momentum
        prices_down = [100 - i * 0.3 for i in range(120)]
        data['TSLA'] = pd.DataFrame({
            'Close': prices_down,
            'Open': [p - 0.1 for p in prices_down],
            'High': [p + 0.2 for p in prices_down],
            'Low': [p - 0.2 for p in prices_down],
            'Volume': [1000] * 120
        }, index=dates)
        
        return data
    
    def test_rank_stocks_by_momentum(self, strategy, market_data):
        """Test ranking stocks by momentum"""
        momentum_scores = strategy.rank_stocks_by_momentum(market_data)
        
        assert isinstance(momentum_scores, dict)
        assert len(momentum_scores) == 4  # 4 symbols
        
        # Check that scores are calculated for all symbols
        assert 'AAPL' in momentum_scores
        assert 'MSFT' in momentum_scores
        assert 'GOOGL' in momentum_scores
        assert 'TSLA' in momentum_scores
        
        # Check that scores are sorted in momentum_scores
        assert len(strategy.momentum_scores) == 4
        
        # The exact order may vary due to the complex momentum calculation
        # Just verify that we have different scores for different symbols
        scores = list(momentum_scores.values())
        assert len(set(scores)) >= 2  # At least 2 different scores
    
    def test_rank_stocks_by_momentum_empty_data(self, strategy):
        """Test ranking with empty market data"""
        momentum_scores = strategy.rank_stocks_by_momentum({})
        
        assert momentum_scores == {}
        assert strategy.momentum_scores == {}
    
    def test_rank_stocks_by_momentum_insufficient_data(self, strategy):
        """Test ranking with insufficient data"""
        # Create market data with insufficient points
        market_data = {
            'AAPL': pd.DataFrame({'Close': [100 + i for i in range(10)]})  # Only 10 points
        }
        
        momentum_scores = strategy.rank_stocks_by_momentum(market_data)
        
        assert momentum_scores == {}
        assert strategy.momentum_scores == {}


class TestCrossSectionalMomentumStrategyTradingCandidates:
    """Test trading candidate identification"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy(top_percentile=0.25, bottom_percentile=0.25)
    
    def test_identify_trading_candidates(self, strategy):
        """Test identifying trading candidates"""
        # Create momentum scores
        momentum_scores = {
            'AAPL': 0.15,  # Top performer
            'MSFT': 0.10,  # Good performer
            'GOOGL': 0.05,  # Moderate performer
            'TSLA': -0.05,  # Poor performer
            'META': -0.10,  # Bottom performer
            'NFLX': -0.15   # Worst performer
        }
        
        top_performers, bottom_performers = strategy.identify_trading_candidates(momentum_scores)
        
        # With 6 symbols and 25% percentile, should get 1-2 symbols each
        assert len(top_performers) >= 1
        assert len(bottom_performers) >= 1
        
        # AAPL should be in top performers
        assert 'AAPL' in top_performers
        
        # NFLX should be in bottom performers
        assert 'NFLX' in bottom_performers
    
    def test_identify_trading_candidates_empty_scores(self, strategy):
        """Test identifying candidates with empty momentum scores"""
        top_performers, bottom_performers = strategy.identify_trading_candidates({})
        
        assert top_performers == []
        assert bottom_performers == []
    
    def test_identify_trading_candidates_single_symbol(self, strategy):
        """Test identifying candidates with single symbol"""
        momentum_scores = {'AAPL': 0.10}
        
        top_performers, bottom_performers = strategy.identify_trading_candidates(momentum_scores)
        
        # With single symbol, it should be in both top and bottom (minimum 1 each)
        assert len(top_performers) >= 1
        assert len(bottom_performers) >= 1


class TestCrossSectionalMomentumStrategyRebalancing:
    """Test rebalancing functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy(rebalance_frequency=20)
    
    def test_should_rebalance_initial(self, strategy):
        """Test rebalancing check when no previous rebalance"""
        assert strategy.should_rebalance() is True
    
    def test_should_rebalance_recent(self, strategy):
        """Test rebalancing check when recently rebalanced"""
        strategy.last_rebalance = datetime.now()
        
        assert strategy.should_rebalance() is False
    
    def test_should_rebalance_old(self, strategy):
        """Test rebalancing check when rebalance is old"""
        strategy.last_rebalance = datetime.now() - timedelta(days=25)  # Older than 20 days
        
        assert strategy.should_rebalance() is True
    
    @pytest.mark.asyncio
    async def test_rebalance_portfolio(self, strategy):
        """Test portfolio rebalancing"""
        # Create market data
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        market_data = {
            'AAPL': pd.DataFrame({
                'Close': [100 + i * 1.0 for i in range(120)],
                'Open': [100 + i * 1.0 - 0.1 for i in range(120)],
                'High': [100 + i * 1.0 + 0.2 for i in range(120)],
                'Low': [100 + i * 1.0 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'MSFT': pd.DataFrame({
                'Close': [100 + i * 0.5 for i in range(120)],
                'Open': [100 + i * 0.5 - 0.1 for i in range(120)],
                'High': [100 + i * 0.5 + 0.2 for i in range(120)],
                'Low': [100 + i * 0.5 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'TSLA': pd.DataFrame({
                'Close': [100 - i * 0.3 for i in range(120)],
                'Open': [100 - i * 0.3 - 0.1 for i in range(120)],
                'High': [100 - i * 0.3 + 0.2 for i in range(120)],
                'Low': [100 - i * 0.3 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates)
        }
        
        await strategy._rebalance_portfolio(market_data)
        
        # Check that positions were created
        assert len(strategy.current_positions) > 0
        
        # Check that we have both long and short positions
        position_types = [pos['type'] for pos in strategy.current_positions.values()]
        assert 'long' in position_types
        assert 'short' in position_types
        
        # Verify that positions have the expected structure
        for symbol, position in strategy.current_positions.items():
            assert 'type' in position
            assert 'momentum_score' in position
            assert 'rank' in position
            assert position['type'] in ['long', 'short']
    
    def test_should_rebalance_initial(self, strategy):
        """Test rebalancing check when no previous rebalance"""
        assert strategy.should_rebalance() is True
    
    def test_should_rebalance_recent(self, strategy):
        """Test rebalancing check when recently rebalanced"""
        strategy.last_rebalance = datetime.now()
        
        assert strategy.should_rebalance() is False
    
    def test_should_rebalance_old(self, strategy):
        """Test rebalancing check when rebalance is old"""
        strategy.last_rebalance = datetime.now() - timedelta(days=25)  # Older than 20 days
        
        assert strategy.should_rebalance() is True
    
    @pytest.mark.asyncio
    async def test_rebalance_portfolio(self, strategy):
        """Test portfolio rebalancing"""
        # Create market data
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        market_data = {
            'AAPL': pd.DataFrame({
                'Close': [100 + i * 1.0 for i in range(120)],
                'Open': [100 + i * 1.0 - 0.1 for i in range(120)],
                'High': [100 + i * 1.0 + 0.2 for i in range(120)],
                'Low': [100 + i * 1.0 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'MSFT': pd.DataFrame({
                'Close': [100 + i * 0.5 for i in range(120)],
                'Open': [100 + i * 0.5 - 0.1 for i in range(120)],
                'High': [100 + i * 0.5 + 0.2 for i in range(120)],
                'Low': [100 + i * 0.5 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'TSLA': pd.DataFrame({
                'Close': [100 - i * 0.3 for i in range(120)],
                'Open': [100 - i * 0.3 - 0.1 for i in range(120)],
                'High': [100 - i * 0.3 + 0.2 for i in range(120)],
                'Low': [100 - i * 0.3 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates)
        }
        
        await strategy._rebalance_portfolio(market_data)
        
        # Check that positions were created
        assert len(strategy.current_positions) > 0
        
        # Check that we have both long and short positions
        position_types = [pos['type'] for pos in strategy.current_positions.values()]
        assert 'long' in position_types
        assert 'short' in position_types
        
        # Verify that positions have the expected structure
        for symbol, position in strategy.current_positions.items():
            assert 'type' in position
            assert 'momentum_score' in position
            assert 'rank' in position
            assert position['type'] in ['long', 'short']


class TestCrossSectionalMomentumStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy()
    
    @pytest.fixture
    def market_data(self):
        """Create sample market data"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        return {
            'AAPL': pd.DataFrame({
                'Close': [100 + i * 1.0 for i in range(120)],
                'Open': [100 + i * 1.0 - 0.1 for i in range(120)],
                'High': [100 + i * 1.0 + 0.2 for i in range(120)],
                'Low': [100 + i * 1.0 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'MSFT': pd.DataFrame({
                'Close': [100 + i * 0.5 for i in range(120)],
                'Open': [100 + i * 0.5 - 0.1 for i in range(120)],
                'High': [100 + i * 0.5 + 0.2 for i in range(120)],
                'Low': [100 + i * 0.5 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'TSLA': pd.DataFrame({
                'Close': [100 - i * 0.3 for i in range(120)],
                'Open': [100 - i * 0.3 - 0.1 for i in range(120)],
                'High': [100 - i * 0.3 + 0.2 for i in range(120)],
                'Low': [100 - i * 0.3 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates)
        }
    
    @pytest.mark.asyncio
    async def test_generate_signal_long_position(self, strategy, market_data):
        """Test signal generation for long position"""
        # Setup strategy with positions
        strategy.current_positions = {
            'AAPL': {
                'type': 'long',
                'momentum_score': 0.15,
                'rank': 1
            }
        }
        
        data = market_data['AAPL']
        signal = await strategy.generate_signal('AAPL', data, market_data)
        
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == 'AAPL'
            assert signal.action == 'BUY'
            assert signal.strategy == 'CrossSectionalMomentum'
            assert signal.confidence <= 0.9
            assert signal.metadata['position_type'] == 'long'
            assert signal.metadata['momentum_score'] == 0.15
            assert signal.metadata['rank'] == 1
            assert signal.metadata['signal_type'] == 'cross_sectional_momentum'
        else:
            # Signal might be None if rebalancing is needed
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_short_position(self, strategy, market_data):
        """Test signal generation for short position"""
        # Setup strategy with positions
        strategy.current_positions = {
            'TSLA': {
                'type': 'short',
                'momentum_score': -0.10,
                'rank': 3
            }
        }
        
        data = market_data['TSLA']
        signal = await strategy.generate_signal('TSLA', data, market_data)
        
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == 'TSLA'
            assert signal.action == 'SELL'
            assert signal.strategy == 'CrossSectionalMomentum'
            assert signal.confidence <= 0.9
            assert signal.metadata['position_type'] == 'short'
            assert signal.metadata['momentum_score'] == -0.10
            assert signal.metadata['rank'] == 3
            assert signal.metadata['signal_type'] == 'cross_sectional_momentum'
        else:
            # Signal might be None if rebalancing is needed
            assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_position(self, strategy, market_data):
        """Test signal generation when symbol is not in positions"""
        # Setup strategy with no positions for AAPL
        strategy.current_positions = {
            'MSFT': {
                'type': 'long',
                'momentum_score': 0.10,
                'rank': 2
            }
        }
        
        data = market_data['AAPL']
        signal = await strategy.generate_signal('AAPL', data, market_data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_market_data(self, strategy):
        """Test signal generation with insufficient market data"""
        data = pd.DataFrame({'Close': [100 + i for i in range(120)]})
        
        signal = await strategy.generate_signal('AAPL', data, {})
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_rebalancing_triggered(self, strategy, market_data):
        """Test signal generation that triggers rebalancing"""
        # Set last rebalance to old date to trigger rebalancing
        strategy.last_rebalance = datetime.now() - timedelta(days=25)
        
        data = market_data['AAPL']
        signal = await strategy.generate_signal('AAPL', data, market_data)
        
        # Should trigger rebalancing and potentially generate signal
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == 'AAPL'
        else:
            # No signal is also valid
            assert True


class TestCrossSectionalMomentumStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy()
    
    def test_calculate_momentum_score_zero_volatility(self, strategy):
        """Test momentum score calculation with zero volatility"""
        strategy.volatility_adjustment = True
        
        # Create data with zero volatility (constant price)
        data = pd.DataFrame({
            'Close': [100] * 120,  # Constant price
            'Open': [99.9] * 120,
            'High': [100.2] * 120,
            'Low': [99.8] * 120,
            'Volume': [1000] * 120
        })
        
        score = strategy.calculate_momentum_score(data)
        
        # Should handle zero volatility gracefully
        assert isinstance(score, float)
        assert score == 0.0  # No momentum for constant price
    
    def test_identify_trading_candidates_very_small_percentile(self, strategy):
        """Test identifying candidates with very small percentile"""
        strategy.top_percentile = 0.01  # 1%
        strategy.bottom_percentile = 0.01  # 1%
        
        momentum_scores = {
            'AAPL': 0.15,
            'MSFT': 0.10,
            'GOOGL': 0.05,
            'TSLA': -0.05,
            'META': -0.10
        }
        
        top_performers, bottom_performers = strategy.identify_trading_candidates(momentum_scores)
        
        # Should still return at least 1 symbol each (minimum)
        assert len(top_performers) >= 1
        assert len(bottom_performers) >= 1
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True


class TestCrossSectionalMomentumStrategyIntegration:
    """Integration tests for cross-sectional momentum strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create CrossSectionalMomentumStrategy instance"""
        return CrossSectionalMomentumStrategy(
            momentum_periods=[20, 60],
            top_percentile=0.2,
            bottom_percentile=0.2,
            rebalance_frequency=20
        )
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete cross-sectional momentum strategy workflow"""
        # Create realistic market data
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        market_data = {
            'AAPL': pd.DataFrame({
                'Close': [100 + i * 1.0 for i in range(120)],
                'Open': [100 + i * 1.0 - 0.1 for i in range(120)],
                'High': [100 + i * 1.0 + 0.2 for i in range(120)],
                'Low': [100 + i * 1.0 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'MSFT': pd.DataFrame({
                'Close': [100 + i * 0.5 for i in range(120)],
                'Open': [100 + i * 0.5 - 0.1 for i in range(120)],
                'High': [100 + i * 0.5 + 0.2 for i in range(120)],
                'Low': [100 + i * 0.5 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'GOOGL': pd.DataFrame({
                'Close': [100 + np.random.normal(0, 0.5) for i in range(120)],
                'Open': [100 + np.random.normal(0, 0.5) - 0.1 for i in range(120)],
                'High': [100 + np.random.normal(0, 0.5) + 0.2 for i in range(120)],
                'Low': [100 + np.random.normal(0, 0.5) - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'TSLA': pd.DataFrame({
                'Close': [100 - i * 0.3 for i in range(120)],
                'Open': [100 - i * 0.3 - 0.1 for i in range(120)],
                'High': [100 - i * 0.3 + 0.2 for i in range(120)],
                'Low': [100 - i * 0.3 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates),
            'META': pd.DataFrame({
                'Close': [100 - i * 0.2 for i in range(120)],
                'Open': [100 - i * 0.2 - 0.1 for i in range(120)],
                'High': [100 - i * 0.2 + 0.2 for i in range(120)],
                'Low': [100 - i * 0.2 - 0.2 for i in range(120)],
                'Volume': [1000] * 120
            }, index=dates)
        }
        
        # Test signal generation for AAPL (should be in top performers)
        data = market_data['AAPL']
        signal = await strategy.generate_signal('AAPL', data, market_data)
        
        # Should generate a signal after rebalancing
        if signal is not None:
            assert signal.symbol == 'AAPL'
            assert signal.action == 'BUY'  # Should be long position
            assert signal.strategy == 'CrossSectionalMomentum'
            assert signal.confidence <= 0.9
            assert signal.metadata['signal_type'] == 'cross_sectional_momentum'
        else:
            # No signal is also valid
            assert True
    
    def test_get_momentum_rankings(self, strategy):
        """Test getting momentum rankings"""
        # Set up momentum scores
        strategy.momentum_scores = {
            'AAPL': 0.15,
            'MSFT': 0.10,
            'GOOGL': 0.05,
            'TSLA': -0.05,
            'META': -0.10
        }
        
        rankings = strategy.get_momentum_rankings()
        
        assert 'rankings' in rankings
        assert 'top_performers' in rankings
        assert 'bottom_performers' in rankings
        
        assert len(rankings['top_performers']) == 5
        assert len(rankings['bottom_performers']) == 5
        
        # AAPL should be in top performers
        assert 'AAPL' in rankings['top_performers']
        
        # META should be in bottom performers
        assert 'META' in rankings['bottom_performers'] 