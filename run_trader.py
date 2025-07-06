#!/usr/bin/env python3
"""
Simple script to run the algorithmic trading bot
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    print("🤖 Starting AlgoTrader...")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 AlgoTrader stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 