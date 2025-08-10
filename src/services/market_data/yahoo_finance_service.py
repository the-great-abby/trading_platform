"""
Enhanced Yahoo Finance Market Data Service
Uses direct HTTP requests to avoid rate limiting issues
"""

import requests
import pandas as pd
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Enhanced Yahoo Finance market data service using direct HTTP requests"""
    
    def __init__(self, rate_limit_delay: float = 15.0):
        self.rate_limit_delay = rate_limit_delay
        self.session = self._create_session()
        self.base_url = "https://query2.finance.yahoo.com/v8/finance/chart"
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_hits = 0
        self.max_requests_per_minute = 5  # Conservative limit
        self.min_delay_between_requests = 15.0  # Minimum 15 seconds between requests
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy with longer backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=5,  # Increased backoff factor
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting with adaptive delays"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Calculate required delay
        required_delay = max(self.min_delay_between_requests, self.rate_limit_delay)
        
        # Add extra delay if we've hit rate limits recently
        if self.rate_limit_hits > 0:
            extra_delay = self.rate_limit_hits * 30  # 30s extra per rate limit hit
            required_delay += extra_delay
        
        # If we haven't waited long enough, wait
        if time_since_last_request < required_delay:
            sleep_time = required_delay - time_since_last_request
            logger.info(f"[YahooFinance] Rate limiting: waiting {sleep_time:.2f}s before next request")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request with sophisticated rate limiting and error handling."""
        try:
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            logger.info(f"[YahooFinance] Requesting: {url} at {datetime.now().isoformat()}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                # Rate limit hit - increase delays
                self.rate_limit_hits += 1
                wait_time = 60 + (self.rate_limit_hits * 30)  # 60s + 30s per hit
                logger.warning(f"[YahooFinance] Rate limited! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return None
            elif response.status_code == 403:
                logger.error(f"[YahooFinance] 403 Forbidden - possible IP block")
                return None
            elif response.status_code != 200:
                logger.error(f"[YahooFinance] HTTP {response.status_code}: {response.text}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Reset rate limit counter on successful request
            if self.rate_limit_hits > 0:
                self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limit_hits += 1
                logger.warning(f"[YahooFinance] Rate limited by Yahoo Finance, waiting 60 seconds...")
                time.sleep(60)
                return None
            else:
                logger.error(f"[YahooFinance] HTTP error: {e}")
                return None
        except Exception as e:
            logger.error(f"[YahooFinance] Request error: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Get historical market data for a symbol using direct API calls
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('1d', '1h', '5m', etc.)
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Convert dates to timestamps
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            
            # Map interval to Yahoo's format
            interval_map = {
                "1d": "1d",
                "1h": "1h", 
                "5m": "5m",
                "1m": "1m"
            }
            yahoo_interval = interval_map.get(interval, "1d")
            
            # Build URL
            url = f"{self.base_url}/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': yahoo_interval,
                'includePrePost': 'false',
                'events': 'div,split'
            }
            
            # Make request
            data = self._make_request(url, params)
            
            if not data or 'chart' not in data:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            chart_data = data['chart']
            if 'error' in chart_data and chart_data['error']:
                logger.error(f"Yahoo Finance error for {symbol}: {chart_data['error']}")
                return None
            
            if 'result' not in chart_data or not chart_data['result']:
                logger.warning(f"No result data for {symbol}")
                return None
            
            result = chart_data['result'][0]
            
            # Extract timestamps and OHLCV data
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            
            # Create DataFrame
            df_data = {
                'Open': quote.get('open', []),
                'High': quote.get('high', []),
                'Low': quote.get('low', []),
                'Close': quote.get('close', []),
                'Volume': quote.get('volume', [])
            }
            
            # Convert timestamps to datetime
            dates = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps])
            
            df = pd.DataFrame(df_data, index=dates)
            
            # Remove rows with NaN values
            df = df.dropna()
            
            if df.empty:
                logger.warning(f"No valid data returned for {symbol}")
                return None
            
            # Add symbol column
            df['Symbol'] = symbol
            
            logger.info(f"Successfully fetched {len(df)} historical records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """
        Get current live price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if failed
        """
        logger.info(f"🔍 DEBUG: YahooFinanceService.get_live_price({symbol}) - Starting")
        
        try:
            # Get recent data (last 2 days to ensure we have current data)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            
            logger.info(f"🔍 DEBUG: {symbol} - Getting historical data from {start_date} to {end_date}")
            data = self.get_historical_data(symbol, start_date, end_date, "1d")
            
            if data is not None and not data.empty:
                # Get the most recent close price
                latest_price = data['Close'].iloc[-1]
                logger.info(f"✅ DEBUG: {symbol} - Found latest close price: {latest_price}")
                return float(latest_price)
            else:
                logger.warning(f"⚠️ DEBUG: {symbol} - No price data available from Yahoo Finance")
                return None
                
        except Exception as e:
            logger.error(f"❌ DEBUG: {symbol} - Error getting live price from Yahoo Finance: {str(e)}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols with optimized batching
        
        Args:
            symbols: List of stock symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
                data = self.get_historical_data(symbol, start_date, end_date, interval)
                if data is not None:
                    results[symbol] = data
                else:
                    logger.warning(f"Failed to get data for {symbol}")
                    
                # Add extra delay between symbols to avoid rate limiting
                if i < len(symbols) - 1:  # Don't delay after the last symbol
                    time.sleep(self.rate_limit_delay * 2)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_live_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get live prices for multiple symbols with optimized batching
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                price = self.get_live_price(symbol)
                if price is not None:
                    results[symbol] = price
                else:
                    logger.warning(f"Failed to get live price for {symbol}")
                    
                # Add extra delay between symbols
                if i < len(symbols) - 1:
                    time.sleep(self.rate_limit_delay * 2)
                    
            except Exception as e:
                logger.error(f"Error getting live price for {symbol}: {str(e)}")
                continue
        
        return results
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed information about a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with symbol information or None if failed
        """
        try:
            # For now, return basic info since detailed info requires different endpoint
            price = self.get_live_price(symbol)
            
            if price is not None:
                symbol_info = {
                    'symbol': symbol,
                    'name': symbol,
                    'current_price': price,
                    'currency': 'USD'
                }
                return symbol_info
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {str(e)}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists and is tradeable
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            # Try to get a small amount of historical data to validate
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            data = self.get_historical_data(symbol, start_date, end_date, "1d")
            
            if data is not None and not data.empty:
                return True
            else:
                logger.warning(f"Symbol {symbol} appears to be invalid or delisted")
                return False
                
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {str(e)}")
            return False
    
    def get_market_hours(self) -> Dict[str, str]:
        """
        Get current market hours information
        
        Returns:
            Dictionary with market hours info
        """
        try:
            # For now, return basic market hours info
            market_hours = {
                'market_state': 'unknown',
                'timezone': 'America/New_York'
            }
            
            return market_hours
            
        except Exception as e:
            logger.error(f"Error getting market hours: {str(e)}")
            return {'market_state': 'unknown'}


# Convenience functions for easy integration
def get_market_data(symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
    """
    Convenience function to get market data for multiple symbols
    
    Args:
        symbols: List of stock symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval
        
    Returns:
        Dictionary mapping symbols to DataFrames
    """
    service = YahooFinanceService()
    return service.get_multiple_symbols(symbols, start_date, end_date, interval)


def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    """
    Convenience function to get live prices for multiple symbols
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dictionary mapping symbols to prices
    """
    service = YahooFinanceService()
    return service.get_live_prices_batch(symbols) 