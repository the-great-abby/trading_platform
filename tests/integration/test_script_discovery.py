"""
Integration Tests for Script Discovery Service

Tests the script discovery functionality that automatically finds and catalogs
backtest scripts in the codebase.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

# This will fail until implementation is complete
from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.models.backtest_script import BacktestScript


class TestScriptDiscoveryIntegration:
    """Integration tests for script discovery"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with test scripts"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test backtest scripts
            test_scripts = [
                {
                    "name": "test_strategy_backtest.py",
                    "content": '''
"""
Test strategy backtest script
"""
import pandas as pd
import numpy as np

def run_backtest():
    """Run backtest for test strategy"""
    return {"total_return": 0.15, "sharpe_ratio": 1.2}

if __name__ == "__main__":
    run_backtest()
'''
                },
                {
                    "name": "iron_condor_backtest.py", 
                    "content": '''
"""
Iron condor options backtest
"""
def iron_condor_backtest():
    """Run iron condor backtest"""
    return {"total_return": 0.08, "max_drawdown": 0.05}

def run_iron_condor():
    return iron_condor_backtest()
'''
                },
                {
                    "name": "test_comprehensive_backtest.py",
                    "content": '''
"""
Comprehensive backtest suite
"""
class ComprehensiveBacktest:
    def run(self):
        return {"total_return": 0.12, "trades": 50}

def run_comprehensive():
    backtest = ComprehensiveBacktest()
    return backtest.run()
'''
                },
                {
                    "name": "regular_script.py",  # Should not be discovered
                    "content": '''
"""
Regular script - not a backtest
"""
def regular_function():
    return "not a backtest"
'''
                }
            ]
            
            for script in test_scripts:
                script_path = temp_path / script["name"]
                script_path.write_text(script["content"])
            
            yield temp_path
    
    def test_discover_scripts_in_directory(self, temp_directory):
        """Test discovering backtest scripts in a directory"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        scripts = discovery.discover_scripts_in_directory(temp_directory)
        
        # Should find 3 backtest scripts, not the regular script
        assert len(scripts) == 3
        
        # Verify script properties
        script_names = [script.name for script in scripts]
        assert "test_strategy_backtest" in script_names
        assert "iron_condor_backtest" in script_names  
        assert "test_comprehensive_backtest" in script_names
        assert "regular_script" not in script_names
    
    def test_script_metadata_extraction(self, temp_directory):
        """Test extraction of script metadata"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        scripts = discovery.discover_scripts_in_directory(temp_directory)
        
        for script in scripts:
            # Verify required fields are populated
            assert script.id is not None
            assert script.name is not None
            assert script.file_path is not None
            assert script.function_name is not None
            assert script.script_type is not None
            assert script.validation_status == "NEVER_RUN"
            assert script.created_at is not None
            
            # Verify file path exists and is readable
            assert Path(script.file_path).exists()
            assert Path(script.file_path).is_file()
            
            # Verify function name exists in script
            script_content = Path(script.file_path).read_text()
            assert script.function_name in script_content
    
    def test_script_type_classification(self, temp_directory):
        """Test automatic classification of script types"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        scripts = discovery.discover_scripts_in_directory(temp_directory)
        
        script_types = {}
        for script in scripts:
            script_types[script.name] = script.script_type
        
        # Verify script type classification
        assert script_types["test_strategy_backtest"] == "INDIVIDUAL_STRATEGY"
        assert script_types["iron_condor_backtest"] == "OPTIONS"
        assert script_types["test_comprehensive_backtest"] == "COMPREHENSIVE"
    
    def test_script_dependencies_extraction(self, temp_directory):
        """Test extraction of script dependencies"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        scripts = discovery.discover_scripts_in_directory(temp_directory)
        
        for script in scripts:
            # Verify dependencies are extracted
            assert isinstance(script.dependencies, list)
            
            # Check for common dependencies
            if "pandas" in script.dependencies or "numpy" in script.dependencies:
                assert "pandas" in script.dependencies
                assert "numpy" in script.dependencies
    
    def test_discover_scripts_with_filters(self, temp_directory):
        """Test script discovery with filters"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        # Test filtering by script type
        options_scripts = discovery.discover_scripts(
            directory=temp_directory,
            script_type="OPTIONS"
        )
        assert len(options_scripts) == 1
        assert options_scripts[0].script_type == "OPTIONS"
        
        # Test filtering by status
        never_run_scripts = discovery.discover_scripts(
            directory=temp_directory,
            status="NEVER_RUN"
        )
        assert len(never_run_scripts) == 3
        
        # Test filtering by name pattern
        strategy_scripts = discovery.discover_scripts(
            directory=temp_directory,
            name_pattern="*strategy*"
        )
        assert len(strategy_scripts) == 1
        assert "strategy" in strategy_scripts[0].name.lower()
    
    def test_script_discovery_error_handling(self):
        """Test error handling in script discovery"""
        # This test will FAIL until implementation is complete
        discovery = BacktestScriptDiscovery()
        
        # Test with non-existent directory
        with pytest.raises(FileNotFoundError):
            discovery.discover_scripts_in_directory(Path("/non/existent/directory"))
        
        # Test with file instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(ValueError):
                discovery.discover_scripts_in_directory(Path(temp_file.name))
    
    def test_script_discovery_performance(self, temp_directory):
        """Test performance of script discovery with many files"""
        # This test will FAIL until implementation is complete
        import time
        
        # Create many test scripts
        for i in range(100):
            script_path = temp_directory / f"test_script_{i}_backtest.py"
            script_path.write_text(f'''
def run_backtest_{i}():
    return {{"total_return": 0.{i:02d}}}

if __name__ == "__main__":
    run_backtest_{i}()
''')
        
        discovery = BacktestScriptDiscovery()
        
        start_time = time.time()
        scripts = discovery.discover_scripts_in_directory(temp_directory)
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds)
        assert end_time - start_time < 5.0
        assert len(scripts) == 103  # 3 original + 100 new
    
    def test_script_discovery_concurrent_access(self, temp_directory):
        """Test concurrent access to script discovery"""
        # This test will FAIL until implementation is complete
        import threading
        import time
        
        discovery = BacktestScriptDiscovery()
        results = []
        errors = []
        
        def discover_scripts():
            try:
                scripts = discovery.discover_scripts_in_directory(temp_directory)
                results.append(len(scripts))
            except Exception as e:
                errors.append(e)
        
        # Run discovery in multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=discover_scripts)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should not have errors
        assert len(errors) == 0
        
        # All threads should get same result
        assert all(result == results[0] for result in results)
        assert results[0] == 3


if __name__ == "__main__":
    pytest.main([__file__])











