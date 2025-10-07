"""
Integration Tests for Backtest Validation

Tests the integration of the validation framework with existing backtest
scripts to ensure they produce reliable and consistent results.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

# This will fail until implementation is complete
from src.validation.execution import BacktestValidator
from src.validation.discovery import BacktestScriptDiscovery
from src.validation.models.backtest_result import BacktestResult


class TestBacktestValidationIntegration:
    """Integration tests for backtest validation"""
    
    @pytest.fixture
    def sample_backtest_script(self):
        """Create a sample backtest script for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Sample backtest script for validation testing
"""
import sys
import json
import time
import random
from datetime import datetime

def run_backtest():
    """Run a sample backtest"""
    # Simulate backtest execution
    time.sleep(0.1)
    
    # Generate realistic backtest results
    results = {
        "total_return_pct": round(random.uniform(5.0, 25.0), 2),
        "sharpe_ratio": round(random.uniform(0.8, 2.0), 2),
        "max_drawdown_pct": round(random.uniform(3.0, 12.0), 2),
        "win_rate": round(random.uniform(0.45, 0.75), 2),
        "total_trades": random.randint(50, 200),
        "initial_capital": 10000.0,
        "final_capital": round(10000.0 * (1 + random.uniform(0.05, 0.25)), 2),
        "execution_time": time.time(),
        "strategy_name": "SampleStrategy",
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    
    # Print results as JSON
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
    def inconsistent_backtest_script(self):
        """Create a backtest script that produces inconsistent results"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Inconsistent backtest script for testing validation
"""
import sys
import json
import time
import random

def run_backtest():
    """Run an inconsistent backtest"""
    time.sleep(0.1)
    
    # Generate inconsistent results (using current time for variation)
    current_time = time.time()
    results = {
        "total_return_pct": round(random.uniform(5.0, 25.0) + (current_time % 10), 2),
        "sharpe_ratio": round(random.uniform(0.8, 2.0) + (current_time % 5), 2),
        "max_drawdown_pct": round(random.uniform(3.0, 12.0) + (current_time % 3), 2),
        "win_rate": round(random.uniform(0.45, 0.75) + (current_time % 2), 2),
        "total_trades": random.randint(50, 200) + int(current_time % 20),
        "initial_capital": 10000.0,
        "final_capital": round(10000.0 * (1 + random.uniform(0.05, 0.25) + (current_time % 5)), 2),
        "execution_time": current_time
    }
    
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
    
    def test_discover_and_validate_backtest_scripts(self, sample_backtest_script):
        """Test discovering and validating backtest scripts"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Discover scripts in directory containing our test script
        script_dir = sample_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        
        # Should find our test script
        assert len(scripts) == 1
        script = scripts[0]
        assert script.file_path == str(sample_backtest_script)
        
        # Validate the script
        result = validator.validate_script(script)
        
        # Verify validation result
        assert isinstance(result, BacktestResult)
        assert result.script_id == script.id
        assert result.status == "SUCCESS"
        assert result.performance_metrics is not None
        
        # Verify performance metrics are reasonable
        metrics = result.performance_metrics
        assert 0.0 <= metrics["total_return_pct"] <= 100.0
        assert 0.0 <= metrics["sharpe_ratio"] <= 10.0
        assert 0.0 <= metrics["max_drawdown_pct"] <= 100.0
        assert 0.0 <= metrics["win_rate"] <= 1.0
        assert metrics["total_trades"] > 0
        assert metrics["initial_capital"] > 0
        assert metrics["final_capital"] > 0
    
    def test_validate_script_consistency(self, sample_backtest_script):
        """Test script validation consistency across multiple runs"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Discover the script
        script_dir = sample_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        script = scripts[0]
        
        # Run validation multiple times
        results = []
        for i in range(5):
            result = validator.validate_script(script)
            results.append(result)
        
        # Verify all runs succeeded
        assert all(result.status == "SUCCESS" for result in results)
        
        # Verify consistency (results should be similar)
        first_result = results[0]
        for result in results[1:]:
            # Trade count should be exactly the same (deterministic)
            assert result.performance_metrics["total_trades"] == first_result.performance_metrics["total_trades"]
            
            # Other metrics should be within reasonable tolerance
            assert abs(result.performance_metrics["total_return_pct"] - 
                      first_result.performance_metrics["total_return_pct"]) < 0.1
    
    def test_validate_script_inconsistency_detection(self, inconsistent_backtest_script):
        """Test detection of inconsistent script results"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Discover the inconsistent script
        script_dir = inconsistent_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        script = scripts[0]
        
        # Run validation multiple times
        results = []
        for i in range(5):
            result = validator.validate_script(script)
            results.append(result)
        
        # Verify all runs succeeded
        assert all(result.status == "SUCCESS" for result in results)
        
        # Check for inconsistency
        first_result = results[0]
        inconsistencies_found = False
        
        for result in results[1:]:
            # Check if results are significantly different
            if abs(result.performance_metrics["total_return_pct"] - 
                   first_result.performance_metrics["total_return_pct"]) > 5.0:
                inconsistencies_found = True
                break
        
        # Should detect inconsistencies
        assert inconsistencies_found
    
    def test_validate_script_with_existing_backtest_engine(self):
        """Test validation with existing backtest engine integration"""
        # This test will FAIL until implementation is complete
        validator = BacktestValidator()
        
        # Test with a mock script that uses the existing backtest engine
        # This would integrate with src/backtesting/engine/backtest_engine.py
        
        # For now, we'll test that the validator can handle engine integration
        assert validator is not None  # Placeholder test
    
    def test_validate_script_error_handling(self):
        """Test error handling in script validation"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Test with non-existent directory
        with pytest.raises(FileNotFoundError):
            discovery.discover_scripts_in_directory(Path("/non/existent/directory"))
        
        # Test with invalid script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def invalid_backtest():
    raise ValueError("Invalid backtest")

if __name__ == "__main__":
    invalid_backtest()
''')
            temp_path = Path(f.name)
        
        try:
            script_dir = temp_path.parent
            scripts = discovery.discover_scripts_in_directory(script_dir)
            
            if scripts:
                script = scripts[0]
                result = validator.validate_script(script)
                
                # Should handle error gracefully
                assert result.status in ["FAILED", "ERROR"]
                assert result.validation_errors is not None
                assert len(result.validation_errors) > 0
        
        finally:
            # Cleanup
            temp_path.unlink()
    
    def test_validate_script_performance_requirements(self, sample_backtest_script):
        """Test that script validation meets performance requirements"""
        # This test will FAIL until implementation is complete
        import time
        
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Discover the script
        script_dir = sample_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        script = scripts[0]
        
        # Measure validation time
        start_time = time.time()
        result = validator.validate_script(script)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Should complete within reasonable time (< 30 seconds for simple script)
        assert validation_time < 30.0
        
        # Should still produce valid result
        assert result.status == "SUCCESS"
    
    def test_validate_script_resource_usage(self, sample_backtest_script):
        """Test resource usage tracking during script validation"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Discover the script
        script_dir = sample_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        script = scripts[0]
        
        # Validate script
        result = validator.validate_script(script)
        
        # Verify resource usage is tracked
        assert result.resource_usage is not None
        assert "peak_memory_mb" in result.resource_usage
        assert "average_cpu_percent" in result.resource_usage
        
        # Verify resource usage is reasonable
        assert result.resource_usage["peak_memory_mb"] < 1000  # Less than 1GB
        assert result.resource_usage["average_cpu_percent"] < 100  # Less than 100% CPU
    
    def test_validate_script_with_different_types(self):
        """Test validation of different types of backtest scripts"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        validator = BacktestValidator()
        
        # Test with different script types
        script_types = ["INDIVIDUAL_STRATEGY", "OPTIONS", "COMPREHENSIVE", "MULTI_STRATEGY"]
        
        for script_type in script_types:
            # Create a test script for each type
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{script_type.lower()}_backtest.py', delete=False) as f:
                f.write(f'''
"""
{script_type} backtest script
"""
import sys
import json

def run_backtest():
    results = {{
        "total_return_pct": 10.0,
        "sharpe_ratio": 1.0,
        "max_drawdown_pct": 5.0,
        "win_rate": 0.6,
        "total_trades": 100,
        "initial_capital": 10000.0,
        "final_capital": 11000.0,
        "script_type": "{script_type}"
    }}
    print(json.dumps(results))
    return results

if __name__ == "__main__":
    run_backtest()
''')
                temp_path = Path(f.name)
            
            try:
                # Discover and validate
                script_dir = temp_path.parent
                scripts = discovery.discover_scripts_in_directory(script_dir)
                
                if scripts:
                    script = scripts[0]
                    assert script.script_type == script_type
                    
                    result = validator.validate_script(script)
                    assert result.status == "SUCCESS"
            
            finally:
                # Cleanup
                temp_path.unlink()
    
    def test_validate_script_integration_with_pytest(self, sample_backtest_script):
        """Test integration with pytest framework"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        # Discover the script
        script_dir = sample_backtest_script.parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        
        # Should be discoverable by pytest plugin
        assert len(scripts) == 1
        
        script = scripts[0]
        
        # Script should have proper metadata for pytest integration
        assert script.function_name is not None
        assert script.file_path is not None
        assert script.script_type is not None
        
        # Should be able to run as pytest test
        # This would be tested with the pytest plugin implementation


if __name__ == "__main__":
    pytest.main([__file__])











