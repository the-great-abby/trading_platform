"""
Risk Limits Manager Service

Provides risk limit configuration and management capabilities for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.risk_limits import RiskLimits, LimitType, EnforcementAction


logger = logging.getLogger(__name__)


class RiskLimitsManager:
    """
    Risk limits configuration and management service.
    
    Provides functionality to configure, update, and manage risk limits
    for portfolios to enforce risk management policies.
    """
    
    def __init__(self):
        """Initialize risk limits manager."""
        self.limits_cache = {}
        self.limits_history = {}
    
    def configure_risk_limits(
        self,
        portfolio_id: str,
        limits_configuration: List[Dict[str, Any]],
        created_by: str = "system"
    ) -> List[RiskLimits]:
        """
        Configure risk limits for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            limits_configuration: List of limit configurations
            created_by: User or system that created the limits
            
        Returns:
            List of configured RiskLimits objects
        """
        logger.info(f"Configuring risk limits for portfolio {portfolio_id}")
        
        # Validate inputs
        self._validate_limits_configuration(portfolio_id, limits_configuration)
        
        configured_limits = []
        
        for limit_config in limits_configuration:
            # Create risk limit object
            risk_limit = RiskLimits(
                portfolio_id=portfolio_id,
                limit_type=LimitType(limit_config["limit_type"]),
                limit_value=limit_config["limit_value"],
                limit_unit=limit_config["limit_unit"],
                breach_threshold=limit_config.get("breach_threshold", limit_config["limit_value"]),
                warning_threshold=limit_config.get("warning_threshold", limit_config["limit_value"] * 0.8),
                enforcement_action=EnforcementAction(limit_config["enforcement_action"]),
                limit_description=limit_config.get("limit_description", f"{limit_config['limit_type']} limit"),
                created_by=created_by
            )
            
            configured_limits.append(risk_limit)
        
        # Store in cache
        self.limits_cache[portfolio_id] = configured_limits
        
        # Store in history
        if portfolio_id not in self.limits_history:
            self.limits_history[portfolio_id] = []
        self.limits_history[portfolio_id].append({
            "timestamp": datetime.utcnow(),
            "action": "configure",
            "limits": [limit.to_dict() for limit in configured_limits],
            "created_by": created_by
        })
        
        logger.info(f"Configured {len(configured_limits)} risk limits for portfolio {portfolio_id}")
        return configured_limits
    
    def update_risk_limit(
        self,
        portfolio_id: str,
        limit_id: str,
        updates: Dict[str, Any],
        updated_by: str = "system"
    ) -> Optional[RiskLimits]:
        """
        Update an existing risk limit.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_id: Limit identifier
            updates: Dictionary of updates to apply
            updated_by: User or system that updated the limit
            
        Returns:
            Updated RiskLimits object or None if not found
        """
        logger.info(f"Updating risk limit {limit_id} for portfolio {portfolio_id}")
        
        # Find the limit
        limits = self.limits_cache.get(portfolio_id, [])
        target_limit = None
        
        for limit in limits:
            if str(limit.risk_limits_id) == limit_id:
                target_limit = limit
                break
        
        if not target_limit:
            logger.warning(f"Risk limit {limit_id} not found for portfolio {portfolio_id}")
            return None
        
        # Store original values for history
        original_limit = target_limit.to_dict()
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(target_limit, field):
                if field == "limit_type":
                    setattr(target_limit, field, LimitType(value))
                elif field == "enforcement_action":
                    setattr(target_limit, field, EnforcementAction(value))
                else:
                    setattr(target_limit, field, value)
        
        # Update timestamp
        target_limit.updated_at = datetime.utcnow()
        
        # Store in history
        self.limits_history[portfolio_id].append({
            "timestamp": datetime.utcnow(),
            "action": "update",
            "limit_id": limit_id,
            "original": original_limit,
            "updated": target_limit.to_dict(),
            "updated_by": updated_by
        })
        
        logger.info(f"Updated risk limit {limit_id} for portfolio {portfolio_id}")
        return target_limit
    
    def get_risk_limits(
        self,
        portfolio_id: str,
        active_only: bool = False
    ) -> List[RiskLimits]:
        """
        Get risk limits for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            active_only: Whether to return only active limits
            
        Returns:
            List of RiskLimits objects
        """
        limits = self.limits_cache.get(portfolio_id, [])
        
        if active_only:
            limits = [limit for limit in limits if limit.is_active]
        
        return limits
    
    def get_risk_limit(
        self,
        portfolio_id: str,
        limit_id: str
    ) -> Optional[RiskLimits]:
        """
        Get a specific risk limit.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_id: Limit identifier
            
        Returns:
            RiskLimits object or None if not found
        """
        limits = self.limits_cache.get(portfolio_id, [])
        
        for limit in limits:
            if str(limit.risk_limits_id) == limit_id:
                return limit
        
        return None
    
    def deactivate_risk_limit(
        self,
        portfolio_id: str,
        limit_id: str,
        deactivated_by: str = "system"
    ) -> bool:
        """
        Deactivate a risk limit.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_id: Limit identifier
            deactivated_by: User or system that deactivated the limit
            
        Returns:
            True if deactivated successfully, False otherwise
        """
        logger.info(f"Deactivating risk limit {limit_id} for portfolio {portfolio_id}")
        
        limit = self.get_risk_limit(portfolio_id, limit_id)
        if not limit:
            logger.warning(f"Risk limit {limit_id} not found for portfolio {portfolio_id}")
            return False
        
        # Store in history
        self.limits_history[portfolio_id].append({
            "timestamp": datetime.utcnow(),
            "action": "deactivate",
            "limit_id": limit_id,
            "limit": limit.to_dict(),
            "deactivated_by": deactivated_by
        })
        
        # Deactivate the limit
        limit.deactivate()
        
        logger.info(f"Deactivated risk limit {limit_id} for portfolio {portfolio_id}")
        return True
    
    def activate_risk_limit(
        self,
        portfolio_id: str,
        limit_id: str,
        activated_by: str = "system"
    ) -> bool:
        """
        Activate a risk limit.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_id: Limit identifier
            activated_by: User or system that activated the limit
            
        Returns:
            True if activated successfully, False otherwise
        """
        logger.info(f"Activating risk limit {limit_id} for portfolio {portfolio_id}")
        
        limit = self.get_risk_limit(portfolio_id, limit_id)
        if not limit:
            logger.warning(f"Risk limit {limit_id} not found for portfolio {portfolio_id}")
            return False
        
        # Store in history
        self.limits_history[portfolio_id].append({
            "timestamp": datetime.utcnow(),
            "action": "activate",
            "limit_id": limit_id,
            "limit": limit.to_dict(),
            "activated_by": activated_by
        })
        
        # Activate the limit
        limit.activate()
        
        logger.info(f"Activated risk limit {limit_id} for portfolio {portfolio_id}")
        return True
    
    def reset_breach_count(
        self,
        portfolio_id: str,
        limit_id: str,
        reset_by: str = "system"
    ) -> bool:
        """
        Reset breach count for a risk limit.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_id: Limit identifier
            reset_by: User or system that reset the breach count
            
        Returns:
            True if reset successfully, False otherwise
        """
        logger.info(f"Resetting breach count for risk limit {limit_id} for portfolio {portfolio_id}")
        
        limit = self.get_risk_limit(portfolio_id, limit_id)
        if not limit:
            logger.warning(f"Risk limit {limit_id} not found for portfolio {portfolio_id}")
            return False
        
        # Store in history
        self.limits_history[portfolio_id].append({
            "timestamp": datetime.utcnow(),
            "action": "reset_breach_count",
            "limit_id": limit_id,
            "previous_breach_count": limit.breach_count,
            "reset_by": reset_by
        })
        
        # Reset breach count
        limit.reset_breach_count()
        
        logger.info(f"Reset breach count for risk limit {limit_id} for portfolio {portfolio_id}")
        return True
    
    def get_limits_status_summary(
        self,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of risk limits status for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with limits status summary
        """
        limits = self.limits_cache.get(portfolio_id, [])
        
        if not limits:
            return {
                "portfolio_id": portfolio_id,
                "total_limits": 0,
                "active_limits": 0,
                "inactive_limits": 0,
                "limits_status": {}
            }
        
        limits_status = {}
        total_breaches = 0
        
        for limit in limits:
            status = limit.check_limit_status()
            limits_status[limit.limit_type.value] = status
            total_breaches += limit.breach_count
        
        return {
            "portfolio_id": portfolio_id,
            "total_limits": len(limits),
            "active_limits": len([l for l in limits if l.is_active]),
            "inactive_limits": len([l for l in limits if not l.is_active]),
            "total_breaches": total_breaches,
            "limits_status": limits_status
        }
    
    def get_limits_history(
        self,
        portfolio_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get risk limits configuration history for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
        """
        history = self.limits_history.get(portfolio_id, [])
        
        # Sort by timestamp (most recent first) and limit results
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return history[:limit]
    
    def validate_limit_configuration(
        self,
        limit_config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate a risk limit configuration.
        
        Args:
            limit_config: Limit configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ["limit_type", "limit_value", "limit_unit", "enforcement_action"]
        for field in required_fields:
            if field not in limit_config:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return errors
        
        # Validate limit type
        try:
            LimitType(limit_config["limit_type"])
        except ValueError:
            errors.append(f"Invalid limit type: {limit_config['limit_type']}")
        
        # Validate enforcement action
        try:
            EnforcementAction(limit_config["enforcement_action"])
        except ValueError:
            errors.append(f"Invalid enforcement action: {limit_config['enforcement_action']}")
        
        # Validate limit value
        try:
            limit_value = float(limit_config["limit_value"])
            if limit_value <= 0:
                errors.append("Limit value must be positive")
        except (ValueError, TypeError):
            errors.append("Limit value must be a valid number")
        
        # Validate thresholds if provided
        if "breach_threshold" in limit_config:
            try:
                breach_threshold = float(limit_config["breach_threshold"])
                if breach_threshold <= 0:
                    errors.append("Breach threshold must be positive")
            except (ValueError, TypeError):
                errors.append("Breach threshold must be a valid number")
        
        if "warning_threshold" in limit_config:
            try:
                warning_threshold = float(limit_config["warning_threshold"])
                if warning_threshold <= 0:
                    errors.append("Warning threshold must be positive")
                
                # Check threshold ordering
                if "breach_threshold" in limit_config:
                    breach_threshold = float(limit_config["breach_threshold"])
                    if warning_threshold >= breach_threshold:
                        errors.append("Warning threshold should be less than breach threshold")
            except (ValueError, TypeError):
                errors.append("Warning threshold must be a valid number")
        
        return errors
    
    def get_default_limit_configurations(self) -> List[Dict[str, Any]]:
        """Get default risk limit configurations."""
        return [
            {
                "limit_type": "position_size",
                "limit_value": 0.10,
                "limit_unit": "percentage",
                "enforcement_action": "alert",
                "limit_description": "Maximum position size as percentage of portfolio",
                "breach_threshold": 0.10,
                "warning_threshold": 0.08
            },
            {
                "limit_type": "daily_loss",
                "limit_value": 1000.0,
                "limit_unit": "dollars",
                "enforcement_action": "halt_trading",
                "limit_description": "Maximum daily loss in dollars",
                "breach_threshold": 1000.0,
                "warning_threshold": 800.0
            },
            {
                "limit_type": "sector_concentration",
                "limit_value": 0.30,
                "limit_unit": "percentage",
                "enforcement_action": "alert",
                "limit_description": "Maximum sector concentration as percentage of portfolio",
                "breach_threshold": 0.30,
                "warning_threshold": 0.25
            },
            {
                "limit_type": "var_limit",
                "limit_value": 5000.0,
                "limit_unit": "dollars",
                "enforcement_action": "reduce_position",
                "limit_description": "Maximum Value at Risk (95% confidence) in dollars",
                "breach_threshold": 5000.0,
                "warning_threshold": 4000.0
            },
            {
                "limit_type": "volatility_limit",
                "limit_value": 0.25,
                "limit_unit": "percentage",
                "enforcement_action": "alert",
                "limit_description": "Maximum portfolio volatility as percentage",
                "breach_threshold": 0.25,
                "warning_threshold": 0.20
            }
        ]
    
    def _validate_limits_configuration(
        self,
        portfolio_id: str,
        limits_configuration: List[Dict[str, Any]]
    ) -> None:
        """Validate limits configuration input."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not limits_configuration:
            raise ValueError("Limits configuration cannot be empty")
        
        if not isinstance(limits_configuration, list):
            raise ValueError("Limits configuration must be a list")
        
        # Validate each limit configuration
        for i, limit_config in enumerate(limits_configuration):
            if not isinstance(limit_config, dict):
                raise ValueError(f"Limit configuration {i} must be a dictionary")
            
            errors = self.validate_limit_configuration(limit_config)
            if errors:
                raise ValueError(f"Limit configuration {i} validation errors: {', '.join(errors)}")
    
    def clear_limits_cache(self, portfolio_id: Optional[str] = None) -> None:
        """Clear limits cache for a portfolio or all portfolios."""
        if portfolio_id:
            if portfolio_id in self.limits_cache:
                del self.limits_cache[portfolio_id]
            logger.info(f"Cleared limits cache for portfolio {portfolio_id}")
        else:
            self.limits_cache.clear()
            logger.info("Cleared all limits cache")



