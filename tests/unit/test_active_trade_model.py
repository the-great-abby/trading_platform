"""
Unit tests for ActiveTrade model
Tests the ActiveTrade Pydantic model validation and behavior
"""
import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from src.services.trade_recovery.models.active_trade import (
    ActiveTrade, ActiveTradeCreate, TradeSide, PositionType, OptionDetails
)


class TestActiveTradeModel:
    """Test cases for ActiveTrade model"""
    
    def test_active_trade_creation_valid_data(self):
        """Test creating ActiveTrade with valid data"""
        trade_data = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("100.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("150.00"),
            "current_price": Decimal("155.00"),
            "entry_date": datetime(2024, 1, 15, 10, 30, 0),
            "position_type": PositionType.STOCK
        }
        
        trade = ActiveTrade(**trade_data)
        
        assert trade.account_id == "acc_123"
        assert trade.symbol == "AAPL"
        assert trade.quantity == Decimal("100.0")
        assert trade.side == TradeSide.BUY
        assert trade.entry_price == Decimal("150.00")
        assert trade.current_price == Decimal("155.00")
        assert trade.position_type == PositionType.STOCK
        assert trade.unrealized_pnl is None  # Should be calculated
        assert trade.detected_at is not None
        assert trade.created_at is not None
        assert trade.updated_at is not None
    
    def test_active_trade_creation_minimal_data(self):
        """Test creating ActiveTrade with minimal required data"""
        trade_data = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("100.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("150.00"),
            "position_type": PositionType.STOCK
        }
        
        trade = ActiveTrade(**trade_data)
        
        assert trade.account_id == "acc_123"
        assert trade.symbol == "AAPL"
        assert trade.quantity == Decimal("100.0")
        assert trade.side == TradeSide.BUY
        assert trade.entry_price == Decimal("150.00")
        assert trade.position_type == PositionType.STOCK
        assert trade.current_price is None
        assert trade.unrealized_pnl is None
        assert trade.entry_date is None
        assert trade.detected_at is not None
    
    def test_active_trade_validation_missing_required_fields(self):
        """Test validation fails with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            ActiveTrade(
                symbol="AAPL",
                quantity=Decimal("100.0"),
                side=TradeSide.BUY,
                entry_price=Decimal("150.00")
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("account_id",) for error in errors)
    
    def test_active_trade_validation_invalid_side(self):
        """Test validation fails with invalid side"""
        with pytest.raises(ValidationError) as exc_info:
            ActiveTrade(
                account_id="acc_123",
                symbol="AAPL",
                quantity=Decimal("100.0"),
                side="INVALID_SIDE",
                entry_price=Decimal("150.00"),
                position_type=PositionType.STOCK
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("side",) for error in errors)
    
    def test_active_trade_validation_negative_quantity(self):
        """Test validation fails with negative quantity"""
        with pytest.raises(ValidationError) as exc_info:
            ActiveTrade(
                account_id="acc_123",
                symbol="AAPL",
                quantity=Decimal("-100.0"),
                side=TradeSide.BUY,
                entry_price=Decimal("150.00"),
                position_type=PositionType.STOCK
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("quantity",) for error in errors)
    
    def test_active_trade_validation_negative_prices(self):
        """Test validation fails with negative prices"""
        with pytest.raises(ValidationError) as exc_info:
            ActiveTrade(
                account_id="acc_123",
                symbol="AAPL",
                quantity=Decimal("100.0"),
                side=TradeSide.BUY,
                entry_price=Decimal("-150.00"),
                position_type=PositionType.STOCK
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("entry_price",) for error in errors)
    
    def test_active_trade_with_option_details(self):
        """Test creating ActiveTrade with option details"""
        option_details = OptionDetails(
            strike=Decimal("150.00"),
            expiration=datetime(2024, 12, 20),
            option_type="CALL"
        )
        
        trade_data = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("10.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("5.00"),
            "position_type": PositionType.OPTION,
            "option_details": option_details
        }
        
        trade = ActiveTrade(**trade_data)
        
        assert trade.position_type == PositionType.OPTION
        assert trade.option_details is not None
        assert trade.option_details.strike == Decimal("150.00")
        assert trade.option_details.expiration == datetime(2024, 12, 20)
        assert trade.option_details.option_type == "CALL"
    
    def test_active_trade_calculate_unrealized_pnl(self):
        """Test calculating unrealized P&L"""
        trade = ActiveTrade(
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            position_type=PositionType.STOCK
        )
        
        # Calculate P&L for long position
        expected_pnl = (Decimal("155.00") - Decimal("150.00")) * Decimal("100.0")
        assert trade.unrealized_pnl == expected_pnl
        
        # Test short position
        short_trade = ActiveTrade(
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.SELL,
            entry_price=Decimal("150.00"),
            current_price=Decimal("145.00"),
            position_type=PositionType.STOCK
        )
        
        expected_short_pnl = (Decimal("150.00") - Decimal("145.00")) * Decimal("100.0")
        assert short_trade.unrealized_pnl == expected_short_pnl
    
    def test_active_trade_calculate_unrealized_pnl_no_current_price(self):
        """Test P&L calculation when current price is None"""
        trade = ActiveTrade(
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=None,
            position_type=PositionType.STOCK
        )
        
        assert trade.unrealized_pnl is None
    
    def test_active_trade_serialization(self):
        """Test ActiveTrade serialization to dict"""
        trade = ActiveTrade(
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            position_type=PositionType.STOCK
        )
        
        trade_dict = trade.dict()
        
        assert isinstance(trade_dict, dict)
        assert trade_dict["account_id"] == "acc_123"
        assert trade_dict["symbol"] == "AAPL"
        assert trade_dict["quantity"] == Decimal("100.0")
        assert trade_dict["side"] == TradeSide.BUY
        assert trade_dict["entry_price"] == Decimal("150.00")
        assert trade_dict["current_price"] == Decimal("155.00")
        assert trade_dict["position_type"] == PositionType.STOCK
    
    def test_active_trade_json_serialization(self):
        """Test ActiveTrade JSON serialization"""
        trade = ActiveTrade(
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            position_type=PositionType.STOCK
        )
        
        json_str = trade.json()
        
        assert isinstance(json_str, str)
        assert "acc_123" in json_str
        assert "AAPL" in json_str
        assert "100.0" in json_str
    
    def test_active_trade_from_dict(self):
        """Test creating ActiveTrade from dictionary"""
        trade_dict = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("100.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("150.00"),
            "current_price": Decimal("155.00"),
            "position_type": PositionType.STOCK,
            "detected_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        trade = ActiveTrade(**trade_dict)
        
        assert trade.account_id == "acc_123"
        assert trade.symbol == "AAPL"
        assert trade.quantity == Decimal("100.0")
        assert trade.side == TradeSide.BUY
        assert trade.entry_price == Decimal("150.00")
        assert trade.current_price == Decimal("155.00")
        assert trade.position_type == PositionType.STOCK


class TestActiveTradeCreate:
    """Test cases for ActiveTradeCreate model"""
    
    def test_active_trade_create_valid_data(self):
        """Test creating ActiveTradeCreate with valid data"""
        trade_data = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("100.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("150.00"),
            "current_price": Decimal("155.00"),
            "entry_date": datetime(2024, 1, 15, 10, 30, 0),
            "position_type": PositionType.STOCK
        }
        
        trade_create = ActiveTradeCreate(**trade_data)
        
        assert trade_create.account_id == "acc_123"
        assert trade_create.symbol == "AAPL"
        assert trade_create.quantity == Decimal("100.0")
        assert trade_create.side == TradeSide.BUY
        assert trade_create.entry_price == Decimal("150.00")
        assert trade_create.current_price == Decimal("155.00")
        assert trade_create.position_type == PositionType.STOCK
    
    def test_active_trade_create_minimal_data(self):
        """Test creating ActiveTradeCreate with minimal required data"""
        trade_data = {
            "account_id": "acc_123",
            "symbol": "AAPL",
            "quantity": Decimal("100.0"),
            "side": TradeSide.BUY,
            "entry_price": Decimal("150.00"),
            "position_type": PositionType.STOCK
        }
        
        trade_create = ActiveTradeCreate(**trade_data)
        
        assert trade_create.account_id == "acc_123"
        assert trade_create.symbol == "AAPL"
        assert trade_create.quantity == Decimal("100.0")
        assert trade_create.side == TradeSide.BUY
        assert trade_create.entry_price == Decimal("150.00")
        assert trade_create.position_type == PositionType.STOCK
        assert trade_create.current_price is None
        assert trade_create.entry_date is None
        assert trade_create.option_details is None


class TestTradeSide:
    """Test cases for TradeSide enum"""
    
    def test_trade_side_values(self):
        """Test TradeSide enum values"""
        assert TradeSide.BUY == "BUY"
        assert TradeSide.SELL == "SELL"
    
    def test_trade_side_validation(self):
        """Test TradeSide validation"""
        assert TradeSide("BUY") == TradeSide.BUY
        assert TradeSide("SELL") == TradeSide.SELL
        
        with pytest.raises(ValueError):
            TradeSide("INVALID")


class TestPositionType:
    """Test cases for PositionType enum"""
    
    def test_position_type_values(self):
        """Test PositionType enum values"""
        assert PositionType.STOCK == "STOCK"
        assert PositionType.OPTION == "OPTION"
        assert PositionType.FUTURE == "FUTURE"
        assert PositionType.CRYPTO == "CRYPTO"
    
    def test_position_type_validation(self):
        """Test PositionType validation"""
        assert PositionType("STOCK") == PositionType.STOCK
        assert PositionType("OPTION") == PositionType.OPTION
        assert PositionType("FUTURE") == PositionType.FUTURE
        assert PositionType("CRYPTO") == PositionType.CRYPTO
        
        with pytest.raises(ValueError):
            PositionType("INVALID")


class TestOptionDetails:
    """Test cases for OptionDetails model"""
    
    def test_option_details_creation(self):
        """Test creating OptionDetails with valid data"""
        option_details = OptionDetails(
            strike=Decimal("150.00"),
            expiration=datetime(2024, 12, 20),
            option_type="CALL"
        )
        
        assert option_details.strike == Decimal("150.00")
        assert option_details.expiration == datetime(2024, 12, 20)
        assert option_details.option_type == "CALL"
    
    def test_option_details_optional_fields(self):
        """Test OptionDetails with optional fields"""
        option_details = OptionDetails(
            strike=None,
            expiration=None,
            option_type=None
        )
        
        assert option_details.strike is None
        assert option_details.expiration is None
        assert option_details.option_type is None
    
    def test_option_details_validation_negative_strike(self):
        """Test OptionDetails validation with negative strike"""
        with pytest.raises(ValidationError) as exc_info:
            OptionDetails(
                strike=Decimal("-150.00"),
                expiration=datetime(2024, 12, 20),
                option_type="CALL"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("strike",) for error in errors)
    
    def test_option_details_serialization(self):
        """Test OptionDetails serialization"""
        option_details = OptionDetails(
            strike=Decimal("150.00"),
            expiration=datetime(2024, 12, 20),
            option_type="CALL"
        )
        
        option_dict = option_details.dict()
        
        assert isinstance(option_dict, dict)
        assert option_dict["strike"] == Decimal("150.00")
        assert option_dict["expiration"] == datetime(2024, 12, 20)
        assert option_dict["option_type"] == "CALL"








