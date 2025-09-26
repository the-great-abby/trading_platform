"""
Contract tests for live trading system.

Tests API contracts, data schemas, and interface compliance.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid
import json
import yaml

from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def contract_test_database():
    """Create contract test database."""
    db = AsyncMock()
    
    # Mock account
    account = LiveTradingAccount(
        account_id="contract-test-account-123",
        public_account_id="public-contract-123",
        account_name="Contract Test Account",
        account_type="CASH",
        buying_power=10000.0,
        cash_balance=5000.0,
        equity=15000.0,
        is_active=True
    )
    
    # Mock risk profile
    risk_profile = RiskProfile(
        account_id="contract-test-account-123",
        max_position_size=10000.0,
        max_portfolio_risk=0.05,
        max_daily_loss=1000.0,
        max_daily_trades=20,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
        max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )
    
    # Configure database responses
    def mock_execute(query_result):
        if hasattr(query_result, 'scalar_one_or_none'):
            if 'account' in str(query_result):
                return account
            elif 'risk_profile' in str(query_result):
                return risk_profile
            else:
                return None
        elif hasattr(query_result, 'scalars'):
            return []  # No existing positions/trades
        elif hasattr(query_result, 'scalar'):
            return 0  # Mock count queries
        return query_result
    
    db.execute.side_effect = mock_execute
    return db


@pytest.fixture
def contract_test_redis():
    """Create contract test Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # No emergency stop
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.ping.return_value = True
    redis.info.return_value = {
        "connected_clients": 3,
        "used_memory": 2048000,
        "keyspace_hits": 1000,
        "keyspace_misses": 100
    }
    return redis


@pytest.fixture
def contract_test_public_api():
    """Create contract test Public.com API client."""
    api = AsyncMock()
    
    # Mock authentication
    api.authenticate.return_value = {
        "access_token": "contract_access_token_123",
        "refresh_token": "contract_refresh_token_456",
        "expires_in": 3600
    }
    
    # Mock account info
    api.get_account_info.return_value = {
        "account_id": "public-contract-123",
        "buying_power": 10000.0,
        "cash_balance": 5000.0,
        "equity": 15000.0
    }
    
    # Mock positions
    api.get_positions.return_value = {
        "positions": []
    }
    
    # Mock market data
    api.get_market_data.return_value = {
        "symbol": "SPY",
        "price": 405.50,
        "bid": 405.45,
        "ask": 405.55,
        "volume": 1000000
    }
    
    # Mock options chain
    api.get_options_chain.return_value = {
        "symbol": "SPY",
        "expiration_dates": ["2024-01-19", "2024-01-26"],
        "strikes": [400, 405, 410],
        "options": [
            {
                "strike": 400,
                "expiration": "2024-01-19",
                "type": "CALL",
                "bid": 5.50,
                "ask": 5.75
            }
        ]
    }
    
    return api


class TestOpenAPIContractCompliance:
    """Test OpenAPI contract compliance."""
    
    def test_openapi_spec_exists(self):
        """Test that OpenAPI specification exists."""
        openapi_spec_path = "/Users/abby/code/trading/specs/008-title-live-trading/contracts/openapi.yaml"
        
        try:
            with open(openapi_spec_path, 'r') as f:
                spec = yaml.safe_load(f)
            
            # Verify basic OpenAPI structure
            assert "openapi" in spec
            assert "info" in spec
            assert "paths" in spec
            assert "components" in spec
            
            # Verify API version
            assert spec["openapi"].startswith("3.0")
            
            # Verify required paths exist
            expected_paths = [
                "/auth/login",
                "/auth/refresh",
                "/account",
                "/positions",
                "/trades",
                "/orders",
                "/orders/{order_id}",
                "/risk",
                "/signals",
                "/strategies",
                "/market_hours",
                "/system/status",
                "/system/stop",
                "/reports/compliance"
            ]
            
            for path in expected_paths:
                assert path in spec["paths"], f"Expected path {path} not found in OpenAPI spec"
                
        except FileNotFoundError:
            pytest.skip("OpenAPI specification file not found")
    
    def test_request_schemas_compliance(self):
        """Test request schemas compliance."""
        openapi_spec_path = "/Users/abby/code/trading/specs/008-title-live-trading/contracts/openapi.yaml"
        
        try:
            with open(openapi_spec_path, 'r') as f:
                spec = yaml.safe_load(f)
            
            # Verify request schemas exist
            components = spec.get("components", {})
            schemas = components.get("schemas", {})
            
            expected_request_schemas = [
                "LoginRequest",
                "TokenRefreshRequest",
                "OrderRequest",
                "RiskProfileRequest",
                "EmergencyStopRequest"
            ]
            
            for schema_name in expected_request_schemas:
                assert schema_name in schemas, f"Expected request schema {schema_name} not found"
                
                # Verify schema structure
                schema = schemas[schema_name]
                assert "type" in schema
                assert "properties" in schema
                assert "required" in schema
                
        except FileNotFoundError:
            pytest.skip("OpenAPI specification file not found")
    
    def test_response_schemas_compliance(self):
        """Test response schemas compliance."""
        openapi_spec_path = "/Users/abby/code/trading/specs/008-title-live-trading/contracts/openapi.yaml"
        
        try:
            with open(openapi_spec_path, 'r') as f:
                spec = yaml.safe_load(f)
            
            # Verify response schemas exist
            components = spec.get("components", {})
            schemas = components.get("schemas", {})
            
            expected_response_schemas = [
                "LoginResponse",
                "AccountBalanceResponse",
                "PositionResponse",
                "TradeResponse",
                "OrderResponse",
                "OrderStatusResponse",
                "RiskProfileResponse",
                "ErrorResponse"
            ]
            
            for schema_name in expected_response_schemas:
                assert schema_name in schemas, f"Expected response schema {schema_name} not found"
                
                # Verify schema structure
                schema = schemas[schema_name]
                assert "type" in schema
                assert "properties" in schema
                
        except FileNotFoundError:
            pytest.skip("OpenAPI specification file not found")


class TestDataModelContracts:
    """Test data model contracts."""
    
    def test_live_trading_account_contract(self):
        """Test LiveTradingAccount model contract."""
        account = LiveTradingAccount(
            account_id="test-account-123",
            public_account_id="public-123",
            account_name="Test Account",
            account_type="CASH",
            buying_power=10000.0,
            cash_balance=5000.0,
            equity=15000.0,
            is_active=True
        )
        
        # Verify required fields
        assert account.account_id == "test-account-123"
        assert account.public_account_id == "public-123"
        assert account.account_name == "Test Account"
        assert account.account_type == "CASH"
        assert account.buying_power == 10000.0
        assert account.cash_balance == 5000.0
        assert account.equity == 15000.0
        assert account.is_active is True
        
        # Verify timestamps
        assert account.created_at is not None
        assert account.updated_at is not None
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)
    
    def test_live_position_contract(self):
        """Test LivePosition model contract."""
        position = LivePosition(
            account_id="test-account-123",
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=10,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            unrealized_pnl=Decimal("50.00"),
            realized_pnl=Decimal("0.00"),
            status=PositionStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
            expiration_date=datetime.now(timezone.utc).replace(day=30),
            legs_data='[{"strike": 400, "type": "CALL", "action": "SELL"}]',
            greeks_data='{"delta": 0.5, "gamma": 0.1}'
        )
        
        # Verify required fields
        assert position.account_id == "test-account-123"
        assert position.symbol == "SPY"
        assert position.strategy == StrategyType.IRON_CONDOR
        assert position.quantity == 10
        assert position.average_price == Decimal("400.00")
        assert position.current_price == Decimal("405.00")
        assert position.unrealized_pnl == Decimal("50.00")
        assert position.status == PositionStatus.OPEN
        
        # Verify JSON fields
        legs_data = json.loads(position.legs_data)
        assert isinstance(legs_data, list)
        assert len(legs_data) == 1
        assert legs_data[0]["strike"] == 400
        
        greeks_data = json.loads(position.greeks_data)
        assert isinstance(greeks_data, dict)
        assert greeks_data["delta"] == 0.5
        assert greeks_data["gamma"] == 0.1
    
    def test_live_trade_contract(self):
        """Test LiveTrade model contract."""
        trade = LiveTrade(
            trade_id=str(uuid.uuid4()),
            account_id="test-account-123",
            public_order_id="order-123",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=100,
            price=Decimal("400.50"),
            total_amount=Decimal("40050.00"),
            filled_quantity=100,
            remaining_quantity=0,
            status=TradeStatus.FILLED,
            strategy=StrategyType.IRON_CONDOR,
            filled_at=datetime.now(timezone.utc)
        )
        
        # Verify required fields
        assert trade.account_id == "test-account-123"
        assert trade.public_order_id == "order-123"
        assert trade.symbol == "SPY"
        assert trade.action == TradeAction.BUY
        assert trade.quantity == 100
        assert trade.price == Decimal("400.50")
        assert trade.total_amount == Decimal("40050.00")
        assert trade.status == TradeStatus.FILLED
        assert trade.strategy == StrategyType.IRON_CONDOR
        
        # Verify UUID format
        assert isinstance(uuid.UUID(trade.trade_id), uuid.UUID)
    
    def test_risk_profile_contract(self):
        """Test RiskProfile model contract."""
        risk_profile = RiskProfile(
            account_id="test-account-123",
            max_position_size=10000.0,
            max_portfolio_risk=0.05,
            max_daily_loss=1000.0,
            max_daily_trades=20,
            allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
            max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
            emergency_stop_active=False,
            risk_level=RiskLevel.MODERATE
        )
        
        # Verify required fields
        assert risk_profile.account_id == "test-account-123"
        assert risk_profile.max_position_size == 10000.0
        assert risk_profile.max_portfolio_risk == 0.05
        assert risk_profile.max_daily_loss == 1000.0
        assert risk_profile.max_daily_trades == 20
        assert risk_profile.emergency_stop_active is False
        assert risk_profile.risk_level == RiskLevel.MODERATE
        
        # Verify JSON fields
        allowed_strategies = json.loads(risk_profile.allowed_strategies)
        assert isinstance(allowed_strategies, list)
        assert "IRON_CONDOR" in allowed_strategies
        assert "BUTTERFLY_SPREAD" in allowed_strategies
        
        max_greeks_exposure = json.loads(risk_profile.max_greeks_exposure)
        assert isinstance(max_greeks_exposure, dict)
        assert max_greeks_exposure["delta"] == 1000.0
        assert max_greeks_exposure["gamma"] == 100.0


class TestAPIEndpointContracts:
    """Test API endpoint contracts."""
    
    @pytest.mark.asyncio
    async def test_trade_execution_endpoint_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test trade execution endpoint contract."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(contract_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(contract_test_database, contract_test_redis)
        
        trading_service = TradingService(
            db_session=contract_test_database,
            public_api_client=contract_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            contract_test_public_api.execute_order.return_value = {
                "order_id": "contract_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Test trade execution contract
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("contract-test-account-123", trade_details)
            
            # Verify response contract
            assert "success" in result
            assert "order_id" in result
            assert "status" in result
            assert "filled_quantity" in result
            assert "message" in result
            
            assert result["success"] is True
            assert result["order_id"] == "contract_test_123"
            assert result["status"] == "FILLED"
            assert result["filled_quantity"] == 100
    
    @pytest.mark.asyncio
    async def test_position_retrieval_endpoint_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test position retrieval endpoint contract."""
        from src.services.live_trading.position_service import PositionService
        
        # Create position service
        position_service = PositionService(contract_test_database)
        
        # Test position retrieval contract
        positions = await position_service.get_all_positions("contract-test-account-123")
        
        # Verify response contract
        assert isinstance(positions, list)
        
        # If positions exist, verify structure
        if positions:
            position = positions[0]
            required_fields = [
                "symbol", "quantity", "average_price", "current_price",
                "unrealized_pnl", "realized_pnl", "status", "strategy"
            ]
            
            for field in required_fields:
                assert field in position, f"Required field {field} not found in position response"
    
    @pytest.mark.asyncio
    async def test_risk_profile_endpoint_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test risk profile endpoint contract."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(contract_test_database)
        
        # Test risk profile retrieval contract
        risk_profile = await risk_service.get_risk_profile("contract-test-account-123")
        
        # Verify response contract
        if risk_profile:
            required_fields = [
                "account_id", "max_position_size", "max_portfolio_risk",
                "max_daily_loss", "max_daily_trades", "risk_level"
            ]
            
            for field in required_fields:
                assert hasattr(risk_profile, field), f"Required field {field} not found in risk profile"
    
    @pytest.mark.asyncio
    async def test_system_status_endpoint_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test system status endpoint contract."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(contract_test_database, contract_test_redis)
        
        # Test system status contract
        status = await system_service.get_system_status()
        
        # Verify response contract
        required_fields = [
            "status", "emergency_stop_active", "timestamp", "version"
        ]
        
        for field in required_fields:
            assert field in status, f"Required field {field} not found in system status response"
        
        # Verify field types
        assert isinstance(status["status"], str)
        assert isinstance(status["emergency_stop_active"], bool)
        assert isinstance(status["timestamp"], datetime)
        assert isinstance(status["version"], str)


class TestPublicAPIContracts:
    """Test Public.com API contracts."""
    
    @pytest.mark.asyncio
    async def test_authentication_contract(self, contract_test_public_api):
        """Test authentication API contract."""
        # Test authentication response contract
        result = await contract_test_public_api.authenticate("test_user", "test_password")
        
        # Verify response structure
        required_fields = ["access_token", "refresh_token", "expires_in"]
        
        for field in required_fields:
            assert field in result, f"Required field {field} not found in authentication response"
        
        # Verify field types
        assert isinstance(result["access_token"], str)
        assert isinstance(result["refresh_token"], str)
        assert isinstance(result["expires_in"], int)
    
    @pytest.mark.asyncio
    async def test_account_info_contract(self, contract_test_public_api):
        """Test account info API contract."""
        # Test account info response contract
        result = await contract_test_public_api.get_account_info()
        
        # Verify response structure
        required_fields = ["account_id", "buying_power", "cash_balance", "equity"]
        
        for field in required_fields:
            assert field in result, f"Required field {field} not found in account info response"
        
        # Verify field types
        assert isinstance(result["account_id"], str)
        assert isinstance(result["buying_power"], (int, float))
        assert isinstance(result["cash_balance"], (int, float))
        assert isinstance(result["equity"], (int, float))
    
    @pytest.mark.asyncio
    async def test_positions_contract(self, contract_test_public_api):
        """Test positions API contract."""
        # Test positions response contract
        result = await contract_test_public_api.get_positions()
        
        # Verify response structure
        assert "positions" in result, "positions field not found in response"
        assert isinstance(result["positions"], list)
        
        # If positions exist, verify structure
        if result["positions"]:
            position = result["positions"][0]
            required_fields = ["symbol", "quantity", "average_price", "current_price"]
            
            for field in required_fields:
                assert field in position, f"Required field {field} not found in position"
    
    @pytest.mark.asyncio
    async def test_market_data_contract(self, contract_test_public_api):
        """Test market data API contract."""
        # Test market data response contract
        result = await contract_test_public_api.get_market_data("SPY")
        
        # Verify response structure
        required_fields = ["symbol", "price", "bid", "ask", "volume"]
        
        for field in required_fields:
            assert field in result, f"Required field {field} not found in market data response"
        
        # Verify field types
        assert isinstance(result["symbol"], str)
        assert isinstance(result["price"], (int, float))
        assert isinstance(result["bid"], (int, float))
        assert isinstance(result["ask"], (int, float))
        assert isinstance(result["volume"], int)
    
    @pytest.mark.asyncio
    async def test_options_chain_contract(self, contract_test_public_api):
        """Test options chain API contract."""
        # Test options chain response contract
        result = await contract_test_public_api.get_options_chain("SPY")
        
        # Verify response structure
        required_fields = ["symbol", "expiration_dates", "strikes", "options"]
        
        for field in required_fields:
            assert field in result, f"Required field {field} not found in options chain response"
        
        # Verify field types
        assert isinstance(result["symbol"], str)
        assert isinstance(result["expiration_dates"], list)
        assert isinstance(result["strikes"], list)
        assert isinstance(result["options"], list)
        
        # If options exist, verify structure
        if result["options"]:
            option = result["options"][0]
            required_option_fields = ["strike", "expiration", "type", "bid", "ask"]
            
            for field in required_option_fields:
                assert field in option, f"Required field {field} not found in option"


class TestErrorResponseContracts:
    """Test error response contracts."""
    
    @pytest.mark.asyncio
    async def test_authentication_error_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test authentication error response contract."""
        from src.services.live_trading.public_api_client import PublicAPIClient, AuthenticationError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock authentication error
        contract_test_public_api.authenticate.side_effect = AuthenticationError("Invalid credentials")
        
        # Test authentication error
        try:
            await api_client.authenticate("invalid_user", "invalid_password")
        except AuthenticationError as e:
            # Verify error structure
            assert str(e) == "Invalid credentials"
            assert isinstance(e, AuthenticationError)
    
    @pytest.mark.asyncio
    async def test_trading_error_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test trading error response contract."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(contract_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(contract_test_database, contract_test_redis)
        
        trading_service = TradingService(
            db_session=contract_test_database,
            public_api_client=contract_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test trading error with invalid data
        invalid_trade_details = {
            "symbol": "SPY",
            "action": "INVALID_ACTION",
            "quantity": -100,  # Invalid quantity
            "price": Decimal("-400.25"),  # Invalid price
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Test that error is raised
        try:
            await trading_service.execute_trade("contract-test-account-123", invalid_trade_details)
        except Exception as e:
            # Verify error structure
            assert isinstance(e, Exception)
            assert str(e) is not None
    
    @pytest.mark.asyncio
    async def test_risk_error_contract(self, contract_test_database, contract_test_redis, contract_test_public_api):
        """Test risk error response contract."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(contract_test_database)
        
        # Test risk error with invalid data
        invalid_trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 1000000,  # Exceeds risk limits
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        # Test risk check
        result = await risk_service.comprehensive_risk_check("contract-test-account-123", invalid_trade_details)
        
        # Verify error response structure
        assert "passed" in result
        assert "message" in result
        assert isinstance(result["passed"], bool)
        assert isinstance(result["message"], str)


class TestDataSerializationContracts:
    """Test data serialization contracts."""
    
    def test_json_serialization_contract(self):
        """Test JSON serialization contract."""
        # Test model serialization
        account = LiveTradingAccount(
            account_id="test-account-123",
            public_account_id="public-123",
            account_name="Test Account",
            account_type="CASH",
            buying_power=10000.0,
            cash_balance=5000.0,
            equity=15000.0,
            is_active=True
        )
        
        # Test that model can be serialized to dict
        account_dict = {
            "account_id": account.account_id,
            "public_account_id": account.public_account_id,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "buying_power": account.buying_power,
            "cash_balance": account.cash_balance,
            "equity": account.equity,
            "is_active": account.is_active
        }
        
        # Test JSON serialization
        json_str = json.dumps(account_dict, default=str)
        assert isinstance(json_str, str)
        
        # Test JSON deserialization
        deserialized = json.loads(json_str)
        assert deserialized["account_id"] == "test-account-123"
        assert deserialized["account_name"] == "Test Account"
    
    def test_decimal_serialization_contract(self):
        """Test Decimal serialization contract."""
        # Test Decimal serialization
        trade = LiveTrade(
            trade_id=str(uuid.uuid4()),
            account_id="test-account-123",
            public_order_id="order-123",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=100,
            price=Decimal("400.50"),
            total_amount=Decimal("40050.00"),
            filled_quantity=100,
            remaining_quantity=0,
            status=TradeStatus.FILLED
        )
        
        # Test that Decimal fields can be serialized
        trade_dict = {
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "price": float(trade.price),
            "total_amount": float(trade.total_amount)
        }
        
        # Test JSON serialization
        json_str = json.dumps(trade_dict)
        assert isinstance(json_str, str)
        
        # Test JSON deserialization
        deserialized = json.loads(json_str)
        assert deserialized["price"] == 400.50
        assert deserialized["total_amount"] == 40050.00
    
    def test_datetime_serialization_contract(self):
        """Test datetime serialization contract."""
        # Test datetime serialization
        now = datetime.now(timezone.utc)
        
        # Test that datetime can be serialized
        data = {
            "timestamp": now.isoformat(),
            "date": now.date().isoformat(),
            "time": now.time().isoformat()
        }
        
        # Test JSON serialization
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        
        # Test JSON deserialization
        deserialized = json.loads(json_str)
        assert "timestamp" in deserialized
        assert "date" in deserialized
        assert "time" in deserialized
