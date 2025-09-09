"""
Metrics configuration
"""

import os
from pydantic import BaseModel, Field, validator


class MetricsConfig(BaseModel):
    """Metrics configuration"""
    enabled: bool = Field(default=True, description="Enable metrics collection")
    backend: str = Field(default="prometheus", description="Metrics backend")
    port: int = Field(default=9090, description="Metrics port")
    path: str = Field(default="/metrics", description="Metrics path")
    collect_system_metrics: bool = Field(default=True, description="Collect system metrics")
    collect_custom_metrics: bool = Field(default=True, description="Collect custom metrics")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
            "backend": os.getenv("METRICS_BACKEND", "prometheus"),
            "port": int(os.getenv("METRICS_PORT", "9090")),
            "path": os.getenv("METRICS_PATH", "/metrics"),
            "collect_system_metrics": os.getenv("METRICS_COLLECT_SYSTEM", "true").lower() == "true",
            "collect_custom_metrics": os.getenv("METRICS_COLLECT_CUSTOM", "true").lower() == "true"
        }
        
        # Override with provided data
        env_data.update(env_data)
        super().__init__(**env_data)
    
    @validator("backend")
    def validate_backend(cls, v):
        allowed_backends = ["prometheus", "statsd", "none"]
        if v not in allowed_backends:
            raise ValueError(f"Backend must be one of: {allowed_backends}")
        return v
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class PrometheusConfig(BaseModel):
    """Prometheus configuration"""
    port: int = Field(default=9090, description="Prometheus port")
    path: str = Field(default="/metrics", description="Metrics path")
    collect_system_metrics: bool = Field(default=True, description="Collect system metrics")
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class StatsDConfig(BaseModel):
    """StatsD configuration"""
    host: str = Field(default="localhost", description="StatsD host")
    port: int = Field(default=8125, description="StatsD port")
    prefix: str = Field(default="trading_api", description="Metrics prefix")
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
