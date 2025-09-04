#!/usr/bin/env python3
"""
Build Backtest Data - Comprehensive data population for full backtesting
"""

import os
import sys
import time
import asyncio
import argparse
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional

# Add src to path
sys.path.append('src')

from src.services.backtest.backtest_data_scanner import (
    BacktestDataScanner, 
    ScanConfig, 
    get_backtest_coverage
)

def get_comprehensive_symbols() -> List[str]:
    """Get comprehensive list of symbols for backtesting"""
    return [
        # Major Tech Stocks
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
        
        # Financial Sector
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
        
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
        
        # Energy
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'HAL', 'BKR',
        
        # Consumer Discretionary
        'HD', 'MCD', 'NKE', 'SBUX', 'DIS', 'CMCSA', 'TGT', 'COST', 'LOW', 'TJX',
        
        # Consumer Staples
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO', 'CL', 'GIS', 'KMB',
        
        # Industrials
        'BA', 'CAT', 'MMM', 'GE', 'HON', 'UPS', 'FDX', 'RTX', 'LMT', 'NOC',
        
        # Materials
        'LIN', 'APD', 'FCX', 'NEM', 'DOW', 'DD', 'NUE', 'BLL', 'VMC', 'MLM',
        
        # Utilities
        'NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'XEL', 'WEC', 'DTE', 'ED',
        
        # Real Estate
        'AMT', 'PLD', 'CCI', 'EQIX', 'DLR', 'PSA', 'SPG', 'O', 'WELL', 'VICI',
        
        # Major ETFs
        'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'TLT', 'GLD',
        
        # Sector ETFs
        'XLK', 'XLF', 'XLV', 'XLE', 'XLY', 'XLP', 'XLI', 'XLB', 'XLU', 'XLRE',
        
        # International ETFs
        'EFA', 'EEM', 'FXI', 'EWJ', 'EWG', 'EWU', 'EWC', 'EWA', 'EWZ', 'EWY'
    ]

def get_backtest_periods() -> List[Dict]:
    """Get comprehensive backtest periods"""
    return [
        # Recent periods for strategy validation
        {"start_date": "2024-01-01", "end_date": "2024-12-31", "interval": "1d", "name": "2024"},
        {"start_date": "2023-01-01", "end_date": "2023-12-31", "interval": "1d", "name": "2023"},
        {"start_date": "2022-01-01", "end_date": "2022-12-31", "interval": "1d", "name": "2022"},
        
        # Longer periods for comprehensive backtesting
        {"start_date": "2018-01-01", "end_date": "2024-12-31", "interval": "1d", "name": "7-Year"},
        {"start_date": "2015-01-01", "end_date": "2024-12-31", "interval": "1d", "name": "10-Year"},
        
        # Crisis periods for stress testing
        {"start_date": "2008-01-01", "end_date": "2009-12-31", "interval": "1d", "name": "2008-Crisis"},
        {"start_date": "2020-03-01", "end_date": "2020-12-31", "interval": "1d", "name": "COVID-Crisis"},
        
        # Intraday periods for high-frequency strategies
        {"start_date": "2024-01-01", "end_date": "2024-01-31", "interval": "1h", "name": "2024-Jan-1h"},
        {"start_date": "2024-02-01", "end_date": "2024-02-29", "interval": "1h", "name": "2024-Feb-1h"},
        {"start_date": "2024-03-01", "end_date": "2024-03-31", "interval": "1h", "name": "2024-Mar-1h"},
        
        # 5-minute data for day trading
        {"start_date": "2024-01-01", "end_date": "2024-01-07", "interval": "5m", "name": "2024-Jan-5m"},
        {"start_date": "2024-02-01", "end_date": "2024-02-07", "interval": "5m", "name": "2024-Feb-5m"},
    ]

def build_backtest_data(symbols: List[str], periods: List[Dict], 
                       parallel_workers: int = 4, force_refresh: bool = False) -> Dict:
    """Build comprehensive backtest data"""
    
    print("🏗️  Building Comprehensive Backtest Data")
    print("=" * 60)
    print(f"📊 Symbols: {len(symbols)} symbols")
    print(f"📅 Periods: {len(periods)} time periods")
    print(f"⚙️  Parallel workers: {parallel_workers}")
    print(f"🔄 Force refresh: {force_refresh}")
    print("=" * 60)
    
    scanner = BacktestDataScanner()
    total_start_time = time.time()
    
    # Track progress
    total_symbols = len(symbols)
    total_periods = len(periods)
    completed_symbols = 0
    completed_periods = 0
    total_records = 0
    total_api_calls = 0
    
    # Process each period
    for period_idx, period in enumerate(periods, 1):
        print(f"\n📅 Period {period_idx}/{total_periods}: {period['name']}")
        print(f"   Date range: {period['start_date']} to {period['end_date']}")
        print(f"   Interval: {period['interval']}")
        
        period_start_time = time.time()
        
        # Configure scan for this period
        config = ScanConfig(
            symbols=symbols,
            start_date=period['start_date'],
            end_date=period['end_date'],
            interval=period['interval'],
            parallel_workers=parallel_workers,
            force_refresh=force_refresh
        )
        
        # Run scan for this period
        try:
            results = asyncio.run(scanner.scan_symbols(config))
            
            # Process results
            period_records = 0
            period_api_calls = 0
            successful_scans = 0
            
            for result in results:
                if result.success:
                    successful_scans += 1
                    period_records += result.records_fetched
                    period_api_calls += result.api_calls
                    completed_symbols += 1
                else:
                    print(f"   ❌ {result.symbol}: {result.error_message}")
            
            period_time = time.time() - period_start_time
            completed_periods += 1
            total_records += period_records
            total_api_calls += period_api_calls
            
            print(f"   ✅ Completed: {successful_scans}/{len(symbols)} symbols")
            print(f"   📊 Records: {period_records:,}")
            print(f"   🌐 API calls: {period_api_calls}")
            print(f"   ⏱️  Time: {period_time:.2f} seconds")
            
        except Exception as e:
            print(f"   ❌ Period failed: {e}")
            continue
    
    total_time = time.time() - total_start_time
    
    # Generate summary
    summary = {
        'total_symbols': total_symbols,
        'total_periods': total_periods,
        'completed_symbols': completed_symbols,
        'completed_periods': completed_periods,
        'total_records': total_records,
        'total_api_calls': total_api_calls,
        'total_time': total_time,
        'success_rate': (completed_periods / total_periods * 100) if total_periods > 0 else 0
    }
    
    return summary

def check_data_coverage(symbols: List[str], periods: List[Dict]) -> Dict:
    """Check coverage of built data"""
    
    print("\n📊 Checking Data Coverage")
    print("=" * 60)
    
    scanner = BacktestDataScanner()
    coverage_summary = {}
    
    for period in periods:
        print(f"\n📅 Period: {period['name']} ({period['start_date']} to {period['end_date']})")
        
        period_coverage = scanner.get_database_coverage(
            symbols[:10],  # Check first 10 symbols for efficiency
            period['start_date'],
            period['end_date']
        )
        
        total_stored = sum(data['stored_records'] for data in period_coverage.values())
        total_expected = sum(data['expected_records'] for data in period_coverage.values())
        avg_coverage = (total_stored / total_expected * 100) if total_expected > 0 else 0
        
        coverage_summary[period['name']] = {
            'stored_records': total_stored,
            'expected_records': total_expected,
            'coverage_rate': avg_coverage
        }
        
        print(f"   📊 Coverage: {avg_coverage:.1f}% ({total_stored:,}/{total_expected:,} records)")
    
    return coverage_summary

def estimate_storage_requirements(symbols: List[str], periods: List[Dict]) -> Dict:
    """Estimate storage requirements for the data"""
    
    print("\n💾 Storage Requirements Estimation")
    print("=" * 60)
    
    # Estimate records per symbol per period
    total_records = 0
    for period in periods:
        start_date = datetime.strptime(period['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(period['end_date'], "%Y-%m-%d").date()
        
        # Calculate business days
        business_days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
            current_date += timedelta(days=1)
        
        # Adjust for interval
        if period['interval'] == '1h':
            records_per_symbol = business_days * 6.5  # 6.5 hours per day
        elif period['interval'] == '5m':
            records_per_symbol = business_days * 6.5 * 12  # 12 5-minute intervals per hour
        else:  # 1d
            records_per_symbol = business_days
        
        period_records = records_per_symbol * len(symbols)
        total_records += period_records
        
        print(f"   📅 {period['name']}: {records_per_symbol:.0f} records/symbol = {period_records:,.0f} total")
    
    # Estimate storage size (rough calculation)
    avg_record_size = 100  # bytes per record (OHLCV + metadata)
    total_storage_bytes = total_records * avg_record_size
    total_storage_mb = total_storage_bytes / (1024 * 1024)
    total_storage_gb = total_storage_mb / 1024
    
    print(f"\n📊 Total Records: {total_records:,.0f}")
    print(f"💾 Estimated Storage: {total_storage_mb:.1f} MB ({total_storage_gb:.2f} GB)")
    
    return {
        'total_records': total_records,
        'storage_mb': total_storage_mb,
        'storage_gb': total_storage_gb
    }

def main():
    parser = argparse.ArgumentParser(description='Build Comprehensive Backtest Data')
    parser.add_argument('--symbols', nargs='+', default=get_comprehensive_symbols(),
                       help='Symbols to scan (default: comprehensive list)')
    parser.add_argument('--periods', choices=['recent', 'comprehensive', 'crisis', 'intraday', 'all'],
                       default='comprehensive', help='Time periods to scan')
    parser.add_argument('--parallel-workers', type=int, default=4,
                       help='Number of parallel workers')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh even if data exists')
    parser.add_argument('--check-coverage', action='store_true',
                       help='Check data coverage after building')
    parser.add_argument('--estimate-storage', action='store_true',
                       help='Estimate storage requirements')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be built without executing')
    parser.add_argument('--start-date', type=str, default=None,
                       help='Custom start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='Custom end date (YYYY-MM-DD)')
    parser.add_argument('--interval', type=str, default='1d',
                       help='Custom interval (default: 1d)')
    
    args = parser.parse_args()
    
    # If both start-date and end-date are provided, use them as a single period
    if args.start_date and args.end_date:
        periods = [{
            'name': f"{args.start_date}_to_{args.end_date}",
            'start_date': args.start_date,
            'end_date': args.end_date,
            'interval': args.interval
        }]
    else:
        # Select periods based on argument
        all_periods = get_backtest_periods()
        if args.periods == 'recent':
            periods = [p for p in all_periods if p['name'] in ['2024', '2023', '2022']]
        elif args.periods == 'comprehensive':
            periods = [p for p in all_periods if p['interval'] == '1d' and 'Crisis' not in p['name']]
        elif args.periods == 'crisis':
            periods = [p for p in all_periods if 'Crisis' in p['name']]
        elif args.periods == 'intraday':
            periods = [p for p in all_periods if p['interval'] in ['1h', '5m']]
        else:  # all
            periods = all_periods
    
    print("🏗️  Backtest Data Builder")
    print("=" * 60)
    print(f"📊 Symbols: {len(args.symbols)} symbols")
    print(f"📅 Periods: {len(periods)} periods")
    print(f"⚙️  Parallel workers: {args.parallel_workers}")
    print(f"🔄 Force refresh: {args.force_refresh}")
    print("=" * 60)
    
    if args.estimate_storage:
        estimate_storage_requirements(args.symbols, periods)
        return
    
    if args.dry_run:
        print("\n🔍 DRY RUN - What would be built:")
        for period in periods:
            print(f"   📅 {period['name']}: {period['start_date']} to {period['end_date']} ({period['interval']})")
        print(f"\n📊 Total: {len(args.symbols)} symbols × {len(periods)} periods = {len(args.symbols) * len(periods)} scans")
        return
    
    # Build the data
    summary = build_backtest_data(
        symbols=args.symbols,
        periods=periods,
        parallel_workers=args.parallel_workers,
        force_refresh=args.force_refresh
    )
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎉 BACKTEST DATA BUILD COMPLETED")
    print("=" * 60)
    print(f"📊 Total symbols processed: {summary['completed_symbols']:,}")
    print(f"📅 Total periods completed: {summary['completed_periods']}/{summary['total_periods']}")
    print(f"📈 Total records stored: {summary['total_records']:,}")
    print(f"🌐 Total API calls: {summary['total_api_calls']}")
    print(f"⏱️  Total time: {summary['total_time']:.2f} seconds ({summary['total_time']/60:.1f} minutes)")
    print(f"✅ Success rate: {summary['success_rate']:.1f}%")
    
    # Check coverage if requested
    if args.check_coverage:
        coverage = check_data_coverage(args.symbols, periods)
        
        print(f"\n📊 Coverage Summary:")
        for period_name, data in coverage.items():
            print(f"   {period_name}: {data['coverage_rate']:.1f}% coverage")
    
    print("\n🚀 Ready for comprehensive backtesting!")
    print("💡 Next steps:")
    print("   • Run backtests with: make run-backtest")
    print("   • Check performance with: make backtest-coverage")
    print("   • Monitor with: make k8s-scanner-logs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Build interrupted by user")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc() 