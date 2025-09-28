"""
Authentication API Routes

Handles Public.com API authentication and credential management.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.models import LiveTradingAccount, APICredentials, RiskProfile
from src.services.live_trading.public_api_client import PublicAPIClient
from src.services.live_trading.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()


# Pydantic models for request/response
class PublicConnectRequest(BaseModel):
    """Request model for Public.com connection."""
    secret_key: str = Field(..., description="Public.com secret key for token generation")
    account_name: str = Field(..., description="Human-readable account name")
    account_type: str = Field(default="CASH", description="Account type (CASH or MARGIN)")
    validity_minutes: int = Field(default=1440, description="Token validity in minutes (default 24 hours)")


class PublicConnectResponse(BaseModel):
    """Response model for Public.com connection."""
    credential_id: str = Field(..., description="Credential ID")
    account_id: str = Field(..., description="Account ID")
    status: str = Field(..., description="Connection status")
    message: Optional[str] = Field(None, description="Status message")


class DisconnectRequest(BaseModel):
    """Request model for disconnection."""
    account_id: str = Field(..., description="Account ID to disconnect")


class DisconnectResponse(BaseModel):
    """Response model for disconnection."""
    account_id: str = Field(..., description="Account ID")
    status: str = Field(..., description="Disconnection status")
    message: Optional[str] = Field(None, description="Status message")


class AuthStatusResponse(BaseModel):
    """Response model for authentication status."""
    is_authenticated: bool = Field(..., description="Authentication status")
    account_id: Optional[str] = Field(None, description="Account ID")
    account_name: Optional[str] = Field(None, description="Account name")
    last_used: Optional[str] = Field(None, description="Last used timestamp")
    expires_at: Optional[str] = Field(None, description="Token expiration")


@router.post("/public-connect", response_model=PublicConnectResponse)
async def connect_to_public(
    request: PublicConnectRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Connect to Public.com API and store credentials.
    
    This endpoint authenticates with Public.com and stores the credentials
    securely for future trading operations.
    """
    try:
        # Create Public.com API client
        api_client = PublicAPIClient()
        
        # Authenticate with Public.com using secret key
        auth_response = await api_client.authenticate(
            secret_key=request.secret_key
        )
        
        # Get account information from Public.com
        accounts_response = await api_client.get_accounts()
        
        if not accounts_response.get("accounts"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accounts found in Public.com response"
            )
        
        # Use the first account (can be extended to support multiple accounts)
        public_account = accounts_response["accounts"][0]
        logger.info(f"Public.com account data: {public_account}")
        public_account_id = public_account.get("accountId") or public_account.get("id")
        logger.info(f"Extracted public_account_id: {public_account_id}")
        
        # Check if account already exists
        existing_account = await db.execute(
            text("SELECT account_id FROM live_trading_accounts WHERE public_account_id = :public_id"),
            {"public_id": public_account_id}
        )
        existing_account = existing_account.fetchone()
        
        if existing_account:
            account_id = existing_account[0]
            logger.info(f"Account already exists: {account_id}")
        else:
            # Create new live trading account
            account_id = str(uuid4())
            
            # Create account record
            account = LiveTradingAccount(
                account_id=account_id,
                public_account_id=public_account_id,
                account_name=request.account_name,
                account_type=request.account_type,
                buying_power=float(public_account.get("buying_power", 0)),
                cash_balance=float(public_account.get("cash_balance", 0)),
                equity=float(public_account.get("equity", 0)),
                is_active=True
            )
            
            db.add(account)
            
            # Create default risk profile
            risk_profile = RiskProfile(
                account_id=account_id,
                max_position_size=10000.0,
                max_portfolio_risk=0.05,  # 5%
                max_daily_loss=1000.0,
                max_daily_trades=20,
                allowed_strategies=json.dumps(["IRON_CONDOR", "BUTTERFLY_SPREAD", "CALENDAR_SPREAD"]),
                max_greeks_exposure=json.dumps({
                    "delta": 1000.0,
                    "gamma": 100.0,
                    "theta": -50.0,
                    "vega": 200.0
                }),
                emergency_stop_active=False
            )
            
            db.add(risk_profile)
            
            # Commit the account and risk profile first
            await db.commit()
            
            logger.info(f"Created new account: {account_id}")
        
        # Store encrypted credentials
        credential_id = str(uuid4())
        
        # Encrypt credentials (simplified - in production use proper encryption)
        encrypted_secret_key = api_client._encrypt_data(request.secret_key)
        encrypted_access_token = api_client._encrypt_data(auth_response["access_token"])
        
        # Calculate token expiration
        expires_at = datetime.utcnow() + timedelta(seconds=auth_response["expires_in"])
        
        # Create credentials record
        credentials = APICredentials(
            credential_id=credential_id,
            account_id=account_id,
            encrypted_api_key=encrypted_secret_key,  # Store secret key
            encrypted_api_secret="",  # Not used for Public.com
            access_token=encrypted_access_token,
            refresh_token="",  # Not used for Public.com
            token_expires_at=expires_at,
            is_active=True,
            last_used_at=datetime.utcnow()
        )
        
        db.add(credentials)
        
        await db.commit()
        
        # Close API client
        await api_client.close()
        
        logger.info(f"Successfully connected to Public.com for account {account_id}")
        
        return PublicConnectResponse(
            credential_id=credential_id,
            account_id=account_id,
            status="CONNECTED",
            message="Successfully connected to Public.com API"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to Public.com: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to Public.com: {str(e)}"
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_from_public(
    request: DisconnectRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Disconnect from Public.com API and deactivate credentials.
    
    This endpoint deactivates the stored credentials and marks the account
    as disconnected from Public.com.
    """
    try:
        # Find credentials for account
        credentials = await db.execute(
            "SELECT credential_id FROM api_credentials WHERE account_id = :account_id AND is_active = true",
            {"account_id": request.account_id}
        )
        credentials = credentials.fetchone()
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active credentials found for account"
            )
        
        # Deactivate credentials
        await db.execute(
            "UPDATE api_credentials SET is_active = false WHERE account_id = :account_id",
            {"account_id": request.account_id}
        )
        
        # Deactivate account
        await db.execute(
            "UPDATE live_trading_accounts SET is_active = false WHERE account_id = :account_id",
            {"account_id": request.account_id}
        )
        
        await db.commit()
        
        logger.info(f"Successfully disconnected account {request.account_id} from Public.com")
        
        return DisconnectResponse(
            account_id=request.account_id,
            status="DISCONNECTED",
            message="Successfully disconnected from Public.com API"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting from Public.com: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect from Public.com: {str(e)}"
        )


@router.get("/status/{account_id}", response_model=AuthStatusResponse)
async def get_auth_status(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get authentication status for an account.
    
    Returns the current authentication status and token information.
    """
    try:
        # Get account and credentials
        result = await db.execute(text("""
            SELECT 
                a.account_name,
                a.is_active,
                c.last_used_at,
                c.token_expires_at,
                c.is_active as cred_active
            FROM live_trading_accounts a
            LEFT JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        is_authenticated = (
            account_data[1] and  # account is_active
            account_data[4] and  # credentials is_active
            account_data[3] and  # token_expires_at exists
            account_data[3] > datetime.utcnow()  # token not expired
        )
        
        return AuthStatusResponse(
            is_authenticated=is_authenticated,
            account_id=account_id,
            account_name=account_data[0],
            last_used=account_data[2].isoformat() if account_data[2] else None,
            expires_at=account_data[3].isoformat() if account_data[3] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting auth status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get authentication status: {str(e)}"
        )


@router.post("/refresh-token/{account_id}")
async def refresh_access_token(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token for an account.
    
    Refreshes the expired access token using the stored refresh token.
    """
    try:
        # Get stored credentials
        result = await db.execute(text("""
            SELECT credential_id, refresh_token, access_token
            FROM api_credentials 
            WHERE account_id = :account_id AND is_active = true
        """), {"account_id": account_id})
        
        credentials = result.fetchone()
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active credentials found for account"
            )
        
        # Create API client and decrypt tokens
        api_client = PublicAPIClient()
        refresh_token = api_client._decrypt_data(credentials[1])
        api_client.refresh_token = refresh_token
        
        # Refresh token
        token_response = await api_client.refresh_access_token()
        
        # Encrypt and store new tokens
        encrypted_access_token = api_client._encrypt_data(token_response["access_token"])
        encrypted_refresh_token = api_client._encrypt_data(token_response["refresh_token"])
        expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
        
        # Update credentials
        await db.execute(text("""
            UPDATE api_credentials 
            SET 
                access_token = :access_token,
                refresh_token = :refresh_token,
                token_expires_at = :expires_at,
                last_used_at = :last_used
            WHERE credential_id = :credential_id
        """), {
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_refresh_token,
            "expires_at": expires_at,
            "last_used": datetime.utcnow(),
            "credential_id": credentials[0]
        })
        
        await db.commit()
        
        # Close API client
        await api_client.close()
        
        logger.info(f"Successfully refreshed access token for account {account_id}")
        
        return {
            "success": True,
            "account_id": account_id,
            "expires_at": expires_at.isoformat(),
            "message": "Access token refreshed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh access token: {str(e)}"
        )


@router.get("/accounts")
async def list_connected_accounts(
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all connected accounts.
    
    Returns a list of all accounts that are connected to Public.com.
    """
    try:
        result = await db.execute(text("""
            SELECT 
                a.account_id,
                a.public_account_id,
                a.account_name,
                a.account_type,
                a.buying_power,
                a.cash_balance,
                a.equity,
                a.is_active,
                c.last_used_at,
                c.token_expires_at,
                c.is_active as cred_active
            FROM live_trading_accounts a
            LEFT JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.is_active = true
            ORDER BY a.created_at DESC
        """))
        
        accounts = result.fetchall()
        
        account_list = []
        for account in accounts:
            is_authenticated = (
                account[7] and  # account is_active
                account[10] and  # credentials is_active
                account[9] and  # token_expires_at exists
                account[9] > datetime.utcnow()  # token not expired
            )
            
            account_list.append({
                "account_id": account[0],
                "public_account_id": account[1],
                "account_name": account[2],
                "account_type": account[3],
                "buying_power": float(account[4]),
                "cash_balance": float(account[5]),
                "equity": float(account[6]),
                "is_active": account[7],
                "is_authenticated": is_authenticated,
                "last_used": account[8].isoformat() if account[8] else None,
                "token_expires": account[9].isoformat() if account[9] else None
            })
        
        return {
            "accounts": account_list,
            "total_count": len(account_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list accounts: {str(e)}"
        )
