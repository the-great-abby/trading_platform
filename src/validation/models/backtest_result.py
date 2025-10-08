"""
BacktestResult model for the validation framework

Contains the output data from a backtest execution including performance metrics and trade data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ExecutionStatus(str, Enum):
    """Enumeration of execution statuses"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class ValidationError(BaseModel):
    """Represents a validation error"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="ERROR", description="Error severity level")


class PerformanceMetrics(BaseModel):
    """Performance metrics from backtest execution"""
    total_return_pct: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown_pct: float = Field(..., description="Maximum drawdown percentage")
    win_rate: float = Field(..., description="Win rate (0.0 to 1.0)")
    total_trades: int = Field(..., description="Total number of trades")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    
    @validator('win_rate')
    def validate_win_rate(cls, v):
        """Validate win rate is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('win_rate must be between 0.0 and 1.0')
        return v
    
    @validator('total_trades')
    def validate_total_trades(cls, v):
        """Validate total trades is non-negative"""
        if v < 0:
            raise ValueError('total_trades must be non-negative')
        return v


class ResourceUsage(BaseModel):
    """Resource usage during execution"""
    peak_memory_mb: float = Field(..., description="Peak memory usage in MB")
    average_cpu_percent: float = Field(..., description="Average CPU usage percentage")
    
    @validator('peak_memory_mb')
    def validate_peak_memory(cls, v):
        """Validate memory usage is positive"""
        if v < 0:
            raise ValueError('peak_memory_mb must be non-negative')
        return v
    
    @validator('average_cpu_percent')
    def validate_cpu_percent(cls, v):
        """Validate CPU percentage is between 0 and 100"""
        if not 0.0 <= v <= 100.0:
            raise ValueError('average_cpu_percent must be between 0.0 and 100.0')
        return v


class BacktestResult(BaseModel):
    """
    Contains the output data from a backtest execution including performance metrics and trade data.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    script_id: str = Field(..., description="ID of the executed script")
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique execution identifier")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: datetime = Field(..., description="Execution end time")
    duration_seconds: float = Field(..., description="Execution duration in seconds")
    status: ExecutionStatus = Field(..., description="Execution status")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    trade_data: List[Dict[str, Any]] = Field(default_factory=list, description="Trade data")
    validation_errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    resource_usage: Optional[ResourceUsage] = Field(None, description="Resource usage")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    @validator('duration_seconds')
    def validate_duration(cls, v):
        """Validate duration is positive"""
        if v < 0:
            raise ValueError('duration_seconds must be non-negative')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_validation_error(self, field: str, message: str, severity: str = "ERROR") -> None:
        """Add a validation error"""
        error = ValidationError(field=field, message=message, severity=severity)
        self.validation_errors.append(error)
    
    def has_validation_errors(self) -> bool:
        """Check if there are validation errors"""
        return len(self.validation_errors) > 0
    
    def get_validation_errors_by_severity(self, severity: str) -> List[ValidationError]:
        """Get validation errors by severity"""
        return [error for error in self.validation_errors if error.severity == severity]
    
    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.status == ExecutionStatus.SUCCESS and not self.has_validation_errors()
    
    def get_return_percentage(self) -> Optional[float]:
        """Get return percentage if available"""
        if self.performance_metrics:
            return self.performance_metrics.total_return_pct
        return None
    
    def get_sharpe_ratio(self) -> Optional[float]:
        """Get Sharpe ratio if available"""
        if self.performance_metrics:
            return self.performance_metrics.sharpe_ratio
        return None
    
    def get_win_rate(self) -> Optional[float]:
        """Get win rate if available"""
        if self.performance_metrics:
            return self.performance_metrics.win_rate
        return None
    
    def get_total_trades(self) -> Optional[int]:
        """Get total trades if available"""
        if self.performance_metrics:
            return self.performance_metrics.total_trades
        return None
    
    def calculate_consistency_score(self, other: 'BacktestResult') -> float:
        """Calculate consistency score with another result"""
        if not self.performance_metrics or not other.performance_metrics:
            return 0.0
        
        score = 0.0
        total_metrics = 0
        
        # Compare return percentage (within 0.1%)
        if abs(self.performance_metrics.total_return_pct - other.performance_metrics.total_return_pct) <= 0.1:
            score += 1.0
        total_metrics += 1
        
        # Compare Sharpe ratio (within 0.01)
        if abs(self.performance_metrics.sharpe_ratio - other.performance_metrics.sharpe_ratio) <= 0.01:
            score += 1.0
        total_metrics += 1
        
        # Compare trade count (exact match)
        if self.performance_metrics.total_trades == other.performance_metrics.total_trades:
            score += 1.0
        total_metrics += 1
        
        # Compare win rate (within 0.01)
        if abs(self.performance_metrics.win_rate - other.performance_metrics.win_rate) <= 0.01:
            score += 1.0
        total_metrics += 1
        
        return (score / total_metrics) * 100.0 if total_metrics > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "script_id": self.script_id,
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "performance_metrics": self.performance_metrics.dict() if self.performance_metrics else None,
            "trade_data": self.trade_data,
            "validation_errors": [error.dict() for error in self.validation_errors],
            "resource_usage": self.resource_usage.dict() if self.resource_usage else None,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create instance from dictionary"""
        # Handle datetime fields
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Handle nested models
        if 'performance_metrics' in data and data['performance_metrics']:
            data['performance_metrics'] = PerformanceMetrics(**data['performance_metrics'])
        
        if 'resource_usage' in data and data['resource_usage']:
            data['resource_usage'] = ResourceUsage(**data['resource_usage'])
        
        if 'validation_errors' in data:
            data['validation_errors'] = [ValidationError(**error) for error in data['validation_errors']]
        
        return cls(**data)













