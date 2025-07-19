#!/usr/bin/env python3
"""
Script to run the FastAPI web interface
"""

import uvicorn
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("🌐 Starting AlgoTrader API...")
    print("Visit http://localhost:8000 for the web interface")
    print("API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 