"""
Risk Management Logging Configuration

Structured logging configuration for the comprehensive risk management framework.
Provides consistent logging across all risk management components.
"""

import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class RiskLoggingFormatter(logging.Formatter):
    """Custom formatter for risk management logs."""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        """
        Initialize risk logging formatter.
        
        Args:
            include_timestamp: Whether to include timestamp in logs
            include_level: Whether to include log level in logs
        """
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        
        # Create base format
        format_parts = []
        if include_timestamp:
            format_parts.append("%(asctime)s")
        if include_level:
            format_parts.append("[%(levelname)s]")
        format_parts.extend([
            "%(name)s",
            "%(funcName)s:%(lineno)d",
            "- %(message)s"
        ])
        
        super().__init__(fmt=" ".join(format_parts))
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with risk-specific information."""
        # Add risk-specific fields
        if hasattr(record, 'portfolio_id'):
            record.msg = f"[Portfolio: {record.portfolio_id}] {record.msg}"
        if hasattr(record, 'calculation_id'):
            record.msg = f"[Calc: {record.calculation_id}] {record.msg}"
        if hasattr(record, 'service'):
            record.msg = f"[Service: {record.service}] {record.msg}"
        
        return super().format(record)


class RiskJSONFormatter(logging.Formatter):
    """JSON formatter for structured risk management logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add risk-specific fields
        if hasattr(record, 'portfolio_id'):
            log_entry['portfolio_id'] = record.portfolio_id
        if hasattr(record, 'calculation_id'):
            log_entry['calculation_id'] = record.calculation_id
        if hasattr(record, 'service'):
            log_entry['service'] = record.service
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class RiskLoggingConfig:
    """Risk management logging configuration."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        json_format: bool = False,
        console_output: bool = True
    ):
        """
        Initialize risk logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            json_format: Whether to use JSON format for logs
            console_output: Whether to output to console
        """
        self.log_level = log_level
        self.log_file = log_file
        self.json_format = json_format
        self.console_output = console_output
        
        # Create logs directory if needed
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def configure_logging(self) -> None:
        """Configure logging for risk management framework."""
        # Create formatters
        if self.json_format:
            formatter = RiskJSONFormatter()
            console_formatter = RiskJSONFormatter()
        else:
            formatter = RiskLoggingFormatter()
            console_formatter = RiskLoggingFormatter()
        
        # Create handlers
        handlers = {}
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            handlers['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.log_level,
                'formatter': 'console_formatter',
                'stream': 'ext://sys.stdout'
            }
        
        # File handler
        if self.log_file:
            handlers['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.log_level,
                'formatter': 'file_formatter',
                'filename': self.log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        
        # Create logging configuration
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'console_formatter': {
                    '()': RiskLoggingFormatter,
                    'include_timestamp': True,
                    'include_level': True
                },
                'file_formatter': {
                    '()': RiskJSONFormatter if self.json_format else RiskLoggingFormatter,
                }
            },
            'handlers': handlers,
            'loggers': {
                '': {  # Root logger
                    'level': self.log_level,
                    'handlers': list(handlers.keys()),
                    'propagate': False
                },
                'src.risk': {
                    'level': self.log_level,
                    'handlers': list(handlers.keys()),
                    'propagate': False
                },
                'uvicorn': {
                    'level': 'INFO',
                    'handlers': list(handlers.keys()),
                    'propagate': False
                },
                'fastapi': {
                    'level': 'INFO',
                    'handlers': list(handlers.keys()),
                    'propagate': False
                }
            }
        }
        
        # Apply configuration
        logging.config.dictConfig(logging_config)
        
        # Set up risk-specific loggers
        self._setup_risk_loggers()
    
    def _setup_risk_loggers(self) -> None:
        """Set up risk-specific loggers."""
        # Risk calculation logger
        risk_calc_logger = logging.getLogger('src.risk.calculations')
        risk_calc_logger.setLevel(self.log_level)
        
        # Risk monitoring logger
        risk_monitor_logger = logging.getLogger('src.risk.monitoring')
        risk_monitor_logger.setLevel(self.log_level)
        
        # Risk integration logger
        risk_integration_logger = logging.getLogger('src.risk.integrations')
        risk_integration_logger.setLevel(self.log_level)
        
        # Risk API logger
        risk_api_logger = logging.getLogger('src.risk.api')
        risk_api_logger.setLevel(self.log_level)


class RiskLogger:
    """Risk management logger with context-aware logging."""
    
    def __init__(self, name: str):
        """
        Initialize risk logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs) -> None:
        """
        Set logging context.
        
        Args:
            **kwargs: Context variables
        """
        self.context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear logging context."""
        self.context.clear()
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """
        Log message with context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional log attributes
        """
        # Merge context and additional kwargs
        log_attrs = {**self.context, **kwargs}
        
        # Create log record with context
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        
        # Add context attributes to record
        for key, value in log_attrs.items():
            setattr(record, key, value)
        
        # Handle the record
        self.logger.handle(record)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self._log_with_context(logging.ERROR, message, exc_info=True, **kwargs)


# Global logging configuration
_logging_config = None


def configure_risk_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    console_output: bool = True
) -> RiskLoggingConfig:
    """
    Configure risk management logging.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        json_format: Whether to use JSON format
        console_output: Whether to output to console
        
    Returns:
        RiskLoggingConfig instance
    """
    global _logging_config
    
    _logging_config = RiskLoggingConfig(
        log_level=log_level,
        log_file=log_file,
        json_format=json_format,
        console_output=console_output
    )
    
    _logging_config.configure_logging()
    return _logging_config


def get_risk_logger(name: str) -> RiskLogger:
    """
    Get risk logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        RiskLogger instance
    """
    return RiskLogger(name)


def get_logging_config() -> Optional[RiskLoggingConfig]:
    """
    Get current logging configuration.
    
    Returns:
        RiskLoggingConfig instance or None
    """
    return _logging_config


# Logging decorators
def log_execution_time(logger: RiskLogger, operation: str):
    """Decorator to log execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.info(f"Starting {operation}")
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(f"Completed {operation}", duration_ms=duration)
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.error(f"Failed {operation}", duration_ms=duration, error=str(e))
                raise
        
        return wrapper
    return decorator


def log_portfolio_operation(logger: RiskLogger, portfolio_id: str):
    """Decorator to log portfolio operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.set_context(portfolio_id=portfolio_id)
            logger.info(f"Starting portfolio operation: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed portfolio operation: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Failed portfolio operation: {func.__name__}", error=str(e))
                raise
            finally:
                logger.clear_context()
        
        return wrapper
    return decorator


def log_risk_calculation(logger: RiskLogger, calculation_type: str):
    """Decorator to log risk calculations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            calculation_id = f"{calculation_type}_{int(datetime.utcnow().timestamp())}"
            logger.set_context(calculation_id=calculation_id, calculation_type=calculation_type)
            logger.info(f"Starting risk calculation: {calculation_type}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed risk calculation: {calculation_type}")
                return result
            except Exception as e:
                logger.error(f"Failed risk calculation: {calculation_type}", error=str(e))
                raise
            finally:
                logger.clear_context()
        
        return wrapper
    return decorator

