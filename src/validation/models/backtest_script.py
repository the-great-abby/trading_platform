"""
BacktestScript model for the validation framework

Represents a backtest script with metadata about its location, parameters, and expected outputs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ScriptType(str, Enum):
    """Enumeration of backtest script types"""
    INDIVIDUAL_STRATEGY = "INDIVIDUAL_STRATEGY"
    MULTI_STRATEGY = "MULTI_STRATEGY"
    OPTIONS = "OPTIONS"
    COMPREHENSIVE = "COMPREHENSIVE"


class ValidationStatus(str, Enum):
    """Enumeration of validation statuses"""
    NEVER_RUN = "NEVER_RUN"
    PASSING = "PASSING"
    FAILING = "FAILING"
    ERROR = "ERROR"


class BacktestScript(BaseModel):
    """
    Represents a backtest script with metadata about its location, parameters, and expected outputs.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Script name/identifier")
    file_path: str = Field(..., description="Absolute path to script file")
    function_name: str = Field(..., description="Entry point function name")
    class_name: Optional[str] = Field(None, description="Class name if applicable")
    script_type: ScriptType = Field(..., description="Type of backtest script")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for execution")
    expected_outputs: Dict[str, Any] = Field(default_factory=dict, description="Expected result structure")
    timeout_seconds: int = Field(default=300, description="Execution timeout in seconds")
    dependencies: List[str] = Field(default_factory=list, description="Required modules/packages")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    last_validated_at: Optional[datetime] = Field(None, description="Last validation timestamp")
    validation_status: ValidationStatus = Field(default=ValidationStatus.NEVER_RUN, description="Current validation status")
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Validate that timeout is positive"""
        if v <= 0:
            raise ValueError('timeout_seconds must be positive')
        return v
    
    @validator('file_path')
    def validate_file_path(cls, v):
        """Validate that file path is absolute"""
        if not v.startswith('/'):
            raise ValueError('file_path must be absolute')
        return v
    
    @validator('function_name')
    def validate_function_name(cls, v):
        """Validate function name format"""
        if not v or not v.replace('_', '').isalnum():
            raise ValueError('function_name must be alphanumeric with underscores')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate script name format - allow spaces and common characters"""
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        # Allow alphanumeric, spaces, underscores, hyphens, and common punctuation
        cleaned = v.strip().replace(' ', '_').replace('-', '_').replace('.', '_')
        return cleaned
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_validation_status(self, status: ValidationStatus) -> None:
        """Update the validation status and timestamp"""
        self.validation_status = status
        self.last_validated_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_dependency(self, dependency: str) -> None:
        """Add a dependency to the script"""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
            self.updated_at = datetime.now()
    
    def remove_dependency(self, dependency: str) -> None:
        """Remove a dependency from the script"""
        if dependency in self.dependencies:
            self.dependencies.remove(dependency)
            self.updated_at = datetime.now()
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set a parameter value"""
        self.parameters[key] = value
        self.updated_at = datetime.now()
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value"""
        return self.parameters.get(key, default)
    
    def is_valid_for_execution(self) -> bool:
        """Check if script is valid for execution"""
        return (
            self.validation_status != ValidationStatus.ERROR and
            len(self.function_name) > 0 and
            len(self.file_path) > 0
        )
    
    def get_timeout_for_type(self) -> int:
        """Get timeout based on script type"""
        timeouts = {
            ScriptType.INDIVIDUAL_STRATEGY: 300,  # 5 minutes
            ScriptType.MULTI_STRATEGY: 600,       # 10 minutes
            ScriptType.OPTIONS: 900,              # 15 minutes
            ScriptType.COMPREHENSIVE: 1800        # 30 minutes
        }
        return timeouts.get(self.script_type, self.timeout_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "script_type": self.script_type,
            "parameters": self.parameters,
            "expected_outputs": self.expected_outputs,
            "timeout_seconds": self.timeout_seconds,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_validated_at": self.last_validated_at.isoformat() if self.last_validated_at else None,
            "validation_status": self.validation_status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestScript':
        """Create instance from dictionary"""
        # Handle datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'last_validated_at' in data and data['last_validated_at'] and isinstance(data['last_validated_at'], str):
            data['last_validated_at'] = datetime.fromisoformat(data['last_validated_at'])
        
        return cls(**data)
