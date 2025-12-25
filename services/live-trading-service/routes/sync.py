"""
Account Sync Routes
===================
API endpoints for syncing account data from Public.com
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.services.live_trading.database import get_db_session
from src.services.live_trading.account_sync_service import AccountSyncService
from src.services.live_trading.public_api_client import PublicAPIClient

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])
logger = logging.getLogger(__name__)


@router.post("/{account_id}/positions")
async def sync_positions(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Sync positions from Public.com to database.
    
    This fetches the current portfolio from Public.com's portfolio/v2 endpoint
    and updates the database with all positions (stocks and options).
    
    Args:
        account_id: Internal account ID
        
    Returns:
        Sync results
    """
    try:
        logger.info(f"🔄 Position sync requested for account {account_id}")
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Get credentials and authenticate
        from sqlalchemy import text
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id 
                AND c.is_active = true
            ORDER BY c.created_at DESC
            LIMIT 1
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not authenticated"
            )
        
        # Set API client credentials
        access_token = api_client._decrypt_data(account_data[1])
        api_client.access_token = access_token
        api_client.is_authenticated = True
        api_client.client.headers.update({
            "Authorization": f"Bearer {access_token}"
        })
        
        # Create sync service
        sync_service = AccountSyncService(db, api_client)
        
        # Sync positions
        result = await sync_service.sync_positions(account_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Position sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Position sync failed: {str(e)}"
        )


@router.post("/{account_id}/all")
async def sync_account(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Full account sync from Public.com (positions, balance, orders).
    
    Args:
        account_id: Internal account ID
        
    Returns:
        Complete sync results
    """
    try:
        logger.info(f"🔄 Full account sync requested for {account_id}")
        
        # For now, just sync positions
        # Can expand to sync balance, orders, etc.
        return await sync_positions(account_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Account sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account sync failed: {str(e)}"
        )

