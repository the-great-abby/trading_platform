#!/usr/bin/env python3
"""
Demo script for Backtest API Client
Tests the backtest API endpoints with Kubernetes support
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.backtest_api_client import BacktestAPIClient
from loguru import logger


async def demo_backtest_api():
    """Demo the backtest API client"""
    print("🚀 ORION Mission Control - Backtest API Demo")
    print("=" * 50)
    
    # Determine API URL based on environment
    api_url = None
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        print("📍 Detected Kubernetes environment")
        api_url = "http://trading-ingress.trading-system.svc.cluster.local/api/v1/backtest"
    else:
        print("📍 Using local development environment")
        # For local development, you can use port forwarding:
        # kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
        api_url = "http://localhost:10001"
    
    print(f"🌐 API URL: {api_url}")
    print()
    
    async with BacktestAPIClient(api_url) as client:
        print("1️⃣ Testing API connection...")
        try:
            # Test basic connectivity
            response = await client.client.get(f"{api_url}/")
            print(f"✅ API is responding (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            print("\n💡 Troubleshooting tips:")
            print("   - For Kubernetes: Ensure backtest-api service is deployed")
            print("   - For local: Run: kubectl port-forward svc/backtest-api 10001:10001 -n trading-system")
            print("   - Check if the API service is running")
            return
        
        print("\n2️⃣ Fetching backtest runs...")
        runs = await client.list_backtest_runs(limit=5)
        if runs:
            print(f"✅ Found {len(runs)} backtest runs")
            for run in runs[:3]:  # Show first 3
                print(f"   📊 Run ID: {run.get('id', 'N/A')}")
                print(f"      Strategy: {run.get('strategy_name', 'N/A')}")
                print(f"      Status: {run.get('status', 'N/A')}")
        else:
            print("⚠️  No backtest runs found")
        
        print("\n3️⃣ Fetching strategies...")
        strategies = await client.get_strategies()
        if strategies:
            print(f"✅ Found {len(strategies)} strategies")
            for strategy in strategies[:3]:  # Show first 3
                print(f"   📈 Strategy: {strategy.get('name', 'N/A')}")
        else:
            print("⚠️  No strategies found")
        
        print("\n4️⃣ Getting overall statistics...")
        stats = await client.get_stats()
        if stats.get('success'):
            data = stats.get('data', {})
            print("✅ Statistics retrieved:")
            print(f"   📊 Total runs: {data.get('total_runs', 'N/A')}")
            print(f"   📈 Total strategies: {data.get('total_strategies', 'N/A')}")
        else:
            print("⚠️  Could not retrieve statistics")
        
        print("\n5️⃣ Comparing strategies...")
        comparison = await client.compare_strategies()
        if comparison.get('success'):
            summary = comparison.get('summary', {})
            print("✅ Strategy comparison:")
            print(f"   📊 Best strategy: {summary.get('best_strategy', 'N/A')}")
            print(f"   📈 Best return: {summary.get('best_return', 'N/A')}%")
        else:
            print("⚠️  Could not compare strategies")
    
    print("\n🎯 Demo completed!")
    print("This is ORION, Mission Control. Backtest API demo finished successfully!")


if __name__ == "__main__":
    asyncio.run(demo_backtest_api()) 