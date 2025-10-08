#!/usr/bin/env python3
"""
Test Kubernetes vs Local Service Access

This script demonstrates the difference between:
1. Running from outside Kubernetes (localhost:11082 with port-forward)
2. Running from inside Kubernetes (internal service address)
"""

import requests
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_service_access():
    """Test both local and Kubernetes service access"""
    
    print("🎯 ELLIOTT WAVE SERVICE ACCESS TEST")
    print("=" * 60)
    
    # Test configurations
    configs = [
        {
            "name": "Local (Port-Forward)",
            "url": "http://localhost:11082",
            "description": "Running from outside Kubernetes with port-forward"
        },
        {
            "name": "Kubernetes Internal",
            "url": "http://elliott-wave-service.trading-system.svc.cluster.local:8000",
            "description": "Running from inside Kubernetes cluster"
        }
    ]
    
    test_symbol = "SPY"
    test_date = "2023-01-15"
    
    for config in configs:
        print(f"\n🔍 Testing: {config['name']}")
        print(f"📡 URL: {config['url']}")
        print(f"💡 Description: {config['description']}")
        print("-" * 50)
        
        try:
            # Test health endpoint
            health_url = f"{config['url']}/elliott-wave/health"
            print(f"   🏥 Health check: {health_url}")
            
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Health check: PASSED")
            else:
                print(f"   ❌ Health check: FAILED ({response.status_code})")
                continue
                
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection failed: {e}")
            print(f"   💡 This is expected when running from outside Kubernetes")
            continue
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
        
        # Test backtesting endpoint
        try:
            backtest_url = f"{config['url']}/elliott-wave/backtest/{test_symbol}"
            params = {
                "historical_date": test_date,
                "timeframe": "1d"
            }
            
            print(f"   🔍 Backtest analysis: {backtest_url}")
            
            response = requests.get(backtest_url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("pattern_found", False):
                print(f"   ✅ Pattern found: {result.get('pattern_type', 'unknown')}")
                print(f"   📊 Confidence: {result.get('confidence', 0.0):.2f}")
                print(f"   📈 Data points: {result.get('data_points', 0)}")
                print(f"   🌊 Swing points: {result.get('swing_points', 0)}")
                print(f"   ⏱️  Analysis time: {result.get('analysis_time', 0):.3f}s")
            else:
                print(f"   ❌ No pattern found: {result.get('message', 'No pattern')}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Backtest request failed: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

def print_usage_scenarios():
    """Print usage scenarios for different environments"""
    
    print("\n🎯 USAGE SCENARIOS")
    print("=" * 60)
    
    print("\n📊 SCENARIO 1: Running from OUTSIDE Kubernetes")
    print("-" * 50)
    print("🔧 Setup:")
    print("   1. kubectl port-forward svc/elliott-wave-service 11082:8000 -n trading-system")
    print("   2. Use URL: http://localhost:11082")
    print("   3. Run backtest scripts from your local machine")
    print()
    print("✅ Pros:")
    print("   - Easy to test and debug")
    print("   - Direct access to logs")
    print("   - No need to deploy to Kubernetes")
    print()
    print("❌ Cons:")
    print("   - Not production-like environment")
    print("   - Port-forward can be unstable")
    print("   - Different network topology")
    
    print("\n📊 SCENARIO 2: Running from INSIDE Kubernetes")
    print("-" * 50)
    print("🔧 Setup:")
    print("   1. Deploy backtest as Kubernetes Job/Pod")
    print("   2. Use URL: http://elliott-wave-service.trading-system.svc.cluster.local:8000")
    print("   3. Run backtest within the cluster")
    print()
    print("✅ Pros:")
    print("   - Production-like environment")
    print("   - Stable service discovery")
    print("   - Same network as live trading")
    print("   - Can scale independently")
    print()
    print("❌ Cons:")
    print("   - Harder to debug")
    print("   - Need to deploy to Kubernetes")
    print("   - More complex setup")
    
    print("\n🎯 RECOMMENDED APPROACH")
    print("-" * 50)
    print("💡 For Development/Testing:")
    print("   - Use Scenario 1 (localhost:11082)")
    print("   - Test strategies and logic")
    print("   - Debug and iterate quickly")
    print()
    print("💡 For Production/Validation:")
    print("   - Use Scenario 2 (internal Kubernetes)")
    print("   - Validate in production environment")
    print("   - Ensure service reliability")
    print("   - Test with real cluster networking")

async def main():
    """Main function"""
    
    print("🚀 KUBERNETES VS LOCAL SERVICE ACCESS TEST")
    print("=" * 70)
    
    # Test service access
    await test_service_access()
    
    # Print usage scenarios
    print_usage_scenarios()
    
    print("\n🎉 Test completed!")
    print("\n💡 Next Steps:")
    print("   1. Choose the appropriate scenario for your use case")
    print("   2. Update your backtesting engine accordingly")
    print("   3. Test with real market data")
    print("   4. Deploy to production when ready")

if __name__ == "__main__":
    asyncio.run(main())

