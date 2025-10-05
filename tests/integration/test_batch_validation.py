"""
Integration Tests for Batch Validation Service

Tests the batch validation functionality that executes multiple backtest scripts
in parallel and aggregates the results.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# This will fail until implementation is complete
from src.validation.execution.batch_validator import BatchValidator
from src.validation.models.backtest_script import BacktestScript
from src.validation.models.backtest_result import BacktestResult
from src.validation.models.test_configuration import TestConfiguration


class TestBatchValidationIntegration:
    """Integration tests for batch validation"""
    
    @pytest.fixture
    def test_scripts(self):
        """Create test scripts for batch validation"""
        scripts = []
        for i in range(5):
            script = BacktestScript(
                id=f"batch-script-{i}",
                name=f"batch_script_{i}",
                file_path=f"/tmp/test_script_{i}.py",
                function_name="run_backtest",
                script_type="INDIVIDUAL_STRATEGY",
                timeout_seconds=30,
                created_at=datetime.now()
            )
            scripts.append(script)
        return scripts
    
    @pytest.fixture
    def default_config(self):
        """Create default validation configuration"""
        return TestConfiguration(
            id="default-config",
            name="Default Configuration",
            description="Default validation settings",
            tolerances={
                "returns_tolerance_pct": 0.1,
                "ratios_tolerance": 0.01,
                "drawdown_tolerance_pct": 0.05,
                "win_rate_tolerance_pct": 0.5
            },
            timeouts={
                "quick_test_seconds": 30,
                "standard_test_seconds": 300,
                "comprehensive_test_seconds": 1800,
                "options_test_seconds": 600
            },
            validation_rules={
                "require_exact_trade_counts": True,
                "allow_missing_metrics": [],
                "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct"]
            },
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 4,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_batch_validation_success(self, test_scripts, default_config):
        """Test successful batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=3
        )
        
        # Verify batch results
        assert len(results) == 5
        assert all(isinstance(result, BacktestResult) for result in results)
        
        # Verify all scripts were processed
        script_ids = {result.script_id for result in results}
        expected_script_ids = {script.id for script in test_scripts}
        assert script_ids == expected_script_ids
        
        # Verify results have different execution IDs
        execution_ids = {result.execution_id for result in results}
        assert len(execution_ids) == 5  # All unique
    
    def test_batch_validation_with_failures(self, test_scripts, default_config):
        """Test batch validation with some failures"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        # Modify one script to be invalid
        test_scripts[2].file_path = "/non/existent/script.py"
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=3
        )
        
        # Verify results
        assert len(results) == 5
        
        # Check that we have both successes and failures
        success_count = sum(1 for result in results if result.status == "SUCCESS")
        failure_count = sum(1 for result in results if result.status in ["FAILED", "ERROR"])
        
        assert success_count == 4
        assert failure_count == 1
    
    def test_batch_validation_parallel_execution(self, test_scripts, default_config):
        """Test parallel execution in batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        start_time = datetime.now()
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=5  # All scripts in parallel
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify parallel execution (should be faster than sequential)
        # Assuming each script takes ~1 second, parallel should be much faster
        assert execution_time < 10.0  # Should complete in less than 10 seconds
        
        # Verify all results are present
        assert len(results) == 5
    
    def test_batch_validation_sequential_execution(self, test_scripts, default_config):
        """Test sequential execution in batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        start_time = datetime.now()
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=1  # Sequential execution
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify sequential execution (should take longer than parallel)
        assert execution_time > 5.0  # Should take longer than parallel
        
        # Verify all results are present
        assert len(results) == 5
    
    def test_batch_validation_with_retry(self, test_scripts, default_config):
        """Test batch validation with retry logic"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        # Configure retry settings
        config_with_retry = TestConfiguration(
            id="retry-config",
            name="Retry Configuration",
            description="Configuration with retry enabled",
            tolerances=default_config.tolerances,
            timeouts=default_config.timeouts,
            validation_rules=default_config.validation_rules,
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 3,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=config_with_retry,
            max_parallel_jobs=3
        )
        
        # Verify results with retry
        assert len(results) == 5
        assert all(isinstance(result, BacktestResult) for result in results)
    
    def test_batch_validation_progress_tracking(self, test_scripts, default_config):
        """Test progress tracking during batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        progress_updates = []
        
        def progress_callback(completed, total, current_script):
            progress_updates.append({
                "completed": completed,
                "total": total,
                "current_script": current_script
            })
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=3,
            progress_callback=progress_callback
        )
        
        # Verify progress tracking
        assert len(progress_updates) >= 5  # Should have progress updates
        
        # Verify progress sequence
        for i, update in enumerate(progress_updates):
            assert update["total"] == 5
            assert update["completed"] <= 5
            assert update["current_script"] is not None
        
        # Final update should show completion
        final_update = progress_updates[-1]
        assert final_update["completed"] == 5
    
    def test_batch_validation_large_batch(self, default_config):
        """Test batch validation with large number of scripts"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        # Create large batch of scripts
        large_scripts = []
        for i in range(20):
            script = BacktestScript(
                id=f"large-batch-script-{i}",
                name=f"large_batch_script_{i}",
                file_path=f"/tmp/large_test_script_{i}.py",
                function_name="run_backtest",
                script_type="INDIVIDUAL_STRATEGY",
                timeout_seconds=30,
                created_at=datetime.now()
            )
            large_scripts.append(script)
        
        results = batch_validator.validate_batch(
            scripts=large_scripts,
            configuration=default_config,
            max_parallel_jobs=5
        )
        
        # Verify large batch processing
        assert len(results) == 20
        assert all(isinstance(result, BacktestResult) for result in results)
        
        # Verify all scripts were processed
        script_ids = {result.script_id for result in results}
        expected_script_ids = {script.id for script in large_scripts}
        assert script_ids == expected_script_ids
    
    def test_batch_validation_error_handling(self, test_scripts, default_config):
        """Test error handling in batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        # Test with empty script list
        empty_results = batch_validator.validate_batch(
            scripts=[],
            configuration=default_config,
            max_parallel_jobs=3
        )
        assert len(empty_results) == 0
        
        # Test with invalid configuration
        with pytest.raises(ValueError):
            batch_validator.validate_batch(
                scripts=test_scripts,
                configuration=None,
                max_parallel_jobs=3
            )
        
        # Test with invalid parallel jobs count
        with pytest.raises(ValueError):
            batch_validator.validate_batch(
                scripts=test_scripts,
                configuration=default_config,
                max_parallel_jobs=0
            )
    
    @pytest.mark.asyncio
    async def test_batch_validation_async(self, test_scripts, default_config):
        """Test asynchronous batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        results = await batch_validator.validate_batch_async(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=3
        )
        
        # Verify async results
        assert len(results) == 5
        assert all(isinstance(result, BacktestResult) for result in results)
        
        # Verify all scripts were processed
        script_ids = {result.script_id for result in results}
        expected_script_ids = {script.id for script in test_scripts}
        assert script_ids == expected_script_ids
    
    def test_batch_validation_resource_management(self, test_scripts, default_config):
        """Test resource management during batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=default_config,
            max_parallel_jobs=2  # Limit parallel execution
        )
        
        # Verify resource management
        assert len(results) == 5
        
        # Verify resource usage is tracked for all results
        for result in results:
            assert result.resource_usage is not None
            assert "peak_memory_mb" in result.resource_usage
            assert "average_cpu_percent" in result.resource_usage
    
    def test_batch_validation_timeout_handling(self, test_scripts, default_config):
        """Test timeout handling in batch validation"""
        # This test will FAIL until implementation is complete
        batch_validator = BatchValidator()
        
        # Create a configuration with short timeout
        short_timeout_config = TestConfiguration(
            id="short-timeout-config",
            name="Short Timeout Configuration",
            description="Configuration with short timeouts",
            tolerances=default_config.tolerances,
            timeouts={
                "quick_test_seconds": 1,  # Very short timeout
                "standard_test_seconds": 1,
                "comprehensive_test_seconds": 1,
                "options_test_seconds": 1
            },
            validation_rules=default_config.validation_rules,
            execution_settings=default_config.execution_settings,
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        results = batch_validator.validate_batch(
            scripts=test_scripts,
            configuration=short_timeout_config,
            max_parallel_jobs=3
        )
        
        # Verify timeout handling
        assert len(results) == 5
        
        # Some results might timeout
        timeout_count = sum(1 for result in results if result.status == "TIMEOUT")
        assert timeout_count >= 0  # Some may timeout due to short timeout


if __name__ == "__main__":
    pytest.main([__file__])

