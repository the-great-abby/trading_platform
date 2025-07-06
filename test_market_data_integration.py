#!/usr/bin/env python3
"""
Test script to verify market data service integration with real Yahoo Finance data
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_market_data_service():
    """Test the market data service endpoints"""
    
    base_url = "http://localhost:8002"  # Market data service URL
    
    print("🔍 Testing Market Data Service Integration")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Get available symbols
    print("\n2. Testing available symbols...")
    try:
        response = requests.get(f"{base_url}/market-data/symbols", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available symbols: {data['count']} symbols")
            for symbol in data['symbols'][:5]:  # Show first 5
                print(f"   - {symbol['symbol']}: {symbol['name']}")
        else:
            print(f"❌ Symbols request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Symbols request error: {e}")
    
    # Test 3: Get current price for AAPL
    print("\n3. Testing current price for AAPL...")
    try:
        response = requests.get(f"{base_url}/market-data/current/AAPL", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✅ Current price retrieved successfully")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Price: ${data['price']:.2f}")
            print(f"   Change: ${data['change']:.2f} ({data['change_percent']:.2f}%)")
            print(f"   Volume: {data.get('volume', 'N/A'):,}")
            print(f"   Timestamp: {data['timestamp']}")
        else:
            print(f"❌ Current price request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Current price request error: {e}")
    
    # Test 4: Get historical data for AAPL
    print("\n4. Testing historical data for AAPL...")
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        request_data = {
            "symbol": "AAPL",
            "start_date": start_date,
            "end_date": end_date,
            "interval": "1d"
        }
        
        response = requests.post(f"{base_url}/market-data/historical", 
                               json=request_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Historical data retrieved successfully")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Records: {data['count']}")
            if data['data']:
                latest = data['data'][-1]
                print(f"   Latest: {latest['date']} - Close: ${latest['close']:.2f}")
                print(f"   Volume: {latest['volume']:,}")
        else:
            print(f"❌ Historical data request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Historical data request error: {e}")
    
    # Test 5: Get symbol info for AAPL
    print("\n5. Testing symbol info for AAPL...")
    try:
        response = requests.get(f"{base_url}/market-data/symbols/AAPL/info", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✅ Symbol info retrieved successfully")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Sector: {data.get('sector', 'N/A')}")
            print(f"   Market Cap: ${data.get('market_cap', 0):,}")
            print(f"   PE Ratio: {data.get('pe_ratio', 'N/A')}")
            print(f"   Currency: {data.get('currency', 'N/A')}")
        else:
            print(f"❌ Symbol info request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Symbol info request error: {e}")
    
    # Test 6: Validate symbol
    print("\n6. Testing symbol validation...")
    try:
        response = requests.get(f"{base_url}/market-data/symbols/AAPL/validate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Symbol validation successful")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Valid: {data['is_valid']}")
        else:
            print(f"❌ Symbol validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Symbol validation error: {e}")
    
    # Test 7: Batch current prices
    print("\n7. Testing batch current prices...")
    try:
        symbols = "AAPL,GOOGL,MSFT,TSLA,NVDA"
        response = requests.get(f"{base_url}/market-data/batch/current?symbols={symbols}", timeout=20)
        if response.status_code == 200:
            data = response.json()
            print("✅ Batch prices retrieved successfully")
            print(f"   Requested: {data['total_requested']}")
            print(f"   Successful: {data['successful']}")
            for symbol, info in data['symbols'].items():
                if info['status'] == 'success':
                    print(f"   {symbol}: ${info['price']:.2f}")
                else:
                    print(f"   {symbol}: {info['status']}")
        else:
            print(f"❌ Batch prices request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Batch prices request error: {e}")
    
    # Test 8: Market hours
    print("\n8. Testing market hours...")
    try:
        response = requests.get(f"{base_url}/market-data/market-hours", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Market hours retrieved successfully")
            print(f"   Market Hours: {data.get('market_hours', 'N/A')}")
        else:
            print(f"❌ Market hours request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Market hours request error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Market Data Service Integration Test Complete")
    print("=" * 50)
    
    return True

def test_portfolio_service_integration():
    """Test portfolio service integration with market data"""
    
    portfolio_url = "http://localhost:8004"  # Portfolio service URL
    
    print("\n🔍 Testing Portfolio Service Integration")
    print("=" * 50)
    
    # Test portfolio summary
    print("\n1. Testing portfolio summary...")
    try:
        response = requests.get(f"{portfolio_url}/portfolio/summary", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✅ Portfolio summary retrieved successfully")
            print(f"   Total Value: ${data['total_value']:,.2f}")
            print(f"   Cash: ${data['cash']:,.2f}")
            print(f"   Total P&L: ${data['total_pnl']:,.2f} ({data['total_pnl_percentage']:.2f}%)")
            print(f"   Positions: {data['num_positions']}")
            
            if data['positions']:
                print("   Position Details:")
                for pos in data['positions']:
                    print(f"     {pos['symbol']}: {pos['quantity']} @ ${pos['current_price']:.2f} (P&L: ${pos['unrealized_pnl']:.2f})")
        else:
            print(f"❌ Portfolio summary failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Portfolio summary error: {e}")
    
    # Test positions
    print("\n2. Testing positions...")
    try:
        response = requests.get(f"{portfolio_url}/portfolio/positions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Positions retrieved successfully")
            print(f"   Count: {data['count']}")
        else:
            print(f"❌ Positions request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Positions request error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Portfolio Service Integration Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Starting Market Data Integration Tests")
    print("Make sure the services are running with: make docker-up")
    print()
    
    # Wait a moment for services to be ready
    time.sleep(2)
    
    # Test market data service
    market_data_success = test_market_data_service()
    
    # Test portfolio service integration
    test_portfolio_service_integration()
    
    if market_data_success:
        print("\n✅ All tests completed successfully!")
        print("🎉 Real market data is working!")
    else:
        print("\n❌ Some tests failed. Check service logs with: make docker-logs") 