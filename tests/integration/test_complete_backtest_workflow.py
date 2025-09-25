"""
Integration tests for complete backtest workflow.

Tests the end-to-end backtest process including:
- Strategy execution with options data
- Error handling and fallbacks
- Performance validation
- Results formatting
"""

import pytest
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the strategy service path
sys.path.append('/Users/abby/code/trading/services/strategy-service')
sys.path.append('/Users/abby/code/trading/services/strategy-service/src')

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.services.mock_options_data_service import MockOptionsDataService
from src.strategies.options.iron_condor_strategy import IronCondorStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.utils.error_handler import ErrorHandler, log_backtest_progress


class TestCompleteBacktestWorkflow:
    """Test the complete backtest workflow integration."""
    
    @pytest.fixture
    def backtest_engine(self):
        """Create a backtest engine for testing."""
        return BacktestEngine(use_real_data=False, use_cache=False)
    
    @pytest.fixture
    def mock_market_data(self):
        """Create mock market data for testing."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Open': 100 + pd.Series(range(len(dates))) * 0.1,
            'High': 105 + pd.Series(range(len(dates))) * 0.1,
            'Low': 95 + pd.Series(range(len(dates))) * 0.1,
            'Close': 100 + pd.Series(range(len(dates))) * 0.1,
            'Volume': 1000000
        })
        data.set_index('Date', inplace=True)
        return data
    
    @pytest.fixture
    def mock_options_service(self):
        """Create mock options data service."""
        return MockOptionsDataService()
    
    @pytest.mark.asyncio
    async def test_complete_backtest_with_options_strategies(self, backtest_engine, mock_market_data, mock_options_service):
        """Test complete backtest workflow with options strategies."""
        
        # Setup mock market data
        symbols = ['AAPL', 'MSFT']
        strategies = ['IronCondor', 'RSI']
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            # Initialize options service
            backtest_engine.options_service = mock_options_service
            
            # Run backtest
            results = await backtest_engine.run_backtest(
                symbols=symbols,
                start_date='2023-01-01',
                end_date='2023-12-31',
                strategies=strategies
            )
            
            # Validate results
            assert isinstance(results, dict)
            assert len(results) == len(strategies)
            
            for strategy_name in strategies:
                assert strategy_name in results
                result = results[strategy_name]
                
                if result is not None:
                    assert hasattr(result, 'total_return')
                    assert hasattr(result, 'sharpe_ratio')
                    assert hasattr(result, 'max_drawdown')
                    assert hasattr(result, 'total_trades')
                    
                    # Validate result types
                    assert isinstance(result.total_return, (int, float))
                    assert isinstance(result.sharpe_ratio, (int, float))
                    assert isinstance(result.total_trades, int)
    
    @pytest.mark.asyncio
    async def test_backtest_performance_validation(self, backtest_engine, mock_market_data):
        """Test that backtest completes within performance targets."""
        
        symbols = ['AAPL', 'MSFT', 'AMD']
        strategies = ['RSI', 'MACD', 'BollingerBands']
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            start_time = datetime.now()
            
            results = await backtest_engine.run_backtest(
                symbols=symbols,
                start_date='2023-01-01',
                end_date='2023-12-31',
                strategies=strategies
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Validate performance (should complete within 30 seconds)
            assert duration < 30.0, f"Backtest took {duration:.2f}s, exceeding 30s target"
            
            # Validate results structure
            assert isinstance(results, dict)
            assert len(results) == len(strategies)
    
    @pytest.mark.asyncio
    async def test_backtest_error_handling_and_fallbacks(self, backtest_engine, mock_market_data):
        """Test error handling and fallback mechanisms."""
        
        symbols = ['AAPL']
        strategies = ['IronCondor', 'ButterflySpread', 'CalendarSpread']  # Options strategies
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            # Test with no options service (should fallback gracefully)
            backtest_engine.options_service = None
            
            results = await backtest_engine.run_backtest(
                symbols=symbols,
                start_date='2023-01-01',
                end_date='2023-12-31',
                strategies=strategies
            )
            
            # Should not crash, results may be None for failed strategies
            assert isinstance(results, dict)
            
            for strategy_name in strategies:
                assert strategy_name in results
                # Results can be None for failed strategies, that's acceptable
    
    @pytest.mark.asyncio
    async def test_backtest_with_mixed_strategy_types(self, backtest_engine, mock_market_data, mock_options_service):
        """Test backtest with both options and stock strategies."""
        
        symbols = ['AAPL', 'MSFT']
        strategies = ['IronCondor', 'RSI', 'MACD', 'BollingerBands']  # Mixed strategy types
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            # Setup options service
            backtest_engine.options_service = mock_options_service
            
            results = await backtest_engine.run_backtest(
                symbols=symbols,
                start_date='2023-01-01',
                end_date='2023-12-31',
                strategies=strategies
            )
            
            # Validate results
            assert isinstance(results, dict)
            assert len(results) == len(strategies)
            
            # Count successful vs failed strategies
            successful_strategies = [name for name, result in results.items() if result is not None]
            failed_strategies = [name for name, result in results.items() if result is None]
            
            # Should have some successful strategies (at least stock-based ones)
            assert len(successful_strategies) > 0, "Should have at least some successful strategies"
            
            # Log results for debugging
            print(f"Successful strategies: {successful_strategies}")
            print(f"Failed strategies: {failed_strategies}")
    
    @pytest.mark.asyncio
    async def test_backtest_results_formatting(self, backtest_engine, mock_market_data):
        """Test that backtest results are properly formatted."""
        
        symbols = ['AAPL']
        strategies = ['RSI']
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            results = await backtest_engine.run_backtest(
                symbols=symbols,
                start_date='2023-01-01',
                end_date='2023-12-31',
                strategies=strategies
            )
            
            # Validate results formatting
            assert isinstance(results, dict)
            assert 'RSI' in results
            
            rsi_result = results['RSI']
            if rsi_result is not None:
                # Validate all required attributes exist
                required_attrs = [
                    'strategy', 'initial_capital', 'final_capital', 'total_return',
                    'total_return_pct', 'max_drawdown_pct', 'sharpe_ratio',
                    'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
                    'profit_factor', 'avg_win', 'avg_loss', 'trades', 'equity_curve',
                    'start_date', 'end_date'
                ]
                
                for attr in required_attrs:
                    assert hasattr(rsi_result, attr), f"Missing attribute: {attr}"
                
                # Validate data types
                assert isinstance(rsi_result.strategy, str)
                assert isinstance(rsi_result.total_return, (int, float))
                assert isinstance(rsi_result.total_trades, int)
                assert isinstance(rsi_result.trades, list)
                assert isinstance(rsi_result.equity_curve, pd.DataFrame)
    
    @pytest.mark.asyncio
    async def test_backtest_logging_and_monitoring(self, backtest_engine, mock_market_data):
        """Test that backtest properly logs progress and errors."""
        
        symbols = ['AAPL']
        strategies = ['RSI', 'InvalidStrategy']  # One valid, one invalid
        
        with patch.object(backtest_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = {symbol: mock_market_data for symbol in symbols}
            
            # Mock the logging functions to capture calls
            with patch('src.utils.error_handler.log_backtest_progress') as mock_log_progress:
                with patch('src.utils.error_handler.ErrorHandler') as mock_error_handler:
                    mock_error_instance = MagicMock()
                    mock_error_handler.return_value = mock_error_instance
                    
                    results = await backtest_engine.run_backtest(
                        symbols=symbols,
                        start_date='2023-01-01',
                        end_date='2023-12-31',
                        strategies=strategies
                    )
                    
                    # Verify logging was called
                    assert mock_log_progress.called, "Progress logging should be called"
                    
                    # Verify error handling was used
                    assert mock_error_instance.handle_error.called or len([r for r in results.values() if r is None]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


