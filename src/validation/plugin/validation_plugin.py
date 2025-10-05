"""
Pytest plugin for backtest validation framework

This plugin provides custom test collection and execution for backtest scripts,
enabling automated validation of backtest reliability and consistency.
"""

import pytest
import asyncio
from typing import List, Optional
from pathlib import Path
import logging

from ..discovery import BacktestScriptDiscovery
from ..execution import ScriptExecutor
from ..models.backtest_script import BacktestScript
from ..models.test_configuration import TestConfiguration

logger = logging.getLogger(__name__)


class ValidationPlugin:
    """Pytest plugin for backtest validation"""
    
    def __init__(self):
        self.discovery = BacktestScriptDiscovery()
        self.executor = ScriptExecutor()
        self.discovered_scripts: List[BacktestScript] = []
        self.validation_results = []
        self.configuration = None
    
    def pytest_configure(self, config):
        """Configure the plugin"""
        # Register custom markers
        config.addinivalue_line(
            "markers", "backtest_validation: mark test as backtest validation"
        )
        config.addinivalue_line(
            "markers", "validation_skip: skip backtest validation"
        )
        
        # Load default configuration
        try:
            from ..config import ConfigManager
            config_manager = ConfigManager()
            self.configuration = config_manager.get_default_configuration()
            if not self.configuration:
                self.configuration = config_manager.create_default_configuration()
        except Exception as e:
            logger.warning(f"Failed to load configuration: {e}")
            self.configuration = TestConfiguration(name="Default")
    
    def pytest_collect_file(self, path, parent):
        """Collect backtest scripts for validation"""
        if self._is_backtest_script(path):
            return BacktestScriptCollector.from_parent(parent, fspath=path)
        return None
    
    def _is_backtest_script(self, path: Path) -> bool:
        """Check if file is a backtest script"""
        # Skip test files to avoid recursion
        if path.name.startswith('test_'):
            return False
        
        patterns = [
            "*backtest*.py",
            "*_backtest.py", 
            "*_simulation*.py",
            "*_strategy*.py"
        ]
        
        for pattern in patterns:
            if path.match(pattern):
                return True
        
        # Check function names in file
        try:
            with open(path, 'r') as f:
                content = f.read()
                if ('backtest' in content.lower() and 'def ' in content and
                    not content.strip().startswith('#')):
                    return True
        except Exception as e:
            logger.debug(f"Could not read file {path}: {e}")
        
        return False


class BacktestScriptCollector(pytest.File):
    """Collector for backtest script files"""
    
    def collect(self):
        """Collect test items from backtest script"""
        yield BacktestValidationItem.from_parent(self, name="backtest_validation")


class BacktestValidationItem(pytest.Item):
    """Test item for backtest validation"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.script_path = parent.fspath
        self.discovery = BacktestScriptDiscovery()
        self.executor = ScriptExecutor()
    
    def runtest(self):
        """Run backtest validation"""
        # Skip if validation is disabled
        if self.hasmarker(pytest.mark.validation_skip):
            pytest.skip("Backtest validation skipped")
        
        # Discover script metadata
        try:
            scripts = self.discovery.discover_scripts_in_directory(self.script_path.parent)
            script = next((s for s in scripts if s.file_path == str(self.script_path)), None)
            
            if not script:
                pytest.skip(f"No backtest script found at {self.script_path}")
            
            # Execute script validation
            result = self.executor.execute_script(script)
            
            # Validate results
            if result.status != "SUCCESS":
                pytest.fail(f"Backtest execution failed: {result.stderr}")
            
            # Check for validation errors
            if result.validation_errors:
                error_messages = [e.message for e in result.validation_errors if e.severity == "ERROR"]
                if error_messages:
                    pytest.fail(f"Validation errors: {'; '.join(error_messages)}")
            
            # Check performance metrics are reasonable
            if result.performance_metrics:
                metrics = result.performance_metrics
                
                # Basic sanity checks
                if metrics.total_return_pct > 10000:  # 10000% return
                    pytest.fail(f"Unrealistic return: {metrics.total_return_pct}%")
                
                if metrics.sharpe_ratio > 50:  # Very high Sharpe
                    pytest.fail(f"Unrealistic Sharpe ratio: {metrics.sharpe_ratio}")
                
                if metrics.max_drawdown_pct > 100:  # 100% drawdown
                    pytest.fail(f"Invalid drawdown: {metrics.max_drawdown_pct}%")
                
                if metrics.win_rate > 1.0:  # Win rate > 100%
                    pytest.fail(f"Invalid win rate: {metrics.win_rate}")
                
                if metrics.total_trades < 0:
                    pytest.fail(f"Negative trade count: {metrics.total_trades}")
        
        except Exception as e:
            pytest.fail(f"Backtest validation error: {e}")
    
    def repr_failure(self, excinfo):
        """Representation of test failure"""
        return f"Backtest validation failed for {self.script_path}: {excinfo.value}"


def pytest_configure(config):
    """Configure pytest with validation plugin"""
    if not hasattr(config, 'validation_plugin'):
        config.validation_plugin = ValidationPlugin()
        config.pluginmanager.register(config.validation_plugin)


def pytest_collection_modifyitems(config, items):
    """Modify collected items for validation"""
    for item in items:
        if isinstance(item, BacktestValidationItem):
            item.add_marker(pytest.mark.backtest_validation)


def pytest_addoption(parser):
    """Add command line options for validation plugin"""
    group = parser.getgroup("backtest validation", "backtest validation options")
    
    group.addoption(
        "--validation-skip",
        action="store_true",
        default=False,
        help="Skip backtest validation tests"
    )
    
    group.addoption(
        "--validation-config",
        type=str,
        help="Path to validation configuration file"
    )
    
    group.addoption(
        "--validation-timeout",
        type=int,
        default=300,
        help="Timeout for backtest validation (seconds)"
    )


def pytest_configure(config):
    """Configure pytest with validation options"""
    if config.getoption("--validation-skip"):
        # Add skip marker to all validation items
        def skip_validation(item):
            if isinstance(item, BacktestValidationItem):
                item.add_marker(pytest.mark.validation_skip)
        
        config.hook.pytest_collection_modifyitems(items=config.items, config=config)
        for item in config.items:
            skip_validation(item)
