"""
Logging Configuration for Trading System
Centralized configuration for all logging settings
"""

import os
from typing import Dict, Any

# Environment-based configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_DIR = os.environ.get('LOG_DIR', 'logs')

# Log file settings
MAX_LOG_SIZE_MB = int(os.environ.get('MAX_LOG_SIZE_MB', '100'))
LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))
PERFORMANCE_LOG_DAYS = int(os.environ.get('PERFORMANCE_LOG_DAYS', '30'))

# Logging configuration by environment
LOGGING_CONFIG = {
    'development': {
        'console_logging': True,
        'file_logging': True,
        'log_level': 'DEBUG',
        'max_log_size': MAX_LOG_SIZE_MB * 1024 * 1024,
        'backup_count': LOG_BACKUP_COUNT,
        'performance_log_days': PERFORMANCE_LOG_DAYS
    },
    'test': {
        'console_logging': True,
        'file_logging': True,
        'log_level': 'INFO',
        'max_log_size': 10 * 1024 * 1024,  # 10MB for tests
        'backup_count': 2,
        'performance_log_days': 7
    },
    'production': {
        'console_logging': False,
        'file_logging': True,
        'log_level': 'INFO',
        'max_log_size': MAX_LOG_SIZE_MB * 1024 * 1024,
        'backup_count': LOG_BACKUP_COUNT,
        'performance_log_days': PERFORMANCE_LOG_DAYS
    }
}

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration for current environment"""
    return LOGGING_CONFIG.get(ENVIRONMENT, LOGGING_CONFIG['development'])

def get_log_level() -> str:
    """Get log level for current environment"""
    config = get_logging_config()
    return LOG_LEVEL if LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] else config['log_level']

def should_log_to_console() -> bool:
    """Check if console logging is enabled"""
    config = get_logging_config()
    return config['console_logging']

def get_log_file_settings() -> Dict[str, Any]:
    """Get log file settings"""
    config = get_logging_config()
    return {
        'max_bytes': config['max_log_size'],
        'backup_count': config['backup_count'],
        'performance_log_days': config['performance_log_days']
    }

# Log file paths
LOG_FILES = {
    'main': f"{LOG_DIR}/trading_system.log",
    'errors': f"{LOG_DIR}/errors.log",
    'performance': f"{LOG_DIR}/performance.log",
    'security': f"{LOG_DIR}/security.log",
    'api': f"{LOG_DIR}/api.log"
}

# Log format templates
LOG_FORMATS = {
    'json': {
        'format': 'json',
        'include_timestamp': True,
        'include_environment': True,
        'include_pid': True
    },
    'simple': {
        'format': 'simple',
        'include_timestamp': True,
        'include_environment': False,
        'include_pid': False
    }
}

# Performance thresholds for alerting
PERFORMANCE_THRESHOLDS = {
    'api_response_time_ms': 1000,  # 1 second
    'cache_hit_rate_percent': 80,   # 80%
    'error_rate_percent': 1,        # 1%
    'memory_usage_percent': 85,     # 85%
    'disk_usage_percent': 90        # 90%
}

# Security logging events
SECURITY_EVENTS = {
    'authentication_failure': 'AUTH_FAILURE',
    'authorization_failure': 'AUTHZ_FAILURE',
    'api_rate_limit_exceeded': 'RATE_LIMIT',
    'suspicious_activity': 'SUSPICIOUS',
    'data_access_violation': 'DATA_VIOLATION',
    'system_compromise': 'COMPROMISE'
}

# Trading-specific log events
TRADING_EVENTS = {
    'trade_signal': 'TRADE_SIGNAL',
    'order_placed': 'ORDER_PLACED',
    'order_executed': 'ORDER_EXECUTED',
    'order_cancelled': 'ORDER_CANCELLED',
    'position_opened': 'POSITION_OPENED',
    'position_closed': 'POSITION_CLOSED',
    'risk_limit_breached': 'RISK_LIMIT',
    'market_data_update': 'MARKET_DATA'
} 