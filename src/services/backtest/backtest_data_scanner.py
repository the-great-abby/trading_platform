"""
Backtest Data Scanner - Fetch and store historical OHLCV data
"""

import os
import logging
import pandas as pd
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..market_data.cached_market_data_manager import get_cached_market_data_manager
from ..database.market_data_service import MarketDataDatabaseService

logger = logging.getLogger(__name__)


@dataclass
class ScanConfig:
    """Configuration for backtest data scanning"""
    symbols: List[str]
    start_date: str
    end_date: str
    interval: str = "1d"
    providers: Optional[List[str]] = None  # If None, use all available providers
    force_refresh: bool = False
    parallel_workers: int = 1  # Reduced to 1 to avoid rate limiting
    batch_size: int = 1  # Process one symbol at a time
    delay_between_requests: float = 20.0  # Increased delay between API requests in seconds
    delay_between_symbols: float = 60.0  # Additional delay between symbols (1 minute)
    max_retries: int = 2  # Reduced retries to avoid overwhelming APIs
    rate_limit_backoff_multiplier: float = 3.0  # Increased multiplier for exponential backoff
    
    def __post_init__(self):
        if self.providers is None:
            self.providers = ["polygon", "yahoo", "alpha_vantage"]


@dataclass
class ScanResult:
    """Result of a backtest data scan"""
    symbol: str
    start_date: str
    end_date: str
    records_fetched: int
    records_stored: int
    cache_hits: int
    api_calls: int
    providers_used: List[str]
    success: bool
    error_message: Optional[str] = None


class BacktestDataScanner:
    """Scanner for fetching and storing backtest data"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.cached_manager = get_cached_market_data_manager(database_url)
        self.db_service = MarketDataDatabaseService(database_url)
        self.scan_results: List[ScanResult] = []
        
        logger.info("Backtest data scanner initialized")
    
    async def scan_symbols(self, config: ScanConfig) -> List[ScanResult]:
        """
        Scan multiple symbols for historical data (one at a time with delays)
        
        Args:
            config: Scan configuration
            
        Returns:
            List of scan results
        """
        logger.info(f"Starting backtest data scan for {len(config.symbols)} symbols")
        logger.info(f"Date range: {config.start_date} to {config.end_date}")
        logger.info(f"Interval: {config.interval}")
        logger.info(f"Processing one symbol at a time with {config.delay_between_requests}s delays")
        logger.info(f"Additional {config.delay_between_symbols}s delay between symbols")
        
        self.scan_results = []
        
        # Track rate limit hits for adaptive delays
        rate_limit_hits = 0
        consecutive_failures = 0
        
        # Process symbols sequentially to avoid rate limiting
        for i, symbol in enumerate(config.symbols):
            try:
                logger.info(f"Processing symbol {i+1}/{len(config.symbols)}: {symbol}")
                
                # Add delay between requests (except for the first one)
                if i > 0:
                    # Calculate adaptive delay based on rate limit hits
                    adaptive_delay = config.delay_between_symbols + (rate_limit_hits * 30)
                    logger.info(f"Waiting {adaptive_delay} seconds before next request...")
                    time.sleep(adaptive_delay)
                
                # Scan single symbol with retry logic
                result = self._scan_single_symbol_with_retry(symbol, config)
                self.scan_results.append(result)
                
                if result.success:
                    logger.info(f"✅ Successfully processed {symbol}: {result.records_fetched} records")
                    consecutive_failures = 0  # Reset failure counter
                else:
                    logger.warning(f"❌ Failed to process {symbol}: {result.error_message}")
                    consecutive_failures += 1
                    
                    # Check if this was a rate limit error
                    if result.error_message and ("rate limit" in result.error_message.lower() or 
                                               "429" in result.error_message or 
                                               "too many" in result.error_message.lower()):
                        rate_limit_hits += 1
                        logger.warning(f"Rate limit hit #{rate_limit_hits} - increasing delays")
                        
                        # If we've hit multiple rate limits, add extra delay
                        if rate_limit_hits >= 3:
                            extra_delay = 120  # 2 minutes
                            logger.warning(f"Multiple rate limits detected. Adding {extra_delay}s extra delay...")
                            time.sleep(extra_delay)
                    
                    # If we have too many consecutive failures, pause longer
                    if consecutive_failures >= 5:
                        pause_delay = 300  # 5 minutes
                        logger.warning(f"Too many consecutive failures. Pausing for {pause_delay}s...")
                        time.sleep(pause_delay)
                        consecutive_failures = 0  # Reset counter
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                consecutive_failures += 1
                self.scan_results.append(ScanResult(
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
                ))
        
        # Log summary
        self._log_scan_summary()
        
        return self.scan_results
    
    def _scan_single_symbol_with_retry(self, symbol: str, config: ScanConfig) -> ScanResult:
        """
        Scan a single symbol with retry logic and sophisticated rate limiting
        
        Args:
            symbol: Stock symbol
            config: Scan configuration
            
        Returns:
            Scan result
        """
        for attempt in range(config.max_retries):
            try:
                result = self._scan_single_symbol(symbol, config)
                
                if result.success:
                    return result
                elif result.error_message and ("rate limit" in result.error_message.lower() or 
                                             "429" in result.error_message or 
                                             "too many" in result.error_message.lower()):
                    # Rate limit error - wait longer and retry
                    wait_time = (attempt + 1) * 60 * config.rate_limit_backoff_multiplier  # 60s, 120s, 180s
                    logger.warning(f"Rate limit hit for {symbol}, waiting {wait_time}s before retry {attempt + 1}/{config.max_retries}")
                    time.sleep(wait_time)
                    continue
                elif result.error_message and "403" in result.error_message:
                    # Forbidden error (likely API key issue) - don't retry
                    logger.error(f"403 Forbidden error for {symbol} - likely API key issue, skipping retries")
                    return result
                else:
                    # Other error - don't retry
                    return result
                    
            except Exception as e:
                if attempt < config.max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    logger.error(f"Error scanning {symbol} (attempt {attempt + 1}): {e}")
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Final attempt failed for {symbol}: {e}")
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
                        error_message=f"All {config.max_retries} attempts failed: {str(e)}"
                    )
        
        # If we get here, all retries failed
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
            error_message=f"All {config.max_retries} retry attempts failed"
        )
    
    def _scan_single_symbol(self, symbol: str, config: ScanConfig) -> ScanResult:
        """
        Scan a single symbol for historical data
        
        Args:
            symbol: Stock symbol
            config: Scan configuration
            
        Returns:
            Scan result
        """
        try:
            logger.info(f"Scanning {symbol} from {config.start_date} to {config.end_date}")
            
            # Get initial cache stats
            initial_stats = self.cached_manager.get_stats()
            
            # Fetch data (this will use cache and store new data)
            data = self.cached_manager.get_historical_data(
                symbol=symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                interval=config.interval,
                force_refresh=config.force_refresh
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
                    error_message="No data retrieved"
                )
            
            # Get final cache stats
            final_stats = self.cached_manager.get_stats()
            
            # Calculate metrics
            records_fetched = len(data)
            cache_hits = final_stats['cache_hits'] - initial_stats['cache_hits']
            api_calls = final_stats['api_calls'] - initial_stats['api_calls']
            
            # Get cache status to see which providers were used
            cache_status = self.cached_manager.get_cache_status(symbol)
            providers_used = list(cache_status.get('providers', {}).keys()) if cache_status else []
            
            # Store data in database (if not already stored)
            records_stored = 0
            if records_fetched > 0:
                # Check if data needs to be stored
                stored_data = self.db_service.get_historical_data(
                    symbol=symbol,
                    start_date=datetime.strptime(config.start_date, "%Y-%m-%d").date(),
                    end_date=datetime.strptime(config.end_date, "%Y-%m-%d").date(),
                    interval=config.interval
                )
                
                if stored_data is None or len(stored_data) < records_fetched:
                    # Store the data
                    success = self.db_service.store_historical_data(
                        symbol=symbol,
                        data=data,
                        provider="backtest_scanner",
                        interval=config.interval
                    )
                    if success:
                        records_stored = records_fetched
                    else:
                        logger.warning(f"Failed to store data for {symbol}")
            
            return ScanResult(
                symbol=symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                records_fetched=records_fetched,
                records_stored=records_stored,
                cache_hits=cache_hits,
                api_calls=api_calls,
                providers_used=providers_used,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
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
    
    def scan_backtest_periods(self, symbols: List[str], periods: List[Dict]) -> List[ScanResult]:
        """
        Scan multiple backtest periods for the same symbols
        
        Args:
            symbols: List of symbols to scan
            periods: List of period configurations
                     [{"start_date": "2024-01-01", "end_date": "2024-06-30", "interval": "1d"}]
            
        Returns:
            List of scan results
        """
        all_results = []
        
        for period in periods:
            config = ScanConfig(
                symbols=symbols,
                start_date=period["start_date"],
                end_date=period["end_date"],
                interval=period.get("interval", "1d")
            )
            
            logger.info(f"Scanning period: {period['start_date']} to {period['end_date']}")
            results = asyncio.run(self.scan_symbols(config))
            all_results.extend(results)
        
        return all_results
    
    def get_scan_summary(self) -> Dict:
        """Get summary of all scan results"""
        if not self.scan_results:
            return {"message": "No scan results available"}
        
        total_symbols = len(self.scan_results)
        successful_scans = sum(1 for r in self.scan_results if r.success)
        failed_scans = total_symbols - successful_scans
        
        total_records_fetched = sum(r.records_fetched for r in self.scan_results)
        total_records_stored = sum(r.records_stored for r in self.scan_results)
        total_cache_hits = sum(r.cache_hits for r in self.scan_results)
        total_api_calls = sum(r.api_calls for r in self.scan_results)
        
        # Calculate cache hit rate
        total_requests = total_cache_hits + total_api_calls
        cache_hit_rate = (total_cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # API call reduction
        api_reduction = (total_cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_symbols": total_symbols,
            "successful_scans": successful_scans,
            "failed_scans": failed_scans,
            "success_rate": (successful_scans / total_symbols * 100) if total_symbols > 0 else 0,
            "total_records_fetched": total_records_fetched,
            "total_records_stored": total_records_stored,
            "total_cache_hits": total_cache_hits,
            "total_api_calls": total_api_calls,
            "cache_hit_rate": cache_hit_rate,
            "api_call_reduction": api_reduction,
            "providers_used": list(set(
                provider 
                for result in self.scan_results 
                for provider in result.providers_used
            ))
        }
    
    def _log_scan_summary(self):
        """Log summary of scan results"""
        summary = self.get_scan_summary()
        
        logger.info("=" * 60)
        logger.info("BACKTEST DATA SCAN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Symbols: {summary['total_symbols']}")
        logger.info(f"Successful Scans: {summary['successful_scans']}")
        logger.info(f"Failed Scans: {summary['failed_scans']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Total Records Fetched: {summary['total_records_fetched']:,}")
        logger.info(f"Total Records Stored: {summary['total_records_stored']:,}")
        logger.info(f"Cache Hits: {summary['total_cache_hits']}")
        logger.info(f"API Calls: {summary['total_api_calls']}")
        logger.info(f"Cache Hit Rate: {summary['cache_hit_rate']:.1f}%")
        logger.info(f"API Call Reduction: {summary['api_call_reduction']:.1f}%")
        logger.info(f"Providers Used: {', '.join(summary['providers_used'])}")
        logger.info("=" * 60)
    
    def get_database_coverage(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """
        Check database coverage for symbols and date range
        
        Args:
            symbols: List of symbols to check
            start_date: Start date
            end_date: End date
            
        Returns:
            Coverage information
        """
        coverage = {}
        
        for symbol in symbols:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Get stored data
            stored_data = self.db_service.get_historical_data(
                symbol=symbol,
                start_date=start_dt,
                end_date=end_dt
            )
            
            if stored_data is not None:
                stored_count = len(stored_data)
                # Calculate expected count (business days)
                expected_count = self._count_business_days(start_dt, end_dt)
                coverage_rate = (stored_count / expected_count * 100) if expected_count > 0 else 0
                
                coverage[symbol] = {
                    "stored_records": stored_count,
                    "expected_records": expected_count,
                    "coverage_rate": coverage_rate,
                    "missing_records": expected_count - stored_count
                }
            else:
                coverage[symbol] = {
                    "stored_records": 0,
                    "expected_records": 0,
                    "coverage_rate": 0,
                    "missing_records": 0
                }
        
        return coverage
    
    def _count_business_days(self, start_date: date, end_date: date) -> int:
        """Count business days between two dates"""
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Clean up old data from database"""
        return self.db_service.cleanup_old_data(days_to_keep)


# Convenience functions
def scan_backtest_data(symbols: List[str], start_date: str, end_date: str, 
                      interval: str = "1d", force_refresh: bool = False) -> List[ScanResult]:
    """Convenience function to scan backtest data"""
    scanner = BacktestDataScanner()
    config = ScanConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        force_refresh=force_refresh
    )
    return asyncio.run(scanner.scan_symbols(config))


def get_backtest_coverage(symbols: List[str], start_date: str, end_date: str) -> Dict:
    """Convenience function to get database coverage"""
    scanner = BacktestDataScanner()
    return scanner.get_database_coverage(symbols, start_date, end_date) 