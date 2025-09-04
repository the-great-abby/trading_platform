#!/usr/bin/env python3
"""
Populate 2-Year Market Data
Fetches and stores 2 years of market data for all symbols in the database
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
from src.utils.trading_config import get_symbols

logger = get_trading_logger()

async def populate_2year_data():
    """Populate database with 2 years of market data"""
    
    print("📊 POPULATE 2-YEAR MARKET DATA")
    print("=" * 60)
    print("Fetching and storing 2 years of market data for all symbols")
    print("=" * 60)
    
    # Configuration
    start_date = "2023-07-10"
    end_date = "2025-07-09"
    
    # Get all symbols
    symbols = get_symbols() or []
    
    print(f"📊 Configuration:")
    print(f"   📅 Date Range: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} symbols")
    print(f"   🗄️  Target: Database storage")
    print()
    
    # Initialize market data manager with API access
    # Force API access by setting DATABASE_ONLY to false
    os.environ['DATABASE_ONLY'] = 'false'
    market_data_manager = get_cached_market_data_manager()
    
    # Disable cache to force API fetching
    market_data_manager.enable_cache(False)
    
    print(f"🏃 Starting data population...")
    print(f"   This will fetch data from external APIs")
    print(f"   Estimated time: 2-5 minutes for {len(symbols)} symbols")
    print()
    
    start_time = datetime.now()
    
    successful_symbols = 0
    failed_symbols = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"📊 Processing {symbol} ({i}/{len(symbols)})...")
        
        try:
            # Fetch data with force refresh
            data = market_data_manager.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d",
                force_refresh=True
            )
            
            if data is not None and len(data) > 0:
                print(f"   ✅ {symbol}: {len(data)} data points")
                print(f"   📅 Range: {data.index.min()} to {data.index.max()}")
                print(f"   💰 Latest: ${data['Close'].iloc[-1]:.2f}")
                successful_symbols += 1
            else:
                print(f"   ❌ {symbol}: No data returned")
                failed_symbols += 1
                
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {e}")
            failed_symbols += 1
        
        print()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"⏱️  Data population completed in {duration}")
    print()
    print(f"📊 Results:")
    print(f"   ✅ Successful: {successful_symbols} symbols")
    print(f"   ❌ Failed: {failed_symbols} symbols")
    print(f"   📈 Success Rate: {(successful_symbols/len(symbols)*100):.1f}%")
    print()
    
    if successful_symbols > 0:
        print("✅ Database now contains 2 years of market data!")
        print("   You can now run backtests with the full date range.")
    else:
        print("❌ No data was successfully populated.")
        print("   Check API keys and network connectivity.")

async def main():
    """Main function"""
    try:
        await populate_2year_data()
    except Exception as e:
        logger.error(f"❌ Error in data population: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 