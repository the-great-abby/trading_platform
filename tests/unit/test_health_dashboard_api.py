"""
Tests for health dashboard API endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import time
from datetime import datetime

from src.api.health_dashboard import router, SystemHealthMonitor


class TestHealthDashboardAPI:
    """Test health dashboard API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager"""
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000,
            'l2_hit_rate': 0.75,
            'l2_cache_size': 5000,
            'total_requests': 10000,
            'total_hits': 8500
        }
        return cache_manager
    
    @pytest.fixture
    def mock_circuit_breaker_manager(self):
        """Mock circuit breaker manager"""
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {
                'state': 'CLOSED',
                'failure_count': 0,
                'success_count': 100,
                'last_failure_time': None
            },
            'trading_api': {
                'state': 'OPEN',
                'failure_count': 5,
                'success_count': 0,
                'last_failure_time': time.time()
            }
        }
        return cb_manager
    
    def test_health_overview_endpoint(self, client):
        """Test health overview endpoint"""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "system" in data
        assert "services" in data
        # uptime is nested in system metrics
        assert "uptime" in data["system"]
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    def test_system_health_endpoint(self, mock_cb_manager, mock_cache_manager, client):
        """Test system health endpoint"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED'},
            'trading_api': {'state': 'OPEN'}
        }
        mock_cb_manager.return_value = cb_manager
        
        response = client.get("/health/system")
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "uptime" in data
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    def test_services_health_endpoint(self, mock_cb_manager, mock_cache_manager, client):
        """Test services health endpoint"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED'},
            'trading_api': {'state': 'OPEN'}
        }
        mock_cb_manager.return_value = cb_manager
        
        response = client.get("/health/services")
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_status" in data
        assert "services" in data
        assert "cache" in data["services"]
        assert "circuit_breakers" in data["services"]
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    def test_trading_health_endpoint(self, mock_cb_manager, mock_cache_manager, client):
        """Test trading health endpoint"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED'},
            'trading_api': {'state': 'OPEN'}
        }
        mock_cb_manager.return_value = cb_manager
        
        response = client.get("/health/trading")
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "active_strategies" in data
        assert "daily_pnl" in data
    
    @patch('src.api.health_dashboard.get_cache_manager')
    def test_cache_health_endpoint(self, mock_cache_manager, client):
        """Test cache health endpoint"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000
        }
        mock_cache_manager.return_value = cache_manager
        
        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "stats" in data
        assert data["stats"]["l1_hit_rate"] == 0.85
        assert data["stats"]["l1_cache_size"] == 1000
    
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    def test_circuit_breakers_health_endpoint(self, mock_cb_manager, client):
        """Test circuit breakers health endpoint"""
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED'},
            'trading_api': {'state': 'OPEN'}
        }
        mock_cb_manager.return_value = cb_manager
        
        response = client.get("/health/circuit-breakers")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "circuit_states" in data
        assert "details" in data
        assert "market_data" in data["details"]
        assert "trading_api" in data["details"]
        assert data["details"]["market_data"]["state"] == "CLOSED"
        assert data["details"]["trading_api"]["state"] == "OPEN"
    
    def test_system_alerts_endpoint(self, client):
        """Test system alerts endpoint"""
        response = client.get("/health/alerts")
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list (even if empty)
        assert isinstance(data, list)


class TestSystemHealthMonitor:
    """Test SystemHealthMonitor class"""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor instance"""
        return SystemHealthMonitor()
    
    @patch('src.api.health_dashboard.psutil')
    async def test_get_system_metrics_success(self, mock_psutil, monitor):
        """Test successful system metrics retrieval"""
        # Mock psutil methods
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.getloadavg.return_value = (1.2, 1.1, 0.9)
        
        memory_mock = Mock()
        memory_mock.total = 16 * 1024**3  # 16GB
        memory_mock.available = 8 * 1024**3  # 8GB
        memory_mock.used = 8 * 1024**3  # 8GB
        memory_mock.percent = 50.0
        mock_psutil.virtual_memory.return_value = memory_mock
        
        disk_mock = Mock()
        disk_mock.total = 1000 * 1024**3  # 1TB
        disk_mock.used = 500 * 1024**3  # 500GB
        disk_mock.free = 500 * 1024**3  # 500GB
        mock_psutil.disk_usage.return_value = disk_mock
        
        network_mock = Mock()
        network_mock.bytes_sent = 1000000
        network_mock.bytes_recv = 2000000
        network_mock.packets_sent = 1000
        network_mock.packets_recv = 2000
        mock_psutil.net_io_counters.return_value = network_mock
        
        metrics = await monitor.get_system_metrics()
        
        assert metrics["cpu"]["usage_percent"] == 25.5
        assert metrics["cpu"]["count"] == 8
        assert metrics["cpu"]["load_average"] == (1.2, 1.1, 0.9)
        assert metrics["memory"]["total_gb"] == 16.0
        assert metrics["memory"]["available_gb"] == 8.0
        assert metrics["memory"]["usage_percent"] == 50.0
        assert metrics["disk"]["total_gb"] == 1000.0
        assert metrics["disk"]["used_gb"] == 500.0
        assert metrics["disk"]["usage_percent"] == 50.0
        assert metrics["network"]["bytes_sent"] == 1000000
        assert metrics["network"]["bytes_recv"] == 2000000
    
    @patch('src.api.health_dashboard.psutil')
    async def test_get_system_metrics_error(self, mock_psutil, monitor):
        """Test system metrics retrieval with error"""
        mock_psutil.cpu_percent.side_effect = Exception("Test error")
        
        metrics = await monitor.get_system_metrics()
        
        assert "error" in metrics
        assert "Test error" in metrics["error"]
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    async def test_get_service_status_success(self, mock_cb_manager, mock_cache_manager, monitor):
        """Test successful service status retrieval"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.85,
            'l1_cache_size': 1000
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED'},
            'trading_api': {'state': 'OPEN'}
        }
        mock_cb_manager.return_value = cb_manager
        
        status = await monitor.get_service_status()
        
        assert status["overall_status"] == "warning"
        assert "services" in status
        assert "cache" in status["services"]
        assert "circuit_breakers" in status["services"]
        assert status["services"]["cache"]["status"] == "healthy"
        assert status["services"]["circuit_breakers"]["open_circuits"] == 1
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    async def test_get_service_status_cache_warning(self, mock_cb_manager, mock_cache_manager, monitor):
        """Test service status with cache warning"""
        # Mock cache manager with no hits
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'l1_hit_rate': 0.0,
            'l1_cache_size': 0
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {}
        mock_cb_manager.return_value = cb_manager
        
        status = await monitor.get_service_status()
        
        assert status["overall_status"] == "warning"
        assert status["services"]["cache"]["status"] == "warning"
    
    @patch('src.api.health_dashboard.get_cache_manager')
    @patch('src.api.health_dashboard.get_circuit_breaker_manager')
    async def test_get_trading_metrics_success(self, mock_cb_manager, mock_cache_manager, monitor):
        """Test successful trading metrics retrieval"""
        # Mock cache manager
        cache_manager = AsyncMock()
        cache_manager.get_stats.return_value = {
            'total_requests': 1000,
            'total_hits': 850
        }
        mock_cache_manager.return_value = cache_manager
        
        # Mock circuit breaker manager
        cb_manager = Mock()
        cb_manager.get_all_stats.return_value = {
            'market_data': {'state': 'CLOSED', 'success_count': 100},
            'trading_api': {'state': 'CLOSED', 'success_count': 50}
        }
        mock_cb_manager.return_value = cb_manager
        
        metrics = await monitor.get_trading_metrics()
        
        assert "active_strategies" in metrics
        assert "daily_pnl" in metrics
        assert "risk_metrics" in metrics
        assert metrics["active_strategies"] == 3
        assert metrics["daily_pnl"] == 1250.5
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.logger is not None
        assert monitor.start_time > 0
        assert isinstance(monitor.start_time, float)


class TestHealthDashboardModels:
    """Test health dashboard data models and validation"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_health_response_structure(self, client):
        """Test health response structure"""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "timestamp", "system", "services"]
        for field in required_fields:
            assert field in data
    
    def test_system_metrics_structure(self, client):
        """Test system metrics response structure"""
        response = client.get("/health/system")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["timestamp", "uptime", "cpu", "memory", "disk", "network"]
        for field in required_fields:
            assert field in data
        
        # Check CPU structure
        assert "usage_percent" in data["cpu"]
        assert "count" in data["cpu"]
        
        # Check memory structure
        assert "total_gb" in data["memory"]
        assert "available_gb" in data["memory"]
        assert "usage_percent" in data["memory"]
        
        # Check disk structure
        assert "total_gb" in data["disk"]
        assert "used_gb" in data["disk"]
        assert "usage_percent" in data["disk"]
        
        # Check network structure
        assert "bytes_sent" in data["network"]
        assert "bytes_recv" in data["network"]
    
    def test_services_health_structure(self, client):
        """Test services health response structure"""
        response = client.get("/health/services")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "overall_status" in data
        assert "services" in data
        assert "cache" in data["services"]
        assert "circuit_breakers" in data["services"]
    
    def test_cache_health_structure(self, client):
        """Test cache health response structure"""
        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "stats" in data
        assert "l1_hit_rate" in data["stats"]
        assert "l1_cache_size" in data["stats"]
    
    def test_circuit_breakers_structure(self, client):
        """Test circuit breakers response structure"""
        response = client.get("/health/circuit-breakers")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "circuit_states" in data
        assert "details" in data
        assert isinstance(data["details"], dict) 