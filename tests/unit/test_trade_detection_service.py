"""
Unit tests for TradeDetectionService
Tests the TradeDetectionService functionality and error handling
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from decimal import Decimal
import httpx

from src.services.trade_recovery.services.trade_detection_service import (
    TradeDetectionService, TradeDetectionError, BrokerAPIError, TradeConversionError
)
from src.services.trade_recovery.models.active_trade import (
    ActiveTrade, TradeSide, PositionType, OptionDetails
)


class TestTradeDetectionService:
    """Test cases for TradeDetectionService"""
    
    @pytest.fixture
    def mock_broker_client(self):
        """Mock broker API client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def trade_detection_service(self, mock_broker_client):
        """Create TradeDetectionService instance with mocked dependencies"""
        return TradeDetectionService(
            broker_api_url="http://test-broker.com",
            api_key="test-api-key",
            timeout=30
        )
    
    def test_trade_detection_service_initialization(self):
        """Test TradeDetectionService initialization"""
        service = TradeDetectionService(
            broker_api_url="http://test-broker.com",
            api_key="test-api-key",
            timeout=30
        )
        
        assert service.broker_api_url == "http://test-broker.com"
        assert service.api_key == "test-api-key"
        assert service.timeout == 30
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_detect_active_trades_success(self, trade_detection_service):
        """Test successful active trade detection"""
        # Mock broker API response
        mock_positions = [
            {
                "id": "pos_1",
                "symbol": "AAPL",
                "quantity": 100.0,
                "side": "BUY",
                "entry_price": 150.00,
                "current_price": 155.00,
                "entry_date": "2024-01-15T10:30:00Z",
                "position_type": "STOCK"
            },
            {
                "id": "pos_2",
                "symbol": "TSLA",
                "quantity": 50.0,
                "side": "SELL",
                "entry_price": 200.00,
                "current_price": 195.00,
                "entry_date": "2024-01-15T11:00:00Z",
                "position_type": "STOCK"
            }
        ]
        
        with patch.object(trade_detection_service, '_get_positions_from_broker', return_value=mock_positions):
            trades = await trade_detection_service.detect_active_trades("acc_123")
        
        assert len(trades) == 2
        
        # Check first trade
        trade1 = trades[0]
        assert trade1.account_id == "acc_123"
        assert trade1.symbol == "AAPL"
        assert trade1.quantity == Decimal("100.0")
        assert trade1.side == TradeSide.BUY
        assert trade1.entry_price == Decimal("150.00")
        assert trade1.current_price == Decimal("155.00")
        assert trade1.position_type == PositionType.STOCK
        
        # Check second trade
        trade2 = trades[1]
        assert trade2.account_id == "acc_123"
        assert trade2.symbol == "TSLA"
        assert trade2.quantity == Decimal("50.0")
        assert trade2.side == TradeSide.SELL
        assert trade2.entry_price == Decimal("200.00")
        assert trade2.current_price == Decimal("195.00")
        assert trade2.position_type == PositionType.STOCK
    
    @pytest.mark.asyncio
    async def test_detect_active_trades_with_options(self, trade_detection_service):
        """Test active trade detection with options"""
        mock_positions = [
            {
                "id": "pos_1",
                "symbol": "AAPL",
                "quantity": 10.0,
                "side": "BUY",
                "entry_price": 5.00,
                "current_price": 6.00,
                "entry_date": "2024-01-15T10:30:00Z",
                "position_type": "OPTION",
                "option_details": {
                    "strike": 150.00,
                    "expiration": "2024-12-20T00:00:00Z",
                    "option_type": "CALL"
                }
            }
        ]
        
        with patch.object(trade_detection_service, '_get_positions_from_broker', return_value=mock_positions):
            trades = await trade_detection_service.detect_active_trades("acc_123")
        
        assert len(trades) == 1
        
        trade = trades[0]
        assert trade.position_type == PositionType.OPTION
        assert trade.option_details is not None
        assert trade.option_details.strike == Decimal("150.00")
        assert trade.option_details.option_type == "CALL"
    
    @pytest.mark.asyncio
    async def test_detect_active_trades_broker_api_error(self, trade_detection_service):
        """Test active trade detection with broker API error"""
        with patch.object(trade_detection_service, '_get_positions_from_broker', side_effect=BrokerAPIError("API Error")):
            with pytest.raises(TradeDetectionError) as exc_info:
                await trade_detection_service.detect_active_trades("acc_123")
            
            assert "Failed to detect active trades" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_detect_active_trades_position_conversion_error(self, trade_detection_service):
        """Test active trade detection with position conversion error"""
        mock_positions = [
            {
                "id": "pos_1",
                "symbol": "AAPL",
                "quantity": "invalid_quantity",  # Invalid quantity
                "side": "BUY",
                "entry_price": 150.00,
                "position_type": "STOCK"
            }
        ]
        
        with patch.object(trade_detection_service, '_get_positions_from_broker', return_value=mock_positions):
            trades = await trade_detection_service.detect_active_trades("acc_123")
        
        # Should return empty list due to conversion error
        assert len(trades) == 0
    
    @pytest.mark.asyncio
    async def test_get_trade_details_success(self, trade_detection_service):
        """Test successful trade details retrieval"""
        mock_position = {
            "id": "pos_1",
            "symbol": "AAPL",
            "quantity": 100.0,
            "side": "BUY",
            "entry_price": 150.00,
            "current_price": 155.00,
            "entry_date": "2024-01-15T10:30:00Z",
            "position_type": "STOCK"
        }
        
        with patch.object(trade_detection_service, '_get_position_details_from_broker', return_value=mock_position):
            trade = await trade_detection_service.get_trade_details("acc_123", "AAPL")
        
        assert trade is not None
        assert trade.symbol == "AAPL"
        assert trade.account_id == "acc_123"
        assert trade.quantity == Decimal("100.0")
        assert trade.side == TradeSide.BUY
    
    @pytest.mark.asyncio
    async def test_get_trade_details_not_found(self, trade_detection_service):
        """Test trade details retrieval when trade not found"""
        with patch.object(trade_detection_service, '_get_position_details_from_broker', return_value=None):
            trade = await trade_detection_service.get_trade_details("acc_123", "NONEXISTENT")
        
        assert trade is None
    
    @pytest.mark.asyncio
    async def test_get_account_summary_success(self, trade_detection_service):
        """Test successful account summary retrieval"""
        mock_summary = {
            "account_id": "acc_123",
            "total_value": 50000.00,
            "cash_balance": 10000.00,
            "positions_count": 5,
            "unrealized_pnl": 2500.00
        }
        
        with patch.object(trade_detection_service, '_get_account_summary_from_broker', return_value=mock_summary):
            summary = await trade_detection_service.get_account_summary("acc_123")
        
        assert summary == mock_summary
    
    @pytest.mark.asyncio
    async def test_get_positions_from_broker_success(self, trade_detection_service):
        """Test successful positions retrieval from broker API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"positions": [{"id": "pos_1", "symbol": "AAPL"}]}
        
        with patch.object(trade_detection_service.client, 'get', return_value=mock_response):
            positions = await trade_detection_service._get_positions_from_broker("acc_123")
        
        assert len(positions) == 1
        assert positions[0]["id"] == "pos_1"
        assert positions[0]["symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_get_positions_from_broker_api_error(self, trade_detection_service):
        """Test positions retrieval with broker API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch.object(trade_detection_service.client, 'get', return_value=mock_response):
            with pytest.raises(Exception) as exc_info:
                await trade_detection_service._get_positions_from_broker("acc_123")
            
            assert "Broker API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_positions_from_broker_timeout(self, trade_detection_service):
        """Test positions retrieval with timeout error"""
        with patch.object(trade_detection_service.client, 'get', side_effect=httpx.TimeoutException("Timeout")):
            with pytest.raises(TradeDetectionError) as exc_info:
                await trade_detection_service._get_positions_from_broker("acc_123")
            
            assert "Broker API timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_positions_from_broker_network_error(self, trade_detection_service):
        """Test positions retrieval with network error"""
        with patch.object(trade_detection_service.client, 'get', side_effect=httpx.RequestError("Network Error")):
            with pytest.raises(TradeDetectionError) as exc_info:
                await trade_detection_service._get_positions_from_broker("acc_123")
            
            assert "Broker API request failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_position_details_from_broker_success(self, trade_detection_service):
        """Test successful position details retrieval from broker API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "pos_1", "symbol": "AAPL"}
        
        with patch.object(trade_detection_service.client, 'get', return_value=mock_response):
            position = await trade_detection_service._get_position_details_from_broker("acc_123", "AAPL")
        
        assert position is not None
        assert position["id"] == "pos_1"
        assert position["symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_get_position_details_from_broker_not_found(self, trade_detection_service):
        """Test position details retrieval when position not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(trade_detection_service.client, 'get', return_value=mock_response):
            position = await trade_detection_service._get_position_details_from_broker("acc_123", "NONEXISTENT")
        
        assert position is None
    
    @pytest.mark.asyncio
    async def test_get_account_summary_from_broker_success(self, trade_detection_service):
        """Test successful account summary retrieval from broker API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"account_id": "acc_123", "total_value": 50000.00}
        
        with patch.object(trade_detection_service.client, 'get', return_value=mock_response):
            summary = await trade_detection_service._get_account_summary_from_broker("acc_123")
        
        assert summary is not None
        assert summary["account_id"] == "acc_123"
        assert summary["total_value"] == 50000.00
    
    @pytest.mark.asyncio
    async def test_convert_position_to_trade_success(self, trade_detection_service):
        """Test successful position to trade conversion"""
        position = {
            "id": "pos_1",
            "symbol": "AAPL",
            "quantity": 100.0,
            "side": "BUY",
            "entry_price": 150.00,
            "current_price": 155.00,
            "entry_date": "2024-01-15T10:30:00Z",
            "position_type": "STOCK"
        }
        
        trade = await trade_detection_service._convert_position_to_trade(position, "acc_123")
        
        assert trade.account_id == "acc_123"
        assert trade.symbol == "AAPL"
        assert trade.quantity == Decimal("100.0")
        assert trade.side == TradeSide.BUY
        assert trade.entry_price == Decimal("150.00")
        assert trade.current_price == Decimal("155.00")
        assert trade.position_type == PositionType.STOCK
    
    @pytest.mark.asyncio
    async def test_convert_position_to_trade_with_option_details(self, trade_detection_service):
        """Test position to trade conversion with option details"""
        position = {
            "id": "pos_1",
            "symbol": "AAPL",
            "quantity": 10.0,
            "side": "BUY",
            "entry_price": 5.00,
            "current_price": 6.00,
            "entry_date": "2024-01-15T10:30:00Z",
            "position_type": "OPTION",
            "option_details": {
                "strike": 150.00,
                "expiration": "2024-12-20T00:00:00Z",
                "option_type": "CALL"
            }
        }
        
        trade = await trade_detection_service._convert_position_to_trade(position, "acc_123")
        
        assert trade.position_type == PositionType.OPTION
        assert trade.option_details is not None
        assert trade.option_details.strike == Decimal("150.00")
        assert trade.option_details.option_type == "CALL"
    
    @pytest.mark.asyncio
    async def test_convert_position_to_trade_conversion_error(self, trade_detection_service):
        """Test position to trade conversion with invalid data"""
        position = {
            "id": "pos_1",
            "symbol": "AAPL",
            "quantity": "invalid_quantity",  # Invalid quantity
            "side": "BUY",
            "entry_price": 150.00,
            "position_type": "STOCK"
        }
        
        with pytest.raises(TradeConversionError) as exc_info:
            await trade_detection_service._convert_position_to_trade(position, "acc_123")
        
        assert "Failed to convert position to trade" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_recovery_log(self, trade_detection_service):
        """Test recovery log creation"""
        from src.services.trade_recovery.models.recovery_log import LogAction, LogSeverity
        
        log = await trade_detection_service.create_recovery_log(
            recovery_session_id="session_123",
            action=LogAction.TRADE_DETECTED,
            details={"symbol": "AAPL", "quantity": 100},
            user_id="user_456",
            trade_id="trade_789",
            strategy_name="Elliott Wave",
            severity=LogSeverity.INFO
        )
        
        assert log.recovery_session_id == "session_123"
        assert log.action == LogAction.TRADE_DETECTED
        assert log.details == {"symbol": "AAPL", "quantity": 100}
        assert log.user_id == "user_456"
        assert log.trade_id == "trade_789"
        assert log.strategy_name == "Elliott Wave"
        assert log.severity == LogSeverity.INFO
    
    @pytest.mark.asyncio
    async def test_close_client(self, trade_detection_service):
        """Test closing HTTP client"""
        with patch.object(trade_detection_service.client, 'aclose') as mock_close:
            await trade_detection_service.close()
            mock_close.assert_called_once()


class TestTradeDetectionError:
    """Test cases for TradeDetectionError exception"""
    
    def test_trade_detection_error_creation(self):
        """Test TradeDetectionError creation"""
        error = TradeDetectionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestBrokerAPIError:
    """Test cases for BrokerAPIError exception"""
    
    def test_broker_api_error_creation(self):
        """Test BrokerAPIError creation"""
        error = BrokerAPIError("API error message")
        assert str(error) == "API error message"
        assert isinstance(error, Exception)


class TestTradeConversionError:
    """Test cases for TradeConversionError exception"""
    
    def test_trade_conversion_error_creation(self):
        """Test TradeConversionError creation"""
        error = TradeConversionError("Conversion error message")
        assert str(error) == "Conversion error message"
        assert isinstance(error, Exception)




















