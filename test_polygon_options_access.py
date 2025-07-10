#!/usr/bin/env python3
"""
Test script to verify Polygon options API access
"""

import os
import requests
import json
from datetime import datetime, timedelta

def test_polygon_options_access():
    """Test Polygon options API access"""
    
    # Get API key from environment
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("❌ POLYGON_API_KEY not found in environment")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test 1: Check API key validity with a simple request
    print("\n📡 Test 1: Checking API key validity...")
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-01?apiKey={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ API key is valid")
        elif response.status_code == 401:
            print("❌ API key is invalid")
            return False
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False
    
    # Test 2: Check options chain endpoint
    print("\n📡 Test 2: Testing options chain endpoint...")
    try:
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Test options chain for AAPL
        url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=AAPL&expiration_date.gte={today}&apiKey={api_key}"
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                print(f"✅ Found {len(data['results'])} options contracts for AAPL")
                if data['results']:
                    contract = data['results'][0]
                    print(f"Sample contract: {contract.get('strike_price', 'N/A')} {contract.get('contract_type', 'N/A')} expiring {contract.get('expiration_date', 'N/A')}")
                return True
            else:
                print("⚠️ No results in response")
        elif response.status_code == 403:
            print("❌ Access denied - options data may not be included in your subscription")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing options endpoint: {e}")
        return False
    
    # Test 3: Check options trades endpoint
    print("\n📡 Test 3: Testing options trades endpoint...")
    try:
        url = f"https://api.polygon.io/v3/reference/options/trades?apiKey={api_key}&limit=1"
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                print("✅ Options trades endpoint accessible")
                return True
            else:
                print("⚠️ No options trades data available")
        else:
            print(f"❌ Options trades endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing options trades: {e}")
        return False
    
    return False

if __name__ == "__main__":
    print("🔍 Testing Polygon Options API Access")
    print("=" * 50)
    
    success = test_polygon_options_access()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Polygon options API access confirmed")
    else:
        print("❌ Polygon options API access failed")
        print("\n💡 Troubleshooting tips:")
        print("1. Verify your Polygon subscription includes options data")
        print("2. Check that your API key is correct")
        print("3. Ensure you're not hitting rate limits")
        print("4. Contact Polygon support if issues persist") 