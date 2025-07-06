#!/usr/bin/env python3
"""
Demo: Backtest Data Scanner with Mock Data
Shows how to scan and store historical OHLCV data to reduce API calls
"""

import os
import sys
import time
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict

# Add src to path
sys.path.append('src')

from src.services.backtest.backtest_data_scanner import (
    BacktestDataScanner, 
    ScanConfig, 
    ScanResult,
    get_backtest_coverage
)

def generate_mock_data(symbol: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
    """Generate mock OHLCV data for testing"""
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate business days
    date_range = pd.bdate_range(start=start_dt, end=end_dt, freq='B')
    
    # Generate realistic price data
    np.random.seed(hash(symbol) % 1000)  # Consistent seed per symbol
    
    # Start with a base price
    base_price = 100 + (hash(symbol) % 200)  # Different base price per symbol
    
    prices = []
    current_price = base_price
    
    for _ in range(len(date_range)):
        # Daily price change (normal distribution)
        daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
        current_price *= (1 + daily_return)
        
        # Generate OHLC from close price
        volatility = current_price * 0.02  # 2% daily volatility
        
        open_price = current_price + np.random.normal(0, volatility * 0.3)
        high_price = max(open_price, current_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(open_price, current_price) - abs(np.random.normal(0, volatility * 0.5))
        close_price = current_price
        
        # Volume (log-normal distribution)
        volume = int(np.random.lognormal(10, 1)) * 1000
        
        prices.append({
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(prices, index=date_range)
    df.index.name = 'date'
    
    return df


class MockBacktestDataScanner(BacktestDataScanner):
    """Mock scanner that generates data instead of calling APIs"""
    
    def _scan_single_symbol(self, symbol: str, config: ScanConfig):
        """Override to use mock data"""
        try:
            print(f"Generating mock data for {symbol} from {config.start_date} to {config.end_date}")
            
            # Generate mock data
            data = generate_mock_data(
                symbol=symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                interval=config.interval
            )
            
            if data is None or data.empty:
                return ScanResult(
                    symbol=symbol,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    records_fetched=0,
                    records_stored=0,
                    cache_hits=0,
                    api_calls=0,
                    providers_used=[],
                    success=False,
                    error_message="No data generated"
                )
            
            # Simulate cache behavior
            records_fetched = len(data)
            cache_hits = 0  # First scan, no cache hits
            api_calls = 1   # Simulate one API call
            
            # Store data in database
            records_stored = 0
            if records_fetched > 0:
                success = self.db_service.store_historical_data(
                    symbol=symbol,
                    data=data,
                    provider="mock_scanner",
                    interval=config.interval
                )
                if success:
                    records_stored = records_fetched
                    print(f"Stored {records_stored} records for {symbol}")
                else:
                    print(f"Failed to store data for {symbol}")
            
            return ScanResult(
                symbol=symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                records_fetched=records_fetched,
                records_stored=records_stored,
                cache_hits=cache_hits,
                api_calls=api_calls,
                providers_used=["mock_provider"],
                success=True
            )
            
        except Exception as e:
            print(f"Error generating mock data for {symbol}: {e}")
            return ScanResult(
                symbol=symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                records_fetched=0,
                records_stored=0,
                cache_hits=0,
                api_calls=0,
                providers_used=[],
                success=False,
                error_message=str(e)
            )


def demo_mock_backtest_scanner():
    """Demonstrate the backtest data scanner with mock data"""
    
    print("🔍 Backtest Data Scanner Demo (Mock Data)")
    print("=" * 50)
    
    # Initialize mock scanner
    scanner = MockBacktestDataScanner()
    
    # Test symbols and periods
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    print(f"📊 Testing with symbols: {symbols}")
    print(f"📅 Period: {start_date} to {end_date}")
    
    # Demo 1: Check initial coverage
    print("\n" + "="*50)
    print("📊 DEMO 1: Initial Database Coverage")
    print("="*50)
    
    coverage = scanner.get_database_coverage(symbols, start_date, end_date)
    
    print("Initial coverage:")
    for symbol, data in coverage.items():
        print(f"   {symbol}: {data['stored_records']} records ({data['coverage_rate']:.1f}% coverage)")
    
    # Demo 2: Generate and store data
    print("\n" + "="*50)
    print("🔄 DEMO 2: Generating and Storing Historical Data")
    print("="*50)
    
    config = ScanConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval="1d",
        parallel_workers=3
    )
    
    start_time = time.time()
    results = asyncio.run(scanner.scan_symbols(config))
    scan_time = time.time() - start_time
    
    print(f"⏱️  Data generation completed in {scan_time:.2f} seconds")
    
    # Show results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")
    
    if successful:
        total_records = sum(r.records_fetched for r in successful)
        total_stored = sum(r.records_stored for r in successful)
        total_api_calls = sum(r.api_calls for r in successful)
        
        print(f"   📊 Total records generated: {total_records:,}")
        print(f"   💾 Total records stored: {total_stored:,}")
        print(f"   🌐 Simulated API calls: {total_api_calls}")
    
    if failed:
        print(f"\n❌ Failed symbols:")
        for result in failed:
            print(f"   {result.symbol}: {result.error_message}")
    
    # Demo 3: Check coverage after generation
    print("\n" + "="*50)
    print("📊 DEMO 3: Coverage After Data Generation")
    print("="*50)
    
    coverage_after = scanner.get_database_coverage(symbols, start_date, end_date)
    
    print("Coverage after generation:")
    for symbol, data in coverage_after.items():
        print(f"   {symbol}: {data['stored_records']} records ({data['coverage_rate']:.1f}% coverage)")
    
    # Demo 4: Second scan (should use database)
    print("\n" + "="*50)
    print("⚡ DEMO 4: Second Scan (Database Cache Test)")
    print("="*50)
    
    start_time = time.time()
    results2 = asyncio.run(scanner.scan_symbols(config))
    scan_time2 = time.time() - start_time
    
    print(f"⏱️  Second scan completed in {scan_time2:.2f} seconds")
    
    # Show database performance
    for result in results2:
        if result.success:
            print(f"   ⚡ {result.symbol}: {result.records_fetched} records from database")
        else:
            print(f"   ❌ {result.symbol}: {result.error_message}")
    
    # Demo 5: Performance comparison
    print("\n" + "="*50)
    print("📈 DEMO 5: Performance Comparison")
    print("="*50)
    
    speedup = scan_time / scan_time2 if scan_time2 > 0 else 0
    
    print(f"First scan time: {scan_time:.2f} seconds")
    print(f"Second scan time: {scan_time2:.2f} seconds")
    print(f"Speedup: {speedup:.1f}x faster with database cache")
    
    # Demo 6: Get scan summary
    print("\n" + "="*50)
    print("📋 DEMO 6: Scan Summary")
    print("="*50)
    
    summary = scanner.get_scan_summary()
    
    print("Final scan summary:")
    print(f"   Total symbols: {summary['total_symbols']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    print(f"   Total records: {summary['total_records_fetched']:,}")
    print(f"   Cache hit rate: {summary['cache_hit_rate']:.1f}%")
    print(f"   API call reduction: {summary['api_call_reduction']:.1f}%")
    print(f"   Providers used: {', '.join(summary['providers_used'])}")
    
    print("\n" + "="*50)
    print("🎉 Mock Demo completed successfully!")
    print("="*50)
    
    print("\n💡 Key Benefits Demonstrated:")
    print("   • Fast data generation and storage")
    print("   • Database persistence across scans")
    print("   • Parallel processing for multiple symbols")
    print("   • Coverage tracking and reporting")
    print("   • Performance improvement with caching")


def demo_multi_period_mock():
    """Demonstrate multi-period scanning with mock data"""
    
    print("\n" + "="*50)
    print("📅 MULTI-PERIOD SCAN DEMO (Mock Data)")
    print("="*50)
    
    scanner = MockBacktestDataScanner()
    
    # Define multiple periods
    periods = [
        {"start_date": "2024-01-01", "end_date": "2024-03-31", "interval": "1d"},
        {"start_date": "2024-04-01", "end_date": "2024-06-30", "interval": "1d"},
        {"start_date": "2024-07-01", "end_date": "2024-09-30", "interval": "1d"},
        {"start_date": "2024-10-01", "end_date": "2024-12-31", "interval": "1d"},
    ]
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"📊 Scanning {len(symbols)} symbols across {len(periods)} periods")
    
    start_time = time.time()
    results = scanner.scan_backtest_periods(symbols, periods)
    total_time = time.time() - start_time
    
    print(f"⏱️  Multi-period scan completed in {total_time:.2f} seconds")
    
    # Show results by period
    for i, period in enumerate(periods):
        period_results = [r for r in results if r.start_date == period['start_date']]
        if period_results:
            total_records = sum(r.records_fetched for r in period_results)
            total_stored = sum(r.records_stored for r in period_results)
            print(f"   Period {i+1}: {total_records} records generated, {total_stored} stored")
    
    # Show overall summary
    summary = scanner.get_scan_summary()
    print(f"\n📈 Overall: {summary['total_records_fetched']} records, {summary['success_rate']:.1f}% success rate")


def demo_coverage_analysis():
    """Demonstrate coverage analysis"""
    
    print("\n" + "="*50)
    print("📊 COVERAGE ANALYSIS DEMO")
    print("="*50)
    
    scanner = MockBacktestDataScanner()
    
    # Generate some data first
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    config = ScanConfig(
        symbols=symbols,
        start_date="2024-01-01",
        end_date="2024-12-31",
        interval="1d"
    )
    
    print("Generating sample data...")
    asyncio.run(scanner.scan_symbols(config))
    
    # Analyze coverage for different periods
    periods = [
        ("Q1 2024", "2024-01-01", "2024-03-31"),
        ("Q2 2024", "2024-04-01", "2024-06-30"),
        ("Q3 2024", "2024-07-01", "2024-09-30"),
        ("Q4 2024", "2024-10-01", "2024-12-31"),
    ]
    
    print("\nCoverage Analysis by Quarter:")
    print(f"{'Quarter':<12} {'Symbol':<8} {'Stored':<8} {'Expected':<10} {'Coverage':<10}")
    print("-" * 50)
    
    for quarter, start_date, end_date in periods:
        coverage = scanner.get_database_coverage(symbols, start_date, end_date)
        
        for symbol, data in coverage.items():
            print(f"{quarter:<12} {symbol:<8} {data['stored_records']:<8} {data['expected_records']:<10} {data['coverage_rate']:<10.1f}%")


if __name__ == "__main__":
    try:
        # Main mock demo
        demo_mock_backtest_scanner()
        
        # Multi-period mock demo
        demo_multi_period_mock()
        
        # Coverage analysis demo
        demo_coverage_analysis()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 