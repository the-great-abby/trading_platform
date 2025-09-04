#!/usr/bin/env python3
"""
Populate Database with 2 Years of Historical Data (Simplified)
Uses the working Polygon provider to fetch and store 2 years of data
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.market_data_provider import get_market_data_manager
from src.services.database.market_data_service import MarketDataService
from src.services.market_data.yahoo_finance_service import YahooFinanceService
from src.utils.config import get_config
from src.utils.trading_config import get_symbols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def populate_historical_data():
    """Populate 2 years of historical data for all symbols"""
    config = get_config()
    
    # Initialize services
    market_data_service = MarketDataService(config.database_url)
    yahoo_service = YahooFinanceService()
    
    # Use centralized symbol list
    symbols = get_symbols()
    
    # Calculate date range (2 years ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    print(f"📊 Populating 2 years of historical data for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    successful_symbols = 0
    failed_symbols = 0
    
    # Initialize market data manager
    market_data_manager = get_market_data_manager()
    
    # Performance tracking
    total_records = 0
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
    asyncio.run(populate_historical_data()) 