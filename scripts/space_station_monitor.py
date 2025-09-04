#!/usr/bin/env python3
"""
Space Trading Station Monitor - Standalone CLI Tool
Inspired by Unix 'top' command for real-time trading performance tracking
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.space_station_monitor import SpaceStationMonitor


async def main():
    """Main function to run the Space Station Monitor"""
    print("🚀 SPACE TRADING STATION MONITOR")
    print("=" * 50)
    print("This is ORION, Mission Control.")
    print("Real-time trading performance monitoring...")
    print()
    
    # Create monitor instance
    monitor = SpaceStationMonitor(refresh_interval=3)  # Update every 3 seconds
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n🛑 Mission Control shutdown initiated by user")
        await monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ Mission Control error: {e}")
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main()) 