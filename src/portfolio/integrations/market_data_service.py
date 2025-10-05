"""
Market Data Service Integration
Integration with existing market data service for portfolio management
"""
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json

from ..models.asset import Asset
from ..utils.market_data import MarketDataManager, get_market_data_manager
from ..config.portfolio_config import get_portfolio_config

logger = logging.getLogger(__name__)

@dataclass
class MarketDataServiceConfig:
    """Configuration for market data service integration"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_per_minute: int = 60

class MarketDataServiceIntegration:
    """Integration with existing market data service"""
    
    def __init__(self, config: Optional[MarketDataServiceConfig] = None):
        self.config = config or self._load_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = self.config.rate_limit_per_minute
        self.rate_limit_reset = datetime.now().timestamp() + 60
    
    def _load_config(self) -> MarketDataServiceConfig:
        """Load configuration from environment or defaults"""
        import os
        
        return MarketDataServiceConfig(
            base_url=os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data-service:11084"),
            api_key=os.getenv("MARKET_DATA_API_KEY"),
            timeout=int(os.getenv("MARKET_DATA_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("MARKET_DATA_RETRY_ATTEMPTS", "3")),
            rate_limit_per_minute=int(os.getenv("MARKET_DATA_RATE_LIMIT", "60"))
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now().timestamp()
        
        # Reset rate limit if minute has passed
        if current_time >= self.rate_limit_reset:
            self.rate_limit_remaining = self.config.rate_limit_per_minute
            self.rate_limit_reset = current_time + 60
        
        if self.rate_limit_remaining <= 0:
            sleep_time = self.rate_limit_reset - current_time
            logger.warning(f"Rate limit exceeded, sleeping for {sleep_time:.1f} seconds")
            await asyncio.sleep(sleep_time)
            self.rate_limit_remaining = self.config.rate_limit_per_minute
            self.rate_limit_reset = datetime.now().timestamp() + 60
        
        self.rate_limit_remaining -= 1
    
    async def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get asset information from market data service"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/assets/{symbol}"
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    logger.warning(f"Asset {symbol} not found in market data service")
                    return None
                else:
                    logger.error(f"Error fetching asset info for {symbol}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching asset info for {symbol}: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from market data service"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/prices/{symbol}/current"
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("price")
                elif response.status == 404:
                    logger.warning(f"Price not found for {symbol}")
                    return None
                else:
                    logger.error(f"Error fetching price for {symbol}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> Optional[List[Dict[str, Any]]]:
        """Get historical prices from market data service"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/prices/{symbol}/historical"
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("prices", [])
                elif response.status == 404:
                    logger.warning(f"Historical prices not found for {symbol}")
                    return None
                else:
                    logger.error(f"Error fetching historical prices for {symbol}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        prices = {}
        
        # Market data service might have a bulk endpoint
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/prices/bulk"
            data = {"symbols": symbols}
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    prices = response_data.get("prices", {})
                else:
                    logger.error(f"Error fetching bulk prices: HTTP {response.status}")
                    # Fall back to individual requests
                    for symbol in symbols:
                        prices[symbol] = None
                    
        except Exception as e:
            logger.error(f"Error fetching bulk prices: {e}")
            # Fall back to individual requests
            for symbol in symbols:
                prices[symbol] = None
        
        # Fill in any missing symbols with individual requests
        for symbol in symbols:
            if symbol not in prices or prices[symbol] is None:
                prices[symbol] = await self.get_current_price(symbol)
        
        return prices
    
    async def get_market_data(self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get comprehensive market data for a symbol"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get asset info and historical prices in parallel
            asset_info_task = self.get_asset_info(symbol)
            historical_prices_task = self.get_historical_prices(symbol, start_date, end_date)
            
            asset_info, historical_prices = await asyncio.gather(
                asset_info_task, historical_prices_task
            )
            
            if not asset_info and not historical_prices:
                return None
            
            return {
                "symbol": symbol,
                "asset_info": asset_info,
                "historical_prices": historical_prices,
                "current_price": historical_prices[-1]["close"] if historical_prices else None,
                "data_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    async def get_correlation_data(self, symbols: List[str], days: int = 252) -> Optional[Dict[str, Any]]:
        """Get correlation data for multiple symbols"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/correlation"
            params = {
                "symbols": ",".join(symbols),
                "days": days
            }
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error fetching correlation data: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching correlation data: {e}")
            return None
    
    async def get_sector_data(self, sector: str) -> Optional[Dict[str, Any]]:
        """Get sector-level market data"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/sectors/{sector}"
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    logger.warning(f"Sector {sector} not found")
                    return None
                else:
                    logger.error(f"Error fetching sector data for {sector}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching sector data for {sector}: {e}")
            return None
    
    async def get_benchmark_data(self, benchmark: str = "SPY", days: int = 252) -> Optional[Dict[str, Any]]:
        """Get benchmark data for portfolio comparison"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.config.base_url}/api/v1/benchmarks/{benchmark}"
            params = {"days": days}
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error fetching benchmark data for {benchmark}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching benchmark data for {benchmark}: {e}")
            return None

class PortfolioMarketDataManager:
    """Unified market data manager for portfolio management"""
    
    def __init__(self):
        self.market_data_service = MarketDataServiceIntegration()
        self.fallback_manager = get_market_data_manager()
        self.config = get_portfolio_config()
    
    async def get_asset_data(self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get asset data with fallback to external sources"""
        try:
            # Try market data service first
            async with self.market_data_service as service:
                data = await service.get_market_data(symbol, days)
                
                if data:
                    logger.info(f"Retrieved data for {symbol} from market data service")
                    return data
            
            # Fall back to external sources
            logger.info(f"Falling back to external sources for {symbol}")
            return await self._get_fallback_data(symbol, days)
            
        except Exception as e:
            logger.error(f"Error getting asset data for {symbol}: {e}")
            return await self._get_fallback_data(symbol, days)
    
    async def _get_fallback_data(self, symbol: str, days: int) -> Optional[Dict[str, Any]]:
        """Get data from fallback sources"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get historical data
            response = await self.fallback_manager.get_historical_data(symbol, start_date, end_date)
            
            if not response.success or not response.data:
                return None
            
            # Convert to expected format
            historical_prices = []
            for point in response.data:
                historical_prices.append({
                    "date": point.timestamp.date().isoformat(),
                    "open": point.open_price,
                    "high": point.high_price,
                    "low": point.low_price,
                    "close": point.close_price,
                    "volume": point.volume,
                    "adjusted_close": point.adjusted_close or point.close_price
                })
            
            return {
                "symbol": symbol,
                "asset_info": None,  # Would need to be fetched separately
                "historical_prices": historical_prices,
                "current_price": historical_prices[-1]["close"] if historical_prices else None,
                "data_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "source": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error getting fallback data for {symbol}: {e}")
            return None
    
    async def get_multiple_asset_data(self, symbols: List[str], days: int = 30) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get data for multiple assets"""
        results = {}
        
        # Process symbols in batches to avoid overwhelming the service
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [self.get_asset_data(symbol, days) for symbol in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {symbol}: {result}")
                    results[symbol] = None
                else:
                    results[symbol] = result
        
        return results
    
    async def get_correlation_matrix(self, symbols: List[str], days: int = 252) -> Optional[Dict[str, Any]]:
        """Get correlation matrix with fallback"""
        try:
            # Try market data service first
            async with self.market_data_service as service:
                data = await service.get_correlation_data(symbols, days)
                
                if data:
                    return data
            
            # Fall back to external sources
            return await self.fallback_manager.get_correlation_matrix(symbols, days)
            
        except Exception as e:
            logger.error(f"Error getting correlation matrix: {e}")
            return None
    
    async def get_benchmark_data(self, benchmark: str = "SPY", days: int = 252) -> Optional[Dict[str, Any]]:
        """Get benchmark data with fallback"""
        try:
            # Try market data service first
            async with self.market_data_service as service:
                data = await service.get_benchmark_data(benchmark, days)
                
                if data:
                    return data
            
            # Fall back to external sources
            return await self.get_asset_data(benchmark, days)
            
        except Exception as e:
            logger.error(f"Error getting benchmark data: {e}")
            return None

# Global market data manager
_portfolio_market_data_manager: Optional[PortfolioMarketDataManager] = None

def get_portfolio_market_data_manager() -> PortfolioMarketDataManager:
    """Get global portfolio market data manager"""
    global _portfolio_market_data_manager
    if _portfolio_market_data_manager is None:
        _portfolio_market_data_manager = PortfolioMarketDataManager()
    return _portfolio_market_data_manager

async def get_asset_data(symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
    """Get asset data for portfolio management"""
    manager = get_portfolio_market_data_manager()
    return await manager.get_asset_data(symbol, days)

async def get_multiple_asset_data(symbols: List[str], days: int = 30) -> Dict[str, Optional[Dict[str, Any]]]:
    """Get data for multiple assets"""
    manager = get_portfolio_market_data_manager()
    return await manager.get_multiple_asset_data(symbols, days)

async def get_correlation_matrix(symbols: List[str], days: int = 252) -> Optional[Dict[str, Any]]:
    """Get correlation matrix for portfolio optimization"""
    manager = get_portfolio_market_data_manager()
    return await manager.get_correlation_matrix(symbols, days)

async def get_benchmark_data(benchmark: str = "SPY", days: int = 252) -> Optional[Dict[str, Any]]:
    """Get benchmark data for portfolio comparison"""
    manager = get_portfolio_market_data_manager()
    return await manager.get_benchmark_data(benchmark, days)












