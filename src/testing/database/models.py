#!/usr/bin/env python3
"""
Database models for Strategy Engine Testing Framework
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .connection import Base


class TestResultModel(Base):
    """Database model for test results"""
    
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_name = Column(String(255), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)
    test_status = Column(String(20), nullable=False)
    test_duration_seconds = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    # Test Results
    interface_valid = Column(Boolean, nullable=False, default=False)
    total_signals_generated = Column(Integer, nullable=False, default=0)
    valid_signals_count = Column(Integer, nullable=False, default=0)
    invalid_signals_count = Column(Integer, nullable=False, default=0)
    average_signal_confidence = Column(Float, nullable=False, default=0.0)
    average_validation_score = Column(Float, nullable=False, default=0.0)
    
    # Performance Metrics
    execution_time_ms = Column(Float, nullable=True)
    memory_peak_mb = Column(Float, nullable=True)
    cpu_peak_percent = Column(Float, nullable=True)
    signals_per_second = Column(Float, nullable=True)
    
    # Error Information
    error_messages = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Configuration and Metadata
    test_config = Column(JSON, nullable=True)
    market_conditions = Column(JSON, nullable=True)
    validation_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "strategy_name": self.strategy_name,
            "test_type": self.test_type,
            "test_status": self.test_status,
            "test_duration_seconds": self.test_duration_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "interface_valid": self.interface_valid,
            "total_signals_generated": self.total_signals_generated,
            "valid_signals_count": self.valid_signals_count,
            "invalid_signals_count": self.invalid_signals_count,
            "average_signal_confidence": self.average_signal_confidence,
            "average_validation_score": self.average_validation_score,
            "execution_time_ms": self.execution_time_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "cpu_peak_percent": self.cpu_peak_percent,
            "signals_per_second": self.signals_per_second,
            "error_messages": self.error_messages,
            "warnings": self.warnings,
            "test_config": self.test_config,
            "market_conditions": self.market_conditions,
            "validation_details": self.validation_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TestSuiteModel(Base):
    """Database model for test suites"""
    
    __tablename__ = "test_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(String(255), nullable=False, unique=True, index=True)
    suite_name = Column(String(255), nullable=False)
    suite_description = Column(Text, nullable=True)
    strategy_name = Column(String(255), nullable=False, index=True)
    
    # Execution Status
    suite_status = Column(String(20), nullable=False, default="pending")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    
    # Results Summary
    total_tests = Column(Integer, nullable=False, default=0)
    passed_tests = Column(Integer, nullable=False, default=0)
    failed_tests = Column(Integer, nullable=False, default=0)
    error_tests = Column(Integer, nullable=False, default=0)
    skipped_tests = Column(Integer, nullable=False, default=0)
    
    # Configuration
    suite_config = Column(JSON, nullable=True)
    execution_order = Column(JSON, nullable=True)
    parallel_execution = Column(Boolean, nullable=False, default=False)
    stop_on_first_failure = Column(Boolean, nullable=False, default=False)
    
    # Error Information
    suite_errors = Column(JSON, nullable=True)
    suite_warnings = Column(JSON, nullable=True)
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "suite_description": self.suite_description,
            "strategy_name": self.strategy_name,
            "suite_status": self.suite_status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time_seconds": self.execution_time_seconds,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "skipped_tests": self.skipped_tests,
            "suite_config": self.suite_config,
            "execution_order": self.execution_order,
            "parallel_execution": self.parallel_execution,
            "stop_on_first_failure": self.stop_on_first_failure,
            "suite_errors": self.suite_errors,
            "suite_warnings": self.suite_warnings,
            "created_by": self.created_by,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TestCaseModel(Base):
    """Database model for test cases"""
    
    __tablename__ = "test_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id = Column(String(255), nullable=False, unique=True, index=True)
    test_name = Column(String(255), nullable=False)
    test_type = Column(String(50), nullable=False)
    test_description = Column(Text, nullable=True)
    strategy_name = Column(String(255), nullable=False, index=True)
    
    # Test Configuration
    test_config = Column(JSON, nullable=True)
    expected_outcomes = Column(JSON, nullable=True)
    validation_criteria = Column(JSON, nullable=True)
    
    # Execution Status
    test_status = Column(String(20), nullable=False, default="pending")
    execution_time_seconds = Column(Float, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Test Results
    actual_results = Column(JSON, nullable=True)
    validation_passed = Column(Boolean, nullable=True)
    error_messages = Column(JSON, nullable=True)
    warning_messages = Column(JSON, nullable=True)
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign Key
    suite_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
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
            "created_by": self.created_by,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "suite_id": str(self.suite_id) if self.suite_id else None
        }


class MockDataModel(Base):
    """Database model for mock data generation"""
    
    __tablename__ = "mock_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    market_regime = Column(String(50), nullable=False)
    
    # Generation Configuration
    initial_price = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    trend_strength = Column(Float, nullable=False)
    volume_pattern = Column(String(50), nullable=False)
    noise_level = Column(Float, nullable=False)
    gaps_probability = Column(Float, nullable=False)
    
    # Generated Data
    data_points = Column(Integer, nullable=False, default=0)
    price_range_min = Column(Float, nullable=True)
    price_range_max = Column(Float, nullable=True)
    volume_total = Column(Integer, nullable=True)
    volatility_estimate = Column(Float, nullable=True)
    trend_direction = Column(String(20), nullable=True)
    
    # Quality Metrics
    data_quality_score = Column(Float, nullable=True)
    generation_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "market_regime": self.market_regime,
            "initial_price": self.initial_price,
            "volatility": self.volatility,
            "trend_strength": self.trend_strength,
            "volume_pattern": self.volume_pattern,
            "noise_level": self.noise_level,
            "gaps_probability": self.gaps_probability,
            "data_points": self.data_points,
            "price_range_min": self.price_range_min,
            "price_range_max": self.price_range_max,
            "volume_total": self.volume_total,
            "volatility_estimate": self.volatility_estimate,
            "trend_direction": self.trend_direction,
            "data_quality_score": self.data_quality_score,
            "generation_metadata": self.generation_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }













