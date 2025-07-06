"""
Order Service - Internal microservice for order management operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version="1.0.0")

class OrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: str  # "market", "limit", "stop"
    price: Optional[float] = None
    strategy: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str

class Order(BaseModel):
    order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    price: Optional[float]
    status: str
    filled_quantity: float
    avg_fill_price: Optional[float]
    created_at: str
    updated_at: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "order-service"}

@app.get("/status")
async def get_status():
    """Get order service status"""
    return {
        "service": "order-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/orders", response_model=OrderResponse)
async def create_order(order_request: OrderRequest):
    """Create a new order"""
    try:
        order_id = str(uuid.uuid4())
        
        # Validate order
        if order_request.order_type == "limit" and not order_request.price:
            raise HTTPException(status_code=400, detail="Limit orders require a price")
        
        if order_request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        # Mock order creation
        logger.info(f"Creating {order_request.side} order for {order_request.quantity} {order_request.symbol}")
        
        return OrderResponse(
            order_id=order_id,
            status="pending",
            message=f"Order created successfully for {order_request.symbol}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    try:
        # Mock order details
        order = Order(
            order_id=order_id,
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            price=None,
            status="filled",
            filled_quantity=100,
            avg_fill_price=150.25,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        return order
    except Exception as e:
        logger.error(f"Failed to get order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")

@app.get("/orders")
async def get_orders(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100
):
    """Get orders with optional filtering"""
    try:
        # Mock orders data
        orders = [
            {
                "order_id": "order_1",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "order_type": "market",
                "price": None,
                "status": "filled",
                "filled_quantity": 100,
                "avg_fill_price": 150.25,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:01:00Z"
            },
            {
                "order_id": "order_2",
                "symbol": "GOOGL",
                "side": "sell",
                "quantity": 50,
                "order_type": "limit",
                "price": 2850.0,
                "status": "pending",
                "filled_quantity": 0,
                "avg_fill_price": None,
                "created_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z"
            }
        ]
        
        # Apply filters
        if status:
            orders = [o for o in orders if o["status"] == status]
        if symbol:
            orders = [o for o in orders if o["symbol"] == symbol]
        
        return {
            "orders": orders[:limit],
            "count": len(orders),
            "total_count": len(orders)
        }
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")

@app.put("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        logger.info(f"Cancelling order: {order_id}")
        
        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": "Order cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

@app.put("/orders/{order_id}/modify")
async def modify_order(order_id: str, modifications: Dict[str, Any]):
    """Modify an existing order"""
    try:
        logger.info(f"Modifying order: {order_id}")
        
        return {
            "order_id": order_id,
            "status": "modified",
            "message": "Order modified successfully",
            "modifications": modifications,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to modify order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to modify order: {str(e)}")

@app.get("/orders/status/{order_id}")
async def get_order_status(order_id: str):
    """Get order status"""
    try:
        # Mock order status
        status = {
            "order_id": order_id,
            "status": "filled",
            "filled_quantity": 100,
            "remaining_quantity": 0,
            "avg_fill_price": 150.25,
            "last_update": datetime.now().isoformat()
        }
        
        return status
    except Exception as e:
        logger.error(f"Failed to get order status for {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get order status: {str(e)}")

@app.get("/orders/statistics")
async def get_order_statistics():
    """Get order statistics"""
    try:
        stats = {
            "total_orders": 150,
            "filled_orders": 120,
            "pending_orders": 20,
            "cancelled_orders": 10,
            "fill_rate": 0.8,
            "avg_fill_time": "2.5 minutes",
            "total_volume": 15000,
            "successful_trades": 95,
            "failed_trades": 5
        }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get order statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get order statistics: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
