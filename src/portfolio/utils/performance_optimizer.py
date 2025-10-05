#!/usr/bin/env python3
"""
Performance optimization utilities for portfolio management system
"""
import time
import functools
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    function_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None


class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.cache = {}
        self.performance_metrics = []
        self.optimization_enabled = True
    
    def measure_performance(self, func: Callable) -> Callable:
        """Decorator to measure function performance"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.optimization_enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                metrics = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=end_time - start_time,
                    memory_usage=end_memory - start_memory,
                    input_size=self._estimate_input_size(args, kwargs),
                    output_size=self._estimate_output_size(result)
                )
                
                self.performance_metrics.append(metrics)
                
                if metrics.execution_time > 1.0:  # Log slow functions
                    logger.warning(f"Slow function {func.__name__}: {metrics.execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                end_time = time.time()
                metrics = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=end_time - start_time
                )
                self.performance_metrics.append(metrics)
                raise e
        
        return wrapper
    
    def cache_result(self, max_size: int = 1000, ttl: float = 3600) -> Callable:
        """Decorator to cache function results"""
        def decorator(func: Callable) -> Callable:
            cache_key_prefix = f"{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Create cache key
                cache_key = self._create_cache_key(cache_key_prefix, args, kwargs)
                
                # Check cache
                if cache_key in self.cache:
                    cached_result, timestamp = self.cache[cache_key]
                    if time.time() - timestamp < ttl:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached_result
                    else:
                        # Remove expired entry
                        del self.cache[cache_key]
                
                # Cache miss - compute result
                result = func(*args, **kwargs)
                
                # Store in cache
                if len(self.cache) < max_size:
                    self.cache[cache_key] = (result, time.time())
                    logger.debug(f"Cache miss for {func.__name__} - result cached")
                
                return result
            
            return wrapper
        return decorator
    
    def parallel_execution(self, max_workers: Optional[int] = None, use_processes: bool = False) -> Callable:
        """Decorator for parallel execution of independent operations"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Check if function supports parallel execution
                if not hasattr(func, '_parallel_execution'):
                    return func(*args, **kwargs)
                
                # Extract parallelizable data
                parallel_data = func._parallel_execution(*args, **kwargs)
                if not parallel_data:
                    return func(*args, **kwargs)
                
                # Execute in parallel
                if use_processes:
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        results = list(executor.map(func, parallel_data))
                else:
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        results = list(executor.map(func, parallel_data))
                
                # Combine results
                return self._combine_parallel_results(results)
            
            return wrapper
        return decorator
    
    def optimize_numpy_operations(self) -> Callable:
        """Decorator to optimize NumPy operations"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Pre-optimize NumPy arrays
                optimized_args = []
                for arg in args:
                    if isinstance(arg, np.ndarray):
                        optimized_args.append(self._optimize_numpy_array(arg))
                    else:
                        optimized_args.append(arg)
                
                # Call function with optimized arguments
                return func(*optimized_args, **kwargs)
            
            return wrapper
        return decorator
    
    def batch_operations(self, batch_size: int = 1000) -> Callable:
        """Decorator to batch large operations"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Check if first argument is a large array/list
                if args and hasattr(args[0], '__len__') and len(args[0]) > batch_size:
                    return self._execute_batched(func, args, kwargs, batch_size)
                else:
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _create_cache_key(self, prefix: str, args: tuple, kwargs: dict) -> str:
        """Create cache key from function arguments"""
        # Convert args and kwargs to hashable format
        key_data = (prefix, args, tuple(sorted(kwargs.items())))
        return str(hash(key_data))
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _estimate_input_size(self, args: tuple, kwargs: dict) -> int:
        """Estimate input data size"""
        total_size = 0
        
        for arg in args:
            if hasattr(arg, '__len__'):
                total_size += len(arg)
            elif isinstance(arg, (np.ndarray, pd.DataFrame)):
                total_size += arg.size
        
        for value in kwargs.values():
            if hasattr(value, '__len__'):
                total_size += len(value)
            elif isinstance(value, (np.ndarray, pd.DataFrame)):
                total_size += value.size
        
        return total_size
    
    def _estimate_output_size(self, result: Any) -> int:
        """Estimate output data size"""
        if hasattr(result, '__len__'):
            return len(result)
        elif isinstance(result, (np.ndarray, pd.DataFrame)):
            return result.size
        else:
            return 1
    
    def _optimize_numpy_array(self, arr: np.ndarray) -> np.ndarray:
        """Optimize NumPy array for better performance"""
        # Ensure contiguous memory layout
        if not arr.flags.c_contiguous:
            arr = np.ascontiguousarray(arr)
        
        # Use appropriate dtype
        if arr.dtype == np.float64 and arr.max() < 3.4e38 and arr.min() > -3.4e38:
            arr = arr.astype(np.float32)
        
        return arr
    
    def _execute_batched(self, func: Callable, args: tuple, kwargs: dict, batch_size: int) -> Any:
        """Execute function in batches"""
        large_array = args[0]
        results = []
        
        for i in range(0, len(large_array), batch_size):
            batch = large_array[i:i + batch_size]
            batch_args = (batch,) + args[1:]
            batch_result = func(*batch_args, **kwargs)
            results.append(batch_result)
        
        return self._combine_batch_results(results)
    
    def _combine_parallel_results(self, results: List[Any]) -> Any:
        """Combine results from parallel execution"""
        if not results:
            return None
        
        if isinstance(results[0], np.ndarray):
            return np.concatenate(results)
        elif isinstance(results[0], (list, tuple)):
            combined = []
            for result in results:
                combined.extend(result)
            return combined
        else:
            return results
    
    def _combine_batch_results(self, results: List[Any]) -> Any:
        """Combine results from batched execution"""
        return self._combine_parallel_results(results)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance optimization report"""
        if not self.performance_metrics:
            return {"message": "No performance data available"}
        
        # Calculate statistics
        execution_times = [m.execution_time for m in self.performance_metrics]
        memory_usage = [m.memory_usage for m in self.performance_metrics if m.memory_usage is not None]
        
        report = {
            "total_functions_called": len(self.performance_metrics),
            "total_execution_time": sum(execution_times),
            "average_execution_time": np.mean(execution_times),
            "median_execution_time": np.median(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "cache_size": len(self.cache),
            "functions_by_performance": self._get_functions_by_performance(),
            "optimization_recommendations": self._get_optimization_recommendations()
        }
        
        if memory_usage:
            report.update({
                "total_memory_usage": sum(memory_usage),
                "average_memory_usage": np.mean(memory_usage),
                "max_memory_usage": max(memory_usage)
            })
        
        return report
    
    def _get_functions_by_performance(self) -> List[Dict[str, Any]]:
        """Get functions sorted by performance"""
        function_stats = {}
        
        for metric in self.performance_metrics:
            func_name = metric.function_name
            if func_name not in function_stats:
                function_stats[func_name] = {
                    "call_count": 0,
                    "total_time": 0.0,
                    "max_time": 0.0,
                    "min_time": float('inf')
                }
            
            stats = function_stats[func_name]
            stats["call_count"] += 1
            stats["total_time"] += metric.execution_time
            stats["max_time"] = max(stats["max_time"], metric.execution_time)
            stats["min_time"] = min(stats["min_time"], metric.execution_time)
        
        # Calculate averages and sort by total time
        for stats in function_stats.values():
            stats["average_time"] = stats["total_time"] / stats["call_count"]
            if stats["min_time"] == float('inf'):
                stats["min_time"] = 0.0
        
        sorted_functions = sorted(
            function_stats.items(),
            key=lambda x: x[1]["total_time"],
            reverse=True
        )
        
        return [
            {"function": name, **stats}
            for name, stats in sorted_functions
        ]
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on performance data"""
        recommendations = []
        
        # Analyze slow functions
        slow_functions = [
            m for m in self.performance_metrics
            if m.execution_time > 1.0
        ]
        
        if slow_functions:
            recommendations.append(
                f"Consider optimizing {len(slow_functions)} slow functions "
                f"(execution time > 1.0s)"
            )
        
        # Analyze cache usage
        cache_utilization = len(self.cache) / 1000.0  # Assuming max cache size of 1000
        if cache_utilization > 0.8:
            recommendations.append("Cache utilization is high - consider increasing cache size")
        
        # Analyze memory usage
        high_memory_functions = [
            m for m in self.performance_metrics
            if m.memory_usage and m.memory_usage > 100.0  # > 100MB
        ]
        
        if high_memory_functions:
            recommendations.append(
                f"Consider memory optimization for {len(high_memory_functions)} "
                "memory-intensive functions"
            )
        
        return recommendations
    
    def clear_cache(self):
        """Clear performance cache"""
        self.cache.clear()
        logger.info("Performance cache cleared")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics.clear()
        logger.info("Performance metrics reset")
    
    def enable_optimization(self):
        """Enable performance optimizations"""
        self.optimization_enabled = True
        logger.info("Performance optimization enabled")
    
    def disable_optimization(self):
        """Disable performance optimizations"""
        self.optimization_enabled = False
        logger.info("Performance optimization disabled")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


# Convenience decorators
def measure_performance(func: Callable) -> Callable:
    """Measure function performance"""
    return performance_optimizer.measure_performance(func)


def cache_result(max_size: int = 1000, ttl: float = 3600) -> Callable:
    """Cache function results"""
    return performance_optimizer.cache_result(max_size, ttl)


def parallel_execution(max_workers: Optional[int] = None, use_processes: bool = False) -> Callable:
    """Enable parallel execution"""
    return performance_optimizer.parallel_execution(max_workers, use_processes)


def optimize_numpy_operations(func: Callable) -> Callable:
    """Optimize NumPy operations"""
    return performance_optimizer.optimize_numpy_operations()(func)


def batch_operations(batch_size: int = 1000) -> Callable:
    """Batch large operations"""
    return performance_optimizer.batch_operations(batch_size)


# Utility functions for common optimizations
def optimize_covariance_calculation(returns: np.ndarray) -> np.ndarray:
    """Optimize covariance matrix calculation"""
    # Use optimized NumPy operations
    returns = np.ascontiguousarray(returns)
    
    # Remove NaN values efficiently
    returns = returns[~np.isnan(returns).any(axis=1)]
    
    # Calculate covariance with optimized settings
    cov_matrix = np.cov(returns.T, ddof=1)
    
    # Ensure positive semi-definite
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    eigenvalues = np.maximum(eigenvalues, 1e-8)  # Ensure positive eigenvalues
    cov_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    return cov_matrix


def optimize_portfolio_weights(weights: np.ndarray, constraints: Dict[str, Any]) -> np.ndarray:
    """Optimize portfolio weights for performance"""
    weights = np.ascontiguousarray(weights)
    
    # Apply constraints efficiently
    if "max_single_asset_weight" in constraints:
        max_weight = constraints["max_single_asset_weight"]
        weights = np.minimum(weights, max_weight)
    
    if "min_single_asset_weight" in constraints:
        min_weight = constraints["min_single_asset_weight"]
        weights = np.maximum(weights, min_weight)
    
    # Normalize weights
    weights = weights / np.sum(weights)
    
    return weights


def optimize_matrix_operations(matrix1: np.ndarray, matrix2: np.ndarray, operation: str = "multiply") -> np.ndarray:
    """Optimize matrix operations"""
    # Ensure contiguous memory layout
    matrix1 = np.ascontiguousarray(matrix1)
    matrix2 = np.ascontiguousarray(matrix2)
    
    if operation == "multiply":
        return np.dot(matrix1, matrix2)
    elif operation == "add":
        return np.add(matrix1, matrix2)
    elif operation == "subtract":
        return np.subtract(matrix1, matrix2)
    else:
        raise ValueError(f"Unsupported operation: {operation}")


def get_performance_report() -> Dict[str, Any]:
    """Get performance optimization report"""
    return performance_optimizer.get_performance_report()


def clear_performance_cache():
    """Clear performance cache"""
    performance_optimizer.clear_cache()


def reset_performance_metrics():
    """Reset performance metrics"""
    performance_optimizer.reset_metrics()












