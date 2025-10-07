"""
Market Data Integration

Integration with market data services for the comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import requests
import pandas as pd
from dataclasses import dataclass

from ..utils.risk_utils import CacheUtils
from ..database.connection import get_redis_client


logger = logging.getLogger(__name__)


@dataclass
class MarketDataConfig:
    """Market data integration configuration."""
    yahoo_finance_enabled: bool = True
    polygon_enabled: bool = True
    alpha_vantage_enabled: bool = False
    cache_ttl_minutes: int = 15
    max_retries: int = 3
    request_timeout_seconds: int = 30
    rate_limit_per_minute: int = 60


class MarketDataProvider:
    """Base class for market data providers."""
    
    def __init__(self, config: MarketDataConfig):
        """Initialize market data provider."""
        self.config = config
        self.redis_client = get_redis_client()
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical market data.
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with historical data or None if failed
        """
        raise NotImplementedError
    
    def get_current_prices(
        self,
        symbols: List[str]
    ) -> Dict[str, float]:
        """
        Get current prices for symbols.
        
        Args:
            symbols: List of asset symbols
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        raise NotImplementedError
    
    def get_volatility_data(
        self,
        symbol: str,
        period_days: int = 30
    ) -> Optional[float]:
        """
        Get volatility data for a symbol.
        
        Args:
            symbol: Asset symbol
            period_days: Period for volatility calculation
            
        Returns:
            Volatility value or None if failed
        """
        raise NotImplementedError


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance market data provider."""
    
    def __init__(self, config: MarketDataConfig):
        """Initialize Yahoo Finance provider."""
        super().__init__(config)
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.quote_url = "https://query1.finance.yahoo.com/v7/finance/quote"
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get historical data from Yahoo Finance."""
        try:
            # Check cache first
            cache_key = CacheUtils.generate_cache_key(
                "yahoo_historical",
                symbol,
                start_date.isoformat(),
                end_date.isoformat(),
                interval
            )
            
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Prepare request parameters
            params = {
                "symbol": symbol,
                "period1": int(start_date.timestamp()),
                "period2": int(end_date.timestamp()),
                "interval": interval,
                "includePrePost": "true",
                "events": "div,split"
            }
            
            # Make request
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.config.request_timeout_seconds
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            chart_data = data.get("chart", {}).get("result", [])
            
            if not chart_data:
                logger.warning(f"No data received for symbol {symbol}")
                return None
            
            # Extract price data
            result = chart_data[0]
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            
            # Create DataFrame
            df_data = {
                "timestamp": [datetime.fromtimestamp(ts) for ts in timestamps],
                "open": quote.get("open", []),
                "high": quote.get("high", []),
                "low": quote.get("low", []),
                "close": quote.get("close", []),
                "volume": quote.get("volume", [])
            }
            
            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            
            # Cache the result
            self._cache_data(cache_key, df)
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
            return None
    
    def get_current_prices(
        self,
        symbols: List[str]
    ) -> Dict[str, float]:
        """Get current prices from Yahoo Finance."""
        try:
            # Check cache first
            cache_key = CacheUtils.generate_cache_key("yahoo_quotes", *symbols)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Prepare request
            symbols_param = ",".join(symbols)
            params = {
                "symbols": symbols_param,
                "fields": "regularMarketPrice"
            }
            
            # Make request
            response = requests.get(
                self.quote_url,
                params=params,
                timeout=self.config.request_timeout_seconds
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            quote_data = data.get("quoteResponse", {}).get("result", [])
            
            prices = {}
            for quote in quote_data:
                symbol = quote.get("symbol")
                price = quote.get("regularMarketPrice")
                
                if symbol and price is not None:
                    prices[symbol] = float(price)
            
            # Cache the result
            self._cache_data(cache_key, prices)
            
            logger.info(f"Retrieved current prices for {len(prices)} symbols")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to get current prices: {str(e)}")
            return {}
    
    def get_volatility_data(
        self,
        symbol: str,
        period_days: int = 30
    ) -> Optional[float]:
        """Get volatility data from Yahoo Finance."""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 10)  # Extra days for calculation
            
            df = self.get_historical_data(symbol, start_date, end_date)
            if df is None or len(df) < 10:
                return None
            
            # Calculate volatility from returns
            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Annualized
            
            logger.info(f"Calculated volatility for {symbol}: {volatility:.4f}")
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Failed to calculate volatility for {symbol}: {str(e)}")
            return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                import pickle
                return pickle.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to get data from cache: {str(e)}")
        
        return None
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data."""
        if not self.redis_client:
            return
        
        try:
            import pickle
            serialized_data = pickle.dumps(data)
            self.redis_client.setex(
                cache_key,
                self.config.cache_ttl_minutes * 60,
                serialized_data
            )
        except Exception as e:
            logger.warning(f"Failed to cache data: {str(e)}")


class PolygonProvider(MarketDataProvider):
    """Polygon.io market data provider."""
    
    def __init__(self, config: MarketDataConfig, api_key: str):
        """Initialize Polygon provider."""
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get historical data from Polygon.io."""
        try:
            # Check cache first
            cache_key = CacheUtils.generate_cache_key(
                "polygon_historical",
                symbol,
                start_date.isoformat(),
                end_date.isoformat(),
                interval
            )
            
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Prepare request
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                "apikey": self.api_key,
                "adjusted": "true",
                "sort": "asc"
            }
            
            # Make request
            response = requests.get(
                url,
                params=params,
                timeout=self.config.request_timeout_seconds
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"No data received for symbol {symbol}")
                return None
            
            # Create DataFrame
            df_data = []
            for result in results:
                df_data.append({
                    "timestamp": datetime.fromtimestamp(result["t"] / 1000),
                    "open": result["o"],
                    "high": result["h"],
                    "low": result["l"],
                    "close": result["c"],
                    "volume": result["v"]
                })
            
            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            
            # Cache the result
            self._cache_data(cache_key, df)
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
            return None
    
    def get_current_prices(
        self,
        symbols: List[str]
    ) -> Dict[str, float]:
        """Get current prices from Polygon.io."""
        prices = {}
        
        for symbol in symbols:
            try:
                # Check cache first
                cache_key = CacheUtils.generate_cache_key("polygon_quote", symbol)
                cached_price = self._get_from_cache(cache_key)
                if cached_price:
                    prices[symbol] = cached_price
                    continue
                
                # Make request
                url = f"{self.base_url}/v1/last_quote/stocks/{symbol}"
                params = {"apikey": self.api_key}
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.config.request_timeout_seconds
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                quote_data = data.get("results", {})
                
                if quote_data:
                    price = (quote_data.get("P", 0) + quote_data.get("p", 0)) / 2  # Average of bid/ask
                    prices[symbol] = float(price)
                    
                    # Cache the result
                    self._cache_data(cache_key, price)
                
            except Exception as e:
                logger.error(f"Failed to get current price for {symbol}: {str(e)}")
        
        logger.info(f"Retrieved current prices for {len(prices)} symbols")
        return prices
    
    def get_volatility_data(
        self,
        symbol: str,
        period_days: int = 30
    ) -> Optional[float]:
        """Get volatility data from Polygon.io."""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 10)
            
            df = self.get_historical_data(symbol, start_date, end_date)
            if df is None or len(df) < 10:
                return None
            
            # Calculate volatility
            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)
            
            logger.info(f"Calculated volatility for {symbol}: {volatility:.4f}")
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Failed to calculate volatility for {symbol}: {str(e)}")
            return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                import pickle
                return pickle.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to get data from cache: {str(e)}")
        
        return None
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data."""
        if not self.redis_client:
            return
        
        try:
            import pickle
            serialized_data = pickle.dumps(data)
            self.redis_client.setex(
                cache_key,
                self.config.cache_ttl_minutes * 60,
                serialized_data
            )
        except Exception as e:
            logger.warning(f"Failed to cache data: {str(e)}")


class MarketDataManager:
    """Market data integration manager."""
    
    def __init__(self, config: MarketDataConfig = None):
        """Initialize market data manager."""
        self.config = config or MarketDataConfig()
        self.providers = {}
        
        # Initialize providers
        if self.config.yahoo_finance_enabled:
            self.providers["yahoo"] = YahooFinanceProvider(self.config)
        
        if self.config.polygon_enabled:
            api_key = self._get_polygon_api_key()
            if api_key:
                self.providers["polygon"] = PolygonProvider(self.config, api_key)
            else:
                logger.warning("Polygon API key not found, disabling Polygon provider")
        
        logger.info(f"Initialized market data manager with {len(self.providers)} providers")
    
    def _get_polygon_api_key(self) -> Optional[str]:
        """Get Polygon API key from environment."""
        import os
        return os.getenv("POLYGON_API_KEY")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        provider: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data from preferred provider.
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            provider: Preferred provider (optional)
            
        Returns:
            DataFrame with historical data or None if failed
        """
        # Try preferred provider first
        if provider and provider in self.providers:
            result = self.providers[provider].get_historical_data(
                symbol, start_date, end_date, interval
            )
            if result is not None:
                return result
        
        # Try all providers
        for provider_name, provider_instance in self.providers.items():
            if provider_name == provider:
                continue  # Already tried
            
            result = provider_instance.get_historical_data(
                symbol, start_date, end_date, interval
            )
            if result is not None:
                logger.info(f"Retrieved data for {symbol} from {provider_name}")
                return result
        
        logger.error(f"Failed to retrieve historical data for {symbol} from all providers")
        return None
    
    def get_current_prices(
        self,
        symbols: List[str],
        provider: str = None
    ) -> Dict[str, float]:
        """
        Get current prices from preferred provider.
        
        Args:
            symbols: List of asset symbols
            provider: Preferred provider (optional)
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        # Try preferred provider first
        if provider and provider in self.providers:
            result = self.providers[provider].get_current_prices(symbols)
            if result:
                return result
        
        # Try all providers
        for provider_name, provider_instance in self.providers.items():
            if provider_name == provider:
                continue  # Already tried
            
            result = provider_instance.get_current_prices(symbols)
            if result:
                logger.info(f"Retrieved current prices from {provider_name}")
                return result
        
        logger.error("Failed to retrieve current prices from all providers")
        return {}
    
    def get_volatility_data(
        self,
        symbol: str,
        period_days: int = 30,
        provider: str = None
    ) -> Optional[float]:
        """
        Get volatility data from preferred provider.
        
        Args:
            symbol: Asset symbol
            period_days: Period for volatility calculation
            provider: Preferred provider (optional)
            
        Returns:
            Volatility value or None if failed
        """
        # Try preferred provider first
        if provider and provider in self.providers:
            result = self.providers[provider].get_volatility_data(symbol, period_days)
            if result is not None:
                return result
        
        # Try all providers
        for provider_name, provider_instance in self.providers.items():
            if provider_name == provider:
                continue  # Already tried
            
            result = provider_instance.get_volatility_data(symbol, period_days)
            if result is not None:
                logger.info(f"Retrieved volatility data for {symbol} from {provider_name}")
                return result
        
        logger.error(f"Failed to retrieve volatility data for {symbol} from all providers")
        return None
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        
        for provider_name, provider_instance in self.providers.items():
            try:
                # Test with a simple request
                test_symbol = "AAPL"
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                test_data = provider_instance.get_historical_data(
                    test_symbol, start_date, end_date
                )
                
                status[provider_name] = {
                    "enabled": True,
                    "status": "healthy" if test_data is not None else "degraded",
                    "last_check": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                status[provider_name] = {
                    "enabled": True,
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
        
        return status
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        redis_client = get_redis_client()
        if redis_client:
            try:
                # Clear all cache keys related to market data
                cache_keys = redis_client.keys("yahoo_*") + redis_client.keys("polygon_*")
                if cache_keys:
                    redis_client.delete(*cache_keys)
                logger.info(f"Cleared {len(cache_keys)} cache entries")
            except Exception as e:
                logger.error(f"Failed to clear cache: {str(e)}")
        else:
            logger.warning("Redis client not available for cache clearing")


# Global market data manager instance
_market_data_manager = None


def get_market_data_manager() -> MarketDataManager:
    """Get global market data manager instance."""
    global _market_data_manager
    
    if _market_data_manager is None:
        config = MarketDataConfig()
        _market_data_manager = MarketDataManager(config)
    
    return _market_data_manager


def initialize_market_data(config: MarketDataConfig = None) -> MarketDataManager:
    """Initialize market data integration."""
    global _market_data_manager
    
    _market_data_manager = MarketDataManager(config)
    logger.info("Market data integration initialized")
    
    return _market_data_manager






















