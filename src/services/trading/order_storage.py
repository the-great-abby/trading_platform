"""
Persistent Order Storage
Handles database operations for order management
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderStorage:
    """Handles persistent storage of orders in the database"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._initialized = False
    
    async def initialize(self):
        """Initialize the order storage tables"""
        if self._initialized:
            return
        
        try:
            # Create orders table
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    account_id VARCHAR(255) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    filled_quantity DECIMAL(20, 8) DEFAULT 0,
                    remaining_quantity DECIMAL(20, 8) NOT NULL,
                    order_type VARCHAR(20) NOT NULL,
                    price DECIMAL(20, 8),
                    stop_price DECIMAL(20, 8),
                    execution_price DECIMAL(20, 8),
                    status VARCHAR(20) NOT NULL,
                    time_in_force VARCHAR(10) NOT NULL,
                    strategy_id VARCHAR(255),
                    signal_id VARCHAR(255),
                    client_order_id VARCHAR(255),
                    commission DECIMAL(20, 8) DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    filled_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    metadata JSONB
                )
            """)
            
            # Create indexes
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_user_account ON orders (user_id, account_id)
            """)
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)
            """)
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders (symbol)
            """)
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at)
            """)
            
            # Create order events table for audit trail
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS order_events (
                    event_id SERIAL PRIMARY KEY,
                    order_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    event_data JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for order events
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_events_order_id ON order_events (order_id)
            """)
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_events_type ON order_events (event_type)
            """)
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_events_created_at ON order_events (created_at)
            """)
            
            self._initialized = True
            logger.info("Order storage tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize order storage: {e}")
            raise
    
    async def create_order(self, order_data: Dict[str, Any]) -> str:
        """Create a new order in the database"""
        try:
            await self.initialize()
            
            order_id = order_data["order_id"]
            
            # Insert order
            await self.db_manager.execute("""
                INSERT INTO orders (
                    order_id, user_id, account_id, symbol, side, quantity,
                    filled_quantity, remaining_quantity, order_type, price,
                    stop_price, status, time_in_force, strategy_id, signal_id,
                    client_order_id, created_at, updated_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            """, 
                order_id,
                order_data["user_id"],
                order_data["account_id"],
                order_data["symbol"],
                order_data["side"],
                order_data["quantity"],
                order_data["filled_quantity"],
                order_data["remaining_quantity"],
                order_data["order_type"],
                order_data["price"],
                order_data["stop_price"],
                order_data["status"],
                order_data["time_in_force"],
                order_data.get("strategy_id"),
                order_data.get("signal_id"),
                order_data.get("client_order_id"),
                order_data["created_at"],
                order_data["updated_at"],
                order_data.get("metadata")
            )
            
            # Log order created event
            await self._log_order_event(order_id, "ORDER_CREATED", {
                "symbol": order_data["symbol"],
                "side": order_data["side"],
                "quantity": str(order_data["quantity"]),
                "order_type": order_data["order_type"]
            })
            
            logger.info(f"Order {order_id} created successfully")
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to create order {order_id}: {e}")
            raise
    
    async def update_order(self, order_id: str, updates: Dict[str, Any]) -> bool:
        """Update an order in the database"""
        try:
            await self.initialize()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            for key, value in updates.items():
                if key != "order_id":  # Don't update the primary key
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            if not set_clauses:
                return True  # No updates to make
            
            # Add updated_at timestamp
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            
            # Add order_id for WHERE clause
            values.append(order_id)
            
            query = f"""
                UPDATE orders 
                SET {', '.join(set_clauses)}
                WHERE order_id = ${param_count}
            """
            
            result = await self.db_manager.execute(query, *values)
            
            if result == "UPDATE 1":
                logger.info(f"Order {order_id} updated successfully")
                return True
            else:
                logger.warning(f"Order {order_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update order {order_id}: {e}")
            raise
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get an order by ID"""
        try:
            await self.initialize()
            
            row = await self.db_manager.fetchrow("""
                SELECT * FROM orders WHERE order_id = $1
            """, order_id)
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise
    
    async def get_orders(
        self, 
        user_id: str, 
        account_id: str, 
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders with optional filtering"""
        try:
            await self.initialize()
            
            # Build dynamic query
            where_clauses = ["user_id = $1", "account_id = $2"]
            params = [user_id, account_id]
            param_count = 3
            
            if status:
                where_clauses.append(f"status = ${param_count}")
                params.append(status)
                param_count += 1
            
            if symbol:
                where_clauses.append(f"symbol = ${param_count}")
                params.append(symbol)
                param_count += 1
            
            # Add pagination
            params.extend([limit, offset])
            
            query = f"""
                SELECT * FROM orders 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY created_at DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            
            rows = await self.db_manager.fetch(query, *params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    async def delete_order(self, order_id: str) -> bool:
        """Delete an order (soft delete by setting status to cancelled)"""
        try:
            await self.initialize()
            
            result = await self.db_manager.execute("""
                UPDATE orders 
                SET status = 'cancelled', cancelled_at = $1, updated_at = $1
                WHERE order_id = $2
            """, datetime.utcnow(), order_id)
            
            if result == "UPDATE 1":
                await self._log_order_event(order_id, "ORDER_CANCELLED", {})
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.warning(f"Order {order_id} not found for cancellation")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def cleanup_expired_orders(self, max_age_hours: int = 24) -> int:
        """Clean up expired orders"""
        try:
            await self.initialize()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            result = await self.db_manager.execute("""
                UPDATE orders 
                SET status = 'expired', updated_at = $1
                WHERE status IN ('pending', 'submitted') 
                AND created_at < $2
            """, datetime.utcnow(), cutoff_time)
            
            # Extract number of affected rows from result
            affected_rows = int(result.split()[-1]) if result.startswith("UPDATE") else 0
            
            if affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} expired orders")
            
            return affected_rows
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired orders: {e}")
            raise
    
    async def _log_order_event(self, order_id: str, event_type: str, event_data: Dict[str, Any]):
        """Log an order event for audit trail"""
        try:
            await self.db_manager.execute("""
                INSERT INTO order_events (order_id, event_type, event_data)
                VALUES ($1, $2, $3)
            """, order_id, event_type, event_data)
            
        except Exception as e:
            logger.error(f"Failed to log order event for {order_id}: {e}")
            # Don't raise here as it's just logging
    
    async def get_order_events(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all events for an order"""
        try:
            await self.initialize()
            
            rows = await self.db_manager.fetch("""
                SELECT * FROM order_events 
                WHERE order_id = $1 
                ORDER BY created_at ASC
            """, order_id)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get order events for {order_id}: {e}")
            raise
