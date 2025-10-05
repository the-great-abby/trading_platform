#!/usr/bin/env python3
"""
Fetch 5 years of historical data for all core stocks using the market-data-service API
"""

import requests
import json
import time
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core stocks (excluding ETFs)
CORE_STOCKS = [
    'AAPL', 'ABBV', 'ADBE', 'AMD', 'AMZN', 'AVGO', 'AXP', 'BA', 'BAC', 'C',
    'CAT', 'COP', 'CRM', 'CSCO', 'CVS', 'CVX', 'DIS', 'EOG', 'FDX', 'GE',
    'GOOGL', 'GS', 'HD', 'HON', 'INTC', 'JNJ', 'JPM', 'KO', 'LLY', 'MA',
    'MCD', 'META', 'MMM', 'MRK', 'MS', 'MSFT', 'NFLX', 'NKE', 'NVDA', 'ORCL',
    'PEP', 'PFE', 'PG', 'PYPL', 'QCOM', 'SBUX', 'SLB', 'SMCI', 'TSLA', 'TXN',
    'UNH', 'UPS', 'V', 'WFC', 'WMT', 'XOM'
]

API_BASE_URL = "http://localhost:8081"
HISTORICAL_ENDPOINT = f"{API_BASE_URL}/market-data/historical"

def fetch_historical_data(symbol, start_date="2020-01-01", end_date="2025-01-01"):
    """Fetch historical data for a single symbol"""
    payload = {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "interval": "1d"
    }
    
    try:
        logger.info(f"Fetching data for {symbol}...")
        response = requests.post(HISTORICAL_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        data_points = len(data.get('data', []))
        
        logger.info(f"✅ {symbol}: {data_points} data points from {start_date} to {end_date}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error for {symbol}: {e}")
        return None

def fetch_all_core_stocks():
    """Fetch 5 years of data for all core stocks"""
    logger.info(f"🚀 Starting to fetch 5 years of data for {len(CORE_STOCKS)} core stocks")
    logger.info(f"📅 Date range: 2020-01-01 to 2025-01-01")
    
    results = {}
    successful_fetches = 0
    failed_fetches = 0
    
    for i, symbol in enumerate(CORE_STOCKS, 1):
        logger.info(f"\n📊 Progress: {i}/{len(CORE_STOCKS)} - Processing {symbol}")
        
        data = fetch_historical_data(symbol)
        
        if data:
            results[symbol] = data
            successful_fetches += 1
        else:
            failed_fetches += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Summary
    logger.info(f"\n🎯 FETCH COMPLETE!")
    logger.info(f"✅ Successful: {successful_fetches}")
    logger.info(f"❌ Failed: {failed_fetches}")
    logger.info(f"📈 Total symbols processed: {len(CORE_STOCKS)}")
    
    # Save results to file
    output_file = f"5year_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Results saved to: {output_file}")
    
    return results

def analyze_data_coverage(results):
    """Analyze the data coverage for each symbol"""
    logger.info(f"\n📊 DATA COVERAGE ANALYSIS:")
    logger.info(f"{'Symbol':<8} {'Data Points':<12} {'Start Date':<12} {'End Date':<12} {'Years':<6}")
    logger.info("-" * 60)
    
    for symbol, data in results.items():
        if data and 'data' in data:
            data_points = len(data['data'])
            if data_points > 0:
                start_date = data['data'][0]['date']
                end_date = data['data'][-1]['date']
                
                # Calculate years
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                years = (end_dt - start_dt).days / 365.25
                
                logger.info(f"{symbol:<8} {data_points:<12} {start_date:<12} {end_date:<12} {years:.1f}")
            else:
                logger.info(f"{symbol:<8} {'No data':<12} {'N/A':<12} {'N/A':<12} {'N/A':<6}")
        else:
            logger.info(f"{symbol:<8} {'Failed':<12} {'N/A':<12} {'N/A':<12} {'N/A':<6}")

if __name__ == "__main__":
    logger.info("🏴‍☠️ Starting 5-year historical data fetch for core stocks")
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Market data service is available")
        else:
            logger.error("❌ Market data service is not responding")
            exit(1)
    except Exception as e:
        logger.error(f"❌ Cannot connect to market data service: {e}")
        exit(1)
    
    # Fetch all data
    results = fetch_all_core_stocks()
    
    # Analyze coverage
    analyze_data_coverage(results)
    
    logger.info("\n🏴‍☠️ Data fetch complete! Ready for comprehensive backtesting!")

