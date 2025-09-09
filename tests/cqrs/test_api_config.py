"""
Tests for Phase 4: API Configuration and Deployment
Tests configuration management, environment variables, and deployment settings
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta

from src.api.config.api_config import APIConfig, DatabaseConfig, RedisConfig, RabbitMQConfig
from src.api.config.deployment_config import DeploymentConfig, KubernetesConfig, DockerConfig
from src.api.config.security_config import SecurityConfig, JWTConfig, RateLimitConfig
from src.api.config.logging_config import LoggingConfig, LogLevel, LogFormat
from src.api.config.metrics_config import MetricsConfig, PrometheusConfig, StatsDConfig


class TestAPIConfig:
    """Test API configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = APIConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug == False
        assert config.title == "Trading System CQRS API"
        assert config.version == "1.0.0"
        assert config.description == "CQRS API for Trading System"
    
    def test_config_from_env(self):
        """Test configuration from environment variables"""
        env_vars = {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "API_DEBUG": "true",
            "API_TITLE": "Test API",
            "API_VERSION": "2.0.0",
            "API_DESCRIPTION": "Test Description"
        }
        
        with patch.dict(os.environ, env_vars):
            config = APIConfig()
            
            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert config.debug == True
            assert config.title == "Test API"
            assert config.version == "2.0.0"
            assert config.description == "Test Description"
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = APIConfig(
            host="127.0.0.1",
            port=8000,
            debug=False
        )
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.debug == False
        
        # Invalid port
        with pytest.raises(ValueError):
            APIConfig(port=-1)
        
        with pytest.raises(ValueError):
            APIConfig(port=65536)
        
        # Invalid host
        with pytest.raises(ValueError):
            APIConfig(host="")
    
    def test_config_serialization(self):
        """Test configuration serialization"""
        config = APIConfig(
            host="127.0.0.1",
            port=8000,
            debug=True,
            title="Test API"
        )
        
        # Test to dict
        data = config.model_dump()
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 8000
        assert data["debug"] == True
        assert data["title"] == "Test API"
        
        # Test from dict
        new_config = APIConfig(**data)
        assert new_config.host == "127.0.0.1"
        assert new_config.port == 8000
        assert new_config.debug == True
        assert new_config.title == "Test API"
    
    def test_config_environment_specific(self):
        """Test environment-specific configuration"""
        # Development environment
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = APIConfig()
            assert config.debug == True
            assert config.host == "127.0.0.1"
        
        # Production environment
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            config = APIConfig()
            assert config.debug == False
            assert config.host == "0.0.0.0"
        
        # Testing environment
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            config = APIConfig()
            assert config.debug == True
            assert config.host == "127.0.0.1"


class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_default_database_config(self):
        """Test default database configuration"""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "trading_bot"
        assert config.username == "postgres"
        assert config.password == ""
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
    
    def test_database_config_from_env(self):
        """Test database configuration from environment variables"""
        env_vars = {
            "DB_HOST": "db.example.com",
            "DB_PORT": "5433",
            "DB_NAME": "trading_prod",
            "DB_USER": "trading_user",
            "DB_PASSWORD": "secure_password",
            "DB_POOL_SIZE": "20",
            "DB_MAX_OVERFLOW": "40",
            "DB_POOL_TIMEOUT": "60",
            "DB_POOL_RECYCLE": "7200"
        }
        
        with patch.dict(os.environ, env_vars):
            config = DatabaseConfig()
            
            assert config.host == "db.example.com"
            assert config.port == 5433
            assert config.database == "trading_prod"
            assert config.username == "trading_user"
            assert config.password == "secure_password"
            assert config.pool_size == 20
            assert config.max_overflow == 40
            assert config.pool_timeout == 60
            assert config.pool_recycle == 7200
    
    def test_database_config_validation(self):
        """Test database configuration validation"""
        # Valid config
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        
        # Invalid port
        with pytest.raises(ValueError):
            DatabaseConfig(port=-1)
        
        with pytest.raises(ValueError):
            DatabaseConfig(port=65536)
        
        # Invalid pool size
        with pytest.raises(ValueError):
            DatabaseConfig(pool_size=0)
        
        with pytest.raises(ValueError):
            DatabaseConfig(pool_size=-1)
    
    def test_database_connection_string(self):
        """Test database connection string generation"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="trading_bot",
            username="postgres",
            password="password"
        )
        
        connection_string = config.get_connection_string()
        assert "postgresql://postgres:password@localhost:5432/trading_bot" in connection_string
    
    def test_database_config_security(self):
        """Test database configuration security"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="trading_bot",
            username="postgres",
            password="sensitive_password"
        )
        
        # Test that password is not exposed in string representation
        config_str = str(config)
        assert "sensitive_password" not in config_str
        assert "password" not in config_str.lower()
        
        # Test that password is not exposed in dict representation
        config_dict = config.model_dump()
        assert "password" not in config_dict


class TestRedisConfig:
    """Test Redis configuration"""
    
    def test_default_redis_config(self):
        """Test default Redis configuration"""
        config = RedisConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password == ""
        assert config.max_connections == 10
        assert config.socket_timeout == 5
        assert config.socket_connect_timeout == 5
        assert config.retry_on_timeout == True
    
    def test_redis_config_from_env(self):
        """Test Redis configuration from environment variables"""
        env_vars = {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "redis_password",
            "REDIS_MAX_CONNECTIONS": "20",
            "REDIS_SOCKET_TIMEOUT": "10",
            "REDIS_SOCKET_CONNECT_TIMEOUT": "10",
            "REDIS_RETRY_ON_TIMEOUT": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = RedisConfig()
            
            assert config.host == "redis.example.com"
            assert config.port == 6380
            assert config.db == 1
            assert config.password == "redis_password"
            assert config.max_connections == 20
            assert config.socket_timeout == 10
            assert config.socket_connect_timeout == 10
            assert config.retry_on_timeout == False
    
    def test_redis_config_validation(self):
        """Test Redis configuration validation"""
        # Valid config
        config = RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            password="test_pass"
        )
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password == "test_pass"
        
        # Invalid port
        with pytest.raises(ValueError):
            RedisConfig(port=-1)
        
        with pytest.raises(ValueError):
            RedisConfig(port=65536)
        
        # Invalid db
        with pytest.raises(ValueError):
            RedisConfig(db=-1)
        
        with pytest.raises(ValueError):
            RedisConfig(db=16)
    
    def test_redis_connection_params(self):
        """Test Redis connection parameters"""
        config = RedisConfig(
            host="localhost",
            port=6379,
            db=1,
            password="test_pass",
            max_connections=20,
            socket_timeout=10
        )
        
        connection_params = config.get_connection_params()
        assert connection_params["host"] == "localhost"
        assert connection_params["port"] == 6379
        assert connection_params["db"] == 1
        assert connection_params["password"] == "test_pass"
        assert connection_params["max_connections"] == 20
        assert connection_params["socket_timeout"] == 10


class TestRabbitMQConfig:
    """Test RabbitMQ configuration"""
    
    def test_default_rabbitmq_config(self):
        """Test default RabbitMQ configuration"""
        config = RabbitMQConfig()
        
        assert config.host == "localhost"
        assert config.port == 5672
        assert config.username == "guest"
        assert config.password == "guest"
        assert config.vhost == "/"
        assert config.connection_timeout == 30
        assert config.heartbeat == 600
        assert config.blocked_connection_timeout == 300
    
    def test_rabbitmq_config_from_env(self):
        """Test RabbitMQ configuration from environment variables"""
        env_vars = {
            "RABBITMQ_HOST": "rabbitmq.example.com",
            "RABBITMQ_PORT": "5673",
            "RABBITMQ_USERNAME": "trading_user",
            "RABBITMQ_PASSWORD": "rabbitmq_password",
            "RABBITMQ_VHOST": "trading_vhost",
            "RABBITMQ_CONNECTION_TIMEOUT": "60",
            "RABBITMQ_HEARTBEAT": "1200",
            "RABBITMQ_BLOCKED_CONNECTION_TIMEOUT": "600"
        }
        
        with patch.dict(os.environ, env_vars):
            config = RabbitMQConfig()
            
            assert config.host == "rabbitmq.example.com"
            assert config.port == 5673
            assert config.username == "trading_user"
            assert config.password == "rabbitmq_password"
            assert config.vhost == "trading_vhost"
            assert config.connection_timeout == 60
            assert config.heartbeat == 1200
            assert config.blocked_connection_timeout == 600
    
    def test_rabbitmq_config_validation(self):
        """Test RabbitMQ configuration validation"""
        # Valid config
        config = RabbitMQConfig(
            host="localhost",
            port=5672,
            username="test_user",
            password="test_pass",
            vhost="test_vhost"
        )
        assert config.host == "localhost"
        assert config.port == 5672
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.vhost == "test_vhost"
        
        # Invalid port
        with pytest.raises(ValueError):
            RabbitMQConfig(port=-1)
        
        with pytest.raises(ValueError):
            RabbitMQConfig(port=65536)
        
        # Invalid timeout
        with pytest.raises(ValueError):
            RabbitMQConfig(connection_timeout=-1)
        
        with pytest.raises(ValueError):
            RabbitMQConfig(heartbeat=-1)
    
    def test_rabbitmq_connection_url(self):
        """Test RabbitMQ connection URL generation"""
        config = RabbitMQConfig(
            host="localhost",
            port=5672,
            username="test_user",
            password="test_pass",
            vhost="test_vhost"
        )
        
        connection_url = config.get_connection_url()
        assert "amqp://test_user:test_pass@localhost:5672/test_vhost" in connection_url


class TestSecurityConfig:
    """Test security configuration"""
    
    def test_default_security_config(self):
        """Test default security configuration"""
        config = SecurityConfig()
        
        assert config.secret_key == "your-secret-key-here"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        assert config.password_min_length == 8
        assert config.password_require_uppercase == True
        assert config.password_require_lowercase == True
        assert config.password_require_numbers == True
        assert config.password_require_special_chars == True
    
    def test_security_config_from_env(self):
        """Test security configuration from environment variables"""
        env_vars = {
            "SECRET_KEY": "super-secret-key",
            "JWT_ALGORITHM": "HS512",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "REFRESH_TOKEN_EXPIRE_DAYS": "14",
            "PASSWORD_MIN_LENGTH": "12",
            "PASSWORD_REQUIRE_UPPERCASE": "false",
            "PASSWORD_REQUIRE_LOWERCASE": "false",
            "PASSWORD_REQUIRE_NUMBERS": "false",
            "PASSWORD_REQUIRE_SPECIAL_CHARS": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = SecurityConfig()
            
            assert config.secret_key == "super-secret-key"
            assert config.algorithm == "HS512"
            assert config.access_token_expire_minutes == 60
            assert config.refresh_token_expire_days == 14
            assert config.password_min_length == 12
            assert config.password_require_uppercase == False
            assert config.password_require_lowercase == False
            assert config.password_require_numbers == False
            assert config.password_require_special_chars == False
    
    def test_security_config_validation(self):
        """Test security configuration validation"""
        # Valid config
        config = SecurityConfig(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
        assert config.secret_key == "test-secret-key"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        
        # Invalid algorithm
        with pytest.raises(ValueError):
            SecurityConfig(algorithm="INVALID")
        
        # Invalid token expiration
        with pytest.raises(ValueError):
            SecurityConfig(access_token_expire_minutes=-1)
        
        with pytest.raises(ValueError):
            SecurityConfig(refresh_token_expire_days=-1)
        
        # Invalid password requirements
        with pytest.raises(ValueError):
            SecurityConfig(password_min_length=0)
        
        with pytest.raises(ValueError):
            SecurityConfig(password_min_length=-1)
    
    def test_jwt_config(self):
        """Test JWT configuration"""
        jwt_config = JWTConfig(
            secret_key="test-secret",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
        
        assert jwt_config.secret_key == "test-secret"
        assert jwt_config.algorithm == "HS256"
        assert jwt_config.access_token_expire_minutes == 30
        assert jwt_config.refresh_token_expire_days == 7
    
    def test_rate_limit_config(self):
        """Test rate limit configuration"""
        rate_limit_config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_size=50
        )
        
        assert rate_limit_config.requests_per_minute == 100
        assert rate_limit_config.requests_per_hour == 1000
        assert rate_limit_config.requests_per_day == 10000
        assert rate_limit_config.burst_size == 50


class TestLoggingConfig:
    """Test logging configuration"""
    
    def test_default_logging_config(self):
        """Test default logging configuration"""
        config = LoggingConfig()
        
        assert config.level == LogLevel.INFO
        assert config.format == LogFormat.JSON
        assert config.file_path == "logs/api.log"
        assert config.max_file_size == 10485760  # 10MB
        assert config.backup_count == 5
        assert config.enable_console == True
        assert config.enable_file == True
    
    def test_logging_config_from_env(self):
        """Test logging configuration from environment variables"""
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "TEXT",
            "LOG_FILE_PATH": "logs/debug.log",
            "LOG_MAX_FILE_SIZE": "20971520",  # 20MB
            "LOG_BACKUP_COUNT": "10",
            "LOG_ENABLE_CONSOLE": "false",
            "LOG_ENABLE_FILE": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = LoggingConfig()
            
            assert config.level == LogLevel.DEBUG
            assert config.format == LogFormat.TEXT
            assert config.file_path == "logs/debug.log"
            assert config.max_file_size == 20971520
            assert config.backup_count == 10
            assert config.enable_console == False
            assert config.enable_file == True
    
    def test_logging_config_validation(self):
        """Test logging configuration validation"""
        # Valid config
        config = LoggingConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            file_path="test.log",
            max_file_size=1024,
            backup_count=3
        )
        assert config.level == LogLevel.DEBUG
        assert config.format == LogFormat.JSON
        assert config.file_path == "test.log"
        assert config.max_file_size == 1024
        assert config.backup_count == 3
        
        # Invalid file size
        with pytest.raises(ValueError):
            LoggingConfig(max_file_size=-1)
        
        # Invalid backup count
        with pytest.raises(ValueError):
            LoggingConfig(backup_count=-1)
    
    def test_log_level_enum(self):
        """Test log level enum"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
    
    def test_log_format_enum(self):
        """Test log format enum"""
        assert LogFormat.TEXT.value == "TEXT"
        assert LogFormat.JSON.value == "JSON"


class TestMetricsConfig:
    """Test metrics configuration"""
    
    def test_default_metrics_config(self):
        """Test default metrics configuration"""
        config = MetricsConfig()
        
        assert config.enabled == True
        assert config.backend == "prometheus"
        assert config.port == 9090
        assert config.path == "/metrics"
        assert config.collect_system_metrics == True
        assert config.collect_custom_metrics == True
    
    def test_metrics_config_from_env(self):
        """Test metrics configuration from environment variables"""
        env_vars = {
            "METRICS_ENABLED": "true",
            "METRICS_BACKEND": "statsd",
            "METRICS_PORT": "8125",
            "METRICS_PATH": "/custom-metrics",
            "METRICS_COLLECT_SYSTEM": "false",
            "METRICS_COLLECT_CUSTOM": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = MetricsConfig()
            
            assert config.enabled == True
            assert config.backend == "statsd"
            assert config.port == 8125
            assert config.path == "/custom-metrics"
            assert config.collect_system_metrics == False
            assert config.collect_custom_metrics == True
    
    def test_metrics_config_validation(self):
        """Test metrics configuration validation"""
        # Valid config
        config = MetricsConfig(
            enabled=True,
            backend="prometheus",
            port=9090,
            path="/metrics"
        )
        assert config.enabled == True
        assert config.backend == "prometheus"
        assert config.port == 9090
        assert config.path == "/metrics"
        
        # Invalid backend
        with pytest.raises(ValueError):
            MetricsConfig(backend="invalid")
        
        # Invalid port
        with pytest.raises(ValueError):
            MetricsConfig(port=-1)
        
        with pytest.raises(ValueError):
            MetricsConfig(port=65536)
    
    def test_prometheus_config(self):
        """Test Prometheus configuration"""
        prometheus_config = PrometheusConfig(
            port=9090,
            path="/metrics",
            collect_system_metrics=True
        )
        
        assert prometheus_config.port == 9090
        assert prometheus_config.path == "/metrics"
        assert prometheus_config.collect_system_metrics == True
    
    def test_statsd_config(self):
        """Test StatsD configuration"""
        statsd_config = StatsDConfig(
            host="localhost",
            port=8125,
            prefix="trading_api"
        )
        
        assert statsd_config.host == "localhost"
        assert statsd_config.port == 8125
        assert statsd_config.prefix == "trading_api"


class TestDeploymentConfig:
    """Test deployment configuration"""
    
    def test_default_deployment_config(self):
        """Test default deployment configuration"""
        config = DeploymentConfig()
        
        assert config.environment == "development"
        assert config.debug == True
        assert config.workers == 1
        assert config.worker_class == "uvicorn.workers.UvicornWorker"
        assert config.bind == "0.0.0.0:8000"
        assert config.max_requests == 1000
        assert config.max_requests_jitter == 100
        assert config.timeout == 30
        assert config.keepalive == 2
    
    def test_deployment_config_from_env(self):
        """Test deployment configuration from environment variables"""
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "WORKERS": "4",
            "WORKER_CLASS": "gunicorn.workers.GunicornWorker",
            "BIND": "0.0.0.0:9000",
            "MAX_REQUESTS": "2000",
            "MAX_REQUESTS_JITTER": "200",
            "TIMEOUT": "60",
            "KEEPALIVE": "5"
        }
        
        with patch.dict(os.environ, env_vars):
            config = DeploymentConfig()
            
            assert config.environment == "production"
            assert config.debug == False
            assert config.workers == 4
            assert config.worker_class == "gunicorn.workers.GunicornWorker"
            assert config.bind == "0.0.0.0:9000"
            assert config.max_requests == 2000
            assert config.max_requests_jitter == 200
            assert config.timeout == 60
            assert config.keepalive == 5
    
    def test_deployment_config_validation(self):
        """Test deployment configuration validation"""
        # Valid config
        config = DeploymentConfig(
            environment="production",
            debug=False,
            workers=4,
            bind="0.0.0.0:8000"
        )
        assert config.environment == "production"
        assert config.debug == False
        assert config.workers == 4
        assert config.bind == "0.0.0.0:8000"
        
        # Invalid environment
        with pytest.raises(ValueError):
            DeploymentConfig(environment="invalid")
        
        # Invalid workers
        with pytest.raises(ValueError):
            DeploymentConfig(workers=0)
        
        with pytest.raises(ValueError):
            DeploymentConfig(workers=-1)
        
        # Invalid timeout
        with pytest.raises(ValueError):
            DeploymentConfig(timeout=-1)
    
    def test_kubernetes_config(self):
        """Test Kubernetes configuration"""
        k8s_config = KubernetesConfig(
            namespace="trading-system",
            image="trading-api:latest",
            replicas=3,
            cpu_request="100m",
            cpu_limit="500m",
            memory_request="256Mi",
            memory_limit="512Mi"
        )
        
        assert k8s_config.namespace == "trading-system"
        assert k8s_config.image == "trading-api:latest"
        assert k8s_config.replicas == 3
        assert k8s_config.cpu_request == "100m"
        assert k8s_config.cpu_limit == "500m"
        assert k8s_config.memory_request == "256Mi"
        assert k8s_config.memory_limit == "512Mi"
    
    def test_docker_config(self):
        """Test Docker configuration"""
        docker_config = DockerConfig(
            image="trading-api:latest",
            tag="v1.0.0",
            registry="docker.io",
            repository="trading-system",
            build_context=".",
            dockerfile="Dockerfile"
        )
        
        assert docker_config.image == "trading-api:latest"
        assert docker_config.tag == "v1.0.0"
        assert docker_config.registry == "docker.io"
        assert docker_config.repository == "trading-system"
        assert docker_config.build_context == "."
        assert docker_config.dockerfile == "Dockerfile"


class TestConfigIntegration:
    """Test configuration integration and validation"""
    
    def test_full_config_loading(self):
        """Test loading full configuration"""
        env_vars = {
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "API_DEBUG": "false",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "trading_bot",
            "DB_USER": "postgres",
            "DB_PASSWORD": "password",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "RABBITMQ_HOST": "localhost",
            "RABBITMQ_PORT": "5672",
            "RABBITMQ_USERNAME": "guest",
            "RABBITMQ_PASSWORD": "guest",
            "SECRET_KEY": "super-secret-key",
            "JWT_ALGORITHM": "HS256",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "JSON",
            "METRICS_ENABLED": "true",
            "METRICS_BACKEND": "prometheus",
            "ENVIRONMENT": "production"
        }
        
        with patch.dict(os.environ, env_vars):
            # Load all configurations
            api_config = APIConfig()
            db_config = DatabaseConfig()
            redis_config = RedisConfig()
            rabbitmq_config = RabbitMQConfig()
            security_config = SecurityConfig()
            logging_config = LoggingConfig()
            metrics_config = MetricsConfig()
            deployment_config = DeploymentConfig()
            
            # Verify configurations are loaded correctly
            assert api_config.host == "0.0.0.0"
            assert api_config.port == 8000
            assert api_config.debug == False
            
            assert db_config.host == "localhost"
            assert db_config.port == 5432
            assert db_config.database == "trading_bot"
            assert db_config.username == "postgres"
            assert db_config.password == "password"
            
            assert redis_config.host == "localhost"
            assert redis_config.port == 6379
            assert redis_config.db == 0
            
            assert rabbitmq_config.host == "localhost"
            assert rabbitmq_config.port == 5672
            assert rabbitmq_config.username == "guest"
            assert rabbitmq_config.password == "guest"
            
            assert security_config.secret_key == "super-secret-key"
            assert security_config.algorithm == "HS256"
            
            assert logging_config.level == LogLevel.INFO
            assert logging_config.format == LogFormat.JSON
            
            assert metrics_config.enabled == True
            assert metrics_config.backend == "prometheus"
            
            assert deployment_config.environment == "production"
            assert deployment_config.debug == False
    
    def test_config_validation_integration(self):
        """Test configuration validation integration"""
        # Test with invalid configurations
        with patch.dict(os.environ, {
            "API_PORT": "-1",
            "DB_PORT": "65536",
            "REDIS_PORT": "invalid",
            "RABBITMQ_PORT": "0",
            "SECRET_KEY": "",
            "LOG_LEVEL": "INVALID",
            "METRICS_BACKEND": "invalid",
            "ENVIRONMENT": "invalid"
        }):
            # These should raise validation errors
            with pytest.raises(ValueError):
                APIConfig()
            
            with pytest.raises(ValueError):
                DatabaseConfig()
            
            with pytest.raises(ValueError):
                RedisConfig()
            
            with pytest.raises(ValueError):
                RabbitMQConfig()
            
            with pytest.raises(ValueError):
                SecurityConfig()
            
            with pytest.raises(ValueError):
                LoggingConfig()
            
            with pytest.raises(ValueError):
                MetricsConfig()
            
            with pytest.raises(ValueError):
                DeploymentConfig()
    
    def test_config_security(self):
        """Test configuration security"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="trading_bot",
            username="postgres",
            password="sensitive_password"
        )
        
        # Test that sensitive data is not exposed
        config_str = str(config)
        assert "sensitive_password" not in config_str
        
        config_dict = config.model_dump()
        assert "password" not in config_dict
        
        # Test that sensitive data is not exposed in logs
        import logging
        logger = logging.getLogger(__name__)
        
        with patch.object(logger, 'info') as mock_info:
            logger.info(f"Database config: {config}")
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "sensitive_password" not in call_args
