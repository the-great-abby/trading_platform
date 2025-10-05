#!/usr/bin/env python3
"""
Test Elliott Wave Service from within Kubernetes

This script demonstrates how to call the Elliott Wave service using
the internal Kubernetes service address for backtesting.
"""

import sys
import os
sys.path.append('src')

import requests
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Internal Kubernetes service address
ELLIOTT_SERVICE_URL = "http://elliott-wave-service.trading-system.svc.cluster.local:8000"
TRACKED_SYMBOLS = ["SPY", "QQQ", "AAPL"]

async def test_kubernetes_elliott_wave_service():
    """Test the Elliott Wave service using internal Kubernetes address"""
    
    print("🎯 TESTING ELLIOTT WAVE SERVICE FROM KUBERNETES")
    print("=" * 60)
    print(f"📡 Service URL: {ELLIOTT_SERVICE_URL}")
    print(f"📊 Symbols: {', '.join(TRACKED_SYMBOLS)}")
    print()
    
    # Test dates for backtesting
    test_dates = [
        "2023-01-15",  # January 2023
        "2023-06-15",  # June 2023
        "2023-12-15",  # December 2023
    ]
    
    print("🔍 Testing Backtesting Endpoints")
    print("-" * 40)
    
    for test_date in test_dates:
        print(f"📅 Historical date: {test_date}")
        
        for symbol in TRACKED_SYMBOLS:
            try:
                # Test the backtest endpoint using internal Kubernetes address
                url = f"{ELLIOTT_SERVICE_URL}/elliott-wave/backtest/{symbol}"
                params = {
                    "historical_date": test_date,
                    "timeframe": "1d"
                }
                
                print(f"   🔍 Analyzing {symbol} for {test_date}...")
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("pattern_found", False):
                    pattern_type = result.get("pattern_type", "unknown")
                    confidence = result.get("confidence", 0.0)
                    data_points = result.get("data_points", 0)
                    swing_points = result.get("swing_points", 0)
                    
                    print(f"      ✅ Pattern found: {pattern_type}")
                    print(f"      📊 Confidence: {confidence:.2f}")
                    print(f"      📈 Data points: {data_points}")
                    print(f"      🌊 Swing points: {swing_points}")
                    
                    if result.get("target_price"):
                        print(f"      🎯 Target price: ${result.get('target_price', 0):.2f}")
                    if result.get("invalidation_level"):
                        print(f"      🛑 Invalidation level: ${result.get('invalidation_level', 0):.2f}")
                else:
                    message = result.get("message", "No pattern detected")
                    data_points = result.get("data_points", 0)
                    swing_points = result.get("swing_points", 0)
                    
                    print(f"      ❌ No pattern: {message}")
                    print(f"      📈 Data points: {data_points}")
                    print(f"      🌊 Swing points: {swing_points}")
                
                analysis_time = result.get("analysis_time", 0)
                print(f"      ⏱️  Analysis time: {analysis_time:.3f}s")
                
            except requests.exceptions.RequestException as e:
                print(f"      ❌ Error calling service for {symbol}: {e}")
            except Exception as e:
                print(f"      ❌ Unexpected error for {symbol}: {e}")
        
        print()
    
    print("🔍 Testing Live Data Endpoints")
    print("-" * 40)
    
    for symbol in TRACKED_SYMBOLS:
        try:
            # Test the live endpoint using internal Kubernetes address
            url = f"{ELLIOTT_SERVICE_URL}/elliott-wave/analyze/{symbol}"
            params = {
                "timeframe": "1d"
            }
            
            print(f"🔍 Analyzing {symbol} for live data...")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("pattern_found", False):
                pattern_type = result.get("pattern_type", "unknown")
                confidence = result.get("confidence", 0.0)
                
                print(f"   ✅ Pattern found: {pattern_type}")
                print(f"   📊 Confidence: {confidence:.2f}")
                
                if result.get("target_price"):
                    print(f"   🎯 Target price: ${result.get('target_price', 0):.2f}")
                if result.get("invalidation_level"):
                    print(f"   🛑 Invalidation level: ${result.get('invalidation_level', 0):.2f}")
            else:
                message = result.get("message", "No pattern detected")
                print(f"   ❌ No pattern: {message}")
            
            analysis_time = result.get("analysis_time", 0)
            print(f"   ⏱️  Analysis time: {analysis_time:.3f}s")
            print()
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error calling service for {symbol}: {e}")
            print()
        except Exception as e:
            print(f"   ❌ Unexpected error for {symbol}: {e}")
            print()
    
    print("🎉 Kubernetes Elliott Wave service test completed!")

async def test_service_health():
    """Test if the Elliott Wave service is accessible from within Kubernetes"""
    
    print("🎯 TESTING ELLIOTT WAVE SERVICE HEALTH (KUBERNETES)")
    print("=" * 60)
    print(f"📡 Service URL: {ELLIOTT_SERVICE_URL}")
    print()
    
    try:
        # Test the root endpoint
        url = f"{ELLIOTT_SERVICE_URL}/"
        
        print("🔍 Checking service health...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"   ✅ Service is accessible from within Kubernetes")
        print(f"   📝 Message: {result.get('message', 'Unknown')}")
        print(f"   🔢 Version: {result.get('version', 'Unknown')}")
        print(f"   📊 Symbols tracked: {result.get('symbols_tracked', 0)}")
        print()
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Service not accessible: {e}")
        print("   💡 Make sure you're running this from within the Kubernetes cluster")
        print("      or that the service is properly configured")
        print()
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        print()
        return False

async def main():
    """Main test function"""
    
    print("🚀 KUBERNETES ELLIOTT WAVE SERVICE TEST SUITE")
    print("=" * 70)
    print()
    
    # Test service health first
    service_healthy = await test_service_health()
    
    if not service_healthy:
        print("❌ Service is not accessible from within Kubernetes.")
        print("💡 This script is designed to run from within the Kubernetes cluster.")
        return
    
    print()
    
    # Test the service
    await test_kubernetes_elliott_wave_service()
    
    print("🎉 All Kubernetes tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

