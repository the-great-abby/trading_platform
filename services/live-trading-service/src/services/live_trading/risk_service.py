"""
Risk Management Service

Handles risk management for live trading operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .models import RiskProfile, LiveTrade, LivePosition, RiskLevel

logger = logging.getLogger(__name__)


class RiskViolationType(str, Enum):
    """Types of risk violations."""
    POSITION_SIZE = "POSITION_SIZE"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    DAILY_LOSS = "DAILY_LOSS"
    DAILY_TRADES = "DAILY_TRADES"
    GREEKS_EXPOSURE = "GREEKS_EXPOSURE"
    STRATEGY_NOT_ALLOWED = "STRATEGY_NOT_ALLOWED"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass
class RiskValidationResult:
    """Result of risk validation."""
    approved: bool
    risk_score: float
    warnings: List[str]
    errors: List[str]
    violations: List[RiskViolationType]
    override_reason: Optional[str] = None


@dataclass
class OrderRiskData:
    """Risk data for an order."""
    symbol: str
    strategy: str
    quantity: int
    estimated_premium: float
    estimated_risk: float
    greeks: Dict[str, float]
    position_size: float
    action: str = "BUY"  # BUY or SELL


class RiskService:
    """Service for managing trading risk."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the risk management service."""
        self.db_session = db_session
    
    async def validate_order(self, account_id: str, order_data: OrderRiskData, emergency_override: bool = False) -> RiskValidationResult:
        """
        Validate an order against risk limits.
        
        Args:
            account_id: Trading account ID
            order_data: Order risk data
            emergency_override: Whether emergency override is active
            
        Returns:
            Risk validation result
        """
        try:
            # Get risk profile for account
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return RiskValidationResult(
                    approved=False,
                    risk_score=1.0,
                    warnings=[],
                    errors=["No risk profile found for account"],
                    violations=[RiskViolationType.EMERGENCY_STOP]
                )
            
            # Check emergency stop
            if risk_profile.emergency_stop_active and not emergency_override:
                return RiskValidationResult(
                    approved=False,
                    risk_score=1.0,
                    warnings=[],
                    errors=["Emergency stop is active"],
                    violations=[RiskViolationType.EMERGENCY_STOP]
                )
            
            warnings = []
            errors = []
            violations = []
            risk_score = 0.0
            
            # SELL orders (exits) bypass most risk checks
            is_exit = order_data.action == "SELL"
            if is_exit:
                logger.info(f"✅ SELL order for {order_data.symbol} - bypassing risk checks (exit position)")
                return RiskValidationResult(
                    approved=True,
                    risk_score=0.0,
                    warnings=["Exit order - risk checks bypassed"],
                    errors=[],
                    violations=[]
                )
            
            # Validate position size (only for BUY orders)
            position_size_result = await self._validate_position_size(risk_profile, order_data)
            if not position_size_result["approved"]:
                errors.append(position_size_result["message"])
                violations.append(RiskViolationType.POSITION_SIZE)
                risk_score += 0.3
            elif position_size_result["warning"]:
                warnings.append(position_size_result["message"])
                risk_score += 0.1
            
            # Validate portfolio risk
            portfolio_risk_result = await self._validate_portfolio_risk(risk_profile, account_id, order_data)
            if not portfolio_risk_result["approved"]:
                errors.append(portfolio_risk_result["message"])
                violations.append(RiskViolationType.PORTFOLIO_RISK)
                risk_score += 0.4
            elif portfolio_risk_result["warning"]:
                warnings.append(portfolio_risk_result["message"])
                risk_score += 0.15
            
            # Validate daily loss limits
            daily_loss_result = await self._validate_daily_loss(risk_profile, account_id, order_data)
            if not daily_loss_result["approved"]:
                errors.append(daily_loss_result["message"])
                violations.append(RiskViolationType.DAILY_LOSS)
                risk_score += 0.3
            elif daily_loss_result["warning"]:
                warnings.append(daily_loss_result["message"])
                risk_score += 0.1
            
            # Validate daily trade limits
            daily_trades_result = await self._validate_daily_trades(risk_profile, account_id)
            if not daily_trades_result["approved"]:
                errors.append(daily_trades_result["message"])
                violations.append(RiskViolationType.DAILY_TRADES)
                risk_score += 0.2
            elif daily_trades_result["warning"]:
                warnings.append(daily_trades_result["warning"])
                risk_score += 0.05
            
            # Validate Greeks exposure
            greeks_result = await self._validate_greeks_exposure(risk_profile, account_id, order_data)
            if not greeks_result["approved"]:
                errors.append(greeks_result["message"])
                violations.append(RiskViolationType.GREEKS_EXPOSURE)
                risk_score += 0.2
            elif greeks_result["warning"]:
                warnings.append(greeks_result["message"])
                risk_score += 0.1
            
            # Validate allowed strategies
            strategy_result = await self._validate_strategy(risk_profile, order_data)
            if not strategy_result["approved"]:
                errors.append(strategy_result["message"])
                violations.append(RiskViolationType.STRATEGY_NOT_ALLOWED)
                risk_score += 0.5
            
            # Determine approval
            approved = len(errors) == 0
            
            # Emergency override handling
            if emergency_override and not approved:
                approved = True
                warnings.append("Emergency override applied")
            
            return RiskValidationResult(
                approved=approved,
                risk_score=min(risk_score, 1.0),
                warnings=warnings,
                errors=errors,
                violations=violations,
                override_reason="Emergency authorization" if emergency_override else None
            )
            
        except Exception as e:
            logger.error(f"Risk validation error: {str(e)}")
            return RiskValidationResult(
                approved=False,
                risk_score=1.0,
                warnings=[],
                errors=[f"Risk validation error: {str(e)}"],
                violations=[RiskViolationType.EMERGENCY_STOP]
            )
    
    async def check_position_limits(self, account_id: str, additional_size: float) -> Dict[str, Any]:
        """
        Check if additional position size would exceed limits.
        
        Args:
            account_id: Trading account ID
            additional_size: Additional position size to check
            
        Returns:
            Position limits check result
        """
        try:
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return {"approved": False, "message": "No risk profile found"}
            
            # Get current total position size
            current_size = await self._get_current_position_size(account_id)
            new_total_size = current_size + additional_size
            
            if new_total_size > risk_profile.max_position_size:
                return {
                    "approved": False,
                    "message": f"Position size limit exceeded: {new_total_size} > {risk_profile.max_position_size}",
                    "current_size": current_size,
                    "new_total_size": new_total_size,
                    "limit": float(risk_profile.max_position_size)
                }
            
            return {
                "approved": True,
                "message": "Position size within limits",
                "current_size": current_size,
                "new_total_size": new_total_size,
                "limit": float(risk_profile.max_position_size)
            }
            
        except Exception as e:
            logger.error(f"Position limits check error: {str(e)}")
            return {"approved": False, "message": f"Error checking position limits: {str(e)}"}
    
    async def check_daily_loss_limits(self, account_id: str, potential_loss: float) -> Dict[str, Any]:
        """
        Check if potential loss would exceed daily limits.
        
        Args:
            account_id: Trading account ID
            potential_loss: Potential loss amount
            
        Returns:
            Daily loss limits check result
        """
        try:
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return {"approved": False, "message": "No risk profile found"}
            
            # Get current daily loss
            current_loss = await self._get_current_daily_loss(account_id)
            new_total_loss = current_loss + potential_loss
            
            if new_total_loss > risk_profile.max_daily_loss:
                return {
                    "approved": False,
                    "message": f"Daily loss limit exceeded: {new_total_loss} > {risk_profile.max_daily_loss}",
                    "current_loss": current_loss,
                    "new_total_loss": new_total_loss,
                    "limit": float(risk_profile.max_daily_loss)
                }
            
            return {
                "approved": True,
                "message": "Daily loss within limits",
                "current_loss": current_loss,
                "new_total_loss": new_total_loss,
                "limit": float(risk_profile.max_daily_loss)
            }
            
        except Exception as e:
            logger.error(f"Daily loss limits check error: {str(e)}")
            return {"approved": False, "message": f"Error checking daily loss limits: {str(e)}"}
    
    async def check_portfolio_risk(self, account_id: str, additional_risk: float) -> Dict[str, Any]:
        """
        Check if additional risk would exceed portfolio risk limits.
        
        Args:
            account_id: Trading account ID
            additional_risk: Additional risk amount
            
        Returns:
            Portfolio risk check result
        """
        try:
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return {"approved": False, "message": "No risk profile found"}
            
            # Get current portfolio risk
            current_risk = await self._get_current_portfolio_risk(account_id)
            new_total_risk = current_risk + additional_risk
            
            # Calculate portfolio value for risk percentage
            portfolio_value = await self._get_portfolio_value(account_id)
            max_risk_amount = portfolio_value * float(risk_profile.max_portfolio_risk)
            
            if new_total_risk > max_risk_amount:
                return {
                    "approved": False,
                    "message": f"Portfolio risk limit exceeded: {new_total_risk} > {max_risk_amount}",
                    "current_risk": current_risk,
                    "new_total_risk": new_total_risk,
                    "max_risk_amount": max_risk_amount,
                    "portfolio_value": portfolio_value
                }
            
            return {
                "approved": True,
                "message": "Portfolio risk within limits",
                "current_risk": current_risk,
                "new_total_risk": new_total_risk,
                "max_risk_amount": max_risk_amount,
                "portfolio_value": portfolio_value
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk check error: {str(e)}")
            return {"approved": False, "message": f"Error checking portfolio risk: {str(e)}"}
    
    async def activate_emergency_stop(self, account_id: str, reason: str, activated_by: str) -> Dict[str, Any]:
        """
        Activate emergency stop for an account.
        
        Args:
            account_id: Trading account ID
            reason: Reason for emergency stop
            activated_by: User who activated emergency stop
            
        Returns:
            Emergency stop activation result
        """
        try:
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return {"success": False, "message": "No risk profile found"}
            
            # Update risk profile
            risk_profile.emergency_stop_active = True
            risk_profile.emergency_stop_reason = reason
            risk_profile.emergency_stop_activated_at = datetime.utcnow()
            
            await self.db_session.commit()
            
            logger.warning(f"Emergency stop activated for account {account_id}: {reason}")
            
            return {
                "success": True,
                "message": "Emergency stop activated",
                "account_id": account_id,
                "reason": reason,
                "activated_by": activated_by,
                "activated_at": risk_profile.emergency_stop_activated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Emergency stop activation error: {str(e)}")
            return {"success": False, "message": f"Error activating emergency stop: {str(e)}"}
    
    async def deactivate_emergency_stop(self, account_id: str, deactivated_by: str) -> Dict[str, Any]:
        """
        Deactivate emergency stop for an account.
        
        Args:
            account_id: Trading account ID
            deactivated_by: User who deactivated emergency stop
            
        Returns:
            Emergency stop deactivation result
        """
        try:
            risk_profile = await self._get_risk_profile(account_id)
            if not risk_profile:
                return {"success": False, "message": "No risk profile found"}
            
            # Update risk profile
            risk_profile.emergency_stop_active = False
            risk_profile.emergency_stop_reason = None
            risk_profile.emergency_stop_activated_at = None
            
            await self.db_session.commit()
            
            logger.info(f"Emergency stop deactivated for account {account_id} by {deactivated_by}")
            
            return {
                "success": True,
                "message": "Emergency stop deactivated",
                "account_id": account_id,
                "deactivated_by": deactivated_by,
                "deactivated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Emergency stop deactivation error: {str(e)}")
            return {"success": False, "message": f"Error deactivating emergency stop: {str(e)}"}
    
    # Private helper methods
    
    async def _get_risk_profile(self, account_id: str) -> Optional[RiskProfile]:
        """Get risk profile for account."""
        try:
            result = await self.db_session.execute(
                select(RiskProfile).where(RiskProfile.account_id == account_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting risk profile: {str(e)}")
            return None
    
    async def _validate_position_size(self, risk_profile: RiskProfile, order_data: OrderRiskData) -> Dict[str, Any]:
        """Validate position size against limits."""
        current_size = await self._get_current_position_size(str(risk_profile.account_id))
        new_total_size = current_size + order_data.position_size
        
        # Convert Decimal to float for comparison
        max_position_size = float(risk_profile.max_position_size)
        
        if new_total_size > max_position_size:
            return {
                "approved": False,
                "message": f"Position size limit exceeded: {new_total_size} > {max_position_size}"
            }
        elif new_total_size > max_position_size * 0.9:
            return {
                "approved": True,
                "warning": f"Approaching position size limit: {new_total_size}/{max_position_size}"
            }
        
        return {"approved": True, "warning": None}
    
    async def _validate_portfolio_risk(self, risk_profile: RiskProfile, account_id: str, order_data: OrderRiskData) -> Dict[str, Any]:
        """Validate portfolio risk against limits."""
        portfolio_value = await self._get_portfolio_value(account_id)
        current_risk = await self._get_current_portfolio_risk(account_id)
        new_total_risk = current_risk + order_data.estimated_risk
        
        # Convert Decimal to float for calculation
        max_risk_amount = portfolio_value * float(risk_profile.max_portfolio_risk)
        
        if new_total_risk > max_risk_amount:
            return {
                "approved": False,
                "message": f"Portfolio risk limit exceeded: {new_total_risk} > {max_risk_amount}"
            }
        elif new_total_risk > max_risk_amount * 0.9:
            return {
                "approved": True,
                "warning": f"Approaching portfolio risk limit: {new_total_risk}/{max_risk_amount}"
            }
        
        return {"approved": True, "warning": None}
    
    async def _validate_daily_loss(self, risk_profile: RiskProfile, account_id: str, order_data: OrderRiskData) -> Dict[str, Any]:
        """Validate daily loss against limits."""
        current_loss = await self._get_current_daily_loss(account_id)
        potential_loss = order_data.estimated_risk
        new_total_loss = current_loss + potential_loss
        
        # Convert Decimal to float for comparison
        max_daily_loss = float(risk_profile.max_daily_loss)
        
        if new_total_loss > max_daily_loss:
            return {
                "approved": False,
                "message": f"Daily loss limit exceeded: {new_total_loss} > {max_daily_loss}"
            }
        elif new_total_loss > max_daily_loss * 0.9:
            return {
                "approved": True,
                "warning": f"Approaching daily loss limit: {new_total_loss}/{max_daily_loss}"
            }
        
        return {"approved": True, "warning": None}
    
    async def _validate_daily_trades(self, risk_profile: RiskProfile, account_id: str) -> Dict[str, Any]:
        """Validate daily trade count against limits."""
        current_trades = await self._get_current_daily_trades(account_id)
        
        # Convert Decimal to int for comparison  
        max_daily_trades = int(risk_profile.max_daily_trades)
        
        if current_trades >= max_daily_trades:
            return {
                "approved": False,
                "message": f"Daily trade limit exceeded: {current_trades} >= {max_daily_trades}"
            }
        elif current_trades >= max_daily_trades * 0.9:
            return {
                "approved": True,
                "warning": f"Approaching daily trade limit: {current_trades}/{risk_profile.max_daily_trades}"
            }
        
        return {"approved": True, "warning": None}
    
    async def _validate_greeks_exposure(self, risk_profile: RiskProfile, account_id: str, order_data: OrderRiskData) -> Dict[str, Any]:
        """Validate Greeks exposure against limits."""
        try:
            max_greeks = json.loads(risk_profile.max_greeks_exposure)
            current_greeks = await self._get_current_greeks_exposure(account_id)
            
            violations = []
            for greek, limit in max_greeks.items():
                if greek in order_data.greeks:
                    new_exposure = current_greeks.get(greek, 0) + order_data.greeks[greek]
                    if abs(new_exposure) > abs(limit):
                        violations.append(f"{greek} exposure limit exceeded: {new_exposure} > {limit}")
            
            if violations:
                return {
                    "approved": False,
                    "message": "; ".join(violations)
                }
            
            return {"approved": True, "warning": None}
            
        except Exception as e:
            logger.error(f"Error validating Greeks exposure: {str(e)}")
            return {"approved": True, "warning": None}
    
    async def _validate_strategy(self, risk_profile: RiskProfile, order_data: OrderRiskData) -> Dict[str, Any]:
        """Validate if strategy is allowed."""
        try:
            allowed_strategies = json.loads(risk_profile.allowed_strategies)
            if order_data.strategy not in allowed_strategies:
                return {
                    "approved": False,
                    "message": f"Strategy {order_data.strategy} not allowed. Allowed strategies: {allowed_strategies}"
                }
            
            return {"approved": True, "warning": None}
            
        except Exception as e:
            logger.error(f"Error validating strategy: {str(e)}")
            return {"approved": True, "warning": None}
    
    async def _get_current_position_size(self, account_id: str) -> float:
        """Get current total position size for account."""
        try:
            result = await self.db_session.execute(
                select(func.sum(LivePosition.quantity * LivePosition.average_price))
                .where(LivePosition.account_id == account_id)
                .where(LivePosition.status == "OPEN")
            )
            return float(result.scalar() or 0)
        except Exception:
            return 0.0
    
    async def _get_current_daily_loss(self, account_id: str) -> float:
        """Get current daily loss for account."""
        try:
            today = datetime.utcnow().date()
            result = await self.db_session.execute(
                select(func.sum(LiveTrade.total_amount))
                .where(LiveTrade.account_id == account_id)
                .where(LiveTrade.status == "FILLED")
                .where(func.date(LiveTrade.filled_at) == today)
                .where(LiveTrade.total_amount < 0)  # Only losses
            )
            return abs(float(result.scalar() or 0))
        except Exception:
            return 0.0
    
    async def _get_current_daily_trades(self, account_id: str) -> int:
        """Get current daily trade count for account."""
        try:
            today = datetime.utcnow().date()
            result = await self.db_session.execute(
                select(func.count(LiveTrade.trade_id))
                .where(LiveTrade.account_id == account_id)
                .where(func.date(LiveTrade.created_at) == today)
            )
            return int(result.scalar() or 0)
        except Exception:
            return 0
    
    async def _get_current_portfolio_risk(self, account_id: str) -> float:
        """Get current portfolio risk for account."""
        try:
            result = await self.db_session.execute(
                select(func.sum(LivePosition.unrealized_pnl))
                .where(LivePosition.account_id == account_id)
                .where(LivePosition.status == "OPEN")
                .where(LivePosition.unrealized_pnl < 0)  # Only negative P&L (risk)
            )
            return abs(float(result.scalar() or 0))
        except Exception:
            return 0.0
    
    async def _get_portfolio_value(self, account_id: str) -> float:
        """Get current portfolio value for account."""
        try:
            # This would typically come from account balance
            # For now, return a default value
            return 10000.0
        except Exception:
            return 10000.0
    
    async def _get_current_greeks_exposure(self, account_id: str) -> Dict[str, float]:
        """Get current Greeks exposure for account."""
        try:
            # This would aggregate Greeks from all open positions
            # For now, return empty dict
            return {}
        except Exception:
            return {}
