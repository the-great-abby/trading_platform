"""
Trading Integration Service
Integrates trading operations with real-time updates and WebSocket notifications
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from src.services.trading.trading_service import TradingService
from src.services.trading.market_data_service import MarketDataService
from src.api.routes.websocket_routes import (
    send_order_update_to_user,
    send_position_update_to_user,
    send_portfolio_update_to_user
)

logger = logging.getLogger(__name__)


class TradingIntegrationService:
    """Service that integrates trading operations with real-time updates"""
    
    def __init__(self, trading_service: TradingService, market_data_service: MarketDataService):
        self.trading_service = trading_service
        self.market_data_service = market_data_service
        self.running = False
        self.update_tasks: Dict[str, asyncio.Task] = {}
    
    async def start(self):
        """Start the integration service"""
        self.running = True
        
        # Start cleanup task for expired orders
        asyncio.create_task(self._cleanup_expired_orders_loop())
        
        logger.info("Trading integration service started")
    
    async def stop(self):
        """Stop the integration service"""
        self.running = False
        
        # Cancel all update tasks
        for task in self.update_tasks.values():
            task.cancel()
        
        self.update_tasks.clear()
        
        logger.info("Trading integration service stopped")
    
    async def place_order_with_updates(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC",
        client_order_id: str = None
    ) -> Dict[str, Any]:
        """
        Place an order with real-time updates
        
        Returns:
            Order placement result with real-time update setup
        """
        try:
            # Place the order
            result = await self.trading_service.place_order(
                user_id=user_id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
                client_order_id=client_order_id
            )
            
            if result.get("success"):
                order_id = result.get("order_id")
                
                # Set up real-time updates for this order
                await self._setup_order_updates(user_id, order_id, symbol)
                
                # Send initial order update
                await send_order_update_to_user(user_id, {
                    "order_id": order_id,
                    "status": "placed",
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "order_type": order_type,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Order {order_id} placed with real-time updates for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing order with updates: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "order_id": None
            }
    
    async def cancel_order_with_updates(
        self,
        user_id: str,
        account_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Cancel an order with real-time updates
        
        Returns:
            Order cancellation result with real-time update
        """
        try:
            # Cancel the order
            result = await self.trading_service.cancel_order(
                user_id=user_id,
                account_id=account_id,
                order_id=order_id
            )
            
            if result.get("success"):
                # Send order update
                await send_order_update_to_user(user_id, {
                    "order_id": order_id,
                    "status": "cancelled",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Clean up order updates
                await self._cleanup_order_updates(user_id, order_id)
                
                logger.info(f"Order {order_id} cancelled with real-time update for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error cancelling order with updates: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}"
            }
    
    async def get_portfolio_with_updates(
        self,
        user_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get portfolio with real-time updates setup
        
        Returns:
            Portfolio data with real-time update setup
        """
        try:
            # Get portfolio data
            result = await self.trading_service.get_portfolio(
                user_id=user_id,
                account_id=account_id
            )
            
            if result.get("success"):
                # Set up portfolio updates
                await self._setup_portfolio_updates(user_id, account_id)
                
                # Send initial portfolio update
                await send_portfolio_update_to_user(user_id, {
                    "portfolio": result.get("portfolio", {}),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Portfolio updates set up for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting portfolio with updates: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "portfolio": {}
            }
    
    async def get_positions_with_updates(
        self,
        user_id: str,
        account_id: str,
        symbol: str = None
    ) -> Dict[str, Any]:
        """
        Get positions with real-time updates setup
        
        Returns:
            Positions data with real-time update setup
        """
        try:
            # Get positions data
            result = await self.trading_service.get_positions(
                user_id=user_id,
                account_id=account_id,
                symbol=symbol
            )
            
            if result.get("success"):
                # Set up position updates for each symbol
                positions = result.get("positions", [])
                for position in positions:
                    position_symbol = position.get("symbol")
                    if position_symbol:
                        await self._setup_position_updates(user_id, account_id, position_symbol)
                
                # Send initial positions update
                await send_position_update_to_user(user_id, {
                    "positions": positions,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Position updates set up for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions with updates: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "positions": []
            }
    
    async def _setup_order_updates(self, user_id: str, order_id: str, symbol: str):
        """Set up real-time updates for an order"""
        try:
            # Subscribe to market data for the symbol
            await self.market_data_service.subscribe_to_symbol(
                symbol,
                lambda data: self._handle_market_data_for_order(user_id, order_id, symbol, data)
            )
            
            # Set up periodic order status checks
            task = asyncio.create_task(self._monitor_order_status(user_id, order_id))
            self.update_tasks[f"order_{user_id}_{order_id}"] = task
            
        except Exception as e:
            logger.error(f"Error setting up order updates for {order_id}: {e}")
    
    async def _cleanup_order_updates(self, user_id: str, order_id: str):
        """Clean up real-time updates for an order"""
        try:
            # Cancel monitoring task
            task_key = f"order_{user_id}_{order_id}"
            if task_key in self.update_tasks:
                self.update_tasks[task_key].cancel()
                del self.update_tasks[task_key]
            
        except Exception as e:
            logger.error(f"Error cleaning up order updates for {order_id}: {e}")
    
    async def _setup_portfolio_updates(self, user_id: str, account_id: str):
        """Set up real-time updates for portfolio"""
        try:
            # Set up periodic portfolio updates
            task = asyncio.create_task(self._monitor_portfolio(user_id, account_id))
            self.update_tasks[f"portfolio_{user_id}"] = task
            
        except Exception as e:
            logger.error(f"Error setting up portfolio updates for user {user_id}: {e}")
    
    async def _setup_position_updates(self, user_id: str, account_id: str, symbol: str):
        """Set up real-time updates for positions"""
        try:
            # Subscribe to market data for the symbol
            await self.market_data_service.subscribe_to_symbol(
                symbol,
                lambda data: self._handle_market_data_for_position(user_id, account_id, symbol, data)
            )
            
        except Exception as e:
            logger.error(f"Error setting up position updates for {symbol}: {e}")
    
    async def _handle_market_data_for_order(self, user_id: str, order_id: str, symbol: str, market_data):
        """Handle market data updates for order monitoring"""
        try:
            # Check if order should be filled based on market data
            order_status = await self.trading_service.get_order_status(order_id)
            
            if order_status.get("success"):
                order = order_status.get("order", {})
                order_type = order.get("order_type")
                side = order.get("side")
                price = order.get("price")
                stop_price = order.get("stop_price")
                
                # Simple order fill logic (in production, this would be more sophisticated)
                should_fill = False
                
                if order_type == "market":
                    should_fill = True
                elif order_type == "limit":
                    if side == "buy" and market_data.price <= price:
                        should_fill = True
                    elif side == "sell" and market_data.price >= price:
                        should_fill = True
                elif order_type == "stop":
                    if side == "buy" and market_data.price >= stop_price:
                        should_fill = True
                    elif side == "sell" and market_data.price <= stop_price:
                        should_fill = True
                
                if should_fill and order.get("status") == "pending":
                    # Simulate order fill
                    await self._simulate_order_fill(user_id, order_id, market_data)
            
        except Exception as e:
            logger.error(f"Error handling market data for order {order_id}: {e}")
    
    async def _handle_market_data_for_position(self, user_id: str, account_id: str, symbol: str, market_data):
        """Handle market data updates for position monitoring"""
        try:
            # Get current positions
            positions_result = await self.trading_service.get_positions(
                user_id=user_id,
                account_id=account_id,
                symbol=symbol
            )
            
            if positions_result.get("success"):
                positions = positions_result.get("positions", [])
                
                # Send position update with current market data
                await send_position_update_to_user(user_id, {
                    "symbol": symbol,
                    "current_price": float(market_data.price),
                    "positions": positions,
                    "timestamp": datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error handling market data for position {symbol}: {e}")
    
    async def _monitor_order_status(self, user_id: str, order_id: str):
        """Monitor order status and send updates"""
        try:
            while self.running:
                order_status = await self.trading_service.get_order_status(order_id)
                
                if order_status.get("success"):
                    order = order_status.get("order", {})
                    
                    # Send order update
                    await send_order_update_to_user(user_id, {
                        "order_id": order_id,
                        "status": order.get("status"),
                        "symbol": order.get("symbol"),
                        "side": order.get("side"),
                        "quantity": order.get("quantity"),
                        "filled_quantity": order.get("filled_quantity", 0),
                        "remaining_quantity": order.get("remaining_quantity", order.get("quantity")),
                        "price": order.get("price"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Stop monitoring if order is complete
                    if order.get("status") in ["filled", "cancelled", "rejected", "expired"]:
                        break
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring order {order_id}: {e}")
    
    async def _monitor_portfolio(self, user_id: str, account_id: str):
        """Monitor portfolio and send updates"""
        try:
            while self.running:
                portfolio_result = await self.trading_service.get_portfolio(
                    user_id=user_id,
                    account_id=account_id
                )
                
                if portfolio_result.get("success"):
                    # Send portfolio update
                    await send_portfolio_update_to_user(user_id, {
                        "portfolio": portfolio_result.get("portfolio", {}),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring portfolio for user {user_id}: {e}")
    
    async def _simulate_order_fill(self, user_id: str, order_id: str, market_data):
        """Simulate order fill (in production, this would integrate with actual broker)"""
        try:
            # This is a simplified simulation
            # In production, this would integrate with actual broker APIs
            
            # Update order status to filled
            order_status = await self.trading_service.get_order_status(order_id)
            if order_status.get("success"):
                order = order_status.get("order", {})
                
                # Send fill notification
                await send_order_update_to_user(user_id, {
                    "order_id": order_id,
                    "status": "filled",
                    "symbol": order.get("symbol"),
                    "side": order.get("side"),
                    "quantity": order.get("quantity"),
                    "fill_price": float(market_data.price),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Order {order_id} simulated as filled at {market_data.price}")
            
        except Exception as e:
            logger.error(f"Error simulating order fill for {order_id}: {e}")
    
    async def _cleanup_expired_orders_loop(self):
        """Periodic cleanup of expired orders"""
        try:
            while self.running:
                await self.trading_service.cleanup_expired_orders()
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in expired orders cleanup: {e}")
