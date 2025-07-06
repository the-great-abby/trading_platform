#!/usr/bin/env python3
"""
Test script to verify Polygon is the primary provider
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.market_data_provider import get_market_data_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_polygon_priority():
    """Test that Polygon is the primary provider"""
    print("🧪 Testing Polygon Priority")
    print("=" * 50)
    
    # Get market data manager
    manager = get_market_data_manager()
    
    print(f"📊 Total providers: {len(manager.providers)}")
    
    # List providers in order
    for i, provider in enumerate(manager.providers):
        provider_name = provider.__class__.__name__
        print(f"  {i+1}. {provider_name}")
        
        # Check if it's Polygon
        if "Polygon" in provider_name:
            print(f"     ✅ Polygon found at position {i+1}")
            if i == 0:
                print("     🎉 Polygon is the PRIMARY provider!")
            else:
                print(f"     ⚠️  Polygon is at position {i+1}, not primary")
    
    # Test with a single symbol
    print("\n🔍 Testing data fetch with AAPL...")
    try:
        data = manager.get_historical_data("AAPL", "2024-01-01", "2024-01-31", "1d")
        if data is not None and not data.empty:
            print(f"✅ Successfully fetched {len(data)} records for AAPL")
            print(f"   First date: {data.index[0]}")
            print(f"   Last date: {data.index[-1]}")
            print(f"   Columns: {list(data.columns)}")
        else:
            print("❌ No data returned")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_polygon_priority() 