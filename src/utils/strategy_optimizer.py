"""
Strategy Performance Optimizer
Automated strategy optimization and performance tuning
"""

import asyncio
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial
import psutil
import gc

logger = logging.getLogger(__name__)


@dataclass
class StrategyProfile:
    """Strategy performance profile"""
    strategy_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    complexity_score: float
    optimization_potential: float
    bottlenecks: List[str]
    recommendations: List[str]


@dataclass
class OptimizationResult:
    """Strategy optimization result"""
    original_performance: float
    optimized_performance: float
    improvement_percent: float
    parameter_changes: Dict[str, Any]
    execution_time_reduction: float
    memory_reduction_mb: float


class StrategyOptimizer:
    """Advanced strategy optimization system"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.strategy_profiles: Dict[str, StrategyProfile] = {}
        self.optimization_history: List[OptimizationResult] = []
        
        # Performance thresholds
        self.slow_execution_threshold = 5.0  # seconds
        self.high_memory_threshold = 500.0  # MB
        self.high_cpu_threshold = 80.0  # percent
        
        # Optimization strategies
        self.optimization_strategies = {
            'parameter_tuning': self._optimize_parameters,
            'algorithm_optimization': self._optimize_algorithm,
            'memory_optimization': self._optimize_memory,
            'parallelization': self._optimize_parallelization,
            'caching': self._optimize_caching
        }
    
    async def profile_strategy(self, strategy_func: Callable, 
                             strategy_name: str, 
                             test_data: pd.DataFrame) -> StrategyProfile:
        """Profile a strategy's performance"""
        
        logger.info(f"📊 Profiling strategy: {strategy_name}")
        
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_cpu = process.cpu_percent()
        
        # Measure execution time
        start_time = time.time()
        start_cpu = time.time()
        
        try:
            # Execute strategy
            result = await strategy_func(test_data)
            
            execution_time = time.time() - start_time
            cpu_time = time.time() - start_cpu
            
            # Measure resource usage
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_usage = final_memory - initial_memory
            cpu_usage = process.cpu_percent(interval=0.1)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(strategy_func, test_data)
            
            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(execution_time, memory_usage, cpu_usage)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(bottlenecks, complexity_score)
            
            # Calculate optimization potential
            optimization_potential = self._calculate_optimization_potential(
                execution_time, memory_usage, cpu_usage, complexity_score
            )
            
            profile = StrategyProfile(
                strategy_name=strategy_name,
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                complexity_score=complexity_score,
                optimization_potential=optimization_potential,
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )
            
            self.strategy_profiles[strategy_name] = profile
            
            logger.info(f"✅ Strategy profiling completed: {strategy_name}")
            logger.info(f"   Execution time: {execution_time:.2f}s")
            logger.info(f"   Memory usage: {memory_usage:.1f}MB")
            logger.info(f"   CPU usage: {cpu_usage:.1f}%")
            logger.info(f"   Optimization potential: {optimization_potential:.1f}%")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Strategy profiling failed: {strategy_name} - {e}")
            raise
    
    def _calculate_complexity_score(self, strategy_func: Callable, test_data: pd.DataFrame) -> float:
        """Calculate strategy complexity score"""
        score = 0.0
        
        # Analyze function source code (simplified)
        func_source = strategy_func.__code__
        
        # Count operations
        score += func_source.co_argcount * 0.1  # More parameters = more complex
        score += len(func_source.co_names) * 0.05  # More names = more complex
        score += func_source.co_nlocals * 0.1  # More locals = more complex
        
        # Data size factor
        data_size_factor = len(test_data) / 1000  # Normalize to 1000 rows
        score += min(data_size_factor * 0.5, 2.0)  # Cap at 2.0
        
        # Strategy type complexity
        strategy_name = strategy_func.__name__.lower()
        if 'neural' in strategy_name or 'ml' in strategy_name:
            score += 3.0
        elif 'advanced' in strategy_name or 'complex' in strategy_name:
            score += 2.0
        elif 'simple' in strategy_name or 'basic' in strategy_name:
            score += 0.5
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _identify_bottlenecks(self, execution_time: float, memory_usage: float, 
                             cpu_usage: float) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if execution_time > self.slow_execution_threshold:
            bottlenecks.append("slow_execution")
        
        if memory_usage > self.high_memory_threshold:
            bottlenecks.append("high_memory_usage")
        
        if cpu_usage > self.high_cpu_threshold:
            bottlenecks.append("high_cpu_usage")
        
        if execution_time > 10.0:
            bottlenecks.append("very_slow_execution")
        
        if memory_usage > 1000.0:
            bottlenecks.append("excessive_memory_usage")
        
        return bottlenecks
    
    def _generate_recommendations(self, bottlenecks: List[str], complexity_score: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if "slow_execution" in bottlenecks:
            recommendations.append("Consider parameter tuning for faster execution")
            recommendations.append("Implement caching for repeated calculations")
            recommendations.append("Use vectorized operations instead of loops")
        
        if "high_memory_usage" in bottlenecks:
            recommendations.append("Optimize data structures to reduce memory footprint")
            recommendations.append("Use generators instead of lists for large datasets")
            recommendations.append("Implement data streaming for large datasets")
        
        if "high_cpu_usage" in bottlenecks:
            recommendations.append("Consider parallelization for CPU-intensive operations")
            recommendations.append("Optimize algorithm complexity")
            recommendations.append("Use more efficient data structures")
        
        if complexity_score > 7.0:
            recommendations.append("Consider breaking down complex strategy into smaller functions")
            recommendations.append("Implement early termination for expensive calculations")
            recommendations.append("Use approximation algorithms for complex calculations")
        
        if not bottlenecks:
            recommendations.append("Strategy performance is good - no optimizations needed")
        
        return recommendations
    
    def _calculate_optimization_potential(self, execution_time: float, memory_usage: float,
                                        cpu_usage: float, complexity_score: float) -> float:
        """Calculate optimization potential percentage"""
        potential = 0.0
        
        # Execution time potential
        if execution_time > self.slow_execution_threshold:
            potential += min((execution_time - self.slow_execution_threshold) / execution_time * 100, 50)
        
        # Memory usage potential
        if memory_usage > self.high_memory_threshold:
            potential += min((memory_usage - self.high_memory_threshold) / memory_usage * 100, 30)
        
        # CPU usage potential
        if cpu_usage > self.high_cpu_threshold:
            potential += min((cpu_usage - self.high_cpu_threshold) / cpu_usage * 100, 20)
        
        # Complexity potential
        if complexity_score > 5.0:
            potential += min((complexity_score - 5.0) / complexity_score * 100, 25)
        
        return min(potential, 100.0)
    
    async def optimize_strategy(self, strategy_func: Callable, strategy_name: str,
                              test_data: pd.DataFrame) -> OptimizationResult:
        """Optimize a strategy's performance"""
        
        logger.info(f"🚀 Optimizing strategy: {strategy_name}")
        
        # Get original profile
        original_profile = await self.profile_strategy(strategy_func, strategy_name, test_data)
        
        # Apply optimizations
        optimized_func = await self._apply_optimizations(strategy_func, original_profile)
        
        # Profile optimized version
        optimized_profile = await self.profile_strategy(optimized_func, f"{strategy_name}_optimized", test_data)
        
        # Calculate improvements
        execution_improvement = ((original_profile.execution_time - optimized_profile.execution_time) / 
                               original_profile.execution_time) * 100
        memory_improvement = ((original_profile.memory_usage_mb - optimized_profile.memory_usage_mb) / 
                            original_profile.memory_usage_mb) * 100 if original_profile.memory_usage_mb > 0 else 0
        
        result = OptimizationResult(
            original_performance=original_profile.execution_time,
            optimized_performance=optimized_profile.execution_time,
            improvement_percent=execution_improvement,
            parameter_changes={},  # Would track actual parameter changes
            execution_time_reduction=original_profile.execution_time - optimized_profile.execution_time,
            memory_reduction_mb=original_profile.memory_usage_mb - optimized_profile.memory_usage_mb
        )
        
        self.optimization_history.append(result)
        
        logger.info(f"✅ Strategy optimization completed: {strategy_name}")
        logger.info(f"   Execution time improvement: {execution_improvement:.1f}%")
        logger.info(f"   Memory reduction: {result.memory_reduction_mb:.1f}MB")
        
        return result
    
    async def _apply_optimizations(self, strategy_func: Callable, 
                                 profile: StrategyProfile) -> Callable:
        """Apply optimizations to strategy function"""
        
        optimized_func = strategy_func
        
        # Apply optimizations based on bottlenecks
        for bottleneck in profile.bottlenecks:
            if bottleneck in self.optimization_strategies:
                try:
                    optimized_func = await self.optimization_strategies[bottleneck](optimized_func, profile)
                    logger.info(f"🔧 Applied {bottleneck} optimization")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to apply {bottleneck} optimization: {e}")
        
        return optimized_func
    
    async def _optimize_parameters(self, strategy_func: Callable, 
                                 profile: StrategyProfile) -> Callable:
        """Optimize strategy parameters for better performance"""
        
        # Create parameter-optimized version
        def optimized_strategy(data: pd.DataFrame):
            # Apply parameter optimizations
            # This is a simplified example - in practice you'd use hyperparameter optimization
            
            # Example: Reduce lookback periods for faster execution
            if hasattr(strategy_func, 'lookback_period'):
                original_lookback = strategy_func.lookback_period
                strategy_func.lookback_period = min(original_lookback, 20)  # Cap at 20
            
            # Example: Use simpler indicators
            if hasattr(strategy_func, 'use_complex_indicators'):
                strategy_func.use_complex_indicators = False
            
            return strategy_func(data)
        
        return optimized_strategy
    
    async def _optimize_algorithm(self, strategy_func: Callable, 
                                profile: StrategyProfile) -> Callable:
        """Optimize algorithm implementation"""
        
        def optimized_strategy(data: pd.DataFrame):
            # Use vectorized operations where possible
            # This is a simplified example
            
            # Example: Use pandas vectorized operations instead of loops
            if 'for' in strategy_func.__code__.co_names:
                # Replace loops with vectorized operations
                pass
            
            return strategy_func(data)
        
        return optimized_strategy
    
    async def _optimize_memory(self, strategy_func: Callable, 
                             profile: StrategyProfile) -> Callable:
        """Optimize memory usage"""
        
        def optimized_strategy(data: pd.DataFrame):
            # Implement memory optimizations
            
            # Example: Use generators for large datasets
            if len(data) > 10000:
                # Process data in chunks
                chunk_size = 1000
                results = []
                for i in range(0, len(data), chunk_size):
                    chunk = data.iloc[i:i+chunk_size]
                    chunk_result = strategy_func(chunk)
                    results.append(chunk_result)
                
                # Combine results
                return pd.concat(results) if results else None
            
            return strategy_func(data)
        
        return optimized_strategy
    
    async def _optimize_parallelization(self, strategy_func: Callable, 
                                      profile: StrategyProfile) -> Callable:
        """Optimize for parallel execution"""
        
        def optimized_strategy(data: pd.DataFrame):
            # Implement parallel processing for CPU-intensive operations
            
            # Example: Parallel processing for large datasets
            if len(data) > 5000 and profile.cpu_usage_percent > 50:
                # Split data for parallel processing
                num_workers = min(mp.cpu_count(), 4)
                chunk_size = len(data) // num_workers
                
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = []
                    for i in range(num_workers):
                        start_idx = i * chunk_size
                        end_idx = start_idx + chunk_size if i < num_workers - 1 else len(data)
                        chunk = data.iloc[start_idx:end_idx]
                        future = executor.submit(strategy_func, chunk)
                        futures.append(future)
                    
                    # Collect results
                    results = [future.result() for future in futures]
                    return pd.concat(results) if results else None
            
            return strategy_func(data)
        
        return optimized_strategy
    
    async def _optimize_caching(self, strategy_func: Callable, 
                               profile: StrategyProfile) -> Callable:
        """Optimize with caching"""
        
        # Simple cache for repeated calculations
        cache = {}
        
        def optimized_strategy(data: pd.DataFrame):
            # Use caching for expensive calculations
            
            # Create cache key based on data hash
            data_hash = hash(str(data.iloc[-100:].values.tobytes()))  # Last 100 rows
            
            if data_hash in cache:
                return cache[data_hash]
            
            # Execute strategy
            result = strategy_func(data)
            
            # Cache result
            cache[data_hash] = result
            
            # Limit cache size
            if len(cache) > 100:
                # Remove oldest entries
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            
            return result
        
        return optimized_strategy
    
    async def batch_optimize_strategies(self, strategies: Dict[str, Callable], 
                                      test_data: pd.DataFrame) -> Dict[str, OptimizationResult]:
        """Optimize multiple strategies in batch"""
        
        logger.info(f"🚀 Starting batch optimization of {len(strategies)} strategies")
        
        results = {}
        
        # Profile all strategies first
        profiles = {}
        for name, strategy in strategies.items():
            try:
                profile = await self.profile_strategy(strategy, name, test_data)
                profiles[name] = profile
            except Exception as e:
                logger.error(f"❌ Failed to profile {name}: {e}")
        
        # Sort by optimization potential
        sorted_strategies = sorted(profiles.items(), 
                                 key=lambda x: x[1].optimization_potential, 
                                 reverse=True)
        
        # Optimize strategies with highest potential first
        for name, profile in sorted_strategies:
            if profile.optimization_potential > 10:  # Only optimize if significant potential
                try:
                    strategy = strategies[name]
                    result = await self.optimize_strategy(strategy, name, test_data)
                    results[name] = result
                except Exception as e:
                    logger.error(f"❌ Failed to optimize {name}: {e}")
        
        logger.info(f"✅ Batch optimization completed: {len(results)} strategies optimized")
        
        return results
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate optimization report"""
        
        if not self.optimization_history:
            return {"message": "No optimization history available"}
        
        # Calculate statistics
        improvements = [r.improvement_percent for r in self.optimization_history]
        time_reductions = [r.execution_time_reduction for r in self.optimization_history]
        memory_reductions = [r.memory_reduction_mb for r in self.optimization_history]
        
        return {
            "total_optimizations": len(self.optimization_history),
            "average_improvement_percent": np.mean(improvements),
            "max_improvement_percent": np.max(improvements),
            "average_time_reduction": np.mean(time_reductions),
            "total_time_saved": np.sum(time_reductions),
            "average_memory_reduction_mb": np.mean(memory_reductions),
            "total_memory_saved_mb": np.sum(memory_reductions),
            "optimization_success_rate": len([r for r in self.optimization_history if r.improvement_percent > 0]) / len(self.optimization_history)
        }


# Global strategy optimizer instance
strategy_optimizer = StrategyOptimizer()


async def get_strategy_optimizer() -> StrategyOptimizer:
    """Get the global strategy optimizer instance"""
    return strategy_optimizer


async def optimize_trading_strategies():
    """Optimize all trading strategies"""
    optimizer = await get_strategy_optimizer()
    
    # Import strategies
    from src.strategies.momentum.macd_strategy import MACDStrategy
    from src.strategies.momentum.rsi_strategy import RSIStrategy
    from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
    
    # Create test data
    test_data = pd.DataFrame({
        'close': np.random.randn(1000).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 1000)
    })
    
    # Define strategies to optimize
    strategies = {
        'MACD': MACDStrategy().generate_signals,
        'RSI': RSIStrategy().generate_signals,
        'BollingerBands': BollingerBandsStrategy().generate_signals
    }
    
    # Run batch optimization
    results = await optimizer.batch_optimize_strategies(strategies, test_data)
    
    # Generate report
    report = optimizer.get_optimization_report()
    
    logger.info("📊 Strategy optimization report:")
    logger.info(f"   Total optimizations: {report['total_optimizations']}")
    logger.info(f"   Average improvement: {report['average_improvement_percent']:.1f}%")
    logger.info(f"   Total time saved: {report['total_time_saved']:.2f}s")
    logger.info(f"   Total memory saved: {report['total_memory_saved_mb']:.1f}MB")
    
    return results 