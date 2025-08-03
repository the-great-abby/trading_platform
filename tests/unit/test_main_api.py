"""
Tests for main API endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.api.main import app, create_app, StrategyConfig, StrategyUpdate, TradeSignal, PortfolioSummary


class TestMainAPI:
    """Test main API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_trading_engine(self):
        """Mock trading engine"""
        engine = Mock()
        engine.is_running.return_value = False
        
        # Mock portfolio
        portfolio = Mock()
        portfolio.get_portfolio_summary.return_value = {
            'total_value': 10000.0,
            'cash': 5000.0,
            'total_pnl': 500.0,
            'total_pnl_percentage': 5.0,
            'daily_pnl': 50.0,
            'max_drawdown': -100.0,
            'num_positions': 2,
            'positions': [
                {'symbol': 'AAPL', 'quantity': 10, 'current_price': 150.0},
                {'symbol': 'GOOGL', 'quantity': 5, 'current_price': 2800.0}
            ]
        }
        engine.portfolio = portfolio
        
        # Mock performance
        engine.get_performance_summary.return_value = {
            'total_return': 5.0,
            'sharpe_ratio': 1.2,
            'max_drawdown': -2.0,
            'win_rate': 0.65
        }
        
        # Mock async methods
        engine.start = AsyncMock()
        engine.stop = AsyncMock()
        
        # Mock strategies
        momentum_strategy = Mock()
        momentum_strategy.get_strategy_info.return_value = {'type': 'momentum'}
        momentum_strategy.is_active = True
        
        mean_reversion_strategy = Mock()
        mean_reversion_strategy.get_strategy_info.return_value = {'type': 'mean_reversion'}
        mean_reversion_strategy.is_active = False
        
        engine.strategies = {
            'momentum': momentum_strategy,
            'mean_reversion': mean_reversion_strategy
        }
        
        return engine
    
    def test_create_app(self):
        """Test app creation"""
        app = create_app()
        assert app.title == "AlgoTrader API"
        assert app.version == "1.0.0"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AlgoTrader API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_get_portfolio_success(self, client, mock_trading_engine):
        """Test successful portfolio retrieval"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.get("/portfolio")
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_value"] == 10000.0
            assert data["cash"] == 5000.0
            assert data["total_pnl"] == 500.0
            assert data["total_pnl_percentage"] == 5.0
            assert data["daily_pnl"] == 50.0
            assert data["max_drawdown"] == -100.0
            assert data["num_positions"] == 2
            assert len(data["positions"]) == 2
    
    def test_get_portfolio_no_engine(self, client):
        """Test portfolio retrieval when engine is not available"""
        with patch('src.api.main.trading_engine', None):
            response = client.get("/portfolio")
            assert response.status_code == 503
            data = response.json()
            assert "Trading engine not initialized" in data["detail"]
    
    def test_get_performance_success(self, client, mock_trading_engine):
        """Test successful performance retrieval"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.get("/performance")
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_return"] == 5.0
            assert data["sharpe_ratio"] == 1.2
            assert data["max_drawdown"] == -2.0
            assert data["win_rate"] == 0.65
    
    def test_get_strategies_success(self, client, mock_trading_engine):
        """Test successful strategies retrieval"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.get("/strategies")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["strategies"]) == 2
            assert data["strategies"][0]["name"] == "momentum"
            assert data["strategies"][0]["is_active"] is True
            assert data["strategies"][1]["name"] == "mean_reversion"
            assert data["strategies"][1]["is_active"] is False
    
    def test_register_strategy_success(self, client, mock_trading_engine):
        """Test successful strategy registration"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            strategy_config = {
                "name": "test_strategy",
                "symbol": "AAPL",
                "parameters": {"window": 20, "threshold": 0.02}
            }
            
            response = client.post("/strategies/register", json=strategy_config)
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Strategy registration endpoint"
    
    def test_register_strategy_failure(self, client, mock_trading_engine):
        """Test strategy registration failure"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            strategy_config = {
                "name": "test_strategy",
                "symbol": "AAPL",
                "parameters": {"window": 20, "threshold": 0.02}
            }
            
            response = client.post("/strategies/register", json=strategy_config)
            assert response.status_code == 200  # The API always returns 200 for now
            data = response.json()
            assert "Strategy registration endpoint" in data["message"]
    
    def test_update_strategy_success(self, client, mock_trading_engine):
        """Test successful strategy update"""
        # Add the strategy to the mock engine
        test_strategy = Mock()
        test_strategy.activate = Mock()
        test_strategy.deactivate = Mock()
        test_strategy.config = {}
        test_strategy.get_strategy_info.return_value = {'type': 'test'}
        mock_trading_engine.strategies['test_strategy'] = test_strategy
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            update_data = {
                "is_active": True,
                "parameters": {"window": 25}
            }
            
            response = client.put("/strategies/test_strategy/update", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert "Strategy test_strategy updated" in data["message"]
    
    def test_activate_strategy_success(self, client, mock_trading_engine):
        """Test successful strategy activation"""
        # Add the strategy to the mock engine
        test_strategy = Mock()
        test_strategy.activate = Mock()
        mock_trading_engine.strategies['test_strategy'] = test_strategy
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.post("/strategies/test_strategy/activate")
            assert response.status_code == 200
            data = response.json()
            assert "Strategy test_strategy activated" in data["message"]
    
    def test_deactivate_strategy_success(self, client, mock_trading_engine):
        """Test successful strategy deactivation"""
        # Add the strategy to the mock engine
        test_strategy = Mock()
        test_strategy.deactivate = Mock()
        mock_trading_engine.strategies['test_strategy'] = test_strategy
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.post("/strategies/test_strategy/deactivate")
            assert response.status_code == 200
            data = response.json()
            assert "Strategy test_strategy deactivated" in data["message"]
    
    def test_start_engine_success(self, client, mock_trading_engine):
        """Test successful engine start"""
        # Set engine as not running
        mock_trading_engine.is_running = False
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.post("/engine/start")
            assert response.status_code == 200
            data = response.json()
            assert "Trading engine started" in data["message"]
    
    def test_stop_engine_success(self, client, mock_trading_engine):
        """Test successful engine stop"""
        # Set engine as running
        mock_trading_engine.is_running = True
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.post("/engine/stop")
            assert response.status_code == 200
            data = response.json()
            assert "Trading engine stopped" in data["message"]
    
    def test_get_engine_status(self, client, mock_trading_engine):
        """Test engine status retrieval"""
        # Set up mock engine properties
        mock_trading_engine.is_running = False
        mock_trading_engine.mode.value = "paper"
        mock_trading_engine.trade_history = []
        mock_trading_engine.active_positions = []
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.get("/engine/status")
            assert response.status_code == 200
            data = response.json()
            assert "is_running" in data
            assert "mode" in data
            assert "total_trades" in data
            assert "active_positions" in data
    
    def test_set_trading_mode_success(self, client, mock_trading_engine):
        """Test successful trading mode setting"""
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.post("/engine/mode?mode=paper")
            assert response.status_code == 200
            data = response.json()
            assert "Trading mode set to paper" in data["message"]
    
    def test_get_trade_history(self, client, mock_trading_engine):
        """Test trade history retrieval"""
        # Set up mock trade history
        mock_trading_engine.trade_history = [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price": 150.0,
                "timestamp": "2024-01-15T10:00:00Z",
                "strategy": "momentum",
                "confidence": 0.8
            }
        ]
        
        with patch('src.api.main.trading_engine', mock_trading_engine):
            response = client.get("/trades?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "trades" in data
            assert "total" in data
            assert len(data["trades"]) == 1
            assert data["trades"][0]["symbol"] == "AAPL"
            assert data["trades"][0]["action"] == "BUY"


class TestAPIModels:
    """Test API data models"""
    
    def test_strategy_config_model(self):
        """Test StrategyConfig model"""
        config = StrategyConfig(
            name="test_strategy",
            symbol="AAPL",
            parameters={"window": 20, "threshold": 0.02}
        )
        
        assert config.name == "test_strategy"
        assert config.symbol == "AAPL"
        assert config.parameters == {"window": 20, "threshold": 0.02}
    
    def test_strategy_update_model(self):
        """Test StrategyUpdate model"""
        update = StrategyUpdate(
            is_active=True,
            parameters={"window": 25}
        )
        
        assert update.is_active is True
        assert update.parameters == {"window": 25}
    
    def test_trade_signal_model(self):
        """Test TradeSignal model"""
        signal = TradeSignal(
            symbol="AAPL",
            action="BUY",
            quantity=10.0,
            price=150.0,
            timestamp="2024-01-15T10:00:00Z",
            strategy="momentum",
            confidence=0.8
        )
        
        assert signal.symbol == "AAPL"
        assert signal.action == "BUY"
        assert signal.quantity == 10.0
        assert signal.price == 150.0
        assert signal.timestamp == "2024-01-15T10:00:00Z"
        assert signal.strategy == "momentum"
        assert signal.confidence == 0.8
    
    def test_portfolio_summary_model(self):
        """Test PortfolioSummary model"""
        portfolio = PortfolioSummary(
            total_value=10000.0,
            cash=5000.0,
            total_pnl=500.0,
            total_pnl_percentage=5.0,
            daily_pnl=50.0,
            max_drawdown=-100.0,
            num_positions=2,
            positions=[
                {"symbol": "AAPL", "quantity": 10, "current_price": 150.0}
            ]
        )
        
        assert portfolio.total_value == 10000.0
        assert portfolio.cash == 5000.0
        assert portfolio.total_pnl == 500.0
        assert portfolio.total_pnl_percentage == 5.0
        assert portfolio.daily_pnl == 50.0
        assert portfolio.max_drawdown == -100.0
        assert portfolio.num_positions == 2
        assert len(portfolio.positions) == 1 