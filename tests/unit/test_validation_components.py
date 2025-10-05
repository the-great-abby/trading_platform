"""
Comprehensive unit tests for validation framework components

This module provides unit tests for all validation framework components
to ensure proper functionality and reliability.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

from src.validation.models.backtest_script import BacktestScript
from src.validation.models.backtest_result import BacktestResult
from src.validation.models.validation_report import ValidationReport
from src.validation.models.test_configuration import TestConfiguration
from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.execution.script_executor import ScriptExecutor
from src.validation.validation.result_validator import ResultValidator
from src.validation.execution.batch_validator import BatchValidator
from src.validation.reporting.report_generator import ReportGenerator
from src.validation.config.config_manager import ConfigManager
from src.validation.integration.database_adapter import DatabaseAdapter
from src.validation.integration.error_handler import ErrorHandler, CircuitBreaker, RetryHandler
from src.validation.integration.logging_config import ValidationLogger, ValidationMetrics
from src.validation.integration.metrics_collector import MetricsCollector


class TestBacktestScript:
    """Test BacktestScript model"""
    
    def test_backtest_script_creation(self):
        """Test BacktestScript model creation"""
        script = BacktestScript(
            script_id="test_script_1",
            file_path="/path/to/test_script.py",
            script_name="Test Script",
            script_type="backtest"
        )
        
        assert script.script_id == "test_script_1"
        assert script.file_path == "/path/to/test_script.py"
        assert script.script_name == "Test Script"
        assert script.script_type == "backtest"
        assert script.validation_status == "PENDING"
    
    def test_backtest_script_validation(self):
        """Test BacktestScript validation"""
        with pytest.raises(ValueError):
            BacktestScript(
                script_id="",  # Empty script_id should raise error
                file_path="/path/to/test_script.py",
                script_name="Test Script",
                script_type="backtest"
            )


class TestBacktestResult:
    """Test BacktestResult model"""
    
    def test_backtest_result_creation(self):
        """Test BacktestResult model creation"""
        result = BacktestResult(
            script_id="test_script_1",
            execution_time=datetime.now(),
            validation_status="PASSED",
            metrics={"total_return_pct": 10.5, "sharpe_ratio": 1.8}
        )
        
        assert result.script_id == "test_script_1"
        assert result.validation_status == "PASSED"
        assert result.metrics["total_return_pct"] == 10.5
        assert result.metrics["sharpe_ratio"] == 1.8
    
    def test_backtest_result_validation(self):
        """Test BacktestResult validation"""
        with pytest.raises(ValueError):
            BacktestResult(
                script_id="test_script_1",
                execution_time=datetime.now(),
                validation_status="INVALID_STATUS",  # Invalid status should raise error
                metrics={}
            )


class TestValidationReport:
    """Test ValidationReport model"""
    
    def test_validation_report_creation(self):
        """Test ValidationReport model creation"""
        report = ValidationReport(
            report_id="report_1",
            report_type="summary",
            script_ids=["script1", "script2"],
            results=[{"script_id": "script1", "status": "PASSED"}],
            summary={"total_scripts": 2, "successful": 1}
        )
        
        assert report.report_id == "report_1"
        assert report.report_type == "summary"
        assert len(report.script_ids) == 2
        assert report.summary["total_scripts"] == 2


class TestTestConfiguration:
    """Test TestConfiguration model"""
    
    def test_test_configuration_creation(self):
        """Test TestConfiguration model creation"""
        config = TestConfiguration(
            config_name="test_config",
            description="Test configuration",
            timeout_seconds=300,
            expected_metrics={"total_return_pct": 10.0},
            tolerance_levels={"total_return_pct": 0.01}
        )
        
        assert config.config_name == "test_config"
        assert config.timeout_seconds == 300
        assert config.expected_metrics["total_return_pct"] == 10.0


class TestBacktestScriptDiscovery:
    """Test BacktestScriptDiscovery service"""
    
    @pytest.fixture
    def discovery_service(self):
        """Create BacktestScriptDiscovery instance"""
        return BacktestScriptDiscovery()
    
    @pytest.mark.asyncio
    async def test_discover_scripts_basic(self, discovery_service):
        """Test basic script discovery"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test script files
            script1_path = Path(temp_dir) / "test_backtest_1.py"
            script2_path = Path(temp_dir) / "test_simulation_1.py"
            script3_path = Path(temp_dir) / "regular_script.py"
            
            script1_path.write_text("# Backtest script")
            script2_path.write_text("# Simulation script")
            script3_path.write_text("# Regular script")
            
            # Discover scripts
            scripts = await discovery_service.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py"
            )
            
            assert len(scripts) == 1
            assert scripts[0].script_name == "test_backtest_1.py"
            assert scripts[0].script_type == "backtest"
    
    @pytest.mark.asyncio
    async def test_discover_scripts_with_subdirectories(self, discovery_service):
        """Test script discovery with subdirectories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory structure
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            script1_path = Path(temp_dir) / "test_backtest_1.py"
            script2_path = subdir / "test_backtest_2.py"
            
            script1_path.write_text("# Backtest script 1")
            script2_path.write_text("# Backtest script 2")
            
            # Discover scripts with subdirectories
            scripts = await discovery_service.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py",
                include_subdirectories=True,
                max_depth=2
            )
            
            assert len(scripts) == 2
            script_names = [s.script_name for s in scripts]
            assert "test_backtest_1.py" in script_names
            assert "test_backtest_2.py" in script_names


class TestScriptExecutor:
    """Test ScriptExecutor service"""
    
    @pytest.fixture
    def executor(self):
        """Create ScriptExecutor instance"""
        return ScriptExecutor()
    
    @pytest.mark.asyncio
    async def test_execute_script_success(self, executor):
        """Test successful script execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple test script
            script_path = Path(temp_dir) / "test_script.py"
            script_content = """
import sys
import json
print(json.dumps({
    "total_return_pct": 10.5,
    "sharpe_ratio": 1.8,
    "max_drawdown_pct": -5.2
}))
"""
            script_path.write_text(script_content)
            
            # Execute script
            result = await executor.execute_script(
                script_path=str(script_path),
                timeout_seconds=30
            )
            
            assert result is not None
            assert result.script_id is not None
            assert result.validation_status == "PASSED"
            assert "total_return_pct" in result.metrics
    
    @pytest.mark.asyncio
    async def test_execute_script_timeout(self, executor):
        """Test script execution timeout"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a script that sleeps
            script_path = Path(temp_dir) / "sleep_script.py"
            script_content = """
import time
time.sleep(10)  # Sleep for 10 seconds
print("Done")
"""
            script_path.write_text(script_content)
            
            # Execute script with short timeout
            result = await executor.execute_script(
                script_path=str(script_path),
                timeout_seconds=2
            )
            
            assert result is not None
            assert result.validation_status == "FAILED"
            assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_execute_script_error(self, executor):
        """Test script execution with error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a script that raises an error
            script_path = Path(temp_dir) / "error_script.py"
            script_content = """
raise Exception("Test error")
"""
            script_path.write_text(script_content)
            
            # Execute script
            result = await executor.execute_script(
                script_path=str(script_path),
                timeout_seconds=30
            )
            
            assert result is not None
            assert result.validation_status == "FAILED"
            assert "test error" in result.error_message.lower()


class TestResultValidator:
    """Test ResultValidator service"""
    
    @pytest.fixture
    def validator(self):
        """Create ResultValidator instance"""
        return ResultValidator()
    
    @pytest.mark.asyncio
    async def test_validate_result_exact_match(self, validator):
        """Test result validation with exact match"""
        result = BacktestResult(
            script_id="test_script",
            execution_time=datetime.now(),
            validation_status="PASSED",
            metrics={"total_return_pct": 10.0}
        )
        
        expected_metrics = {"total_return_pct": 10.0}
        tolerance_levels = {}
        
        validation_result = await validator.validate_result(
            result=result,
            expected_metrics=expected_metrics,
            tolerance_levels=tolerance_levels
        )
        
        assert validation_result.is_valid
        assert validation_result.validation_status == "PASSED"
    
    @pytest.mark.asyncio
    async def test_validate_result_with_tolerance(self, validator):
        """Test result validation with tolerance"""
        result = BacktestResult(
            script_id="test_script",
            execution_time=datetime.now(),
            validation_status="PASSED",
            metrics={"total_return_pct": 10.1}
        )
        
        expected_metrics = {"total_return_pct": 10.0}
        tolerance_levels = {"total_return_pct": 0.05}
        
        validation_result = await validator.validate_result(
            result=result,
            expected_metrics=expected_metrics,
            tolerance_levels=tolerance_levels
        )
        
        assert validation_result.is_valid
        assert validation_result.validation_status == "PASSED"
    
    @pytest.mark.asyncio
    async def test_validate_result_tolerance_exceeded(self, validator):
        """Test result validation with tolerance exceeded"""
        result = BacktestResult(
            script_id="test_script",
            execution_time=datetime.now(),
            validation_status="PASSED",
            metrics={"total_return_pct": 15.0}
        )
        
        expected_metrics = {"total_return_pct": 10.0}
        tolerance_levels = {"total_return_pct": 0.01}
        
        validation_result = await validator.validate_result(
            result=result,
            expected_metrics=expected_metrics,
            tolerance_levels=tolerance_levels
        )
        
        assert not validation_result.is_valid
        assert validation_result.validation_status == "FAILED"


class TestBatchValidator:
    """Test BatchValidator service"""
    
    @pytest.fixture
    def batch_validator(self):
        """Create BatchValidator instance"""
        return BatchValidator()
    
    @pytest.mark.asyncio
    async def test_validate_batch_basic(self, batch_validator):
        """Test basic batch validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test scripts
            script1_path = Path(temp_dir) / "test_backtest_1.py"
            script2_path = Path(temp_dir) / "test_backtest_2.py"
            
            script_content = """
import json
print(json.dumps({
    "total_return_pct": 10.0,
    "sharpe_ratio": 1.5
}))
"""
            script1_path.write_text(script_content)
            script2_path.write_text(script_content)
            
            # Create script objects
            scripts = [
                BacktestScript(
                    script_id="script1",
                    file_path=str(script1_path),
                    script_name="test_backtest_1.py",
                    script_type="backtest"
                ),
                BacktestScript(
                    script_id="script2",
                    file_path=str(script2_path),
                    script_name="test_backtest_2.py",
                    script_type="backtest"
                )
            ]
            
            # Validate batch
            results = await batch_validator.validate_batch(
                scripts=scripts,
                parallel_execution=False,
                max_concurrent=2
            )
            
            assert len(results) == 2
            assert all(r.get("status") == "PASSED" for r in results)


class TestReportGenerator:
    """Test ReportGenerator service"""
    
    @pytest.fixture
    def report_generator(self):
        """Create ReportGenerator instance"""
        return ReportGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_report_summary(self, report_generator):
        """Test summary report generation"""
        results = [
            {
                "script_id": "script1",
                "status": "PASSED",
                "metrics": {"total_return_pct": 10.0, "sharpe_ratio": 1.5}
            },
            {
                "script_id": "script2",
                "status": "FAILED",
                "error": "Timeout"
            }
        ]
        
        report = await report_generator.generate_report(
            script_ids=["script1", "script2"],
            results=results,
            report_type="summary",
            format="json"
        )
        
        assert report is not None
        assert report["report_type"] == "summary"
        assert report["summary"]["total_scripts"] == 2
        assert report["summary"]["successful_scripts"] == 1
        assert report["summary"]["failed_scripts"] == 1


class TestConfigManager:
    """Test ConfigManager service"""
    
    @pytest.fixture
    def config_manager(self):
        """Create ConfigManager instance"""
        return ConfigManager()
    
    @pytest.mark.asyncio
    async def test_save_and_load_configuration(self, config_manager):
        """Test saving and loading configuration"""
        config = TestConfiguration(
            config_name="test_config",
            description="Test configuration",
            timeout_seconds=300
        )
        
        # Save configuration
        await config_manager.save_configuration(config)
        
        # Load configuration
        loaded_config = await config_manager.get_configuration(config.config_name)
        
        assert loaded_config is not None
        assert loaded_config.config_name == "test_config"
        assert loaded_config.timeout_seconds == 300
    
    @pytest.mark.asyncio
    async def test_list_configurations(self, config_manager):
        """Test listing configurations"""
        config1 = TestConfiguration(
            config_name="config1",
            description="Configuration 1",
            timeout_seconds=300
        )
        config2 = TestConfiguration(
            config_name="config2",
            description="Configuration 2",
            timeout_seconds=600
        )
        
        # Save configurations
        await config_manager.save_configuration(config1)
        await config_manager.save_configuration(config2)
        
        # List configurations
        configs = await config_manager.list_configurations()
        
        assert len(configs) >= 2
        config_names = [c.config_name for c in configs]
        assert "config1" in config_names
        assert "config2" in config_names


class TestDatabaseAdapter:
    """Test DatabaseAdapter service"""
    
    @pytest.fixture
    def db_adapter(self):
        """Create DatabaseAdapter instance with mock connection"""
        adapter = DatabaseAdapter()
        adapter.connection = AsyncMock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_connect_success(self, db_adapter):
        """Test successful database connection"""
        db_adapter.connection.fetch.return_value = [{"version": "PostgreSQL 13.0"}]
        
        result = await db_adapter.connect()
        
        assert result is True
        db_adapter.connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, db_adapter):
        """Test database connection failure"""
        db_adapter.connection.fetch.side_effect = Exception("Connection failed")
        
        result = await db_adapter.connect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_query(self, db_adapter):
        """Test query execution"""
        db_adapter.connection.fetch.return_value = [{"id": 1, "name": "test"}]
        
        result = await db_adapter.execute_query("SELECT * FROM test_table")
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == 1


class TestErrorHandler:
    """Test ErrorHandler service"""
    
    def test_circuit_breaker_creation(self):
        """Test CircuitBreaker creation"""
        cb = CircuitBreaker()
        
        assert cb.state == "closed"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
    
    def test_retry_handler_creation(self):
        """Test RetryHandler creation"""
        rh = RetryHandler()
        
        assert rh.retry_config.max_attempts == 3
        assert rh.retry_config.base_delay == 1.0
    
    @pytest.mark.asyncio
    async def test_retry_handler_success(self):
        """Test RetryHandler with successful operation"""
        rh = RetryHandler()
        
        async def success_func():
            return "success"
        
        result = await rh.execute_with_retry(success_func)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_handler_failure(self):
        """Test RetryHandler with failed operation"""
        rh = RetryHandler()
        
        async def fail_func():
            raise Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            await rh.execute_with_retry(fail_func)


class TestValidationLogger:
    """Test ValidationLogger service"""
    
    def test_logger_creation(self):
        """Test ValidationLogger creation"""
        logger = ValidationLogger()
        
        assert logger.logger is not None
        assert logger.logger.name == "validation_framework"
    
    def test_logger_get_logger(self):
        """Test getting logger instance"""
        logger = ValidationLogger()
        child_logger = logger.get_logger("test")
        
        assert child_logger.name == "validation_framework.test"


class TestValidationMetrics:
    """Test ValidationMetrics service"""
    
    def test_metrics_creation(self):
        """Test ValidationMetrics creation"""
        logger = ValidationLogger()
        metrics = ValidationMetrics(logger)
        
        assert metrics.metrics["validations_started"] == 0
        assert metrics.metrics["validations_completed"] == 0
    
    def test_metrics_increment(self):
        """Test metrics increment"""
        logger = ValidationLogger()
        metrics = ValidationMetrics(logger)
        
        metrics.increment_validation_started()
        metrics.increment_validation_completed()
        
        assert metrics.metrics["validations_started"] == 1
        assert metrics.metrics["validations_completed"] == 1
    
    def test_metrics_summary(self):
        """Test metrics summary"""
        logger = ValidationLogger()
        metrics = ValidationMetrics(logger)
        
        metrics.increment_validation_started()
        metrics.increment_validation_started()
        metrics.increment_validation_completed()
        
        summary = metrics.get_metrics_summary()
        
        assert summary["total_errors"] == 0
        assert summary["validations_started"] == 2
        assert summary["validations_completed"] == 1


class TestMetricsCollector:
    """Test MetricsCollector service"""
    
    def test_metrics_collector_creation(self):
        """Test MetricsCollector creation"""
        collector = MetricsCollector()
        
        assert collector.counters == {}
        assert collector.gauges == {}
        assert collector.histograms == {}
    
    def test_increment_counter(self):
        """Test counter increment"""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 1.0)
        
        assert collector.counters["test_counter_default"] == 1.0
    
    def test_set_gauge(self):
        """Test gauge setting"""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 10.0)
        
        assert collector.gauges["test_gauge_default"] == 10.0
    
    def test_observe_histogram(self):
        """Test histogram observation"""
        collector = MetricsCollector()
        
        collector.observe_histogram("test_histogram", 5.0)
        
        assert len(collector.histograms["test_histogram_default"]) == 1
        assert collector.histograms["test_histogram_default"][0] == 5.0
    
    def test_start_stop_timer(self):
        """Test timer functionality"""
        collector = MetricsCollector()
        
        collector.start_timer("test_timer")
        import time
        time.sleep(0.1)
        duration = collector.stop_timer("test_timer")
        
        assert duration >= 0.1
        assert "test_timer_default" in collector.histograms
    
    def test_export_prometheus_format(self):
        """Test Prometheus format export"""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 1.0)
        collector.set_gauge("test_gauge", 10.0)
        
        prometheus_data = collector.export_prometheus_format()
        
        assert "test_counter 1.0" in prometheus_data
        assert "test_gauge 10.0" in prometheus_data
        assert "# Validation Framework Metrics" in prometheus_data


# Integration tests
class TestValidationIntegration:
    """Test validation framework integration"""
    
    @pytest.mark.asyncio
    async def test_full_validation_workflow(self):
        """Test complete validation workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test script
            script_path = Path(temp_dir) / "integration_test_backtest.py"
            script_content = """
import json
print(json.dumps({
    "total_return_pct": 12.5,
    "sharpe_ratio": 1.8,
    "max_drawdown_pct": -5.2,
    "trades_count": 100
}))
"""
            script_path.write_text(script_content)
            
            # Create services
            discovery = BacktestScriptDiscovery()
            executor = ScriptExecutor()
            validator = ResultValidator()
            
            # Discover script
            scripts = await discovery.discover_scripts(
                directory=temp_dir,
                pattern="*_backtest*.py"
            )
            
            assert len(scripts) == 1
            
            # Execute script
            result = await executor.execute_script(
                script_path=str(script_path),
                timeout_seconds=30
            )
            
            assert result.validation_status == "PASSED"
            
            # Validate result
            expected_metrics = {
                "total_return_pct": 12.0,
                "sharpe_ratio": 1.5
            }
            tolerance_levels = {
                "total_return_pct": 0.1,
                "sharpe_ratio": 0.5
            }
            
            validation_result = await validator.validate_result(
                result=result,
                expected_metrics=expected_metrics,
                tolerance_levels=tolerance_levels
            )
            
            assert validation_result.is_valid
            assert validation_result.validation_status == "PASSED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

