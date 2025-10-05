#!/usr/bin/env python3
"""
PerformanceMetrics model for Strategy Engine Testing Framework
Represents performance validation results for strategy execution
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .enums import PerformanceStatus, validate_performance_status


class PerformanceMetrics(BaseModel):
    """
    Performance validation results for strategy execution
    
    Tracks execution time, memory usage, CPU usage, and other performance metrics
    """
    
    strategy_name: str = Field(..., description="Strategy name")
    test_duration_seconds: float = Field(..., gt=0, description="Total test duration")
    signals_generated: int = Field(..., ge=0, description="Number of signals generated")
    signals_per_second: float = Field(..., ge=0, description="Signal generation rate")
    average_execution_time_ms: float = Field(..., gt=0, description="Average time per signal")
    max_execution_time_ms: float = Field(..., gt=0, description="Maximum time for single signal")
    min_execution_time_ms: float = Field(..., gt=0, description="Minimum time for single signal")
    memory_peak_mb: float = Field(..., gt=0, description="Peak memory usage")
    memory_average_mb: float = Field(..., gt=0, description="Average memory usage")
    cpu_peak_percent: float = Field(..., ge=0, le=100, description="Peak CPU usage")
    cpu_average_percent: float = Field(..., ge=0, le=100, description="Average CPU usage")
    validation_status: str = Field(..., description="Performance validation result")
    benchmark_comparison: Optional[Dict[str, float]] = Field(None, description="Comparison to performance benchmarks")
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "strategy_name": "ElliottWaveStrategy",
                "test_duration_seconds": 45.2,
                "signals_generated": 150,
                "signals_per_second": 3.32,
                "average_execution_time_ms": 85.5,
                "max_execution_time_ms": 125.0,
                "min_execution_time_ms": 45.0,
                "memory_peak_mb": 256.8,
                "memory_average_mb": 180.2,
                "cpu_peak_percent": 75.5,
                "cpu_average_percent": 45.2,
                "validation_status": PerformanceStatus.WITHIN_LIMITS,
                "benchmark_comparison": {
                    "previous_baseline": 95.0,
                    "performance_change_percent": -10.1
                }
            }
        }
    
    @validator('max_execution_time_ms')
    def validate_max_execution_time(cls, v, values):
        """Validate that max execution time is >= min execution time"""
        if 'min_execution_time_ms' in values and v < values['min_execution_time_ms']:
            raise ValueError('Max execution time must be >= min execution time')
        return v
    
    @validator('average_execution_time_ms')
    def validate_average_execution_time(cls, v, values):
        """Validate that average execution time is within min/max range"""
        if 'min_execution_time_ms' in values and v < values['min_execution_time_ms']:
            raise ValueError('Average execution time must be >= min execution time')
        if 'max_execution_time_ms' in values and v > values['max_execution_time_ms']:
            raise ValueError('Average execution time must be <= max execution time')
        return v
    
    @validator('memory_peak_mb')
    def validate_memory_peak(cls, v, values):
        """Validate that peak memory is >= average memory"""
        if 'memory_average_mb' in values and v < values['memory_average_mb']:
            raise ValueError('Peak memory must be >= average memory')
        return v
    
    @validator('cpu_peak_percent')
    def validate_cpu_peak(cls, v, values):
        """Validate that peak CPU is >= average CPU"""
        if 'cpu_average_percent' in values and v < values['cpu_average_percent']:
            raise ValueError('Peak CPU must be >= average CPU')
        return v
    
    @validator('signals_per_second')
    def validate_signals_per_second(cls, v, values):
        """Validate signals per second calculation"""
        if 'test_duration_seconds' in values and 'signals_generated' in values:
            expected = values['signals_generated'] / values['test_duration_seconds']
            if abs(v - expected) > 0.01:  # Allow small floating point differences
                raise ValueError(f'Signals per second should be {expected:.2f}, got {v:.2f}')
        return v
    
    @validator('validation_status')
    def validate_performance_status(cls, v):
        """Validate performance status is valid"""
        if not validate_performance_status(v):
            raise ValueError(f'Invalid performance status: {v}')
        return v
    
    def is_within_limits(self, 
                        max_execution_time_ms: float = 100.0,
                        max_memory_mb: float = 1024.0,
                        max_cpu_percent: float = 80.0) -> bool:
        """Check if performance is within specified limits"""
        return (
            self.max_execution_time_ms <= max_execution_time_ms and
            self.memory_peak_mb <= max_memory_mb and
            self.cpu_peak_percent <= max_cpu_percent
        )
    
    def get_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        # Weight different metrics
        execution_score = max(0, 100 - (self.average_execution_time_ms - 50) * 2)
        memory_score = max(0, 100 - (self.memory_peak_mb - 256) * 0.5)
        cpu_score = max(0, 100 - (self.cpu_peak_percent - 50) * 2)
        
        # Weighted average
        return (execution_score * 0.4 + memory_score * 0.3 + cpu_score * 0.3)
    
    def get_efficiency_ratio(self) -> float:
        """Calculate efficiency ratio (signals per second per MB of memory)"""
        if self.memory_average_mb == 0:
            return 0.0
        return self.signals_per_second / self.memory_average_mb
    
    def get_memory_efficiency(self) -> float:
        """Calculate memory efficiency (MB per signal)"""
        if self.signals_generated == 0:
            return 0.0
        return self.memory_average_mb / self.signals_generated
    
    def get_cpu_efficiency(self) -> float:
        """Calculate CPU efficiency (signals per second per CPU percent)"""
        if self.cpu_average_percent == 0:
            return 0.0
        return self.signals_per_second / self.cpu_average_percent
    
    def compare_to_benchmark(self, benchmark_metrics: 'PerformanceMetrics') -> Dict[str, float]:
        """Compare performance to benchmark metrics"""
        return {
            "execution_time_change_percent": 
                ((self.average_execution_time_ms - benchmark_metrics.average_execution_time_ms) / 
                 benchmark_metrics.average_execution_time_ms) * 100,
            "memory_change_percent": 
                ((self.memory_peak_mb - benchmark_metrics.memory_peak_mb) / 
                 benchmark_metrics.memory_peak_mb) * 100,
            "cpu_change_percent": 
                ((self.cpu_peak_percent - benchmark_metrics.cpu_peak_percent) / 
                 benchmark_metrics.cpu_peak_percent) * 100,
            "signals_per_second_change_percent": 
                ((self.signals_per_second - benchmark_metrics.signals_per_second) / 
                 benchmark_metrics.signals_per_second) * 100
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for reports"""
        return {
            "strategy_name": self.strategy_name,
            "execution_time_ms": self.average_execution_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "cpu_peak_percent": self.cpu_peak_percent,
            "signals_per_second": self.signals_per_second,
            "validation_status": self.validation_status,
            "performance_score": self.get_performance_score(),
            "efficiency_ratio": self.get_efficiency_ratio()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_name": self.strategy_name,
            "test_duration_seconds": self.test_duration_seconds,
            "signals_generated": self.signals_generated,
            "signals_per_second": self.signals_per_second,
            "average_execution_time_ms": self.average_execution_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "min_execution_time_ms": self.min_execution_time_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "memory_average_mb": self.memory_average_mb,
            "cpu_peak_percent": self.cpu_peak_percent,
            "cpu_average_percent": self.cpu_average_percent,
            "validation_status": self.validation_status,
            "benchmark_comparison": self.benchmark_comparison
        }
