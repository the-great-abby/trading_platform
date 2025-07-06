#!/usr/bin/env python3
"""
Fetch and Store Polygon Data
Fetches fresh data from Polygon API and stores it in the database
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Add src to path
sys.path.append('src')

from src.services.market_data.market_data_provider import get_market_data_manager
from src.services.database.market_data_service import MarketDataDatabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_and_store_polygon_data():
    """Fetch data from Polygon API and store in database"""
    
    print("🚀 FETCHING AND STORING POLYGON DATA")
    print("=" * 60)
    
    # Configuration - Use specified date range for all symbols
    start_date = "2023-07-06"  # Start date
    end_date = "2025-07-03"    # End date
    
    # All symbols we want data for
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',  # Tech stocks
        'JPM', 'GS', 'PFE', 'MRK', 'UNH',          # Finance & Healthcare
        'SPY', 'VTI', 'COP'                        # ETFs & Energy
    ]
    
    print(f"📊 Configuration:")
    print(f"   📅 Date Range: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} stocks")
    print(f"   🎯 Provider: Polygon API")
    print(f"   💾 Storage: PostgreSQL Database")
    print()
    
    # Initialize services
    market_data_manager = get_market_data_manager()
    db_service = MarketDataDatabaseService()
    
    # Performance tracking
    total_stored = 0
    successful_symbols = 0
    failed_symbols = 0
    start_time = time.time()
    
    print(f"🔍 Processing {len(symbols)} symbols...")
    print("-" * 50)
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n📈 {i}/{len(symbols)}: Processing {symbol}...")
        
        try:
            symbol_start_time = time.time()
            
            # Fetch data from Polygon
            data = market_data_manager.get_historical_data(
                symbol, 
                start_date, 
                end_date, 
                "1d"
            )
            
            if data is not None and not data.empty:
                # Store in database
                success = db_service.store_historical_data(
                    symbol=symbol,
                    data=data,
                    provider="polygon",
                    interval="1d"
                )
                
                if success:
                    symbol_time = time.time() - symbol_start_time
                    successful_symbols += 1
                    total_stored += len(data)
                    
                    print(f"   ✅ Success: {len(data)} records fetched and stored in {symbol_time:.2f}s")
                    print(f"   📊 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                    print(f"   💰 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                    print(f"   📈 Avg volume: {data['Volume'].mean():,.0f}")
                    
                else:
                    failed_symbols += 1
                    print(f"   ❌ Failed: Database storage error")
                    
            else:
                failed_symbols += 1
                print(f"   ❌ Failed: No data returned from Polygon")
                
        except Exception as e:
            failed_symbols += 1
            print(f"   ❌ Error: {str(e)}")
        
        # Rate limiting - wait between requests
        if i < len(symbols):
            print(f"   ⏳ Waiting 2 seconds before next request...")
            time.sleep(2)
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 FETCH AND STORE RESULTS")
    print(f"=" * 60)
    print(f"✅ Successful symbols: {successful_symbols}/{len(symbols)}")
    print(f"❌ Failed symbols: {failed_symbols}/{len(symbols)}")
    print(f"📈 Total records stored: {total_stored:,}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"⚡ Average time per symbol: {total_time/len(symbols):.2f}s")
    
    if successful_symbols > 0:
        print(f"🎯 Success rate: {(successful_symbols/len(symbols)*100):.1f}%")
        print(f"📈 Average records per symbol: {total_stored/successful_symbols:.0f}")
    
    # Verify database contents
    print(f"\n🔍 VERIFYING DATABASE CONTENTS")
    print(f"-" * 40)
    
    try:
        # Get total records
        session = db_service.get_session()
        
        # Get total records for our date range
        from sqlalchemy import text
        result = session.execute(text("""
            SELECT COUNT(*) as total 
            FROM historical_prices 
            WHERE date >= :start_date AND date <= :end_date
        """), {
            'start_date': start_date,
            'end_date': end_date
        })
        total_records = result.fetchone()[0]
        
        # Get symbol count for our date range
        result = session.execute(text("""
            SELECT COUNT(DISTINCT symbol) as symbols 
            FROM historical_prices 
            WHERE date >= :start_date AND date <= :end_date
        """), {
            'start_date': start_date,
            'end_date': end_date
        })
        symbol_count = result.fetchone()[0]
        
        print(f"📊 Total records in date range: {total_records:,}")
        print(f"📈 Unique symbols: {symbol_count}")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # Get records per symbol for our date range
        result = session.execute(text("""
            SELECT symbol, COUNT(*) as records, MIN(date) as start_date, MAX(date) as end_date 
            FROM historical_prices 
            WHERE date >= :start_date AND date <= :end_date
            GROUP BY symbol 
            ORDER BY records DESC
        """), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        print(f"\n📈 Records per symbol:")
        for row in result.fetchall():
            print(f"   {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
    
    print(f"\n✅ Data fetch and store completed!")
    print(f"🎉 Database now has fresh Polygon data for backtesting!")


if __name__ == "__main__":
    fetch_and_store_polygon_data() 