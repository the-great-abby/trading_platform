#!/usr/bin/env python3
"""
String constants for Strategy Engine Testing Framework
Defines all string constants used across the testing framework
"""

from typing import List


# Test Types
class TestType:
    """Types of tests that can be performed on strategies"""
    INTERFACE = "interface"
    SIGNAL = "signal"
    PERFORMANCE = "performance"
    EDGE_CASE = "edge_case"
    ENSEMBLE = "ensemble"


# Test Status
class TestStatus:
    """Status of test execution"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    RUNNING = "running"


# Signal Actions
class SignalAction:
    """Trading signal actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# Validation Status
class ValidationStatus:
    """Status of signal validation"""
    VALID = "valid"
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"


# Market Conditions
class MarketCondition:
    """Market conditions for testing"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"


# Performance Status
class PerformanceStatus:
    """Performance validation status"""
    WITHIN_LIMITS = "within_limits"
    EXCEEDS_LIMITS = "exceeds_limits"
    CRITICAL = "critical"


# Test Suite Status
class TestSuiteStatus:
    """Test suite execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Time Frames
class TimeFrame:
    """Market data timeframes"""
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"


# Market Regimes
class MarketRegime:
    """Market regimes for testing"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


# Conflict Resolution Methods
class ConflictResolutionMethod:
    """Methods for resolving conflicts in ensemble strategies"""
    WEIGHTED_VOTING = "weighted_voting"
    MAJORITY_VOTE = "majority_vote"
    EXPERT_OVERRIDE = "expert_override"
    CONSENSUS = "consensus"
    ADAPTIVE_WEIGHTED_VOTING = "adaptive_weighted_voting"


# Strategy Categories
class StrategyCategory:
    """Categories of trading strategies"""
    BASIC = "basic"
    OPTIONS = "options"
    ADVANCED = "advanced"


# Elliott Wave Pattern Types
class ElliottWavePatternType:
    """Elliott Wave pattern types"""
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"


# Ichimoku Cloud Positions
class IchimokuCloudPosition:
    """Ichimoku cloud positions"""
    ABOVE = "above"
    BELOW = "below"
    NEUTRAL = "neutral"


# Ichimoku Signal Strength
class IchimokuSignalStrength:
    """Ichimoku signal strength"""
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


# Ichimoku Crossover Types
class IchimokuCrossoverType:
    """Ichimoku crossover types"""
    TENKAN_KIJUN = "tenkan_kijun"
    PRICE_CLOUD = "price_cloud"
    CHIKOU_PRICE = "chikou_price"
    NONE = "none"


# Sector Types
class SectorType:
    """Sector types for adaptive wave strategies"""
    TECHNOLOGY = "technology"
    FINANCIALS = "financials"
    ENERGY = "energy"
    HEALTHCARE = "healthcare"
    CONSUMER = "consumer"


# Rotation Phases
class RotationPhase:
    """Rotation phases for adaptive wave strategies"""
    EARLY_CYCLE = "early_cycle"
    MID_CYCLE = "mid_cycle"
    LATE_CYCLE = "late_cycle"
    RECESSION = "recession"


# Quantum States
class QuantumState:
    """Quantum states for quantum momentum strategies"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    SUPERPOSITION = "superposition"


# Options Strategy Types
class OptionsStrategyType:
    """Types of options strategies"""
    IRON_CONDOR = "iron_condor"
    COVERED_CALL = "covered_call"
    CASH_SECURED_PUT = "cash_secured_put"
    STRADDLE = "straddle"
    STRANGLE = "strangle"


# Greeks Types
class GreeksType:
    """Types of options Greeks"""
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"
    RHO = "rho"


# Data Quality Scores
class DataQualityScore:
    """Data quality score levels"""
    POOR = 0
    FAIR = 25
    GOOD = 50
    VERY_GOOD = 75
    EXCELLENT = 100


# Log Levels
class LogLevel:
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Utility functions for string constant validation
def get_valid_test_types() -> List[str]:
    """Get list of valid test types"""
    return [
        TestType.INTERFACE,
        TestType.SIGNAL,
        TestType.PERFORMANCE,
        TestType.EDGE_CASE,
        TestType.ENSEMBLE
    ]


def get_valid_timeframes() -> List[str]:
    """Get list of valid timeframes"""
    return [
        TimeFrame.ONE_MINUTE,
        TimeFrame.FIVE_MINUTE,
        TimeFrame.FIFTEEN_MINUTE,
        TimeFrame.ONE_HOUR,
        TimeFrame.FOUR_HOUR,
        TimeFrame.ONE_DAY
    ]


def get_valid_market_regimes() -> List[str]:
    """Get list of valid market regimes"""
    return [
        MarketRegime.BULL,
        MarketRegime.BEAR,
        MarketRegime.SIDEWAYS,
        MarketRegime.VOLATILE
    ]


def get_valid_signal_actions() -> List[str]:
    """Get list of valid signal actions"""
    return [
        SignalAction.BUY,
        SignalAction.SELL,
        SignalAction.HOLD
    ]


def get_valid_conflict_resolution_methods() -> List[str]:
    """Get list of valid conflict resolution methods"""
    return [
        ConflictResolutionMethod.WEIGHTED_VOTING,
        ConflictResolutionMethod.MAJORITY_VOTE,
        ConflictResolutionMethod.EXPERT_OVERRIDE,
        ConflictResolutionMethod.CONSENSUS,
        ConflictResolutionMethod.ADAPTIVE_WEIGHTED_VOTING
    ]


def get_valid_test_statuses() -> List[str]:
    """Get list of valid test statuses"""
    return [
        TestStatus.PASSED,
        TestStatus.FAILED,
        TestStatus.ERROR,
        TestStatus.SKIPPED,
        TestStatus.RUNNING
    ]


def get_valid_validation_statuses() -> List[str]:
    """Get list of valid validation statuses"""
    return [
        ValidationStatus.VALID,
        ValidationStatus.INVALID,
        ValidationStatus.AMBIGUOUS
    ]


def get_valid_performance_statuses() -> List[str]:
    """Get list of valid performance statuses"""
    return [
        PerformanceStatus.WITHIN_LIMITS,
        PerformanceStatus.EXCEEDS_LIMITS,
        PerformanceStatus.CRITICAL
    ]


def get_valid_test_suite_statuses() -> List[str]:
    """Get list of valid test suite statuses"""
    return [
        TestSuiteStatus.PENDING,
        TestSuiteStatus.RUNNING,
        TestSuiteStatus.COMPLETED,
        TestSuiteStatus.FAILED,
        TestSuiteStatus.CANCELLED
    ]


def validate_test_type(test_type: str) -> bool:
    """Validate if test type is valid"""
    return test_type in get_valid_test_types()


def validate_timeframe(timeframe: str) -> bool:
    """Validate if timeframe is valid"""
    return timeframe in get_valid_timeframes()


def validate_market_regime(regime: str) -> bool:
    """Validate if market regime is valid"""
    return regime in get_valid_market_regimes()


def validate_signal_action(action: str) -> bool:
    """Validate if signal action is valid"""
    return action in get_valid_signal_actions()


def validate_conflict_resolution_method(method: str) -> bool:
    """Validate if conflict resolution method is valid"""
    return method in get_valid_conflict_resolution_methods()


def validate_test_status(status: str) -> bool:
    """Validate if test status is valid"""
    return status in get_valid_test_statuses()


def validate_validation_status(status: str) -> bool:
    """Validate if validation status is valid"""
    return status in get_valid_validation_statuses()


def validate_performance_status(status: str) -> bool:
    """Validate if performance status is valid"""
    return status in get_valid_performance_statuses()


def validate_test_suite_status(status: str) -> bool:
    """Validate if test suite status is valid"""
    return status in get_valid_test_suite_statuses()
