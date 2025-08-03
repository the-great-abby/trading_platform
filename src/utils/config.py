"""
Configuration management for the trading bot
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
from src.utils.trading_config import get_symbols, get_options_symbols

load_dotenv()


@dataclass
class Config:
    """Configuration class for the trading bot"""
    
    # API Configuration
    alpaca_api_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")
    alpaca_base_url: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    # Public API Configuration
    public_api_key: str = os.getenv("PUBLIC_API_KEY", "")
    public_api_secret: str = os.getenv("PUBLIC_API_SECRET", "")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "https://api.public.com")
    public_username: str = os.getenv("PUBLIC_USERNAME", "")
    public_password: str = os.getenv("PUBLIC_PASSWORD", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///algo_trader.db")
    
    # RabbitMQ Configuration
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # Trading Configuration
    initial_capital: float = float(os.getenv("INITIAL_CAPITAL", "10000"))
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", "0.1"))
    stop_loss_percentage: float = float(os.getenv("STOP_LOSS_PERCENTAGE", "0.02"))
    take_profit_percentage: float = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "0.05"))
    trading_interval: int = int(os.getenv("TRADING_INTERVAL", "60"))  # seconds
    
    # Risk Management
    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", "0.05"))
    max_positions: int = int(os.getenv("MAX_POSITIONS", "5"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/trader.log")
    
    # Data Configuration
    data_provider: str = os.getenv("DATA_PROVIDER", "public")  # Changed default to public
    historical_days: int = int(os.getenv("HISTORICAL_DAYS", "30"))
    
    # Symbol lists - use default_factory for mutable defaults
    symbols: Optional[List[str]] = field(default_factory=get_symbols)
    options_symbols: Optional[List[str]] = field(default_factory=get_options_symbols)
    
    def get(self, key: str, default=None):
        """Get configuration value by key (for compatibility with dict-like access)"""
        return getattr(self, key.lower(), default)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.data_provider == "public":
            if not self.public_username or not self.public_password:
                print("Warning: Public API credentials not configured")
                return False
        elif self.data_provider == "alpaca":
            if not self.alpaca_api_key or not self.alpaca_secret_key:
                print("Warning: Alpaca API credentials not configured")
                return False
        return True


def get_config() -> Config:
    """Get configuration instance"""
    return Config() 