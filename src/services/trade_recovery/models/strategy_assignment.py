"""
StrategyAssignment model for trade recovery system
Represents the mapping of a recovered trade to a specific trading strategy for ongoing management
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


class AssignmentStatus(str, Enum):
    """Assignment status enumeration"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class StrategyAssignmentModel(Base):
    """SQLAlchemy model for StrategyAssignment"""
    __tablename__ = "strategy_assignments"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    recovery_session_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    active_trade_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    strategy_name = Column(String(255), nullable=False)
    assigned_at = Column(DateTime, nullable=False, index=True)
    assigned_by = Column(String(255), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    assignment_reason = Column(String(1000), nullable=True)
    status = Column(SQLEnum(AssignmentStatus), nullable=False, default=AssignmentStatus.PENDING)
    strategy_parameters = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_recovery_session', 'recovery_session_id'),
        Index('idx_active_trade', 'active_trade_id'),
        Index('idx_strategy_name', 'strategy_name'),
        Index('idx_assigned_at', 'assigned_at'),
    )


class StrategyAssignment(BaseModel):
    """Pydantic model for StrategyAssignment"""
    id: UUID = Field(default_factory=uuid4)
    recovery_session_id: UUID
    active_trade_id: UUID
    strategy_name: str = Field(..., min_length=1, max_length=255)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: str = Field(..., min_length=1, max_length=255)
    confidence_score: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    assignment_reason: Optional[str] = Field(None, max_length=1000)
    status: AssignmentStatus = Field(default=AssignmentStatus.PENDING)
    strategy_parameters: Optional[Dict[str, Any]] = None
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Validate confidence score is between 0.0 and 1.0"""
        if v is not None:
            if not (0.0 <= float(v) <= 1.0):
                raise ValueError('confidence_score must be between 0.0 and 1.0')
        return v
    
    @validator('strategy_name')
    def validate_strategy_name(cls, v):
        """Validate strategy name format"""
        if not v or not v.strip():
            raise ValueError('Strategy name cannot be empty')
        return v.strip()
    
    @validator('assigned_by')
    def validate_assigned_by(cls, v):
        """Validate assigned_by format"""
        if not v or not v.strip():
            raise ValueError('assigned_by cannot be empty')
        return v.strip()
    
    @validator('strategy_parameters')
    def validate_strategy_parameters(cls, v):
        """Validate strategy parameters are valid JSON"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('strategy_parameters must be a valid JSON object')
        return v
    
    def is_pending(self) -> bool:
        """Check if assignment is pending"""
        return self.status == AssignmentStatus.PENDING
    
    def is_active(self) -> bool:
        """Check if assignment is active"""
        return self.status == AssignmentStatus.ACTIVE
    
    def is_paused(self) -> bool:
        """Check if assignment is paused"""
        return self.status == AssignmentStatus.PAUSED
    
    def is_cancelled(self) -> bool:
        """Check if assignment is cancelled"""
        return self.status == AssignmentStatus.CANCELLED
    
    def can_be_activated(self) -> bool:
        """Check if assignment can be activated"""
        return self.status in [AssignmentStatus.PENDING, AssignmentStatus.PAUSED]
    
    def can_be_paused(self) -> bool:
        """Check if assignment can be paused"""
        return self.status == AssignmentStatus.ACTIVE
    
    def can_be_cancelled(self) -> bool:
        """Check if assignment can be cancelled"""
        return self.status in [AssignmentStatus.PENDING, AssignmentStatus.ACTIVE, AssignmentStatus.PAUSED]
    
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
                "recovery_session_id": "456e7890-e89b-12d3-a456-426614174001",
                "active_trade_id": "789e0123-e89b-12d3-a456-426614174002",
                "strategy_name": "BollingerBands",
                "assigned_at": "2025-01-27T10:00:00Z",
                "assigned_by": "user_123",
                "confidence_score": 0.85,
                "assignment_reason": "High volatility, mean reversion opportunity",
                "status": "PENDING",
                "strategy_parameters": {
                    "period": 20,
                    "std_dev": 2.0
                }
            }
        }


class StrategyAssignmentCreate(BaseModel):
    """Model for creating new StrategyAssignment"""
    recovery_session_id: UUID
    active_trade_id: UUID
    strategy_name: str = Field(..., min_length=1, max_length=255)
    assigned_by: str = Field(..., min_length=1, max_length=255)
    confidence_score: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    assignment_reason: Optional[str] = Field(None, max_length=1000)
    strategy_parameters: Optional[Dict[str, Any]] = None


class StrategyAssignmentUpdate(BaseModel):
    """Model for updating StrategyAssignment"""
    status: Optional[AssignmentStatus] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    assignment_reason: Optional[str] = Field(None, max_length=1000)
    strategy_parameters: Optional[Dict[str, Any]] = None


class StrategyAssignmentResponse(BaseModel):
    """Model for StrategyAssignment API responses"""
    id: UUID
    recovery_session_id: UUID
    active_trade_id: UUID
    strategy_name: str
    assigned_at: datetime
    assigned_by: str
    confidence_score: Optional[Decimal]
    assignment_reason: Optional[str]
    status: AssignmentStatus
    strategy_parameters: Optional[Dict[str, Any]]
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class StrategyAssignmentSummary(BaseModel):
    """Model for strategy assignment summary"""
    total_assignments: int = Field(..., ge=0)
    pending_assignments: int = Field(..., ge=0)
    active_assignments: int = Field(..., ge=0)
    paused_assignments: int = Field(..., ge=0)
    cancelled_assignments: int = Field(..., ge=0)
    average_confidence: Optional[Decimal] = None
    
    @validator('average_confidence', always=True)
    def calculate_average_confidence(cls, v, values):
        """Calculate average confidence score"""
        # This would be calculated from actual assignments
        # For now, return None as placeholder
        return v
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "total_assignments": 10,
                "pending_assignments": 3,
                "active_assignments": 5,
                "paused_assignments": 1,
                "cancelled_assignments": 1,
                "average_confidence": 0.78
            }
        }




















