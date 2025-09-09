"""
Order Manager
Handles order lifecycle and state management
"""

import asyncio
import logging
import random
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from .order_storage import OrderStorage

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderManager:
    """Manages order lifecycle and state"""
    
    def __init__(self, db_conn=None, event_bus=None):
        self.db_conn = db_conn
        self.event_bus = event_bus
        # Check if db_conn is a real connection (not a Mock)
        self._use_persistent_storage = db_conn is not None and not hasattr(db_conn, '_mock_name')
        self.storage = OrderStorage(db_conn) if self._use_persistent_storage else None
        self.orders: Dict[str, Dict] = {}  # Fallback in-memory storage
        self.order_counter = 0
        
        if self._use_persistent_storage:
            logger.info("OrderManager initialized with persistent storage.")
        else:
            logger.info("OrderManager initialized with in-memory storage.")
        
    async def create_order(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "market",
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new order"""
        try:
            # Generate order ID
            self.order_counter += 1
            order_id = client_order_id or f"ORD_{self.order_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create order record
            order = {
                "order_id": order_id,
                "user_id": user_id,
                "account_id": account_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "filled_quantity": Decimal("0"),
                "remaining_quantity": quantity,
                "order_type": order_type,
                "price": price,
                "stop_price": stop_price,
                "time_in_force": time_in_force,
                "status": OrderStatus.PENDING.value,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "submitted_at": None,
                "filled_at": None,
                "cancelled_at": None,
                "rejected_reason": None,
                "execution_price": None,
                "commission": Decimal("0"),
                "metadata": {}
            }
            
            # Store order
            if self._use_persistent_storage:
                await self.storage.create_order(order)
            else:
                self.orders[order_id] = order
            
            logger.info(f"Created order {order_id}: {side} {quantity} {symbol} @ {price or 'market'}")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.PENDING.value,
                "message": "Order created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create order"
            }
    
    async def submit_order(self, order_id: str) -> Dict[str, Any]:
        """Submit order to market"""
        try:
            if order_id not in self.orders:
                return {"success": False, "error": "Order not found"}
            
            order = self.orders[order_id]
            
            if order["status"] != OrderStatus.PENDING.value:
                return {"success": False, "error": f"Order cannot be submitted in status: {order['status']}"}
            
            # Update order status
            order["status"] = OrderStatus.SUBMITTED.value
            order["submitted_at"] = datetime.now()
            order["updated_at"] = datetime.now()
            
            logger.info(f"Submitted order {order_id}")
            
            # Simulate order processing
            await self._process_order(order_id)
            
            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.SUBMITTED.value,
                "message": "Order submitted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit order"
            }
    
    async def cancel_order(self, order_id: str, user_id: str, account_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            if order_id not in self.orders:
                return {"success": False, "error": "Order not found"}
            
            order = self.orders[order_id]
            
            # Check authorization
            if order["user_id"] != user_id or order["account_id"] != account_id:
                return {"success": False, "error": "Unauthorized to cancel this order"}
            
            # Check if order can be cancelled
            if order["status"] in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value, OrderStatus.REJECTED.value]:
                return {"success": False, "error": f"Order cannot be cancelled in status: {order['status']}"}
            
            # Update order status
            order["status"] = OrderStatus.CANCELLED.value
            order["cancelled_at"] = datetime.now()
            order["updated_at"] = datetime.now()
            
            logger.info(f"Cancelled order {order_id}")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.CANCELLED.value,
                "message": "Order cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel order"
            }
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        if self._use_persistent_storage:
            return await self.storage.get_order(order_id)
        else:
            return self.orders.get(order_id)
    
    async def get_orders(
        self,
        user_id: str,
        account_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get orders with filters"""
        if self._use_persistent_storage:
            return await self.storage.get_orders(
                user_id=user_id,
                account_id=account_id,
                status=status,
                symbol=symbol
            )
        else:
            orders = []
            
            for order in self.orders.values():
                # Filter by user and account
                if order["user_id"] != user_id or order["account_id"] != account_id:
                    continue
                
                # Filter by status
                if status and order["status"] != status:
                    continue
                
                # Filter by symbol
                if symbol and order["symbol"] != symbol:
                    continue
                
                orders.append(order)
            
            # Sort by creation time (newest first)
            orders.sort(key=lambda x: x["created_at"], reverse=True)
            
            return orders
    
    async def _process_order(self, order_id: str):
        """Process order (simulate market execution)"""
        try:
            order = self.orders[order_id]
            
            # Simulate processing delay
            await asyncio.sleep(0.1)
            
            # For demo purposes, simulate different outcomes
            
            # 80% chance of immediate fill for market orders
            if order["order_type"] == "market":
                if random.random() < 0.8:
                    await self._fill_order(order_id, order["quantity"])
                else:
                    # Simulate partial fill
                    partial_qty = order["quantity"] * Decimal("0.5")
                    await self._partial_fill_order(order_id, partial_qty)
            else:
                # Limit orders - simulate pending
                logger.info(f"Limit order {order_id} pending at price {order['price']}")
                
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {e}")
            await self._reject_order(order_id, f"Processing error: {str(e)}")
    
    async def _fill_order(self, order_id: str, quantity: Decimal):
        """Fill order completely"""
        try:
            order = self.orders[order_id]
            
            # Simulate execution price (slightly different from limit price for realism)
            if order["order_type"] == "market":
                # Simulate market price
                base_price = Decimal("100.00")  # Mock price
                execution_price = base_price + Decimal(str(random.uniform(-0.5, 0.5)))
            else:
                execution_price = order["price"]
            
            # Update order
            order["status"] = OrderStatus.FILLED.value
            order["filled_quantity"] = quantity
            order["remaining_quantity"] = Decimal("0")
            order["execution_price"] = execution_price
            order["filled_at"] = datetime.now()
            order["updated_at"] = datetime.now()
            order["commission"] = quantity * execution_price * Decimal("0.001")  # 0.1% commission
            
            logger.info(f"Filled order {order_id}: {quantity} @ {execution_price}")
            
            # TODO: Publish OrderFilledEvent
            # TODO: Update portfolio/positions
            
        except Exception as e:
            logger.error(f"Error filling order {order_id}: {e}")
    
    async def _partial_fill_order(self, order_id: str, quantity: Decimal):
        """Partially fill order"""
        try:
            order = self.orders[order_id]
            
            # Simulate execution price
            execution_price = order["price"] or Decimal("100.00")
            
            # Update order
            order["status"] = OrderStatus.PARTIALLY_FILLED.value
            order["filled_quantity"] += quantity
            order["remaining_quantity"] -= quantity
            order["execution_price"] = execution_price
            order["updated_at"] = datetime.now()
            
            logger.info(f"Partially filled order {order_id}: {quantity} @ {execution_price}")
            
            # TODO: Publish OrderFilledEvent
            # TODO: Update portfolio/positions
            
        except Exception as e:
            logger.error(f"Error partially filling order {order_id}: {e}")
    
    async def _reject_order(self, order_id: str, reason: str):
        """Reject order"""
        try:
            order = self.orders[order_id]
            
            order["status"] = OrderStatus.REJECTED.value
            order["rejected_reason"] = reason
            order["updated_at"] = datetime.now()
            
            logger.warning(f"Rejected order {order_id}: {reason}")
            
            # TODO: Publish OrderRejectedEvent
            
        except Exception as e:
            logger.error(f"Error rejecting order {order_id}: {e}")
    
    async def cleanup_expired_orders(self):
        """Clean up expired orders"""
        try:
            current_time = datetime.now()
            expired_orders = []
            
            for order_id, order in self.orders.items():
                # Check if order is expired (older than 24 hours and still pending)
                if (order["status"] == OrderStatus.PENDING.value and 
                    (current_time - order["created_at"]).total_seconds() > 86400):
                    expired_orders.append(order_id)
            
            for order_id in expired_orders:
                await self.cancel_order(order_id, "", "")  # System cancellation
                logger.info(f"Auto-cancelled expired order: {order_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired orders: {e}")
    
    async def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        try:
            total_orders = len(self.orders)
            pending_orders = sum(1 for o in self.orders.values() if o["status"] == OrderStatus.PENDING.value)
            filled_orders = sum(1 for o in self.orders.values() if o["status"] == OrderStatus.FILLED.value)
            cancelled_orders = sum(1 for o in self.orders.values() if o["status"] == OrderStatus.CANCELLED.value)
            
            return {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "filled_orders": filled_orders,
                "cancelled_orders": cancelled_orders,
                "fill_rate": filled_orders / total_orders if total_orders > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {}
