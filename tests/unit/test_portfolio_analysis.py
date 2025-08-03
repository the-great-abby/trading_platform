"""
Tests for portfolio analysis modules
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, date, timedelta
import pandas as pd

# Import the analysis functions
from src.analyze_fixed_portfolio_performance import analyze_fixed_portfolio_performance
from src.analyze_portfolio_performance import analyze_portfolio_performance
from src.analyze_real_portfolio_performance import analyze_real_portfolio_performance


class TestFixedPortfolioAnalysis:
    """Test the fixed portfolio performance analysis"""
    
    @pytest.fixture
    def mock_backtest_service(self):
        """Mock backtest results service"""
        service = Mock()
        
        # Mock backtest results
        mock_results = [
            {
                'run_id': 'test-1',
                'strategy_name': 'SMA_Crossover',
                'start_date': '2023-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 15.5,
                'total_trades': 150,
                'win_rate': 65.0,
                'sharpe_ratio': 1.2,
                'max_drawdown_pct': 8.5,
                'created_at': '2024-01-15T10:00:00'
            },
            {
                'run_id': 'test-2',
                'strategy_name': 'RSI_Strategy',
                'start_date': '2023-02-01',
                'end_date': '2024-11-30',
                'total_return_pct': 12.3,
                'total_trades': 120,
                'win_rate': 58.0,
                'sharpe_ratio': 0.9,
                'max_drawdown_pct': 12.0,
                'created_at': '2024-01-16T11:00:00'
            },
            {
                'run_id': 'test-3',
                'strategy_name': 'SMA_Crossover',
                'start_date': '2023-03-01',
                'end_date': '2024-10-31',
                'total_return_pct': 18.7,
                'total_trades': 180,
                'win_rate': 70.0,
                'sharpe_ratio': 1.5,
                'max_drawdown_pct': 6.2,
                'created_at': '2024-01-17T12:00:00'
            }
        ]
        
        service.get_backtest_runs.return_value = mock_results
        return service
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_analyze_fixed_portfolio_performance_success(self, mock_print, mock_service_class, mock_backtest_service):
        """Test successful portfolio analysis"""
        mock_service_class.return_value = mock_backtest_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify service was initialized
        mock_service_class.assert_called_once()
        
        # Verify results were processed
        mock_backtest_service.get_backtest_runs.assert_called_once()
        
        # Verify output was printed
        assert mock_print.call_count > 0
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_analyze_fixed_portfolio_performance_no_results(self, mock_print, mock_service_class):
        """Test analysis with no backtest results"""
        mock_service = Mock()
        mock_service.get_backtest_runs.return_value = []
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify appropriate message was printed
        mock_print.assert_any_call("❌ No backtest results found in database")
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_analyze_fixed_portfolio_performance_no_two_year_runs(self, mock_print, mock_service_class):
        """Test analysis with no 2-year period runs"""
        mock_service = Mock()
        # Mock results with short periods
        mock_results = [
            {
                'run_id': 'test-1',
                'strategy_name': 'SMA_Crossover',
                'start_date': '2024-01-01',
                'end_date': '2024-06-30',  # Only 6 months
                'total_return_pct': 5.0,
                'total_trades': 50,
                'win_rate': 60.0,
                'sharpe_ratio': 0.8,
                'max_drawdown_pct': 3.0,
                'created_at': '2024-01-15T10:00:00'
            }
        ]
        mock_service.get_backtest_runs.return_value = mock_results
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify appropriate message was printed
        mock_print.assert_any_call("❌ No 2-year period backtest runs found")
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_analyze_fixed_portfolio_performance_exception(self, mock_print, mock_service_class):
        """Test analysis with exception handling"""
        mock_service = Mock()
        mock_service.get_backtest_runs.side_effect = Exception("Database error")
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify error was handled
        mock_print.assert_any_call("❌ Error analyzing portfolio performance: Database error")
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_analyze_fixed_portfolio_performance_strategy_breakdown(self, mock_print, mock_service_class, mock_backtest_service):
        """Test strategy performance breakdown calculation"""
        mock_service_class.return_value = mock_backtest_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify strategy breakdown was calculated
        # Check that SMA_Crossover appears twice and RSI_Strategy once
        sma_calls = [call for call in mock_print.call_args_list if 'SMA_Crossover' in str(call)]
        rsi_calls = [call for call in mock_print.call_args_list if 'RSI_Strategy' in str(call)]
        
        assert len(sma_calls) > 0
        assert len(rsi_calls) > 0


class TestPortfolioAnalysis:
    """Test the general portfolio performance analysis"""
    
    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data"""
        return {
            'initial_capital': 100000,
            'current_value': 115000,
            'total_return': 15.0,
            'trades': [
                {'symbol': 'AAPL', 'quantity': 100, 'price': 150.0, 'timestamp': '2024-01-01'},
                {'symbol': 'MSFT', 'quantity': 50, 'price': 300.0, 'timestamp': '2024-01-02'}
            ],
            'positions': [
                {'symbol': 'AAPL', 'quantity': 100, 'avg_price': 150.0, 'current_price': 155.0},
                {'symbol': 'MSFT', 'quantity': 50, 'avg_price': 300.0, 'current_price': 310.0}
            ]
        }
    
    @patch('src.analyze_portfolio_performance.get_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_portfolio_performance_success(self, mock_print, mock_get_data, mock_portfolio_data):
        """Test successful portfolio analysis"""
        mock_get_data.return_value = mock_portfolio_data
        
        await analyze_portfolio_performance()
        
        # Verify data was retrieved
        mock_get_data.assert_called_once()
        
        # Verify analysis was performed
        assert mock_print.call_count > 0
    
    @patch('src.analyze_portfolio_performance.get_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_portfolio_performance_no_data(self, mock_print, mock_get_data):
        """Test analysis with no portfolio data"""
        mock_get_data.return_value = None
        
        await analyze_portfolio_performance()
        
        # Verify appropriate message was printed
        mock_print.assert_any_call("❌ No portfolio data available")
    
    @patch('src.analyze_portfolio_performance.get_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_portfolio_performance_exception(self, mock_print, mock_get_data):
        """Test analysis with exception handling"""
        mock_get_data.side_effect = Exception("Data retrieval error")
        
        await analyze_portfolio_performance()
        
        # Verify error was handled
        mock_print.assert_any_call("❌ Error analyzing portfolio: Data retrieval error")


class TestRealPortfolioAnalysis:
    """Test the real portfolio performance analysis"""
    
    @pytest.fixture
    def mock_real_portfolio_data(self):
        """Mock real portfolio data"""
        return {
            'account_value': 125000,
            'cash_balance': 25000,
            'total_positions': 100000,
            'daily_pnl': 1500,
            'monthly_pnl': 5000,
            'positions': [
                {
                    'symbol': 'AAPL',
                    'quantity': 100,
                    'avg_price': 150.0,
                    'current_price': 155.0,
                    'unrealized_pnl': 500
                },
                {
                    'symbol': 'MSFT',
                    'quantity': 50,
                    'avg_price': 300.0,
                    'current_price': 310.0,
                    'unrealized_pnl': 500
                }
            ],
            'recent_trades': [
                {
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'quantity': 50,
                    'price': 152.0,
                    'timestamp': '2024-01-15T10:30:00'
                }
            ]
        }
    
    @patch('src.analyze_real_portfolio_performance.get_real_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_real_portfolio_performance_success(self, mock_print, mock_get_data, mock_real_portfolio_data):
        """Test successful real portfolio analysis"""
        mock_get_data.return_value = mock_real_portfolio_data
        
        await analyze_real_portfolio_performance()
        
        # Verify data was retrieved
        mock_get_data.assert_called_once()
        
        # Verify analysis was performed
        assert mock_print.call_count > 0
    
    @patch('src.analyze_real_portfolio_performance.get_real_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_real_portfolio_performance_no_data(self, mock_print, mock_get_data):
        """Test analysis with no real portfolio data"""
        mock_get_data.return_value = None
        
        await analyze_real_portfolio_performance()
        
        # Verify appropriate message was printed
        mock_print.assert_any_call("❌ No real portfolio data available")
    
    @patch('src.analyze_real_portfolio_performance.get_real_portfolio_data')
    @patch('builtins.print')
    async def test_analyze_real_portfolio_performance_exception(self, mock_print, mock_get_data):
        """Test analysis with exception handling"""
        mock_get_data.side_effect = Exception("Real data retrieval error")
        
        await analyze_real_portfolio_performance()
        
        # Verify error was handled
        mock_print.assert_any_call("❌ Error analyzing real portfolio: Real data retrieval error")


class TestPortfolioAnalysisIntegration:
    """Integration tests for portfolio analysis"""
    
    @pytest.fixture
    def sample_backtest_results(self):
        """Sample backtest results for integration testing"""
        return [
            {
                'run_id': 'integration-test-1',
                'strategy_name': 'Integration_Strategy',
                'start_date': '2023-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 20.0,
                'total_trades': 200,
                'win_rate': 75.0,
                'sharpe_ratio': 1.8,
                'max_drawdown_pct': 5.0,
                'created_at': '2024-01-20T09:00:00'
            }
        ]
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_integration_fixed_analysis(self, mock_print, mock_service_class, sample_backtest_results):
        """Integration test for fixed portfolio analysis"""
        mock_service = Mock()
        mock_service.get_backtest_runs.return_value = sample_backtest_results
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Verify the analysis completed successfully
        mock_service_class.assert_called_once()
        mock_service.get_backtest_runs.assert_called_once()
        
        # Verify output contains expected information
        output_calls = [str(call) for call in mock_print.call_args_list]
        assert any('Integration_Strategy' in call for call in output_calls)
        assert any('20.0' in call for call in output_calls)  # Return percentage


class TestPortfolioAnalysisEdgeCases:
    """Test edge cases for portfolio analysis"""
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_malformed_date_data(self, mock_print, mock_service_class):
        """Test handling of malformed date data"""
        mock_service = Mock()
        mock_results = [
            {
                'run_id': 'malformed-1',
                'strategy_name': 'Test_Strategy',
                'start_date': 'invalid-date',
                'end_date': '2024-12-31',
                'total_return_pct': 10.0,
                'total_trades': 100,
                'win_rate': 60.0,
                'sharpe_ratio': 1.0,
                'max_drawdown_pct': 5.0,
                'created_at': '2024-01-15T10:00:00'
            }
        ]
        mock_service.get_backtest_runs.return_value = mock_results
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Should handle malformed dates gracefully
        # The analysis should skip invalid dates and continue
        assert mock_print.call_count > 0
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_missing_required_fields(self, mock_print, mock_service_class):
        """Test handling of missing required fields"""
        mock_service = Mock()
        mock_results = [
            {
                'run_id': 'missing-fields-1',
                'strategy_name': 'Test_Strategy',
                # Missing start_date and end_date
                'total_return_pct': 10.0,
                'total_trades': 100,
                'win_rate': 60.0,
                'sharpe_ratio': 1.0,
                'max_drawdown_pct': 5.0,
                'created_at': '2024-01-15T10:00:00'
            }
        ]
        mock_service.get_backtest_runs.return_value = mock_results
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Should handle missing fields gracefully
        assert mock_print.call_count > 0
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_negative_performance_values(self, mock_print, mock_service_class):
        """Test handling of negative performance values"""
        mock_service = Mock()
        mock_results = [
            {
                'run_id': 'negative-1',
                'strategy_name': 'Test_Strategy',
                'start_date': '2023-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': -5.0,  # Negative return
                'total_trades': 100,
                'win_rate': 45.0,  # Below 50%
                'sharpe_ratio': -0.5,  # Negative Sharpe
                'max_drawdown_pct': 15.0,
                'created_at': '2024-01-15T10:00:00'
            }
        ]
        mock_service.get_backtest_runs.return_value = mock_results
        mock_service_class.return_value = mock_service
        
        await analyze_fixed_portfolio_performance()
        
        # Should handle negative values gracefully
        assert mock_print.call_count > 0


class TestPortfolioAnalysisPerformance:
    """Performance tests for portfolio analysis"""
    
    @patch('src.analyze_fixed_portfolio_performance.BacktestResultsService')
    @patch('builtins.print')
    async def test_large_dataset_performance(self, mock_print, mock_service_class):
        """Test performance with large dataset"""
        import time
        
        # Create large dataset
        large_results = []
        for i in range(1000):
            large_results.append({
                'run_id': f'large-test-{i}',
                'strategy_name': f'Strategy_{i % 10}',
                'start_date': '2023-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 10.0 + (i % 20),
                'total_trades': 100 + (i % 50),
                'win_rate': 50.0 + (i % 30),
                'sharpe_ratio': 0.5 + (i % 2),
                'max_drawdown_pct': 5.0 + (i % 10),
                'created_at': '2024-01-15T10:00:00'
            })
        
        mock_service = Mock()
        mock_service.get_backtest_runs.return_value = large_results
        mock_service_class.return_value = mock_service
        
        start_time = time.time()
        await analyze_fixed_portfolio_performance()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0  # Less than 5 seconds 