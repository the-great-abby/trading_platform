#!/usr/bin/env python3
"""
Main entry point for Strategy Engine Testing Framework
"""

import asyncio
import logging
import sys
from typing import Optional

from .config import get_config, load_config_from_env
from .database.connection import init_database, close_database
from .api.main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("strategy_testing_framework.log")
    ]
)

logger = logging.getLogger(__name__)


async def startup():
    """Application startup"""
    logger.info("Starting Strategy Engine Testing Framework")
    
    try:
        # Load configuration
        config = load_config_from_env()
        logger.info(f"Configuration loaded: API on {config.api_host}:{config.api_port}")
        
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize other services here (Redis, etc.)
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


async def shutdown():
    """Application shutdown"""
    logger.info("Shutting down Strategy Engine Testing Framework")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
        # Close other services here
        logger.info("All services shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> app:
    """Create and configure the FastAPI application"""
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Run startup
    asyncio.run(startup())
    
    try:
        # Start the server
        config = get_config()
        uvicorn.run(
            "src.testing.api.main:app",
            host=config.api_host,
            port=config.api_port,
            workers=config.api_workers,
            log_level=config.log_level.lower(),
            reload=config.debug
        )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Run shutdown
        asyncio.run(shutdown())













