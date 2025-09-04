#!/usr/bin/env python3
"""
Test Polygon API connectivity and data retrieval
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

def test_polygon_api():
    """Test Polygon API with a simple AAPL request"""
    
    # Get API key from environment
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("❌ POLYGON_API_KEY not found in environment")
        return False
    
    print(f"🔑 Using Polygon API key: {api_key[:10]}...")
    
    # Test dates - use a known good period
    end_date = datetime(2024, 12, 31)
    start_date = end_date - timedelta(days=30)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"📅 Testing date range: {start_str} to {end_str}")
    
    # Test with AAPL
    symbol = "AAPL"
    endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{start_str}/{end_str}"
    base_url = "https://api.polygon.io"
    params = {"apiKey": api_key}
    
    url = f"{base_url}{endpoint}"
    print(f"🌐 Making request to: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response keys: {list(data.keys())}")
            
            status = data.get("status")
            results = data.get("results", [])
            
            print(f"📊 Status: {status}")
            print(f"📊 Results count: {len(results)}")
            
            if results:
                print(f"✅ Success! Got {len(results)} data points for {symbol}")
                print(f"📊 First result: {results[0]}")
                print(f"📊 Last result: {results[-1]}")
                return True
            else:
                print(f"❌ No results returned for {symbol}")
                print(f"📊 Full response: {data}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Polygon API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Polygon API connectivity...")
    success = test_polygon_api()
    if success:
        print("✅ Polygon API test successful!")
    else:
        print("❌ Polygon API test failed!") 