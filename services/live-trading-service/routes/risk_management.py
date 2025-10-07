"""
Risk Management API Routes

Handles risk management configuration for live trading.
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

router = APIRouter(prefix="/api/v1/risk-management", tags=["risk-management"])


# Pydantic models
class RiskManagementConfig(BaseModel):
    """Risk management configuration model."""
    account_id: str = Field(..., description="Account ID")
    risk_level: str = Field(..., description="Risk level (CONSERVATIVE, MODERATE, AGGRESSIVE)")
    max_greeks_exposure: Dict[str, float] = Field(..., description="Maximum Greeks exposure")
    position_limits: Dict[str, int] = Field(..., description="Position limits")
    emergency_controls: Dict[str, Any] = Field(..., description="Emergency controls")


class RiskManagementResponse(BaseModel):
    """Risk management response model."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error message")


@router.post("/", response_model=RiskManagementResponse)
async def configure_risk_management(
    config: RiskManagementConfig,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Configure risk management settings for an account.
    
    Args:
        config: Risk management configuration
        
    Returns:
        Configuration result
    """
    try:
        # Validate risk level
        valid_risk_levels = ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"]
        if config.risk_level not in valid_risk_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk level. Must be one of: {valid_risk_levels}"
            )
        
        # Check if account exists
        result = await db.execute(text("""
            SELECT account_id FROM live_trading_accounts 
            WHERE account_id = :account_id
        """), {"account_id": config.account_id})
        
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Update risk profile
        await db.execute(text("""
            UPDATE risk_profiles SET
                risk_level = :risk_level,
                max_greeks_exposure = :max_greeks_exposure,
                position_limits = :position_limits,
                emergency_controls = :emergency_controls,
                updated_at = :updated_at
            WHERE account_id = :account_id
        """), {
            "account_id": config.account_id,
            "risk_level": config.risk_level,
            "max_greeks_exposure": json.dumps(config.max_greeks_exposure),
            "position_limits": json.dumps(config.position_limits),
            "emergency_controls": json.dumps(config.emergency_controls),
            "updated_at": datetime.utcnow()
        })
        
        await db.commit()
        
        logger.info(f"Risk management configured for account {config.account_id}")
        
        return RiskManagementResponse(
            success=True,
            message=f"Risk management configured successfully for {config.risk_level} level"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring risk management: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure risk management: {str(e)}"
        )


@router.get("/{account_id}")
async def get_risk_management(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get risk management configuration for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Risk management configuration
    """
    try:
        result = await db.execute(text("""
            SELECT 
                risk_level, max_greeks_exposure, position_limits, 
                emergency_controls, updated_at
            FROM risk_profiles
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk profile not found"
            )
        
        return {
            "account_id": account_id,
            "risk_level": row[0],
            "max_greeks_exposure": json.loads(row[1]) if row[1] else {},
            "position_limits": json.loads(row[2]) if row[2] else {},
            "emergency_controls": json.loads(row[3]) if row[3] else {},
            "updated_at": row[4].isoformat() if row[4] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk management: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk management: {str(e)}"
        )





















