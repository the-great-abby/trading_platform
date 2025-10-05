#!/usr/bin/env python3
"""
TestSuite model for Strategy Engine Testing Framework
Represents a collection of test cases for comprehensive strategy validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .enums import TestSuiteStatus, validate_test_suite_status
from .test_case import TestCase


class TestSuite(BaseModel):
    """
    Collection of test cases for comprehensive strategy validation
    
    Organizes and manages multiple test cases for thorough strategy testing
    """
    
    suite_id: str = Field(..., description="Unique test suite identifier")
    suite_name: str = Field(..., description="Human-readable test suite name")
    suite_description: str = Field(..., description="Detailed test suite description")
    strategy_name: str = Field(..., description="Strategy being tested")
    
    # Test Cases
    test_cases: List[TestCase] = Field(default_factory=list, description="Test cases in the suite")
    
    # Suite Configuration
    suite_config: Dict[str, Any] = Field(default_factory=dict, description="Suite configuration")
    execution_order: Optional[List[str]] = Field(None, description="Test execution order")
    parallel_execution: bool = Field(False, description="Whether tests can run in parallel")
    stop_on_first_failure: bool = Field(False, description="Stop execution on first failure")
    
    # Execution Status
    suite_status: str = Field(default="pending", description="Suite execution status")
    start_time: Optional[datetime] = Field(None, description="Suite start timestamp")
    end_time: Optional[datetime] = Field(None, description="Suite end timestamp")
    execution_time_seconds: Optional[float] = Field(None, description="Total execution time")
    
    # Results Summary
    total_tests: int = Field(0, description="Total number of tests")
    passed_tests: int = Field(0, description="Number of passed tests")
    failed_tests: int = Field(0, description="Number of failed tests")
    error_tests: int = Field(0, description="Number of tests with errors")
    skipped_tests: int = Field(0, description="Number of skipped tests")
    
    # Error Information
    suite_errors: List[str] = Field(default_factory=list, description="Suite-level errors")
    suite_warnings: List[str] = Field(default_factory=list, description="Suite-level warnings")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Suite creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Suite creator")
    tags: List[str] = Field(default_factory=list, description="Suite tags for categorization")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "suite_id": "suite_elliott_wave_comprehensive",
                "suite_name": "Elliott Wave Comprehensive Test Suite",
                "suite_description": "Comprehensive testing of Elliott Wave strategy",
                "strategy_name": "ElliottWaveStrategy",
                "test_cases": [],
                "suite_config": {
                    "timeout_seconds": 300,
                    "retry_failed_tests": True,
                    "max_retries": 3
                },
                "execution_order": None,
                "parallel_execution": False,
                "stop_on_first_failure": False,
                "suite_status": "pending",
                "start_time": None,
                "end_time": None,
                "execution_time_seconds": None,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "error_tests": 0,
                "skipped_tests": 0,
                "suite_errors": [],
                "suite_warnings": [],
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "created_by": "test_engine",
                "tags": ["elliott_wave", "comprehensive", "strategy_validation"]
            }
        }
    
    @validator('suite_status')
    def validate_suite_status(cls, v):
        """Validate suite status is valid"""
        if not validate_test_suite_status(v):
            raise ValueError(f'Invalid suite status: {v}')
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time"""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('execution_order')
    def validate_execution_order(cls, v, values):
        """Validate execution order contains valid test IDs"""
        if v and 'test_cases' in values:
            test_ids = {test_case.test_id for test_case in values['test_cases']}
            for test_id in v:
                if test_id not in test_ids:
                    raise ValueError(f'Execution order contains invalid test ID: {test_id}')
        return v
    
    def add_test_case(self, test_case: TestCase) -> None:
        """Add a test case to the suite"""
        self.test_cases.append(test_case)
        self.total_tests = len(self.test_cases)
        self.updated_at = datetime.utcnow()
    
    def remove_test_case(self, test_id: str) -> bool:
        """Remove a test case from the suite"""
        for i, test_case in enumerate(self.test_cases):
            if test_case.test_id == test_id:
                del self.test_cases[i]
                self.total_tests = len(self.test_cases)
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Get a test case by ID"""
        for test_case in self.test_cases:
            if test_case.test_id == test_id:
                return test_case
        return None
    
    def is_pending(self) -> bool:
        """Check if suite is pending"""
        return self.suite_status == TestSuiteStatus.PENDING
    
    def is_running(self) -> bool:
        """Check if suite is running"""
        return self.suite_status == TestSuiteStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if suite is completed"""
        return self.suite_status in [TestSuiteStatus.COMPLETED, TestSuiteStatus.FAILED]
    
    def is_failed(self) -> bool:
        """Check if suite failed"""
        return self.suite_status == TestSuiteStatus.FAILED
    
    def has_errors(self) -> bool:
        """Check if suite has errors"""
        return len(self.suite_errors) > 0 or any(tc.has_errors() for tc in self.test_cases)
    
    def has_warnings(self) -> bool:
        """Check if suite has warnings"""
        return len(self.suite_warnings) > 0 or any(tc.has_warnings() for tc in self.test_cases)
    
    def get_success_rate(self) -> float:
        """Calculate test success rate"""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests
    
    def get_failure_rate(self) -> float:
        """Calculate test failure rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.failed_tests + self.error_tests) / self.total_tests
    
    def get_execution_duration(self) -> Optional[float]:
        """Get suite execution duration"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def start_execution(self) -> None:
        """Start suite execution"""
        self.suite_status = TestSuiteStatus.RUNNING
        self.start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Reset counters
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
    
    def complete_execution(self) -> None:
        """Complete suite execution"""
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.start_time:
            self.execution_time_seconds = (self.end_time - self.start_time).total_seconds()
        
        # Update counters
        self.passed_tests = sum(1 for tc in self.test_cases if tc.is_passed())
        self.failed_tests = sum(1 for tc in self.test_cases if tc.is_failed())
        self.error_tests = sum(1 for tc in self.test_cases if tc.is_error())
        self.skipped_tests = sum(1 for tc in self.test_cases if tc.is_pending())
        
        # Determine final status
        if self.failed_tests > 0 or self.error_tests > 0:
            self.suite_status = TestSuiteStatus.FAILED
        else:
            self.suite_status = TestSuiteStatus.COMPLETED
    
    def add_suite_error(self, error_message: str) -> None:
        """Add suite-level error"""
        self.suite_errors.append(error_message)
        self.updated_at = datetime.utcnow()
    
    def add_suite_warning(self, warning_message: str) -> None:
        """Add suite-level warning"""
        self.suite_warnings.append(warning_message)
        self.updated_at = datetime.utcnow()
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all tests"""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "skipped_tests": self.skipped_tests,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate()
        }
    
    def get_failed_tests(self) -> List[TestCase]:
        """Get list of failed tests"""
        return [tc for tc in self.test_cases if tc.is_failed() or tc.is_error()]
    
    def get_passed_tests(self) -> List[TestCase]:
        """Get list of passed tests"""
        return [tc for tc in self.test_cases if tc.is_passed()]
    
    def get_test_cases_by_type(self, test_type: str) -> List[TestCase]:
        """Get test cases by type"""
        return [tc for tc in self.test_cases if tc.test_type == test_type]
    
    def get_test_cases_by_tag(self, tag: str) -> List[TestCase]:
        """Get test cases by tag"""
        return [tc for tc in self.test_cases if tag in tc.tags]
    
    def get_execution_order(self) -> List[TestCase]:
        """Get test cases in execution order"""
        if not self.execution_order:
            return self.test_cases.copy()
        
        ordered_tests = []
        test_dict = {tc.test_id: tc for tc in self.test_cases}
        
        for test_id in self.execution_order:
            if test_id in test_dict:
                ordered_tests.append(test_dict[test_id])
        
        # Add any tests not in execution order
        for tc in self.test_cases:
            if tc.test_id not in self.execution_order:
                ordered_tests.append(tc)
        
        return ordered_tests
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for reports"""
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "strategy_name": self.strategy_name,
            "suite_status": self.suite_status,
            "execution_time_seconds": self.execution_time_seconds,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "skipped_tests": self.skipped_tests,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "suite_description": self.suite_description,
            "strategy_name": self.strategy_name,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "suite_config": self.suite_config,
            "execution_order": self.execution_order,
            "parallel_execution": self.parallel_execution,
            "stop_on_first_failure": self.stop_on_first_failure,
            "suite_status": self.suite_status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time_seconds": self.execution_time_seconds,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "skipped_tests": self.skipped_tests,
            "suite_errors": self.suite_errors,
            "suite_warnings": self.suite_warnings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags
        }
