#!/usr/bin/env python3
"""
SignalValidation model for Strategy Engine Testing Framework
Represents validation results for trading signals
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .enums import ValidationStatus, SignalAction, validate_validation_status, validate_signal_action


class SignalValidation(BaseModel):
    """
    Validation results for trading signals
    
    Tracks signal quality, timing, and consistency across different market conditions
    """
    
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    signal_timestamp: datetime = Field(..., description="Signal generation timestamp")
    signal_action: str = Field(..., description="Signal action (BUY/SELL/HOLD)")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence score")
    validation_status: str = Field(..., description="Validation result")
    validation_score: float = Field(..., ge=0.0, le=100.0, description="Overall validation score")
    timing_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Timing accuracy score")
    consistency_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Consistency across conditions")
    edge_case_handling: Optional[float] = Field(None, ge=0.0, le=1.0, description="Edge case handling score")
    validation_details: Optional[Dict[str, Any]] = Field(None, description="Detailed validation results")
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Market conditions during signal")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "strategy_name": "ElliottWaveStrategy",
                "symbol": "AAPL",
                "signal_timestamp": "2024-01-15T10:30:00Z",
                "signal_action": "BUY",
                "signal_confidence": 0.85,
                "validation_status": "valid",
                "validation_score": 87.5,
                "timing_accuracy": 0.92,
                "consistency_score": 0.88,
                "edge_case_handling": 0.75,
                "validation_details": {
                    "wave_pattern": "impulse_5",
                    "fibonacci_level": 0.618,
                    "volume_confirmation": True
                },
                "market_conditions": {
                    "volatility": "medium",
                    "trend": "bullish",
                    "volume": "above_average"
                }
            }
        }
    
    @validator('signal_action')
    def validate_signal_action(cls, v):
        """Validate signal action is valid"""
        if not validate_signal_action(v):
            raise ValueError(f'Invalid signal action: {v}')
        return v
    
    @validator('validation_status')
    def validate_validation_status(cls, v):
        """Validate validation status is valid"""
        if not validate_validation_status(v):
            raise ValueError(f'Invalid validation status: {v}')
        return v
    
    @validator('signal_confidence')
    def validate_signal_confidence(cls, v):
        """Validate signal confidence is within valid range"""
        if not (0.0 <= v <= 1.0):
            raise ValueError('Signal confidence must be between 0.0 and 1.0')
        return v
    
    @validator('validation_score')
    def validate_validation_score(cls, v):
        """Validate validation score is within valid range"""
        if not (0.0 <= v <= 100.0):
            raise ValueError('Validation score must be between 0.0 and 100.0')
        return v
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if signal has high confidence"""
        return self.signal_confidence >= threshold
    
    def is_high_quality(self, threshold: float = 80.0) -> bool:
        """Check if signal has high quality score"""
        return self.validation_score >= threshold
    
    def is_valid_signal(self) -> bool:
        """Check if signal is valid"""
        return self.validation_status == ValidationStatus.VALID
    
    def is_buy_signal(self) -> bool:
        """Check if signal is a buy signal"""
        return self.signal_action == SignalAction.BUY
    
    def is_sell_signal(self) -> bool:
        """Check if signal is a sell signal"""
        return self.signal_action == SignalAction.SELL
    
    def is_hold_signal(self) -> bool:
        """Check if signal is a hold signal"""
        return self.signal_action == SignalAction.HOLD
    
    def get_quality_grade(self) -> str:
        """Get quality grade based on validation score"""
        if self.validation_score >= 90:
            return "A"
        elif self.validation_score >= 80:
            return "B"
        elif self.validation_score >= 70:
            return "C"
        elif self.validation_score >= 60:
            return "D"
        else:
            return "F"
    
    def get_confidence_level(self) -> str:
        """Get confidence level description"""
        if self.signal_confidence >= 0.9:
            return "Very High"
        elif self.signal_confidence >= 0.8:
            return "High"
        elif self.signal_confidence >= 0.6:
            return "Medium"
        elif self.signal_confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def get_composite_score(self) -> float:
        """Calculate composite score combining confidence and validation"""
        return (self.signal_confidence * 0.4 + self.validation_score / 100.0 * 0.6) * 100
    
    def compare_to_baseline(self, baseline_validation: 'SignalValidation') -> Dict[str, float]:
        """Compare validation to baseline"""
        return {
            "confidence_change": self.signal_confidence - baseline_validation.signal_confidence,
            "validation_score_change": self.validation_score - baseline_validation.validation_score,
            "timing_accuracy_change": (self.timing_accuracy or 0) - (baseline_validation.timing_accuracy or 0),
            "consistency_change": (self.consistency_score or 0) - (baseline_validation.consistency_score or 0)
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for reports"""
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "signal_action": self.signal_action,
            "signal_confidence": self.signal_confidence,
            "validation_status": self.validation_status,
            "validation_score": self.validation_score,
            "quality_grade": self.get_quality_grade(),
            "confidence_level": self.get_confidence_level(),
            "composite_score": self.get_composite_score()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "signal_timestamp": self.signal_timestamp.isoformat(),
            "signal_action": self.signal_action,
            "signal_confidence": self.signal_confidence,
            "validation_status": self.validation_status,
            "validation_score": self.validation_score,
            "timing_accuracy": self.timing_accuracy,
            "consistency_score": self.consistency_score,
            "edge_case_handling": self.edge_case_handling,
            "validation_details": self.validation_details,
            "market_conditions": self.market_conditions
        }


class SignalValidationBatch(BaseModel):
    """Batch of signal validations for analysis"""
    
    validations: List[SignalValidation] = Field(..., description="List of signal validations")
    batch_id: str = Field(..., description="Unique batch identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation timestamp")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get batch statistics"""
        if not self.validations:
            return {}
        
        total_signals = len(self.validations)
        valid_signals = sum(1 for v in self.validations if v.is_valid_signal())
        buy_signals = sum(1 for v in self.validations if v.is_buy_signal())
        sell_signals = sum(1 for v in self.validations if v.is_sell_signal())
        hold_signals = sum(1 for v in self.validations if v.is_hold_signal())
        
        avg_confidence = sum(v.signal_confidence for v in self.validations) / total_signals
        avg_validation_score = sum(v.validation_score for v in self.validations) / total_signals
        
        return {
            "total_signals": total_signals,
            "valid_signals": valid_signals,
            "validity_rate": valid_signals / total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "average_confidence": avg_confidence,
            "average_validation_score": avg_validation_score,
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat()
        }
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by strategy"""
        strategy_stats = {}
        
        for validation in self.validations:
            strategy_name = validation.strategy_name
            if strategy_name not in strategy_stats:
                strategy_stats[strategy_name] = {
                    "total_signals": 0,
                    "valid_signals": 0,
                    "avg_confidence": 0.0,
                    "avg_validation_score": 0.0,
                    "signal_actions": {"BUY": 0, "SELL": 0, "HOLD": 0}
                }
            
            stats = strategy_stats[strategy_name]
            stats["total_signals"] += 1
            if validation.is_valid_signal():
                stats["valid_signals"] += 1
            stats["avg_confidence"] += validation.signal_confidence
            stats["avg_validation_score"] += validation.validation_score
            stats["signal_actions"][validation.signal_action] += 1
        
        # Calculate averages
        for strategy_name, stats in strategy_stats.items():
            if stats["total_signals"] > 0:
                stats["avg_confidence"] /= stats["total_signals"]
                stats["avg_validation_score"] /= stats["total_signals"]
                stats["validity_rate"] = stats["valid_signals"] / stats["total_signals"]
        
        return strategy_stats
