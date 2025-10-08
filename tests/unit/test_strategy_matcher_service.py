"""
Unit tests for StrategyMatcherService
Tests the StrategyMatcherService functionality and strategy matching logic
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from decimal import Decimal

from src.services.trade_recovery.services.strategy_matcher_service import (
    StrategyMatcherService, StrategyMatcherError
)
from src.services.trade_recovery.models.active_trade import (
    ActiveTrade, TradeSide, PositionType
)
from src.services.trade_recovery.models.strategy_assignment import (
    StrategyAssignment, AssignmentReason, AssignmentStatus
)


class TestStrategyMatcherService:
    """Test cases for StrategyMatcherService"""
    
    @pytest.fixture
    def mock_strategy_client(self):
        """Mock strategy service client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_market_data_client(self):
        """Mock market data service client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def strategy_matcher_service(self, mock_strategy_client, mock_market_data_client):
        """Create StrategyMatcherService instance with mocked dependencies"""
        return StrategyMatcherService(
            strategy_service_url="http://test-strategy.com",
            market_data_service_url="http://test-market.com",
            timeout=30
        )
    
    @pytest.fixture
    def sample_trade(self):
        """Create a sample ActiveTrade for testing"""
        return ActiveTrade(
            id="trade_123",
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            entry_time=datetime(2024, 1, 15, 10, 30, 0),
            detected_at=datetime.utcnow(),
            position_type=PositionType.STOCK
        )
    
    def test_strategy_matcher_service_initialization(self):
        """Test StrategyMatcherService initialization"""
        service = StrategyMatcherService(
            strategy_service_url="http://test-strategy.com",
            market_data_service_url="http://test-market.com",
            timeout=30
        )
        
        assert service.strategy_service_url == "http://test-strategy.com"
        assert service.market_data_service_url == "http://test-market.com"
        assert service.timeout == 30
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_get_available_strategies_success(self, strategy_matcher_service):
        """Test successful retrieval of available strategies"""
        mock_strategies = [
            {
                "id": "strategy_1",
                "name": "Elliott Wave Strategy",
                "description": "Elliott Wave pattern detection",
                "is_active": True,
                "confidence_threshold": 0.7
            },
            {
                "id": "strategy_2",
                "name": "Moving Average Strategy",
                "description": "Moving average crossover strategy",
                "is_active": True,
                "confidence_threshold": 0.6
            }
        ]
        
        with patch.object(strategy_matcher_service, '_get_strategies_from_service', return_value=mock_strategies):
            strategies = await strategy_matcher_service.get_available_strategies("acc_123")
        
        assert len(strategies) == 2
        assert strategies[0]["id"] == "strategy_1"
        assert strategies[0]["name"] == "Elliott Wave Strategy"
        assert strategies[1]["id"] == "strategy_2"
        assert strategies[1]["name"] == "Moving Average Strategy"
    
    @pytest.mark.asyncio
    async def test_get_available_strategies_service_error(self, strategy_matcher_service):
        """Test available strategies retrieval with service error"""
        with patch.object(strategy_matcher_service, '_get_strategies_from_service', side_effect=Exception("Service Error")):
            with pytest.raises(StrategyMatcherError) as exc_info:
                await strategy_matcher_service.get_available_strategies("acc_123")
            
            assert "Failed to get available strategies" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_match_strategies_success(self, strategy_matcher_service, sample_trade):
        """Test successful strategy matching"""
        mock_matches = [
            {
                "strategy_id": "strategy_1",
                "strategy_name": "Elliott Wave Strategy",
                "confidence_score": 0.85,
                "match_reason": "High confidence Elliott Wave pattern detected",
                "market_conditions": "Bullish trend with clear wave structure"
            },
            {
                "strategy_id": "strategy_2",
                "strategy_name": "Moving Average Strategy",
                "confidence_score": 0.65,
                "match_reason": "Price above moving averages",
                "market_conditions": "Uptrend confirmed"
            }
        ]
        
        with patch.object(strategy_matcher_service, '_match_strategies_from_service', return_value=mock_matches):
            matches = await strategy_matcher_service.match_strategies(sample_trade)
        
        assert len(matches) == 2
        assert matches[0]["strategy_id"] == "strategy_1"
        assert matches[0]["confidence_score"] == 0.85
        assert matches[1]["strategy_id"] == "strategy_2"
        assert matches[1]["confidence_score"] == 0.65
    
    @pytest.mark.asyncio
    async def test_match_strategies_no_matches(self, strategy_matcher_service, sample_trade):
        """Test strategy matching with no matches"""
        with patch.object(strategy_matcher_service, '_match_strategies_from_service', return_value=[]):
            matches = await strategy_matcher_service.match_strategies(sample_trade)
        
        assert len(matches) == 0
    
    @pytest.mark.asyncio
    async def test_match_strategies_service_error(self, strategy_matcher_service, sample_trade):
        """Test strategy matching with service error"""
        with patch.object(strategy_matcher_service, '_match_strategies_from_service', side_effect=Exception("Service Error")):
            with pytest.raises(StrategyMatcherError) as exc_info:
                await strategy_matcher_service.match_strategies(sample_trade)
            
            assert "Failed to match strategies" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_suggest_fallback_strategies_success(self, strategy_matcher_service, sample_trade):
        """Test successful fallback strategy suggestions"""
        mock_suggestions = [
            {
                "strategy_id": "strategy_3",
                "strategy_name": "Conservative Strategy",
                "confidence_score": 0.45,
                "suggestion_reason": "Conservative approach for uncertain market conditions",
                "market_conditions": "Mixed signals, low volatility"
            },
            {
                "strategy_id": "strategy_4",
                "strategy_name": "Default Strategy",
                "confidence_score": 0.30,
                "suggestion_reason": "Default fallback strategy",
                "market_conditions": "No clear pattern detected"
            }
        ]
        
        with patch.object(strategy_matcher_service, '_suggest_fallback_strategies', return_value=mock_suggestions):
            suggestions = await strategy_matcher_service.suggest_fallback_strategies(sample_trade)
        
        assert len(suggestions) == 2
        assert suggestions[0]["strategy_id"] == "strategy_3"
        assert suggestions[0]["confidence_score"] == 0.45
        assert suggestions[1]["strategy_id"] == "strategy_4"
        assert suggestions[1]["confidence_score"] == 0.30
    
    @pytest.mark.asyncio
    async def test_suggest_fallback_strategies_service_error(self, strategy_matcher_service, sample_trade):
        """Test fallback strategy suggestions with service error"""
        with patch.object(strategy_matcher_service, '_suggest_fallback_strategies', side_effect=Exception("Service Error")):
            with pytest.raises(StrategyMatcherError) as exc_info:
                await strategy_matcher_service.suggest_fallback_strategies(sample_trade)
            
            assert "Failed to suggest fallback strategies" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_strategy_details_success(self, strategy_matcher_service):
        """Test successful strategy details retrieval"""
        mock_details = {
            "id": "strategy_1",
            "name": "Elliott Wave Strategy",
            "description": "Elliott Wave pattern detection strategy",
            "parameters": {
                "wave_count": 5,
                "confidence_threshold": 0.7
            },
            "performance_metrics": {
                "win_rate": 0.65,
                "avg_return": 0.12
            }
        }
        
        with patch.object(strategy_matcher_service, '_get_strategy_details_from_service', return_value=mock_details):
            details = await strategy_matcher_service.get_strategy_details("strategy_1")
        
        assert details is not None
        assert details["id"] == "strategy_1"
        assert details["name"] == "Elliott Wave Strategy"
        assert details["parameters"]["wave_count"] == 5
    
    @pytest.mark.asyncio
    async def test_get_strategy_details_not_found(self, strategy_matcher_service):
        """Test strategy details retrieval when strategy not found"""
        with patch.object(strategy_matcher_service, '_get_strategy_details_from_service', return_value=None):
            details = await strategy_matcher_service.get_strategy_details("nonexistent_strategy")
        
        assert details is None
    
    @pytest.mark.asyncio
    async def test_get_strategies_from_service_success(self, strategy_matcher_service):
        """Test successful strategies retrieval from service"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "strategies": [
                {"id": "strategy_1", "name": "Elliott Wave Strategy"},
                {"id": "strategy_2", "name": "Moving Average Strategy"}
            ]
        }
        
        with patch.object(strategy_matcher_service.client, 'get', return_value=mock_response):
            strategies = await strategy_matcher_service._get_strategies_from_service("acc_123")
        
        assert len(strategies) == 2
        assert strategies[0]["id"] == "strategy_1"
        assert strategies[1]["id"] == "strategy_2"
    
    @pytest.mark.asyncio
    async def test_get_strategies_from_service_api_error(self, strategy_matcher_service):
        """Test strategies retrieval with API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch.object(strategy_matcher_service.client, 'get', return_value=mock_response):
            with pytest.raises(Exception) as exc_info:
                await strategy_matcher_service._get_strategies_from_service("acc_123")
            
            assert "Strategy service error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_match_strategies_from_service_success(self, strategy_matcher_service, sample_trade):
        """Test successful strategy matching from service"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "matches": [
                {
                    "strategy_id": "strategy_1",
                    "strategy_name": "Elliott Wave Strategy",
                    "confidence_score": 0.85,
                    "match_reason": "High confidence match"
                }
            ]
        }
        
        with patch.object(strategy_matcher_service.client, 'post', return_value=mock_response):
            matches = await strategy_matcher_service._match_strategies_from_service(sample_trade)
        
        assert len(matches) == 1
        assert matches[0]["strategy_id"] == "strategy_1"
        assert matches[0]["confidence_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_match_strategies_from_service_no_matches(self, strategy_matcher_service, sample_trade):
        """Test strategy matching from service with no matches"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"matches": []}
        
        with patch.object(strategy_matcher_service.client, 'post', return_value=mock_response):
            matches = await strategy_matcher_service._match_strategies_from_service(sample_trade)
        
        assert len(matches) == 0
    
    @pytest.mark.asyncio
    async def test_suggest_fallback_strategies_success(self, strategy_matcher_service, sample_trade):
        """Test successful fallback strategy suggestions from service"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestions": [
                {
                    "strategy_id": "strategy_3",
                    "strategy_name": "Conservative Strategy",
                    "confidence_score": 0.45,
                    "suggestion_reason": "Conservative approach"
                }
            ]
        }
        
        with patch.object(strategy_matcher_service.client, 'post', return_value=mock_response):
            suggestions = await strategy_matcher_service._suggest_fallback_strategies(sample_trade)
        
        assert len(suggestions) == 1
        assert suggestions[0]["strategy_id"] == "strategy_3"
        assert suggestions[0]["confidence_score"] == 0.45
    
    @pytest.mark.asyncio
    async def test_get_strategy_details_from_service_success(self, strategy_matcher_service):
        """Test successful strategy details retrieval from service"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "strategy_1",
            "name": "Elliott Wave Strategy",
            "description": "Elliott Wave pattern detection"
        }
        
        with patch.object(strategy_matcher_service.client, 'get', return_value=mock_response):
            details = await strategy_matcher_service._get_strategy_details_from_service("strategy_1")
        
        assert details is not None
        assert details["id"] == "strategy_1"
        assert details["name"] == "Elliott Wave Strategy"
    
    @pytest.mark.asyncio
    async def test_get_strategy_details_from_service_not_found(self, strategy_matcher_service):
        """Test strategy details retrieval from service when not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(strategy_matcher_service.client, 'get', return_value=mock_response):
            details = await strategy_matcher_service._get_strategy_details_from_service("nonexistent_strategy")
        
        assert details is None
    
    @pytest.mark.asyncio
    async def test_validate_trade_for_matching_success(self, strategy_matcher_service, sample_trade):
        """Test successful trade validation for matching"""
        is_valid = await strategy_matcher_service._validate_trade_for_matching(sample_trade)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_trade_for_matching_invalid_trade(self, strategy_matcher_service):
        """Test trade validation with invalid trade"""
        invalid_trade = ActiveTrade(
            id="trade_123",
            account_id="acc_123",
            symbol="",  # Empty symbol
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            position_type=PositionType.STOCK
        )
        
        is_valid = await strategy_matcher_service._validate_trade_for_matching(invalid_trade)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_calculate_match_confidence_success(self, strategy_matcher_service):
        """Test successful match confidence calculation"""
        trade_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "entry_price": 150.00,
            "current_price": 155.00
        }
        
        strategy_data = {
            "id": "strategy_1",
            "name": "Elliott Wave Strategy",
            "parameters": {
                "confidence_threshold": 0.7
            }
        }
        
        market_data = {
            "trend": "bullish",
            "volatility": "low",
            "volume": "high"
        }
        
        confidence = await strategy_matcher_service._calculate_match_confidence(
            trade_data, strategy_data, market_data
        )
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_close_client(self, strategy_matcher_service):
        """Test closing HTTP client"""
        with patch.object(strategy_matcher_service.client, 'aclose') as mock_close:
            await strategy_matcher_service.close()
            mock_close.assert_called_once()


class TestStrategyMatcherError:
    """Test cases for StrategyMatcherError exception"""
    
    def test_strategy_matcher_error_creation(self):
        """Test StrategyMatcherError creation"""
        error = StrategyMatcherError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)




















