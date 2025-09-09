"""
Logging configuration
"""

import os
from pydantic import BaseModel, Field, validator
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: LogFormat = Field(default=LogFormat.JSON, description="Log format")
    file_path: str = Field(default="logs/api.log", description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "level": LogLevel(os.getenv("LOG_LEVEL", "INFO")),
            "format": LogFormat(os.getenv("LOG_FORMAT", "JSON")),
            "file_path": os.getenv("LOG_FILE_PATH", "logs/api.log"),
            "max_file_size": int(os.getenv("LOG_MAX_FILE_SIZE", "10485760")),
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
            "enable_console": os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true",
            "enable_file": os.getenv("LOG_ENABLE_FILE", "true").lower() == "true"
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError("Max file size must be positive")
        return v
    
    @validator("backup_count")
    def validate_backup_count(cls, v):
        if v < 0:
            raise ValueError("Backup count must be non-negative")
        return v
