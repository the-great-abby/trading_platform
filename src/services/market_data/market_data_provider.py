"""
Comprehensive Market Data Provider System
Supports multiple data sources with fallback mechanisms
"""

import os
import time
import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import existing Yahoo Finance service
from .yahoo_finance_service import YahooFinanceService

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get historical market data"""
        pass
    
    @abstractmethod
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get current live price"""
        pass
    
    @abstractmethod
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        pass


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided")
        
        self.base_url = "https://www.alphavantage.co/query"
        self.session = self._create_session()
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_hits = 0
        self.min_delay_between_requests = 15.0  # Alpha Vantage has strict limits
        self.max_requests_per_minute = 5  # Free tier limit
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,  # Increased backoff factor
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting with adaptive delays"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Calculate required delay
        required_delay = self.min_delay_between_requests
        
        # Add extra delay if we've hit rate limits recently
        if self.rate_limit_hits > 0:
            extra_delay = self.rate_limit_hits * 45  # 45s extra per rate limit hit
            required_delay += extra_delay
        
        # If we haven't waited long enough, wait
        if time_since_last_request < required_delay:
            sleep_time = required_delay - time_since_last_request
            logger.info(f"[AlphaVantage] Rate limiting: waiting {sleep_time:.2f}s before next request")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get historical data from Alpha Vantage"""
        if not self.api_key:
            logger.error("Alpha Vantage API key required")
            return None
        
        try:
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            logger.info(f"[AlphaVantage] Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Alpha Vantage uses different interval formats
            interval_map = {
                "1d": "TIME_SERIES_DAILY",
                "1h": "TIME_SERIES_INTRADAY",
                "5m": "TIME_SERIES_INTRADAY"
            }
            
            function = interval_map.get(interval, "TIME_SERIES_DAILY")
            
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "full"
            }
            
            if interval == "1h":
                params["interval"] = "60min"
            elif interval == "5m":
                params["interval"] = "5min"
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            # Print detailed response information
            logger.info(f"[AlphaVantage] Response status: {response.status_code}")
            logger.info(f"[AlphaVantage] Response headers: {dict(response.headers)}")
            
            if response.status_code == 429:
                # Rate limit hit - increase delays
                self.rate_limit_hits += 1
                wait_time = 90 + (self.rate_limit_hits * 45)  # 90s + 45s per hit
                logger.warning(f"[AlphaVantage] Rate limited! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return None
            elif response.status_code != 200:
                logger.error(f"[AlphaVantage] HTTP {response.status_code}: {response.text}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Print response content for debugging
            logger.info(f"[AlphaVantage] Response keys: {list(data.keys())}")
            if "Error Message" in data:
                logger.error(f"[AlphaVantage] Error: {data['Error Message']}")
                return None
            
            if "Note" in data:
                # Rate limit message from Alpha Vantage
                self.rate_limit_hits += 1
                wait_time = 90 + (self.rate_limit_hits * 45)
                logger.warning(f"[AlphaVantage] Rate limit: {data['Note']}")
                logger.warning(f"[AlphaVantage] Waiting {wait_time}s...")
                time.sleep(wait_time)
                return None
            
            # Parse the response
            time_series_key = None
            for key in data.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                logger.error("[AlphaVantage] No time series data found in response")
                logger.error(f"[AlphaVantage] Available keys: {list(data.keys())}")
                logger.error(f"[AlphaVantage] Response content: {data}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            df.index = pd.to_datetime(df.index)
            
            # Rename columns
            column_mapping = {
                "1. open": "Open",
                "2. high": "High", 
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            }
            df = df.rename(columns=column_mapping)
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            # Add symbol column
            df['Symbol'] = symbol
            
            # Convert to numeric
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Reset rate limit counter on successful request
            if self.rate_limit_hits > 0:
                self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
            
            logger.info(f"[AlphaVantage] Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"[AlphaVantage] Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get current price from Alpha Vantage"""
        logger.info(f"🔍 DEBUG: AlphaVantageProvider.get_live_price({symbol}) - Starting")
        
        if not self.api_key:
            logger.warning(f"⚠️ DEBUG: {symbol} - No API key configured for Alpha Vantage")
            return None
        
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            url = f"{self.base_url}"
            logger.info(f"🔍 DEBUG: {symbol} - Making request to: {url}")
            logger.info(f"🔍 DEBUG: {symbol} - Params: {params}")
            
            response = self.session.get(url, params=params)
            logger.info(f"🔍 DEBUG: {symbol} - Response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"🔍 DEBUG: {symbol} - Response data: {data}")
            
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                logger.info(f"🔍 DEBUG: {symbol} - Global Quote keys: {list(quote.keys())}")
                
                price = quote.get("05. price")
                logger.info(f"🔍 DEBUG: {symbol} - Raw price from Alpha Vantage: {price}")
                
                if price:
                    final_price = float(price)
                    logger.info(f"✅ DEBUG: {symbol} - Final price from Alpha Vantage: {final_price}")
                    return final_price
                else:
                    logger.warning(f"⚠️ DEBUG: {symbol} - No price found in Global Quote")
            else:
                logger.warning(f"⚠️ DEBUG: {symbol} - No Global Quote found in response")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ DEBUG: {symbol} - Error getting live price from Alpha Vantage: {str(e)}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_historical_data(symbol, start_date, end_date, interval)
                if data is not None:
                    results[symbol] = data
                else:
                    logger.warning(f"Failed to get Alpha Vantage data for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched Alpha Vantage data for {len(results)}/{len(symbols)} symbols")
        return results


class IEXCloudProvider(MarketDataProvider):
    """IEX Cloud market data provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('IEX_CLOUD_API_KEY')
        if not self.api_key:
            logger.warning("IEX Cloud API key not provided")
        
        self.base_url = "https://cloud.iexapis.com/stable"
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get historical data from IEX Cloud"""
        if not self.api_key:
            logger.error("IEX Cloud API key required")
            return None
        
        try:
            # IEX Cloud uses different endpoint for historical data
            endpoint = f"/stock/{symbol}/chart/5y"  # 5 years of data
            
            params = {
                "token": self.api_key
            }
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Rename columns
            column_mapping = {
                "open": "Open",
                "high": "High",
                "low": "Low", 
                "close": "Close",
                "volume": "Volume"
            }
            df = df.rename(columns=column_mapping)
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            # Add symbol column
            df['Symbol'] = symbol
            
            logger.info(f"Successfully fetched {len(df)} records for {symbol} from IEX Cloud")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from IEX Cloud for {symbol}: {str(e)}")
            return None
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get current price from IEX Cloud"""
        if not self.api_key:
            return None
        
        try:
            endpoint = f"/stock/{symbol}/quote"
            params = {"token": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "latestPrice" in data:
                return float(data["latestPrice"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting live price from IEX Cloud for {symbol}: {str(e)}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_historical_data(symbol, start_date, end_date, interval)
                if data is not None:
                    results[symbol] = data
                else:
                    logger.warning(f"Failed to get IEX Cloud data for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched IEX Cloud data for {len(results)}/{len(symbols)} symbols")
        return results


class PolygonProvider(MarketDataProvider):
    """Polygon.io market data provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            logger.warning("Polygon API key not provided")
        
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        # Rate limiting state - more aggressive for paid plans
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_hits = 0
        self.min_delay_between_requests = 1.0  # Reduced delay for paid plans
        self.max_requests_per_minute = 60  # Higher limit for paid plans
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=3,  # Increased backoff factor
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting with adaptive delays"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Calculate required delay
        required_delay = self.min_delay_between_requests
        
        # Add extra delay if we've hit rate limits recently
        if self.rate_limit_hits > 0:
            extra_delay = self.rate_limit_hits * 60  # 60s extra per rate limit hit
            required_delay += extra_delay
        
        # If we haven't waited long enough, wait
        if time_since_last_request < required_delay:
            sleep_time = required_delay - time_since_last_request
            logger.info(f"[Polygon] Rate limiting: waiting {sleep_time:.2f}s before next request")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get historical data from Polygon"""
        if not self.api_key:
            logger.error("Polygon API key required")
            return None
        
        try:
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            logger.info(f"[Polygon] Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Polygon uses different interval formats
            interval_map = {
                "1d": "day",
                "1h": "hour",
                "5m": "minute"
            }
            
            timespan = interval_map.get(interval, "day")
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{start_date}/{end_date}"
            params = {"apiKey": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            # Print detailed response information
            logger.info(f"[Polygon] Response status: {response.status_code}")
            logger.info(f"[Polygon] Response headers: {dict(response.headers)}")
            logger.info(f"[Polygon] Request URL: {response.url}")
            
            if response.status_code == 429:
                # Rate limit hit - increase delays
                self.rate_limit_hits += 1
                wait_time = 120 + (self.rate_limit_hits * 60)  # 2min + 1min per hit
                logger.warning(f"[Polygon] Rate limited! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return None
            elif response.status_code == 403:
                logger.error(f"[Polygon] 403 Forbidden - check API key and subscription tier")
                logger.error(f"[Polygon] Response content: {response.text}")
                return None
            elif response.status_code != 200:
                logger.error(f"[Polygon] HTTP {response.status_code}: {response.text}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Print response content for debugging
            logger.info(f"[Polygon] Response keys: {list(data.keys())}")
            
            # Polygon can return "OK" or "DELAYED" status - both are valid
            status = data.get("status")
            if status not in ["OK", "DELAYED"]:
                logger.error(f"[Polygon] Error: {data.get('error', 'Unknown error')}")
                logger.error(f"[Polygon] Full response: {data}")
                return None
            
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"[Polygon] No data returned for {symbol}")
                logger.warning(f"[Polygon] Response content: {data}")
                return None
            
            # Debug: Log first few results
            logger.info(f"[Polygon] First 3 results: {results[:3]}")
            logger.info(f"[Polygon] Full response data: {data}")
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            df = df.set_index('t')
            
            # Rename columns
            column_mapping = {
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Close",
                "v": "Volume"
            }
            df = df.rename(columns=column_mapping)
            
            # Add symbol column
            df['Symbol'] = symbol
            
            # Reset rate limit counter on successful request
            if self.rate_limit_hits > 0:
                self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
            
            logger.info(f"[Polygon] Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"[Polygon] Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get current price from Polygon"""
        logger.info(f"🔍 DEBUG: PolygonProvider.get_live_price({symbol}) - Starting")
        
        if not self.api_key:
            logger.warning(f"⚠️ DEBUG: {symbol} - No API key configured for Polygon")
            return None
        
        try:
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {"apiKey": self.api_key}
            
            url = f"{self.base_url}{endpoint}"
            logger.info(f"🔍 DEBUG: {symbol} - Making request to: {url}")
            
            response = self.session.get(url, params=params)
            logger.info(f"🔍 DEBUG: {symbol} - Response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"🔍 DEBUG: {symbol} - Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if "ticker" in data and data["ticker"]:
                ticker_data = data["ticker"]
                logger.info(f"🔍 DEBUG: {symbol} - Ticker keys: {list(ticker_data.keys()) if isinstance(ticker_data, dict) else 'Not a dict'}")
                
                # Try to get current price from day data
                if "day" in ticker_data and "c" in ticker_data["day"]:
                    price = float(ticker_data["day"]["c"])
                    logger.info(f"✅ DEBUG: {symbol} - Found price in ticker.day.c: {price}")
                    return price
                # Fallback to min data
                elif "min" in ticker_data and "c" in ticker_data["min"]:
                    price = float(ticker_data["min"]["c"])
                    logger.info(f"✅ DEBUG: {symbol} - Found price in ticker.min.c: {price}")
                    return price
                else:
                    logger.warning(f"⚠️ DEBUG: {symbol} - No price found in ticker data")
            else:
                logger.warning(f"⚠️ DEBUG: {symbol} - No ticker found in response")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ DEBUG: {symbol} - Error getting live price from Polygon: {str(e)}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_historical_data(symbol, start_date, end_date, interval)
                if data is not None:
                    results[symbol] = data
                else:
                    logger.warning(f"Failed to get Polygon data for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched Polygon data for {len(results)}/{len(symbols)} symbols")
        return results


class MarketDataManager:
    """Manages multiple market data providers with fallback mechanisms"""
    
    def __init__(self, providers: Optional[List[MarketDataProvider]] = None):
        self.providers = providers or []
        self.current_provider_index = 0
        
        # Add default providers if none provided
        if not self.providers:
            self._add_default_providers()
    
    def _add_default_providers(self):
        """Add default providers in order of preference"""
        # 1. Polygon (paid - highest priority)
        polygon = PolygonProvider()
        if polygon.api_key:
            self.providers.append(polygon)
            logger.info("Added Polygon as primary provider (paid)")
        
        # 2. Yahoo Finance (free, no API key required)
        self.providers.append(YahooFinanceService())
        logger.info("Added Yahoo Finance as secondary provider (free)")
        
        # 3. IEX Cloud (free tier available)
        iex_cloud = IEXCloudProvider()
        if iex_cloud.api_key:
            self.providers.append(iex_cloud)
            logger.info("Added IEX Cloud as tertiary provider (free tier)")
        
        logger.info(f"Total providers configured: {len(self.providers)}")
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            logger.info(f"  {i+1}. {provider_name}")
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get historical data with provider fallback"""
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Trying provider {i+1}/{len(self.providers)} for {symbol}")
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
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get live price with provider fallback"""
        logger.info(f"🔍 DEBUG: MarketDataManager.get_live_price({symbol}) - Starting with {len(self.providers)} providers")
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            logger.info(f"🔍 DEBUG: {symbol} - Trying provider {i+1}/{len(self.providers)}: {provider_name}")
            
            try:
                price = provider.get_live_price(symbol)
                logger.info(f"🔍 DEBUG: {symbol} - {provider_name} returned: {price}")
                
                if price is not None:
                    logger.info(f"✅ DEBUG: {symbol} - Successfully got live price from {provider_name}: {price}")
                    return price
                else:
                    logger.warning(f"⚠️ DEBUG: {symbol} - {provider_name} returned None")
                    
            except Exception as e:
                logger.error(f"❌ DEBUG: {symbol} - {provider_name} failed: {str(e)}")
                continue
        
        logger.error(f"❌ DEBUG: {symbol} - All providers failed for live price")
        return None
    
    def get_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols with provider fallback"""
        results = {}
        
        for symbol in symbols:
            data = self.get_historical_data(symbol, start_date, end_date, interval)
            if data is not None:
                results[symbol] = data
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        status = {}
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            
            # Test with a simple symbol
            try:
                price = provider.get_live_price("AAPL")
                status[provider_name] = price is not None
            except:
                status[provider_name] = False
        
        return status


# Convenience functions
def get_market_data_manager() -> MarketDataManager:
    """Get a configured market data manager"""
    return MarketDataManager()


def get_historical_data(symbols: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
    """Get historical data for multiple symbols"""
    manager = get_market_data_manager()
    return manager.get_multiple_symbols(symbols, start_date, end_date, interval)


def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    """Get live prices for multiple symbols"""
    manager = get_market_data_manager()
    results = {}
    
    for symbol in symbols:
        price = manager.get_live_price(symbol)
        if price is not None:
            results[symbol] = price
    
    return results 