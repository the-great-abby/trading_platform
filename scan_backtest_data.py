#!/usr/bin/env python3
"""
Backtest Data Scanner Script
Fetches and stores historical OHLCV data in the database to reduce API calls
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict

# Add src to path
sys.path.append('src')

from src.services.backtest.backtest_data_scanner import (
    BacktestDataScanner, 
    ScanConfig, 
    scan_backtest_data, 
    get_backtest_coverage
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_default_symbols() -> List[str]:
    """Get default symbols for scanning"""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',  # Tech
        'JPM', 'BAC', 'WFC', 'GS', 'MS',          # Finance
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',       # Healthcare
        'XOM', 'CVX', 'COP', 'EOG', 'SLB',        # Energy
        'SPY', 'QQQ', 'IWM', 'VTI', 'VOO'         # ETFs
    ]


def get_backtest_periods() -> List[Dict]:
    """Get common backtest periods"""
    return [
        # Recent periods
        {"start_date": "2024-01-01", "end_date": "2024-12-31", "interval": "1d"},
        {"start_date": "2023-01-01", "end_date": "2023-12-31", "interval": "1d"},
        {"start_date": "2022-01-01", "end_date": "2022-12-31", "interval": "1d"},
        
        # Longer periods for comprehensive backtesting
        {"start_date": "2018-01-01", "end_date": "2024-12-31", "interval": "1d"},
        
        # Intraday periods (if needed)
        {"start_date": "2024-01-01", "end_date": "2024-01-31", "interval": "1h"},
        {"start_date": "2024-02-01", "end_date": "2024-02-29", "interval": "1h"},
    ]


def scan_single_period(symbols: List[str], start_date: str, end_date: str, 
                      interval: str = "1d", force_refresh: bool = False) -> List:
    """Scan a single time period"""
    
    print(f"🔍 Scanning {len(symbols)} symbols from {start_date} to {end_date}")
    print(f"📊 Interval: {interval}")
    print(f"🔄 Force refresh: {force_refresh}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create scanner and scan
    scanner = BacktestDataScanner()
    config = ScanConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        force_refresh=force_refresh,
        parallel_workers=4
    )
    
    results = asyncio.run(scanner.scan_symbols(config))
    
    scan_time = time.time() - start_time
    
    # Print results
    print(f"\n⏱️  Scan completed in {scan_time:.2f} seconds")
    print("📈 Results:")
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")
    
    if successful:
        total_records = sum(r.records_fetched for r in successful)
        total_api_calls = sum(r.api_calls for r in successful)
        total_cache_hits = sum(r.cache_hits for r in successful)
        
        print(f"   📊 Total records: {total_records:,}")
        print(f"   🌐 API calls: {total_api_calls}")
        print(f"   ⚡ Cache hits: {total_cache_hits}")
        
        if total_api_calls + total_cache_hits > 0:
            cache_rate = (total_cache_hits / (total_api_calls + total_cache_hits)) * 100
            print(f"   📈 Cache hit rate: {cache_rate:.1f}%")
    
    if failed:
        print(f"\n❌ Failed symbols:")
        for result in failed:
            print(f"   {result.symbol}: {result.error_message}")
    
    return results


def scan_multiple_periods(symbols: List[str], periods: List[Dict], 
                         force_refresh: bool = False) -> List:
    """Scan multiple time periods"""
    
    print(f"🚀 Starting multi-period scan for {len(symbols)} symbols")
    print(f"📅 Scanning {len(periods)} periods")
    print("=" * 60)
    
    all_results = []
    
    for i, period in enumerate(periods, 1):
        print(f"\n📅 Period {i}/{len(periods)}: {period['start_date']} to {period['end_date']}")
        
        results = scan_single_period(
            symbols=symbols,
            start_date=period['start_date'],
            end_date=period['end_date'],
            interval=period.get('interval', '1d'),
            force_refresh=force_refresh
        )
        
        all_results.extend(results)
    
    return all_results


def check_coverage(symbols: List[str], start_date: str, end_date: str):
    """Check database coverage for symbols"""
    
    print(f"🔍 Checking database coverage for {len(symbols)} symbols")
    print(f"📅 Period: {start_date} to {end_date}")
    print("=" * 60)
    
    coverage = get_backtest_coverage(symbols, start_date, end_date)
    
    print("📊 Coverage Summary:")
    print(f"{'Symbol':<10} {'Stored':<8} {'Expected':<10} {'Coverage':<10} {'Missing':<8}")
    print("-" * 50)
    
    total_stored = 0
    total_expected = 0
    
    for symbol, data in coverage.items():
        stored = data['stored_records']
        expected = data['expected_records']
        coverage_rate = data['coverage_rate']
        missing = data['missing_records']
        
        total_stored += stored
        total_expected += expected
        
        print(f"{symbol:<10} {stored:<8} {expected:<10} {coverage_rate:<10.1f}% {missing:<8}")
    
    print("-" * 50)
    overall_coverage = (total_stored / total_expected * 100) if total_expected > 0 else 0
    print(f"{'TOTAL':<10} {total_stored:<8} {total_expected:<10} {overall_coverage:<10.1f}% {total_expected - total_stored:<8}")
    
    return coverage


def main():
    parser = argparse.ArgumentParser(description='Backtest Data Scanner')
    parser.add_argument('--symbols', nargs='+', default=get_default_symbols(),
                       help='Symbols to scan (default: common stocks and ETFs)')
    parser.add_argument('--start-date', default='2024-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--interval', default='1d',
                       help='Data interval (1d, 1h, 5m)')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh even if data exists in cache')
    parser.add_argument('--multi-period', action='store_true',
                       help='Scan multiple common backtest periods')
    parser.add_argument('--check-coverage', action='store_true',
                       help='Check database coverage instead of scanning')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old data (keep last 365 days)')
    
    args = parser.parse_args()
    
    print("🔍 Backtest Data Scanner")
    print("=" * 50)
    print(f"📊 Symbols: {len(args.symbols)} symbols")
    print(f"📅 Period: {args.start_date} to {args.end_date}")
    print(f"⏱️  Interval: {args.interval}")
    print(f"🔄 Force refresh: {args.force_refresh}")
    print("=" * 50)
    
    if args.check_coverage:
        # Check coverage
        check_coverage(args.symbols, args.start_date, args.end_date)
        return
    
    if args.cleanup:
        # Clean up old data
        scanner = BacktestDataScanner()
        deleted_count = scanner.cleanup_old_data(days_to_keep=365)
        print(f"🧹 Cleaned up {deleted_count} old records")
        return
    
    if args.multi_period:
        # Scan multiple periods
        periods = get_backtest_periods()
        results = scan_multiple_periods(args.symbols, periods, args.force_refresh)
        
        # Print final summary
        scanner = BacktestDataScanner()
        scanner.scan_results = results
        summary = scanner.get_scan_summary()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Symbols: {summary['total_symbols']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Records: {summary['total_records_fetched']:,}")
        print(f"Cache Hit Rate: {summary['cache_hit_rate']:.1f}%")
        print(f"API Call Reduction: {summary['api_call_reduction']:.1f}%")
        print(f"Providers Used: {', '.join(summary['providers_used'])}")
        
    else:
        # Scan single period
        scan_single_period(
            symbols=args.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            interval=args.interval,
            force_refresh=args.force_refresh
        )


if __name__ == "__main__":
    import asyncio
    main() 