"""
Market data provider for real-time and historical data
Supports multiple providers: yfinance, Alpaca, and Public API
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf
import pandas as pd
from loguru import logger

from ..utils.config import Config
from .public_data import PublicDataProvider


class MarketDataProvider:
    """Market data provider using multiple sources"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connected = False
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
        # Initialize provider based on configuration
        if config.data_provider == "public":
            self.provider = PublicDataProvider(config)
        else:
            self.provider = None  # Use yfinance as fallback
        
    async def connect(self):
        """Connect to data sources"""
        try:
            if self.provider:
                await self.provider.connect()
            self.connected = True
            logger.info(f"Market data provider connected using {self.config.data_provider}")
        except Exception as e:
            logger.error(f"Failed to connect to market data: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from data sources"""
        if self.provider:
            await self.provider.disconnect()
        self.connected = False
        logger.info("Market data provider disconnected")
    
    async def get_latest_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get latest market data for symbols"""
        if self.provider:
            # Use configured provider (Public API)
            return await self.provider.get_latest_data(symbols)
        else:
            # Fallback to yfinance
            return await self._get_yfinance_data(symbols)
    
    async def _get_yfinance_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get data using yfinance (fallback)"""
        data = {}
        
        for symbol in symbols:
            try:
                df = await self._fetch_latest_data(symbol)
                if df is not None and not df.empty:
                    data[symbol] = df
                    self.data_cache[symbol] = df
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
        
        return data
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol"""
        if self.provider:
            # Use configured provider
            return await self.provider.get_historical_data(symbol, days)
        else:
            # Fallback to yfinance
            return await self._get_yfinance_historical_data(symbol, days)
    
    async def _get_yfinance_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get historical data using yfinance"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def _fetch_latest_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch latest data for a symbol using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get recent data (last 5 days with 1-minute intervals)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            
            df = ticker.history(start=start_date, end=end_date, interval="1m")
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching latest data for {symbol}: {e}")
            return None
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        try:
            # Simple Moving Averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get cached data for a symbol"""
        return self.data_cache.get(symbol)
    
    def clear_cache(self):
        """Clear the data cache"""
        self.data_cache.clear()
        logger.info("Data cache cleared")
    
    # Proxy methods for Public API specific functionality
    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str = "market") -> Dict:
        """Place an order (Public API only)"""
        if self.provider and hasattr(self.provider, 'place_order'):
            return await self.provider.place_order(symbol, side, quantity, order_type)
        else:
            raise NotImplementedError("Order placement not available with current provider")
    
    async def get_accounts(self) -> List[Dict]:
        """Get accounts (Public API only)"""
        if self.provider and hasattr(self.provider, 'get_accounts'):
            return await self.provider.get_accounts()
        else:
            return []
    
    async def get_account_portfolio(self, account_id: str) -> Dict:
        """Get account portfolio (Public API only)"""
        if self.provider and hasattr(self.provider, 'get_account_portfolio'):
            return await self.provider.get_account_portfolio(account_id)
        else:
            return {} 