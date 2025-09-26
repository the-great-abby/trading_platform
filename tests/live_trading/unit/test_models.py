"""
Unit tests for live trading entity models.

Tests the SQLAlchemy models for data validation, relationships, and constraints.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, 
    APICredentials, TradeSignal, OrderStatus, Base,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_account():
    """Create a sample trading account."""
    return LiveTradingAccount(
        account_id="test-account-123",
        public_account_id="public-123",
        account_name="Test Account",
        account_type="CASH",
        buying_power=10000.0,
        cash_balance=5000.0,
        equity=15000.0,
        is_active=True
    )


@pytest.fixture
def sample_risk_profile(sample_account):
    """Create a sample risk profile."""
    return RiskProfile(
        account_id=sample_account.account_id,
        max_position_size=10000.0,
        max_portfolio_risk=0.05,
        max_daily_loss=1000.0,
        max_daily_trades=20,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
        max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )


class TestLiveTradingAccount:
    """Test LiveTradingAccount model."""
    
    def test_create_account(self, db_session, sample_account):
        """Test creating a trading account."""
        db_session.add(sample_account)
        db_session.commit()
        
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert account is not None
        assert account.account_id == "test-account-123"
        assert account.public_account_id == "public-123"
        assert account.account_name == "Test Account"
        assert account.account_type == "CASH"
        assert account.buying_power == 10000.0
        assert account.cash_balance == 5000.0
        assert account.equity == 15000.0
        assert account.is_active is True
    
    def test_account_timestamps(self, db_session, sample_account):
        """Test that timestamps are automatically set."""
        db_session.add(sample_account)
        db_session.commit()
        
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert account.created_at is not None
        assert account.updated_at is not None
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)
    
    def test_account_unique_constraint(self, db_session):
        """Test that account_id is unique."""
        account1 = LiveTradingAccount(
            account_id="duplicate-id",
            public_account_id="public-1",
            account_name="Account 1",
            account_type="CASH"
        )
        account2 = LiveTradingAccount(
            account_id="duplicate-id",
            public_account_id="public-2",
            account_name="Account 2",
            account_type="CASH"
        )
        
        db_session.add(account1)
        db_session.commit()
        
        db_session.add(account2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestLivePosition:
    """Test LivePosition model."""
    
    def test_create_position(self, db_session, sample_account):
        """Test creating a position."""
        position = LivePosition(
            account_id=sample_account.account_id,
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
        
        db_session.add(position)
        db_session.commit()
        
        saved_position = db_session.query(LivePosition).filter_by(
            account_id=sample_account.account_id,
            symbol="SPY"
        ).first()
        
        assert saved_position is not None
        assert saved_position.symbol == "SPY"
        assert saved_position.strategy == StrategyType.IRON_CONDOR
        assert saved_position.quantity == 10
        assert saved_position.average_price == Decimal("400.00")
        assert saved_position.current_price == Decimal("405.00")
        assert saved_position.unrealized_pnl == Decimal("50.00")
        assert saved_position.status == PositionStatus.OPEN
    
    def test_position_unique_constraint(self, db_session, sample_account):
        """Test that account_id + symbol combination is unique."""
        position1 = LivePosition(
            account_id=sample_account.account_id,
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=10,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            status=PositionStatus.OPEN
        )
        position2 = LivePosition(
            account_id=sample_account.account_id,
            symbol="SPY",
            strategy=StrategyType.BUTTERFLY_SPREAD,
            quantity=5,
            average_price=Decimal("300.00"),
            current_price=Decimal("305.00"),
            status=PositionStatus.OPEN
        )
        
        db_session.add(position1)
        db_session.commit()
        
        db_session.add(position2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestLiveTrade:
    """Test LiveTrade model."""
    
    def test_create_trade(self, db_session, sample_account):
        """Test creating a trade."""
        trade = LiveTrade(
            account_id=sample_account.account_id,
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
            leg_data='[{"strike": 400, "type": "CALL"}]',
            filled_at=datetime.now(timezone.utc)
        )
        
        db_session.add(trade)
        db_session.commit()
        
        saved_trade = db_session.query(LiveTrade).filter_by(
            trade_id=trade.trade_id
        ).first()
        
        assert saved_trade is not None
        assert saved_trade.account_id == sample_account.account_id
        assert saved_trade.public_order_id == "order-123"
        assert saved_trade.symbol == "SPY"
        assert saved_trade.action == TradeAction.BUY
        assert saved_trade.quantity == 100
        assert saved_trade.price == Decimal("400.50")
        assert saved_trade.status == TradeStatus.FILLED
        assert saved_trade.strategy == StrategyType.IRON_CONDOR


class TestRiskProfile:
    """Test RiskProfile model."""
    
    def test_create_risk_profile(self, db_session, sample_account, sample_risk_profile):
        """Test creating a risk profile."""
        db_session.add(sample_risk_profile)
        db_session.commit()
        
        risk_profile = db_session.query(RiskProfile).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert risk_profile is not None
        assert risk_profile.max_position_size == 10000.0
        assert risk_profile.max_portfolio_risk == 0.05
        assert risk_profile.max_daily_loss == 1000.0
        assert risk_profile.max_daily_trades == 20
        assert risk_profile.emergency_stop_active is False
        assert risk_profile.risk_level == RiskLevel.MODERATE
    
    def test_risk_profile_unique_constraint(self, db_session, sample_account):
        """Test that each account can only have one risk profile."""
        risk_profile1 = RiskProfile(
            account_id=sample_account.account_id,
            max_position_size=10000.0,
            max_portfolio_risk=0.05,
            max_daily_loss=1000.0,
            max_daily_trades=20,
            risk_level=RiskLevel.MODERATE
        )
        risk_profile2 = RiskProfile(
            account_id=sample_account.account_id,
            max_position_size=5000.0,
            max_portfolio_risk=0.03,
            max_daily_loss=500.0,
            max_daily_trades=10,
            risk_level=RiskLevel.CONSERVATIVE
        )
        
        db_session.add(risk_profile1)
        db_session.commit()
        
        db_session.add(risk_profile2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAPICredentials:
    """Test APICredentials model."""
    
    def test_create_api_credentials(self, db_session, sample_account):
        """Test creating API credentials."""
        credentials = APICredentials(
            account_id=sample_account.account_id,
            brokerage="public",
            encrypted_api_key="encrypted_key_123",
            encrypted_api_secret="encrypted_secret_456",
            access_token="access_token_789",
            refresh_token="refresh_token_abc",
            token_expires_at=datetime.now(timezone.utc).replace(day=30),
            is_active=True
        )
        
        db_session.add(credentials)
        db_session.commit()
        
        saved_credentials = db_session.query(APICredentials).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert saved_credentials is not None
        assert saved_credentials.brokerage == "public"
        assert saved_credentials.encrypted_api_key == "encrypted_key_123"
        assert saved_credentials.access_token == "access_token_789"
        assert saved_credentials.is_active is True
    
    def test_api_credentials_unique_constraint(self, db_session, sample_account):
        """Test that each account can only have one set of API credentials."""
        credentials1 = APICredentials(
            account_id=sample_account.account_id,
            brokerage="public",
            encrypted_api_key="key1",
            encrypted_api_secret="secret1",
            is_active=True
        )
        credentials2 = APICredentials(
            account_id=sample_account.account_id,
            brokerage="public",
            encrypted_api_key="key2",
            encrypted_api_secret="secret2",
            is_active=True
        )
        
        db_session.add(credentials1)
        db_session.commit()
        
        db_session.add(credentials2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTradeSignal:
    """Test TradeSignal model."""
    
    def test_create_trade_signal(self, db_session, sample_account):
        """Test creating a trade signal."""
        signal = TradeSignal(
            account_id=sample_account.account_id,
            strategy_name="Iron Condor",
            symbol="SPY",
            signal_type="BUY",
            confidence=0.85,
            is_executed=False
        )
        
        db_session.add(signal)
        db_session.commit()
        
        saved_signal = db_session.query(TradeSignal).filter_by(
            signal_id=signal.signal_id
        ).first()
        
        assert saved_signal is not None
        assert saved_signal.account_id == sample_account.account_id
        assert saved_signal.strategy_name == "Iron Condor"
        assert saved_signal.symbol == "SPY"
        assert saved_signal.signal_type == "BUY"
        assert saved_signal.confidence == 0.85
        assert saved_signal.is_executed is False


class TestOrderStatus:
    """Test OrderStatus model."""
    
    def test_create_order_status(self, db_session, sample_account):
        """Test creating an order status."""
        order_status = OrderStatus(
            account_id=sample_account.account_id,
            order_id="order-456",
            status="FILLED",
            status_message="Order executed successfully",
            filled_quantity=100,
            remaining_quantity=0,
            average_price=Decimal("400.25"),
            external_status='{"broker_status": "filled", "fill_price": 400.25}'
        )
        
        db_session.add(order_status)
        db_session.commit()
        
        saved_status = db_session.query(OrderStatus).filter_by(
            order_status_id=order_status.order_status_id
        ).first()
        
        assert saved_status is not None
        assert saved_status.account_id == sample_account.account_id
        assert saved_status.order_id == "order-456"
        assert saved_status.status == "FILLED"
        assert saved_status.filled_quantity == 100
        assert saved_status.remaining_quantity == 0
        assert saved_status.average_price == Decimal("400.25")


class TestModelRelationships:
    """Test relationships between models."""
    
    def test_account_positions_relationship(self, db_session, sample_account):
        """Test account to positions relationship."""
        position = LivePosition(
            account_id=sample_account.account_id,
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=10,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            status=PositionStatus.OPEN
        )
        
        db_session.add(sample_account)
        db_session.add(position)
        db_session.commit()
        
        # Test relationship
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert len(account.positions) == 1
        assert account.positions[0].symbol == "SPY"
    
    def test_account_trades_relationship(self, db_session, sample_account):
        """Test account to trades relationship."""
        trade = LiveTrade(
            account_id=sample_account.account_id,
            public_order_id="order-789",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=100,
            price=Decimal("400.50"),
            total_amount=Decimal("40050.00"),
            filled_quantity=100,
            remaining_quantity=0,
            status=TradeStatus.FILLED
        )
        
        db_session.add(sample_account)
        db_session.add(trade)
        db_session.commit()
        
        # Test relationship
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert len(account.trades) == 1
        assert account.trades[0].symbol == "SPY"
    
    def test_account_risk_profile_relationship(self, db_session, sample_account, sample_risk_profile):
        """Test account to risk profile relationship."""
        db_session.add(sample_account)
        db_session.add(sample_risk_profile)
        db_session.commit()
        
        # Test relationship
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert account.risk_profile is not None
        assert account.risk_profile.max_position_size == 10000.0
        assert account.risk_profile.risk_level == RiskLevel.MODERATE
    
    def test_account_api_credentials_relationship(self, db_session, sample_account):
        """Test account to API credentials relationship."""
        credentials = APICredentials(
            account_id=sample_account.account_id,
            brokerage="public",
            encrypted_api_key="test_key",
            encrypted_api_secret="test_secret",
            is_active=True
        )
        
        db_session.add(sample_account)
        db_session.add(credentials)
        db_session.commit()
        
        # Test relationship
        account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert account.api_credentials is not None
        assert account.api_credentials.brokerage == "public"
        assert account.api_credentials.is_active is True


class TestModelValidation:
    """Test model validation and constraints."""
    
    def test_decimal_precision(self, db_session, sample_account):
        """Test that Decimal fields maintain precision."""
        trade = LiveTrade(
            account_id=sample_account.account_id,
            public_order_id="order-precision-test",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=1,
            price=Decimal("400.123456789"),  # High precision
            total_amount=Decimal("400.123456789"),
            filled_quantity=1,
            remaining_quantity=0,
            status=TradeStatus.FILLED
        )
        
        db_session.add(trade)
        db_session.commit()
        
        saved_trade = db_session.query(LiveTrade).filter_by(
            public_order_id="order-precision-test"
        ).first()
        
        assert saved_trade.price == Decimal("400.123456789")
        assert saved_trade.total_amount == Decimal("400.123456789")
    
    def test_enum_values(self, db_session, sample_account):
        """Test that enum fields accept valid values."""
        position = LivePosition(
            account_id=sample_account.account_id,
            symbol="SPY",
            strategy=StrategyType.CALENDAR_SPREAD,
            quantity=10,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            status=PositionStatus.OPEN
        )
        
        db_session.add(position)
        db_session.commit()
        
        saved_position = db_session.query(LivePosition).filter_by(
            account_id=sample_account.account_id,
            symbol="SPY"
        ).first()
        
        assert saved_position.strategy == StrategyType.CALENDAR_SPREAD
        assert saved_position.status == PositionStatus.OPEN
    
    def test_timestamps_auto_update(self, db_session, sample_account):
        """Test that updated_at timestamp is automatically updated."""
        db_session.add(sample_account)
        db_session.commit()
        
        original_updated_at = sample_account.updated_at
        
        # Wait a moment and update the account
        import time
        time.sleep(0.01)
        
        sample_account.account_name = "Updated Account Name"
        db_session.commit()
        
        updated_account = db_session.query(LiveTradingAccount).filter_by(
            account_id=sample_account.account_id
        ).first()
        
        assert updated_account.updated_at > original_updated_at
        assert updated_account.account_name == "Updated Account Name"
