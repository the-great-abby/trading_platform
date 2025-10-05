"""
Strategy Engine Testing Framework

Comprehensive testing framework for trading strategies to ensure correct execution
during backtesting, with focus on Elliott Wave, Adaptive Wave, Ichimoku, and other
advanced strategies.

This framework provides:
- Strategy interface validation
- Signal generation testing
- Performance benchmarking
- Ensemble strategy coordination
- Mock data generation
- Comprehensive test suites
"""

from .api import app, testing_router
from .services import (
    StrategyValidator, SignalValidator, PerformanceValidator,
    MockDataGenerator
)
from .models import *
from .config import get_config, TestingConfig
from .database import init_database, get_database

__version__ = "1.0.0"
__author__ = "Trading System Team"

__all__ = [
    # API
    'app',
    'testing_router',
    
    # Services
    'StrategyValidator',
    'SignalValidator', 
    'PerformanceValidator',
    'MockDataGenerator',
    
    # Models (imported from models.__init__)
    
    # Configuration
    'get_config',
    'TestingConfig',
    
    # Database
    'init_database',
    'get_database'
]
