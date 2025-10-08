"""
Integration Tests for Script Execution Service

Tests the isolated execution of backtest scripts with proper environment
isolation and resource management.
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path
from typing import Dict, Any
import json

# This will fail until implementation is complete
from src.validation.execution.script_executor import ScriptExecutor
from src.validation.models.backtest_result import BacktestResult
from src.validation.models.backtest_script import BacktestScript


class TestScriptExecutionIntegration:
    """Integration tests for script execution"""
    
    @pytest.fixture
    def test_script(self):
        """Create a test backtest script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Test backtest script for execution testing
"""
import sys
import json
import time
import random

def run_backtest():
    """Run a test backtest"""
    # Simulate some processing time
    time.sleep(0.1)
    
    # Simulate backtest results
    results = {
        "total_return_pct": 15.5,
        "sharpe_ratio": 1.25,
        "max_drawdown_pct": 5.2,
        "win_rate": 0.65,
        "total_trades": 120,
        "initial_capital": 10000.0,
        "final_capital": 11550.0,
        "trade_data": [
            {"symbol": "AAPL", "action": "BUY", "price": 150.0, "quantity": 100},
            {"symbol": "AAPL", "action": "SELL", "price": 155.0, "quantity": 100}
        ]
    }
    
    # Print results as JSON (standard output)
    print(json.dumps(results))
    
    return results

if __name__ == "__main__":
    try:
        result = run_backtest()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
''')
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        temp_path.unlink()
    
    @pytest.fixture
    def failing_script(self):
        """Create a failing test script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Failing backtest script for error testing
"""
import sys

def run_backtest():
    """Run a failing backtest"""
    raise ValueError("Simulated backtest failure")

if __name__ == "__main__":
    try:
        run_backtest()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
''')
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        temp_path.unlink()
    
    @pytest.fixture
    def timeout_script(self):
        """Create a script that times out"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Timeout test script
"""
import time
import sys

def run_backtest():
    """Run a backtest that takes too long"""
    time.sleep(10)  # Sleep for 10 seconds
    return {"total_return": 0.1}

if __name__ == "__main__":
    run_backtest()
''')
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        temp_path.unlink()
    
    def test_execute_script_success(self, test_script):
        """Test successful script execution"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="test-script-1",
            name="test_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify result structure
        assert isinstance(result, BacktestResult)
        assert result.script_id == script.id
        assert result.status == "SUCCESS"
        assert result.exit_code == 0
        assert result.duration_seconds > 0
        assert result.start_time is not None
        assert result.end_time is not None
        
        # Verify performance metrics
        assert result.performance_metrics is not None
        metrics = result.performance_metrics
        assert metrics["total_return_pct"] == 15.5
        assert metrics["sharpe_ratio"] == 1.25
        assert metrics["max_drawdown_pct"] == 5.2
        assert metrics["win_rate"] == 0.65
        assert metrics["total_trades"] == 120
        assert metrics["initial_capital"] == 10000.0
        assert metrics["final_capital"] == 11550.0
        
        # Verify trade data
        assert result.trade_data is not None
        assert len(result.trade_data) == 2
        assert result.trade_data[0]["symbol"] == "AAPL"
        assert result.trade_data[0]["action"] == "BUY"
        
        # Verify stdout contains results
        assert "total_return_pct" in result.stdout
        
        # Verify resource usage is tracked
        assert result.resource_usage is not None
        assert "peak_memory_mb" in result.resource_usage
        assert "average_cpu_percent" in result.resource_usage
    
    def test_execute_script_failure(self, failing_script):
        """Test script execution failure handling"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="failing-script-1",
            name="failing_script",
            file_path=str(failing_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify failure result
        assert isinstance(result, BacktestResult)
        assert result.script_id == script.id
        assert result.status == "FAILED"
        assert result.exit_code != 0
        assert result.duration_seconds > 0
        
        # Verify error information
        assert "Simulated backtest failure" in result.stderr
        assert result.validation_errors is not None
        assert len(result.validation_errors) > 0
    
    def test_execute_script_timeout(self, timeout_script):
        """Test script execution timeout"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="timeout-script-1",
            name="timeout_script",
            file_path=str(timeout_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=2  # 2 second timeout
        )
        
        result = executor.execute_script(script)
        
        # Verify timeout result
        assert isinstance(result, BacktestResult)
        assert result.script_id == script.id
        assert result.status == "TIMEOUT"
        assert result.duration_seconds >= 2.0
        assert result.duration_seconds < 10.0  # Should timeout before 10 seconds
    
    def test_execute_script_with_parameters(self, test_script):
        """Test script execution with custom parameters"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="param-script-1",
            name="param_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            parameters={"initial_capital": 20000.0, "risk_level": "high"},
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify result with parameters
        assert isinstance(result, BacktestResult)
        assert result.status == "SUCCESS"
        assert result.performance_metrics is not None
    
    def test_execute_script_environment_isolation(self, test_script):
        """Test that script execution is properly isolated"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        # Set environment variable in current process
        os.environ["TEST_VAR"] = "original_value"
        
        script = BacktestScript(
            id="env-script-1",
            name="env_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify environment variable is unchanged
        assert os.environ.get("TEST_VAR") == "original_value"
        
        # Verify script executed successfully
        assert result.status == "SUCCESS"
    
    def test_execute_script_resource_limits(self, test_script):
        """Test script execution with resource limits"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="resource-script-1",
            name="resource_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify resource usage is within limits
        assert result.status == "SUCCESS"
        assert result.resource_usage is not None
        
        # Memory usage should be reasonable (< 500MB for simple script)
        assert result.resource_usage["peak_memory_mb"] < 500
        
        # CPU usage should be reasonable (< 50% average)
        assert result.resource_usage["average_cpu_percent"] < 50
    
    @pytest.mark.asyncio
    async def test_execute_script_async(self, test_script):
        """Test asynchronous script execution"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="async-script-1",
            name="async_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        result = await executor.execute_script_async(script)
        
        # Verify async result
        assert isinstance(result, BacktestResult)
        assert result.status == "SUCCESS"
        assert result.performance_metrics is not None
    
    def test_execute_multiple_scripts_parallel(self, test_script):
        """Test parallel execution of multiple scripts"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        scripts = []
        for i in range(3):
            script = BacktestScript(
                id=f"parallel-script-{i}",
                name=f"parallel_script_{i}",
                file_path=str(test_script),
                function_name="run_backtest",
                script_type="INDIVIDUAL_STRATEGY",
                timeout_seconds=30
            )
            scripts.append(script)
        
        results = executor.execute_scripts_parallel(scripts, max_parallel=3)
        
        # Verify all scripts executed successfully
        assert len(results) == 3
        for result in results:
            assert isinstance(result, BacktestResult)
            assert result.status == "SUCCESS"
    
    def test_execute_script_with_dependencies(self, test_script):
        """Test script execution with external dependencies"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        script = BacktestScript(
            id="dep-script-1",
            name="dep_script",
            file_path=str(test_script),
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            dependencies=["pandas", "numpy"],
            timeout_seconds=30
        )
        
        result = executor.execute_script(script)
        
        # Verify script executed with dependencies
        assert result.status == "SUCCESS"
        assert result.performance_metrics is not None
    
    def test_execute_script_error_handling(self):
        """Test error handling for invalid scripts"""
        # This test will FAIL until implementation is complete
        executor = ScriptExecutor()
        
        # Test with non-existent script
        script = BacktestScript(
            id="invalid-script-1",
            name="invalid_script",
            file_path="/non/existent/script.py",
            function_name="run_backtest",
            script_type="INDIVIDUAL_STRATEGY",
            timeout_seconds=30
        )
        
        with pytest.raises(FileNotFoundError):
            executor.execute_script(script)
        
        # Test with invalid script ID
        with pytest.raises(ValueError):
            executor.execute_script(None)


if __name__ == "__main__":
    pytest.main([__file__])













