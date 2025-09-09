#!/usr/bin/env python3
"""
CQRS API Startup Script
Production startup script for the CQRS API service
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.cqrs_api import app
from src.api.config.api_config import APIConfig
from src.api.config.security_config import JWTConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    try:
        # Load configuration
        api_config = APIConfig()
        jwt_config = JWTConfig()
        
        logger.info("Starting CQRS API service...")
        logger.info(f"API Host: {api_config.host}")
        logger.info(f"API Port: {api_config.port}")
        logger.info(f"Environment: {api_config.environment}")
        
        # Import uvicorn here to avoid import issues
        import uvicorn
        
        # Start the server
        uvicorn.run(
            app,
            host=api_config.host,
            port=api_config.port,
            log_level="info",
            access_log=True,
            reload=False  # Disable reload in production
        )
        
    except Exception as e:
        logger.error(f"Failed to start CQRS API service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
