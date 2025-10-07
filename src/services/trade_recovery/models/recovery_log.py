"""
RecoveryLog model for trade recovery system
Represents the audit trail of all recovery actions taken by the system
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LogAction(str, Enum):
    """Log action enumeration"""
    TRADE_DETECTED = "TRADE_DETECTED"
    STRATEGY_ASSIGNED = "STRATEGY_ASSIGNED"
    TRADE_MANAGED = "TRADE_MANAGED"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    SESSION_FAILED = "SESSION_FAILED"
    SESSION_CANCELLED = "SESSION_CANCELLED"


class LogSeverity(str, Enum):
    """Log severity enumeration"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RecoveryLogModel(Base):
    """SQLAlchemy model for RecoveryLog"""
    __tablename__ = "recovery_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    recovery_session_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    action = Column(SQLEnum(LogAction), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    details = Column(JSON, nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    trade_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    strategy_name = Column(String(255), nullable=True, index=True)
    severity = Column(SQLEnum(LogSeverity), nullable=False, default=LogSeverity.INFO)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_timestamp', 'recovery_session_id', 'timestamp'),
        Index('idx_action_timestamp', 'action', 'timestamp'),
        Index('idx_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


class RecoveryLog(BaseModel):
    """Pydantic model for RecoveryLog"""
    id: UUID = Field(default_factory=uuid4)
    recovery_session_id: UUID
    action: LogAction
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = Field(None, max_length=255)
    trade_id: Optional[UUID] = None
    strategy_name: Optional[str] = Field(None, max_length=255)
    severity: LogSeverity = Field(default=LogSeverity.INFO)
    
    @validator('details')
    def validate_details(cls, v):
        """Validate details are valid JSON"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('details must be a valid JSON object')
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format"""
        if v is not None and not v.strip():
            raise ValueError('user_id cannot be empty if provided')
        return v.strip() if v else None
    
    @validator('strategy_name')
    def validate_strategy_name(cls, v):
        """Validate strategy name format"""
        if v is not None and not v.strip():
            raise ValueError('strategy_name cannot be empty if provided')
        return v.strip() if v else None
    
    @validator('severity')
    def validate_severity_for_action(cls, v, values):
        """Validate severity is appropriate for action"""
        if 'action' in values:
            action = values['action']
            if action == LogAction.ERROR_OCCURRED and v not in [LogSeverity.ERROR, LogSeverity.CRITICAL]:
                raise ValueError('ERROR_OCCURRED action must have ERROR or CRITICAL severity')
            elif action in [LogAction.SESSION_FAILED, LogAction.SESSION_CANCELLED] and v == LogSeverity.INFO:
                raise ValueError('Session failure/cancellation should not have INFO severity')
        return v
    
    def is_error(self) -> bool:
        """Check if log entry is an error"""
        return self.severity in [LogSeverity.ERROR, LogSeverity.CRITICAL]
    
    def is_warning(self) -> bool:
        """Check if log entry is a warning"""
        return self.severity == LogSeverity.WARNING
    
    def is_info(self) -> bool:
        """Check if log entry is informational"""
        return self.severity == LogSeverity.INFO
    
    def is_critical(self) -> bool:
        """Check if log entry is critical"""
        return self.severity == LogSeverity.CRITICAL
    
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
                "recovery_session_id": "456e7890-e89b-12d3-a456-426614174001",
                "action": "TRADE_DETECTED",
                "timestamp": "2025-01-27T10:00:00Z",
                "details": {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 150.00
                },
                "user_id": "user_123",
                "trade_id": "789e0123-e89b-12d3-a456-426614174002",
                "strategy_name": None,
                "severity": "INFO"
            }
        }


class RecoveryLogCreate(BaseModel):
    """Model for creating new RecoveryLog"""
    recovery_session_id: UUID
    action: LogAction
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = Field(None, max_length=255)
    trade_id: Optional[UUID] = None
    strategy_name: Optional[str] = Field(None, max_length=255)
    severity: LogSeverity = Field(default=LogSeverity.INFO)


class RecoveryLogResponse(BaseModel):
    """Model for RecoveryLog API responses"""
    id: UUID
    recovery_session_id: UUID
    action: LogAction
    timestamp: datetime
    details: Optional[Dict[str, Any]]
    user_id: Optional[str]
    trade_id: Optional[UUID]
    strategy_name: Optional[str]
    severity: LogSeverity
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class RecoveryLogSummary(BaseModel):
    """Model for recovery log summary"""
    total_logs: int = Field(..., ge=0)
    info_logs: int = Field(..., ge=0)
    warning_logs: int = Field(..., ge=0)
    error_logs: int = Field(..., ge=0)
    critical_logs: int = Field(..., ge=0)
    last_log_timestamp: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "total_logs": 25,
                "info_logs": 20,
                "warning_logs": 3,
                "error_logs": 2,
                "critical_logs": 0,
                "last_log_timestamp": "2025-01-27T10:30:00Z"
            }
        }


class RecoveryLogFilter(BaseModel):
    """Model for filtering recovery logs"""
    recovery_session_id: Optional[UUID] = None
    action: Optional[LogAction] = None
    severity: Optional[LogSeverity] = None
    user_id: Optional[str] = None
    trade_id: Optional[UUID] = None
    strategy_name: Optional[str] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    
    @validator('end_timestamp')
    def validate_end_timestamp(cls, v, values):
        """Validate end timestamp is after start timestamp"""
        if v is not None and 'start_timestamp' in values and values['start_timestamp'] is not None:
            if v <= values['start_timestamp']:
                raise ValueError('end_timestamp must be after start_timestamp')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


















