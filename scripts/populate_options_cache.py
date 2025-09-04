#!/usr/bin/env python3
"""
Populate Options Cache - Historical options data population script
Fetches and caches historical options data for all symbols
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Add src to path
sys.path.append('src')

from src.services.market_data.options_data_cache import get_options_cache
from src.utils.trading_config import get_options_symbols
from src.utils.enhanced_logging import get_trading_logger

class OptionsCachePopulator:
    """Populate options cache with historical data"""
    
    def __init__(self):
        self.logger = get_trading_logger()
        self.options_cache = get_options_cache()
        
        # Configuration
        self.symbols = get_options_symbols()
        self.start_date = datetime(2023, 7, 15)
        self.end_date = datetime(2025, 7, 14)
        
        # Progress tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    async def populate_cache(self):
        """Populate options cache with historical data"""
        self.logger.info("🚀 Starting Options Cache Population")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Configuration:")
        self.logger.info(f"   Symbols: {len(self.symbols)} options symbols")
        self.logger.info(f"   Date Range: {self.start_date.date()} to {self.end_date.date()}")
        self.logger.info(f"   Duration: {(self.end_date - self.start_date).days} days")
        
        # Calculate total work
        total_days = (self.end_date - self.start_date).days
        total_work = len(self.symbols) * total_days
        self.logger.info(f"   Total Work: {total_work} symbol-days")
        
        # Process each symbol
        for i, symbol in enumerate(self.symbols, 1):
            self.logger.info(f"\n📈 Processing Symbol {i}/{len(self.symbols)}: {symbol}")
            
            try:
                await self._populate_symbol_cache(symbol)
                self.successful_requests += 1
                
            except Exception as e:
                self.logger.error(f"❌ Error processing {symbol}: {str(e)}")
                self.failed_requests += 1
        
        # Final summary
        self._print_summary()
    
    async def _populate_symbol_cache(self, symbol: str):
        """Populate cache for a single symbol"""
        current_date = self.start_date
        
        while current_date <= self.end_date:
            try:
                # Get options chain for this date
                options_chain = await self.options_cache.get_options_chain(symbol, current_date)
                
                if options_chain and options_chain.get('contracts'):
                    # Get ATM options for this date
                    atm_options = await self.options_cache.get_atm_options(symbol, current_date)
                    
                    # Cache historical data for ATM options
                    for option in atm_options:
                        # Get 1 year of historical data for each option
                        hist_start = current_date - timedelta(days=365)
                        hist_end = current_date
                        
                        historical_data = await self.options_cache.get_contract_history(
                            option.contract_id, hist_start, hist_end
                        )
                        
                        if historical_data is not None:
                            self.logger.info(f"   ✅ Cached {len(historical_data)} days for {option.contract_id}")
                
                self.total_requests += 1
                
                # Progress update every 30 days
                if current_date.day % 30 == 0:
                    progress = ((current_date - self.start_date).days / 
                              (self.end_date - self.start_date).days) * 100
                    self.logger.info(f"   📊 Progress: {progress:.1f}%")
                
                current_date += timedelta(days=1)
                
            except Exception as e:
                self.logger.error(f"   ❌ Error processing {symbol} on {current_date.date()}: {str(e)}")
                current_date += timedelta(days=1)
                continue
    
    def _print_summary(self):
        """Print final summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 Options Cache Population Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"   Total Requests: {self.total_requests}")
        self.logger.info(f"   Successful: {self.successful_requests}")
        self.logger.info(f"   Failed: {self.failed_requests}")
        self.logger.info(f"   Success Rate: {(self.successful_requests/self.total_requests)*100:.1f}%")
        
        # Cache statistics
        cache_stats = self.options_cache.get_cache_stats()
        self.logger.info(f"\n📈 Cache Performance:")
        self.logger.info(f"   Cache Hits: {cache_stats['cache_hits']}")
        self.logger.info(f"   Cache Misses: {cache_stats['cache_misses']}")
        self.logger.info(f"   API Calls: {cache_stats['api_calls']}")
        self.logger.info(f"   Hit Rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")
        
        # Cache size
        cache_size = self.options_cache.get_cache_size()
        self.logger.info(f"\n💾 Cache Size:")
        self.logger.info(f"   Options Chains: {cache_size['options_chains']}")
        self.logger.info(f"   Historical Records: {cache_size['historical_records']}")
        self.logger.info(f"   Total Records: {cache_size['total_records']}")
        
        self.logger.info("\n✅ Options cache population completed!")

async def main():
    """Main entry point"""
    populator = OptionsCachePopulator()
    await populator.populate_cache()

if __name__ == "__main__":
    asyncio.run(main()) 