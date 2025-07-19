"""
Enhanced Logging System - Structured logging with performance tracking
Production-ready with log rotation, environment configuration, and monitoring
"""

import logging
import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_DIR = os.environ.get('LOG_DIR', 'logs')
MAX_LOG_SIZE = int(os.environ.get('MAX_LOG_SIZE_MB', '100')) * 1024 * 1024  # 100MB default
LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'environment': ENVIRONMENT,
            'pid': os.getpid()
        }
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        extra_fields = getattr(record, 'extra_fields', None)
        if extra_fields:
            log_entry.update(extra_fields)
        
        return json.dumps(log_entry)


class PerformanceLogger:
    """Performance tracking logger"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, Dict[str, Any]] = {}
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.metrics[timer_id] = {
            'operation': operation,
            'start_time': time.time(),
            'status': 'running'
        }
        return timer_id
    
    def end_timer(self, timer_id: str, success: bool = True, extra_data: Optional[Dict] = None):
        """End timing an operation"""
        if timer_id not in self.metrics:
            return
        
        end_time = time.time()
        metric = self.metrics[timer_id]
        duration = end_time - metric['start_time']
        
        metric.update({
            'end_time': end_time,
            'duration': duration,
            'success': success,
            'status': 'completed'
        })
        
        if extra_data:
            metric['extra_data'] = extra_data
        
        # Log performance metric
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Performance: {metric['operation']}", 
                       extra={'extra_fields': {'performance_metric': metric}})
        
        # Clean up
        del self.metrics[timer_id]


class TradingLogger:
    """Enhanced logger for trading system"""
    
    def __init__(self, name: str = "trading_system"):
        self.logger = logging.getLogger(name)
        self.performance_logger = PerformanceLogger(self.logger)
        
        # Set up handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers with production-ready configuration"""
        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Console handler with structured formatting (development)
        if ENVIRONMENT in ['development', 'test']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(console_handler)
        
        # Rotating file handler for main logs
        main_log_file = f"{LOG_DIR}/trading_system.log"
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        main_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(main_handler)
        
        # Rotating file handler for errors only
        error_log_file = f"{LOG_DIR}/errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(error_handler)
        
        # Daily rotating handler for performance logs
        perf_log_file = f"{LOG_DIR}/performance.log"
        perf_handler = TimedRotatingFileHandler(
            perf_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of performance logs
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(StructuredFormatter())
        # Add filter for performance logs only
        perf_handler.addFilter(lambda record: 'performance_metric' in getattr(record, 'extra_fields', {}))
        self.logger.addHandler(perf_handler)
        
        # Set log level based on environment
        log_level = getattr(logging, LOG_LEVEL, logging.INFO)
        self.logger.setLevel(log_level)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def info(self, message: str, extra_fields: Optional[Dict] = None):
        """Log info message with extra fields"""
        self.logger.info(message, extra={'extra_fields': extra_fields or {}})
    
    def warning(self, message: str, extra_fields: Optional[Dict] = None):
        """Log warning message with extra fields"""
        self.logger.warning(message, extra={'extra_fields': extra_fields or {}})
    
    def error(self, message: str, extra_fields: Optional[Dict] = None, exc_info: bool = True):
        """Log error message with extra fields and exception info"""
        self.logger.error(message, extra={'extra_fields': extra_fields or {}}, exc_info=exc_info)
    
    def critical(self, message: str, extra_fields: Optional[Dict] = None, exc_info: bool = True):
        """Log critical message with extra fields and exception info"""
        self.logger.critical(message, extra={'extra_fields': extra_fields or {}}, exc_info=exc_info)
    
    def debug(self, message: str, extra_fields: Optional[Dict] = None):
        """Log debug message with extra fields"""
        self.logger.debug(message, extra={'extra_fields': extra_fields or {}})
    
    def trade_signal(self, signal_data: Dict[str, Any]):
        """Log trading signal"""
        self.info("Trading signal generated", {
            'signal_type': 'trade_signal',
            'signal_data': signal_data
        })
    
    def order_executed(self, order_data: Dict[str, Any]):
        """Log order execution"""
        self.info("Order executed", {
            'event_type': 'order_executed',
            'order_data': order_data
        })
    
    def market_data_received(self, symbol: str, data_type: str, data_size: int):
        """Log market data reception"""
        self.info("Market data received", {
            'event_type': 'market_data',
            'symbol': symbol,
            'data_type': data_type,
            'data_size': data_size
        })
    
    def performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log performance metric"""
        self.info(f"Performance metric: {metric_name}", {
            'metric_type': 'performance',
            'metric_name': metric_name,
            'value': value,
            'unit': unit
        })
    
    def system_health(self, component: str, status: str, details: Optional[Dict] = None):
        """Log system health status"""
        self.info(f"System health: {component}", {
            'event_type': 'system_health',
            'component': component,
            'status': status,
            'details': details or {}
        })
    
    def security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.warning(f"Security event: {event_type}", {
            'event_type': 'security',
            'security_event_type': event_type,
            'details': details
        })
    
    def api_call(self, method: str, endpoint: str, status_code: int, duration: float, 
                 request_size: Optional[int] = None, response_size: Optional[int] = None):
        """Log API calls"""
        self.info(f"API call: {method} {endpoint}", {
            'event_type': 'api_call',
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration': duration,
            'request_size': request_size,
            'response_size': response_size
        })


def log_performance(operation_name: str):
    """Decorator to log performance of functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = TradingLogger()
            timer_id = logger.performance_logger.start_timer(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                logger.performance_logger.end_timer(timer_id, success=True)
                return result
            except Exception as e:
                logger.performance_logger.end_timer(timer_id, success=False, 
                                                  extra_data={'error': str(e)})
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = TradingLogger()
            timer_id = logger.performance_logger.start_timer(operation_name)
            
            try:
                result = func(*args, **kwargs)
                logger.performance_logger.end_timer(timer_id, success=True)
                return result
            except Exception as e:
                logger.performance_logger.end_timer(timer_id, success=False, 
                                                  extra_data={'error': str(e)})
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def log_errors(func: Callable) -> Callable:
    """Decorator to log errors with full context"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = TradingLogger()
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}", {
                'function': func.__name__,
                'module': func.__module__,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'args': str(args),
                'kwargs': str(kwargs)
            })
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = TradingLogger()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}", {
                'function': func.__name__,
                'module': func.__module__,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'args': str(args),
                'kwargs': str(kwargs)
            })
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def get_trading_logger() -> TradingLogger:
    """Get a trading logger instance"""
    return TradingLogger()


# Import asyncio for coroutine detection
import asyncio 