#!/usr/bin/env python3
"""
TestCase model for Strategy Engine Testing Framework
Represents individual test cases for strategy validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .enums import TestType, TestStatus, validate_test_type, validate_test_status


class TestCase(BaseModel):
    """
    Individual test case for strategy validation
    
    Defines a specific test scenario with expected outcomes and validation criteria
    """
    
    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Human-readable test name")
    test_type: str = Field(..., description="Type of test")
    test_description: str = Field(..., description="Detailed test description")
    
    # Test Configuration
    strategy_name: str = Field(..., description="Strategy to test")
    test_config: Dict[str, Any] = Field(default_factory=dict, description="Test configuration parameters")
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict, description="Expected test outcomes")
    validation_criteria: Dict[str, Any] = Field(default_factory=dict, description="Validation criteria")
    
    # Test Execution
    test_status: str = Field(default="pending", description="Current test status")
    execution_time_seconds: Optional[float] = Field(None, description="Test execution time")
    start_time: Optional[datetime] = Field(None, description="Test start timestamp")
    end_time: Optional[datetime] = Field(None, description="Test end timestamp")
    
    # Test Results
    actual_results: Optional[Dict[str, Any]] = Field(None, description="Actual test results")
    validation_passed: Optional[bool] = Field(None, description="Whether validation passed")
    error_messages: List[str] = Field(default_factory=list, description="Error messages from test")
    warning_messages: List[str] = Field(default_factory=list, description="Warning messages from test")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Test creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Test creator")
    tags: List[str] = Field(default_factory=list, description="Test tags for categorization")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "test_id": "test_elliott_wave_impulse_001",
                "test_name": "Elliott Wave Impulse Pattern Detection",
                "test_type": "signal",
                "test_description": "Test Elliott Wave strategy's ability to detect impulse patterns",
                "strategy_name": "ElliottWaveStrategy",
                "test_config": {
                    "symbols": ["AAPL"],
                    "timeframe": "1d",
                    "lookback_periods": 50,
                    "confidence_threshold": 0.8
                },
                "expected_outcomes": {
                    "min_signals_generated": 10,
                    "max_false_positive_rate": 0.1,
                    "min_confidence_score": 0.75
                },
                "validation_criteria": {
                    "pattern_accuracy": 0.85,
                    "signal_timing": "within_2_bars"
                },
                "test_status": "pending",
                "execution_time_seconds": None,
                "start_time": None,
                "end_time": None,
                "actual_results": None,
                "validation_passed": None,
                "error_messages": [],
                "warning_messages": [],
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "created_by": "test_engine",
                "tags": ["elliott_wave", "pattern_detection", "signal_validation"]
            }
        }
    
    @validator('test_type')
    def validate_test_type(cls, v):
        """Validate test type is valid"""
        if not validate_test_type(v):
            raise ValueError(f'Invalid test type: {v}')
        return v
    
    @validator('test_status')
    def validate_test_status(cls, v):
        """Validate test status is valid"""
        if not validate_test_status(v):
            raise ValueError(f'Invalid test status: {v}')
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time"""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    def is_pending(self) -> bool:
        """Check if test is pending"""
        return self.test_status == TestStatus.PENDING
    
    def is_running(self) -> bool:
        """Check if test is running"""
        return self.test_status == TestStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if test is completed"""
        return self.test_status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
    
    def is_passed(self) -> bool:
        """Check if test passed"""
        return self.test_status == TestStatus.PASSED
    
    def is_failed(self) -> bool:
        """Check if test failed"""
        return self.test_status == TestStatus.FAILED
    
    def is_error(self) -> bool:
        """Check if test had errors"""
        return self.test_status == TestStatus.ERROR
    
    def has_errors(self) -> bool:
        """Check if test has error messages"""
        return len(self.error_messages) > 0
    
    def has_warnings(self) -> bool:
        """Check if test has warning messages"""
        return len(self.warning_messages) > 0
    
    def get_execution_duration(self) -> Optional[float]:
        """Get test execution duration"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def start_execution(self) -> None:
        """Start test execution"""
        self.test_status = TestStatus.RUNNING
        self.start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_execution(self, status: str, results: Optional[Dict[str, Any]] = None, 
                          validation_passed: Optional[bool] = None) -> None:
        """Complete test execution"""
        self.test_status = status
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.start_time:
            self.execution_time_seconds = (self.end_time - self.start_time).total_seconds()
        
        if results is not None:
            self.actual_results = results
        
        if validation_passed is not None:
            self.validation_passed = validation_passed
    
    def add_error(self, error_message: str) -> None:
        """Add error message"""
        self.error_messages.append(error_message)
        self.updated_at = datetime.utcnow()
    
    def add_warning(self, warning_message: str) -> None:
        """Add warning message"""
        self.warning_messages.append(warning_message)
        self.updated_at = datetime.utcnow()
    
    def validate_results(self) -> bool:
        """Validate test results against criteria"""
        if not self.actual_results or not self.validation_criteria:
            return False
        
        # Example validation logic - can be extended based on criteria
        for criterion, expected_value in self.validation_criteria.items():
            if criterion not in self.actual_results:
                return False
            
            actual_value = self.actual_results[criterion]
            
            # Handle different types of comparisons
            if isinstance(expected_value, dict):
                if 'min' in expected_value and actual_value < expected_value['min']:
                    return False
                if 'max' in expected_value and actual_value > expected_value['max']:
                    return False
                if 'equals' in expected_value and actual_value != expected_value['equals']:
                    return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test case summary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "strategy_name": self.strategy_name,
            "test_status": self.test_status,
            "execution_time_seconds": self.execution_time_seconds,
            "validation_passed": self.validation_passed,
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
            "error_count": len(self.error_messages),
            "warning_count": len(self.warning_messages),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "test_description": self.test_description,
            "strategy_name": self.strategy_name,
            "test_config": self.test_config,
            "expected_outcomes": self.expected_outcomes,
            "validation_criteria": self.validation_criteria,
            "test_status": self.test_status,
            "execution_time_seconds": self.execution_time_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "actual_results": self.actual_results,
            "validation_passed": self.validation_passed,
            "error_messages": self.error_messages,
            "warning_messages": self.warning_messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags
        }
