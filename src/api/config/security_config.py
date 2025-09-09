"""
Security configuration
"""

import os
from pydantic import BaseModel, Field, validator
from typing import List


class SecurityConfig(BaseModel):
    """Security configuration"""
    secret_key: str = Field(default="your-secret-key-here", description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    password_require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    password_require_numbers: bool = Field(default=True, description="Require numbers")
    password_require_special_chars: bool = Field(default=True, description="Require special characters")
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {
            "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
            "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            "password_min_length": int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            "password_require_uppercase": os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
            "password_require_lowercase": os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true",
            "password_require_numbers": os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true",
            "password_require_special_chars": os.getenv("PASSWORD_REQUIRE_SPECIAL_CHARS", "true").lower() == "true"
        }
        
        # Override with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @validator("algorithm")
    def validate_algorithm(cls, v):
        allowed_algorithms = ["HS256", "HS512", "RS256", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"Algorithm must be one of: {allowed_algorithms}")
        return v
    
    @validator("access_token_expire_minutes")
    def validate_access_token_expire_minutes(cls, v):
        if v <= 0:
            raise ValueError("Access token expiration must be positive")
        return v
    
    @validator("refresh_token_expire_days")
    def validate_refresh_token_expire_days(cls, v):
        if v <= 0:
            raise ValueError("Refresh token expiration must be positive")
        return v
    
    @validator("password_min_length")
    def validate_password_min_length(cls, v):
        if v <= 0:
            raise ValueError("Password minimum length must be positive")
        return v


class JWTConfig(BaseModel):
    """JWT configuration"""
    secret_key: str = Field(..., description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    @validator("algorithm")
    def validate_algorithm(cls, v):
        allowed_algorithms = ["HS256", "HS512", "RS256", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"Algorithm must be one of: {allowed_algorithms}")
        return v


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = Field(default=100, description="Requests per minute")
    requests_per_hour: int = Field(default=1000, description="Requests per hour")
    requests_per_day: int = Field(default=10000, description="Requests per day")
    burst_size: int = Field(default=50, description="Burst size")
    
    @validator("requests_per_minute")
    def validate_requests_per_minute(cls, v):
        if v <= 0:
            raise ValueError("Requests per minute must be positive")
        return v
    
    @validator("requests_per_hour")
    def validate_requests_per_hour(cls, v):
        if v <= 0:
            raise ValueError("Requests per hour must be positive")
        return v
    
    @validator("requests_per_day")
    def validate_requests_per_day(cls, v):
        if v <= 0:
            raise ValueError("Requests per day must be positive")
        return v
    
    @validator("burst_size")
    def validate_burst_size(cls, v):
        if v <= 0:
            raise ValueError("Burst size must be positive")
        return v
