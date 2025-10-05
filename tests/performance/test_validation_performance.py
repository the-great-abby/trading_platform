"""
Performance tests for validation framework

This module provides performance tests to ensure the validation framework
can handle expected loads and performance requirements.
"""

import pytest
import asyncio
import tempfile
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, AsyncMock

from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.execution.script_executor import ScriptExecutor
from src.validation.validation.result_validator import ResultValidator
from src.validation.execution.batch_validator import BatchValidator
from src.validation.reporting.report_generator import ReportGenerator
from src.validation.models.backtest_script import BacktestScript
from src.validation.models.backtest_result import BacktestResult
from src.validation.integration.metrics_collector import MetricsCollector
from src.validation.integration.error_handler import RetryHandler, CircuitBreaker


class TestDiscoveryPerformance:
    """Test script discovery performance"""
    
    @pytest.fixture
    def discovery_service(self):
        """Create BacktestScriptDiscovery instance"""
        return BacktestScriptDiscovery()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_discover_large_directory(self, discovery_service):
        """Test discovery performance with large directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 100 test scripts
            for i in range(100):
                script_path = Path(temp_dir) / f"test_backtest_{i:03d}.py"
                script_path.write_text(f"# Backtest script {i}")
            
            # Measure discovery time
            start_time = time.time()
            scripts = await discovery_service.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py"
            )
            discovery_time = time.time() - start_time
            
            assert len(scripts) == 100
            assert discovery_time < 5.0  # Should discover 100 scripts in under 5 seconds
            print(f"Discovered 100 scripts in {discovery_time:.2f} seconds")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_discover_nested_directories(self, discovery_service):
        """Test discovery performance with nested directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure with scripts
            for level1 in range(5):
                level1_dir = Path(temp_dir) / f"level1_{level1}"
                level1_dir.mkdir()
                
                for level2 in range(5):
                    level2_dir = level1_dir / f"level2_{level2}"
                    level2_dir.mkdir()
                    
                    for script_num in range(4):
                        script_path = level2_dir / f"test_backtest_{script_num}.py"
                        script_path.write_text(f"# Backtest script {level1}_{level2}_{script_num}")
            
            # Measure discovery time
            start_time = time.time()
            scripts = await discovery_service.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py",
                include_subdirectories=True,
                max_depth=3
            )
            discovery_time = time.time() - start_time
            
            assert len(scripts) == 100  # 5 * 5 * 4 = 100 scripts
            assert discovery_time < 10.0  # Should discover 100 scripts in under 10 seconds
            print(f"Discovered 100 nested scripts in {discovery_time:.2f} seconds")


class TestExecutionPerformance:
    """Test script execution performance"""
    
    @pytest.fixture
    def executor(self):
        """Create ScriptExecutor instance"""
        return ScriptExecutor()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_execute_multiple_scripts_sequential(self, executor):
        """Test sequential execution performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 10 test scripts
            scripts = []
            for i in range(10):
                script_path = Path(temp_dir) / f"test_script_{i}.py"
                script_content = f"""
import json
import time
time.sleep(0.1)  # Simulate processing time
print(json.dumps({{
    "total_return_pct": {10.0 + i},
    "sharpe_ratio": {1.5 + i * 0.1},
    "script_id": "script_{i}"
}}))
"""
                script_path.write_text(script_content)
                scripts.append(str(script_path))
            
            # Execute scripts sequentially
            start_time = time.time()
            results = []
            for script_path in scripts:
                result = await executor.execute_script(
                    script_path=script_path,
                    timeout_seconds=30
                )
                results.append(result)
            execution_time = time.time() - start_time
            
            assert len(results) == 10
            assert all(r.validation_status == "PASSED" for r in results)
            assert execution_time < 15.0  # Should complete in under 15 seconds
            print(f"Executed 10 scripts sequentially in {execution_time:.2f} seconds")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_execute_multiple_scripts_concurrent(self, executor):
        """Test concurrent execution performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 10 test scripts
            scripts = []
            for i in range(10):
                script_path = Path(temp_dir) / f"test_script_{i}.py"
                script_content = f"""
import json
import time
time.sleep(0.1)  # Simulate processing time
print(json.dumps({{
    "total_return_pct": {10.0 + i},
    "sharpe_ratio": {1.5 + i * 0.1},
    "script_id": "script_{i}"
}}))
"""
                script_path.write_text(script_content)
                scripts.append(str(script_path))
            
            # Execute scripts concurrently
            start_time = time.time()
            tasks = [
                executor.execute_script(script_path=script_path, timeout_seconds=30)
                for script_path in scripts
            ]
            results = await asyncio.gather(*tasks)
            execution_time = time.time() - start_time
            
            assert len(results) == 10
            assert all(r.validation_status == "PASSED" for r in results)
            assert execution_time < 5.0  # Should complete much faster than sequential
            print(f"Executed 10 scripts concurrently in {execution_time:.2f} seconds")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_execute_large_script_output(self, executor):
        """Test execution performance with large output"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create script with large output
            script_path = Path(temp_dir) / "large_output_script.py"
            script_content = """
import json
import random

# Generate large dataset
data = {
    "total_return_pct": 15.5,
    "sharpe_ratio": 2.1,
    "max_drawdown_pct": -8.2,
    "trades": []
}

# Add 1000 fake trades
for i in range(1000):
    data["trades"].append({
        "trade_id": i,
        "symbol": f"STOCK_{i % 50}",
        "price": round(random.uniform(10, 100), 2),
        "quantity": random.randint(1, 100),
        "timestamp": f"2024-01-{(i % 30) + 1:02d}T10:00:00Z"
    })

print(json.dumps(data))
"""
            script_path.write_text(script_content)
            
            # Measure execution time
            start_time = time.time()
            result = await executor.execute_script(
                script_path=str(script_path),
                timeout_seconds=30
            )
            execution_time = time.time() - start_time
            
            assert result.validation_status == "PASSED"
            assert execution_time < 5.0  # Should handle large output efficiently
            assert len(result.metrics.get("trades", [])) == 1000
            print(f"Executed large output script in {execution_time:.2f} seconds")


class TestValidationPerformance:
    """Test result validation performance"""
    
    @pytest.fixture
    def validator(self):
        """Create ResultValidator instance"""
        return ResultValidator()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validate_large_result_set(self, validator):
        """Test validation performance with large result set"""
        # Create 1000 results
        results = []
        for i in range(1000):
            result = BacktestResult(
                script_id=f"script_{i}",
                execution_time=time.time(),
                validation_status="PASSED",
                metrics={
                    "total_return_pct": 10.0 + (i % 20),
                    "sharpe_ratio": 1.0 + (i % 10) * 0.1,
                    "max_drawdown_pct": -5.0 - (i % 15)
                }
            )
            results.append(result)
        
        expected_metrics = {
            "total_return_pct": 15.0,
            "sharpe_ratio": 1.5,
            "max_drawdown_pct": -8.0
        }
        tolerance_levels = {
            "total_return_pct": 0.1,
            "sharpe_ratio": 0.2,
            "max_drawdown_pct": 0.1
        }
        
        # Measure validation time
        start_time = time.time()
        validation_results = []
        for result in results:
            validation_result = await validator.validate_result(
                result=result,
                expected_metrics=expected_metrics,
                tolerance_levels=tolerance_levels
            )
            validation_results.append(validation_result)
        validation_time = time.time() - start_time
        
        assert len(validation_results) == 1000
        assert validation_time < 10.0  # Should validate 1000 results in under 10 seconds
        print(f"Validated 1000 results in {validation_time:.2f} seconds")


class TestBatchValidationPerformance:
    """Test batch validation performance"""
    
    @pytest.fixture
    def batch_validator(self):
        """Create BatchValidator instance"""
        return BatchValidator()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_validation_large_set(self, batch_validator):
        """Test batch validation with large script set"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 50 test scripts
            scripts = []
            for i in range(50):
                script_path = Path(temp_dir) / f"batch_test_script_{i}.py"
                script_content = f"""
import json
import time
time.sleep(0.05)  # Simulate processing time
print(json.dumps({{
    "total_return_pct": {10.0 + (i % 20)},
    "sharpe_ratio": {1.0 + (i % 10) * 0.1},
    "script_id": "batch_script_{i}"
}}))
"""
                script_path.write_text(script_content)
                
                script = BacktestScript(
                    script_id=f"batch_script_{i}",
                    file_path=str(script_path),
                    script_name=f"batch_test_script_{i}.py",
                    script_type="backtest"
                )
                scripts.append(script)
            
            # Measure batch validation time
            start_time = time.time()
            results = await batch_validator.validate_batch(
                scripts=scripts,
                parallel_execution=True,
                max_concurrent=10
            )
            batch_time = time.time() - start_time
            
            assert len(results) == 50
            successful_count = sum(1 for r in results if r.get("status") == "PASSED")
            assert successful_count >= 40  # At least 80% should succeed
            assert batch_time < 30.0  # Should complete in under 30 seconds
            print(f"Batch validated 50 scripts in {batch_time:.2f} seconds ({successful_count}/50 successful)")


class TestReportGenerationPerformance:
    """Test report generation performance"""
    
    @pytest.fixture
    def report_generator(self):
        """Create ReportGenerator instance"""
        return ReportGenerator()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_generate_large_report(self, report_generator):
        """Test report generation with large dataset"""
        # Create large result set
        results = []
        for i in range(1000):
            result = {
                "script_id": f"script_{i}",
                "status": "PASSED" if i % 10 != 0 else "FAILED",
                "metrics": {
                    "total_return_pct": 10.0 + (i % 20),
                    "sharpe_ratio": 1.0 + (i % 10) * 0.1,
                    "max_drawdown_pct": -5.0 - (i % 15),
                    "trades_count": 100 + (i % 500)
                },
                "execution_time": f"2024-01-{(i % 30) + 1:02d}T10:00:00Z"
            }
            results.append(result)
        
        # Measure report generation time
        start_time = time.time()
        report = await report_generator.generate_report(
            script_ids=[f"script_{i}" for i in range(1000)],
            results=results,
            report_type="detailed",
            format="json"
        )
        generation_time = time.time() - start_time
        
        assert report is not None
        assert report["summary"]["total_scripts"] == 1000
        assert generation_time < 15.0  # Should generate report in under 15 seconds
        print(f"Generated large report in {generation_time:.2f} seconds")


class TestMetricsPerformance:
    """Test metrics collection performance"""
    
    @pytest.mark.performance
    def test_metrics_collection_performance(self):
        """Test metrics collection performance"""
        collector = MetricsCollector()
        
        # Measure metrics collection time
        start_time = time.time()
        
        # Simulate high-frequency metrics collection
        for i in range(10000):
            collector.increment_counter("test_counter", 1.0)
            collector.set_gauge("test_gauge", i % 100)
            collector.observe_histogram("test_histogram", i % 50)
            
            # Every 1000 operations, export metrics
            if i % 1000 == 0:
                collector.export_prometheus_format()
        
        collection_time = time.time() - start_time
        
        assert collection_time < 5.0  # Should handle 10k operations in under 5 seconds
        assert collector.counters["test_counter_default"] == 10000
        print(f"Collected 10k metrics in {collection_time:.2f} seconds")


class TestErrorHandlingPerformance:
    """Test error handling performance"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_retry_handler_performance(self):
        """Test retry handler performance"""
        retry_handler = RetryHandler()
        
        async def flaky_function():
            """Function that fails 50% of the time"""
            import random
            if random.random() < 0.5:
                raise Exception("Random failure")
            return "success"
        
        # Measure retry performance
        start_time = time.time()
        
        # Execute 100 operations
        tasks = [retry_handler.execute_with_retry(flaky_function) for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        
        success_count = sum(1 for r in results if r == "success")
        failure_count = sum(1 for r in results if isinstance(r, Exception))
        
        assert success_count + failure_count == 100
        assert execution_time < 20.0  # Should handle retries efficiently
        print(f"Retry handler processed 100 operations in {execution_time:.2f} seconds ({success_count} success, {failure_count} failures)")
    
    @pytest.mark.performance
    def test_circuit_breaker_performance(self):
        """Test circuit breaker performance"""
        circuit_breaker = CircuitBreaker()
        
        # Measure circuit breaker operations
        start_time = time.time()
        
        # Simulate 1000 circuit breaker calls
        for i in range(1000):
            # Simulate failures to trigger circuit breaker
            if i % 10 == 0:
                circuit_breaker._on_failure()
            else:
                circuit_breaker._on_success()
        
        execution_time = time.time() - start_time
        
        assert execution_time < 1.0  # Should handle 1k operations very quickly
        print(f"Circuit breaker processed 1000 operations in {execution_time:.4f} seconds")


class TestConcurrentLoadPerformance:
    """Test concurrent load performance"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """Test concurrent API request simulation"""
        # Simulate API request processing
        async def simulate_api_request(request_id: int):
            """Simulate API request processing"""
            await asyncio.sleep(0.01)  # Simulate processing time
            return {"request_id": request_id, "status": "processed"}
        
        # Measure concurrent request handling
        start_time = time.time()
        
        # Simulate 100 concurrent requests
        tasks = [simulate_api_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        
        assert len(results) == 100
        assert execution_time < 2.0  # Should handle 100 concurrent requests in under 2 seconds
        print(f"Processed 100 concurrent requests in {execution_time:.2f} seconds")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many objects to test memory usage
        collectors = []
        for i in range(1000):
            collector = MetricsCollector()
            collector.increment_counter("test_counter", i)
            collector.set_gauge("test_gauge", i)
            collectors.append(collector)
        
        # Check memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        assert memory_increase < 100  # Should not use more than 100MB additional memory
        print(f"Memory usage increased by {memory_increase:.2f} MB for 1000 metrics collectors")


class TestStressTest:
    """Stress tests for validation framework"""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_stress_validation_workflow(self):
        """Stress test complete validation workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 100 test scripts
            scripts = []
            for i in range(100):
                script_path = Path(temp_dir) / f"stress_test_script_{i}.py"
                script_content = f"""
import json
import time
import random
time.sleep(random.uniform(0.01, 0.1))  # Random processing time
print(json.dumps({{
    "total_return_pct": {10.0 + random.uniform(-5, 5)},
    "sharpe_ratio": {1.0 + random.uniform(-0.5, 0.5)},
    "max_drawdown_pct": {-5.0 - random.uniform(0, 10)},
    "script_id": "stress_script_{i}"
}}))
"""
                script_path.write_text(script_content)
                scripts.append(str(script_path))
            
            # Create services
            discovery = BacktestScriptDiscovery()
            executor = ScriptExecutor()
            validator = ResultValidator()
            
            # Stress test workflow
            start_time = time.time()
            
            # Discover scripts
            discovered_scripts = await discovery.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py"
            )
            
            # Execute all scripts concurrently
            execution_tasks = [
                executor.execute_script(script_path=script.file_path, timeout_seconds=30)
                for script in discovered_scripts
            ]
            execution_results = await asyncio.gather(*execution_tasks)
            
            # Validate all results
            validation_tasks = []
            for result in execution_results:
                if result.validation_status == "PASSED":
                    validation_task = validator.validate_result(
                        result=result,
                        expected_metrics={"total_return_pct": 10.0, "sharpe_ratio": 1.0},
                        tolerance_levels={"total_return_pct": 0.2, "sharpe_ratio": 0.5}
                    )
                    validation_tasks.append(validation_task)
            
            validation_results = await asyncio.gather(*validation_tasks)
            
            total_time = time.time() - start_time
            
            # Verify results
            assert len(discovered_scripts) == 100
            assert len(execution_results) == 100
            successful_executions = sum(1 for r in execution_results if r.validation_status == "PASSED")
            successful_validations = sum(1 for r in validation_results if r.is_valid)
            
            assert total_time < 60.0  # Should complete stress test in under 60 seconds
            assert successful_executions >= 80  # At least 80% should execute successfully
            assert successful_validations >= 70  # At least 70% should validate successfully
            
            print(f"Stress test completed in {total_time:.2f} seconds:")
            print(f"  - Discovered: {len(discovered_scripts)} scripts")
            print(f"  - Executed successfully: {successful_executions}/100")
            print(f"  - Validated successfully: {successful_validations}/{len(validation_results)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])

