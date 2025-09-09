"""
WebSocket support for real-time events
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, event_types: List[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket] = event_types
            logger.info(f"WebSocket subscribed to: {event_types}")
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all subscribed connections"""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to all subscribed connections
        for websocket in self.active_connections:
            if websocket in self.subscriptions:
                subscribed_types = self.subscriptions[websocket]
                if not subscribed_types or event_type in subscribed_types:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error sending to WebSocket: {e}")
                        self.disconnect(websocket)

# Global connection manager
manager = ConnectionManager()

# Create router
from fastapi import APIRouter
websocket_router = APIRouter()

@websocket_router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket, event_types: str = None):
    """WebSocket endpoint for real-time events"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                # Handle subscription
                event_types_list = message.get("event_types", [])
                manager.subscribe(websocket, event_types_list)
                
                # Send confirmation
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "event_types": event_types_list
                }))
            
            elif message.get("type") == "ping":
                # Handle ping
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                }))
            
            else:
                # Unknown message type
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Unknown message type"
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Function to broadcast events (can be called from other parts of the application)
async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast event to all WebSocket connections"""
    await manager.broadcast_event(event_type, data)
