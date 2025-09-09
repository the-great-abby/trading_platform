"""
Order management routes
"""

from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import uuid
from datetime import datetime

from src.api.models.cqrs_models import (
    PlaceOrderRequest, CancelOrderRequest, OrderResponse
)

router = APIRouter()


@router.post("/orders", response_model=Dict[str, Any], status_code=201)
async def place_order(request: PlaceOrderRequest, app_request: Request):
    """Place a new order"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create order command
    from src.services.cqrs.commands import PlaceOrderCommand
    command = PlaceOrderCommand(
        symbol=request.symbol,
        side=request.side.value,
        quantity=request.quantity,
        order_type=request.order_type.value,
        price=request.price,
        user_id=request.user_id,
        account_id=request.account_id
    )
    
    # Dispatch command
    result = await cqrs_service.dispatch_command(command)
    
    if result.get("success"):
        return {
            "success": True,
            "order_id": result.get("order_id"),
            "status": result.get("status")
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to place order")
        )


@router.post("/orders/cancel", response_model=Dict[str, Any])
async def cancel_order(request: CancelOrderRequest, app_request: Request):
    """Cancel an existing order"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create cancel command
    from src.services.cqrs.commands import CancelOrderCommand
    command = CancelOrderCommand(
        order_id=request.order_id,
        reason=request.reason
    )
    
    # Dispatch command
    result = await cqrs_service.dispatch_command(command)
    
    if result.get("success"):
        return {
            "success": True,
            "order_id": result.get("order_id"),
            "status": result.get("status")
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to cancel order")
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, app_request: Request):
    """Get order details"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetOrderQuery
    query = GetOrderQuery(order_id=order_id)
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return result.get("order")
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Order not found")
        )
