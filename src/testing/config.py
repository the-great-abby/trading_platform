#!/usr/bin/env python3
"""
Configuration for Strategy Engine Testing Framework
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class TestingConfig(BaseSettings):
    """Configuration for the testing framework"""
    
    # API Configuration
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(11003, description="API port")
    api_workers: int = Field(1, description="Number of API workers")
    debug: bool = Field(False, description="Debug mode")
    
    # Database Configuration
    database_url: str = Field(
        "postgresql://user:password@localhost:5432/trading_testing",
        description="Database connection URL"
    )
    database_pool_size: int = Field(10, description="Database connection pool size")
    database_max_overflow: int = Field(20, description="Database max overflow connections")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection URL")
    redis_max_connections: int = Field(10, description="Redis max connections")
    
    # Strategy Service Configuration
    strategy_service_url: str = Field(
        "http://localhost:11002",
        description="Strategy service base URL"
    )
    strategy_service_timeout: int = Field(30, description="Strategy service timeout in seconds")
    
    # Testing Configuration
    default_test_timeout: int = Field(300, description="Default test timeout in seconds")
    max_concurrent_tests: int = Field(10, description="Maximum concurrent tests")
    mock_data_cache_ttl: int = Field(3600, description="Mock data cache TTL in seconds")
    
    # Performance Limits
    max_execution_time_ms: float = Field(100.0, description="Maximum execution time per signal")
    max_memory_mb: float = Field(1024.0, description="Maximum memory usage in MB")
    max_cpu_percent: float = Field(80.0, description="Maximum CPU usage percentage")
    min_signals_per_second: float = Field(1.0, description="Minimum signals per second")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Security Configuration
    api_key_header: str = Field("X-API-Key", description="API key header name")
    allowed_origins: list = Field(["*"], description="Allowed CORS origins")
    
    # Monitoring Configuration
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    metrics_port: int = Field(9090, description="Metrics server port")
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


class DatabaseConfig:
    """Database-specific configuration"""
    
    @staticmethod
    def get_connection_params(config: TestingConfig) -> Dict[str, Any]:
        """Get database connection parameters"""
        return {
            "pool_size": config.database_pool_size,
            "max_overflow": config.database_max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo": config.debug
        }


class RedisConfig:
    """Redis-specific configuration"""
    
    @staticmethod
    def get_connection_params(config: TestingConfig) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        return {
            "max_connections": config.redis_max_connections,
            "retry_on_timeout": True,
            "socket_keepalive": True,
            "socket_keepalive_options": {}
        }


class StrategyServiceConfig:
    """Strategy service configuration"""
    
    @staticmethod
    def get_endpoints(base_url: str) -> Dict[str, str]:
        """Get strategy service endpoints"""
        return {
            "list_strategies": f"{base_url}/api/v1/strategies",
            "get_strategy": f"{base_url}/api/v1/strategies/{{strategy_name}}",
            "create_strategy": f"{base_url}/api/v1/strategies",
            "update_strategy": f"{base_url}/api/v1/strategies/{{strategy_name}}",
            "delete_strategy": f"{base_url}/api/v1/strategies/{{strategy_name}}"
        }


# Global configuration instance
config = TestingConfig()


def get_config() -> TestingConfig:
    """Get the global configuration instance"""
    return config


def update_config(**kwargs) -> TestingConfig:
    """Update configuration with new values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def load_config_from_env() -> TestingConfig:
    """Load configuration from environment variables"""
    global config
    config = TestingConfig()
    return config
