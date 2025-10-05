"""
Environment Variable Loader for Live Trading Service
==================================================

This module handles loading and validating environment variables
for the live trading service.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class TradingEnvLoader:
    """Environment variable loader for trading service"""
    
    def __init__(self, env_file: str = '.env'):
        self.env_file = Path(env_file)
        self.loaded = False
        
    def load_env(self) -> bool:
        """
        Load environment variables from .env file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from dotenv import load_dotenv
            
            if not self.env_file.exists():
                logger.warning(f".env file not found: {self.env_file.absolute()}")
                return False
            
            # Load .env file
            load_dotenv(self.env_file)
            self.loaded = True
            logger.info(f"✅ Loaded environment variables from {self.env_file.absolute()}")
            return True
            
        except ImportError:
            logger.error("python-dotenv not installed. Run: pip install python-dotenv")
            return False
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            return False
    
    def get_env_var(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get environment variable with optional validation
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether the variable is required
            
        Returns:
            Environment variable value or default
            
        Raises:
            ValueError: If required variable is missing
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        
        return value
    
    def get_public_api_config(self) -> Dict[str, Any]:
        """Get Public.com API configuration"""
        return {
            'api_key': self.get_env_var('PUBLIC_API_KEY', required=True),
            'timeout': int(self.get_env_var('PUBLIC_API_TIMEOUT', '30')),
            'max_retries': int(self.get_env_var('PUBLIC_API_MAX_RETRIES', '3')),
            'rate_limit': int(self.get_env_var('PUBLIC_API_RATE_LIMIT', '100')),
            'rate_limit_window': int(self.get_env_var('PUBLIC_API_RATE_LIMIT_WINDOW', '60'))
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            'database_url': self.get_env_var(
                'DATABASE_URL', 
                'postgresql+asyncpg://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot'
            ),
            'redis_url': self.get_env_var(
                'REDIS_URL',
                'redis://redis.trading-system.svc.cluster.local:6379'
            )
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return {
            'max_position_size': float(self.get_env_var('MAX_POSITION_SIZE', '0.05')),
            'max_daily_loss': float(self.get_env_var('MAX_DAILY_LOSS', '1000.0')),
            'max_daily_trades': int(self.get_env_var('MAX_DAILY_TRADES', '15')),
            'risk_level': self.get_env_var('RISK_LEVEL', 'MODERATE')
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'log_level': self.get_env_var('LOG_LEVEL', 'INFO'),
            'debug': self.get_env_var('DEBUG', 'false').lower() == 'true',
            'port': int(self.get_env_var('PORT', '8080'))
        }
    
    def validate_required_vars(self) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = [
            'PUBLIC_API_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        logger.info("✅ All required environment variables are set")
        return True

# Global instance
env_loader = TradingEnvLoader()

def load_trading_env() -> bool:
    """Load trading environment variables"""
    return env_loader.load_env()

def get_public_api_config() -> Dict[str, Any]:
    """Get Public.com API configuration"""
    return env_loader.get_public_api_config()

def get_database_config() -> Dict[str, str]:
    """Get database configuration"""
    return env_loader.get_database_config()

def get_trading_config() -> Dict[str, Any]:
    """Get trading configuration"""
    return env_loader.get_trading_config()

def get_app_config() -> Dict[str, Any]:
    """Get application configuration"""
    return env_loader.get_app_config()

def validate_env() -> bool:
    """Validate environment variables"""
    return env_loader.validate_required_vars()











