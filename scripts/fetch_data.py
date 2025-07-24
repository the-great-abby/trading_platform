#!/usr/bin/env python3
"""
Data Fetching Script - Fetch historical market data from Polygon
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')

from src.services.backtest.backtest_data_scanner import scan_backtest_data, get_backtest_coverage
from src.utils.trading_config import get_symbols

def fetch_recent_data():
    """Fetch recent data (last 30 days) for all symbols"""
    symbols = get_symbols()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"Fetching data for {len(symbols)} symbols from {start_date} to {end_date}")
    
    results = scan_backtest_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        force_refresh=False
    )
    
    total_records = sum(r.records_fetched for r in results)
    successful_symbols = sum(1 for r in results if r.success)
    
    print(f"Data fetch complete:")
    print(f"  Symbols processed: {len(results)}")
    print(f"  Successful: {successful_symbols}")
    print(f"  Total records: {total_records:,}")
    
    return results

def fetch_custom_data(symbols, start_date, end_date, interval='1d'):
    """Fetch custom data for specific symbols and date range"""
    if not symbols:
        symbols = get_symbols()
    
    print(f"Fetching data for {len(symbols)} symbols: {symbols}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    
    results = scan_backtest_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        force_refresh=False
    )
    
    total_records = sum(r.records_fetched for r in results)
    successful_symbols = sum(1 for r in results if r.success)
    
    print(f"Data fetch complete:")
    print(f"  Symbols processed: {len(results)}")
    print(f"  Successful: {successful_symbols}")
    print(f"  Total records: {total_records:,}")
    
    for result in results:
        print(f"  {result.symbol}: {result.records_fetched} records")
    
    return results

def check_coverage():
    """Check data coverage for all symbols"""
    symbols = get_symbols()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"Checking data coverage for {len(symbols)} symbols")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 80)
    
    coverage = get_backtest_coverage(symbols, start_date, end_date)
    
    # Sort by coverage rate
    sorted_coverage = sorted(coverage.items(), key=lambda x: x[1]['coverage_rate'], reverse=True)
    
    print(f"{'Symbol':<10} {'Records':<10} {'Expected':<10} {'Coverage':<10} {'Missing':<10}")
    print("-" * 80)
    
    for symbol, data in sorted_coverage:
        coverage_rate = data['coverage_rate']
        records = data['stored_records']
        expected = data['expected_records']
        missing = data['missing_records']
        
        print(f"{symbol:<10} {records:<10} {expected:<10} {coverage_rate:>7.1f}% {missing:<10}")
    
    # Summary
    total_symbols = len(coverage)
    symbols_with_data = sum(1 for data in coverage.values() if data['stored_records'] > 0)
    avg_coverage = sum(data['coverage_rate'] for data in coverage.values()) / total_symbols
    
    print("=" * 80)
    print(f"Summary:")
    print(f"  Total symbols: {total_symbols}")
    print(f"  Symbols with data: {symbols_with_data}")
    print(f"  Average coverage: {avg_coverage:.1f}%")

def show_status():
    """Show current data status"""
    print("=== Current Data Status ===")
    
    # This would need to be implemented with direct database access
    # For now, we'll use the coverage check
    check_coverage()

def main():
    parser = argparse.ArgumentParser(description='Fetch historical market data')
    parser.add_argument('action', choices=['recent', 'custom', 'coverage', 'status'], 
                       help='Action to perform')
    parser.add_argument('--symbols', nargs='+', help='Symbols to fetch (for custom action)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--interval', default='1d', help='Data interval (1d, 1h, 5m)')
    
    args = parser.parse_args()
    
    if args.action == 'recent':
        fetch_recent_data()
    elif args.action == 'custom':
        if not args.start_date or not args.end_date:
            print("Error: --start-date and --end-date are required for custom action")
            return
        fetch_custom_data(args.symbols, args.start_date, args.end_date, args.interval)
    elif args.action == 'coverage':
        check_coverage()
    elif args.action == 'status':
        show_status()

if __name__ == "__main__":
    main() 