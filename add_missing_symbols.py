#!/usr/bin/env python3
"""
Add Missing Symbols to Database
Adds the symbols we successfully fetched (AMZN, TSLA, NVDA, META, UNH, JNJ) to the database
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.market_data_provider import get_market_data_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def add_missing_symbols():
    """Add missing symbols to database"""
    print("➕ Adding Missing Symbols to Database")
    print("=" * 60)
    
    # Database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot')
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Calculate 2-year date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)  # ~2 years
    
    print(f"📅 Target Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Missing symbols to add (these were successfully fetched in our test)
    missing_symbols = ["AMZN", "TSLA", "NVDA", "META", "UNH", "JNJ"]
    
    # Initialize market data manager
    market_data_manager = get_market_data_manager()
    
    # Performance tracking
    total_stored = 0
    successful_symbols = 0
    failed_symbols = 0
    start_time = time.time()
    
    print(f"\n🔍 Processing {len(missing_symbols)} missing symbols...")
    print("-" * 50)
    
    for i, symbol in enumerate(missing_symbols, 1):
        print(f"\n📈 {i}/{len(missing_symbols)}: Processing {symbol}...")
        
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
                # Store in database
                session = SessionLocal()
                try:
                    stored_count = 0
                    
                    for index, row in data.iterrows():
                        # Handle different date formats
                        if hasattr(index, 'date'):
                            record_date = index.date()
                        elif isinstance(index, str):
                            record_date = datetime.strptime(index, '%Y-%m-%d').date()
                        else:
                            record_date = index
                        
                        # Insert or update record
                        insert_query = text("""
                            INSERT INTO historical_prices 
                            (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
                            VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :provider, :interval)
                            ON CONFLICT (symbol, date) 
                            DO UPDATE SET 
                                open_price = EXCLUDED.open_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                close_price = EXCLUDED.close_price,
                                volume = EXCLUDED.volume,
                                provider = EXCLUDED.provider,
                                interval = EXCLUDED.interval
                        """)
                        
                        session.execute(insert_query, {
                            'symbol': symbol,
                            'date': record_date,
                            'open': float(row.get('Open', row.get('open', 0))),
                            'high': float(row.get('High', row.get('high', 0))),
                            'low': float(row.get('Low', row.get('low', 0))),
                            'close': float(row.get('Close', row.get('close', 0))),
                            'volume': int(row.get('Volume', row.get('volume', 0))),
                            'provider': 'polygon',
                            'interval': '1d'
                        })
                        stored_count += 1
                    
                    session.commit()
                    
                    symbol_time = time.time() - symbol_start_time
                    successful_symbols += 1
                    total_stored += stored_count
                    
                    print(f"   ✅ Success: {len(data)} records fetched, {stored_count} stored in {symbol_time:.2f}s")
                    print(f"   📊 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                    print(f"   💰 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                    print(f"   📈 Avg volume: {data['Volume'].mean():,.0f}")
                    
                except SQLAlchemyError as e:
                    session.rollback()
                    print(f"   ❌ Database error: {str(e)}")
                    failed_symbols += 1
                finally:
                    session.close()
                    
            else:
                failed_symbols += 1
                print(f"   ❌ Failed: No data returned")
                
        except Exception as e:
            failed_symbols += 1
            print(f"   ❌ Error: {str(e)}")
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 ADDITION RESULTS")
    print(f"=" * 60)
    print(f"✅ Successful symbols: {successful_symbols}/{len(missing_symbols)}")
    print(f"❌ Failed symbols: {failed_symbols}/{len(missing_symbols)}")
    print(f"📈 Total records stored: {total_stored:,}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"⚡ Average time per symbol: {total_time/len(missing_symbols):.2f}s")
    
    if successful_symbols > 0:
        print(f"🎯 Success rate: {(successful_symbols/len(missing_symbols)*100):.1f}%")
        print(f"📈 Average records per symbol: {total_stored/successful_symbols:.0f}")
    
    # Verify database contents
    print(f"\n🔍 VERIFYING DATABASE CONTENTS")
    print(f"-" * 40)
    
    try:
        session = SessionLocal()
        
        # Get total records
        result = session.execute(text("SELECT COUNT(*) as total FROM historical_prices"))
        total_records = result.fetchone()[0]
        
        # Get symbol count
        result = session.execute(text("SELECT COUNT(DISTINCT symbol) as symbols FROM historical_prices"))
        symbol_count = result.fetchone()[0]
        
        # Get date range
        result = session.execute(text("SELECT MIN(date) as start_date, MAX(date) as end_date FROM historical_prices"))
        date_range = result.fetchone()
        
        print(f"📊 Total records in database: {total_records:,}")
        print(f"📈 Unique symbols: {symbol_count}")
        print(f"📅 Database date range: {date_range[0]} to {date_range[1]}")
        print(f"📊 Days of data: {(date_range[1] - date_range[0]).days}")
        
        # Get records per symbol
        result = session.execute(text("""
            SELECT symbol, COUNT(*) as records, MIN(date) as start_date, MAX(date) as end_date 
            FROM historical_prices 
            GROUP BY symbol 
            ORDER BY records DESC
        """))
        
        print(f"\n📈 Records per symbol:")
        for row in result.fetchall():
            print(f"   {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
    
    print(f"\n✅ MISSING SYMBOLS ADDED!")
    print(f"🎉 Database now has more comprehensive data!")

if __name__ == "__main__":
    add_missing_symbols() 