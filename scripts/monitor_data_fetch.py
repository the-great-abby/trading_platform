#!/usr/bin/env python3
"""
Simple monitoring script for data fetch progress
Shows real-time statistics and progress for 2-year data fetch operations
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
import sys

class DataFetchMonitor:
    def __init__(self):
        self.base_url = "http://localhost:11005"
        self.unified_url = "http://localhost:11115"
        
    async def get_data_coverage(self):
        """Get current data coverage statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/data/coverage") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error getting coverage: {e}")
        return None
    
    async def get_symbols(self):
        """Get list of symbols"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/symbols") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error getting symbols: {e}")
        return None
    
    async def trigger_data_fetch(self):
        """Trigger a 2-year data fetch"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {"action": "fetch_2year"}
                async with session.post(f"{self.unified_url}/api/data/fetch-2year", 
                                     json=data) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error triggering fetch: {e}")
        return None
    
    def print_header(self):
        """Print monitoring header"""
        print("=" * 80)
        print("📊 DATA FETCH MONITORING DASHBOARD")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def print_coverage_stats(self, coverage_data):
        """Print coverage statistics"""
        if not coverage_data:
            print("❌ Could not fetch coverage data")
            return
        
        print(f"\n📈 DATA COVERAGE STATISTICS")
        print(f"   Total Symbols: {coverage_data.get('total_symbols', 0)}")
        print(f"   Symbols with Data: {coverage_data.get('symbols_with_data', 0)}")
        print(f"   Average Coverage: {coverage_data.get('avg_coverage', 0):.1f}%")
        
        if coverage_data.get('coverage_details'):
            print(f"\n📋 COVERAGE DETAILS:")
            for detail in coverage_data['coverage_details'][:5]:  # Show first 5
                symbol = detail.get('symbol', 'Unknown')
                coverage = detail.get('coverage', 0)
                print(f"   {symbol}: {coverage:.1f}%")
            if len(coverage_data['coverage_details']) > 5:
                print(f"   ... and {len(coverage_data['coverage_details']) - 5} more")
    
    def print_symbols(self, symbols_data):
        """Print symbols information"""
        if not symbols_data:
            print("❌ Could not fetch symbols data")
            return
        
        symbols = symbols_data.get('symbols', [])
        print(f"\n📊 SYMBOLS MONITORED ({len(symbols)} total)")
        
        # Group symbols by type
        stocks = [s for s in symbols if len(s) <= 4 and s.isalpha()]
        etfs = [s for s in symbols if len(s) > 4 or not s.isalpha()]
        
        print(f"   Stocks: {len(stocks)}")
        print(f"   ETFs: {len(etfs)}")
        
        # Show some examples
        if stocks:
            print(f"   Stock Examples: {', '.join(stocks[:5])}")
        if etfs:
            print(f"   ETF Examples: {', '.join(etfs[:5])}")
    
    async def monitor_progress(self, duration_minutes=5):
        """Monitor data fetch progress for specified duration"""
        print(f"\n🔄 MONITORING PROGRESS (for {duration_minutes} minutes)")
        print("Press Ctrl+C to stop monitoring")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        try:
            while time.time() < end_time:
                # Get current stats
                coverage = await self.get_data_coverage()
                symbols = await self.get_symbols()
                
                # Clear screen (simple approach)
                print("\033[2J\033[H")  # Clear screen
                self.print_header()
                self.print_coverage_stats(coverage)
                self.print_symbols(symbols)
                
                # Show monitoring info
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                print(f"\n⏱️  MONITORING STATUS")
                print(f"   Elapsed: {elapsed/60:.1f} minutes")
                print(f"   Remaining: {remaining/60:.1f} minutes")
                print(f"   Last Update: {datetime.now().strftime('%H:%M:%S')}")
                
                print(f"\n💡 MONITORING TIPS:")
                print(f"   • Check Grafana: http://localhost:11102/")
                print(f"   • Check Prometheus: http://localhost:11101/")
                print(f"   • Worker Logs: kubectl logs -f market-data-worker-7d7965ddcf-7wqhl -n trading-system")
                print(f"   • Data Fetch: http://localhost:11115/central-hub")
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoring stopped by user")
    
    async def run(self):
        """Main monitoring function"""
        self.print_header()
        
        # Get initial stats
        print("\n📊 INITIAL STATUS")
        coverage = await self.get_data_coverage()
        symbols = await self.get_symbols()
        
        self.print_coverage_stats(coverage)
        self.print_symbols(symbols)
        
        # Ask user what they want to do
        print(f"\n🎯 MONITORING OPTIONS:")
        print(f"   1. Monitor progress for 5 minutes")
        print(f"   2. Trigger 2-year data fetch")
        print(f"   3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                await self.monitor_progress(5)
            elif choice == "2":
                print(f"\n🚀 Triggering 2-year data fetch...")
                result = await self.trigger_data_fetch()
                if result:
                    print(f"✅ Fetch triggered successfully!")
                    print(f"   Symbols processed: {result.get('symbols_processed', 0)}")
                    print(f"   Records added: {result.get('records_added', 0)}")
                    print(f"   Time taken: {result.get('time_taken', 'Unknown')}")
                else:
                    print(f"❌ Failed to trigger fetch")
            elif choice == "3":
                print(f"👋 Goodbye!")
            else:
                print(f"❌ Invalid choice")
                
        except KeyboardInterrupt:
            print(f"\n👋 Goodbye!")

async def main():
    monitor = DataFetchMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main()) 