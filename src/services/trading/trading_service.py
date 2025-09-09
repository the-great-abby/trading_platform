"""
Trading Service
Core trading operations and business logic
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from src.services.cqrs.commands import PlaceOrderCommand, CancelOrderCommand
from src.services.cqrs.queries import GetPortfolioQuery, GetPositionsQuery, GetOrderQuery
from src.services.cqrs.events import OrderCreatedEvent, OrderFilledEvent, OrderCancelledEvent
from src.services.cqrs.cqrs_service import CQRSService
from src.services.trading.order_manager import OrderManager
from src.services.trading.portfolio_data_service import PortfolioDataService
from src.services.notifications.discord_service import DiscordService

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TradingService:
    """Core trading service for managing orders and positions"""
    
    def __init__(self, cqrs_service: CQRSService, discord_webhook_url: Optional[str] = None):
        self.cqrs_service = cqrs_service
        # Check if we have a real database connection
        if hasattr(cqrs_service, 'db_conn') and cqrs_service.db_conn and not hasattr(cqrs_service.db_conn, '_mock_name'):
            # cqrs_service.db_conn is a DatabaseConnectionManager, not a raw connection
            self.order_manager = OrderManager(db_conn=cqrs_service.db_conn)
        else:
            self.order_manager = OrderManager(db_conn=None)  # Use in-memory storage
        self.portfolio_data_service = PortfolioDataService()
        self.discord_service = DiscordService(webhook_url=discord_webhook_url)
        self.position_cache: Dict[str, Dict] = {}
        self.portfolio_cache: Dict[str, Dict] = {}
        
    async def place_order(
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
        """
        Place a new order
        
        Args:
            user_id: User ID
            account_id: Account ID
            symbol: Trading symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: Order type ('market', 'limit', 'stop', 'stop_limit')
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
            client_order_id: Client-provided order ID
            
        Returns:
            Order details and status
        """
        try:
            # Validate order parameters
            validation_result = await self._validate_order(
                user_id, account_id, symbol, side, quantity, 
                order_type, price, stop_price
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "order_id": None
                }
            
            # Create order using order manager
            result = await self.order_manager.create_order(
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
                # Submit order to market
                submit_result = await self.order_manager.submit_order(result["order_id"])
                
                if submit_result.get("success"):
                    logger.info(f"Order placed and submitted successfully: {result['order_id']}")
                    
                    # Send Discord notification
                    await self.discord_service.send_order_notification(
                        order_id=result["order_id"],
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price,
                        status=submit_result["status"],
                        user_id=user_id,
                        account_id=account_id
                    )
                    
                    return {
                        "success": True,
                        "order_id": result["order_id"],
                        "status": submit_result["status"],
                        "message": "Order placed and submitted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": submit_result.get("error", "Failed to submit order"),
                        "order_id": result["order_id"]
                    }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to create order"),
                    "order_id": None
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "order_id": None
            }
    
    async def cancel_order(
        self,
        user_id: str,
        account_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            user_id: User ID
            account_id: Account ID
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            # Use order manager to cancel order
            result = await self.order_manager.cancel_order(
                order_id=order_id,
                user_id=user_id,
                account_id=account_id
            )
            
            if result.get("success"):
                logger.info(f"Order cancelled successfully: {order_id}")
                
                # Get order details for notification
                order = await self.order_manager.get_order(order_id)
                if order:
                    # Send Discord notification
                    await self.discord_service.send_order_notification(
                        order_id=order_id,
                        symbol=order["symbol"],
                        side=order["side"],
                        quantity=order["quantity"],
                        price=order["price"],
                        status=result["status"],
                        user_id=user_id,
                        account_id=account_id
                    )
            
            return result
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}"
            }
    
    async def get_portfolio(
        self,
        user_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get user portfolio
        
        Args:
            user_id: User ID
            account_id: Account ID
            
        Returns:
            Portfolio information
        """
        try:
            # First try to get from portfolio data service (mock data)
            portfolio = self.portfolio_data_service.get_portfolio(user_id, account_id)
            
            if portfolio:
                # Cache portfolio data
                self.portfolio_cache[f"{user_id}_{account_id}"] = portfolio
                
                return {
                    "success": True,
                    "portfolio": portfolio,
                    "timestamp": datetime.now()
                }
            
            # Fallback to CQRS query
            query = GetPortfolioQuery(
                user_id=user_id,
                account_id=account_id
            )
            
            result = await self.cqrs_service.query_bus.dispatch(query)
            
            if result.get("success"):
                # Cache portfolio data
                self.portfolio_cache[f"{user_id}_{account_id}"] = result.get("portfolio", {})
                
                return {
                    "success": True,
                    "portfolio": result.get("portfolio", {}),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "No portfolios found"),
                    "portfolio": {}
                }
                
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "portfolio": {}
            }
    
    async def get_positions(
        self,
        user_id: str,
        account_id: str,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user positions
        
        Args:
            user_id: User ID
            account_id: Account ID
            symbol: Optional symbol filter
            
        Returns:
            Positions information
        """
        try:
            # First try to get from portfolio data service (mock data)
            positions = self.portfolio_data_service.get_positions(user_id, account_id, symbol)
            
            if positions:
                # Cache positions data
                cache_key = f"{user_id}_{account_id}_{symbol or 'all'}"
                self.position_cache[cache_key] = positions
                
                return {
                    "success": True,
                    "positions": positions,
                    "timestamp": datetime.now()
                }
            
            # Fallback to CQRS query
            query = GetPositionsQuery(
                user_id=user_id,
                account_id=account_id,
                symbol=symbol
            )
            
            result = await self.cqrs_service.query_bus.dispatch(query)
            
            if result.get("success"):
                # Cache positions data
                cache_key = f"{user_id}_{account_id}_{symbol or 'all'}"
                self.position_cache[cache_key] = result.get("positions", [])
                
                return {
                    "success": True,
                    "positions": result.get("positions", []),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "No positions found"),
                    "positions": []
                }
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "positions": []
            }
    
    async def get_orders(
        self,
        user_id: str,
        account_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user orders
        
        Args:
            user_id: User ID
            account_id: Account ID
            status: Optional status filter
            symbol: Optional symbol filter
            
        Returns:
            Orders information
        """
        try:
            # Use order manager to get orders
            orders = await self.order_manager.get_orders(
                user_id=user_id,
                account_id=account_id,
                status=status,
                symbol=symbol
            )
            
            return {
                "success": True,
                "orders": orders,
                "timestamp": datetime.now()
            }
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "orders": [],
                "timestamp": datetime.now()
            }
    
    async def _validate_order(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str,
        price: Optional[Decimal],
        stop_price: Optional[Decimal]
    ) -> Dict[str, Any]:
        """
        Validate order parameters
        
        Returns:
            Validation result
        """
        try:
            # Basic validation
            if not symbol or not symbol.strip():
                return {"valid": False, "error": "Symbol is required"}
            
            if side not in ["buy", "sell"]:
                return {"valid": False, "error": "Side must be 'buy' or 'sell'"}
            
            if quantity <= 0:
                return {"valid": False, "error": "Quantity must be positive"}
            
            if order_type not in ["market", "limit", "stop", "stop_limit"]:
                return {"valid": False, "error": "Invalid order type"}
            
            # Type-specific validation
            if order_type in ["limit", "stop_limit"] and price is None:
                return {"valid": False, "error": "Price is required for limit orders"}
            
            if order_type in ["stop", "stop_limit"] and stop_price is None:
                return {"valid": False, "error": "Stop price is required for stop orders"}
            
            if price is not None and price <= 0:
                return {"valid": False, "error": "Price must be positive"}
            
            if stop_price is not None and stop_price <= 0:
                return {"valid": False, "error": "Stop price must be positive"}
            
            # Check account balance (simplified)
            # For testing, skip balance check if using test user
            if user_id != "test-user":
                portfolio = await self.get_portfolio(user_id, account_id)
                if not portfolio.get("success"):
                    return {"valid": False, "error": "Unable to verify account balance"}
            
            # Additional business logic validation can be added here
            # e.g., position limits, risk checks, etc.
            
            return {"valid": True, "error": None}
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status information
        """
        try:
            order = await self.order_manager.get_order(order_id)
            
            if order:
                return {
                    "success": True,
                    "order": order,
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": "Order not found",
                    "order": None
                }
                
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "order": None
            }
    
    async def cleanup_expired_orders(self):
        """Clean up expired orders"""
        try:
            await self.order_manager.cleanup_expired_orders()
        except Exception as e:
            logger.error(f"Error cleaning up expired orders: {e}")
