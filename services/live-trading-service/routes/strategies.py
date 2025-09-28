"""
Strategy Management API Routes

Handles strategy configuration and management for live trading.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.database import get_db_session
from src.services.live_trading.models import StrategyType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


# Pydantic models
class StrategyConfig(BaseModel):
    """Strategy configuration model."""
    strategy_name: str = Field(..., description="Strategy name")
    enabled: bool = Field(True, description="Whether strategy is enabled")
    max_position_size: float = Field(..., description="Maximum position size as percentage")
    max_risk_per_trade: float = Field(..., description="Maximum risk per trade as percentage")
    max_daily_trades: int = Field(..., description="Maximum daily trades")
    max_daily_loss: float = Field(..., description="Maximum daily loss")
    description: str = Field(..., description="Strategy description")
    symbols: List[str] = Field(..., description="Allowed symbols")


class StrategyResponse(BaseModel):
    """Strategy response model."""
    success: bool = Field(..., description="Success status")
    strategy_id: Optional[str] = Field(None, description="Strategy ID")
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error message")


class RiskManagementConfig(BaseModel):
    """Risk management configuration model."""
    risk_level: str = Field(..., description="Risk level (CONSERVATIVE, MODERATE, AGGRESSIVE)")
    max_greeks_exposure: Dict[str, float] = Field(..., description="Maximum Greeks exposure")
    position_limits: Dict[str, int] = Field(..., description="Position limits")
    emergency_controls: Dict[str, Any] = Field(..., description="Emergency controls")


class TrailingStopConfig(BaseModel):
    """Trailing stop configuration model."""
    strategy_name: str = Field(..., description="Strategy name")
    profit_threshold: float = Field(..., description="Profit threshold to activate trailing stop")
    trail_percentage: float = Field(..., description="Trailing percentage")
    min_profit: float = Field(..., description="Minimum profit to activate")
    enabled: bool = Field(True, description="Whether trailing stop is enabled")


class TrailingStopsRequest(BaseModel):
    """Trailing stops request model."""
    account_id: str = Field(..., description="Account ID")
    trailing_stops: Dict[str, Dict[str, Any]] = Field(..., description="Trailing stop configurations")


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    account_id: str,
    strategy_config: StrategyConfig,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create or update a trading strategy configuration.
    
    Args:
        account_id: Account ID
        strategy_config: Strategy configuration
        
    Returns:
        Strategy creation result
    """
    try:
        # Validate strategy name
        try:
            StrategyType(strategy_config.strategy_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid strategy name: {strategy_config.strategy_name}"
            )
        
        # Check if account exists
        result = await db.execute(text("""
            SELECT account_id FROM live_trading_accounts 
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Insert or update strategy configuration
        strategy_id = f"{account_id}_{strategy_config.strategy_name}"
        
        await db.execute(text("""
            INSERT INTO strategy_configurations (
                strategy_id, account_id, strategy_name, enabled, 
                max_position_size, max_risk_per_trade, max_daily_trades, 
                max_daily_loss, description, symbols, created_at, updated_at
            ) VALUES (
                :strategy_id, :account_id, :strategy_name, :enabled,
                :max_position_size, :max_risk_per_trade, :max_daily_trades,
                :max_daily_loss, :description, :symbols, :created_at, :updated_at
            )
            ON CONFLICT (strategy_id) DO UPDATE SET
                enabled = :enabled,
                max_position_size = :max_position_size,
                max_risk_per_trade = :max_risk_per_trade,
                max_daily_trades = :max_daily_trades,
                max_daily_loss = :max_daily_loss,
                description = :description,
                symbols = :symbols,
                updated_at = :updated_at
        """), {
            "strategy_id": strategy_id,
            "account_id": account_id,
            "strategy_name": strategy_config.strategy_name,
            "enabled": strategy_config.enabled,
            "max_position_size": strategy_config.max_position_size,
            "max_risk_per_trade": strategy_config.max_risk_per_trade,
            "max_daily_trades": strategy_config.max_daily_trades,
            "max_daily_loss": strategy_config.max_daily_loss,
            "description": strategy_config.description,
            "symbols": json.dumps(strategy_config.symbols),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        await db.commit()
        
        logger.info(f"Strategy {strategy_config.strategy_name} configured for account {account_id}")
        
        return StrategyResponse(
            success=True,
            strategy_id=strategy_id,
            message=f"Strategy {strategy_config.strategy_name} configured successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {str(e)}"
        )


@router.get("/{account_id}")
async def get_strategies(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all strategies for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        List of strategies
    """
    try:
        result = await db.execute(text("""
            SELECT 
                strategy_id, strategy_name, enabled, max_position_size,
                max_risk_per_trade, max_daily_trades, max_daily_loss,
                description, symbols, created_at, updated_at
            FROM strategy_configurations
            WHERE account_id = :account_id
            ORDER BY created_at DESC
        """), {"account_id": account_id})
        
        strategies = []
        for row in result.fetchall():
            strategies.append({
                "strategy_id": row[0],
                "strategy_name": row[1],
                "enabled": row[2],
                "max_position_size": row[3],
                "max_risk_per_trade": row[4],
                "max_daily_trades": row[5],
                "max_daily_loss": row[6],
                "description": row[7],
                "symbols": json.loads(row[8]) if row[8] else [],
                "created_at": row[9].isoformat() if row[9] else None,
                "updated_at": row[10].isoformat() if row[10] else None
            })
        
        return {
            "account_id": account_id,
            "strategies": strategies,
            "total_count": len(strategies)
        }
        
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategies: {str(e)}"
        )


@router.delete("/{account_id}/{strategy_name}")
async def delete_strategy(
    account_id: str,
    strategy_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a strategy configuration.
    
    Args:
        account_id: Account ID
        strategy_name: Strategy name
        
    Returns:
        Deletion result
    """
    try:
        strategy_id = f"{account_id}_{strategy_name}"
        
        result = await db.execute(text("""
            DELETE FROM strategy_configurations
            WHERE strategy_id = :strategy_id
        """), {"strategy_id": strategy_id})
        
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        logger.info(f"Strategy {strategy_name} deleted for account {account_id}")
        
        return StrategyResponse(
            success=True,
            message=f"Strategy {strategy_name} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete strategy: {str(e)}"
        )


