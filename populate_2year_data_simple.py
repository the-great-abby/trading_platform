#!/usr/bin/env python3
"""
Populate Database with 2 Years of Historical Data (Simplified)
Uses the working Polygon provider to fetch and store 2 years of data
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.market_data_provider import get_market_data_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def populate_2year_data():
    """Populate database with 2 years of historical data"""
    print("🏗️  Populating Database with 2 Years of Historical Data")
    print("=" * 70)
    
    # Calculate 2-year date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)  # ~2 years
    
    print(f"📅 Target Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Top 10 symbols for testing
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "UNH", "JNJ", "JPM"]
    
    # Initialize market data manager
    market_data_manager = get_market_data_manager()
    
    # Performance tracking
    total_records = 0
    successful_symbols = 0
    failed_symbols = 0
    start_time = time.time()
    
    print(f"\n🔍 Processing {len(symbols)} symbols...")
    print("-" * 50)
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n📈 {i}/{len(symbols)}: Processing {symbol}...")
        
        try:
            symbol_start_time = time.time()
            
            # Fetch data from Polygon
            data = market_data_manager.get_historical_data(
                symbol, 
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d'), 
                "1d"
            )
            
            if data is not None and not data.empty:
                symbol_time = time.time() - symbol_start_time
                successful_symbols += 1
                total_records += len(data)
                
                print(f"   ✅ Success: {len(data)} records fetched in {symbol_time:.2f}s")
                print(f"   📊 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                print(f"   💰 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                print(f"   📈 Avg volume: {data['Volume'].mean():,.0f}")
                
                # Show sample data
                print(f"   📋 Sample data:")
                print(f"      {data.head(3).to_string()}")
                
            else:
                failed_symbols += 1
                print(f"   ❌ Failed: No data returned")
                
        except Exception as e:
            failed_symbols += 1
            print(f"   ❌ Error: {str(e)}")
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"📊 POPULATION RESULTS")
    print(f"=" * 70)
    print(f"✅ Successful symbols: {successful_symbols}/{len(symbols)}")
    print(f"❌ Failed symbols: {failed_symbols}/{len(symbols)}")
    print(f"📈 Total records fetched: {total_records:,}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"⚡ Average time per symbol: {total_time/len(symbols):.2f}s")
    
    if successful_symbols > 0:
        print(f"🎯 Success rate: {(successful_symbols/len(symbols)*100):.1f}%")
        print(f"📈 Average records per symbol: {total_records/successful_symbols:.0f}")
    
    print(f"\n✅ 2-YEAR DATA FETCHING COMPLETE!")
    print(f"🎉 Ready to store in database!")
    print(f"\n📝 Next steps:")
    print(f"   1. Run database storage script")
    print(f"   2. Verify data in PostgreSQL")
    print(f"   3. Use for backtesting")

if __name__ == "__main__":
    populate_2year_data() 