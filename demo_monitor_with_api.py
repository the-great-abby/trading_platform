#!/usr/bin/env python3
"""
Demo: Space Station Monitor with Backtest API Integration
Shows how the monitor on the host connects to the API in Kubernetes
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.space_station_monitor import SpaceStationMonitor
from loguru import logger


async def demo_monitor_with_api():
    """Demo the monitor with API integration"""
    print("🚀 ORION Mission Control - Monitor with API Integration Demo")
    print("=" * 60)
    print()
    print("📡 Architecture:")
    print("   Host Monitor ←→ Kubernetes API ←→ Database")
    print("   (Your Machine)    (Containers)    (PostgreSQL)")
    print()
    print("🔗 Connection Flow:")
    print("   1. Monitor runs on your host machine")
    print("   2. Monitor connects to backtest-api service in Kubernetes")
    print("   3. API service queries the database")
    print("   4. Real-time data flows back to your monitor")
    print()
    
    # Create monitor instance
    monitor = SpaceStationMonitor(refresh_interval=3)
    
    print("🌐 API Connection Status:")
    if monitor.backtest_api_client:
        print("   ✅ Backtest API client available")
        print("   📍 Will connect to Kubernetes API service")
    else:
        print("   ❌ Backtest API client not available")
        print("   💡 Run: pip install httpx")
    
    print()
    print("📊 Data Sources:")
    print("   • Real-time API data from Kubernetes")
    print("   • System metrics from host")
    print("   • Simulated data (fallback)")
    print()
    
    print("🚀 Starting monitor...")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
        await monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ Error: {e}")
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(demo_monitor_with_api()) 