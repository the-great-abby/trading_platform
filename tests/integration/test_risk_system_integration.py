"""
End-to-End Integration Tests for Risk Management System

Tests the complete integration between risk management framework
and other trading system components.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from src.risk.integrations.portfolio_service_integration import (
    PortfolioServiceIntegration, PortfolioData, get_portfolio_integration
)
from src.risk.integrations.trading_engine_integration import (
    TradingEngineIntegration, TradeData, RiskCheckResult, get_trading_engine_integration
)
from src.risk.integrations.market_data_service_integration import (
    MarketDataServiceIntegration, MarketData, HistoricalData, get_market_data_integration
)
from src.risk.integrations.data_synchronization_service import (
    DataSynchronizationService, SyncStatus, get_data_sync_service
)


class TestPortfolioServiceIntegration:
    """Test portfolio service integration."""
    
    @pytest.fixture
    def portfolio_integration(self):
        """Create portfolio integration instance."""
        return PortfolioServiceIntegration(
            portfolio_service_url="http://test-portfolio-service:80",
            timeout_seconds=5,
            retry_attempts=1
        )
    
    @pytest.fixture
    def mock_portfolio_response(self):
        """Mock portfolio service response."""
        return {
            'data': {
                'portfolio': {
                    'portfolio_id': 'test-portfolio-123',
                    'total_value': 10000.0,
                    'cash_balance': 2000.0,
                    'last_updated': datetime.utcnow().isoformat()
                },
                'positions': [
                    {
                        'symbol': 'AAPL',
                        'quantity': 10,
                        'current_price': 150.0,
                        'market_value': 1500.0,
                        'weight': 0.15,
                        'asset_type': 'stock',
                        'sector': 'technology'
                    },
                    {
                        'symbol': 'GOOGL',
                        'quantity': 5,
                        'current_price': 2800.0,
                        'market_value': 14000.0,
                        'weight': 0.70,
                        'asset_type': 'stock',
                        'sector': 'technology'
                    }
                ],
                'performance': {
                    'total_return': 0.05,
                    'sharpe_ratio': 1.2
                }
            }
        }
    
    @patch('requests.Session.request')
    def test_get_portfolio_data_success(self, mock_request, portfolio_integration, mock_portfolio_response):
        """Test successful portfolio data retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_portfolio_response
        mock_request.return_value = mock_response
        
        # Test portfolio data retrieval
        portfolio_data = portfolio_integration.get_portfolio_data('test-portfolio-123')
        
        # Verify results
        assert portfolio_data is not None
        assert portfolio_data.portfolio_id == 'test-portfolio-123'
        assert portfolio_data.total_value == 10000.0
        assert portfolio_data.cash_balance == 2000.0
        assert len(portfolio_data.positions) == 2
        assert portfolio_data.positions[0]['symbol'] == 'AAPL'
        assert portfolio_data.positions[1]['symbol'] == 'GOOGL'
    
    @patch('requests.Session.request')
    def test_get_portfolio_data_failure(self, mock_request, portfolio_integration):
        """Test portfolio data retrieval failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        # Test portfolio data retrieval
        portfolio_data = portfolio_integration.get_portfolio_data('nonexistent-portfolio')
        
        # Verify results
        assert portfolio_data is None
    
    @patch('requests.Session.request')
    def test_update_portfolio_risk_metrics(self, mock_request, portfolio_integration):
        """Test updating portfolio risk metrics."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_request.return_value = mock_response
        
        # Test risk metrics update
        risk_metrics = {
            'var_95': 100.0,
            'var_99': 150.0,
            'portfolio_volatility': 0.15
        }
        
        result = portfolio_integration.update_portfolio_risk_metrics(
            'test-portfolio-123', risk_metrics
        )
        
        # Verify results
        assert result is True
    
    def test_health_check(self, portfolio_integration):
        """Test portfolio integration health check."""
        with patch('requests.Session.request') as mock_request:
            # Mock successful health check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy'}
            mock_request.return_value = mock_response
            
            health = portfolio_integration.health_check()
            
            assert health['status'] == 'healthy'
            assert health['service'] == 'portfolio_service_integration'


class TestTradingEngineIntegration:
    """Test trading engine integration."""
    
    @pytest.fixture
    def trading_engine_integration(self):
        """Create trading engine integration instance."""
        return TradingEngineIntegration(
            trading_engine_url="http://test-trading-engine:80",
            timeout_seconds=5,
            retry_attempts=1
        )
    
    @pytest.fixture
    def mock_trade_data(self):
        """Mock trade data."""
        return {
            'trade_id': 'trade-123',
            'symbol': 'AAPL',
            'side': 'BUY',
            'quantity': 10,
            'price': 150.0
        }
    
    @pytest.fixture
    def mock_risk_limits(self):
        """Mock risk limits."""
        return [
            {
                'limit_type': 'position_size',
                'limit_value': 0.15,
                'limit_unit': 'percentage'
            },
            {
                'limit_type': 'daily_loss',
                'limit_value': 1000.0,
                'limit_unit': 'dollars'
            }
        ]
    
    def test_validate_trade_risk_approved(self, trading_engine_integration, mock_trade_data, mock_risk_limits):
        """Test trade risk validation - approved trade."""
        # Test trade validation
        result = trading_engine_integration.validate_trade_risk(
            mock_trade_data, 'test-portfolio-123', mock_risk_limits
        )
        
        # Verify results
        assert isinstance(result, RiskCheckResult)
        assert result.trade_id == 'trade-123'
        assert result.approved is True  # Mock implementation approves small trades
        assert result.risk_score < 0.7
        assert len(result.risk_factors) == 0
        assert len(result.warnings) == 0
    
    def test_validate_trade_risk_rejected(self, trading_engine_integration, mock_risk_limits):
        """Test trade risk validation - rejected trade."""
        # Create large trade that should be rejected
        large_trade_data = {
            'trade_id': 'trade-456',
            'symbol': 'AAPL',
            'side': 'BUY',
            'quantity': 1000,  # Large quantity
            'price': 150.0
        }
        
        # Test trade validation
        result = trading_engine_integration.validate_trade_risk(
            large_trade_data, 'test-portfolio-123', mock_risk_limits
        )
        
        # Verify results
        assert isinstance(result, RiskCheckResult)
        assert result.trade_id == 'trade-456'
        assert result.approved is False  # Should be rejected due to size
        assert result.risk_score >= 0.7
        assert len(result.risk_factors) > 0
        assert len(result.recommendations) > 0
    
    @patch('requests.Session.request')
    def test_get_recent_trades(self, mock_request, trading_engine_integration):
        """Test getting recent trades."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'trades': [
                    {
                        'trade_id': 'trade-123',
                        'symbol': 'AAPL',
                        'side': 'BUY',
                        'quantity': 10,
                        'price': 150.0,
                        'timestamp': datetime.utcnow().isoformat(),
                        'strategy': 'momentum',
                        'portfolio_id': 'test-portfolio-123'
                    }
                ]
            }
        }
        mock_request.return_value = mock_response
        
        # Test getting recent trades
        trades = trading_engine_integration.get_recent_trades('test-portfolio-123')
        
        # Verify results
        assert len(trades) == 1
        assert trades[0].trade_id == 'trade-123'
        assert trades[0].symbol == 'AAPL'
        assert trades[0].side == 'BUY'
        assert trades[0].quantity == 10
        assert trades[0].price == 150.0
    
    def test_health_check(self, trading_engine_integration):
        """Test trading engine integration health check."""
        with patch('requests.Session.request') as mock_request:
            # Mock successful health check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy'}
            mock_request.return_value = mock_response
            
            health = trading_engine_integration.health_check()
            
            assert health['status'] == 'healthy'
            assert health['service'] == 'trading_engine_integration'


class TestMarketDataServiceIntegration:
    """Test market data service integration."""
    
    @pytest.fixture
    def market_data_integration(self):
        """Create market data integration instance."""
        return MarketDataServiceIntegration(
            market_data_service_url="http://test-market-data:80",
            timeout_seconds=5,
            retry_attempts=1
        )
    
    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return {
            'AAPL': {
                'price': 150.0,
                'volume': 1000000,
                'bid': 149.9,
                'ask': 150.1,
                'high': 151.0,
                'low': 149.0,
                'open': 149.5,
                'timestamp': datetime.utcnow().isoformat()
            },
            'GOOGL': {
                'price': 2800.0,
                'volume': 500000,
                'bid': 2799.5,
                'ask': 2800.5,
                'high': 2810.0,
                'low': 2795.0,
                'open': 2798.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    @patch('requests.Session.request')
    def test_get_current_prices(self, mock_request, market_data_integration, mock_price_data):
        """Test getting current prices."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'prices': mock_price_data
            }
        }
        mock_request.return_value = mock_response
        
        # Test getting current prices
        prices = market_data_integration.get_current_prices(['AAPL', 'GOOGL'])
        
        # Verify results
        assert len(prices) == 2
        assert 'AAPL' in prices
        assert 'GOOGL' in prices
        assert prices['AAPL'].price == 150.0
        assert prices['GOOGL'].price == 2800.0
        assert prices['AAPL'].symbol == 'AAPL'
        assert prices['GOOGL'].symbol == 'GOOGL'
    
    @patch('requests.Session.request')
    def test_get_historical_data(self, mock_request, market_data_integration):
        """Test getting historical data."""
        # Mock historical data
        historical_data = [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'open': 149.0,
                'high': 151.0,
                'low': 148.5,
                'close': 150.0,
                'volume': 1000000
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'open': 150.0,
                'high': 152.0,
                'low': 149.5,
                'close': 151.5,
                'volume': 1200000
            }
        ]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'historical_data': historical_data
            }
        }
        mock_request.return_value = mock_response
        
        # Test getting historical data
        start_date = datetime.utcnow() - timedelta(days=2)
        end_date = datetime.utcnow()
        
        historical = market_data_integration.get_historical_data(
            'AAPL', start_date, end_date
        )
        
        # Verify results
        assert historical is not None
        assert historical.symbol == 'AAPL'
        assert len(historical.data) == 2
        assert historical.frequency == '1D'
    
    @patch('requests.Session.request')
    def test_get_volatility_data(self, mock_request, market_data_integration):
        """Test getting volatility data."""
        # Mock volatility data
        volatility_data = {
            'AAPL': {
                'volatility_30d': 0.25,
                'volatility_90d': 0.22,
                'volatility_1y': 0.20
            },
            'GOOGL': {
                'volatility_30d': 0.30,
                'volatility_90d': 0.28,
                'volatility_1y': 0.25
            }
        }
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'volatility': volatility_data
            }
        }
        mock_request.return_value = mock_response
        
        # Test getting volatility data
        volatility = market_data_integration.get_volatility_data(['AAPL', 'GOOGL'])
        
        # Verify results
        assert len(volatility) == 2
        assert 'AAPL' in volatility
        assert 'GOOGL' in volatility
        assert volatility['AAPL']['volatility_30d'] == 0.25
        assert volatility['GOOGL']['volatility_30d'] == 0.30
    
    def test_health_check(self, market_data_integration):
        """Test market data integration health check."""
        with patch('requests.Session.request') as mock_request:
            # Mock successful health check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy'}
            mock_request.return_value = mock_response
            
            health = market_data_integration.health_check()
            
            assert health['status'] == 'healthy'
            assert health['service'] == 'market_data_service_integration'


class TestDataSynchronizationService:
    """Test data synchronization service."""
    
    @pytest.fixture
    def data_sync_service(self):
        """Create data synchronization service instance."""
        return DataSynchronizationService(
            sync_interval_minutes=1,  # Short interval for testing
            batch_size=10,
            retry_attempts=1,
            timeout_seconds=5
        )
    
    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data."""
        return PortfolioData(
            portfolio_id='test-portfolio-123',
            positions=[
                {'symbol': 'AAPL', 'quantity': 10, 'current_price': 150.0},
                {'symbol': 'GOOGL', 'quantity': 5, 'current_price': 2800.0}
            ],
            total_value=10000.0,
            cash_balance=2000.0,
            last_updated=datetime.utcnow(),
            metadata={}
        )
    
    def test_sync_portfolio_data_success(self, data_sync_service, mock_portfolio_data):
        """Test successful portfolio data synchronization."""
        with patch.object(data_sync_service.portfolio_integration, 'get_portfolio_list') as mock_list, \
             patch.object(data_sync_service.portfolio_integration, 'get_portfolio_data') as mock_data, \
             patch.object(data_sync_service.portfolio_integration, 'update_portfolio_risk_metrics') as mock_update:
            
            # Mock portfolio list
            mock_list.return_value = [{'portfolio_id': 'test-portfolio-123'}]
            
            # Mock portfolio data
            mock_data.return_value = mock_portfolio_data
            
            # Mock successful update
            mock_update.return_value = True
            
            # Test synchronization
            sync_status = data_sync_service.sync_portfolio_data()
            
            # Verify results
            assert isinstance(sync_status, SyncStatus)
            assert sync_status.service == 'portfolio_data'
            assert sync_status.status == 'success'
            assert sync_status.records_synced == 1
            assert sync_status.error_message is None
    
    def test_sync_portfolio_data_failure(self, data_sync_service):
        """Test portfolio data synchronization failure."""
        with patch.object(data_sync_service.portfolio_integration, 'get_portfolio_list') as mock_list:
            # Mock portfolio list failure
            mock_list.side_effect = Exception("Connection failed")
            
            # Test synchronization
            sync_status = data_sync_service.sync_portfolio_data()
            
            # Verify results
            assert isinstance(sync_status, SyncStatus)
            assert sync_status.service == 'portfolio_data'
            assert sync_status.status == 'error'
            assert sync_status.records_synced == 0
            assert sync_status.error_message is not None
    
    def test_sync_trade_data_success(self, data_sync_service):
        """Test successful trade data synchronization."""
        with patch.object(data_sync_service.portfolio_integration, 'get_portfolio_list') as mock_list, \
             patch.object(data_sync_service.trading_engine_integration, 'get_recent_trades') as mock_trades:
            
            # Mock portfolio list
            mock_list.return_value = [{'portfolio_id': 'test-portfolio-123'}]
            
            # Mock recent trades
            mock_trade = Mock()
            mock_trade.trade_id = 'trade-123'
            mock_trade.symbol = 'AAPL'
            mock_trade.side = 'BUY'
            mock_trade.quantity = 10
            mock_trade.price = 150.0
            mock_trades.return_value = [mock_trade]
            
            # Test synchronization
            sync_status = data_sync_service.sync_trade_data()
            
            # Verify results
            assert isinstance(sync_status, SyncStatus)
            assert sync_status.service == 'trade_data'
            assert sync_status.status == 'success'
            assert sync_status.records_synced == 1
            assert sync_status.error_message is None
    
    def test_sync_market_data_success(self, data_sync_service):
        """Test successful market data synchronization."""
        with patch.object(data_sync_service.portfolio_integration, 'get_portfolio_list') as mock_list, \
             patch.object(data_sync_service.portfolio_integration, 'get_portfolio_positions') as mock_positions, \
             patch.object(data_sync_service.market_data_integration, 'get_current_prices') as mock_prices, \
             patch.object(data_sync_service.market_data_integration, 'get_volatility_data') as mock_volatility, \
             patch.object(data_sync_service.market_data_integration, 'get_correlation_matrix') as mock_correlation:
            
            # Mock portfolio list
            mock_list.return_value = [{'portfolio_id': 'test-portfolio-123'}]
            
            # Mock portfolio positions
            mock_positions.return_value = [
                {'symbol': 'AAPL'}, {'symbol': 'GOOGL'}
            ]
            
            # Mock market data responses
            mock_prices.return_value = {'AAPL': Mock(), 'GOOGL': Mock()}
            mock_volatility.return_value = {'AAPL': {}, 'GOOGL': {}}
            mock_correlation.return_value = Mock()
            
            # Test synchronization
            sync_status = data_sync_service.sync_market_data()
            
            # Verify results
            assert isinstance(sync_status, SyncStatus)
            assert sync_status.service == 'market_data'
            assert sync_status.status == 'success'
            assert sync_status.records_synced > 0
            assert sync_status.error_message is None
    
    def test_get_sync_status(self, data_sync_service):
        """Test getting synchronization status."""
        # Test empty status
        status = data_sync_service.get_sync_status()
        assert isinstance(status, dict)
        assert len(status) == 0
        
        # Test specific service status
        status = data_sync_service.get_sync_status('portfolio_data')
        assert status is None or isinstance(status, dict)
    
    def test_get_sync_health(self, data_sync_service):
        """Test getting synchronization health."""
        # Test health with no sync status
        health = data_sync_service.get_sync_health()
        
        assert isinstance(health, dict)
        assert 'status' in health
        assert 'service' in health
        assert health['service'] == 'data_synchronization'
        assert health['total_services'] == 0
        assert health['healthy_services'] == 0


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""
    
    def test_complete_risk_assessment_workflow(self):
        """Test complete risk assessment workflow."""
        # This would test the complete workflow from portfolio data retrieval
        # through risk calculation to risk monitoring and alerting
        pass
    
    def test_risk_breach_notification_workflow(self):
        """Test risk breach notification workflow."""
        # This would test the complete workflow from risk limit breach detection
        # through notification to trading engine and portfolio service
        pass
    
    def test_data_consistency_across_services(self):
        """Test data consistency across all services."""
        # This would test that data remains consistent across all integrated services
        pass
    
    def test_performance_under_load(self):
        """Test system performance under load."""
        # This would test the system's performance when handling multiple
        # portfolios and high-frequency data updates
        pass


# Integration test configuration
@pytest.fixture(scope="session")
def integration_test_config():
    """Integration test configuration."""
    return {
        'test_timeout': 30,
        'mock_services': True,
        'test_data_cleanup': True
    }


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup logic would go here
    pass

