"""
WebSocket Routes
Real-time data streaming endpoints
"""

import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from src.services.trading.market_data_service import MarketDataService, MarketData
from src.api.middleware.auth_middleware import get_current_user_websocket

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of symbols
        self.symbol_subscribers: Dict[str, Set[str]] = {}  # symbol -> set of user_ids
        self.market_data_service: MarketDataService = None
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.user_subscriptions:
            # Unsubscribe from all symbols
            for symbol in self.user_subscriptions[user_id]:
                if symbol in self.symbol_subscribers:
                    self.symbol_subscribers[symbol].discard(user_id)
                    if not self.symbol_subscribers[symbol]:
                        del self.symbol_subscribers[symbol]
            
            del self.user_subscriptions[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    self.disconnect(user_id)
    
    async def subscribe_to_symbol(self, user_id: str, symbol: str):
        """Subscribe a user to a symbol"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(symbol)
        
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
        
        self.symbol_subscribers[symbol].add(user_id)
        
        # Subscribe to market data service if available
        if self.market_data_service:
            await self.market_data_service.subscribe_to_symbol(
                symbol, 
                lambda data: self._broadcast_market_data(symbol, data)
            )
        
        logger.info(f"User {user_id} subscribed to {symbol}")
    
    async def unsubscribe_from_symbol(self, user_id: str, symbol: str):
        """Unsubscribe a user from a symbol"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(symbol)
        
        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(user_id)
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]
        
        logger.info(f"User {user_id} unsubscribed from {symbol}")
    
    async def _broadcast_market_data(self, symbol: str, market_data: MarketData):
        """Broadcast market data to all subscribers of a symbol"""
        if symbol in self.symbol_subscribers:
            message = {
                "type": "market_data",
                "symbol": symbol,
                "data": {
                    "price": float(market_data.price),
                    "volume": market_data.volume,
                    "timestamp": market_data.timestamp.isoformat(),
                    "bid": float(market_data.bid) if market_data.bid else None,
                    "ask": float(market_data.ask) if market_data.ask else None,
                    "high": float(market_data.high) if market_data.high else None,
                    "low": float(market_data.low) if market_data.low else None,
                    "open": float(market_data.open) if market_data.open else None,
                    "change": float(market_data.change) if market_data.change else None,
                    "change_percent": float(market_data.change_percent) if market_data.change_percent else None
                }
            }
            
            message_str = json.dumps(message)
            
            # Send to all subscribers
            for user_id in list(self.symbol_subscribers[symbol]):
                await self.send_personal_message(message_str, user_id)
    
    async def send_order_update(self, user_id: str, order_data: dict):
        """Send order update to a user"""
        message = {
            "type": "order_update",
            "data": order_data
        }
        
        message_str = json.dumps(message)
        await self.send_personal_message(message_str, user_id)
    
    async def send_position_update(self, user_id: str, position_data: dict):
        """Send position update to a user"""
        message = {
            "type": "position_update",
            "data": position_data
        }
        
        message_str = json.dumps(message)
        await self.send_personal_message(message_str, user_id)
    
    async def send_portfolio_update(self, user_id: str, portfolio_data: dict):
        """Send portfolio update to a user"""
        message = {
            "type": "portfolio_update",
            "data": portfolio_data
        }
        
        message_str = json.dumps(message)
        await self.send_personal_message(message_str, user_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/trading/{user_id}")
async def websocket_trading_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for real-time trading data
    
    - **user_id**: User ID for the connection
    
    Message types:
    - subscribe: Subscribe to a symbol
    - unsubscribe: Unsubscribe from a symbol
    - ping: Keep-alive ping
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    symbol = message.get("symbol")
                    if symbol:
                        await manager.subscribe_to_symbol(user_id, symbol)
                        
                        # Send confirmation
                        response = {
                            "type": "subscription_confirmed",
                            "symbol": symbol,
                            "status": "subscribed"
                        }
                        await manager.send_personal_message(json.dumps(response), user_id)
                
                elif message_type == "unsubscribe":
                    symbol = message.get("symbol")
                    if symbol:
                        await manager.unsubscribe_from_symbol(user_id, symbol)
                        
                        # Send confirmation
                        response = {
                            "type": "unsubscription_confirmed",
                            "symbol": symbol,
                            "status": "unsubscribed"
                        }
                        await manager.send_personal_message(json.dumps(response), user_id)
                
                elif message_type == "ping":
                    # Respond to ping with pong
                    response = {
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }
                    await manager.send_personal_message(json.dumps(response), user_id)
                
                else:
                    # Unknown message type
                    response = {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }
                    await manager.send_personal_message(json.dumps(response), user_id)
                    
            except json.JSONDecodeError:
                response = {
                    "type": "error",
                    "message": "Invalid JSON message"
                }
                await manager.send_personal_message(json.dumps(response), user_id)
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                response = {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }
                await manager.send_personal_message(json.dumps(response), user_id)
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


@router.websocket("/market-data/{symbol}")
async def websocket_market_data_endpoint(
    websocket: WebSocket,
    symbol: str
):
    """
    WebSocket endpoint for real-time market data for a specific symbol
    
    - **symbol**: Trading symbol to stream data for
    """
    await websocket.accept()
    
    try:
        # Initialize market data service
        market_data_service = MarketDataService()
        await market_data_service.initialize()
        
        # Subscribe to symbol
        await market_data_service.subscribe_to_symbol(
            symbol,
            lambda data: websocket.send_text(json.dumps({
                "type": "market_data",
                "symbol": data.symbol,
                "price": float(data.price),
                "volume": data.volume,
                "timestamp": data.timestamp.isoformat(),
                "bid": float(data.bid) if data.bid else None,
                "ask": float(data.ask) if data.ask else None,
                "high": float(data.high) if data.high else None,
                "low": float(data.low) if data.low else None,
                "open": float(data.open) if data.open else None,
                "change": float(data.change) if data.change else None,
                "change_percent": float(data.change_percent) if data.change_percent else None
            }))
        )
        
        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in market data WebSocket: {e}")
                break
    
    except Exception as e:
        logger.error(f"Error setting up market data WebSocket for {symbol}: {e}")
    
    finally:
        # Cleanup
        if 'market_data_service' in locals():
            await market_data_service.shutdown()


# Helper function to initialize market data service
async def initialize_market_data_service():
    """Initialize the market data service for the connection manager"""
    manager.market_data_service = MarketDataService()
    await manager.market_data_service.initialize()


# Helper function to send order updates
async def send_order_update_to_user(user_id: str, order_data: dict):
    """Send order update to a specific user"""
    await manager.send_order_update(user_id, order_data)


# Helper function to send position updates
async def send_position_update_to_user(user_id: str, position_data: dict):
    """Send position update to a specific user"""
    await manager.send_position_update(user_id, position_data)


# Helper function to send portfolio updates
async def send_portfolio_update_to_user(user_id: str, portfolio_data: dict):
    """Send portfolio update to a specific user"""
    await manager.send_portfolio_update(user_id, portfolio_data)
