"""
TestConfiguration model for the validation framework

Settings that define how backtests should be validated including tolerances and expected behaviors.
"""

from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class Tolerances(BaseModel):
    """Tolerance settings for validation"""
    returns_tolerance_pct: float = Field(default=0.1, description="Returns tolerance percentage")
    ratios_tolerance: float = Field(default=0.01, description="Ratios tolerance")
    drawdown_tolerance_pct: float = Field(default=0.05, description="Drawdown tolerance percentage")
    win_rate_tolerance_pct: float = Field(default=0.5, description="Win rate tolerance percentage")
    
    @validator('returns_tolerance_pct', 'drawdown_tolerance_pct', 'win_rate_tolerance_pct')
    def validate_percentage_tolerances(cls, v):
        """Validate percentage tolerances are non-negative"""
        if v < 0:
            raise ValueError('percentage tolerances must be non-negative')
        return v
    
    @validator('ratios_tolerance')
    def validate_ratios_tolerance(cls, v):
        """Validate ratios tolerance is non-negative"""
        if v < 0:
            raise ValueError('ratios tolerance must be non-negative')
        return v


class Timeouts(BaseModel):
    """Timeout settings for different test types"""
    quick_test_seconds: int = Field(default=30, description="Quick test timeout")
    standard_test_seconds: int = Field(default=300, description="Standard test timeout")
    comprehensive_test_seconds: int = Field(default=1800, description="Comprehensive test timeout")
    options_test_seconds: int = Field(default=600, description="Options test timeout")
    
    @validator('quick_test_seconds', 'standard_test_seconds', 'comprehensive_test_seconds', 'options_test_seconds')
    def validate_timeouts(cls, v):
        """Validate timeouts are positive"""
        if v <= 0:
            raise ValueError('timeouts must be positive')
        return v


class ValidationRules(BaseModel):
    """Validation rules and requirements"""
    require_exact_trade_counts: bool = Field(default=True, description="Require exact trade counts")
    allow_missing_metrics: List[str] = Field(default_factory=list, description="Metrics that can be missing")
    required_metrics: List[str] = Field(
        default_factory=lambda: [
            "total_return_pct", "sharpe_ratio", "max_drawdown_pct", 
            "win_rate", "total_trades", "initial_capital", "final_capital"
        ],
        description="Required metrics"
    )
    
    @validator('required_metrics')
    def validate_required_metrics(cls, v):
        """Validate required metrics list"""
        if not v:
            raise ValueError('required_metrics cannot be empty')
        return v


class ExecutionSettings(BaseModel):
    """Execution settings for validation"""
    parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    max_parallel_jobs: int = Field(default=4, description="Maximum parallel jobs")
    retry_failed_tests: bool = Field(default=True, description="Retry failed tests")
    max_retries: int = Field(default=2, description="Maximum retry attempts")
    
    @validator('max_parallel_jobs')
    def validate_max_parallel_jobs(cls, v):
        """Validate max parallel jobs is positive"""
        if v <= 0:
            raise ValueError('max_parallel_jobs must be positive')
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        """Validate max retries is non-negative"""
        if v < 0:
            raise ValueError('max_retries must be non-negative')
        return v


class TestConfiguration(BaseModel):
    """
    Settings that define how backtests should be validated including tolerances and expected behaviors.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Configuration name")
    description: str = Field(default="", description="Configuration description")
    tolerances: Tolerances = Field(default_factory=Tolerances, description="Tolerance settings")
    timeouts: Timeouts = Field(default_factory=Timeouts, description="Timeout settings")
    validation_rules: ValidationRules = Field(default_factory=ValidationRules, description="Validation rules")
    execution_settings: ExecutionSettings = Field(default_factory=ExecutionSettings, description="Execution settings")
    is_default: bool = Field(default=False, description="Whether this is the default configuration")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate configuration name"""
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_timeout_for_script_type(self, script_type: str) -> int:
        """Get timeout for specific script type"""
        timeouts_map = {
            "INDIVIDUAL_STRATEGY": self.timeouts.standard_test_seconds,
            "MULTI_STRATEGY": self.timeouts.standard_test_seconds,
            "OPTIONS": self.timeouts.options_test_seconds,
            "COMPREHENSIVE": self.timeouts.comprehensive_test_seconds
        }
        return timeouts_map.get(script_type, self.timeouts.standard_test_seconds)
    
    def is_metric_required(self, metric_name: str) -> bool:
        """Check if a metric is required"""
        return metric_name in self.validation_rules.required_metrics
    
    def is_metric_allowed_missing(self, metric_name: str) -> bool:
        """Check if a metric is allowed to be missing"""
        return metric_name in self.validation_rules.allow_missing_metrics
    
    def can_skip_metric(self, metric_name: str) -> bool:
        """Check if a metric can be skipped"""
        return not self.is_metric_required(metric_name) or self.is_metric_allowed_missing(metric_name)
    
    def update_tolerance(self, tolerance_type: str, value: float) -> None:
        """Update a tolerance value"""
        if hasattr(self.tolerances, tolerance_type):
            setattr(self.tolerances, tolerance_type, value)
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Unknown tolerance type: {tolerance_type}")
    
    def update_timeout(self, timeout_type: str, value: int) -> None:
        """Update a timeout value"""
        if hasattr(self.timeouts, timeout_type):
            setattr(self.timeouts, timeout_type, value)
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Unknown timeout type: {timeout_type}")
    
    def add_required_metric(self, metric_name: str) -> None:
        """Add a required metric"""
        if metric_name not in self.validation_rules.required_metrics:
            self.validation_rules.required_metrics.append(metric_name)
            self.updated_at = datetime.now()
    
    def remove_required_metric(self, metric_name: str) -> None:
        """Remove a required metric"""
        if metric_name in self.validation_rules.required_metrics:
            self.validation_rules.required_metrics.remove(metric_name)
            self.updated_at = datetime.now()
    
    def add_allowed_missing_metric(self, metric_name: str) -> None:
        """Add a metric that's allowed to be missing"""
        if metric_name not in self.validation_rules.allow_missing_metrics:
            self.validation_rules.allow_missing_metrics.append(metric_name)
            self.updated_at = datetime.now()
    
    def remove_allowed_missing_metric(self, metric_name: str) -> None:
        """Remove a metric that's allowed to be missing"""
        if metric_name in self.validation_rules.allow_missing_metrics:
            self.validation_rules.allow_missing_metrics.remove(metric_name)
            self.updated_at = datetime.now()
    
    def is_strict_mode(self) -> bool:
        """Check if configuration is in strict mode"""
        return (
            self.tolerances.returns_tolerance_pct <= 0.01 and
            self.tolerances.ratios_tolerance <= 0.001 and
            self.tolerances.drawdown_tolerance_pct <= 0.01 and
            self.validation_rules.require_exact_trade_counts is True
        )
    
    def is_permissive_mode(self) -> bool:
        """Check if configuration is in permissive mode"""
        return (
            self.tolerances.returns_tolerance_pct >= 1.0 and
            self.tolerances.ratios_tolerance >= 0.1 and
            self.tolerances.drawdown_tolerance_pct >= 0.5 and
            self.validation_rules.require_exact_trade_counts is False
        )
    
    def clone(self, new_name: str, new_description: str = "") -> 'TestConfiguration':
        """Create a copy of this configuration with a new name"""
        return TestConfiguration(
            name=new_name,
            description=new_description,
            tolerances=Tolerances(**self.tolerances.dict()),
            timeouts=Timeouts(**self.timeouts.dict()),
            validation_rules=ValidationRules(**self.validation_rules.dict()),
            execution_settings=ExecutionSettings(**self.execution_settings.dict()),
            is_default=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tolerances": self.tolerances.dict(),
            "timeouts": self.timeouts.dict(),
            "validation_rules": self.validation_rules.dict(),
            "execution_settings": self.execution_settings.dict(),
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfiguration':
        """Create instance from dictionary"""
        # Handle datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Handle nested models
        if 'tolerances' in data:
            data['tolerances'] = Tolerances(**data['tolerances'])
        
        if 'timeouts' in data:
            data['timeouts'] = Timeouts(**data['timeouts'])
        
        if 'validation_rules' in data:
            data['validation_rules'] = ValidationRules(**data['validation_rules'])
        
        if 'execution_settings' in data:
            data['execution_settings'] = ExecutionSettings(**data['execution_settings'])
        
        return cls(**data)













