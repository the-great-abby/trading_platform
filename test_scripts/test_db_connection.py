#!/usr/bin/env python3
"""
Simple database connection test
"""

import os
import sys
sys.path.append('src')

def test_db_connection():
    """Test database connection and basic operations"""
    
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    try:
        from src.services.database.market_data_service import MarketDataDatabaseService
        
        # Initialize database connection
        db_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@postgres-dev.trading-system.svc.cluster.local:5432/trading_bot')
        print(f"📊 Connecting to: {db_url}")
        
        market_data_service = MarketDataDatabaseService(db_url)
        print("✅ Database service initialized")
        
        # Test getting symbols
        print("📈 Getting available symbols...")
        symbols = market_data_service.get_all_symbols()
        print(f"✅ Found {len(symbols)} symbols: {symbols[:5]}...")
        
        # Test getting data for first symbol
        if symbols:
            symbol = symbols[0]
            print(f"📊 Getting data for {symbol}...")
            
            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            data = market_data_service.get_historical_data(symbol, start_date, end_date)
            if data is not None and not data.empty:
                print(f"✅ Got {len(data)} records for {symbol}")
                print(f"   Date range: {data.index.min()} to {data.index.max()}")
                print(f"   Latest price: ${data['Close'].iloc[-1]:.2f}")
            else:
                print(f"❌ No data found for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_db_connection() 