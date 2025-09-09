"""
API configuration management
"""

import os
from pydantic import BaseModel, Field, validator
from typing import Optional


class APIConfig(BaseModel):
    """Main API configuration"""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    title: str = Field(default="Trading System CQRS API", description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: str = Field(default="CQRS API for Trading System", description="API description")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "debug": os.getenv("API_DEBUG", "false").lower() == "true",
            "title": os.getenv("API_TITLE", "Trading System CQRS API"),
            "version": os.getenv("API_VERSION", "1.0.0"),
            "description": os.getenv("API_DESCRIPTION", "CQRS API for Trading System")
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("host")
    def validate_host(cls, v):
        if not v:
            raise ValueError("Host cannot be empty")
        return v


class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="trading_bot", description="Database name")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "trading_bot"),
            "username": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600"))
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("pool_size")
    def validate_pool_size(cls, v):
        if v <= 0:
            raise ValueError("Pool size must be positive")
        return v
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: str = Field(default="", description="Redis password")
    max_connections: int = Field(default=10, description="Max connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=5, description="Socket connect timeout in seconds")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", ""),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            "socket_connect_timeout": int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5")),
            "retry_on_timeout": os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("db")
    def validate_db(cls, v):
        if not 0 <= v <= 15:
            raise ValueError("Redis database must be between 0 and 15")
        return v
    
    def get_connection_params(self) -> dict:
        """Get Redis connection parameters"""
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout
        }


class RabbitMQConfig(BaseModel):
    """RabbitMQ configuration"""
    host: str = Field(default="localhost", description="RabbitMQ host")
    port: int = Field(default=5672, description="RabbitMQ port")
    username: str = Field(default="guest", description="RabbitMQ username")
    password: str = Field(default="guest", description="RabbitMQ password")
    vhost: str = Field(default="/", description="RabbitMQ virtual host")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    heartbeat: int = Field(default=600, description="Heartbeat interval in seconds")
    blocked_connection_timeout: int = Field(default=300, description="Blocked connection timeout in seconds")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "host": os.getenv("RABBITMQ_HOST", "localhost"),
            "port": int(os.getenv("RABBITMQ_PORT", "5672")),
            "username": os.getenv("RABBITMQ_USERNAME", "guest"),
            "password": os.getenv("RABBITMQ_PASSWORD", "guest"),
            "vhost": os.getenv("RABBITMQ_VHOST", "/"),
            "connection_timeout": int(os.getenv("RABBITMQ_CONNECTION_TIMEOUT", "30")),
            "heartbeat": int(os.getenv("RABBITMQ_HEARTBEAT", "600")),
            "blocked_connection_timeout": int(os.getenv("RABBITMQ_BLOCKED_CONNECTION_TIMEOUT", "300"))
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("connection_timeout")
    def validate_connection_timeout(cls, v):
        if v <= 0:
            raise ValueError("Connection timeout must be positive")
        return v
    
    @validator("heartbeat")
    def validate_heartbeat(cls, v):
        if v <= 0:
            raise ValueError("Heartbeat must be positive")
        return v
    
    def get_connection_url(self) -> str:
        """Get RabbitMQ connection URL"""
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}{self.vhost}"
