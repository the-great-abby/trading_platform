"""
Tests for backtest API endpoints
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.api.backtest_api import app, get_backtest_service


class TestBacktestAPI:
    """Test backtest API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_backtest_service(self):
        """Mock backtest service"""
        service = Mock()
        
        # Mock get_backtest_runs
        runs_data = [
            {
                'run_id': 'test_run_1',
                'strategy_name': 'momentum',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'total_return': 5.2,
                'total_return_pct': 5.2,
                'sharpe_ratio': 1.1,
                'max_drawdown': -2.1,
                'win_rate': 0.65,
                'total_trades': 25,
                'created_at': '2024-01-01T00:00:00Z'
            },
            {
                'run_id': 'test_run_2',
                'strategy_name': 'mean_reversion',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'total_return': 3.8,
                'total_return_pct': 3.8,
                'sharpe_ratio': 0.9,
                'max_drawdown': -1.5,
                'win_rate': 0.58,
                'total_trades': 18,
                'created_at': '2024-01-01T00:00:00Z'
            },
            {
                'run_id': 'test_run_3',
                'strategy_name': 'bollinger_bands',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'total_return': 4.1,
                'total_return_pct': 4.1,
                'sharpe_ratio': 1.0,
                'max_drawdown': -1.8,
                'win_rate': 0.62,
                'total_trades': 22,
                'created_at': '2024-01-01T00:00:00Z'
            },
            {
                'run_id': 'test_run_4',
                'strategy_name': 'rsi_strategy',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'total_return': 2.5,
                'total_return_pct': 2.5,
                'sharpe_ratio': 0.7,
                'max_drawdown': -2.5,
                'win_rate': 0.52,
                'total_trades': 15,
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        service.get_backtest_runs.return_value = runs_data
        
        # Mock get_backtest_trades
        trades_data = [
            {
                'trade_id': 'trade_1',
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 10,
                'price': 150.0,
                'timestamp': '2024-01-15T10:00:00Z',
                'pnl': 50.0
            },
            {
                'trade_id': 'trade_2',
                'symbol': 'AAPL',
                'action': 'SELL',
                'quantity': 10,
                'price': 155.0,
                'timestamp': '2024-01-20T14:30:00Z',
                'pnl': 50.0
            }
        ]
        service.get_backtest_trades.return_value = trades_data
        
        # Mock delete_backtest_run
        service.delete_backtest_run.return_value = True
        
        # Mock get_equity_curve
        equity_data = [
            {
                'date': '2024-01-01',
                'equity': 10000.0,
                'drawdown': 0.0
            },
            {
                'date': '2024-01-15',
                'equity': 10500.0,
                'drawdown': -100.0
            },
            {
                'date': '2024-01-31',
                'equity': 10520.0,
                'drawdown': -80.0
            }
        ]
        service.get_equity_curve.return_value = equity_data
        
        # Mock get_strategy_comparison
        service.get_strategy_comparison.return_value = {
            'strategies': ['momentum', 'mean_reversion'],
            'metrics': {
                'total_return': [5.2, 3.8],
                'sharpe_ratio': [1.1, 0.9],
                'max_drawdown': [-2.1, -1.5],
                'win_rate': [0.65, 0.58]
            }
        }
        
        # Mock get_available_strategies
        service.get_available_strategies.return_value = [
            'momentum',
            'mean_reversion',
            'bollinger_bands',
            'rsi_strategy'
        ]
        
        # Mock get_backtest_stats
        service.get_backtest_stats.return_value = {
            'total_runs': 50,
            'total_trades': 1250,
            'avg_return': 4.2,
            'best_strategy': 'momentum',
            'worst_strategy': 'rsi_strategy'
        }
        
        # Mock get_backtest_stats
        service.get_backtest_stats.return_value = {
            'total_runs': 50,
            'total_trades': 1250,
            'avg_return': 4.2,
            'best_strategy': 'momentum',
            'worst_strategy': 'rsi_strategy'
        }
        
        return service
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Backtest Results API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_list_runs_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful listing of backtest runs"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 4
        assert data["count"] == 4
        run_ids = [run["run_id"] for run in data["data"]]
        assert "test_run_1" in run_ids
        assert "test_run_2" in run_ids
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_list_runs_with_filters(self, mock_service_class, client, mock_backtest_service):
        """Test listing runs with filters"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs?strategy_name=momentum&start_date=2024-01-01&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["filters"]["strategy_name"] == "momentum"
        assert data["filters"]["start_date"] == "2024-01-01"
        assert data["filters"]["limit"] == 10
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_list_runs_error(self, mock_service_class, client):
        """Test error handling in list runs"""
        mock_service = Mock()
        mock_service.get_backtest_runs.side_effect = Exception("Database error")
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/runs")
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_run_details_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful run details retrieval"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs/test_run_1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["run_id"] == "test_run_1"
        assert data["data"]["strategy_name"] == "momentum"
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_run_details_not_found(self, mock_service_class, client, mock_backtest_service):
        """Test run details when run not found"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs/nonexistent_run")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_run_trades_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful trades retrieval"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs/test_run_1/trades")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["symbol"] == "AAPL"
        assert data["data"][0]["action"] == "BUY"
        assert data["data"][1]["action"] == "SELL"
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_run_trades_with_limit(self, mock_service_class, client, mock_backtest_service):
        """Test trades retrieval with limit"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs/test_run_1/trades?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 1  # API applies limit correctly
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_run_equity_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful equity curve retrieval"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/runs/test_run_1/equity")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["data"][0]["equity"] == 10000.0
        assert data["data"][1]["equity"] == 10500.0
        assert data["data"][2]["equity"] == 10520.0
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_compare_strategies_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful strategy comparison"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/compare")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 4
        strategy_names = [run["strategy_name"] for run in data["data"]]
        assert "momentum" in strategy_names
        assert "mean_reversion" in strategy_names
        assert "summary" in data
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_delete_run_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful run deletion"""
        mock_service_class.return_value = mock_backtest_service
        mock_backtest_service.delete_backtest_run.return_value = True
        
        response = client.delete("/api/v1/runs/test_run_1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully deleted backtest run" in data["message"]
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_delete_run_not_found(self, mock_service_class, client, mock_backtest_service):
        """Test run deletion when run not found"""
        mock_service_class.return_value = mock_backtest_service
        mock_backtest_service.delete_backtest_run.return_value = False
        
        response = client.delete("/api/v1/runs/nonexistent_run")
        assert response.status_code == 500
        data = response.json()
        assert "Failed to delete backtest run" in data["detail"]
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_list_strategies_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful strategies listing"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/strategies")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 4
        strategy_names = [s["name"] for s in data["data"]]
        assert "momentum" in strategy_names
        assert "mean_reversion" in strategy_names
        assert "bollinger_bands" in strategy_names
        assert "rsi_strategy" in strategy_names
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_get_stats_success(self, mock_service_class, client, mock_backtest_service):
        """Test successful stats retrieval"""
        mock_service_class.return_value = mock_backtest_service
        
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_runs"] == 4
        assert data["data"]["total_strategies"] == 4
        assert "performance_summary" in data["data"]
        assert "date_range" in data["data"]
        assert data["data"]["performance_summary"]["average_return"] > 0
        assert data["data"]["performance_summary"]["total_trades"] > 0
    
    def test_get_backtest_service(self):
        """Test service dependency injection"""
        service = get_backtest_service()
        assert service is not None
        # Should be an instance of BacktestResultsService
        assert hasattr(service, 'get_backtest_runs')
    
    @patch('src.api.backtest_api.BacktestResultsService')
    def test_global_exception_handler(self, mock_service_class, client):
        """Test global exception handler"""
        mock_service = Mock()
        mock_service.get_backtest_runs.side_effect = ValueError("Test error")
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/runs")
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]


class TestBacktestAPIModels:
    """Test backtest API data models and validation"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from src.api.backtest_api import app
        
        return TestClient(app)
    
    def test_query_parameter_validation(self, client):
        """Test query parameter validation"""
        # Test invalid limit (too high)
        response = client.get("/api/v1/runs?limit=2000")
        assert response.status_code == 422  # Validation error
        
        # Test invalid limit (too low)
        response = client.get("/api/v1/runs?limit=0")
        assert response.status_code == 422  # Validation error
        
        # Test valid limit
        response = client.get("/api/v1/runs?limit=100")
        assert response.status_code == 200
    
    def test_date_format_validation(self, client):
        """Test date format validation"""
        # Test invalid date format
        response = client.get("/api/v1/runs?start_date=invalid-date")
        assert response.status_code == 422  # Validation error
        
        # Test valid date format
        response = client.get("/api/v1/runs?start_date=2024-01-01")
        assert response.status_code == 200 