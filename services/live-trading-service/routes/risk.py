"""
Risk Management API Routes

Handles risk management operations and emergency controls.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.live_trading.database import get_db_session
from src.services.live_trading.risk_service import RiskService, RiskValidationResult
from src.services.live_trading.models import RiskLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


# Pydantic models
class RiskProfileUpdate(BaseModel):
    """Risk profile update model."""
    max_position_size: Optional[float] = Field(None, description="Maximum position size")
    max_portfolio_risk: Optional[float] = Field(None, description="Maximum portfolio risk (as decimal)")
    max_daily_loss: Optional[float] = Field(None, description="Maximum daily loss")
    max_daily_trades: Optional[int] = Field(None, description="Maximum daily trades")
    allowed_strategies: Optional[List[str]] = Field(None, description="Allowed strategies")
    max_greeks_exposure: Optional[Dict[str, float]] = Field(None, description="Maximum Greeks exposure")
    risk_level: Optional[str] = Field(None, description="Risk level")


class RiskProfileResponse(BaseModel):
    """Risk profile response model."""
    risk_profile_id: str = Field(..., description="Risk profile ID")
    account_id: str = Field(..., description="Account ID")
    max_position_size: float = Field(..., description="Maximum position size")
    max_portfolio_risk: float = Field(..., description="Maximum portfolio risk")
    max_daily_loss: float = Field(..., description="Maximum daily loss")
    max_daily_trades: int = Field(..., description="Maximum daily trades")
    allowed_strategies: List[str] = Field(..., description="Allowed strategies")
    max_greeks_exposure: Dict[str, float] = Field(..., description="Maximum Greeks exposure")
    emergency_stop_active: bool = Field(..., description="Emergency stop status")
    emergency_stop_reason: Optional[str] = Field(None, description="Emergency stop reason")
    risk_level: str = Field(..., description="Risk level")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class EmergencyStopRequest(BaseModel):
    """Emergency stop request model."""
    reason: str = Field(..., description="Reason for emergency stop")
    severity: str = Field(default="HIGH", description="Severity level")
    cancel_orders: bool = Field(default=True, description="Cancel all orders")
    close_positions: bool = Field(default=False, description="Close all positions")


class EmergencyStopResponse(BaseModel):
    """Emergency stop response model."""
    success: bool = Field(..., description="Success status")
    emergency_stop_id: Optional[str] = Field(None, description="Emergency stop ID")
    status: str = Field(..., description="Emergency stop status")
    reason: str = Field(..., description="Emergency stop reason")
    activated_at: Optional[str] = Field(None, description="Activation timestamp")
    actions_taken: Optional[List[str]] = Field(None, description="Actions taken")


class RiskValidationRequest(BaseModel):
    """Risk validation request model."""
    symbol: str = Field(..., description="Trading symbol")
    strategy: str = Field(..., description="Strategy type")
    quantity: int = Field(..., description="Quantity")
    estimated_premium: float = Field(..., description="Estimated premium")
    estimated_risk: float = Field(..., description="Estimated risk")
    greeks: Optional[Dict[str, float]] = Field(None, description="Greeks")


class RiskValidationResponse(BaseModel):
    """Risk validation response model."""
    approved: bool = Field(..., description="Approval status")
    risk_score: float = Field(..., description="Risk score (0.0 to 1.0)")
    warnings: List[str] = Field(..., description="Risk warnings")
    errors: List[str] = Field(..., description="Risk errors")
    violations: List[str] = Field(..., description="Risk violations")
    override_reason: Optional[str] = Field(None, description="Override reason")


@router.get("/profile/{account_id}", response_model=RiskProfileResponse)
async def get_risk_profile(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get risk profile for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Risk profile information
    """
    try:
        risk_service = RiskService(db)
        risk_profile = await risk_service._get_risk_profile(account_id)
        
        if not risk_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk profile not found for account"
            )
        
        # Parse JSON fields
        allowed_strategies = json.loads(risk_profile.allowed_strategies) if risk_profile.allowed_strategies else []
        max_greeks_exposure = json.loads(risk_profile.max_greeks_exposure) if risk_profile.max_greeks_exposure else {}
        
        return RiskProfileResponse(
            risk_profile_id=str(risk_profile.risk_profile_id),
            account_id=str(risk_profile.account_id),
            max_position_size=float(risk_profile.max_position_size),
            max_portfolio_risk=float(risk_profile.max_portfolio_risk),
            max_daily_loss=float(risk_profile.max_daily_loss),
            max_daily_trades=risk_profile.max_daily_trades,
            allowed_strategies=allowed_strategies,
            max_greeks_exposure=max_greeks_exposure,
            emergency_stop_active=risk_profile.emergency_stop_active,
            emergency_stop_reason=risk_profile.emergency_stop_reason,
            risk_level=risk_profile.risk_level.value,
            created_at=risk_profile.created_at.isoformat(),
            updated_at=risk_profile.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk profile: {str(e)}"
        )


@router.put("/profile/{account_id}", response_model=RiskProfileResponse)
async def update_risk_profile(
    account_id: str,
    profile_update: RiskProfileUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update risk profile for an account.
    
    Args:
        account_id: Account ID
        profile_update: Risk profile update data
        
    Returns:
        Updated risk profile
    """
    try:
        risk_service = RiskService(db)
        risk_profile = await risk_service._get_risk_profile(account_id)
        
        if not risk_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk profile not found for account"
            )
        
        # Update fields if provided
        if profile_update.max_position_size is not None:
            risk_profile.max_position_size = profile_update.max_position_size
        
        if profile_update.max_portfolio_risk is not None:
            risk_profile.max_portfolio_risk = profile_update.max_portfolio_risk
        
        if profile_update.max_daily_loss is not None:
            risk_profile.max_daily_loss = profile_update.max_daily_loss
        
        if profile_update.max_daily_trades is not None:
            risk_profile.max_daily_trades = profile_update.max_daily_trades
        
        if profile_update.allowed_strategies is not None:
            risk_profile.allowed_strategies = json.dumps(profile_update.allowed_strategies)
        
        if profile_update.max_greeks_exposure is not None:
            risk_profile.max_greeks_exposure = json.dumps(profile_update.max_greeks_exposure)
        
        if profile_update.risk_level is not None:
            risk_profile.risk_level = RiskLevel(profile_update.risk_level)
        
        await db.commit()
        
        # Return updated profile
        allowed_strategies = json.loads(risk_profile.allowed_strategies) if risk_profile.allowed_strategies else []
        max_greeks_exposure = json.loads(risk_profile.max_greeks_exposure) if risk_profile.max_greeks_exposure else {}
        
        return RiskProfileResponse(
            risk_profile_id=str(risk_profile.risk_profile_id),
            account_id=str(risk_profile.account_id),
            max_position_size=float(risk_profile.max_position_size),
            max_portfolio_risk=float(risk_profile.max_portfolio_risk),
            max_daily_loss=float(risk_profile.max_daily_loss),
            max_daily_trades=risk_profile.max_daily_trades,
            allowed_strategies=allowed_strategies,
            max_greeks_exposure=max_greeks_exposure,
            emergency_stop_active=risk_profile.emergency_stop_active,
            emergency_stop_reason=risk_profile.emergency_stop_reason,
            risk_level=risk_profile.risk_level.value,
            created_at=risk_profile.created_at.isoformat(),
            updated_at=risk_profile.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update risk profile: {str(e)}"
        )


@router.post("/emergency-stop/{account_id}", response_model=EmergencyStopResponse)
async def activate_emergency_stop(
    account_id: str,
    request: EmergencyStopRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Activate emergency stop for an account.
    
    Args:
        account_id: Account ID
        request: Emergency stop request
        
    Returns:
        Emergency stop activation result
    """
    try:
        risk_service = RiskService(db)
        
        # Create request data
        request_data = {
            "reason": request.reason,
            "requested_by": "api_user",  # Would come from authentication
            "severity": request.severity,
            "cancel_orders": request.cancel_orders,
            "close_positions": request.close_positions
        }
        
        result = await risk_service.activate_emergency_stop(account_id, request.reason, "api_user")
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return EmergencyStopResponse(
            success=True,
            emergency_stop_id=result.get("emergency_stop_id"),
            status="ACTIVATED",
            reason=result["reason"],
            activated_at=result["activated_at"],
            actions_taken=result.get("actions_taken", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating emergency stop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate emergency stop: {str(e)}"
        )


@router.post("/emergency-stop/{account_id}/deactivate")
async def deactivate_emergency_stop(
    account_id: str,
    deactivated_by: str = "api_user",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Deactivate emergency stop for an account.
    
    Args:
        account_id: Account ID
        deactivated_by: User deactivating emergency stop
        
    Returns:
        Emergency stop deactivation result
    """
    try:
        risk_service = RiskService(db)
        
        result = await risk_service.deactivate_emergency_stop(account_id, "emergency_stop_id", deactivated_by)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "account_id": account_id,
            "status": "DEACTIVATED",
            "deactivated_by": deactivated_by,
            "deactivated_at": result["deactivated_at"],
            "message": "Emergency stop deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating emergency stop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate emergency stop: {str(e)}"
        )


@router.get("/emergency-stop/{account_id}/status")
async def get_emergency_stop_status(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get emergency stop status for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Emergency stop status
    """
    try:
        risk_service = RiskService(db)
        
        result = await risk_service.is_emergency_stop_active(account_id)
        
        return {
            "account_id": account_id,
            "is_active": result["is_active"],
            "emergency_stop_id": result.get("emergency_stop_id"),
            "activated_at": result.get("activated_at"),
            "reason": result.get("reason")
        }
        
    except Exception as e:
        logger.error(f"Error getting emergency stop status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emergency stop status: {str(e)}"
        )


@router.post("/validate/{account_id}", response_model=RiskValidationResponse)
async def validate_risk(
    account_id: str,
    request: RiskValidationRequest,
    emergency_override: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Validate risk for a potential trade.
    
    Args:
        account_id: Account ID
        request: Risk validation request
        emergency_override: Whether to apply emergency override
        
    Returns:
        Risk validation result
    """
    try:
        risk_service = RiskService(db)
        
        # Create order risk data
        from src.services.live_trading.risk_service import OrderRiskData
        
        order_data = OrderRiskData(
            symbol=request.symbol,
            strategy=request.strategy,
            quantity=request.quantity,
            estimated_premium=request.estimated_premium,
            estimated_risk=request.estimated_risk,
            greeks=request.greeks or {},
            position_size=request.estimated_premium
        )
        
        # Validate risk
        result = await risk_service.validate_order(account_id, order_data, emergency_override)
        
        return RiskValidationResponse(
            approved=result.approved,
            risk_score=result.risk_score,
            warnings=result.warnings,
            errors=result.errors,
            violations=[v.value for v in result.violations],
            override_reason=result.override_reason
        )
        
    except Exception as e:
        logger.error(f"Error validating risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate risk: {str(e)}"
        )


@router.get("/limits/{account_id}")
async def get_risk_limits(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get current risk limits and usage for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Risk limits and current usage
    """
    try:
        risk_service = RiskService(db)
        
        # Get risk profile
        risk_profile = await risk_service._get_risk_profile(account_id)
        if not risk_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk profile not found for account"
            )
        
        # Get current usage
        current_position_size = await risk_service._get_current_position_size(account_id)
        current_daily_loss = await risk_service._get_current_daily_loss(account_id)
        current_daily_trades = await risk_service._get_current_daily_trades(account_id)
        current_portfolio_risk = await risk_service._get_current_portfolio_risk(account_id)
        portfolio_value = await risk_service._get_portfolio_value(account_id)
        
        # Calculate usage percentages
        position_size_usage = (current_position_size / float(risk_profile.max_position_size)) * 100
        daily_loss_usage = (current_daily_loss / float(risk_profile.max_daily_loss)) * 100
        daily_trades_usage = (current_daily_trades / risk_profile.max_daily_trades) * 100
        max_risk_amount = portfolio_value * float(risk_profile.max_portfolio_risk)
        portfolio_risk_usage = (current_portfolio_risk / max_risk_amount) * 100 if max_risk_amount > 0 else 0
        
        return {
            "account_id": account_id,
            "limits": {
                "max_position_size": float(risk_profile.max_position_size),
                "max_portfolio_risk": float(risk_profile.max_portfolio_risk),
                "max_daily_loss": float(risk_profile.max_daily_loss),
                "max_daily_trades": risk_profile.max_daily_trades
            },
            "current_usage": {
                "position_size": current_position_size,
                "daily_loss": current_daily_loss,
                "daily_trades": current_daily_trades,
                "portfolio_risk": current_portfolio_risk,
                "portfolio_value": portfolio_value
            },
            "usage_percentages": {
                "position_size": round(position_size_usage, 2),
                "daily_loss": round(daily_loss_usage, 2),
                "daily_trades": round(daily_trades_usage, 2),
                "portfolio_risk": round(portfolio_risk_usage, 2)
            },
            "emergency_stop_active": risk_profile.emergency_stop_active,
            "risk_level": risk_profile.risk_level.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk limits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk limits: {str(e)}"
        )
