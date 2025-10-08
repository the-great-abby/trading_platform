"""
RecoverySession model for trade recovery system
Represents a system startup event where active trades are detected and recovery actions are taken
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RecoveryType(str, Enum):
    """Recovery type enumeration"""
    DATABASE_FAILURE = "DATABASE_FAILURE"
    MANUAL_RECOVERY = "MANUAL_RECOVERY"
    SCHEDULED_RECOVERY = "SCHEDULED_RECOVERY"


class SessionStatus(str, Enum):
    """Session status enumeration"""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RecoverySessionModel(Base):
    """SQLAlchemy model for RecoverySession"""
    __tablename__ = "recovery_sessions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.IN_PROGRESS)
    total_trades_detected = Column(Integer, nullable=False, default=0)
    trades_processed = Column(Integer, nullable=False, default=0)
    trades_assigned = Column(Integer, nullable=False, default=0)
    error_message = Column(String(1000), nullable=True)
    recovery_type = Column(SQLEnum(RecoveryType), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_account_started', 'account_id', 'started_at'),
        Index('idx_status_started', 'status', 'started_at'),
    )


class RecoverySession(BaseModel):
    """Pydantic model for RecoverySession"""
    id: UUID = Field(default_factory=uuid4)
    account_id: str = Field(..., min_length=1, max_length=255)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: SessionStatus = Field(default=SessionStatus.IN_PROGRESS)
    total_trades_detected: int = Field(default=0, ge=0)
    trades_processed: int = Field(default=0, ge=0)
    trades_assigned: int = Field(default=0, ge=0)
    error_message: Optional[str] = Field(None, max_length=1000)
    recovery_type: RecoveryType
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        """Validate that completed_at is after started_at"""
        if v is not None and 'started_at' in values:
            if v <= values['started_at']:
                raise ValueError('completed_at must be after started_at')
        return v
    
    @validator('trades_processed')
    def validate_trades_processed(cls, v, values):
        """Validate that trades_processed <= total_trades_detected"""
        if 'total_trades_detected' in values:
            if v > values['total_trades_detected']:
                raise ValueError('trades_processed cannot exceed total_trades_detected')
        return v
    
    @validator('trades_assigned')
    def validate_trades_assigned(cls, v, values):
        """Validate that trades_assigned <= trades_processed"""
        if 'trades_processed' in values:
            if v > values['trades_processed']:
                raise ValueError('trades_assigned cannot exceed trades_processed')
        return v
    
    @validator('account_id')
    def validate_account_id(cls, v):
        """Validate account ID format"""
        if not v or not v.strip():
            raise ValueError('Account ID cannot be empty')
        return v.strip()
    
    @validator('error_message')
    def validate_error_message(cls, v, values):
        """Validate error message is only set for failed sessions"""
        if v is not None and 'status' in values:
            if values['status'] not in [SessionStatus.FAILED, SessionStatus.CANCELLED]:
                raise ValueError('error_message can only be set for failed or cancelled sessions')
        return v
    
    def calculate_completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_trades_detected == 0:
            return 100.0
        return (self.trades_processed / self.total_trades_detected) * 100.0
    
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.status == SessionStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if session failed"""
        return self.status == SessionStatus.FAILED
    
    def is_cancelled(self) -> bool:
        """Check if session is cancelled"""
        return self.status == SessionStatus.CANCELLED
    
    def is_in_progress(self) -> bool:
        """Check if session is in progress"""
        return self.status == SessionStatus.IN_PROGRESS
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "test_account_123",
                "started_at": "2025-01-27T10:00:00Z",
                "completed_at": None,
                "status": "IN_PROGRESS",
                "total_trades_detected": 0,
                "trades_processed": 0,
                "trades_assigned": 0,
                "error_message": None,
                "recovery_type": "DATABASE_FAILURE",
                "description": "System recovery after database failure"
            }
        }


class RecoverySessionCreate(BaseModel):
    """Model for creating new RecoverySession"""
    account_id: str = Field(..., min_length=1, max_length=255)
    recovery_type: RecoveryType
    description: Optional[str] = Field(None, max_length=500)


class RecoverySessionUpdate(BaseModel):
    """Model for updating RecoverySession"""
    status: Optional[SessionStatus] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    total_trades_detected: Optional[int] = Field(None, ge=0)
    trades_processed: Optional[int] = Field(None, ge=0)
    trades_assigned: Optional[int] = Field(None, ge=0)
    completed_at: Optional[datetime] = None


class RecoverySessionResponse(BaseModel):
    """Model for RecoverySession API responses"""
    id: UUID
    account_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: SessionStatus
    total_trades_detected: int
    trades_processed: int
    trades_assigned: int
    error_message: Optional[str]
    recovery_type: RecoveryType
    description: Optional[str]
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class RecoverySessionStatus(BaseModel):
    """Model for recovery session status response"""
    session_id: UUID
    status: SessionStatus
    progress: 'RecoveryProgress'
    last_updated: datetime
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class RecoveryProgress(BaseModel):
    """Model for recovery progress details"""
    total_trades_detected: int = Field(..., ge=0)
    trades_processed: int = Field(..., ge=0)
    trades_assigned: int = Field(..., ge=0)
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    
    @validator('completion_percentage', always=True)
    def calculate_completion_percentage(cls, v, values):
        """Calculate completion percentage"""
        if 'total_trades_detected' in values and 'trades_processed' in values:
            total = values['total_trades_detected']
            processed = values['trades_processed']
            if total == 0:
                return 100.0
            return min(100.0, (processed / total) * 100.0)
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "total_trades_detected": 5,
                "trades_processed": 3,
                "trades_assigned": 2,
                "completion_percentage": 60.0
            }
        }


# Update forward references
RecoverySessionStatus.model_rebuild()
RecoveryProgress.model_rebuild()




















