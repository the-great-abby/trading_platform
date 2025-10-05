# Centralized trading configuration

import os
import json
from typing import Dict, Any, List, Optional

SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
    'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
    'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'SMCI'
]

OPTIONS_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
    'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV', 'USO', 'UNG', 'XLE', 'XLF'
]

# LLM Service Configuration - Read from LLM_SERVICE_CONFIG environment variable
def get_llm_service_config() -> Dict[str, Any]:
    """Get LLM service configuration from environment variable"""
    llm_config_str = os.getenv('LLM_SERVICE_CONFIG')
    if llm_config_str:
        try:
            return json.loads(llm_config_str)
        except json.JSONDecodeError:
            pass
    
    # Fallback to individual environment variables
    return {
        'base_url': os.getenv('LLM_BASE_URL', 'http://llm-proxy:11081'),
        'api_key': os.getenv('LLM_API_KEY', ''),
        'timeout': int(os.getenv('LLM_TIMEOUT', '30')),
        'max_retries': int(os.getenv('LLM_MAX_RETRIES', '3')),
        'rate_limit_requests': int(os.getenv('LLM_RATE_LIMIT', '100')),
        'rate_limit_window': int(os.getenv('LLM_RATE_LIMIT_WINDOW', '60')),
        'cache_ttl': int(os.getenv('LLM_CACHE_TTL', '300')),
        'health_check_interval': int(os.getenv('LLM_HEALTH_CHECK_INTERVAL', '60'))
    }

LLM_SERVICE_CONFIG = get_llm_service_config()

# Risk Management Configuration
RISK_CONFIG = {
    'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', '1000')),
    'max_position_size': int(os.getenv('MAX_POSITION_SIZE', '10000')),
    'max_concentration': float(os.getenv('MAX_CONCENTRATION', '0.1')),
    'max_correlation': float(os.getenv('MAX_CORRELATION', '0.7')),
    'var_confidence_level': float(os.getenv('VAR_CONFIDENCE_LEVEL', '0.95')),
    'var_time_horizon': int(os.getenv('VAR_TIME_HORIZON', '1'))
}

# Order Management Configuration
ORDER_CONFIG = {
    'max_order_value': float(os.getenv('MAX_ORDER_VALUE', '100000')),
    'max_daily_value': float(os.getenv('MAX_DAILY_VALUE', '1000000')),
    'execution_venues': ['NYSE', 'NASDAQ', 'ARCA'],
    'heartbeat_timeout_minutes': int(os.getenv('HEARTBEAT_TIMEOUT_MINUTES', '5')),
    'order_validation_rules': ['basic', 'risk', 'compliance'],
    'order_routing_strategy': 'best_execution',
    'order_analytics_enabled': True,
    'order_monitoring_enabled': True
}

# Market Data Configuration
MARKET_DATA_CONFIG = {
    'data_providers': ['polygon', 'alpha_vantage', 'yahoo'],
    'cache_enabled': True,
    'cache_ttl_minutes': int(os.getenv('CACHE_TTL_MINUTES', '5')),
    'real_time_enabled': True,
    'historical_data_enabled': True,
    'options_data_enabled': True,
    'news_data_enabled': True
}

# Elliott Wave Analysis Configuration
ELLIOTT_WAVE_CONFIG = {
    'service_url': os.getenv('ELLIOTT_WAVE_SERVICE_URL', 'http://elliott-wave-service.trading-system.svc.cluster.local:8000'),
    'timeout': int(os.getenv('ELLIOTT_WAVE_TIMEOUT', '30')),
    'max_retries': int(os.getenv('ELLIOTT_WAVE_MAX_RETRIES', '3')),
    'analysis_timeout': int(os.getenv('ELLIOTT_WAVE_ANALYSIS_TIMEOUT', '30')),
    'min_confidence_threshold': float(os.getenv('ELLIOTT_WAVE_MIN_CONFIDENCE', '0.6')),
    'tracked_symbols': SYMBOLS,  # Track all 43 symbols available in the database
    'timeframe': os.getenv('ELLIOTT_WAVE_TIMEFRAME', '15m'),
    'options_integration_enabled': True,
    'fibonacci_levels': [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618],
    'pattern_types': ['impulse', 'corrective', 'extension', 'diagonal', 'triangle', 'flat', 'zigzag'],
    'risk_levels': {
        'high': {'max_position_size': 0.1, 'min_confidence': 0.8},
        'medium': {'max_position_size': 0.05, 'min_confidence': 0.6},
        'low': {'max_position_size': 0.02, 'min_confidence': 0.4}
    },
    'strategy_mappings': {
        'impulse_completion': ['StraddleStrategy', 'LongStrangleStrategy'],
        'corrective_completion': ['IronCondorStrategy', 'ButterflySpreadStrategy'],
        'fibonacci_retracement': ['CalendarSpreadStrategy', 'DiagonalSpreadStrategy'],
        'wave_extension': ['VolatilityStrategy', 'StraddleStrategy'],
        'pattern_invalidation': ['ButterflySpreadStrategy', 'IronCondorStrategy']
    }
}

# Trade Recovery Configuration
TRADE_RECOVERY_CONFIG = {
    'service': {
        'port': int(os.getenv('TRADE_RECOVERY_PORT', '10001')),
        'host': os.getenv('TRADE_RECOVERY_HOST', '0.0.0.0'),
        'timeout': int(os.getenv('TRADE_RECOVERY_TIMEOUT', '30')),
        'max_retries': int(os.getenv('TRADE_RECOVERY_MAX_RETRIES', '3'))
    },
    'broker_api': {
        'base_url': os.getenv('BROKER_API_URL', 'http://broker-api.example.com'),
        'api_key': os.getenv('BROKER_API_KEY', ''),
        'timeout': int(os.getenv('BROKER_API_TIMEOUT', '30')),
        'max_retries': int(os.getenv('BROKER_API_MAX_RETRIES', '3'))
    },
    'strategy_service': {
        'base_url': os.getenv('STRATEGY_SERVICE_URL', 'http://strategy-service.trading-system.svc.cluster.local:10002'),
        'timeout': int(os.getenv('STRATEGY_SERVICE_TIMEOUT', '30')),
        'max_retries': int(os.getenv('STRATEGY_SERVICE_MAX_RETRIES', '3'))
    },
    'market_data_service': {
        'base_url': os.getenv('MARKET_DATA_SERVICE_URL', 'http://market-data-service.trading-system.svc.cluster.local:10003'),
        'timeout': int(os.getenv('MARKET_DATA_SERVICE_TIMEOUT', '30')),
        'max_retries': int(os.getenv('MARKET_DATA_SERVICE_MAX_RETRIES', '3'))
    },
    'redis': {
        'url': os.getenv('TRADE_RECOVERY_REDIS_URL', 'redis://redis.redis.svc.cluster.local:6379'),
        'db': int(os.getenv('TRADE_RECOVERY_REDIS_DB', '1')),
        'timeout': int(os.getenv('TRADE_RECOVERY_REDIS_TIMEOUT', '5')),
        'max_connections': int(os.getenv('TRADE_RECOVERY_REDIS_MAX_CONNECTIONS', '10'))
    },
    'database': {
        'url': os.getenv('TRADE_RECOVERY_DATABASE_URL', 'postgresql+asyncpg://postgres:password@timescaledb-service:5432/trading_db'),
        'pool_size': int(os.getenv('TRADE_RECOVERY_DB_POOL_SIZE', '5')),
        'max_overflow': int(os.getenv('TRADE_RECOVERY_DB_MAX_OVERFLOW', '10')),
        'pool_timeout': int(os.getenv('TRADE_RECOVERY_DB_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.getenv('TRADE_RECOVERY_DB_POOL_RECYCLE', '3600'))
    },
    'recovery': {
        'max_concurrent_sessions': int(os.getenv('TRADE_RECOVERY_MAX_CONCURRENT_SESSIONS', '10')),
        'session_timeout_minutes': int(os.getenv('TRADE_RECOVERY_SESSION_TIMEOUT', '60')),
        'trade_detection_timeout': int(os.getenv('TRADE_RECOVERY_DETECTION_TIMEOUT', '30')),
        'strategy_matching_timeout': int(os.getenv('TRADE_RECOVERY_MATCHING_TIMEOUT', '15')),
        'auto_assign_strategies': os.getenv('TRADE_RECOVERY_AUTO_ASSIGN', 'false').lower() == 'true',
        'min_confidence_threshold': float(os.getenv('TRADE_RECOVERY_MIN_CONFIDENCE', '0.7')),
        'max_trades_per_session': int(os.getenv('TRADE_RECOVERY_MAX_TRADES', '100'))
    },
    'logging': {
        'level': os.getenv('TRADE_RECOVERY_LOG_LEVEL', 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_rotation': True,
        'max_file_size': '10MB',
        'backup_count': 5
    }
}

# Live Trading Configuration
LIVE_TRADING_CONFIG = {
    'public_api': {
        'base_url': os.getenv('PUBLIC_API_BASE_URL', 'https://api.public.com'),
        'api_version': os.getenv('PUBLIC_API_VERSION', 'v1'),
        'timeout': int(os.getenv('PUBLIC_API_TIMEOUT', '30')),
        'max_retries': int(os.getenv('PUBLIC_API_MAX_RETRIES', '3')),
        'rate_limit_requests': int(os.getenv('PUBLIC_API_RATE_LIMIT', '100')),
        'rate_limit_window': int(os.getenv('PUBLIC_API_RATE_LIMIT_WINDOW', '60'))
    },
    'database': {
        'url': os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:password@timescaledb-service:5432/trading_db'),
        'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600'))
    },
    'redis': {
        'url': os.getenv('REDIS_URL', 'redis://redis.redis.svc.cluster.local:6379'),
        'db': int(os.getenv('REDIS_DB', '0')),
        'timeout': int(os.getenv('REDIS_TIMEOUT', '5')),
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '10'))
    },
    'encryption': {
        'key': os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here'),
        'algorithm': 'AES-256-GCM',
        'key_derivation': 'PBKDF2'
    },
    'risk_management': {
        'max_position_size': float(os.getenv('LIVE_MAX_POSITION_SIZE', '10000.0')),
        'max_portfolio_risk': float(os.getenv('LIVE_MAX_PORTFOLIO_RISK', '0.05')),
        'max_daily_loss': float(os.getenv('LIVE_MAX_DAILY_LOSS', '1000.0')),
        'max_daily_trades': int(os.getenv('LIVE_MAX_DAILY_TRADES', '20')),
        'emergency_stop_enabled': True,
        'market_hours_enforcement': True,
        'greeks_limits': {
            'max_delta': float(os.getenv('LIVE_MAX_DELTA', '1000.0')),
            'max_gamma': float(os.getenv('LIVE_MAX_GAMMA', '100.0')),
            'max_theta': float(os.getenv('LIVE_MAX_THETA', '-50.0')),
            'max_vega': float(os.getenv('LIVE_MAX_VEGA', '200.0'))
        }
    },
    'trading': {
        'allowed_strategies': ['IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD'],
        'default_order_type': 'MARKET',
        'default_time_in_force': 'DAY',
        'position_sizing_method': 'fixed_dollar',
        'default_position_size': float(os.getenv('LIVE_DEFAULT_POSITION_SIZE', '1000.0'))
    },
    'logging': {
        'level': os.getenv('LIVE_TRADING_LOG_LEVEL', 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_rotation': True,
        'max_file_size': '10MB',
        'backup_count': 5
    }
}

# Validation Framework Configuration
VALIDATION_CONFIG = {
    'discovery': {
        'default_directory': os.getenv('VALIDATION_DEFAULT_DIRECTORY', './backtests'),
        'patterns': json.loads(os.getenv('VALIDATION_PATTERNS', '["*_backtest*.py", "*_simulation*.py"]')),
        'max_depth': int(os.getenv('VALIDATION_MAX_DEPTH', '3')),
        'include_subdirectories': os.getenv('VALIDATION_INCLUDE_SUBDIRS', 'true').lower() == 'true'
    },
    'execution': {
        'default_timeout': int(os.getenv('VALIDATION_DEFAULT_TIMEOUT', '300')),
        'max_concurrent': int(os.getenv('VALIDATION_MAX_CONCURRENT', '5')),
        'resource_limits': {
            'memory_mb': int(os.getenv('VALIDATION_MEMORY_LIMIT_MB', '1024')),
            'cpu_percent': int(os.getenv('VALIDATION_CPU_LIMIT_PERCENT', '80'))
        }
    },
    'validation': {
        'default_tolerance': {
            'total_return_pct': float(os.getenv('VALIDATION_TOLERANCE_RETURN', '0.01')),
            'sharpe_ratio': float(os.getenv('VALIDATION_TOLERANCE_SHARPE', '0.1')),
            'max_drawdown_pct': float(os.getenv('VALIDATION_TOLERANCE_DRAWDOWN', '0.05'))
        },
        'validation_strategies': json.loads(os.getenv('VALIDATION_STRATEGIES', '["exact", "tolerance", "range"]'))
    },
    'reporting': {
        'default_format': os.getenv('VALIDATION_DEFAULT_FORMAT', 'json'),
        'include_charts': os.getenv('VALIDATION_INCLUDE_CHARTS', 'false').lower() == 'true',
        'include_metrics': os.getenv('VALIDATION_INCLUDE_METRICS', 'true').lower() == 'true'
    },
    'database': {
        'host': os.getenv('VALIDATION_DB_HOST', 'postgres.external-namespace.svc.cluster.local'),
        'port': int(os.getenv('VALIDATION_DB_PORT', '5432')),
        'database': os.getenv('VALIDATION_DB_NAME', 'validation_framework'),
        'ssl_mode': os.getenv('VALIDATION_DB_SSL_MODE', 'require'),
        'connection_pool': {
            'size': int(os.getenv('VALIDATION_DB_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('VALIDATION_DB_MAX_OVERFLOW', '20')),
            'timeout': int(os.getenv('VALIDATION_DB_POOL_TIMEOUT', '30')),
            'recycle': int(os.getenv('VALIDATION_DB_POOL_RECYCLE', '3600'))
        },
        'retry': {
            'max_attempts': int(os.getenv('VALIDATION_DB_RETRY_ATTEMPTS', '3')),
            'base_delay': float(os.getenv('VALIDATION_DB_RETRY_DELAY', '1.0')),
            'max_delay': float(os.getenv('VALIDATION_DB_RETRY_MAX_DELAY', '60.0')),
            'strategy': os.getenv('VALIDATION_DB_RETRY_STRATEGY', 'exponential'),
            'jitter': os.getenv('VALIDATION_DB_RETRY_JITTER', 'true').lower() == 'true'
        },
        'circuit_breaker': {
            'failure_threshold': int(os.getenv('VALIDATION_DB_CB_THRESHOLD', '5')),
            'recovery_timeout': float(os.getenv('VALIDATION_DB_CB_RECOVERY', '60.0')),
            'expected_exceptions': json.loads(os.getenv('VALIDATION_DB_CB_EXCEPTIONS', '["OperationalError", "DatabaseError"]'))
        }
    },
    'api': {
        'cors': {
            'allow_origins': json.loads(os.getenv('VALIDATION_CORS_ORIGINS', '["*"]')),
            'allow_methods': json.loads(os.getenv('VALIDATION_CORS_METHODS', '["GET", "POST", "PUT", "DELETE"]')),
            'allow_headers': json.loads(os.getenv('VALIDATION_CORS_HEADERS', '["*"]'))
        },
        'rate_limiting': {
            'enabled': os.getenv('VALIDATION_RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            'requests_per_minute': int(os.getenv('VALIDATION_RATE_LIMIT_RPM', '100')),
            'burst_size': int(os.getenv('VALIDATION_RATE_LIMIT_BURST', '20'))
        },
        'pagination': {
            'default_limit': int(os.getenv('VALIDATION_PAGINATION_LIMIT', '20')),
            'max_limit': int(os.getenv('VALIDATION_PAGINATION_MAX', '100'))
        },
        'timeouts': {
            'request_timeout': int(os.getenv('VALIDATION_REQUEST_TIMEOUT', '30')),
            'validation_timeout': int(os.getenv('VALIDATION_VALIDATION_TIMEOUT', '300'))
        }
    },
    'logging': {
        'level': os.getenv('VALIDATION_LOG_LEVEL', 'INFO'),
        'format': os.getenv('VALIDATION_LOG_FORMAT', 'json'),
        'file_rotation': {
            'max_bytes': int(os.getenv('VALIDATION_LOG_MAX_BYTES', '10485760')),  # 10MB
            'backup_count': int(os.getenv('VALIDATION_LOG_BACKUP_COUNT', '5'))
        }
    },
    'monitoring': {
        'metrics': {
            'enabled': os.getenv('VALIDATION_METRICS_ENABLED', 'true').lower() == 'true',
            'collection_interval': int(os.getenv('VALIDATION_METRICS_INTERVAL', '30')),
            'retention_hours': int(os.getenv('VALIDATION_METRICS_RETENTION', '24'))
        },
        'prometheus': {
            'enabled': os.getenv('VALIDATION_PROMETHEUS_ENABLED', 'true').lower() == 'true',
            'port': int(os.getenv('VALIDATION_PROMETHEUS_PORT', '8000')),
            'path': os.getenv('VALIDATION_PROMETHEUS_PATH', '/metrics')
        },
        'health_checks': {
            'database': {
                'enabled': os.getenv('VALIDATION_HEALTH_DB_ENABLED', 'true').lower() == 'true',
                'timeout_seconds': int(os.getenv('VALIDATION_HEALTH_DB_TIMEOUT', '5'))
            },
            'disk_space': {
                'enabled': os.getenv('VALIDATION_HEALTH_DISK_ENABLED', 'true').lower() == 'true',
                'threshold_percent': int(os.getenv('VALIDATION_HEALTH_DISK_THRESHOLD', '90'))
            },
            'memory': {
                'enabled': os.getenv('VALIDATION_HEALTH_MEMORY_ENABLED', 'true').lower() == 'true',
                'threshold_percent': int(os.getenv('VALIDATION_HEALTH_MEMORY_THRESHOLD', '85'))
            }
        }
    }
}

def get_symbols():
    return SYMBOLS

def get_options_symbols():
    return OPTIONS_SYMBOLS

def get_trading_config() -> Dict[str, Any]:
    """Get complete trading configuration"""
    return {
        'symbols': SYMBOLS,
        'options_symbols': OPTIONS_SYMBOLS,
        'llm_service': LLM_SERVICE_CONFIG,
        'risk_management': RISK_CONFIG,
        'order_management': ORDER_CONFIG,
        'market_data': MARKET_DATA_CONFIG,
        'elliott_wave': ELLIOTT_WAVE_CONFIG,
        'trade_recovery': TRADE_RECOVERY_CONFIG,
        'live_trading': LIVE_TRADING_CONFIG,
        'validation': VALIDATION_CONFIG
    }

def get_live_trading_config() -> Dict[str, Any]:
    """Get live trading configuration"""
    return LIVE_TRADING_CONFIG

def get_trade_recovery_config() -> Dict[str, Any]:
    """Get trade recovery configuration"""
    return TRADE_RECOVERY_CONFIG

def get_validation_config() -> Dict[str, Any]:
    """Get validation framework configuration"""
    return VALIDATION_CONFIG