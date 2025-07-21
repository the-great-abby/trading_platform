"""
Configuration for Market Data Worker
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class WorkerConfig:
    """Configuration for the market data worker"""
    
    # RabbitMQ settings
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq-service:5672/"
    
    # Data fetching settings
    update_interval_minutes: int = 15
    gap_fill_days: int = 7
    max_concurrent_jobs: int = 5
    
    # API settings
    polygon_api_key: str = ""
    rate_limit_delay: float = 1.0  # seconds between requests
    
    # Database settings
    database_url: str = ""
    
    # Logging
    log_level: str = "INFO"
    
    # Job priorities
    job_priorities: Dict[str, int] = None
    
    def __post_init__(self):
        # Load from environment variables
        self.rabbitmq_url = os.getenv('RABBITMQ_URL', self.rabbitmq_url)
        self.update_interval_minutes = int(os.getenv('MARKET_DATA_UPDATE_INTERVAL', str(self.update_interval_minutes)))
        self.gap_fill_days = int(os.getenv('MARKET_DATA_GAP_FILL_DAYS', str(self.gap_fill_days)))
        self.max_concurrent_jobs = int(os.getenv('MAX_CONCURRENT_JOBS', str(self.max_concurrent_jobs)))
        self.polygon_api_key = os.getenv('POLYGON_API_KEY', self.polygon_api_key)
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', str(self.rate_limit_delay)))
        self.database_url = os.getenv('DATABASE_URL', self.database_url)
        self.log_level = os.getenv('LOG_LEVEL', self.log_level)
        
        # Set default job priorities
        if self.job_priorities is None:
            self.job_priorities = {
                'fetch_ohlcv': 5,
                'fetch_options': 3,
                'fill_gaps': 7,
                'cleanup_cache': 1
            }


def get_worker_config() -> WorkerConfig:
    """Get worker configuration"""
    return WorkerConfig() 