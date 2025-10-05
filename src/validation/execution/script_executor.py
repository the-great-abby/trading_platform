"""
Script execution service for running backtest scripts in isolation

This service executes backtest scripts in isolated environments to prevent
side effects and ensure reliable, consistent results.
"""

import asyncio
import subprocess
import tempfile
import json
import time
import psutil
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from ..models.backtest_script import BacktestScript
from ..models.backtest_result import BacktestResult, ExecutionStatus, PerformanceMetrics, ResourceUsage

logger = logging.getLogger(__name__)


class ScriptExecutor:
    """
    Service for executing backtest scripts in isolated environments.
    """
    
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.resource_monitors: Dict[str, psutil.Process] = {}
    
    def execute_script(self, script: BacktestScript, 
                      parameters: Optional[Dict[str, Any]] = None,
                      timeout_override: Optional[int] = None) -> BacktestResult:
        """
        Execute a backtest script synchronously.
        
        Args:
            script: BacktestScript to execute
            parameters: Optional parameters to pass to the script
            timeout_override: Override the script's timeout
            
        Returns:
            BacktestResult with execution details
            
        Raises:
            FileNotFoundError: If script file doesn't exist
            ValueError: If script is invalid for execution
        """
        if not script.is_valid_for_execution():
            raise ValueError(f"Script {script.name} is not valid for execution")
        
        script_path = Path(script.file_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script.file_path}")
        
        # Determine timeout
        timeout = timeout_override or script.get_timeout_for_type()
        
        logger.info(f"Executing script {script.name} with timeout {timeout}s")
        
        start_time = datetime.now()
        execution_id = script.execution_id if hasattr(script, 'execution_id') else f"exec-{int(time.time())}"
        
        try:
            # Execute script in isolated environment
            result = self._run_script_isolated(script, parameters, timeout, start_time, execution_id)
            
            # Parse results and create BacktestResult
            backtest_result = self._create_backtest_result(script, result, start_time, execution_id)
            
            logger.info(f"Script {script.name} executed successfully")
            return backtest_result
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Script {script.name} timed out after {timeout}s")
            return self._create_timeout_result(script, start_time, execution_id, timeout)
            
        except Exception as e:
            logger.error(f"Script {script.name} failed with error: {e}")
            return self._create_error_result(script, start_time, execution_id, str(e))
    
    async def execute_script_async(self, script: BacktestScript,
                                 parameters: Optional[Dict[str, Any]] = None,
                                 timeout_override: Optional[int] = None) -> BacktestResult:
        """
        Execute a backtest script asynchronously.
        
        Args:
            script: BacktestScript to execute
            parameters: Optional parameters to pass to the script
            timeout_override: Override the script's timeout
            
        Returns:
            BacktestResult with execution details
        """
        # Run synchronous execution in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.execute_script, 
            script, 
            parameters, 
            timeout_override
        )
    
    def execute_scripts_parallel(self, scripts: List[BacktestScript],
                               max_parallel: int = 4,
                               parameters: Optional[Dict[str, Any]] = None) -> List[BacktestResult]:
        """
        Execute multiple scripts in parallel.
        
        Args:
            scripts: List of BacktestScript objects to execute
            max_parallel: Maximum number of parallel executions
            parameters: Optional parameters to pass to scripts
            
        Returns:
            List of BacktestResult objects
        """
        logger.info(f"Executing {len(scripts)} scripts in parallel (max {max_parallel})")
        
        # Create semaphore to limit parallel execution
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(script: BacktestScript) -> BacktestResult:
            async with semaphore:
                return await self.execute_script_async(script, parameters)
        
        # Execute all scripts
        async def run_all():
            tasks = [execute_with_semaphore(script) for script in scripts]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(run_all())
        except RuntimeError:
            # Create new event loop if none exists
            results = asyncio.run(run_all())
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Script {scripts[i].name} failed: {result}")
                # Create error result
                error_result = self._create_error_result(
                    scripts[i], 
                    datetime.now(), 
                    f"exec-{int(time.time())}-{i}",
                    str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        logger.info(f"Completed parallel execution of {len(scripts)} scripts")
        return processed_results
    
    def _run_script_isolated(self, script: BacktestScript,
                           parameters: Optional[Dict[str, Any]],
                           timeout: int,
                           start_time: datetime,
                           execution_id: str) -> Dict[str, Any]:
        """
        Run script in isolated environment with resource monitoring.
        
        Args:
            script: Script to execute
            parameters: Optional parameters
            timeout: Execution timeout
            start_time: Start time
            execution_id: Execution identifier
            
        Returns:
            Dictionary with execution results
        """
        # Create temporary directory for script execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create parameter file if parameters provided
            param_file = None
            if parameters:
                param_file = temp_path / "parameters.json"
                param_file.write_text(json.dumps(parameters))
            
            # Prepare environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(script.file_path).parent)
            if param_file:
                env['VALIDATION_PARAMETERS'] = str(param_file)
            
            # Prepare command
            cmd = ['python', str(script.file_path)]
            
            # Start process with resource monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_path,
                env=env,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Monitor resources
            resource_monitor = psutil.Process(process.pid)
            peak_memory = 0.0
            cpu_samples = []
            
            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Collect final resource usage
                try:
                    memory_info = resource_monitor.memory_info()
                    peak_memory = memory_info.rss / 1024 / 1024  # Convert to MB
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                return {
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': process.returncode,
                    'peak_memory_mb': peak_memory,
                    'average_cpu_percent': sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
                    'success': process.returncode == 0
                }
                
            except subprocess.TimeoutExpired:
                # Terminate process and all children
                try:
                    os.killpg(os.getpgid(process.pid), 9)  # SIGKILL
                except ProcessLookupError:
                    pass
                raise
    
    def _create_backtest_result(self, script: BacktestScript,
                              execution_data: Dict[str, Any],
                              start_time: datetime,
                              execution_id: str) -> BacktestResult:
        """
        Create BacktestResult from execution data.
        
        Args:
            script: Executed script
            execution_data: Execution results
            start_time: Execution start time
            execution_id: Execution identifier
            
        Returns:
            BacktestResult object
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Determine status
        if execution_data['success']:
            status = ExecutionStatus.SUCCESS
        else:
            status = ExecutionStatus.FAILED
        
        # Parse performance metrics from stdout
        performance_metrics = None
        if execution_data['success'] and execution_data['stdout']:
            try:
                # Try to parse JSON from stdout
                metrics_data = json.loads(execution_data['stdout'].strip())
                performance_metrics = PerformanceMetrics(**metrics_data)
            except (json.JSONDecodeError, TypeError, ValueError):
                # Try to extract metrics from text output
                performance_metrics = self._extract_metrics_from_text(execution_data['stdout'])
        
        # Create resource usage
        resource_usage = ResourceUsage(
            peak_memory_mb=execution_data['peak_memory_mb'],
            average_cpu_percent=execution_data['average_cpu_percent']
        )
        
        return BacktestResult(
            script_id=script.id,
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            status=status,
            exit_code=execution_data['exit_code'],
            stdout=execution_data['stdout'],
            stderr=execution_data['stderr'],
            performance_metrics=performance_metrics,
            resource_usage=resource_usage
        )
    
    def _create_timeout_result(self, script: BacktestScript,
                             start_time: datetime,
                             execution_id: str,
                             timeout: int) -> BacktestResult:
        """Create BacktestResult for timeout scenario."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return BacktestResult(
            script_id=script.id,
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            status=ExecutionStatus.TIMEOUT,
            exit_code=-1,
            stdout="",
            stderr=f"Script execution timed out after {timeout} seconds",
            validation_errors=[{
                "field": "execution",
                "message": "Script execution timeout",
                "severity": "ERROR"
            }]
        )
    
    def _create_error_result(self, script: BacktestScript,
                           start_time: datetime,
                           execution_id: str,
                           error_message: str) -> BacktestResult:
        """Create BacktestResult for error scenario."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return BacktestResult(
            script_id=script.id,
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            status=ExecutionStatus.ERROR,
            exit_code=1,
            stdout="",
            stderr=error_message,
            validation_errors=[{
                "field": "execution",
                "message": error_message,
                "severity": "ERROR"
            }]
        )
    
    def _extract_metrics_from_text(self, stdout: str) -> Optional[PerformanceMetrics]:
        """
        Extract performance metrics from text output.
        
        Args:
            stdout: Standard output from script
            
        Returns:
            PerformanceMetrics object or None
        """
        try:
            # Look for common metric patterns in text
            metrics = {}
            
            # Extract return percentage
            return_match = re.search(r'return[:\s]+([0-9.-]+)%?', stdout, re.IGNORECASE)
            if return_match:
                metrics['total_return_pct'] = float(return_match.group(1))
            
            # Extract Sharpe ratio
            sharpe_match = re.search(r'sharpe[:\s]+([0-9.-]+)', stdout, re.IGNORECASE)
            if sharpe_match:
                metrics['sharpe_ratio'] = float(sharpe_match.group(1))
            
            # Extract drawdown
            drawdown_match = re.search(r'drawdown[:\s]+([0-9.-]+)%?', stdout, re.IGNORECASE)
            if drawdown_match:
                metrics['max_drawdown_pct'] = float(drawdown_match.group(1))
            
            # Extract win rate
            winrate_match = re.search(r'win\s*rate[:\s]+([0-9.-]+)%?', stdout, re.IGNORECASE)
            if winrate_match:
                metrics['win_rate'] = float(winrate_match.group(1)) / 100.0  # Convert to decimal
            
            # Extract trade count
            trades_match = re.search(r'trades?[:\s]+([0-9]+)', stdout, re.IGNORECASE)
            if trades_match:
                metrics['total_trades'] = int(trades_match.group(1))
            
            # Set defaults for missing metrics
            metrics.setdefault('total_return_pct', 0.0)
            metrics.setdefault('sharpe_ratio', 0.0)
            metrics.setdefault('max_drawdown_pct', 0.0)
            metrics.setdefault('win_rate', 0.0)
            metrics.setdefault('total_trades', 0)
            metrics.setdefault('initial_capital', 10000.0)
            metrics.setdefault('final_capital', 10000.0)
            
            return PerformanceMetrics(**metrics)
            
        except Exception as e:
            logger.debug(f"Failed to extract metrics from text: {e}")
            return None
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running script execution.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            True if cancellation was successful
        """
        if execution_id in self.active_processes:
            process = self.active_processes[execution_id]
            try:
                process.terminate()
                process.wait(timeout=5)
                del self.active_processes[execution_id]
                logger.info(f"Cancelled execution {execution_id}")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                del self.active_processes[execution_id]
                logger.warning(f"Force killed execution {execution_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel execution {execution_id}: {e}")
                return False
        return False
    
    def get_active_executions(self) -> List[str]:
        """
        Get list of active execution IDs.
        
        Returns:
            List of active execution identifiers
        """
        return list(self.active_processes.keys())
