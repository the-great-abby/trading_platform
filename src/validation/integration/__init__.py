"""
Integration services for external systems

This package provides integration services for connecting the validation
framework to external systems like databases, monitoring, and logging.
"""

from .database_adapter import DatabaseAdapter
from .health_check import HealthChecker
from .env_manager import EnvironmentManager
from .error_handler import ErrorHandler, DatabaseRetryHandler, CircuitBreaker
from .logging_config import ValidationLogger, ValidationMetrics, setup_validation_logging, get_validation_logger
from .metrics_collector import (
    MetricsCollector, get_metrics_collector, 
    record_validation_metric, record_discovery_metric, 
    record_database_metric, record_batch_metric
)

__all__ = [
    "DatabaseAdapter", 
    "HealthChecker", 
    "EnvironmentManager",
    "ErrorHandler",
    "DatabaseRetryHandler", 
    "CircuitBreaker",
    "ValidationLogger",
    "ValidationMetrics",
    "setup_validation_logging",
    "get_validation_logger",
    "MetricsCollector",
    "get_metrics_collector",
    "record_validation_metric",
    "record_discovery_metric", 
    "record_database_metric",
    "record_batch_metric"
]
