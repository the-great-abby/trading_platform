"""
Market Data Integration Utilities
Integration with market data services for portfolio management
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import aiohttp
import json
import time
from functools import lru_cache

from ..models.asset import Asset
from ..config.portfolio_config import MarketDataConfig

logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Single market data point"""
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None

@dataclass
class MarketDataResponse:
    """Market data response"""
    symbol: str
    data: List[MarketDataPoint]
    success: bool
    error_message: Optional[str] = None
    source: str = "unknown"
    cached: bool = False

class MarketDataProvider:
    """Base class for market data providers"""
    
    def __init__(self, config: MarketDataConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = config.api_rate_limit_per_minute
        self.rate_limit_reset = time.time() + 60
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.api_timeout_seconds)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset rate limit if minute has passed
        if current_time >= self.rate_limit_reset:
            self.rate_limit_remaining = self.config.api_rate_limit_per_minute
            self.rate_limit_reset = current_time + 60
        
        if self.rate_limit_remaining <= 0:
            sleep_time = self.rate_limit_reset - current_time
            logger.warning(f"Rate limit exceeded, sleeping for {sleep_time:.1f} seconds")
            await asyncio.sleep(sleep_time)
            self.rate_limit_remaining = self.config.api_rate_limit_per_minute
            self.rate_limit_reset = time.time() + 60
        
        self.rate_limit_remaining -= 1
    
    async def get_historical_data(self, symbol: str, start_date: date, end_date: date) -> MarketDataResponse:
        """Get historical market data"""
        raise NotImplementedError
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        raise NotImplementedError
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        raise NotImplementedError

class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider"""
    
    def __init__(self, config: MarketDataConfig):
        super().__init__(config)
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    async def get_historical_data(self, symbol: str, start_date: date, end_date: date) -> MarketDataResponse:
        """Get historical data from Yahoo Finance"""
        try:
            await self._check_rate_limit()
            
            # Convert dates to timestamps
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            url = f"{self.base_url}/{symbol}"
            params = {
                "period1": start_timestamp,
                "period2": end_timestamp,
                "interval": "1d",
                "includePrePost": "false",
                "events": "div,split"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return MarketDataResponse(
                        symbol=symbol,
                        data=[],
                        success=False,
                        error_message=f"HTTP {response.status}: {await response.text()}"
                    )
                
                data = await response.json()
                
                if "chart" not in data or not data["chart"]["result"]:
                    return MarketDataResponse(
                        symbol=symbol,
                        data=[],
                        success=False,
                        error_message="No data available"
                    )
                
                result = data["chart"]["result"][0]
                timestamps = result["timestamp"]
                quotes = result["indicators"]["quote"][0]
                
                data_points = []
                for i, timestamp in enumerate(timestamps):
                    if quotes["open"][i] is not None:
                        data_point = MarketDataPoint(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(timestamp),
                            open_price=quotes["open"][i],
                            high_price=quotes["high"][i],
                            low_price=quotes["low"][i],
                            close_price=quotes["close"][i],
                            volume=quotes["volume"][i] or 0
                        )
                        data_points.append(data_point)
                
                return MarketDataResponse(
                    symbol=symbol,
                    data=data_points,
                    success=True,
                    source="yfinance"
                )
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return MarketDataResponse(
                symbol=symbol,
                data=[],
                success=False,
                error_message=str(e)
            )
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Yahoo Finance"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/{symbol}"
            params = {
                "interval": "1m",
                "range": "1d"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if "chart" not in data or not data["chart"]["result"]:
                    return None
                
                result = data["chart"]["result"][0]
                quotes = result["indicators"]["quote"][0]
                
                if quotes["close"] and quotes["close"][-1] is not None:
                    return quotes["close"][-1]
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        prices = {}
        
        # Yahoo Finance doesn't have a bulk endpoint, so we'll fetch individually
        # but with some concurrency
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.get_current_price(symbol))
            tasks.append((symbol, task))
        
        for symbol, task in tasks:
            try:
                price = await task
                prices[symbol] = price
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                prices[symbol] = None
        
        return prices

class PolygonProvider(MarketDataProvider):
    """Polygon.io data provider"""
    
    def __init__(self, config: MarketDataConfig, api_key: str):
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
    
    async def get_historical_data(self, symbol: str, start_date: date, end_date: date) -> MarketDataResponse:
        """Get historical data from Polygon.io"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
            params = {
                "adjusted": "true",
                "sort": "asc",
                "apikey": self.api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return MarketDataResponse(
                        symbol=symbol,
                        data=[],
                        success=False,
                        error_message=f"HTTP {response.status}: {await response.text()}"
                    )
                
                data = await response.json()
                
                if data.get("status") != "OK" or "results" not in data:
                    return MarketDataResponse(
                        symbol=symbol,
                        data=[],
                        success=False,
                        error_message="No data available"
                    )
                
                data_points = []
                for result in data["results"]:
                    data_point = MarketDataPoint(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(result["t"] / 1000),
                        open_price=result["o"],
                        high_price=result["h"],
                        low_price=result["l"],
                        close_price=result["c"],
                        volume=result["v"],
                        adjusted_close=result.get("c")
                    )
                    data_points.append(data_point)
                
                return MarketDataResponse(
                    symbol=symbol,
                    data=data_points,
                    success=True,
                    source="polygon"
                )
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return MarketDataResponse(
                symbol=symbol,
                data=[],
                success=False,
                error_message=str(e)
            )
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Polygon.io"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {"apikey": self.api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get("status") != "OK" or "ticker" not in data:
                    return None
                
                ticker = data["ticker"]
                if "day" in ticker and "c" in ticker["day"]:
                    return ticker["day"]["c"]
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        try:
            await self._check_rate_limit()
            
            # Polygon.io has a snapshot endpoint for multiple tickers
            symbols_str = ",".join(symbols)
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers"
            params = {
                "tickers": symbols_str,
                "apikey": self.api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    # Fall back to individual requests
                    return await super().get_multiple_prices(symbols)
                
                data = await response.json()
                
                if data.get("status") != "OK" or "tickers" not in data:
                    return await super().get_multiple_prices(symbols)
                
                prices = {}
                for ticker_data in data["tickers"]:
                    symbol = ticker_data["ticker"]
                    if "day" in ticker_data and "c" in ticker_data["day"]:
                        prices[symbol] = ticker_data["day"]["c"]
                    else:
                        prices[symbol] = None
                
                # Fill in any missing symbols
                for symbol in symbols:
                    if symbol not in prices:
                        prices[symbol] = None
                
                return prices
                
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            return await super().get_multiple_prices(symbols)

class MarketDataManager:
    """Manages market data providers and caching"""
    
    def __init__(self, config: MarketDataConfig, polygon_api_key: Optional[str] = None):
        self.config = config
        self.polygon_api_key = polygon_api_key
        self.providers: Dict[str, MarketDataProvider] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize market data providers"""
        self.providers["yfinance"] = YFinanceProvider(self.config)
        
        if self.polygon_api_key:
            self.providers["polygon"] = PolygonProvider(self.config, self.polygon_api_key)
    
    def _get_cache_key(self, symbol: str, start_date: date, end_date: date, data_type: str) -> str:
        """Generate cache key"""
        return f"{data_type}:{symbol}:{start_date}:{end_date}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid"""
        if cache_key not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[cache_key]
        cache_age = datetime.now() - cache_time
        
        return cache_age.total_seconds() < (self.config.cache_duration_hours * 3600)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache"""
        if self._is_cache_valid(cache_key):
            return self.cache.get(cache_key)
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set data in cache"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now()
    
    async def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                                provider: Optional[str] = None) -> MarketDataResponse:
        """Get historical market data"""
        # Check cache first
        cache_key = self._get_cache_key(symbol, start_date, end_date, "historical")
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            cached_data.cached = True
            return cached_data
        
        # Determine provider
        if provider is None:
            provider = self.config.primary_data_source
        
        if provider not in self.providers:
            provider = self.config.backup_data_source
        
        # Fetch data
        async with self.providers[provider] as provider_instance:
            response = await provider_instance.get_historical_data(symbol, start_date, end_date)
        
        # Cache successful responses
        if response.success:
            self._set_cache(cache_key, response)
        
        return response
    
    async def get_current_price(self, symbol: str, provider: Optional[str] = None) -> Optional[float]:
        """Get current market price"""
        # Check cache first (shorter cache duration for current prices)
        cache_key = f"current_price:{symbol}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            return cached_data
        
        # Determine provider
        if provider is None:
            provider = self.config.primary_data_source
        
        if provider not in self.providers:
            provider = self.config.backup_data_source
        
        # Fetch data
        async with self.providers[provider] as provider_instance:
            price = await provider_instance.get_current_price(symbol)
        
        # Cache price (shorter duration)
        if price is not None:
            self._set_cache(cache_key, price)
        
        return price
    
    async def get_multiple_prices(self, symbols: List[str], provider: Optional[str] = None) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        prices = {}
        uncached_symbols = []
        
        # Check cache for each symbol
        for symbol in symbols:
            cache_key = f"current_price:{symbol}"
            cached_price = self._get_from_cache(cache_key)
            
            if cached_price is not None:
                prices[symbol] = cached_price
            else:
                uncached_symbols.append(symbol)
        
        # Fetch uncached symbols
        if uncached_symbols:
            # Determine provider
            if provider is None:
                provider = self.config.primary_data_source
            
            if provider not in self.providers:
                provider = self.config.backup_data_source
            
            # Fetch data
            async with self.providers[provider] as provider_instance:
                fetched_prices = await provider_instance.get_multiple_prices(uncached_symbols)
            
            # Update results and cache
            for symbol, price in fetched_prices.items():
                prices[symbol] = price
                if price is not None:
                    cache_key = f"current_price:{symbol}"
                    self._set_cache(cache_key, price)
        
        return prices
    
    async def get_asset_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get asset data as pandas DataFrame"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        response = await self.get_historical_data(symbol, start_date, end_date)
        
        if not response.success or not response.data:
            return None
        
        # Convert to DataFrame
        data = []
        for point in response.data:
            data.append({
                "date": point.timestamp.date(),
                "open": point.open_price,
                "high": point.high_price,
                "low": point.low_price,
                "close": point.close_price,
                "volume": point.volume,
                "adjusted_close": point.adjusted_close or point.close_price
            })
        
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    async def get_returns_data(self, symbols: List[str], days: int = 252) -> Optional[pd.DataFrame]:
        """Get returns data for multiple symbols"""
        returns_data = {}
        
        for symbol in symbols:
            df = await self.get_asset_data(symbol, days)
            if df is not None and len(df) > 1:
                returns = df["adjusted_close"].pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            return None
        
        # Align dates
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        return returns_df
    
    async def get_correlation_matrix(self, symbols: List[str], days: int = 252) -> Optional[pd.DataFrame]:
        """Get correlation matrix for symbols"""
        returns_df = await self.get_returns_data(symbols, days)
        
        if returns_df is None or len(returns_df) < 30:
            return None
        
        return returns_df.corr()
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Market data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for key in self.cache.keys() if self._is_cache_valid(key))
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "cache_hit_rate": valid_entries / max(total_entries, 1),
            "cache_size_mb": sum(len(str(data)) for data in self.cache.values()) / (1024 * 1024)
        }

# Global market data manager
_market_data_manager: Optional[MarketDataManager] = None

def get_market_data_manager(config: Optional[MarketDataConfig] = None, 
                          polygon_api_key: Optional[str] = None) -> MarketDataManager:
    """Get global market data manager"""
    global _market_data_manager
    if _market_data_manager is None or config is not None:
        if config is None:
            from ..config.portfolio_config import get_portfolio_config
            config = get_portfolio_config().market_data
        _market_data_manager = MarketDataManager(config, polygon_api_key)
    return _market_data_manager

async def get_historical_data(symbol: str, start_date: date, end_date: date, 
                            provider: Optional[str] = None) -> MarketDataResponse:
    """Get historical market data"""
    manager = get_market_data_manager()
    return await manager.get_historical_data(symbol, start_date, end_date, provider)

async def get_current_price(symbol: str, provider: Optional[str] = None) -> Optional[float]:
    """Get current market price"""
    manager = get_market_data_manager()
    return await manager.get_current_price(symbol, provider)

async def get_multiple_prices(symbols: List[str], provider: Optional[str] = None) -> Dict[str, Optional[float]]:
    """Get current prices for multiple symbols"""
    manager = get_market_data_manager()
    return await manager.get_multiple_prices(symbols, provider)

async def get_asset_data(symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
    """Get asset data as pandas DataFrame"""
    manager = get_market_data_manager()
    return await manager.get_asset_data(symbol, days)

async def get_returns_data(symbols: List[str], days: int = 252) -> Optional[pd.DataFrame]:
    """Get returns data for multiple symbols"""
    manager = get_market_data_manager()
    return await manager.get_returns_data(symbols, days)

async def get_correlation_matrix(symbols: List[str], days: int = 252) -> Optional[pd.DataFrame]:
    """Get correlation matrix for symbols"""
    manager = get_market_data_manager()
    return await manager.get_correlation_matrix(symbols, days)
























