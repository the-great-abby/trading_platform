"""
Account Management API Routes

Handles account information and balance management.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.database import get_db_session
from src.services.live_trading.public_api_client import PublicAPIClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


# Pydantic models
class AccountBalance(BaseModel):
    """Account balance information."""
    account_id: str = Field(..., description="Account ID")
    buying_power: float = Field(..., description="Available buying power")
    cash_balance: float = Field(..., description="Cash balance")
    equity: float = Field(..., description="Total account equity")
    margin_used: Optional[float] = Field(None, description="Margin used")
    margin_available: Optional[float] = Field(None, description="Available margin")
    last_updated: str = Field(..., description="Last updated timestamp")


class AccountInfo(BaseModel):
    """Account information."""
    account_id: str = Field(..., description="Account ID")
    public_account_id: str = Field(..., description="Public.com account ID")
    account_name: str = Field(..., description="Account name")
    account_type: str = Field(..., description="Account type")
    is_active: bool = Field(..., description="Account active status")
    created_at: str = Field(..., description="Account creation timestamp")


class AccountListResponse(BaseModel):
    """Response for account list."""
    accounts: list = Field(..., description="List of accounts")
    total_count: int = Field(..., description="Total number of accounts")


@router.get("", response_model=AccountListResponse)
async def get_accounts(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all live trading accounts.
    
    Returns a list of all configured live trading accounts.
    """
    try:
        result = await db.execute(text("""
            SELECT 
                account_id,
                public_account_id,
                account_name,
                account_type,
                buying_power,
                cash_balance,
                equity,
                is_active,
                created_at
            FROM live_trading_accounts
            ORDER BY created_at DESC
        """))
        
        accounts = result.fetchall()
        
        account_list = []
        for account in accounts:
            account_list.append({
                "account_id": account[0],
                "public_account_id": account[1],
                "account_name": account[2],
                "account_type": account[3],
                "buying_power": float(account[4]),
                "cash_balance": float(account[5]),
                "equity": float(account[6]),
                "is_active": account[7],
                "created_at": account[8].isoformat()
            })
        
        return AccountListResponse(
            accounts=account_list,
            total_count=len(account_list)
        )
        
    except Exception as e:
        logger.error(f"Error getting accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accounts: {str(e)}"
        )


@router.get("/{account_id}", response_model=AccountInfo)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get account information by ID.
    
    Args:
        account_id: Account ID
        
    Returns:
        Account information
    """
    try:
        result = await db.execute(text("""
            SELECT 
                account_id,
                public_account_id,
                account_name,
                account_type,
                is_active,
                created_at
            FROM live_trading_accounts
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        account = result.fetchone()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return AccountInfo(
            account_id=account[0],
            public_account_id=account[1],
            account_name=account[2],
            account_type=account[3],
            is_active=account[4],
            created_at=account[5].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account: {str(e)}"
        )


@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get real-time account balance from Public.com.
    
    Args:
        account_id: Account ID
        
    Returns:
        Real-time account balance information
    """
    try:
        # Get stored credentials (latest active)
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN (
                SELECT DISTINCT ON (account_id) 
                    account_id, access_token, refresh_token, token_expires_at
                FROM api_credentials 
                WHERE is_active = true
                ORDER BY account_id, last_used_at DESC
            ) c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not authenticated"
            )
        
        public_account_id = account_data[0]
        
        # Create API client and authenticate
        api_client = PublicAPIClient()
        
        # Check if token is expired and refresh if needed
        if account_data[3] and account_data[3] <= datetime.utcnow():
            logger.info(f"Token expired for account {account_id}, refreshing...")
            refresh_token = api_client._decrypt_data(account_data[2])
            api_client.refresh_token = refresh_token
            await api_client.refresh_access_token()
        else:
            access_token = api_client._decrypt_data(account_data[1])
            api_client.access_token = access_token
            api_client.is_authenticated = True
            api_client.client.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
        
        # Get balance from Public.com
        balance_response = await api_client.get_account_balance(public_account_id)
        
        # Update local account balance
        await db.execute(text("""
            UPDATE live_trading_accounts 
            SET 
                buying_power = :buying_power,
                cash_balance = :cash_balance,
                equity = :equity,
                updated_at = :updated_at
            WHERE account_id = :account_id
        """), {
            "buying_power": balance_response.get("buying_power", 0),
            "cash_balance": balance_response.get("cash_balance", 0),
            "equity": balance_response.get("equity", 0),
            "updated_at": datetime.utcnow(),
            "account_id": account_id
        })
        
        await db.commit()
        
        # Close API client
        await api_client.close()
        
        return AccountBalance(
            account_id=account_id,
            buying_power=float(balance_response.get("buying_power", 0)),
            cash_balance=float(balance_response.get("cash_balance", 0)),
            equity=float(balance_response.get("equity", 0)),
            margin_used=balance_response.get("margin_used"),
            margin_available=balance_response.get("margin_available"),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account balance for {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account balance: {str(e)}"
        )


@router.post("/{account_id}/sync")
async def sync_account_data(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Sync account data with Public.com.
    
    Updates local account information with latest data from Public.com.
    
    Args:
        account_id: Account ID to sync
        
    Returns:
        Sync result
    """
    try:
        # Get stored credentials (latest active)
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN (
                SELECT DISTINCT ON (account_id) 
                    account_id, access_token, refresh_token, token_expires_at
                FROM api_credentials 
                WHERE is_active = true
                ORDER BY account_id, last_used_at DESC
            ) c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not authenticated"
            )
        
        public_account_id = account_data[0]
        
        # Create API client and authenticate
        api_client = PublicAPIClient()
        
        # Check if token is expired and refresh if needed
        if account_data[3] and account_data[3] <= datetime.utcnow():
            logger.info(f"Token expired for account {account_id}, refreshing...")
            refresh_token = api_client._decrypt_data(account_data[2])
            api_client.refresh_token = refresh_token
            await api_client.refresh_access_token()
        else:
            access_token = api_client._decrypt_data(account_data[1])
            api_client.access_token = access_token
            api_client.is_authenticated = True
            api_client.client.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
        
        # Get account information from Public.com
        accounts_response = await api_client.get_accounts()
        
        # Find matching account
        public_account = None
        for account in accounts_response.get("accounts", []):
            if account["id"] == public_account_id:
                public_account = account
                break
        
        if not public_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found in Public.com"
            )
        
        # Update local account data
        await db.execute(text("""
            UPDATE live_trading_accounts 
            SET 
                buying_power = :buying_power,
                cash_balance = :cash_balance,
                equity = :equity,
                updated_at = :updated_at
            WHERE account_id = :account_id
        """), {
            "buying_power": public_account.get("buying_power", 0),
            "cash_balance": public_account.get("cash_balance", 0),
            "equity": public_account.get("equity", 0),
            "updated_at": datetime.utcnow(),
            "account_id": account_id
        })
        
        await db.commit()
        
        # Close API client
        await api_client.close()
        
        logger.info(f"Successfully synced account data for {account_id}")
        
        return {
            "success": True,
            "account_id": account_id,
            "synced_at": datetime.utcnow().isoformat(),
            "message": "Account data synchronized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing account data for {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync account data: {str(e)}"
        )
