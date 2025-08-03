# Centralized trading configuration

import os
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

# LLM Service Configuration
LLM_SERVICE_CONFIG = {
    'base_url': os.getenv('LLM_BASE_URL', 'http://llm-proxy:8081'),
    'api_key': os.getenv('LLM_API_KEY', ''),
    'timeout': int(os.getenv('LLM_TIMEOUT', '30')),
    'max_retries': int(os.getenv('LLM_MAX_RETRIES', '3')),
    'rate_limit_requests': int(os.getenv('LLM_RATE_LIMIT', '100')),
    'rate_limit_window': int(os.getenv('LLM_RATE_LIMIT_WINDOW', '60')),
    'cache_ttl': int(os.getenv('LLM_CACHE_TTL', '300')),
    'health_check_interval': int(os.getenv('LLM_HEALTH_CHECK_INTERVAL', '60'))
}

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
        'market_data': MARKET_DATA_CONFIG
    } 