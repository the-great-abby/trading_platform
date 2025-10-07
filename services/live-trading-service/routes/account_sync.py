"""
Account Sync Routes

API endpoints for syncing account balances and positions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Dict, Any
import logging
import os

from src.services.live_trading.database import get_db_session
from src.services.live_trading.account_sync_service import AccountSyncService
from src.services.live_trading.public_api_client import PublicAPIClient
from src.services.live_trading.models import APICredentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.post("/sync/{account_id}")
async def sync_account(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Sync account balance and positions from Public.com.
    
    This endpoint:
    1. Fetches current account balance from Public.com
    2. Fetches current positions from Public.com
    3. Updates the database with latest values
    
    Useful after orders fill or for periodic reconciliation.
    """
    try:
        logger.info(f"🔄 Account sync requested for {account_id}")
        
        # Get API credentials
        result = await db.execute(
            select(
                APICredentials.access_token
            ).where(
                APICredentials.account_id == account_id,
                APICredentials.is_active == True
            ).order_by(APICredentials.created_at.desc()).limit(1)
        )
        
        creds = result.fetchone()
        if not creds:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active credentials found for account"
            )
        
        # Create API client
        api_client = PublicAPIClient()
        api_client.access_token = creds[0]
        api_client.is_authenticated = True
        api_client.client.headers.update({
            "Authorization": f"Bearer {creds[0]}"
        })
        
        # Create sync service
        sync_service = AccountSyncService(db, api_client)
        
        # Sync balance
        balance_result = await sync_service.sync_account_balance(account_id)
        
        # Sync positions
        positions_result = await sync_service.sync_positions(account_id)
        
        # Close API client
        await api_client.close()
        
        return {
            "success": True,
            "message": "Account synced successfully",
            "balance": balance_result,
            "positions": positions_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Account sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account sync failed: {str(e)}"
        )


@router.get("/balance/{account_id}")
async def get_account_balance(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get current account balance from database.
    
    Returns the last synced balance. Use /sync endpoint to refresh from Public.com.
    """
    try:
        result = await db.execute(text("""
            SELECT 
                cash_balance,
                equity,
                buying_power,
                updated_at
            FROM live_trading_accounts
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        cash, equity, buying_power, updated_at = row
        
        return {
            "success": True,
            "account_id": account_id,
            "cash_balance": float(cash),
            "equity": float(equity),
            "buying_power": float(buying_power),
            "portfolio_value": float(cash) + float(equity),
            "last_synced": updated_at.isoformat() if updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get account balance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account balance: {str(e)}"
        )
