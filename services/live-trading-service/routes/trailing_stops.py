"""
Trailing Stops API Routes

Handles trailing stop configuration for live trading.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trailing-stops", tags=["trailing-stops"])


# Pydantic models
class TrailingStopsRequest(BaseModel):
    """Trailing stops request model."""
    account_id: str = Field(..., description="Account ID")
    trailing_stops: Dict[str, Dict[str, Any]] = Field(..., description="Trailing stop configurations")


class TrailingStopsResponse(BaseModel):
    """Trailing stops response model."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error message")


@router.post("/", response_model=TrailingStopsResponse)
async def configure_trailing_stops(
    request: TrailingStopsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Configure trailing stop settings for an account.
    
    Args:
        request: Trailing stops configuration request
        
    Returns:
        Configuration result
    """
    try:
        # Check if account exists
        result = await db.execute(text("""
            SELECT account_id FROM live_trading_accounts 
            WHERE account_id = :account_id
        """), {"account_id": request.account_id})
        
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Insert or update trailing stop configurations
        for strategy_name, config in request.trailing_stops.items():
            trailing_stop_id = f"{request.account_id}_{strategy_name}"
            
            await db.execute(text("""
                INSERT INTO trailing_stop_configurations (
                    trailing_stop_id, account_id, strategy_name, 
                    profit_threshold, trail_percentage, min_profit, 
                    enabled, created_at, updated_at
                ) VALUES (
                    :trailing_stop_id, :account_id, :strategy_name,
                    :profit_threshold, :trail_percentage, :min_profit,
                    :enabled, :created_at, :updated_at
                )
                ON CONFLICT (trailing_stop_id) DO UPDATE SET
                    profit_threshold = :profit_threshold,
                    trail_percentage = :trail_percentage,
                    min_profit = :min_profit,
                    enabled = :enabled,
                    updated_at = :updated_at
            """), {
                "trailing_stop_id": trailing_stop_id,
                "account_id": request.account_id,
                "strategy_name": strategy_name,
                "profit_threshold": config.get("profit_threshold", 0.5),
                "trail_percentage": config.get("trail_percentage", 0.05),
                "min_profit": config.get("min_profit", 0.3),
                "enabled": config.get("enabled", True),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        
        await db.commit()
        
        logger.info(f"Trailing stops configured for account {request.account_id}")
        
        return TrailingStopsResponse(
            success=True,
            message=f"Trailing stops configured successfully for {len(request.trailing_stops)} strategies"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring trailing stops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure trailing stops: {str(e)}"
        )


@router.get("/{account_id}")
async def get_trailing_stops(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get trailing stop configurations for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Trailing stop configurations
    """
    try:
        result = await db.execute(text("""
            SELECT 
                strategy_name, profit_threshold, trail_percentage, 
                min_profit, enabled, created_at, updated_at
            FROM trailing_stop_configurations
            WHERE account_id = :account_id
            ORDER BY strategy_name
        """), {"account_id": account_id})
        
        trailing_stops = {}
        for row in result.fetchall():
            trailing_stops[row[0]] = {
                "profit_threshold": row[1],
                "trail_percentage": row[2],
                "min_profit": row[3],
                "enabled": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "updated_at": row[6].isoformat() if row[6] else None
            }
        
        return {
            "account_id": account_id,
            "trailing_stops": trailing_stops,
            "total_count": len(trailing_stops)
        }
        
    except Exception as e:
        logger.error(f"Error getting trailing stops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trailing stops: {str(e)}"
        )


@router.delete("/{account_id}/{strategy_name}")
async def delete_trailing_stop(
    account_id: str,
    strategy_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a trailing stop configuration.
    
    Args:
        account_id: Account ID
        strategy_name: Strategy name
        
    Returns:
        Deletion result
    """
    try:
        trailing_stop_id = f"{account_id}_{strategy_name}"
        
        result = await db.execute(text("""
            DELETE FROM trailing_stop_configurations
            WHERE trailing_stop_id = :trailing_stop_id
        """), {"trailing_stop_id": trailing_stop_id})
        
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trailing stop configuration not found"
            )
        
        logger.info(f"Trailing stop {strategy_name} deleted for account {account_id}")
        
        return TrailingStopsResponse(
            success=True,
            message=f"Trailing stop {strategy_name} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trailing stop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trailing stop: {str(e)}"
        )























