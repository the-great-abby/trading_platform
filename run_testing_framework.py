#!/usr/bin/env python3
"""
Startup script for Strategy Engine Testing Framework
"""

import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.testing.main import create_app
from src.testing.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Global variable to track if shutdown is requested
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    sys.exit(0)

def main():
    """Main entry point"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        # Get configuration
        config = get_config()
        logger.info(f"Starting Strategy Engine Testing Framework on {config.api_host}:{config.api_port}")
        logger.info(f"API Documentation: http://{config.api_host}:{config.api_port}/docs")
        logger.info(f"Health Check: http://{config.api_host}:{config.api_port}/api/v1/testing/health")
        logger.info("Press Ctrl+C to stop the server")
        
        # Import and run uvicorn
        import uvicorn
        uvicorn.run(
            create_app(),
            host=config.api_host,
            port=config.api_port,
            workers=config.api_workers,
            log_level="info",
            reload=False
        )
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C) - shutting down gracefully")
    except SystemExit as e:
        logger.info(f"System exit requested - shutting down gracefully (exit code: {e.code})")
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.error("Shutting down due to error")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()
