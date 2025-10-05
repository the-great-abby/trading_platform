"""
Logging integration with existing trading system logging

This service provides structured logging configuration that integrates
with the existing trading system logging infrastructure.
"""

import logging
import logging.config
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class ValidationLogger:
    """
    Structured logging configuration for the validation framework.
    """
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self.logger_config = self._create_logger_config()
        
        # Configure logging
        logging.config.dictConfig(self.logger_config)
        
        # Create main logger
        self.logger = logging.getLogger("validation_framework")
    
    def _create_logger_config(self) -> Dict[str, Any]:
        """Create logging configuration dictionary."""
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "()": "src.validation.integration.logging_config.JSONFormatter",
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "validation_framework": {
                    "level": self.log_level,
                    "handlers": ["console"],
                    "propagate": False
                },
                "validation_framework.discovery": {
                    "level": self.log_level,
                    "handlers": ["console"],
                    "propagate": False
                },
                "validation_framework.execution": {
                    "level": self.log_level,
                    "handlers": ["console"],
                    "propagate": False
                },
                "validation_framework.validation": {
                    "level": self.log_level,
                    "handlers": ["console"],
                    "propagate": False
                },
                "validation_framework.integration": {
                    "level": self.log_level,
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"]
            }
        }
        
        # Add file handler if log file specified
        if self.log_file:
            config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": self.log_level,
                "formatter": "detailed",
                "filename": self.log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
            
            # Add file handler to all loggers
            for logger_name in config["loggers"]:
                config["loggers"][logger_name]["handlers"].append("file")
        
        return config
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance."""
        return logging.getLogger(f"validation_framework.{name}")
    
    def log_validation_start(self, script_id: str, script_name: str) -> None:
        """Log validation start event."""
        self.logger.info(f"Validation started - Script: {script_name} (ID: {script_id})")
    
    def log_validation_complete(self, script_id: str, script_name: str, status: str, duration: float) -> None:
        """Log validation completion event."""
        self.logger.info(f"Validation completed - Script: {script_name} (ID: {script_id}) - Status: {status} - Duration: {duration:.2f}s")
    
    def log_batch_start(self, script_count: int, batch_id: str) -> None:
        """Log batch validation start event."""
        self.logger.info(f"Batch validation started - Scripts: {script_count} - Batch ID: {batch_id}")
    
    def log_batch_complete(self, batch_id: str, results: Dict[str, int]) -> None:
        """Log batch validation completion event."""
        self.logger.info(f"Batch validation completed - Batch ID: {batch_id} - Results: {results}")
    
    def log_discovery(self, directory: str, script_count: int) -> None:
        """Log script discovery event."""
        self.logger.info(f"Script discovery completed - Directory: {directory} - Scripts found: {script_count}")
    
    def log_database_operation(self, operation: str, table: str, record_id: str = None) -> None:
        """Log database operation event."""
        record_info = f" (ID: {record_id})" if record_id else ""
        self.logger.debug(f"Database operation - {operation} on {table}{record_info}")
    
    def log_performance_metrics(self, script_id: str, metrics: Dict[str, Any]) -> None:
        """Log performance metrics."""
        self.logger.info(f"Performance metrics - Script: {script_id} - Return: {metrics.get('total_return_pct', 0):.2f}% - Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None) -> None:
        """Log error event with context."""
        context_str = f" - Context: {context}" if context else ""
        self.logger.error(f"Error - Type: {error_type} - Message: {error_message}{context_str}")
    
    def log_warning(self, warning_type: str, warning_message: str, context: Dict[str, Any] = None) -> None:
        """Log warning event with context."""
        context_str = f" - Context: {context}" if context else ""
        self.logger.warning(f"Warning - Type: {warning_type} - Message: {warning_message}{context_str}")


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class ValidationMetrics:
    """
    Metrics collection for validation framework operations.
    """
    
    def __init__(self, logger: ValidationLogger):
        self.logger = logger
        self.metrics = {
            "validations_started": 0,
            "validations_completed": 0,
            "validations_failed": 0,
            "scripts_discovered": 0,
            "database_operations": 0,
            "batch_validations": 0,
            "average_validation_time": 0.0,
            "total_validation_time": 0.0
        }
    
    def increment_validation_started(self) -> None:
        """Increment validation started counter."""
        self.metrics["validations_started"] += 1
        self.logger.logger.debug(f"Metrics - Validations started: {self.metrics['validations_started']}")
    
    def increment_validation_completed(self) -> None:
        """Increment validation completed counter."""
        self.metrics["validations_completed"] += 1
        self.logger.logger.debug(f"Metrics - Validations completed: {self.metrics['validations_completed']}")
    
    def increment_validation_failed(self) -> None:
        """Increment validation failed counter."""
        self.metrics["validations_failed"] += 1
        self.logger.logger.debug(f"Metrics - Validations failed: {self.metrics['validations_failed']}")
    
    def increment_scripts_discovered(self, count: int) -> None:
        """Increment scripts discovered counter."""
        self.metrics["scripts_discovered"] += count
        self.logger.logger.debug(f"Metrics - Scripts discovered: {self.metrics['scripts_discovered']}")
    
    def increment_database_operations(self) -> None:
        """Increment database operations counter."""
        self.metrics["database_operations"] += 1
        self.logger.logger.debug(f"Metrics - Database operations: {self.metrics['database_operations']}")
    
    def increment_batch_validations(self) -> None:
        """Increment batch validations counter."""
        self.metrics["batch_validations"] += 1
        self.logger.logger.debug(f"Metrics - Batch validations: {self.metrics['batch_validations']}")
    
    def record_validation_time(self, duration: float) -> None:
        """Record validation execution time."""
        self.metrics["total_validation_time"] += duration
        
        if self.metrics["validations_completed"] > 0:
            self.metrics["average_validation_time"] = (
                self.metrics["total_validation_time"] / self.metrics["validations_completed"]
            )
        
        self.logger.logger.debug(f"Metrics - Average validation time: {self.metrics['average_validation_time']:.2f}s")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        success_rate = 0.0
        if self.metrics["validations_started"] > 0:
            success_rate = self.metrics["validations_completed"] / self.metrics["validations_started"]
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        for key in self.metrics:
            if isinstance(self.metrics[key], (int, float)):
                self.metrics[key] = 0
        self.logger.logger.info("Metrics reset")


def setup_validation_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> ValidationLogger:
    """
    Set up validation framework logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        ValidationLogger instance
    """
    return ValidationLogger(log_level, log_file)


def get_validation_logger(name: str) -> logging.Logger:
    """
    Get a validation framework logger.
    
    Args:
        name: Logger name (will be prefixed with 'validation_framework.')
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"validation_framework.{name}")
