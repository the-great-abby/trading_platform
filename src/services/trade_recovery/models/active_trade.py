"""
ActiveTrade model for trade recovery system
Represents an open position detected on a trading account during recovery
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TradeSide(str, Enum):
    """Trade side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class PositionType(str, Enum):
    """Position type enumeration"""
    STOCK = "STOCK"
    OPTION = "OPTION"
    FUTURE = "FUTURE"


class TradeStatus(str, Enum):
    """Trade status enumeration"""
    DETECTED = "DETECTED"
    ASSIGNED = "ASSIGNED"
    MANAGED = "MANAGED"
    CLOSED = "CLOSED"


class OptionDetails(BaseModel):
    """Option details for options positions"""
    strike: Optional[Decimal] = None
    expiration: Optional[datetime] = None
    option_type: Optional[str] = None  # CALL or PUT


class ActiveTradeModel(Base):
    """SQLAlchemy model for ActiveTrade"""
    __tablename__ = "active_trades"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(String(255), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    side = Column(SQLEnum(TradeSide), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8), nullable=False)
    current_value = Column(Numeric(20, 8), nullable=True)
    unrealized_pnl = Column(Numeric(20, 8), nullable=True)
    entry_date = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, nullable=False, index=True)
    position_type = Column(SQLEnum(PositionType), nullable=False)
    option_details = Column(JSON, nullable=True)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.DETECTED)
    
    # Indexes
    __table_args__ = (
        Index('idx_account_detected', 'account_id', 'detected_at'),
        Index('idx_symbol_detected', 'symbol', 'detected_at'),
    )


class ActiveTrade(BaseModel):
    """Pydantic model for ActiveTrade"""
    id: UUID = Field(default_factory=uuid4)
    account_id: str = Field(..., min_length=1, max_length=255)
    symbol: str = Field(..., min_length=1, max_length=50)
    quantity: Decimal = Field(..., gt=0)
    side: TradeSide
    entry_price: Decimal = Field(..., gt=0)
    current_price: Decimal = Field(..., gt=0)
    current_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    entry_date: Optional[datetime] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    position_type: PositionType
    option_details: Optional[OptionDetails] = None
    status: TradeStatus = Field(default=TradeStatus.DETECTED)
    
    @validator('entry_date', 'detected_at')
    def validate_dates(cls, v, values):
        """Validate that entry_date is before detected_at"""
        if v is None:
            return v
        
        if 'entry_date' in values and 'detected_at' in values:
            if values['entry_date'] and values['detected_at']:
                if values['entry_date'] >= values['detected_at']:
                    raise ValueError('entry_date must be before detected_at')
        
        return v
    
    @validator('current_value', always=True)
    def calculate_current_value(cls, v, values):
        """Calculate current value if not provided"""
        if v is None and 'quantity' in values and 'current_price' in values:
            return values['quantity'] * values['current_price']
        return v
    
    @validator('unrealized_pnl', always=True)
    def calculate_unrealized_pnl(cls, v, values):
        """Calculate unrealized P&L if not provided"""
        if v is None and all(key in values for key in ['quantity', 'entry_price', 'current_price', 'side']):
            quantity = values['quantity']
            entry_price = values['entry_price']
            current_price = values['current_price']
            side = values['side']
            
            if side == TradeSide.BUY:
                return quantity * (current_price - entry_price)
            else:  # SELL
                return quantity * (entry_price - current_price)
        return v
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate symbol format"""
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()
    
    @validator('option_details')
    def validate_option_details(cls, v, values):
        """Validate option details for options positions"""
        if v is not None and 'position_type' in values:
            if values['position_type'] == PositionType.OPTION:
                if not v.strike or not v.expiration or not v.option_type:
                    raise ValueError('Option details must include strike, expiration, and option_type for OPTION positions')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "test_account_123",
                "symbol": "AAPL",
                "quantity": 100.0,
                "side": "BUY",
                "entry_price": 150.00,
                "current_price": 155.00,
                "current_value": 15500.00,
                "unrealized_pnl": 500.00,
                "entry_date": "2025-01-20T09:30:00Z",
                "detected_at": "2025-01-27T10:00:00Z",
                "position_type": "STOCK",
                "option_details": None,
                "status": "DETECTED"
            }
        }


class ActiveTradeCreate(BaseModel):
    """Model for creating new ActiveTrade"""
    account_id: str = Field(..., min_length=1, max_length=255)
    symbol: str = Field(..., min_length=1, max_length=50)
    quantity: Decimal = Field(..., gt=0)
    side: TradeSide
    entry_price: Decimal = Field(..., gt=0)
    current_price: Decimal = Field(..., gt=0)
    entry_date: Optional[datetime] = None
    position_type: PositionType
    option_details: Optional[OptionDetails] = None


class ActiveTradeUpdate(BaseModel):
    """Model for updating ActiveTrade"""
    current_price: Optional[Decimal] = Field(None, gt=0)
    status: Optional[TradeStatus] = None
    option_details: Optional[OptionDetails] = None


class ActiveTradeResponse(BaseModel):
    """Model for ActiveTrade API responses"""
    id: UUID
    account_id: str
    symbol: str
    quantity: Decimal
    side: TradeSide
    entry_price: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    entry_date: Optional[datetime]
    detected_at: datetime
    position_type: PositionType
    option_details: Optional[OptionDetails]
    status: TradeStatus
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }








