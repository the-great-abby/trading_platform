"""
Batch validation service for executing multiple backtest scripts

This service coordinates the execution of multiple backtest scripts in parallel
and aggregates the results for comprehensive validation reporting.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
import logging
from datetime import datetime

from ..models.backtest_script import BacktestScript
from ..models.backtest_result import BacktestResult
from ..models.test_configuration import TestConfiguration
from ..validation.result_validator import ResultValidator
from .script_executor import ScriptExecutor

logger = logging.getLogger(__name__)


class BatchValidator:
    """
    Service for coordinating batch validation of multiple backtest scripts.
    """
    
    def __init__(self):
        self.script_executor = ScriptExecutor()
        self.result_validator = ResultValidator()
    
    def validate_batch(self, scripts: List[BacktestScript],
                      configuration: TestConfiguration,
                      max_parallel_jobs: int = 4,
                      progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[BacktestResult]:
        """
        Validate a batch of scripts.
        
        Args:
            scripts: List of BacktestScript objects to validate
            configuration: TestConfiguration with validation settings
            max_parallel_jobs: Maximum number of parallel executions
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of BacktestResult objects
            
        Raises:
            ValueError: If scripts list is empty or configuration is invalid
        """
        if not scripts:
            raise ValueError("Scripts list cannot be empty")
        
        if not configuration:
            raise ValueError("Configuration is required")
        
        logger.info(f"Starting batch validation of {len(scripts)} scripts")
        
        # Execute scripts in parallel
        results = self.script_executor.execute_scripts_parallel(
            scripts=scripts,
            max_parallel=max_parallel_jobs,
            parameters=configuration.parameters if hasattr(configuration, 'parameters') else None
        )
        
        # Validate results
        validated_results = []
        for i, (script, result) in enumerate(zip(scripts, results)):
            # Report progress
            if progress_callback:
                progress_callback(i + 1, len(scripts), script.name)
            
            # Validate the result
            validation_result = self.result_validator.validate_result(result, configuration)
            
            # Add validation errors to the result
            if validation_result.errors:
                for error in validation_result.errors:
                    result.add_validation_error(error.field, error.message, error.severity)
            
            # Add validation warnings
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    result.add_validation_error(warning.field, warning.message, warning.severity)
            
            validated_results.append(result)
            
            logger.debug(f"Validated script {script.name}: {result.status}")
        
        logger.info(f"Completed batch validation of {len(scripts)} scripts")
        return validated_results
    
    async def validate_batch_async(self, scripts: List[BacktestScript],
                                 configuration: TestConfiguration,
                                 max_parallel_jobs: int = 4,
                                 progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[BacktestResult]:
        """
        Validate a batch of scripts asynchronously.
        
        Args:
            scripts: List of BacktestScript objects to validate
            configuration: TestConfiguration with validation settings
            max_parallel_jobs: Maximum number of parallel executions
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of BacktestResult objects
        """
        if not scripts:
            raise ValueError("Scripts list cannot be empty")
        
        if not configuration:
            raise ValueError("Configuration is required")
        
        logger.info(f"Starting async batch validation of {len(scripts)} scripts")
        
        # Create semaphore to limit parallel execution
        semaphore = asyncio.Semaphore(max_parallel_jobs)
        
        async def validate_single_script(script: BacktestScript) -> BacktestResult:
            """Validate a single script with semaphore control."""
            async with semaphore:
                # Execute script
                result = await self.script_executor.execute_script_async(
                    script, 
                    parameters=configuration.parameters if hasattr(configuration, 'parameters') else None,
                    timeout_override=configuration.get_timeout_for_script_type(script.script_type)
                )
                
                # Validate result
                validation_result = self.result_validator.validate_result(result, configuration)
                
                # Add validation errors to the result
                if validation_result.errors:
                    for error in validation_result.errors:
                        result.add_validation_error(error.field, error.message, error.severity)
                
                # Add validation warnings
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        result.add_validation_error(warning.field, warning.message, warning.severity)
                
                return result
        
        # Execute all scripts
        tasks = [validate_single_script(script) for script in scripts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Script {scripts[i].name} failed: {result}")
                # Create error result
                error_result = BacktestResult(
                    script_id=scripts[i].id,
                    execution_id=f"error-{int(datetime.now().timestamp())}-{i}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration_seconds=0.0,
                    status="ERROR",
                    exit_code=1,
                    stdout="",
                    stderr=str(result),
                    validation_errors=[{
                        "field": "execution",
                        "message": str(result),
                        "severity": "ERROR"
                    }]
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
                
                # Report progress
                if progress_callback:
                    progress_callback(i + 1, len(scripts), scripts[i].name)
        
        logger.info(f"Completed async batch validation of {len(scripts)} scripts")
        return processed_results
    
    def validate_batch_with_retry(self, scripts: List[BacktestScript],
                                configuration: TestConfiguration,
                                max_parallel_jobs: int = 4,
                                max_retries: int = 2) -> List[BacktestResult]:
        """
        Validate a batch of scripts with retry logic for failed scripts.
        
        Args:
            scripts: List of BacktestScript objects to validate
            configuration: TestConfiguration with validation settings
            max_parallel_jobs: Maximum number of parallel executions
            max_retries: Maximum number of retry attempts for failed scripts
            
        Returns:
            List of BacktestResult objects
        """
        if not configuration.execution_settings.retry_failed_tests:
            return self.validate_batch(scripts, configuration, max_parallel_jobs)
        
        logger.info(f"Starting batch validation with retry logic (max {max_retries} retries)")
        
        # Initial validation
        results = self.validate_batch(scripts, configuration, max_parallel_jobs)
        
        # Retry failed scripts
        for retry_attempt in range(max_retries):
            failed_scripts = []
            failed_results = []
            
            # Identify failed scripts
            for script, result in zip(scripts, results):
                if result.status in ["FAILED", "ERROR", "TIMEOUT"]:
                    failed_scripts.append(script)
                    failed_results.append((script, result))
            
            if not failed_scripts:
                logger.info(f"All scripts passed after {retry_attempt} retries")
                break
            
            logger.info(f"Retry attempt {retry_attempt + 1}: retrying {len(failed_scripts)} failed scripts")
            
            # Retry failed scripts
            retry_results = self.validate_batch(failed_scripts, configuration, max_parallel_jobs)
            
            # Update results with retry outcomes
            for i, (script, result) in enumerate(failed_results):
                retry_result = retry_results[i]
                if retry_result.status == "SUCCESS":
                    # Replace failed result with successful retry
                    script_index = scripts.index(script)
                    results[script_index] = retry_result
                    logger.info(f"Script {script.name} succeeded on retry {retry_attempt + 1}")
                else:
                    logger.warning(f"Script {script.name} failed on retry {retry_attempt + 1}")
        
        return results
    
    def get_batch_summary(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """
        Generate a summary of batch validation results.
        
        Args:
            results: List of BacktestResult objects
            
        Returns:
            Dictionary with batch summary statistics
        """
        total_scripts = len(results)
        successful_scripts = sum(1 for r in results if r.status == "SUCCESS")
        failed_scripts = sum(1 for r in results if r.status == "FAILED")
        error_scripts = sum(1 for r in results if r.status in ["ERROR", "TIMEOUT"])
        
        total_execution_time = sum(r.duration_seconds for r in results)
        average_execution_time = total_execution_time / total_scripts if total_scripts > 0 else 0.0
        
        success_rate = successful_scripts / total_scripts if total_scripts > 0 else 0.0
        
        return {
            "total_scripts": total_scripts,
            "passed_scripts": successful_scripts,
            "failed_scripts": failed_scripts,
            "error_scripts": error_scripts,
            "success_rate": success_rate,
            "execution_time_seconds": total_execution_time,
            "average_execution_time_seconds": average_execution_time,
            "parallel_execution_enabled": True
        }
    
    def analyze_performance_trends(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """
        Analyze performance trends across batch results.
        
        Args:
            results: List of BacktestResult objects
            
        Returns:
            Dictionary with performance analysis
        """
        successful_results = [r for r in results if r.performance_metrics and r.status == "SUCCESS"]
        
        if not successful_results:
            return {
                "average_return": 0.0,
                "average_sharpe": 0.0,
                "average_drawdown": 0.0,
                "average_win_rate": 0.0,
                "performance_trends": {},
                "top_performers": [],
                "underperformers": []
            }
        
        # Calculate averages
        returns = [r.performance_metrics.total_return_pct for r in successful_results]
        sharpes = [r.performance_metrics.sharpe_ratio for r in successful_results]
        drawdowns = [r.performance_metrics.max_drawdown_pct for r in successful_results]
        win_rates = [r.performance_metrics.win_rate for r in successful_results]
        
        # Identify top and bottom performers
        sorted_by_return = sorted(successful_results, 
                                key=lambda r: r.performance_metrics.total_return_pct, 
                                reverse=True)
        
        top_performers = [r.script_id for r in sorted_by_return[:3]]
        underperformers = [r.script_id for r in sorted_by_return[-3:]]
        
        return {
            "average_return": sum(returns) / len(returns),
            "average_sharpe": sum(sharpes) / len(sharpes),
            "average_drawdown": sum(drawdowns) / len(drawdowns),
            "average_win_rate": sum(win_rates) / len(win_rates),
            "performance_trends": {
                "return_std": self._calculate_std(returns),
                "sharpe_std": self._calculate_std(sharpes),
                "drawdown_std": self._calculate_std(drawdowns),
                "win_rate_std": self._calculate_std(win_rates)
            },
            "top_performers": top_performers,
            "underperformers": underperformers
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5











