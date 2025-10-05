"""
Trade Recovery Models

Pydantic models for trade recovery operations.
Consolidated into Live Trading Service for resource efficiency.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

Base = declarative_base()


# Enums
class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionType(str, Enum):
    STOCK = "STOCK"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    CRYPTO = "CRYPTO"


class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class RecoveryType(str, Enum):
    DATABASE_FAILURE = "DATABASE_FAILURE"
    SYSTEM_RESTART = "SYSTEM_RESTART"
    MANUAL_RECOVERY = "MANUAL_RECOVERY"
    DISASTER_RECOVERY = "DISASTER_RECOVERY"


class AssignmentStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class AssignmentReason(str, Enum):
    HIGH_CONFIDENCE_MATCH = "HIGH_CONFIDENCE_MATCH"
    MARKET_CONDITIONS = "MARKET_CONDITIONS"
    USER_PREFERENCE = "USER_PREFERENCE"
    FALLBACK_ASSIGNMENT = "FALLBACK_ASSIGNMENT"
    MANUAL_ASSIGNMENT = "MANUAL_ASSIGNMENT"


# Database Models
class ActiveTradeModel(Base):
    """Database model for active trades"""
    __tablename__ = "active_trades"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    account_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    entry_time = Column(DateTime, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    trade_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecoverySessionModel(Base):
    """Database model for recovery sessions"""
    __tablename__ = "recovery_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    account_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="IN_PROGRESS")
    recovery_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    total_trades_detected = Column(Integer, nullable=False, default=0)
    trades_processed = Column(Integer, nullable=False, default=0)
    trades_assigned = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyAssignmentModel(Base):
    """Database model for strategy assignments"""
    __tablename__ = "strategy_assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("recovery_sessions.id"), nullable=False, index=True)
    trade_id = Column(String, ForeignKey("active_trades.id"), nullable=False, index=True)
    strategy_id = Column(String, nullable=False)
    strategy_name = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    assignment_reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ASSIGNED")
    auto_assigned = Column(Boolean, nullable=False, default=False)
    user_confirmed = Column(Boolean, nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecoveryLogModel(Base):
    """Database model for recovery logs"""
    __tablename__ = "recovery_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("recovery_sessions.id"), nullable=False, index=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Pydantic Models
class OptionDetails(BaseModel):
    """Option details for trades"""
    strike: Optional[Decimal] = None
    expiration: Optional[datetime] = None
    option_type: Optional[str] = None


class ActiveTrade(BaseModel):
    """Active trade model"""
    id: str
    account_id: str
    symbol: str
    side: TradeSide
    quantity: Decimal
    entry_price: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    entry_time: datetime
    detected_at: datetime
    position_type: PositionType = PositionType.STOCK
    option_details: Optional[OptionDetails] = None
    trade_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @validator('entry_price')
    def validate_entry_price(cls, v):
        if v <= 0:
            raise ValueError('Entry price must be positive')
        return v

    @validator('current_price')
    def validate_current_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Current price must be positive')
        return v


class ActiveTradeResponse(BaseModel):
    """Active trade response model"""
    id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    entry_time: datetime
    detected_at: datetime
    position_type: str
    trade_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_orm(cls, trade: ActiveTrade):
        return cls(
            id=trade.id,
            account_id=trade.account_id,
            symbol=trade.symbol,
            side=trade.side.value,
            quantity=float(trade.quantity),
            entry_price=float(trade.entry_price),
            current_price=float(trade.current_price) if trade.current_price else None,
            unrealized_pnl=float(trade.unrealized_pnl) if trade.unrealized_pnl else None,
            entry_time=trade.entry_time,
            detected_at=trade.detected_at,
            position_type=trade.position_type.value,
            trade_metadata=trade.trade_metadata
        )


class RecoverySessionCreate(BaseModel):
    """Create recovery session request"""
    account_id: str
    user_id: Optional[str] = None
    recovery_type: RecoveryType
    description: Optional[str] = None


class RecoverySession(BaseModel):
    """Recovery session model"""
    id: str
    account_id: str
    user_id: Optional[str] = None
    status: SessionStatus
    recovery_type: RecoveryType
    description: Optional[str] = None
    total_trades_detected: int = 0
    trades_processed: int = 0
    trades_assigned: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    error_message: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    def calculate_completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_trades_detected == 0:
            return 0.0
        return (self.trades_processed / self.total_trades_detected) * 100


class RecoverySessionResponse(BaseModel):
    """Recovery session response model"""
    id: str
    account_id: str
    user_id: Optional[str] = None
    status: str
    recovery_type: str
    description: Optional[str] = None
    total_trades_detected: int
    trades_processed: int
    trades_assigned: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    error_message: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, session: RecoverySession):
        return cls(
            id=session.id,
            account_id=session.account_id,
            user_id=session.user_id,
            status=session.status.value,
            recovery_type=session.recovery_type.value,
            description=session.description,
            total_trades_detected=session.total_trades_detected,
            trades_processed=session.trades_processed,
            trades_assigned=session.trades_assigned,
            started_at=session.started_at,
            completed_at=session.completed_at,
            cancelled_at=session.cancelled_at,
            cancellation_reason=session.cancellation_reason,
            error_message=session.error_message,
            summary=session.summary,
            created_at=session.created_at,
            updated_at=session.updated_at
        )


class RecoveryProgress(BaseModel):
    """Recovery progress model"""
    total_trades_detected: int
    trades_processed: int
    trades_assigned: int
    completion_percentage: float


class RecoverySessionStatus(BaseModel):
    """Recovery session status model"""
    session_id: str
    status: SessionStatus
    progress: RecoveryProgress
    last_updated: datetime


class StrategyAssignment(BaseModel):
    """Strategy assignment model"""
    id: str
    session_id: str
    trade_id: str
    strategy_id: str
    strategy_name: str
    confidence_score: float
    assignment_reason: AssignmentReason
    status: AssignmentStatus
    auto_assigned: bool
    user_confirmed: Optional[bool] = None
    assigned_at: datetime
    confirmed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v


class StrategyAssignmentRequest(BaseModel):
    """Strategy assignment request"""
    session_id: str
    trade_id: str
    strategy_id: str
    strategy_name: str
    confidence_score: float
    assignment_reason: AssignmentReason
    auto_assigned: bool = False
    notes: Optional[str] = None


class StrategyAssignmentResponse(BaseModel):
    """Strategy assignment response"""
    id: str
    session_id: str
    trade_id: str
    strategy_id: str
    strategy_name: str
    confidence_score: float
    assignment_reason: str
    status: str
    auto_assigned: bool
    user_confirmed: Optional[bool] = None
    assigned_at: datetime
    confirmed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_orm(cls, assignment: StrategyAssignment):
        return cls(
            id=assignment.id,
            session_id=assignment.session_id,
            trade_id=assignment.trade_id,
            strategy_id=assignment.strategy_id,
            strategy_name=assignment.strategy_name,
            confidence_score=assignment.confidence_score,
            assignment_reason=assignment.assignment_reason.value,
            status=assignment.status.value,
            auto_assigned=assignment.auto_assigned,
            user_confirmed=assignment.user_confirmed,
            assigned_at=assignment.assigned_at,
            confirmed_at=assignment.confirmed_at,
            rejected_at=assignment.rejected_at,
            rejection_reason=assignment.rejection_reason,
            notes=assignment.notes
        )


class StrategyMatch(BaseModel):
    """Strategy match model"""
    strategy_id: str
    strategy_name: str
    confidence_score: float
    match_reason: str
    market_conditions: Optional[str] = None


class StrategyMatchResponse(BaseModel):
    """Strategy match response"""
    strategy_id: str
    strategy_name: str
    confidence_score: float
    match_reason: str
    market_conditions: Optional[str] = None

    @classmethod
    def from_orm(cls, match: StrategyMatch):
        return cls(
            strategy_id=match.strategy_id,
            strategy_name=match.strategy_name,
            confidence_score=match.confidence_score,
            match_reason=match.match_reason,
            market_conditions=match.market_conditions
        )
