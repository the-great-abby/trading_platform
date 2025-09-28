"""
Market Data Service Integration

Integration with the existing market data service for the comprehensive
risk management framework.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import pandas as pd

from ..utils.risk_utils import CacheUtils, PerformanceUtils


logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data structure for risk management."""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: float
    ask: float
    high: float
    low: float
    open_price: float
    metadata: Dict[str, Any]


@dataclass
class HistoricalData:
    """Historical market data structure."""
    symbol: str
    data: pd.DataFrame
    start_date: datetime
    end_date: datetime
    frequency: str
    metadata: Dict[str, Any]


class MarketDataServiceIntegration:
    """
    Integration with the existing market data service.
    
    Provides market data access for risk calculations, including
    historical prices, volatility, and correlation data.
    """
    
    def __init__(
        self,
        market_data_service_url: str = "http://market-data-service:80",
        timeout_seconds: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize market data service integration.
        
        Args:
            market_data_service_url: URL of the market data service
            timeout_seconds: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.market_data_service_url = market_data_service_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Set up session with proper headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RiskManagementService/1.0.0'
        })
    
    @PerformanceUtils.measure_execution_time
    def get_current_prices(
        self,
        symbols: List[str]
    ) -> Dict[str, MarketData]:
        """
        Get current prices for multiple symbols.
        
        Args:
            symbols: List of symbols to get prices for
            
        Returns:
            Dictionary mapping symbols to MarketData objects
        """
        logger.info(f"Fetching current prices for {len(symbols)} symbols")
        
        try:
            # Build request parameters
            params = {
                'symbols': ','.join(symbols)
            }
            
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/current-prices',
                params=params
            )
            
            if not response:
                logger.error("Failed to fetch current prices")
                return {}
            
            # Parse prices from response
            prices_data = response.get('data', {}).get('prices', {})
            
            # Convert to MarketData objects
            market_data = {}
            for symbol, price_data in prices_data.items():
                try:
                    market_data[symbol] = self._parse_market_data(price_data, symbol)
                except Exception as e:
                    logger.warning(f"Error parsing price data for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched current prices for {len(market_data)} symbols")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching current prices: {str(e)}")
            return {}
    
    @PerformanceUtils.measure_execution_time
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        frequency: str = '1D'
    ) -> Optional[HistoricalData]:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            start_date: Start date for historical data
            end_date: End date for historical data
            frequency: Data frequency ('1D', '1H', '15M', etc.)
            
        Returns:
            HistoricalData object or None if failed
        """
        logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
        
        try:
            # Build request parameters
            params = {
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'frequency': frequency
            }
            
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/historical',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch historical data for {symbol}")
                return None
            
            # Parse historical data from response
            historical_data = response.get('data', {}).get('historical_data', [])
            
            if not historical_data:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            # Convert to DataFrame
            df = self._convert_to_dataframe(historical_data)
            
            # Create HistoricalData object
            historical = HistoricalData(
                symbol=symbol,
                data=df,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                metadata={
                    'source': 'market_data_service',
                    'fetched_at': datetime.utcnow().isoformat(),
                    'data_points': len(df)
                }
            )
            
            logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
            return historical
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def get_volatility_data(
        self,
        symbols: List[str],
        period_days: int = 30
    ) -> Dict[str, Dict[str, float]]:
        """
        Get volatility data for multiple symbols.
        
        Args:
            symbols: List of symbols to get volatility for
            period_days: Number of days for volatility calculation
            
        Returns:
            Dictionary mapping symbols to volatility metrics
        """
        logger.info(f"Fetching volatility data for {len(symbols)} symbols")
        
        try:
            # Build request parameters
            params = {
                'symbols': ','.join(symbols),
                'period_days': period_days
            }
            
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/volatility',
                params=params
            )
            
            if not response:
                logger.error("Failed to fetch volatility data")
                return {}
            
            # Parse volatility data from response
            volatility_data = response.get('data', {}).get('volatility', {})
            
            logger.info(f"Successfully fetched volatility data for {len(volatility_data)} symbols")
            return volatility_data
            
        except Exception as e:
            logger.error(f"Error fetching volatility data: {str(e)}")
            return {}
    
    @PerformanceUtils.measure_execution_time
    def get_correlation_matrix(
        self,
        symbols: List[str],
        period_days: int = 90,
        frequency: str = '1D'
    ) -> Optional[pd.DataFrame]:
        """
        Get correlation matrix for multiple symbols.
        
        Args:
            symbols: List of symbols to get correlations for
            period_days: Number of days for correlation calculation
            frequency: Data frequency for correlation calculation
            
        Returns:
            Correlation matrix DataFrame or None if failed
        """
        logger.info(f"Fetching correlation matrix for {len(symbols)} symbols")
        
        try:
            # Build request parameters
            params = {
                'symbols': ','.join(symbols),
                'period_days': period_days,
                'frequency': frequency
            }
            
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/correlation',
                params=params
            )
            
            if not response:
                logger.error("Failed to fetch correlation matrix")
                return None
            
            # Parse correlation data from response
            correlation_data = response.get('data', {}).get('correlation_matrix', [])
            
            if not correlation_data:
                logger.warning("No correlation data found")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(correlation_data)
            df.set_index('symbol', inplace=True)
            
            logger.info(f"Successfully fetched correlation matrix for {len(symbols)} symbols")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching correlation matrix: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def get_sector_data(
        self,
        sectors: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get sector data and sector mappings.
        
        Args:
            sectors: List of sectors to get data for (None for all)
            
        Returns:
            Dictionary mapping sectors to sector data
        """
        logger.info("Fetching sector data")
        
        try:
            # Build request parameters
            params = {}
            if sectors:
                params['sectors'] = ','.join(sectors)
            
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/sectors',
                params=params
            )
            
            if not response:
                logger.error("Failed to fetch sector data")
                return {}
            
            # Parse sector data from response
            sector_data = response.get('data', {}).get('sectors', {})
            
            logger.info(f"Successfully fetched sector data for {len(sector_data)} sectors")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error fetching sector data: {str(e)}")
            return {}
    
    @PerformanceUtils.measure_execution_time
    def get_benchmark_data(
        self,
        benchmark: str = 'SPY',
        period_days: int = 252
    ) -> Optional[HistoricalData]:
        """
        Get benchmark data for risk calculations.
        
        Args:
            benchmark: Benchmark symbol (default: SPY)
            period_days: Number of days for benchmark data
            
        Returns:
            HistoricalData object for benchmark or None if failed
        """
        logger.info(f"Fetching benchmark data for {benchmark}")
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get historical data for benchmark
            return self.get_historical_data(
                symbol=benchmark,
                start_date=start_date,
                end_date=end_date,
                frequency='1D'
            )
            
        except Exception as e:
            logger.error(f"Error fetching benchmark data for {benchmark}: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status.
        
        Returns:
            Market status information
        """
        logger.info("Fetching market status")
        
        try:
            # Make request to market data service
            response = self._make_request(
                'GET',
                '/api/market-data/status'
            )
            
            if not response:
                logger.error("Failed to fetch market status")
                return {}
            
            # Parse market status from response
            market_status = response.get('data', {}).get('market_status', {})
            
            logger.info("Successfully fetched market status")
            return market_status
            
        except Exception as e:
            logger.error(f"Error fetching market status: {str(e)}")
            return {}
    
    def _parse_market_data(
        self,
        price_data: Dict[str, Any],
        symbol: str
    ) -> MarketData:
        """Parse market data from service response."""
        try:
            # Extract price information
            price = float(price_data.get('price', 0))
            volume = int(price_data.get('volume', 0))
            bid = float(price_data.get('bid', price))
            ask = float(price_data.get('ask', price))
            high = float(price_data.get('high', price))
            low = float(price_data.get('low', price))
            open_price = float(price_data.get('open', price))
            
            # Parse timestamp
            timestamp_str = price_data.get('timestamp', datetime.utcnow().isoformat())
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
            
            return MarketData(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=timestamp,
                bid=bid,
                ask=ask,
                high=high,
                low=low,
                open_price=open_price,
                metadata=price_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.warning(f"Error parsing market data for {symbol}: {str(e)}")
            raise
    
    def _convert_to_dataframe(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Convert historical data to DataFrame."""
        try:
            # Create DataFrame from historical data
            df = pd.DataFrame(historical_data)
            
            # Convert timestamp column to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Ensure numeric columns are properly typed
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by timestamp
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting historical data to DataFrame: {str(e)}")
            raise
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to market data service with retry logic."""
        url = f"{self.market_data_service_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout_seconds
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} for {endpoint}, attempt {attempt + 1}")
                    if attempt < self.retry_attempts - 1:
                        continue
                else:
                    logger.error(f"HTTP {response.status_code} for {endpoint}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {endpoint}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    continue
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {endpoint}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    continue
            except Exception as e:
                logger.error(f"Unexpected error for {endpoint}: {str(e)}")
                return None
        
        logger.error(f"Failed to make request to {endpoint} after {self.retry_attempts} attempts")
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of market data service integration."""
        try:
            response = self._make_request('GET', '/health')
            
            if response:
                return {
                    'status': 'healthy',
                    'service': 'market_data_service_integration',
                    'market_data_service_status': response.get('status', 'unknown'),
                    'last_check': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'market_data_service_integration',
                    'error': 'Market data service not responding',
                    'last_check': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'market_data_service_integration',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }


# Global market data service integration instance
_market_data_integration = None


def get_market_data_integration() -> MarketDataServiceIntegration:
    """Get global market data service integration instance."""
    global _market_data_integration
    
    if _market_data_integration is None:
        _market_data_integration = MarketDataServiceIntegration()
    
    return _market_data_integration


def initialize_market_data_integration(
    market_data_service_url: str = None
) -> MarketDataServiceIntegration:
    """Initialize market data service integration."""
    global _market_data_integration
    
    _market_data_integration = MarketDataServiceIntegration(
        market_data_service_url=market_data_service_url or "http://market-data-service:80"
    )
    
    logger.info("Market data service integration initialized")
    return _market_data_integration



