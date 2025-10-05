#!/usr/bin/env python3
"""
StrategyTestResult model for Strategy Engine Testing Framework
Represents comprehensive test results for a strategy
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .enums import TestStatus, TestType, validate_test_status, validate_test_type
from .signal_validation import SignalValidation
from .performance_metrics import PerformanceMetrics


class StrategyTestResult(BaseModel):
    """
    Comprehensive test results for a strategy
    
    Contains all test results including interface validation, signal validation,
    performance metrics, and edge case handling
    """
    
    strategy_name: str = Field(..., description="Strategy name")
    test_type: str = Field(..., description="Type of test performed")
    test_status: str = Field(..., description="Overall test status")
    test_duration_seconds: float = Field(..., gt=0, description="Total test duration")
    start_time: datetime = Field(..., description="Test start timestamp")
    end_time: Optional[datetime] = Field(None, description="Test end timestamp")
    
    # Test Results
    interface_valid: bool = Field(..., description="Interface validation result")
    signal_validations: List[SignalValidation] = Field(default_factory=list, description="Signal validation results")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    edge_case_results: Optional[Dict[str, Any]] = Field(None, description="Edge case test results")
    
    # Summary Metrics
    total_signals_generated: int = Field(..., ge=0, description="Total signals generated")
    valid_signals_count: int = Field(..., ge=0, description="Number of valid signals")
    invalid_signals_count: int = Field(..., ge=0, description="Number of invalid signals")
    average_signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Average signal confidence")
    average_validation_score: float = Field(..., ge=0.0, le=100.0, description="Average validation score")
    
    # Error Information
    error_messages: List[str] = Field(default_factory=list, description="Error messages from test")
    warnings: List[str] = Field(default_factory=list, description="Warning messages from test")
    
    # Test Configuration
    test_config: Optional[Dict[str, Any]] = Field(None, description="Test configuration used")
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Market conditions during test")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "strategy_name": "ElliottWaveStrategy",
                "test_type": "signal",
                "test_status": "passed",
                "test_duration_seconds": 45.2,
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T10:00:45Z",
                "interface_valid": True,
                "signal_validations": [],
                "performance_metrics": None,
                "edge_case_results": None,
                "total_signals_generated": 150,
                "valid_signals_count": 142,
                "invalid_signals_count": 8,
                "average_signal_confidence": 0.85,
                "average_validation_score": 87.5,
                "error_messages": [],
                "warnings": ["Low volume detected in 3 signals"],
                "test_config": {
                    "symbols": ["AAPL", "MSFT"],
                    "timeframe": "1d",
                    "lookback_periods": 50
                },
                "market_conditions": {
                    "regime": "bull",
                    "volatility": "medium"
                }
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
    
    @validator('valid_signals_count')
    def validate_valid_signals_count(cls, v, values):
        """Validate valid signals count is <= total signals"""
        if 'total_signals_generated' in values and v > values['total_signals_generated']:
            raise ValueError('Valid signals count cannot exceed total signals generated')
        return v
    
    @validator('invalid_signals_count')
    def validate_invalid_signals_count(cls, v, values):
        """Validate invalid signals count is <= total signals"""
        if 'total_signals_generated' in values and v > values['total_signals_generated']:
            raise ValueError('Invalid signals count cannot exceed total signals generated')
        return v
    
    @validator('average_signal_confidence')
    def validate_average_confidence(cls, v):
        """Validate average confidence is within valid range"""
        if not (0.0 <= v <= 1.0):
            raise ValueError('Average signal confidence must be between 0.0 and 1.0')
        return v
    
    @validator('average_validation_score')
    def validate_average_validation_score(cls, v):
        """Validate average validation score is within valid range"""
        if not (0.0 <= v <= 100.0):
            raise ValueError('Average validation score must be between 0.0 and 100.0')
        return v
    
    def is_passed(self) -> bool:
        """Check if test passed"""
        return self.test_status == TestStatus.PASSED
    
    def is_failed(self) -> bool:
        """Check if test failed"""
        return self.test_status == TestStatus.FAILED
    
    def is_error(self) -> bool:
        """Check if test had errors"""
        return self.test_status == TestStatus.ERROR
    
    def get_success_rate(self) -> float:
        """Calculate signal success rate"""
        if self.total_signals_generated == 0:
            return 0.0
        return self.valid_signals_count / self.total_signals_generated
    
    def get_failure_rate(self) -> float:
        """Calculate signal failure rate"""
        if self.total_signals_generated == 0:
            return 0.0
        return self.invalid_signals_count / self.total_signals_generated
    
    def get_overall_score(self) -> float:
        """Calculate overall test score"""
        # Weight different components
        interface_score = 100.0 if self.interface_valid else 0.0
        signal_score = self.average_validation_score
        confidence_score = self.average_signal_confidence * 100.0
        
        # Performance score (if available)
        performance_score = 100.0
        if self.performance_metrics:
            performance_score = self.performance_metrics.get_performance_score()
        
        # Weighted average
        return (interface_score * 0.2 + signal_score * 0.4 + 
                confidence_score * 0.2 + performance_score * 0.2)
    
    def get_quality_grade(self) -> str:
        """Get quality grade based on overall score"""
        score = self.get_overall_score()
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def has_errors(self) -> bool:
        """Check if test has errors"""
        return len(self.error_messages) > 0
    
    def has_warnings(self) -> bool:
        """Check if test has warnings"""
        return len(self.warnings) > 0
    
    def get_signal_breakdown(self) -> Dict[str, int]:
        """Get breakdown of signal actions"""
        breakdown = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for validation in self.signal_validations:
            breakdown[validation.signal_action] += 1
        return breakdown
    
    def get_confidence_distribution(self) -> Dict[str, int]:
        """Get distribution of confidence levels"""
        distribution = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0, "Very Low": 0}
        for validation in self.signal_validations:
            level = validation.get_confidence_level()
            distribution[level] += 1
        return distribution
    
    def get_validation_status_breakdown(self) -> Dict[str, int]:
        """Get breakdown of validation statuses"""
        breakdown = {"valid": 0, "invalid": 0, "ambiguous": 0}
        for validation in self.signal_validations:
            breakdown[validation.validation_status] += 1
        return breakdown
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for reports"""
        return {
            "strategy_name": self.strategy_name,
            "test_type": self.test_type,
            "test_status": self.test_status,
            "test_duration_seconds": self.test_duration_seconds,
            "interface_valid": self.interface_valid,
            "total_signals_generated": self.total_signals_generated,
            "valid_signals_count": self.valid_signals_count,
            "success_rate": self.get_success_rate(),
            "average_signal_confidence": self.average_signal_confidence,
            "average_validation_score": self.average_validation_score,
            "overall_score": self.get_overall_score(),
            "quality_grade": self.get_quality_grade(),
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
            "error_count": len(self.error_messages),
            "warning_count": len(self.warnings)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_name": self.strategy_name,
            "test_type": self.test_type,
            "test_status": self.test_status,
            "test_duration_seconds": self.test_duration_seconds,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "interface_valid": self.interface_valid,
            "signal_validations": [v.to_dict() for v in self.signal_validations],
            "performance_metrics": self.performance_metrics.to_dict() if self.performance_metrics else None,
            "edge_case_results": self.edge_case_results,
            "total_signals_generated": self.total_signals_generated,
            "valid_signals_count": self.valid_signals_count,
            "invalid_signals_count": self.invalid_signals_count,
            "average_signal_confidence": self.average_signal_confidence,
            "average_validation_score": self.average_validation_score,
            "error_messages": self.error_messages,
            "warnings": self.warnings,
            "test_config": self.test_config,
            "market_conditions": self.market_conditions
        }
