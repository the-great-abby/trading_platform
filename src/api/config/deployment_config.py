"""
Deployment configuration
"""

import os
from pydantic import BaseModel, Field, validator
from typing import Optional


class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    environment: str = Field(default="development", description="Deployment environment")
    debug: bool = Field(default=True, description="Debug mode")
    workers: int = Field(default=1, description="Number of workers")
    worker_class: str = Field(default="uvicorn.workers.UvicornWorker", description="Worker class")
    bind: str = Field(default="0.0.0.0:8000", description="Bind address")
    max_requests: int = Field(default=1000, description="Max requests per worker")
    max_requests_jitter: int = Field(default=100, description="Max requests jitter")
    timeout: int = Field(default=30, description="Worker timeout in seconds")
    keepalive: int = Field(default=2, description="Keepalive timeout in seconds")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "true").lower() == "true",
            "workers": int(os.getenv("WORKERS", "1")),
            "worker_class": os.getenv("WORKER_CLASS", "uvicorn.workers.UvicornWorker"),
            "bind": os.getenv("BIND", "0.0.0.0:8000"),
            "max_requests": int(os.getenv("MAX_REQUESTS", "1000")),
            "max_requests_jitter": int(os.getenv("MAX_REQUESTS_JITTER", "100")),
            "timeout": int(os.getenv("TIMEOUT", "30")),
            "keepalive": int(os.getenv("KEEPALIVE", "2"))
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed_environments = ["development", "testing", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v
    
    @validator("workers")
    def validate_workers(cls, v):
        if v <= 0:
            raise ValueError("Workers must be positive")
        return v
    
    @validator("timeout")
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class KubernetesConfig(BaseModel):
    """Kubernetes configuration"""
    namespace: str = Field(default="trading-system", description="Kubernetes namespace")
    image: str = Field(default="trading-api:latest", description="Docker image")
    replicas: int = Field(default=3, description="Number of replicas")
    cpu_request: str = Field(default="100m", description="CPU request")
    cpu_limit: str = Field(default="500m", description="CPU limit")
    memory_request: str = Field(default="256Mi", description="Memory request")
    memory_limit: str = Field(default="512Mi", description="Memory limit")
    
    @validator("replicas")
    def validate_replicas(cls, v):
        if v <= 0:
            raise ValueError("Replicas must be positive")
        return v


class DockerConfig(BaseModel):
    """Docker configuration"""
    image: str = Field(default="trading-api:latest", description="Docker image")
    tag: str = Field(default="v1.0.0", description="Image tag")
    registry: str = Field(default="docker.io", description="Docker registry")
    repository: str = Field(default="trading-system", description="Repository name")
    build_context: str = Field(default=".", description="Build context")
    dockerfile: str = Field(default="Dockerfile", description="Dockerfile path")
