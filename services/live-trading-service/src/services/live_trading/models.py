"""
Live Trading Entity Models

SQLAlchemy models for the live trading system.
Defines all database entities for live trading operations.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from enum import Enum

Base = declarative_base()


class AccountType(str, Enum):
    """Account type enumeration."""
    CASH = "CASH"
    MARGIN = "MARGIN"


class TradeStatus(str, Enum):
    """Trade status enumeration."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionStatus(str, Enum):
    """Position status enumeration."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class StrategyType(str, Enum):
    """Strategy type enumeration."""
    # Original strategies
    IRON_CONDOR = "IRON_CONDOR"
    BUTTERFLY_SPREAD = "BUTTERFLY_SPREAD"
    CALENDAR_SPREAD = "CALENDAR_SPREAD"
    
    # Volatility strategies
    VOLATILITY_TRADING = "VOLATILITY_TRADING"
    VOLATILITY_BREAKOUT = "VOLATILITY_BREAKOUT"
    
    # Market regime strategies
    MARKET_REGIME_ADAPTIVE = "MARKET_REGIME_ADAPTIVE"
    REGIME_SWITCHING = "REGIME_SWITCHING"
    
    # Elliott Wave strategies
    ELLIOTT_WAVE_CORRECTIVE = "ELLIOTT_WAVE_CORRECTIVE"
    ELLIOTT_WAVE_IMPULSE = "ELLIOTT_WAVE_IMPULSE"
    
    # Sector strategies
    SECTOR_ROTATION = "SECTOR_ROTATION"
    
    # Advanced strategies
    NEWS_ENHANCED = "NEWS_ENHANCED"
    RSI_AI_ENHANCED = "RSI_AI_ENHANCED"
    QUANTUM_MOMENTUM = "QUANTUM_MOMENTUM"
    
    # Options strategies
    COVERED_CALL = "COVERED_CALL"
    CASH_SECURED_PUT = "CASH_SECURED_PUT"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    DIAGONAL_SPREAD = "DIAGONAL_SPREAD"
    EARNINGS_STRATEGY = "EARNINGS_STRATEGY"
    GREEKS_ENHANCED = "GREEKS_ENHANCED"
    
    # Advanced options
    ENHANCED_IRON_CONDOR = "ENHANCED_IRON_CONDOR"
    OPTIONS_WHEEL = "OPTIONS_WHEEL"
    
    # Multi-Strategy Ensemble
    MULTI_STRATEGY_ENSEMBLE = "MULTI_STRATEGY_ENSEMBLE"


class OptionType(str, Enum):
    """Option type enumeration."""
    CALL = "CALL"
    PUT = "PUT"


class TradeAction(str, Enum):
    """Trade action enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# T014: LiveTradingAccount model (lines 1-50)
class LiveTradingAccount(Base):
    """Represents a Public.com brokerage account with real money."""
    
    __tablename__ = "live_trading_accounts"
    
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_account_id = Column(String(100), unique=True, nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    buying_power = Column(Numeric(15, 2), nullable=False, default=0.00)
    cash_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    equity = Column(Numeric(15, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("LivePosition", back_populates="account")
    trades = relationship("LiveTrade", back_populates="account")
    risk_profile = relationship("RiskProfile", back_populates="account", uselist=False)
    
    def __repr__(self):
        return f"<LiveTradingAccount(account_id={self.account_id}, public_account_id={self.public_account_id})>"


# T015: LivePosition model (lines 51-100)
class LivePosition(Base):
    """Represents an actual position held in the brokerage account."""
    
    __tablename__ = "live_positions"
    
    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("live_trading_accounts.account_id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy = Column(SQLEnum(StrategyType), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric(10, 4), nullable=False)
    current_price = Column(Numeric(10, 4))
    unrealized_pnl = Column(Numeric(15, 2), default=0.00)
    realized_pnl = Column(Numeric(15, 2), default=0.00)
    status = Column(SQLEnum(PositionStatus), nullable=False, default=PositionStatus.OPEN)
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime)
    expiration_date = Column(DateTime)
    legs_data = Column(Text)  # JSON string of position legs
    greeks_data = Column(Text)  # JSON string of current Greeks
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("LiveTradingAccount", back_populates="positions")
    trades = relationship("LiveTrade", back_populates="position")
    
    def __repr__(self):
        return f"<LivePosition(position_id={self.position_id}, symbol={self.symbol}, quantity={self.quantity})>"


# T016: LiveTrade model (lines 101-150)
class LiveTrade(Base):
    """Represents an actual trade executed through the Public.com API."""
    
    __tablename__ = "live_trades"
    
    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("live_trading_accounts.account_id"), nullable=False)
    position_id = Column(UUID(as_uuid=True), ForeignKey("live_positions.position_id"))
    public_order_id = Column(String(100), unique=True, nullable=False)
    symbol = Column(String(50), nullable=False)
    action = Column(SQLEnum(TradeAction), nullable=False)
    option_type = Column(SQLEnum(OptionType))
    strike_price = Column(Numeric(10, 4))
    expiration_date = Column(DateTime)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 4), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    commission = Column(Numeric(10, 4), default=0.00)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    filled_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer, nullable=False)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    rejection_reason = Column(Text)
    strategy = Column(SQLEnum(StrategyType))
    leg_data = Column(Text)  # JSON string of trade leg details
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("LiveTradingAccount", back_populates="trades")
    position = relationship("LivePosition", back_populates="trades")
    
    def __repr__(self):
        return f"<LiveTrade(trade_id={self.trade_id}, symbol={self.symbol}, action={self.action}, quantity={self.quantity})>"


# T017: RiskProfile model (lines 151-200)
class RiskProfile(Base):
    """Risk management profile for live trading accounts."""
    
    __tablename__ = "risk_profiles"
    
    risk_profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("live_trading_accounts.account_id"), nullable=False, unique=True)
    max_position_size = Column(Numeric(15, 2), nullable=False)
    max_portfolio_risk = Column(Numeric(5, 4), nullable=False)  # Percentage as decimal (0.05 = 5%)
    max_daily_loss = Column(Numeric(15, 2), nullable=False)
    max_daily_trades = Column(Integer, nullable=False)
    allowed_strategies = Column(Text, nullable=False)  # JSON array of allowed strategies
    max_greeks_exposure = Column(Text, nullable=False)  # JSON object of Greeks limits
    emergency_stop_active = Column(Boolean, nullable=False, default=False)
    emergency_stop_reason = Column(Text)
    emergency_stop_activated_at = Column(DateTime)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.MEDIUM)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("LiveTradingAccount", back_populates="risk_profile")
    
    def __repr__(self):
        return f"<RiskProfile(risk_profile_id={self.risk_profile_id}, account_id={self.account_id}, risk_level={self.risk_level})>"


# T018: APICredentials model (lines 201-250)
class APICredentials(Base):
    """Encrypted API credentials for Public.com integration."""
    
    __tablename__ = "api_credentials"
    
    credential_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("live_trading_accounts.account_id"), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    access_token = Column(Text)  # Encrypted access token
    refresh_token = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<APICredentials(credential_id={self.credential_id}, account_id={self.account_id}, is_active={self.is_active})>"


# T019: TradeSignal model (lines 251-300)
class TradeSignal(Base):
    """Trading signals generated by the system."""
    
    __tablename__ = "trade_signals"
    
    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("live_trading_accounts.account_id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy = Column(SQLEnum(StrategyType), nullable=False)
    signal_type = Column(String(50), nullable=False)  # ENTRY, EXIT, ADJUSTMENT
    signal_strength = Column(Numeric(3, 2), nullable=False)  # 0.00 to 1.00
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.00 to 1.00
    market_conditions = Column(Text)  # JSON object of market conditions
    signal_data = Column(Text, nullable=False)  # JSON object of signal parameters
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, EXECUTED, CANCELLED, EXPIRED
    executed_at = Column(DateTime)
    executed_trade_id = Column(UUID(as_uuid=True), ForeignKey("live_trades.trade_id"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def __repr__(self):
        return f"<TradeSignal(signal_id={self.signal_id}, symbol={self.symbol}, strategy={self.strategy}, signal_type={self.signal_type})>"


# T020: OrderStatus model (lines 301-350)
class OrderStatus(Base):
    """Order status tracking and audit trail."""
    
    __tablename__ = "order_status_history"
    
    status_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("live_trades.trade_id"), nullable=False)
    order_id = Column(String(100), nullable=False)
    status = Column(SQLEnum(TradeStatus), nullable=False)
    status_message = Column(Text)
    filled_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric(10, 4))
    commission = Column(Numeric(10, 4), default=0.00)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    external_status = Column(Text)  # Raw status from Public.com API
    error_details = Column(Text)
    
    def __repr__(self):
        return f"<OrderStatus(status_id={self.status_id}, order_id={self.order_id}, status={self.status}, timestamp={self.timestamp})>"
