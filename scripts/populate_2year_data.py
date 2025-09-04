#!/usr/bin/env python3
"""
Populate Database with 2 Years of Historical Data
Uses the working Polygon provider to fetch and store 2 years of data
"""

import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_data.market_data_provider import get_market_data_manager
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
    market_data_manager = get_market_data_manager()
    market_data_service = MarketDataService(config.database_url)
    
    # Use centralized symbol list
    symbols = get_symbols()
    
    # Calculate date range (2 years ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    print(f"📊 Populating 2 years of historical data for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    successful_symbols = 0
    failed_symbols = 0
    
    # Performance tracking
    total_records = 0
    start_time = time.time()
    
    print(f"\n🔍 Processing {len(symbols)} symbols...")
    print("-" * 50)
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n📈 {i}/{len(symbols)}: Processing {symbol}...")
        
        try:
            symbol_start_time = time.time()
            
            # Fetch data from market data manager
            data = market_data_manager.get_historical_data(
                symbol, 
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d'), 
                "1d"
            )
            
            if data is not None and not data.empty:
                # Store in database
                stored_count = market_data_service.store_historical_data(symbol, data)
                
                symbol_time = time.time() - symbol_start_time
                successful_symbols += 1
                total_records += stored_count
                
                print(f"   ✅ Success: {len(data)} records fetched, {stored_count} stored in {symbol_time:.2f}s")
                if len(data) > 0:
                    first_date = data.index[0] if hasattr(data.index[0], 'strftime') else str(data.index[0])
                    last_date = data.index[-1] if hasattr(data.index[-1], 'strftime') else str(data.index[-1])
                    print(f"   📊 Date range: {first_date} to {last_date}")
                    if 'Low' in data.columns and 'High' in data.columns:
                        print(f"   💰 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                
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
    print(f"📈 Total records stored: {total_records:,}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"⚡ Average time per symbol: {total_time/len(symbols):.2f}s")
    
    if successful_symbols > 0:
        print(f"🎯 Success rate: {(successful_symbols/len(symbols)*100):.1f}%")
        print(f"📈 Average records per symbol: {total_records/successful_symbols:.0f}")
    
    # Verify database contents
    print(f"\n🔍 VERIFYING DATABASE CONTENTS")
    print(f"-" * 40)
    
    try:
        # Get database statistics
        all_symbols = market_data_service.get_all_symbols()
        print(f"📊 Total symbols in database: {len(all_symbols)}")
        print(f"📈 Unique symbols: {len(all_symbols)}")
        print(f"📅 Database symbols: {all_symbols[:10]}...")
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
    
    print(f"\n✅ 2-YEAR DATA POPULATION COMPLETE!")
    print(f"🎉 Database ready for backtesting!")

if __name__ == "__main__":
    asyncio.run(populate_historical_data()) 