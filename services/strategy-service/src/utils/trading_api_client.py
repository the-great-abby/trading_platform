"""
Trading API Client for External Systems
Provides a clean interface to interact with the Space Trading Station API Gateway
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class TimeInterval(Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"

@dataclass
class TradingOrder:
    """Trading order model"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    stop_price: Optional[float] = None
    strategy: Optional[str] = None
    time_in_force: str = "day"
    client_order_id: Optional[str] = None

@dataclass
class MarketDataRequest:
    """Market data request model"""
    symbols: List[str]
    interval: TimeInterval = TimeInterval.DAY_1
    period: str = "1y"
    include_indicators: bool = True

@dataclass
class BacktestRequest:
    """Backtest request model"""
    strategy: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000
    commission: float = 0.001
    slippage: float = 0.001

class TradingAPIClient:
    """
    Comprehensive API client for the Space Trading Station
    
    This client provides a clean interface for external systems to interact
    with all trading system functionality through the centralized API gateway.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}" if api_key else "",
                "Content-Type": "application/json",
                "User-Agent": "SpaceTradingStation-Client/1.0.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await self.client.put(url, json=data)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 500, 502, 503, 504] and attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error: {e}")
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed: {e}")
                    raise
    
    # Health and Status
    async def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        return await self._make_request("GET", "/health")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and information"""
        return await self._make_request("GET", "/")
    
    # Trading Operations
    async def create_order(self, order: TradingOrder) -> Dict[str, Any]:
        """Create a new trading order"""
        order_data = asdict(order)
        order_data['side'] = order.side.value
        order_data['order_type'] = order.order_type.value
        
        return await self._make_request("POST", "/api/v1/trading/orders", data=order_data)
    
    async def get_orders(self, status: Optional[str] = None, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get user's trading orders"""
        params = {}
        if status:
            params['status'] = status
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request("GET", "/api/v1/trading/orders", params=params)
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a trading order"""
        return await self._make_request("DELETE", f"/api/v1/trading/orders/{order_id}")
    
    # Market Data
    async def get_market_quotes(self, request: MarketDataRequest) -> Dict[str, Any]:
        """Get market data quotes"""
        data = asdict(request)
        data['interval'] = request.interval.value
        
        return await self._make_request("POST", "/api/v1/market-data/quotes", data=data)
    
    async def get_real_time_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time market quotes"""
        request = MarketDataRequest(symbols=symbols, interval=TimeInterval.MINUTE_1)
        return await self.get_market_quotes(request)
    
    # Portfolio Management
    async def get_portfolio(
        self,
        account_id: Optional[str] = None,
        include_positions: bool = True,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """Get user portfolio"""
        params = {
            'include_positions': include_positions,
            'include_history': include_history
        }
        if account_id:
            params['account_id'] = account_id
        
        return await self._make_request("GET", "/api/v1/portfolio", params=params)
    
    async def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get current positions"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request("GET", "/api/v1/portfolio/positions", params=params)
    
    # Strategy Management
    async def get_strategies(self) -> Dict[str, Any]:
        """Get available trading strategies"""
        return await self._make_request("GET", "/api/v1/strategies")
    
    async def get_strategy_recommendations(
        self,
        symbol: str,
        strategies: Optional[List[str]] = None,
        include_ai_analysis: bool = True,
        include_news_sentiment: bool = True
    ) -> Dict[str, Any]:
        """Get strategy recommendations for a symbol"""
        data = {
            "symbol": symbol,
            "include_ai_analysis": include_ai_analysis,
            "include_news_sentiment": include_news_sentiment
        }
        if strategies:
            data["strategies"] = strategies
        
        return await self._make_request("POST", "/api/v1/strategies/recommendations", data=data)
    
    # Backtesting
    async def run_backtest(self, request: BacktestRequest) -> Dict[str, Any]:
        """Run a backtest"""
        return await self._make_request("POST", "/api/v1/backtest/run", data=asdict(request))
    
    async def get_backtest_results(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get backtest results"""
        if run_id:
            return await self._make_request("GET", f"/api/v1/backtest/results/{run_id}")
        else:
            return await self._make_request("GET", "/api/v1/backtest/results")
    
    async def compare_strategies(
        self,
        strategies: List[str],
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        """Compare multiple strategies"""
        data = {
            "strategies": strategies,
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital
        }
        return await self._make_request("POST", "/api/v1/backtest/compare", data=data)
    
    # Analytics
    async def get_performance_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get performance analytics"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if metrics:
            params['metrics'] = ','.join(metrics)
        
        return await self._make_request("GET", "/api/v1/analytics/performance", params=params)
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk management metrics"""
        return await self._make_request("GET", "/api/v1/risk/positions")
    
    # User Management
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return await self._make_request("GET", "/api/v1/users/profile")
    
    async def update_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        return await self._make_request("PUT", "/api/v1/users/profile", data=profile_data)
    
    # WebSocket Support
    async def subscribe_to_market_data(
        self,
        symbols: List[str],
        callback: callable
    ):
        """Subscribe to real-time market data via WebSocket"""
        import websockets
        
        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/market-data"
        
        async with websockets.connect(ws_url) as websocket:
            # Send subscription message
            subscription = {
                "action": "subscribe",
                "symbols": symbols
            }
            await websocket.send(json.dumps(subscription))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await callback(data)
    
    # Utility Methods
    async def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols"""
        response = await self.get_market_quotes(
            MarketDataRequest(symbols=[], interval=TimeInterval.DAY_1)
        )
        return response.get('data', {}).get('available_symbols', [])
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        portfolio = await self.get_portfolio()
        return portfolio.get('data', {}).get('balance', {})
    
    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get open orders"""
        orders = await self.get_orders(status="open")
        return orders.get('data', {}).get('orders', [])

# Synchronous wrapper for convenience
class TradingAPIClientSync:
    """Synchronous wrapper for the Trading API Client"""
    
    def __init__(self, *args, **kwargs):
        self.client = TradingAPIClient(*args, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def health_check(self) -> Dict[str, Any]:
        return self._run_async(self.client.health_check())
    
    def create_order(self, order: TradingOrder) -> Dict[str, Any]:
        return self._run_async(self.client.create_order(order))
    
    def get_market_quotes(self, request: MarketDataRequest) -> Dict[str, Any]:
        return self._run_async(self.client.get_market_quotes(request))
    
    def get_portfolio(self, **kwargs) -> Dict[str, Any]:
        return self._run_async(self.client.get_portfolio(**kwargs))
    
    def get_strategy_recommendations(self, **kwargs) -> Dict[str, Any]:
        return self._run_async(self.client.get_strategy_recommendations(**kwargs))
    
    def run_backtest(self, request: BacktestRequest) -> Dict[str, Any]:
        return self._run_async(self.client.run_backtest(request))

# Example usage
async def example_usage():
    """Example usage of the Trading API Client"""
    
    # Initialize client
    async with TradingAPIClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    ) as client:
        
        # Check system health
        health = await client.health_check()
        print(f"System health: {health['status']}")
        
        # Get market data
        market_request = MarketDataRequest(
            symbols=["AAPL", "MSFT", "GOOGL"],
            interval=TimeInterval.DAY_1,
            period="1m"
        )
        quotes = await client.get_market_quotes(market_request)
        print(f"Market data: {quotes}")
        
        # Create a trading order
        order = TradingOrder(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        order_result = await client.create_order(order)
        print(f"Order created: {order_result}")
        
        # Get strategy recommendations
        recommendations = await client.get_strategy_recommendations("AAPL")
        print(f"Recommendations: {recommendations}")
        
        # Run a backtest
        backtest_request = BacktestRequest(
            strategy="rsi_strategy",
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000
        )
        backtest_result = await client.run_backtest(backtest_request)
        print(f"Backtest result: {backtest_result}")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage()) 