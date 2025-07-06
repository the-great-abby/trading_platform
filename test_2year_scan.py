#!/usr/bin/env python3
"""
Test 2-Year Data Scan - Fetches 2 years of historical data for a set of symbols
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_data.market_data_provider import get_market_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_2year_scan():
    """Test fetching 2 years of historical data for a set of symbols"""
    print("\U0001F50D Testing 2-Year Data Scan")
    print("=" * 50)

    # Calculate 2-year date range
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=2*365)

    print(f"Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()

    # Symbols to test
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    # Get market data manager
    manager = get_market_data_manager()

    print(f"Fetching data for {len(symbols)} symbols...")
    for symbol in symbols:
        print(f"  - {symbol}")
        data = manager.get_historical_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if data is not None and len(data) > 0:
            print(f"    \u2705 Success: {len(data)} records, {data.index.min()} to {data.index.max()}")
        else:
            print(f"    \u274c No data returned")
    print("\n\u2705 2-Year Data Scan Complete!")

if __name__ == "__main__":
    test_2year_scan() 