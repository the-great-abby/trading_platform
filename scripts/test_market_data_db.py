#!/usr/bin/env python3
"""
Test script to verify market data database query works correctly
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append('/app')

from src.services.database.market_data_service import MarketDataService

def test_database_query():
    """Test the database query for NVDA"""
    try:
        # Initialize the database service
        db_service = MarketDataService()
        
        # Get recent data for NVDA
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        print(f"🔍 Testing database query for NVDA from {start_date} to {end_date}")
        
        # Try to get data from database
        data = db_service.get_historical_data('NVDA', start_date, end_date, provider="polygon", interval="1d")
        
        if data is not None and not data.empty:
            print(f"✅ Found {len(data)} records in database")
            print(f"📊 Data columns: {list(data.columns)}")
            print(f"📅 Date range: {data.index.min()} to {data.index.max()}")
            print(f"💰 Latest close price: {data['Close'].iloc[-1]}")
            print(f"📈 Sample data:")
            print(data.tail(3))
            return True
        else:
            print("❌ No data found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database query: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_query()
    sys.exit(0 if success else 1) 