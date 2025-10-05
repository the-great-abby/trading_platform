"""
Backtest Test Validation Framework

A comprehensive framework for discovering, executing, and validating backtest scripts
to ensure they produce reliable and consistent results.
"""

__version__ = "1.0.0"
__author__ = "Trading System Team"

from .models import (
    BacktestScript,
    BacktestResult,
    ValidationReport,
    TestConfiguration
)

from .discovery import BacktestScriptDiscovery
from .execution import ScriptExecutor, BatchValidator
from .reporting import ReportGenerator
from .config import ConfigManager

__all__ = [
    "BacktestScript",
    "BacktestResult", 
    "ValidationReport",
    "TestConfiguration",
    "BacktestScriptDiscovery",
    "ScriptExecutor",
    "BatchValidator",
    "ReportGenerator",
    "ConfigManager"
]
