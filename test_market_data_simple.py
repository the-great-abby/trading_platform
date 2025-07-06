#!/usr/bin/env python3
"""
Simple Market Data Test - Check what each provider can return
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_data.yahoo_finance_service import YahooFinanceService
from src.services.market_data.market_data_provider import AlphaVantageProvider, PolygonProvider

def test_providers():
    """Test each provider individually"""
    
    print("🔍 Testing Market Data Providers")
    print("=" * 50)
    
    # Test period - last 30 days
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    
    print(f"Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # Test Yahoo Finance
    print("1. Testing Yahoo Finance...")
    try:
        yahoo = YahooFinanceService()
        data = yahoo.get_historical_data('AAPL', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if data is not None and len(data) > 0:
            print(f"   ✅ Success: {len(data)} records")
            print(f"   📅 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
            print(f"   💰 Latest close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test Alpha Vantage
    print("2. Testing Alpha Vantage...")
    try:
        alpha = AlphaVantageProvider()
        data = alpha.get_historical_data('AAPL', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if data is not None and len(data) > 0:
            print(f"   ✅ Success: {len(data)} records")
            print(f"   📅 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
            print(f"   💰 Latest close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test Polygon
    print("3. Testing Polygon...")
    try:
        polygon = PolygonProvider()
        data = polygon.get_historical_data('AAPL', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if data is not None and len(data) > 0:
            print(f"   ✅ Success: {len(data)} records")
            print(f"   📅 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
            print(f"   💰 Latest close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()

if __name__ == "__main__":
    test_providers() 