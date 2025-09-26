#!/usr/bin/env python3
"""
Elliott Wave Analysis Service - Data Models

This module defines the core data models for Elliott Wave pattern analysis,
including pattern detection, Fibonacci analysis, and trading signals.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class WaveType(str, Enum):
    """Elliott Wave pattern types"""
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"
    EXTENSION = "extension"
    DIAGONAL = "diagonal"
    TRIANGLE = "triangle"
    FLAT = "flat"
    ZIGZAG = "zigzag"


class WaveDirection(str, Enum):
    """Wave direction enumeration"""
    UP = "up"
    DOWN = "down"


class SignalType(str, Enum):
    """Trading signal types"""
    WAVE_COMPLETION_ENTRY = "wave_completion_entry"
    FIBONACCI_RETRACEMENT = "fibonacci_retracement"
    VOLATILITY_EXPANSION = "volatility_expansion"
    PATTERN_INVALIDATION = "pattern_invalidation"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WavePoint(BaseModel):
    """Individual wave high or low point in the pattern"""
    timestamp: datetime = Field(..., description="Wave point timestamp")
    price: float = Field(..., gt=0, description="Wave point price")
    wave_number: Optional[int] = Field(None, ge=1, le=5, description="Wave number (1-5 for impulse, A-C for corrective)")
    wave_type: Optional[WaveType] = Field(None, description="Wave type classification")
    direction: Optional[WaveDirection] = Field(None, description="Wave direction (up, down)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Point reliability score (0.0-1.0)")
    
    @validator('wave_number')
    def validate_wave_number(cls, v, values):
        """Validate wave number based on pattern type"""
        if v is not None:
            wave_type = values.get('wave_type')
            if wave_type == WaveType.IMPULSE and v not in range(1, 6):
                raise ValueError('Impulse waves must be numbered 1-5')
            elif wave_type == WaveType.CORRECTIVE and v not in range(1, 4):
                raise ValueError('Corrective waves must be numbered 1-3')
        return v
    
    @validator('direction')
    def validate_direction(cls, v, values):
        """Validate wave direction consistency"""
        if v is not None:
            wave_number = values.get('wave_number')
            if wave_number is not None:
                # Impulse waves: odd numbers up, even numbers down
                if wave_number % 2 == 1 and v != WaveDirection.UP:
                    raise ValueError('Odd-numbered impulse waves must be up')
                elif wave_number % 2 == 0 and v != WaveDirection.DOWN:
                    raise ValueError('Even-numbered impulse waves must be down')
        return v


class FibonacciLevel(BaseModel):
    """Fibonacci retracement and extension levels for pattern analysis"""
    level_name: str = Field(..., description="Level identifier (e.g., 'fib_0.618_retracement')")
    price: float = Field(..., gt=0, description="Fibonacci level price")
    ratio: float = Field(..., description="Fibonacci ratio")
    level_type: str = Field(..., description="Type (retracement, extension)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Level reliability score (0.0-1.0)")
    
    @validator('ratio')
    def validate_fibonacci_ratio(cls, v):
        """Validate Fibonacci ratio is a valid Fibonacci number"""
        valid_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618, 4.236]
        if v not in valid_ratios:
            raise ValueError(f'Ratio {v} is not a valid Fibonacci number')
        return v
    
    @validator('level_type')
    def validate_level_type(cls, v):
        """Validate level type"""
        valid_types = ['retracement', 'extension']
        if v not in valid_types:
            raise ValueError(f'Level type {v} must be either retracement or extension')
        return v


class WaveRelationship(BaseModel):
    """Relationship between two waves with Fibonacci analysis"""
    wave1_number: int = Field(..., ge=1, le=5, description="First wave number")
    wave2_number: int = Field(..., ge=1, le=5, description="Second wave number")
    ratio: float = Field(..., gt=0, description="Length ratio between waves")
    fibonacci_level: Optional[float] = Field(None, description="Closest Fibonacci ratio")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Relationship confidence (0.0-1.0)")
    
    @validator('wave2_number')
    def validate_wave_numbers(cls, v, values):
        """Validate wave numbers are different"""
        wave1_number = values.get('wave1_number')
        if wave1_number is not None and v == wave1_number:
            raise ValueError('Wave numbers must be different')
        return v


class TradingSignal(BaseModel):
    """Generated trading signal based on Elliott Wave analysis"""
    symbol: str = Field(..., description="Trading symbol")
    signal_type: SignalType = Field(..., description="Signal type")
    wave_pattern: str = Field(..., description="Associated wave pattern")
    confidence: float = Field(..., ge=0.6, le=1.0, description="Signal confidence (0.6-1.0 minimum)")
    recommended_strategy: str = Field(..., description="Suggested options strategy")
    strike_selection: Dict[str, float] = Field(..., description="Recommended strike prices")
    expiration_preference: str = Field(..., description="Preferred expiration timeframe")
    risk_level: RiskLevel = Field(..., description="Risk level (high, medium, low)")
    profit_target: Optional[float] = Field(None, gt=0, description="Profit target price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    description: str = Field(..., description="Signal description")
    timestamp: datetime = Field(default_factory=datetime.now, description="Signal generation time")
    
    @validator('confidence')
    def validate_confidence_threshold(cls, v):
        """Validate confidence meets minimum threshold for signal generation"""
        if v < 0.6:
            raise ValueError('Signal confidence must be at least 0.6 for signal generation')
        return v
    
    @validator('profit_target', 'stop_loss')
    def validate_price_levels(cls, v, values):
        """Validate profit target and stop loss are reasonable"""
        if v is not None:
            # Basic validation - prices should be positive and reasonable
            if v <= 0:
                raise ValueError('Price levels must be positive')
        return v


class PatternAnalysis(BaseModel):
    """Complete analysis including extensions, relationships, and strength"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique pattern identifier")
    wave_extensions: Dict[str, Any] = Field(default_factory=dict, description="Wave extension analysis")
    fibonacci_relationships: List[WaveRelationship] = Field(default_factory=list, description="Wave-to-wave relationships")
    pattern_subtype: Optional[str] = Field(None, description="Specific pattern subtype")
    pattern_completion_prediction: Dict[str, Any] = Field(default_factory=dict, description="Completion predictions")
    pattern_strength: float = Field(..., ge=0.0, le=1.0, description="Overall pattern strength (0.0-1.0)")
    trading_signals: List[TradingSignal] = Field(default_factory=list, description="Generated trading signals")
    
    @validator('pattern_strength')
    def validate_pattern_strength(cls, v):
        """Validate pattern strength is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Pattern strength must be between 0.0 and 1.0')
        return v


class ElliottWavePattern(BaseModel):
    """Complete Elliott Wave pattern with all analysis results"""
    symbol: str = Field(..., description="Trading symbol (e.g., 'SPY', 'QQQ', 'AAPL')")
    timeframe: str = Field(default="15m", description="Analysis timeframe")
    pattern_type: WaveType = Field(..., description="Pattern type")
    waves: List[WavePoint] = Field(..., description="Individual wave points in the pattern")
    start_time: datetime = Field(..., description="Pattern start timestamp")
    end_time: datetime = Field(..., description="Pattern end timestamp")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Pattern reliability score (0.0-1.0)")
    fibonacci_levels: Dict[str, float] = Field(default_factory=dict, description="Fibonacci retracement and extension levels")
    target_price: Optional[float] = Field(None, gt=0, description="Predicted completion price")
    invalidation_level: Optional[float] = Field(None, gt=0, description="Pattern invalidation price level")
    enhanced_analysis: Optional[PatternAnalysis] = Field(None, description="Advanced analysis results")
    
    @validator('end_time')
    def validate_time_sequence(cls, v, values):
        """Validate end time is after start time"""
        start_time = values.get('start_time')
        if start_time is not None and v <= start_time:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('waves')
    def validate_wave_count(cls, v, values):
        """Validate minimum wave count for pattern type"""
        pattern_type = values.get('pattern_type')
        if pattern_type == WaveType.IMPULSE and len(v) < 5:
            raise ValueError('Impulse patterns must have at least 5 waves')
        elif pattern_type == WaveType.CORRECTIVE and len(v) < 3:
            raise ValueError('Corrective patterns must have at least 3 waves')
        return v
    
    @validator('target_price', 'invalidation_level')
    def validate_price_reasonableness(cls, v, values):
        """Validate target and invalidation prices are reasonable"""
        if v is not None:
            # Get current price from waves
            waves = values.get('waves', [])
            if waves:
                current_price = waves[-1].price
                # Target/invalidation should be within 50% of current price
                if abs(v - current_price) / current_price > 0.5:
                    raise ValueError('Target/invalidation price must be within 50% of current price')
        return v
    
    @validator('confidence')
    def validate_confidence_range(cls, v):
        """Validate confidence is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class AnalysisRequest(BaseModel):
    """Request model for Elliott Wave analysis"""
    symbol: str = Field(..., description="Trading symbol to analyze")
    timeframe: str = Field(default="15m", description="Analysis timeframe")
    include_options: bool = Field(default=True, description="Include options analysis")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence threshold")


class AnalysisResponse(BaseModel):
    """Response model for Elliott Wave analysis"""
    symbol: str = Field(..., description="Analyzed symbol")
    pattern_found: bool = Field(..., description="Whether a pattern was detected")
    pattern: Optional[ElliottWavePattern] = Field(None, description="Detected pattern (if any)")
    analysis_time: float = Field(..., description="Analysis time in seconds")
    message: Optional[str] = Field(None, description="Analysis message")


class OptionsAnalysisRequest(BaseModel):
    """Request model for options analysis"""
    symbol: str = Field(..., description="Trading symbol to analyze")
    pattern: ElliottWavePattern = Field(..., description="Elliott Wave pattern")
    current_price: float = Field(..., gt=0, description="Current market price")
    risk_tolerance: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk tolerance level")


class OptionsAnalysisResponse(BaseModel):
    """Response model for options analysis"""
    symbol: str = Field(..., description="Analyzed symbol")
    options_signals: List[TradingSignal] = Field(..., description="Generated options signals")
    trading_plan: Dict[str, Any] = Field(..., description="Comprehensive trading plan")
    analysis_time: float = Field(..., description="Analysis time in seconds")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(default="healthy", description="Service status")
    service: str = Field(default="Elliott Wave Analysis", description="Service name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    market_data_available: bool = Field(..., description="Market data service availability")
    options_integration: bool = Field(..., description="Options integration status")
    version: str = Field(default="1.0.0", description="Service version")


# Utility functions for model validation
def validate_pattern_completeness(pattern: ElliottWavePattern) -> bool:
    """Validate that a pattern is complete and follows Elliott Wave rules"""
    if pattern.pattern_type == WaveType.IMPULSE:
        return len(pattern.waves) == 5
    elif pattern.pattern_type == WaveType.CORRECTIVE:
        return len(pattern.waves) == 3
    return True


def calculate_pattern_duration(pattern: ElliottWavePattern) -> float:
    """Calculate pattern duration in hours"""
    duration = pattern.end_time - pattern.start_time
    return duration.total_seconds() / 3600


def get_pattern_price_range(pattern: ElliottWavePattern) -> tuple[float, float]:
    """Get minimum and maximum prices in the pattern"""
    prices = [wave.price for wave in pattern.waves]
    return min(prices), max(prices)


def is_pattern_valid(pattern: ElliottWavePattern) -> bool:
    """Check if pattern meets Elliott Wave validation rules"""
    try:
        # Validate the pattern
        pattern.validate(pattern.dict())
        return True
    except Exception:
        return False
