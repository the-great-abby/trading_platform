#!/usr/bin/env python3
"""
Models package for Strategy Engine Testing Framework
Provides all data models for the testing framework
"""

from .enums import (
    TestType, TestStatus, SignalAction, ValidationStatus, MarketCondition,
    PerformanceStatus, TestSuiteStatus, TimeFrame, MarketRegime,
    ConflictResolutionMethod, StrategyCategory, ElliottWavePatternType,
    IchimokuCloudPosition, IchimokuSignalStrength, IchimokuCrossoverType,
    SectorType, RotationPhase, QuantumState, OptionsStrategyType,
    GreeksType, DataQualityScore, LogLevel,
    get_valid_test_types, get_valid_timeframes, get_valid_market_regimes,
    get_valid_signal_actions, get_valid_conflict_resolution_methods,
    get_valid_test_statuses, get_valid_validation_statuses,
    get_valid_performance_statuses, get_valid_test_suite_statuses,
    validate_test_type, validate_timeframe, validate_market_regime,
    validate_signal_action, validate_conflict_resolution_method,
    validate_test_status, validate_validation_status,
    validate_performance_status, validate_test_suite_status
)

from .price_bar import PriceBar

from .performance_metrics import PerformanceMetrics

from .signal_validation import SignalValidation, SignalValidationBatch

from .strategy_test_result import StrategyTestResult

from .mock_market_data import MockMarketData, MockDataGenerationConfig

from .test_case import TestCase

from .test_suite import TestSuite

__all__ = [
    # Enums and constants
    'TestType', 'TestStatus', 'SignalAction', 'ValidationStatus', 'MarketCondition',
    'PerformanceStatus', 'TestSuiteStatus', 'TimeFrame', 'MarketRegime',
    'ConflictResolutionMethod', 'StrategyCategory', 'ElliottWavePatternType',
    'IchimokuCloudPosition', 'IchimokuSignalStrength', 'IchimokuCrossoverType',
    'SectorType', 'RotationPhase', 'QuantumState', 'OptionsStrategyType',
    'GreeksType', 'DataQualityScore', 'LogLevel',
    
    # Validation functions
    'get_valid_test_types', 'get_valid_timeframes', 'get_valid_market_regimes',
    'get_valid_signal_actions', 'get_valid_conflict_resolution_methods',
    'get_valid_test_statuses', 'get_valid_validation_statuses',
    'get_valid_performance_statuses', 'get_valid_test_suite_statuses',
    'validate_test_type', 'validate_timeframe', 'validate_market_regime',
    'validate_signal_action', 'validate_conflict_resolution_method',
    'validate_test_status', 'validate_validation_status',
    'validate_performance_status', 'validate_test_suite_status',
    
    # Data models
    'PriceBar',
    'PerformanceMetrics',
    'SignalValidation', 'SignalValidationBatch',
    'StrategyTestResult',
    'MockMarketData', 'MockDataGenerationConfig',
    'TestCase',
    'TestSuite'
]













