#!/usr/bin/env python3
"""
Backtest API Service - Main entry point
Runs the backtest API on port 10001
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.api.backtest_api import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 10001
    port = int(os.getenv("API_PORT", "10001"))
    
    print(f"🚀 Starting Backtest API Service on port {port}")
    print("This is ORION, Mission Control. Backtest API is now active!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 