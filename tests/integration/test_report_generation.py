"""
Integration Tests for Report Generation Service

Tests the report generation functionality that creates comprehensive
validation reports with analysis and recommendations.
"""

import pytest
from typing import List, Dict, Any
from datetime import datetime

# This will fail until implementation is complete
from src.validation.reporting.report_generator import ReportGenerator
from src.validation.models.validation_report import ValidationReport
from src.validation.models.backtest_result import BacktestResult
from src.validation.models.backtest_script import BacktestScript


class TestReportGenerationIntegration:
    """Integration tests for report generation"""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample backtest results for report generation"""
        results = []
        
        # Create successful results
        for i in range(3):
            result = BacktestResult(
                id=f"success-result-{i}",
                script_id=f"success-script-{i}",
                execution_id=f"success-exec-{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=45.2 + (i * 5.0),
                status="SUCCESS",
                exit_code=0,
                stdout=f"Script {i} completed successfully",
                stderr="",
                performance_metrics={
                    "total_return_pct": 15.5 + (i * 2.0),
                    "sharpe_ratio": 1.25 + (i * 0.1),
                    "max_drawdown_pct": 5.2 + (i * 0.5),
                    "win_rate": 0.65 + (i * 0.05),
                    "total_trades": 120 + (i * 10),
                    "initial_capital": 10000.0,
                    "final_capital": 11550.0 + (i * 200.0)
                },
                trade_data=[
                    {"symbol": "AAPL", "action": "BUY", "price": 150.0 + (i * 5.0), "quantity": 100}
                ],
                validation_errors=[],
                resource_usage={
                    "peak_memory_mb": 256.5 + (i * 10.0),
                    "average_cpu_percent": 15.2 + (i * 2.0)
                },
                created_at=datetime.now()
            )
            results.append(result)
        
        # Create failed result
        failed_result = BacktestResult(
            id="failed-result-1",
            script_id="failed-script-1",
            execution_id="failed-exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=30.0,
            status="FAILED",
            exit_code=1,
            stdout="Script execution started",
            stderr="Error: Invalid configuration",
            performance_metrics=None,
            trade_data=[],
            validation_errors=[
                {"field": "configuration", "message": "Invalid configuration", "severity": "ERROR"}
            ],
            resource_usage={
                "peak_memory_mb": 200.0,
                "average_cpu_percent": 10.0
            },
            created_at=datetime.now()
        )
        results.append(failed_result)
        
        # Create timeout result
        timeout_result = BacktestResult(
            id="timeout-result-1",
            script_id="timeout-script-1",
            execution_id="timeout-exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=300.0,  # 5 minutes timeout
            status="TIMEOUT",
            exit_code=-1,
            stdout="Script execution started",
            stderr="Timeout after 300 seconds",
            performance_metrics=None,
            trade_data=[],
            validation_errors=[
                {"field": "execution", "message": "Script execution timeout", "severity": "ERROR"}
            ],
            resource_usage={
                "peak_memory_mb": 512.0,
                "average_cpu_percent": 25.0
            },
            created_at=datetime.now()
        )
        results.append(timeout_result)
        
        return results
    
    @pytest.fixture
    def sample_scripts(self):
        """Create sample backtest scripts for report generation"""
        scripts = []
        
        script_types = ["INDIVIDUAL_STRATEGY", "OPTIONS", "COMPREHENSIVE", "MULTI_STRATEGY"]
        
        for i, script_type in enumerate(script_types):
            script = BacktestScript(
                id=f"script-{i}",
                name=f"test_script_{i}",
                file_path=f"/tmp/test_script_{i}.py",
                function_name="run_backtest",
                script_type=script_type,
                timeout_seconds=300,
                validation_status="PASSING" if i < 3 else "FAILING",
                created_at=datetime.now()
            )
            scripts.append(script)
        
        return scripts
    
    def test_generate_validation_report_success(self, sample_results, sample_scripts):
        """Test successful report generation"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Test Validation Report",
            results=sample_results,
            scripts=sample_scripts,
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        # Verify report structure
        assert isinstance(report, ValidationReport)
        assert report.report_name == "Test Validation Report"
        assert report.generated_at is not None
        assert report.total_scripts == 4
        assert report.passed_scripts == 3
        assert report.failed_scripts == 1
        assert report.error_scripts == 1
        
        # Verify execution summary
        assert report.execution_summary is not None
        assert "total_execution_time_seconds" in report.execution_summary
        assert "average_execution_time_seconds" in report.execution_summary
        assert "parallel_execution_enabled" in report.execution_summary
        
        # Verify consistency analysis
        assert report.consistency_results is not None
        assert "consistent_scripts" in report.consistency_results
        assert "inconsistent_scripts" in report.consistency_results
        
        # Verify performance analysis
        assert report.performance_analysis is not None
        assert "average_return" in report.performance_analysis
        assert "average_sharpe" in report.performance_analysis
        assert "performance_trends" in report.performance_analysis
        
        # Verify recommendations
        assert report.recommendations is not None
        assert len(report.recommendations) > 0
        
        # Verify detailed results
        assert report.detailed_results is not None
        assert len(report.detailed_results) == 4
    
    def test_generate_report_consistency_analysis(self, sample_results):
        """Test consistency analysis in report generation"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Consistency Analysis Report",
            results=sample_results,
            scripts=[],
            include_consistency_analysis=True,
            include_performance_analysis=False,
            include_recommendations=False
        )
        
        # Verify consistency analysis
        assert report.consistency_results is not None
        
        consistency = report.consistency_results
        assert "consistent_scripts" in consistency
        assert "inconsistent_scripts" in consistency
        assert "consistency_score" in consistency
        assert "inconsistency_details" in consistency
        
        # Verify consistency score is reasonable
        assert 0.0 <= consistency["consistency_score"] <= 100.0
    
    def test_generate_report_performance_analysis(self, sample_results):
        """Test performance analysis in report generation"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Performance Analysis Report",
            results=sample_results,
            scripts=[],
            include_consistency_analysis=False,
            include_performance_analysis=True,
            include_recommendations=False
        )
        
        # Verify performance analysis
        assert report.performance_analysis is not None
        
        performance = report.performance_analysis
        assert "average_return" in performance
        assert "average_sharpe" in performance
        assert "average_drawdown" in performance
        assert "average_win_rate" in performance
        assert "performance_trends" in performance
        assert "top_performers" in performance
        assert "underperformers" in performance
        
        # Verify performance metrics are calculated correctly
        assert isinstance(performance["average_return"], (int, float))
        assert isinstance(performance["average_sharpe"], (int, float))
        assert isinstance(performance["average_drawdown"], (int, float))
        assert isinstance(performance["average_win_rate"], (int, float))
    
    def test_generate_report_recommendations(self, sample_results, sample_scripts):
        """Test recommendation generation in report"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Recommendations Report",
            results=sample_results,
            scripts=sample_scripts,
            include_consistency_analysis=False,
            include_performance_analysis=False,
            include_recommendations=True
        )
        
        # Verify recommendations
        assert report.recommendations is not None
        assert len(report.recommendations) > 0
        
        for recommendation in report.recommendations:
            assert "script_id" in recommendation
            assert "recommendation" in recommendation
            assert "priority" in recommendation
            assert recommendation["priority"] in ["HIGH", "MEDIUM", "LOW"]
            assert "category" in recommendation
            assert "description" in recommendation
    
    def test_generate_report_with_empty_results(self):
        """Test report generation with empty results"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Empty Results Report",
            results=[],
            scripts=[],
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        # Verify empty report structure
        assert isinstance(report, ValidationReport)
        assert report.total_scripts == 0
        assert report.passed_scripts == 0
        assert report.failed_scripts == 0
        assert report.error_scripts == 0
        assert len(report.detailed_results) == 0
        assert len(report.recommendations) == 0
    
    def test_generate_report_execution_summary(self, sample_results):
        """Test execution summary generation"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Execution Summary Report",
            results=sample_results,
            scripts=[],
            include_consistency_analysis=False,
            include_performance_analysis=False,
            include_recommendations=False
        )
        
        # Verify execution summary
        assert report.execution_summary is not None
        
        summary = report.execution_summary
        assert "total_execution_time_seconds" in summary
        assert "average_execution_time_seconds" in summary
        assert "parallel_execution_enabled" in summary
        assert "success_rate" in summary
        assert "failure_rate" in summary
        
        # Verify summary calculations
        assert isinstance(summary["total_execution_time_seconds"], (int, float))
        assert isinstance(summary["average_execution_time_seconds"], (int, float))
        assert isinstance(summary["success_rate"], (int, float))
        assert isinstance(summary["failure_rate"], (int, float))
        assert 0.0 <= summary["success_rate"] <= 1.0
        assert 0.0 <= summary["failure_rate"] <= 1.0
    
    def test_generate_report_export_formats(self, sample_results):
        """Test report export in different formats"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Export Test Report",
            results=sample_results,
            scripts=[],
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        # Test JSON export
        json_export = report_generator.export_to_json(report)
        assert isinstance(json_export, str)
        
        # Test HTML export
        html_export = report_generator.export_to_html(report)
        assert isinstance(html_export, str)
        assert "<html>" in html_export.lower()
        
        # Test CSV export
        csv_export = report_generator.export_to_csv(report)
        assert isinstance(csv_export, str)
        assert "," in csv_export  # CSV should contain commas
    
    def test_generate_report_with_script_metadata(self, sample_results, sample_scripts):
        """Test report generation with script metadata"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        report = report_generator.generate_report(
            report_name="Metadata Report",
            results=sample_results,
            scripts=sample_scripts,
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        # Verify script metadata is included
        assert report.detailed_results is not None
        
        for detail in report.detailed_results:
            assert "script_info" in detail
            assert "script_type" in detail["script_info"]
            assert "validation_status" in detail["script_info"]
            assert "file_path" in detail["script_info"]
    
    def test_generate_report_error_handling(self):
        """Test error handling in report generation"""
        # This test will FAIL until implementation is complete
        report_generator = ReportGenerator()
        
        # Test with invalid parameters
        with pytest.raises(ValueError):
            report_generator.generate_report(
                report_name="",  # Empty name
                results=[],
                scripts=[],
                include_consistency_analysis=True,
                include_performance_analysis=True,
                include_recommendations=True
            )
        
        with pytest.raises(ValueError):
            report_generator.generate_report(
                report_name="Test Report",
                results=None,  # None results
                scripts=[],
                include_consistency_analysis=True,
                include_performance_analysis=True,
                include_recommendations=True
            )
    
    def test_generate_report_performance_with_large_dataset(self):
        """Test report generation performance with large dataset"""
        # This test will FAIL until implementation is complete
        import time
        
        report_generator = ReportGenerator()
        
        # Create large dataset
        large_results = []
        for i in range(100):
            result = BacktestResult(
                id=f"large-result-{i}",
                script_id=f"large-script-{i}",
                execution_id=f"large-exec-{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=45.0,
                status="SUCCESS",
                exit_code=0,
                stdout=f"Script {i} completed",
                stderr="",
                performance_metrics={
                    "total_return_pct": 15.0 + (i % 10),
                    "sharpe_ratio": 1.0 + (i % 5) * 0.1,
                    "max_drawdown_pct": 5.0 + (i % 3),
                    "win_rate": 0.6 + (i % 4) * 0.1,
                    "total_trades": 100 + i,
                    "initial_capital": 10000.0,
                    "final_capital": 11500.0 + i * 10.0
                },
                trade_data=[],
                validation_errors=[],
                resource_usage={
                    "peak_memory_mb": 250.0,
                    "average_cpu_percent": 15.0
                },
                created_at=datetime.now()
            )
            large_results.append(result)
        
        start_time = time.time()
        
        report = report_generator.generate_report(
            report_name="Large Dataset Report",
            results=large_results,
            scripts=[],
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify performance (should complete within reasonable time)
        assert execution_time < 30.0  # Less than 30 seconds for 100 results
        
        # Verify report structure
        assert report.total_scripts == 100
        assert report.passed_scripts == 100
        assert len(report.detailed_results) == 100


if __name__ == "__main__":
    pytest.main([__file__])











