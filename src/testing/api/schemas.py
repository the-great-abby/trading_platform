#!/usr/bin/env python3
"""
API schemas for Strategy Engine Testing Framework
Defines request/response models for all API endpoints
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from ..models import (
    StrategyTestResult, SignalValidation, PerformanceMetrics,
    MockMarketData, TestSuite, TestCase
)


# Request Models
class StrategyValidationRequest(BaseModel):
    """Request model for strategy validation"""
    strategy_name: str = Field(..., description="Name of the strategy to validate")
    config: Dict[str, Any] = Field(default_factory=dict, description="Strategy configuration")
    mock_market_data: Optional[Dict[str, Any]] = Field(None, description="Mock market data for testing")


class SignalTestingRequest(BaseModel):
    """Request model for signal testing"""
    strategy_name: str = Field(..., description="Name of the strategy to test")
    symbol: str = Field(..., description="Trading symbol")
    mock_data: Dict[str, Any] = Field(..., description="Mock market data")
    test_config: Dict[str, Any] = Field(default_factory=dict, description="Test configuration")


class PerformanceTestingRequest(BaseModel):
    """Request model for performance testing"""
    strategy_name: str = Field(..., description="Name of the strategy to test")
    test_config: Dict[str, Any] = Field(default_factory=dict, description="Test configuration")
    signal_count: int = Field(100, ge=1, le=1000, description="Number of signals to generate")
    performance_limits: Optional[Dict[str, float]] = Field(None, description="Custom performance limits")


class EnsembleTestingRequest(BaseModel):
    """Request model for ensemble testing"""
    strategies: List[Dict[str, Any]] = Field(..., description="List of strategies and their configs")
    symbols: List[str] = Field(..., description="Trading symbols to test")
    mock_data: Dict[str, Any] = Field(..., description="Mock market data")
    conflict_resolution_method: str = Field("weighted_voting", description="Conflict resolution method")


class MockDataRequest(BaseModel):
    """Request model for mock data generation"""
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Data timeframe")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    market_regime: str = Field(..., description="Market regime")
    initial_price: float = Field(100.0, gt=0, description="Initial price")
    volatility: float = Field(0.2, ge=0.0, le=1.0, description="Price volatility")
    trend_strength: float = Field(0.0, ge=-1.0, le=1.0, description="Trend strength")
    volume_pattern: str = Field("normal", description="Volume pattern")
    noise_level: float = Field(0.1, ge=0.0, le=1.0, description="Market noise level")
    gaps_probability: float = Field(0.05, ge=0.0, le=1.0, description="Probability of gaps")


class TestSuiteRequest(BaseModel):
    """Request model for test suite operations"""
    suite_name: str = Field(..., description="Test suite name")
    strategy_name: str = Field(..., description="Strategy to test")
    test_cases: List[Dict[str, Any]] = Field(..., description="Test cases to include")
    suite_config: Dict[str, Any] = Field(default_factory=dict, description="Suite configuration")


# Response Models
class StrategyValidationResponse(BaseModel):
    """Response model for strategy validation"""
    strategy_name: str = Field(..., description="Strategy name")
    validation_result: StrategyTestResult = Field(..., description="Validation results")
    success: bool = Field(..., description="Whether validation succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class SignalTestingResponse(BaseModel):
    """Response model for signal testing"""
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    signal_validations: List[SignalValidation] = Field(..., description="Signal validation results")
    quality_summary: Dict[str, Any] = Field(..., description="Overall quality summary")
    success: bool = Field(..., description="Whether testing succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class PerformanceTestingResponse(BaseModel):
    """Response model for performance testing"""
    strategy_name: str = Field(..., description="Strategy name")
    performance_metrics: PerformanceMetrics = Field(..., description="Performance metrics")
    limits_validation: Dict[str, Any] = Field(..., description="Performance limits validation")
    recommendations: List[str] = Field(..., description="Performance optimization recommendations")
    success: bool = Field(..., description="Whether testing succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class EnsembleTestingResponse(BaseModel):
    """Response model for ensemble testing"""
    ensemble_results: Dict[str, Any] = Field(..., description="Ensemble testing results")
    conflict_resolution: Dict[str, Any] = Field(..., description="Conflict resolution details")
    consensus_signals: List[Dict[str, Any]] = Field(..., description="Consensus signals")
    success: bool = Field(..., description="Whether testing succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class MockDataResponse(BaseModel):
    """Response model for mock data generation"""
    mock_data: MockMarketData = Field(..., description="Generated mock data")
    generation_info: Dict[str, Any] = Field(..., description="Data generation information")
    success: bool = Field(..., description="Whether generation succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class TestSuiteResponse(BaseModel):
    """Response model for test suite operations"""
    test_suite: TestSuite = Field(..., description="Test suite")
    execution_results: Dict[str, Any] = Field(..., description="Execution results")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Response message")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class StrategyListResponse(BaseModel):
    """Response model for strategy listing"""
    strategies: List[Dict[str, Any]] = Field(..., description="List of available strategies")
    total_count: int = Field(..., description="Total number of strategies")
    categories: Dict[str, int] = Field(..., description="Strategy counts by category")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Response message")


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime")
    timestamp: datetime = Field(..., description="Health check timestamp")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Utility Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Page size")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Filter parameters"""
    strategy_name: Optional[str] = Field(None, description="Filter by strategy name")
    test_type: Optional[str] = Field(None, description="Filter by test type")
    test_status: Optional[str] = Field(None, description="Filter by test status")
    date_from: Optional[str] = Field(None, description="Filter from date")
    date_to: Optional[str] = Field(None, description="Filter to date")


class BatchOperationRequest(BaseModel):
    """Request model for batch operations"""
    operation: str = Field(..., description="Operation to perform")
    parameters: List[Dict[str, Any]] = Field(..., description="Operation parameters")
    parallel: bool = Field(False, description="Whether to run operations in parallel")
    timeout_seconds: int = Field(300, ge=1, le=3600, description="Operation timeout")


class BatchOperationResponse(BaseModel):
    """Response model for batch operations"""
    operation: str = Field(..., description="Operation performed")
    results: List[Dict[str, Any]] = Field(..., description="Operation results")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    total_execution_time_ms: float = Field(..., description="Total execution time")
    success: bool = Field(..., description="Whether batch operation succeeded")
    message: str = Field(..., description="Response message")
