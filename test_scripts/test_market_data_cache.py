#!/usr/bin/env python3
"""
Test Market Data Cache
Simple script to test if market data cache is working
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
from src.services.database.market_data_service import MarketDataService
from src.utils.trading_config import get_symbols

async def test_market_data_cache():
    """Test market data cache functionality"""
    
    print("🧪 Testing Market Data Cache")
    print("=" * 50)
    
    # Initialize services
    market_data_manager = get_cached_market_data_manager()
    market_data_service = MarketDataService()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Date range (last 7 days)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"📅 Date Range: {start_date} to {end_date}")
    print(f"📈 Test Symbols: {test_symbols}")
    print()
    
    for symbol in test_symbols:
        print(f"🔍 Testing {symbol}...")
        
        try:
            # Fetch data using cached manager
            data = market_data_manager.get_historical_data(
                symbol, start_date, end_date, '1d'
            )
            
            if data is not None and len(data) > 0:
                print(f"✅ {symbol}: {len(data)} records fetched")
                print(f"   Latest: {data.index[-1].strftime('%Y-%m-%d')}")
                print(f"   Close: ${data['Close'].iloc[-1]:.2f}")
            else:
                print(f"❌ {symbol}: No data returned")
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
        
        print()
    
    # Check database tables
    print("🗄️ Checking database tables...")
    try:
        # This would require database connection
        print("   (Database check would go here)")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_market_data_cache()) 