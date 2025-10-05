"""
Integration Tests for Result Validation Service

Tests the validation logic that ensures backtest results are consistent,
complete, and meet quality standards.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime

# This will fail until implementation is complete
from src.validation.validation.result_validator import ResultValidator
from src.validation.models.backtest_result import BacktestResult
from src.validation.models.test_configuration import TestConfiguration


class TestResultValidationIntegration:
    """Integration tests for result validation"""
    
    @pytest.fixture
    def valid_result(self):
        """Create a valid backtest result"""
        return BacktestResult(
            id="valid-result-1",
            script_id="script-1",
            execution_id="exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=45.2,
            status="SUCCESS",
            exit_code=0,
            stdout="Backtest completed successfully",
            stderr="",
            performance_metrics={
                "total_return_pct": 15.5,
                "sharpe_ratio": 1.25,
                "max_drawdown_pct": 5.2,
                "win_rate": 0.65,
                "total_trades": 120,
                "initial_capital": 10000.0,
                "final_capital": 11550.0
            },
            trade_data=[
                {"symbol": "AAPL", "action": "BUY", "price": 150.0, "quantity": 100},
                {"symbol": "AAPL", "action": "SELL", "price": 155.0, "quantity": 100}
            ],
            validation_errors=[],
            resource_usage={
                "peak_memory_mb": 256.5,
                "average_cpu_percent": 15.2
            },
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def invalid_result(self):
        """Create an invalid backtest result"""
        return BacktestResult(
            id="invalid-result-1",
            script_id="script-1",
            execution_id="exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=45.2,
            status="SUCCESS",
            exit_code=0,
            stdout="Backtest completed",
            stderr="",
            performance_metrics={
                "total_return_pct": 1500.0,  # Unrealistic return
                "sharpe_ratio": 50.0,  # Unrealistic Sharpe ratio
                "max_drawdown_pct": 0.0,  # Missing drawdown
                "win_rate": 1.0,  # 100% win rate (suspicious)
                "total_trades": 0,  # No trades but positive return
                "initial_capital": 10000.0,
                "final_capital": 160000.0  # Unrealistic final capital
            },
            trade_data=[],  # Empty trade data
            validation_errors=[],
            resource_usage={
                "peak_memory_mb": 256.5,
                "average_cpu_percent": 15.2
            },
            created_at=datetime.now()
        )
    
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
                "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate", "total_trades"]
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
    
    def test_validate_result_success(self, valid_result, default_config):
        """Test successful result validation"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        validation_result = validator.validate_result(valid_result, default_config)
        
        # Verify validation passed
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        assert len(validation_result.warnings) == 0
        assert validation_result.score >= 90.0  # High quality score
    
    def test_validate_result_failure(self, invalid_result, default_config):
        """Test result validation failure"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        validation_result = validator.validate_result(invalid_result, default_config)
        
        # Verify validation failed
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        assert validation_result.score < 50.0  # Low quality score
        
        # Verify specific error types
        error_messages = [error.message for error in validation_result.errors]
        assert any("unrealistic return" in msg.lower() for msg in error_messages)
        assert any("unrealistic sharpe" in msg.lower() for msg in error_messages)
        assert any("missing trades" in msg.lower() for msg in error_messages)
    
    def test_validate_result_consistency(self, valid_result, default_config):
        """Test result consistency validation"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create multiple results with slight variations
        results = []
        for i in range(5):
            result = BacktestResult(
                id=f"consistency-result-{i}",
                script_id="script-1",
                execution_id=f"exec-{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=45.2 + (i * 0.1),
                status="SUCCESS",
                exit_code=0,
                stdout="Backtest completed successfully",
                stderr="",
                performance_metrics={
                    "total_return_pct": 15.5 + (i * 0.01),  # Slight variation
                    "sharpe_ratio": 1.25 + (i * 0.001),
                    "max_drawdown_pct": 5.2 + (i * 0.01),
                    "win_rate": 0.65 + (i * 0.001),
                    "total_trades": 120,  # Exact match
                    "initial_capital": 10000.0,
                    "final_capital": 11550.0 + (i * 1.0)
                },
                trade_data=valid_result.trade_data,
                validation_errors=[],
                resource_usage=valid_result.resource_usage,
                created_at=datetime.now()
            )
            results.append(result)
        
        consistency_result = validator.validate_consistency(results, default_config)
        
        # Verify consistency validation
        assert consistency_result.is_consistent is True
        assert consistency_result.consistency_score >= 95.0
        assert len(consistency_result.inconsistencies) == 0
    
    def test_validate_result_inconsistency(self, default_config):
        """Test result inconsistency detection"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create inconsistent results
        results = []
        for i in range(3):
            result = BacktestResult(
                id=f"inconsistent-result-{i}",
                script_id="script-1",
                execution_id=f"exec-{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=45.2,
                status="SUCCESS",
                exit_code=0,
                stdout="Backtest completed successfully",
                stderr="",
                performance_metrics={
                    "total_return_pct": 15.5 + (i * 10.0),  # Large variations
                    "sharpe_ratio": 1.25 + (i * 0.5),
                    "max_drawdown_pct": 5.2 + (i * 2.0),
                    "win_rate": 0.65 + (i * 0.1),
                    "total_trades": 120 + (i * 50),  # Different trade counts
                    "initial_capital": 10000.0,
                    "final_capital": 11550.0 + (i * 1000.0)
                },
                trade_data=[],
                validation_errors=[],
                resource_usage={},
                created_at=datetime.now()
            )
            results.append(result)
        
        consistency_result = validator.validate_consistency(results, default_config)
        
        # Verify inconsistency detection
        assert consistency_result.is_consistent is False
        assert consistency_result.consistency_score < 70.0
        assert len(consistency_result.inconsistencies) > 0
    
    def test_validate_result_metrics_completeness(self, default_config):
        """Test validation of metrics completeness"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create result with missing metrics
        incomplete_result = BacktestResult(
            id="incomplete-result-1",
            script_id="script-1",
            execution_id="exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=45.2,
            status="SUCCESS",
            exit_code=0,
            stdout="Backtest completed",
            stderr="",
            performance_metrics={
                "total_return_pct": 15.5,
                # Missing sharpe_ratio, max_drawdown_pct, win_rate, total_trades
                "initial_capital": 10000.0,
                "final_capital": 11550.0
            },
            trade_data=[],
            validation_errors=[],
            resource_usage={},
            created_at=datetime.now()
        )
        
        validation_result = validator.validate_result(incomplete_result, default_config)
        
        # Verify missing metrics detection
        assert validation_result.is_valid is False
        error_messages = [error.message for error in validation_result.errors]
        assert any("missing required metric" in msg.lower() for msg in error_messages)
        assert any("sharpe_ratio" in msg.lower() for msg in error_messages)
        assert any("max_drawdown_pct" in msg.lower() for msg in error_messages)
    
    def test_validate_result_with_custom_config(self, valid_result):
        """Test validation with custom configuration"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create strict configuration
        strict_config = TestConfiguration(
            id="strict-config",
            name="Strict Configuration",
            description="Strict validation settings",
            tolerances={
                "returns_tolerance_pct": 0.01,  # Very strict
                "ratios_tolerance": 0.001,
                "drawdown_tolerance_pct": 0.01,
                "win_rate_tolerance_pct": 0.1
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
                "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate", "total_trades"]
            },
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 4,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        validation_result = validator.validate_result(valid_result, strict_config)
        
        # Verify strict validation
        assert validation_result.is_valid is True  # Should still pass with valid data
        assert validation_result.score >= 90.0
    
    def test_validate_result_performance_bounds(self, default_config):
        """Test validation of performance bounds"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create result with performance outside normal bounds
        extreme_result = BacktestResult(
            id="extreme-result-1",
            script_id="script-1",
            execution_id="exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=45.2,
            status="SUCCESS",
            exit_code=0,
            stdout="Backtest completed",
            stderr="",
            performance_metrics={
                "total_return_pct": 5000.0,  # 5000% return (impossible)
                "sharpe_ratio": 100.0,  # Unrealistic Sharpe
                "max_drawdown_pct": 200.0,  # 200% drawdown (impossible)
                "win_rate": 1.0,  # 100% win rate
                "total_trades": 1000000,  # Too many trades
                "initial_capital": 10000.0,
                "final_capital": 510000.0
            },
            trade_data=[],
            validation_errors=[],
            resource_usage={},
            created_at=datetime.now()
        )
        
        validation_result = validator.validate_result(extreme_result, default_config)
        
        # Verify extreme values detection
        assert validation_result.is_valid is False
        error_messages = [error.message for error in validation_result.errors]
        assert any("outside normal bounds" in msg.lower() for msg in error_messages)
        assert any("unrealistic" in msg.lower() for msg in error_messages)
    
    def test_validate_result_trade_data_validation(self, default_config):
        """Test validation of trade data"""
        # This test will FAIL until implementation is complete
        validator = ResultValidator()
        
        # Create result with invalid trade data
        invalid_trade_result = BacktestResult(
            id="invalid-trade-result-1",
            script_id="script-1",
            execution_id="exec-1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=45.2,
            status="SUCCESS",
            exit_code=0,
            stdout="Backtest completed",
            stderr="",
            performance_metrics={
                "total_return_pct": 15.5,
                "sharpe_ratio": 1.25,
                "max_drawdown_pct": 5.2,
                "win_rate": 0.65,
                "total_trades": 2,
                "initial_capital": 10000.0,
                "final_capital": 11550.0
            },
            trade_data=[
                {"symbol": "AAPL", "action": "BUY", "price": -150.0, "quantity": 100},  # Negative price
                {"symbol": "", "action": "SELL", "price": 155.0, "quantity": 0}  # Empty symbol, zero quantity
            ],
            validation_errors=[],
            resource_usage={},
            created_at=datetime.now()
        )
        
        validation_result = validator.validate_result(invalid_trade_result, default_config)
        
        # Verify trade data validation
        assert validation_result.is_valid is False
        error_messages = [error.message for error in validation_result.errors]
        assert any("invalid trade data" in msg.lower() for msg in error_messages)
        assert any("negative price" in msg.lower() for msg in error_messages)
        assert any("empty symbol" in msg.lower() for msg in error_messages)


if __name__ == "__main__":
    pytest.main([__file__])

