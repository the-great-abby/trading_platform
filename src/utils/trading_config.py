# Centralized trading configuration

import os
import json
from typing import Dict, Any

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
        'live_trading': LIVE_TRADING_CONFIG
    }

def get_live_trading_config() -> Dict[str, Any]:
    """Get live trading configuration"""
    return LIVE_TRADING_CONFIG 