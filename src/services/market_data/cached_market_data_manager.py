"""
Cached Market Data Manager - Database-first approach with API fallback
"""

import logging
import os
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..database.market_data_service import MarketDataDatabaseService
from .market_data_provider import get_market_data_manager

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    cache_hit_rate: float = 0.0
    
    def update_hit(self):
        """Update stats for cache hit"""
        self.total_requests += 1
        self.cache_hits += 1
        self.cache_hit_rate = (self.cache_hits / self.total_requests) * 100
    
    def update_miss(self, api_calls: int = 0):
        """Update stats for cache miss"""
        self.total_requests += 1
        self.cache_misses += 1
        self.api_calls += api_calls
        self.cache_hit_rate = (self.cache_hits / self.total_requests) * 100


class CachedMarketDataManager:
    """Smart market data manager with database caching"""
    
    def __init__(self, database_url: Optional[str] = None, database_only: Optional[bool] = None):
        self.db_service = MarketDataDatabaseService(database_url)
        self.api_manager = get_market_data_manager()
        self.stats = CacheStats()
        self._cache_enabled = True
        
        # Check environment variable if database_only not explicitly set
        if database_only is None:
            database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
        
        self.database_only = bool(database_only)
        
        logger.info(f"Cached market data manager initialized (database_only={self.database_only})")
        if self.database_only:
            logger.info("Database-only mode enabled - will not fetch from external APIs")
    
    def enable_cache(self, enabled: bool = True):
        """Enable or disable caching"""
        self._cache_enabled = enabled
        logger.info(f"Cache {'enabled' if enabled else 'disabled'}")
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                          interval: str = "1d", force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Get historical data with smart caching
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
            force_refresh: Force API refresh even if data exists in cache
            
        Returns:
            DataFrame with historical data or None if failed
        """
        try:
            # Convert string dates to date objects
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            logger.info(f"Requesting historical data for {symbol} from {start_date} to {end_date}")
            
            if self.database_only:
                # Only use database, never fetch from API
                cached_data = self.db_service.get_historical_data(symbol, start_dt, end_dt, interval=interval)
                if cached_data is not None and len(cached_data) > 0:
                    logger.info(f"[DB-ONLY] Returning {len(cached_data)} records for {symbol}")
                    return cached_data
                else:
                    logger.warning(f"[DB-ONLY] No data found for {symbol}")
                    return None
            
            if not self._cache_enabled or force_refresh:
                # Skip cache, go directly to API
                logger.info("Cache disabled or force refresh requested, using API")
                return self._fetch_from_api(symbol, start_date, end_date, interval)
            
            # Step 1: Check database for existing data
            cached_data = self.db_service.get_historical_data(symbol, start_dt, end_dt, interval=interval)
            
            if cached_data is not None and len(cached_data) > 0:
                # Check if we have complete data coverage
                # Handle different index types robustly
                if isinstance(cached_data.index, pd.DatetimeIndex):
                    cached_dates = set(dt.date() for dt in cached_data.index)
                elif isinstance(cached_data.index, pd.Index):
                    # Handle case where index contains date objects directly
                    cached_dates = set()
                    for d in cached_data.index:
                        if isinstance(d, date):
                            cached_dates.add(d)
                        elif hasattr(d, 'date'):
                            cached_dates.add(d.date())
                        else:
                            # Try to convert to date
                            try:
                                if isinstance(d, str):
                                    cached_dates.add(datetime.strptime(d, "%Y-%m-%d").date())
                                else:
                                    cached_dates.add(d)
                            except:
                                logger.warning(f"Could not convert index value {d} to date for {symbol}")
                                continue
                else:
                    # Fallback: try to convert to date
                    cached_dates = set([d.date() if hasattr(d, 'date') else d for d in cached_data.index])
                
                requested_dates = self._generate_date_range(start_dt, end_dt)
                
                missing_dates = requested_dates - cached_dates
                
                if not missing_dates:
                    # Complete cache hit!
                    self.stats.update_hit()
                    logger.info(f"Complete cache hit for {symbol}: {len(cached_data)} records")
                    return cached_data
                else:
                    # Partial cache hit - fetch missing dates
                    logger.info(f"Partial cache hit for {symbol}: missing {len(missing_dates)} dates")
                    self.stats.update_miss()
                    
                    if self.database_only:
                        logger.warning(f"[DB-ONLY] Missing {len(missing_dates)} dates for {symbol}, not fetching from API")
                        return cached_data
                    # Fetch missing data from API
                    missing_data = self._fetch_missing_dates(symbol, missing_dates, interval)
                    
                    if missing_data is not None and len(missing_data) > 0:
                        # Combine cached and new data
                        combined_data = pd.concat([cached_data, missing_data])
                        combined_data = combined_data.sort_index()
                        
                        # Store new data in database
                        self.db_service.store_historical_data(symbol, missing_data, "api_fallback", interval)
                        
                        logger.info(f"Combined cached and API data for {symbol}: {len(combined_data)} records")
                        return combined_data
                    else:
                        # Fallback to cached data only
                        logger.warning(f"Failed to fetch missing data for {symbol}, using cached data only")
                        return cached_data
            
            # Step 2: No cached data, fetch from API
            logger.info(f"Cache miss for {symbol}, fetching from API")
            self.stats.update_miss(api_calls=1)
            
            if self.database_only:
                logger.warning(f"[DB-ONLY] No data for {symbol}, not fetching from API")
                return None
            api_data = self._fetch_from_api(symbol, start_date, end_date, interval)
            
            if api_data is not None and len(api_data) > 0:
                # Store in database for future use
                self.db_service.store_historical_data(symbol, api_data, "api_primary", interval)
                logger.info(f"Stored {len(api_data)} records for {symbol} in database")
            
            return api_data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, 
                           interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols with caching
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_historical_data(symbol, start_date, end_date, interval)
                if data is not None and len(data) > 0:
                    results[symbol] = data
                else:
                    logger.warning(f"No data available for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        logger.info(f"Retrieved data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def _fetch_from_api(self, symbol: str, start_date: str, end_date: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch data from API providers"""
        try:
            # Try each provider in order
            for i, provider in enumerate(self.api_manager.providers):
                try:
                    logger.info(f"Trying provider {i+1}/{len(self.api_manager.providers)} for {symbol}")
                    data = provider.get_historical_data(symbol, start_date, end_date, interval)
                    
                    if data is not None and not data.empty:
                        logger.info(f"Successfully got data from provider {i+1}")
                        return data
                    else:
                        logger.warning(f"Provider {i+1} returned no data for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Provider {i+1} failed for {symbol}: {str(e)}")
                    continue
            
            logger.error(f"All providers failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from API for {symbol}: {e}")
            return None
    
    def _fetch_missing_dates(self, symbol: str, missing_dates: set, interval: str) -> Optional[pd.DataFrame]:
        """Fetch only missing dates from API"""
        try:
            if not missing_dates:
                return None
            
            # Convert missing dates to date range
            min_date = min(missing_dates)
            max_date = max(missing_dates)
            
            # Fetch the entire range and filter
            start_date = min_date.strftime("%Y-%m-%d")
            end_date = max_date.strftime("%Y-%m-%d")
            
            api_data = self._fetch_from_api(symbol, start_date, end_date, interval)
            
            if api_data is not None:
                # Filter to only include missing dates
                filtered_data = api_data[api_data.index.isin(missing_dates)]
                return filtered_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching missing dates for {symbol}: {e}")
            return None
    
    def _generate_date_range(self, start_date: date, end_date: date) -> set:
        """Generate set of business days in range"""
        dates = set()
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends (optional - remove for crypto/24-7 markets)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                dates.add(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    def get_cache_status(self, symbol: str) -> Dict:
        """Get cache status for a symbol"""
        return self.db_service.get_cache_status(symbol)
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        return {
            'total_requests': self.stats.total_requests,
            'cache_hits': self.stats.cache_hits,
            'cache_misses': self.stats.cache_misses,
            'api_calls': self.stats.api_calls,
            'cache_hit_rate': self.stats.cache_hit_rate,
            'cache_enabled': self._cache_enabled
        }
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Clean up old data from database"""
        return self.db_service.cleanup_old_data(days_to_keep)


# Convenience function
def get_cached_market_data_manager(database_url: Optional[str] = None) -> CachedMarketDataManager:
    """Get a configured cached market data manager"""
    # Respect the DATABASE_ONLY env variable
    database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
    return CachedMarketDataManager(database_url, database_only=database_only) 