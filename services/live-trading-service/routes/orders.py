"""
Order Management Routes

API endpoints for order status synchronization and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.services.live_trading.database import get_db_session
from src.services.live_trading.order_sync_service import OrderSyncService
from src.services.live_trading.public_api_client import PublicAPIClient, PublicAPIConfig

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("/sync/{account_id}")
async def sync_pending_orders(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Synchronize all pending orders for an account with Public.com.
    
    This will:
    1. Fetch all pending orders from the database
    2. Query Public.com for their current status
    3. Update the database with fills, cancellations, etc.
    
    Args:
        account_id: Account ID to sync orders for
        
    Returns:
        Summary of sync results
    """
    try:
        from sqlalchemy import select
        from src.services.live_trading.models import APICredentials
        import os
        
        # Get API credentials from database (most recent active one)
        result = await db.execute(
            select(APICredentials).where(
                APICredentials.account_id == account_id,
                APICredentials.is_active == True
            ).order_by(APICredentials.created_at.desc()).limit(1)
        )
        credentials = result.scalar_one_or_none()
        
        if not credentials:
            raise HTTPException(status_code=404, detail="No active API credentials found")
        
        # Initialize Public.com API client with credentials
        config = PublicAPIConfig()
        config.access_token = credentials.access_token
        config.secret_key = credentials.api_secret if hasattr(credentials, 'api_secret') else ""
        
        public_client = PublicAPIClient(config)
        
        # Initialize order sync service
        sync_service = OrderSyncService(db, public_client)
        
        # Sync pending orders
        result = await sync_service.sync_pending_orders(account_id)
        
        # If any orders were filled, recalculate account balance
        balance_result = {}
        if result.get("filled", 0) > 0:
            logger.info(f"Orders filled, recalculating account balance...")
            balance_result = await sync_service.recalculate_account_balance(account_id)
        
        return {
            "success": True,
            "account_id": account_id,
            "balance_updated": balance_result.get("success", False),
            **result,
            "balance": balance_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order sync failed: {str(e)}")


@router.post("/sync/{account_id}/trade/{trade_id}")
async def sync_single_order(
    account_id: str,
    trade_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Synchronize a single order with Public.com.
    
    Args:
        account_id: Account ID
        trade_id: Trade ID to sync
        
    Returns:
        Updated trade information
    """
    try:
        # Initialize Public.com API client
        config = PublicAPIConfig()
        public_client = PublicAPIClient(config)
        
        # Initialize order sync service
        sync_service = OrderSyncService(db, public_client)
        
        # Sync single order
        result = await sync_service.sync_single_order(account_id, trade_id)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order sync failed: {str(e)}")


@router.get("/pending/{account_id}")
async def get_pending_orders(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get all pending orders for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        List of pending orders
    """
    try:
        from sqlalchemy import select
        from src.services.live_trading.models import LiveTrade, TradeStatus
        
        result = await db.execute(
            select(LiveTrade).where(
                LiveTrade.account_id == account_id,
                LiveTrade.status == TradeStatus.PENDING
            ).order_by(LiveTrade.created_at.desc())
        )
        
        pending_trades = result.scalars().all()
        
        return {
            "success": True,
            "account_id": account_id,
            "pending_count": len(pending_trades),
            "orders": [
                {
                    "trade_id": str(trade.trade_id),
                    "symbol": trade.symbol,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "price": float(trade.price) if trade.price else None,
                    "public_order_id": trade.public_order_id,
                    "created_at": trade.created_at.isoformat(),
                    "is_temp_id": trade.public_order_id.startswith("TEMP_") if trade.public_order_id else True
                }
                for trade in pending_trades
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending orders: {str(e)}")

