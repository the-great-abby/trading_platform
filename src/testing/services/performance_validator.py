#!/usr/bin/env python3
"""
PerformanceValidator service for Strategy Engine Testing Framework
Validates strategy performance and execution metrics
"""

import asyncio
import time
import psutil
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import (
    PerformanceMetrics, PerformanceStatus, StrategyTestResult,
    TestStatus, TestType
)


class PerformanceValidator:
    """
    Validates strategy performance and execution metrics
    
    Tests execution time, memory usage, CPU usage, and other performance indicators
    """
    
    def __init__(self):
        """Initialize performance validator"""
        self.max_execution_time_ms = 100.0  # 100ms per signal
        self.max_memory_mb = 1024.0  # 1GB max memory
        self.max_cpu_percent = 80.0  # 80% max CPU
        self.min_signals_per_second = 1.0  # Minimum signal generation rate
    
    async def validate_performance(self, strategy, test_config: Dict[str, Any], 
                                 signal_count: int = 100) -> PerformanceMetrics:
        """
        Validate strategy performance
        
        Args:
            strategy: Strategy instance to test
            test_config: Test configuration
            signal_count: Number of signals to generate for testing
            
        Returns:
            PerformanceMetrics with validation results
        """
        start_time = datetime.utcnow()
        process = psutil.Process(os.getpid())
        
        # Initialize performance tracking
        execution_times = []
        memory_samples = []
        cpu_samples = []
        signals_generated = 0
        
        try:
            # Start performance monitoring
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = process.cpu_percent()
            
            # Generate signals and measure performance
            for i in range(signal_count):
                # Measure execution time
                exec_start = time.time()
                
                try:
                    # Generate a test signal (simplified for performance testing)
                    signal = await self._generate_test_signal(strategy, test_config)
                    if signal:
                        signals_generated += 1
                except Exception as e:
                    # Continue testing even if individual signals fail
                    pass
                
                exec_end = time.time()
                execution_time_ms = (exec_end - exec_start) * 1000
                execution_times.append(execution_time_ms)
                
                # Sample memory and CPU
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                memory_samples.append(memory_mb)
                cpu_samples.append(cpu_percent)
                
                # Small delay to allow CPU sampling
                await asyncio.sleep(0.001)
            
            # Calculate final metrics
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            # Performance calculations
            signals_per_second = signals_generated / total_duration if total_duration > 0 else 0
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0
            
            memory_peak = max(memory_samples) if memory_samples else initial_memory
            memory_average = sum(memory_samples) / len(memory_samples) if memory_samples else initial_memory
            cpu_peak = max(cpu_samples) if cpu_samples else initial_cpu
            cpu_average = sum(cpu_samples) / len(cpu_samples) if cpu_samples else initial_cpu
            
            # Determine validation status
            validation_status = self._determine_performance_status(
                avg_execution_time, memory_peak, cpu_peak, signals_per_second
            )
            
            # Create performance metrics
            performance_metrics = PerformanceMetrics(
                strategy_name=getattr(strategy, 'name', 'Unknown'),
                test_duration_seconds=total_duration,
                signals_generated=signals_generated,
                signals_per_second=signals_per_second,
                average_execution_time_ms=avg_execution_time,
                max_execution_time_ms=max_execution_time,
                min_execution_time_ms=min_execution_time,
                memory_peak_mb=memory_peak,
                memory_average_mb=memory_average,
                cpu_peak_percent=cpu_peak,
                cpu_average_percent=cpu_average,
                validation_status=validation_status,
                benchmark_comparison=self._generate_benchmark_comparison(
                    avg_execution_time, memory_peak, cpu_peak, signals_per_second
                )
            )
            
            return performance_metrics
            
        except Exception as e:
            # Return error performance metrics
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            return PerformanceMetrics(
                strategy_name=getattr(strategy, 'name', 'Unknown'),
                test_duration_seconds=total_duration,
                signals_generated=0,
                signals_per_second=0.0,
                average_execution_time_ms=0.0,
                max_execution_time_ms=0.0,
                min_execution_time_ms=0.0,
                memory_peak_mb=0.0,
                memory_average_mb=0.0,
                cpu_peak_percent=0.0,
                cpu_average_percent=0.0,
                validation_status=PerformanceStatus.CRITICAL,
                benchmark_comparison={"error": str(e)}
            )
    
    async def _generate_test_signal(self, strategy, test_config: Dict[str, Any]):
        """Generate a test signal for performance testing"""
        try:
            # Create minimal test data
            import pandas as pd
            import numpy as np
            
            # Generate simple test data
            dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
            test_data = pd.DataFrame({
                'open': np.random.uniform(100, 110, 50),
                'high': np.random.uniform(105, 115, 50),
                'low': np.random.uniform(95, 105, 50),
                'close': np.random.uniform(100, 110, 50),
                'volume': np.random.randint(1000, 10000, 50)
            }, index=dates)
            
            # Generate signal
            signal = await strategy.generate_signal(
                symbol=test_config.get('symbol', 'TEST'),
                data=test_data
            )
            
            return signal
            
        except Exception:
            # Return None if signal generation fails
            return None
    
    def _determine_performance_status(self, avg_execution_time: float, 
                                    memory_peak: float, cpu_peak: float,
                                    signals_per_second: float) -> str:
        """Determine performance validation status"""
        # Check critical thresholds
        if (avg_execution_time > self.max_execution_time_ms * 2 or
            memory_peak > self.max_memory_mb * 1.5 or
            cpu_peak > self.max_cpu_percent * 1.2 or
            signals_per_second < self.min_signals_per_second * 0.5):
            return PerformanceStatus.CRITICAL
        
        # Check warning thresholds
        if (avg_execution_time > self.max_execution_time_ms or
            memory_peak > self.max_memory_mb or
            cpu_peak > self.max_cpu_percent or
            signals_per_second < self.min_signals_per_second):
            return PerformanceStatus.EXCEEDS_LIMITS
        
        # Within acceptable limits
        return PerformanceStatus.WITHIN_LIMITS
    
    def _generate_benchmark_comparison(self, avg_execution_time: float,
                                     memory_peak: float, cpu_peak: float,
                                     signals_per_second: float) -> Dict[str, float]:
        """Generate benchmark comparison data"""
        # Define baseline benchmarks (these could be configurable)
        baseline_execution_time = 50.0  # ms
        baseline_memory = 256.0  # MB
        baseline_cpu = 30.0  # percent
        baseline_signals_per_second = 5.0
        
        return {
            "baseline_execution_time_ms": baseline_execution_time,
            "execution_time_change_percent": 
                ((avg_execution_time - baseline_execution_time) / baseline_execution_time) * 100,
            "baseline_memory_mb": baseline_memory,
            "memory_change_percent": 
                ((memory_peak - baseline_memory) / baseline_memory) * 100,
            "baseline_cpu_percent": baseline_cpu,
            "cpu_change_percent": 
                ((cpu_peak - baseline_cpu) / baseline_cpu) * 100,
            "baseline_signals_per_second": baseline_signals_per_second,
            "signals_per_second_change_percent": 
                ((signals_per_second - baseline_signals_per_second) / baseline_signals_per_second) * 100
        }
    
    async def validate_performance_limits(self, performance_metrics: PerformanceMetrics,
                                        custom_limits: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Validate performance against custom limits"""
        limits = custom_limits or {
            'max_execution_time_ms': self.max_execution_time_ms,
            'max_memory_mb': self.max_memory_mb,
            'max_cpu_percent': self.max_cpu_percent,
            'min_signals_per_second': self.min_signals_per_second
        }
        
        violations = []
        warnings = []
        
        # Check execution time
        if performance_metrics.average_execution_time_ms > limits['max_execution_time_ms']:
            violations.append(f"Average execution time {performance_metrics.average_execution_time_ms:.1f}ms exceeds limit {limits['max_execution_time_ms']}ms")
        
        # Check memory usage
        if performance_metrics.memory_peak_mb > limits['max_memory_mb']:
            violations.append(f"Peak memory usage {performance_metrics.memory_peak_mb:.1f}MB exceeds limit {limits['max_memory_mb']}MB")
        
        # Check CPU usage
        if performance_metrics.cpu_peak_percent > limits['max_cpu_percent']:
            violations.append(f"Peak CPU usage {performance_metrics.cpu_peak_percent:.1f}% exceeds limit {limits['max_cpu_percent']}%")
        
        # Check signal generation rate
        if performance_metrics.signals_per_second < limits['min_signals_per_second']:
            violations.append(f"Signal generation rate {performance_metrics.signals_per_second:.2f}/s below minimum {limits['min_signals_per_second']}/s")
        
        # Generate warnings for approaching limits
        if performance_metrics.average_execution_time_ms > limits['max_execution_time_ms'] * 0.8:
            warnings.append("Average execution time approaching limit")
        
        if performance_metrics.memory_peak_mb > limits['max_memory_mb'] * 0.8:
            warnings.append("Memory usage approaching limit")
        
        if performance_metrics.cpu_peak_percent > limits['max_cpu_percent'] * 0.8:
            warnings.append("CPU usage approaching limit")
        
        return {
            'within_limits': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'performance_score': performance_metrics.get_performance_score(),
            'efficiency_ratio': performance_metrics.get_efficiency_ratio()
        }
    
    async def benchmark_performance(self, performance_metrics: PerformanceMetrics,
                                  benchmark_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Benchmark performance against historical data"""
        if not benchmark_data:
            benchmark_data = {
                'previous_execution_time': 75.0,
                'previous_memory': 300.0,
                'previous_cpu': 45.0,
                'previous_signals_per_second': 4.0
            }
        
        # Calculate improvements
        execution_improvement = ((benchmark_data['previous_execution_time'] - performance_metrics.average_execution_time_ms) / 
                               benchmark_data['previous_execution_time']) * 100
        
        memory_improvement = ((benchmark_data['previous_memory'] - performance_metrics.memory_peak_mb) / 
                            benchmark_data['previous_memory']) * 100
        
        cpu_improvement = ((benchmark_data['previous_cpu'] - performance_metrics.cpu_peak_percent) / 
                         benchmark_data['previous_cpu']) * 100
        
        signals_improvement = ((performance_metrics.signals_per_second - benchmark_data['previous_signals_per_second']) / 
                             benchmark_data['previous_signals_per_second']) * 100
        
        return {
            'execution_time_improvement_percent': execution_improvement,
            'memory_improvement_percent': memory_improvement,
            'cpu_improvement_percent': cpu_improvement,
            'signals_per_second_improvement_percent': signals_improvement,
            'overall_improvement_percent': (execution_improvement + memory_improvement + cpu_improvement + signals_improvement) / 4,
            'benchmark_date': datetime.utcnow().isoformat()
        }
    
    async def get_performance_recommendations(self, performance_metrics: PerformanceMetrics) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        # Execution time recommendations
        if performance_metrics.average_execution_time_ms > 100:
            recommendations.append("Consider optimizing signal generation algorithms")
            recommendations.append("Review data processing efficiency")
        
        if performance_metrics.max_execution_time_ms > performance_metrics.average_execution_time_ms * 3:
            recommendations.append("Investigate signal generation outliers")
        
        # Memory recommendations
        if performance_metrics.memory_peak_mb > 512:
            recommendations.append("Consider implementing data streaming for large datasets")
            recommendations.append("Review memory usage in signal generation")
        
        if performance_metrics.memory_average_mb > performance_metrics.memory_peak_mb * 0.8:
            recommendations.append("Consider memory optimization and garbage collection")
        
        # CPU recommendations
        if performance_metrics.cpu_peak_percent > 70:
            recommendations.append("Consider parallel processing for signal generation")
            recommendations.append("Review computational complexity of algorithms")
        
        if performance_metrics.cpu_average_percent > 50:
            recommendations.append("Consider caching frequently used calculations")
        
        # Signal generation rate recommendations
        if performance_metrics.signals_per_second < 2:
            recommendations.append("Consider optimizing signal generation pipeline")
            recommendations.append("Review data preprocessing efficiency")
        
        # General recommendations
        if performance_metrics.get_efficiency_ratio() < 0.01:
            recommendations.append("Overall efficiency is low - consider comprehensive optimization")
        
        return recommendations











