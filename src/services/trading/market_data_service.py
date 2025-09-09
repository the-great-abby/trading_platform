"""
Market Data Service
Real-time market data streaming and management
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import websockets
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: Decimal
    volume: int
    timestamp: datetime
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None


class MarketDataService:
    """Service for managing real-time market data"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.data_cache: Dict[str, MarketData] = {}
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Market data providers
        self.polygon_api_key = None
        self.alpha_vantage_api_key = None
        self.iex_api_key = None
        
    async def initialize(self, polygon_api_key: str = None, alpha_vantage_api_key: str = None, iex_api_key: str = None):
        """Initialize the market data service"""
        self.polygon_api_key = polygon_api_key
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.iex_api_key = iex_api_key
        
        self.session = aiohttp.ClientSession()
        self.running = True
        
        logger.info("Market data service initialized")
    
    async def shutdown(self):
        """Shutdown the market data service"""
        self.running = False
        
        # Close all WebSocket connections
        for connection in self.websocket_connections.values():
            await connection.close()
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("Market data service shutdown")
    
    async def subscribe_to_symbol(
        self,
        symbol: str,
        callback: Callable[[MarketData], None]
    ) -> bool:
        """
        Subscribe to real-time data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            callback: Callback function to receive data updates
            
        Returns:
            Success status
        """
        try:
            if symbol not in self.subscribers:
                self.subscribers[symbol] = []
            
            self.subscribers[symbol].append(callback)
            
            # Start streaming if not already running
            if len(self.subscribers[symbol]) == 1:
                await self._start_symbol_streaming(symbol)
            
            logger.info(f"Subscribed to {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {e}")
            return False
    
    async def unsubscribe_from_symbol(
        self,
        symbol: str,
        callback: Callable[[MarketData], None]
    ) -> bool:
        """
        Unsubscribe from real-time data for a symbol
        
        Args:
            symbol: Trading symbol
            callback: Callback function to remove
            
        Returns:
            Success status
        """
        try:
            if symbol in self.subscribers:
                if callback in self.subscribers[symbol]:
                    self.subscribers[symbol].remove(callback)
                
                # Stop streaming if no more subscribers
                if not self.subscribers[symbol]:
                    await self._stop_symbol_streaming(symbol)
                    del self.subscribers[symbol]
            
            logger.info(f"Unsubscribed from {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from {symbol}: {e}")
            return False
    
    async def get_latest_price(self, symbol: str) -> Optional[MarketData]:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Latest market data or None
        """
        return self.data_cache.get(symbol)
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1min"
    ) -> List[MarketData]:
        """
        Get historical market data
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ('1min', '5min', '1hour', '1day')
            
        Returns:
            List of historical market data
        """
        try:
            if self.polygon_api_key:
                return await self._get_polygon_historical_data(symbol, start_date, end_date, interval)
            elif self.alpha_vantage_api_key:
                return await self._get_alpha_vantage_historical_data(symbol, start_date, end_date, interval)
            else:
                logger.warning("No market data provider configured")
                return []
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    async def _start_symbol_streaming(self, symbol: str):
        """Start streaming data for a symbol"""
        try:
            if self.polygon_api_key:
                await self._start_polygon_streaming(symbol)
            else:
                # Fallback to simulated data
                await self._start_simulated_streaming(symbol)
                
        except Exception as e:
            logger.error(f"Error starting streaming for {symbol}: {e}")
    
    async def _stop_symbol_streaming(self, symbol: str):
        """Stop streaming data for a symbol"""
        try:
            if symbol in self.websocket_connections:
                await self.websocket_connections[symbol].close()
                del self.websocket_connections[symbol]
                
        except Exception as e:
            logger.error(f"Error stopping streaming for {symbol}: {e}")
    
    async def _start_polygon_streaming(self, symbol: str):
        """Start Polygon.io WebSocket streaming"""
        try:
            if not self.polygon_api_key:
                logger.warning("Polygon API key not configured")
                return
            
            # Polygon WebSocket URL
            ws_url = f"wss://socket.polygon.io/stocks"
            
            async with websockets.connect(ws_url) as websocket:
                self.websocket_connections[symbol] = websocket
                
                # Authenticate
                auth_message = {
                    "action": "auth",
                    "params": self.polygon_api_key
                }
                await websocket.send(json.dumps(auth_message))
                
                # Subscribe to symbol
                subscribe_message = {
                    "action": "subscribe",
                    "params": f"T.{symbol}"
                }
                await websocket.send(json.dumps(subscribe_message))
                
                # Listen for data
                async for message in websocket:
                    if not self.running:
                        break
                    
                    try:
                        data = json.loads(message)
                        market_data = self._parse_polygon_data(data)
                        if market_data:
                            await self._broadcast_data(symbol, market_data)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Error processing Polygon data: {e}")
                        
        except Exception as e:
            logger.error(f"Error in Polygon streaming for {symbol}: {e}")
    
    async def _start_simulated_streaming(self, symbol: str):
        """Start simulated data streaming for testing"""
        try:
            # Simulate real-time data updates
            base_price = Decimal("150.00")  # Starting price
            
            while self.running and symbol in self.subscribers:
                # Generate random price movement
                import random
                change = Decimal(str(random.uniform(-0.02, 0.02)))  # ±2% change
                new_price = base_price * (1 + change)
                base_price = new_price
                
                # Create market data
                market_data = MarketData(
                    symbol=symbol,
                    price=new_price,
                    volume=random.randint(1000, 10000),
                    timestamp=datetime.now(),
                    bid=new_price - Decimal("0.01"),
                    ask=new_price + Decimal("0.01"),
                    high=new_price * Decimal("1.01"),
                    low=new_price * Decimal("0.99"),
                    open=base_price,
                    change=change,
                    change_percent=change * 100
                )
                
                await self._broadcast_data(symbol, market_data)
                
                # Wait before next update
                await asyncio.sleep(1)  # 1 second updates
                
        except Exception as e:
            logger.error(f"Error in simulated streaming for {symbol}: {e}")
    
    async def _broadcast_data(self, symbol: str, market_data: MarketData):
        """Broadcast market data to all subscribers"""
        try:
            # Update cache
            self.data_cache[symbol] = market_data
            
            # Notify all subscribers
            if symbol in self.subscribers:
                for callback in self.subscribers[symbol]:
                    try:
                        await callback(market_data)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback for {symbol}: {e}")
                        
        except Exception as e:
            logger.error(f"Error broadcasting data for {symbol}: {e}")
    
    def _parse_polygon_data(self, data: Dict) -> Optional[MarketData]:
        """Parse Polygon.io WebSocket data"""
        try:
            if data.get("ev") == "T":  # Trade data
                return MarketData(
                    symbol=data.get("sym", ""),
                    price=Decimal(str(data.get("p", 0))),
                    volume=data.get("s", 0),
                    timestamp=datetime.fromtimestamp(data.get("t", 0) / 1000),
                    bid=Decimal(str(data.get("bp", 0))) if data.get("bp") else None,
                    ask=Decimal(str(data.get("ap", 0))) if data.get("ap") else None
                )
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Polygon data: {e}")
            return None
    
    async def _get_polygon_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[MarketData]:
        """Get historical data from Polygon.io"""
        try:
            if not self.session:
                return []
            
            # Convert interval to Polygon format
            interval_map = {
                "1min": "1",
                "5min": "5",
                "1hour": "60",
                "1day": "day"
            }
            
            polygon_interval = interval_map.get(interval, "1")
            
            # Format dates
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{polygon_interval}/minute/{start_str}/{end_str}"
            params = {"apikey": self.polygon_api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_polygon_historical_data(data)
                else:
                    logger.error(f"Polygon API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting Polygon historical data: {e}")
            return []
    
    def _parse_polygon_historical_data(self, data: Dict) -> List[MarketData]:
        """Parse Polygon.io historical data response"""
        try:
            results = data.get("results", [])
            market_data_list = []
            
            for item in results:
                market_data = MarketData(
                    symbol=data.get("ticker", ""),
                    price=Decimal(str(item.get("c", 0))),
                    volume=item.get("v", 0),
                    timestamp=datetime.fromtimestamp(item.get("t", 0) / 1000),
                    high=Decimal(str(item.get("h", 0))),
                    low=Decimal(str(item.get("l", 0))),
                    open=Decimal(str(item.get("o", 0)))
                )
                market_data_list.append(market_data)
            
            return market_data_list
            
        except Exception as e:
            logger.error(f"Error parsing Polygon historical data: {e}")
            return []
    
    async def _get_alpha_vantage_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[MarketData]:
        """Get historical data from Alpha Vantage"""
        try:
            if not self.session or not self.alpha_vantage_api_key:
                return []
            
            # Alpha Vantage API call
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "apikey": self.alpha_vantage_api_key,
                "outputsize": "full"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_alpha_vantage_historical_data(data)
                else:
                    logger.error(f"Alpha Vantage API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting Alpha Vantage historical data: {e}")
            return []
    
    def _parse_alpha_vantage_historical_data(self, data: Dict) -> List[MarketData]:
        """Parse Alpha Vantage historical data response"""
        try:
            time_series = data.get("Time Series (1min)", {})
            market_data_list = []
            
            for timestamp_str, values in time_series.items():
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                market_data = MarketData(
                    symbol=data.get("Meta Data", {}).get("2. Symbol", ""),
                    price=Decimal(str(values.get("4. close", 0))),
                    volume=int(values.get("5. volume", 0)),
                    timestamp=timestamp,
                    high=Decimal(str(values.get("2. high", 0))),
                    low=Decimal(str(values.get("3. low", 0))),
                    open=Decimal(str(values.get("1. open", 0)))
                )
                market_data_list.append(market_data)
            
            return sorted(market_data_list, key=lambda x: x.timestamp)
            
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage historical data: {e}")
            return []
