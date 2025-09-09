"""
Test configuration for CQRS testing
Uses separate test database to avoid affecting production data
"""

import os
from typing import Dict, Any

# Test Database Configuration
TEST_DATABASE_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'timescaledb.trading-system.svc.cluster.local'),
    'port': int(os.getenv('TEST_DB_PORT', '5432')),
    'database': os.getenv('TEST_DB_NAME', 'trading_bot_test'),
    'username': os.getenv('TEST_DB_USER', 'trading_user'),
    'password': os.getenv('TEST_DB_PASSWORD', 'trading_pass'),
    'url': f"postgresql://{os.getenv('TEST_DB_USER', 'trading_user')}:{os.getenv('TEST_DB_PASSWORD', 'trading_pass')}@{os.getenv('TEST_DB_HOST', 'timescaledb.trading-system.svc.cluster.local')}:{os.getenv('TEST_DB_PORT', '5432')}/{os.getenv('TEST_DB_NAME', 'trading_bot_test')}"
}

# Test Redis Configuration
TEST_REDIS_CONFIG = {
    'host': os.getenv('TEST_REDIS_HOST', 'redis.redis.svc.cluster.local'),
    'port': int(os.getenv('TEST_REDIS_PORT', '6379')),
    'db': int(os.getenv('TEST_REDIS_DB', '1')),  # Use different Redis DB for testing
    'password': os.getenv('TEST_REDIS_PASSWORD', ''),
    'url': f"redis://{os.getenv('TEST_REDIS_HOST', 'redis.redis.svc.cluster.local')}:{os.getenv('TEST_REDIS_PORT', '6379')}/{os.getenv('TEST_REDIS_DB', '1')}"
}

# Test RabbitMQ Configuration
TEST_RABBITMQ_CONFIG = {
    'host': os.getenv('TEST_RABBITMQ_HOST', 'rabbitmq.rabbitmq-system.svc.cluster.local'),
    'port': int(os.getenv('TEST_RABBITMQ_PORT', '5672')),
    'username': os.getenv('TEST_RABBITMQ_USER', 'trading'),
    'password': os.getenv('TEST_RABBITMQ_PASSWORD', 'trading_pass'),
    'vhost': os.getenv('TEST_RABBITMQ_VHOST', 'trading_vhost_test'),
    'url': f"amqp://{os.getenv('TEST_RABBITMQ_USER', 'trading')}:{os.getenv('TEST_RABBITMQ_PASSWORD', 'trading_pass')}@{os.getenv('TEST_RABBITMQ_HOST', 'rabbitmq.rabbitmq-system.svc.cluster.local')}:{os.getenv('TEST_RABBITMQ_PORT', '5672')}/{os.getenv('TEST_RABBITMQ_VHOST', 'trading_vhost_test')}"
}

# Test Environment Settings
TEST_ENVIRONMENT = {
    'environment': 'test',
    'log_level': 'DEBUG',
    'debug': True,
    'testing': True,
    'database': TEST_DATABASE_CONFIG,
    'redis': TEST_REDIS_CONFIG,
    'rabbitmq': TEST_RABBITMQ_CONFIG
}

def get_test_config() -> Dict[str, Any]:
    """Get test configuration"""
    return TEST_ENVIRONMENT

def get_test_database_url() -> str:
    """Get test database URL"""
    return TEST_DATABASE_CONFIG['url']

def get_test_redis_url() -> str:
    """Get test Redis URL"""
    return TEST_REDIS_CONFIG['url']

def get_test_rabbitmq_url() -> str:
    """Get test RabbitMQ URL"""
    return TEST_RABBITMQ_CONFIG['url']
