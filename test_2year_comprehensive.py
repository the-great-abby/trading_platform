#!/usr/bin/env python3
"""
Test 2-Year Comprehensive Data - Checks that 2 years of data is present in the database for a set of symbols
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.database.market_data_service import MarketDataDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_2year_comprehensive():
    """Test that 2 years of data is present in the database for a set of symbols"""
    print("\U0001F4C8 Testing 2-Year Comprehensive Data in Database")
    print("=" * 60)

    # Calculate 2-year date range
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=2*365)

    print(f"Checking period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()

    # Symbols to check
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    # Get database service
    db_service = MarketDataDatabaseService()

    print(f"Checking data for {len(symbols)} symbols...")
    for symbol in symbols:
        print(f"  - {symbol}")
        data = db_service.get_historical_data(symbol, start_date.date(), end_date.date())
        count = len(data) if data is not None else 0
        if count > 0:
            print(f"    \u2705 {count} records found")
        else:
            print(f"    \u274c No records found")
    print("\n\u2705 2-Year Comprehensive Data Check Complete!")

if __name__ == "__main__":
    test_2year_comprehensive() 