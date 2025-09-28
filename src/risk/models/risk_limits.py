"""
Risk Limits Data Model

Represents configurable risk thresholds and limits for the comprehensive
risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4, UUID
from enum import Enum


class LimitType(Enum):
    """Types of risk limits."""
    POSITION_SIZE = "position_size"
    DAILY_LOSS = "daily_loss"
    SECTOR_CONCENTRATION = "sector_concentration"
    VAR_LIMIT = "var_limit"
    VOLATILITY_LIMIT = "volatility_limit"


class EnforcementAction(Enum):
    """Actions to take when limits are breached."""
    ALERT = "alert"
    REDUCE_POSITION = "reduce_position"
    HALT_TRADING = "halt_trading"


@dataclass
class RiskLimits:
    """
    Configurable risk thresholds and limits.
    
    This model represents risk limits that can be configured for a portfolio
    to enforce risk management policies and prevent excessive risk taking.
    """
    
    # Primary key
    risk_limits_id: UUID = field(default_factory=uuid4)
    
    # Portfolio reference
    portfolio_id: UUID = field()
    
    # Limit configuration
    limit_type: LimitType = field()
    limit_value: float = field()
    limit_unit: str = field()
    
    # Current state
    current_value: float = field(default=0.0)
    breach_threshold: float = field()
    warning_threshold: float = field()
    
    # Status and enforcement
    is_active: bool = field(default=True)
    enforcement_action: EnforcementAction = field()
    
    # Breach tracking
    last_breach_timestamp: Optional[datetime] = field(default=None)
    breach_count: int = field(default=0)
    
    # Metadata
    limit_description: str = field()
    created_by: str = field()
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate risk limits data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if not isinstance(self.limit_type, LimitType):
            raise ValueError("Limit type must be a valid LimitType")
        
        if not isinstance(self.enforcement_action, EnforcementAction):
            raise ValueError("Enforcement action must be a valid EnforcementAction")
        
        if self.limit_value <= 0:
            raise ValueError("Limit value must be positive")
        
        if self.current_value < 0:
            raise ValueError("Current value must be non-negative")
        
        if self.breach_threshold <= 0:
            raise ValueError("Breach threshold must be positive")
        
        if self.warning_threshold <= 0:
            raise ValueError("Warning threshold must be positive")
        
        if self.breach_count < 0:
            raise ValueError("Breach count must be non-negative")
        
        if not self.limit_description:
            raise ValueError("Limit description is required")
        
        if not self.created_by:
            raise ValueError("Created by field is required")
        
        # Validate threshold ordering
        if self.warning_threshold >= self.breach_threshold:
            raise ValueError("Warning threshold should be less than breach threshold")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RiskLimits to dictionary."""
        return {
            "risk_limits_id": str(self.risk_limits_id),
            "portfolio_id": str(self.portfolio_id),
            "limit_type": self.limit_type.value,
            "limit_value": self.limit_value,
            "limit_unit": self.limit_unit,
            "current_value": self.current_value,
            "breach_threshold": self.breach_threshold,
            "warning_threshold": self.warning_threshold,
            "is_active": self.is_active,
            "enforcement_action": self.enforcement_action.value,
            "last_breach_timestamp": self.last_breach_timestamp.isoformat() if self.last_breach_timestamp else None,
            "breach_count": self.breach_count,
            "limit_description": self.limit_description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskLimits":
        """Create RiskLimits from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("risk_limits_id"), str):
            data["risk_limits_id"] = UUID(data["risk_limits_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        
        # Convert enum strings back to enum objects
        if isinstance(data.get("limit_type"), str):
            data["limit_type"] = LimitType(data["limit_type"])
        if isinstance(data.get("enforcement_action"), str):
            data["enforcement_action"] = EnforcementAction(data["enforcement_action"])
        
        # Convert datetime strings back to datetime objects
        if data.get("last_breach_timestamp") and isinstance(data["last_breach_timestamp"], str):
            data["last_breach_timestamp"] = datetime.fromisoformat(data["last_breach_timestamp"].replace("Z", "+00:00"))
        for field in ["created_at", "updated_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def check_limit_status(self) -> Dict[str, Any]:
        """Check the current status of the risk limit."""
        utilization_pct = (self.current_value / self.limit_value) * 100
        warning_pct = (self.warning_threshold / self.limit_value) * 100
        breach_pct = (self.breach_threshold / self.limit_value) * 100
        
        if self.current_value >= self.breach_threshold:
            status = "breach"
            severity = "high"
        elif self.current_value >= self.warning_threshold:
            status = "warning"
            severity = "medium"
        else:
            status = "within_limits"
            severity = "low"
        
        return {
            "limit_id": str(self.risk_limits_id),
            "limit_type": self.limit_type.value,
            "limit_description": self.limit_description,
            "status": status,
            "severity": severity,
            "current_value": self.current_value,
            "limit_value": self.limit_value,
            "utilization_pct": utilization_pct,
            "warning_threshold": self.warning_threshold,
            "breach_threshold": self.breach_threshold,
            "enforcement_action": self.enforcement_action.value,
            "is_active": self.is_active,
            "breach_count": self.breach_count,
            "last_breach_timestamp": self.last_breach_timestamp.isoformat() if self.last_breach_timestamp else None
        }
    
    def update_current_value(self, new_value: float) -> Dict[str, Any]:
        """Update the current value and check for breaches."""
        old_value = self.current_value
        self.current_value = new_value
        self.updated_at = datetime.utcnow()
        
        status = self.check_limit_status()
        
        # Check if this update caused a breach
        if new_value >= self.breach_threshold and old_value < self.breach_threshold:
            self.breach_count += 1
            self.last_breach_timestamp = datetime.utcnow()
            status["breach_detected"] = True
            status["breach_count"] = self.breach_count
        else:
            status["breach_detected"] = False
        
        return status
    
    def is_breached(self) -> bool:
        """Check if the limit is currently breached."""
        return self.current_value >= self.breach_threshold and self.is_active
    
    def is_warning(self) -> bool:
        """Check if the limit is in warning state."""
        return (self.current_value >= self.warning_threshold and 
                self.current_value < self.breach_threshold and 
                self.is_active)
    
    def is_within_limits(self) -> bool:
        """Check if the limit is within acceptable bounds."""
        return self.current_value < self.warning_threshold and self.is_active
    
    def get_utilization_percentage(self) -> float:
        """Get the current utilization as a percentage of the limit."""
        return (self.current_value / self.limit_value) * 100
    
    def get_remaining_capacity(self) -> float:
        """Get the remaining capacity before hitting the limit."""
        return max(0, self.limit_value - self.current_value)
    
    def deactivate(self) -> None:
        """Deactivate the risk limit."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the risk limit."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def reset_breach_count(self) -> None:
        """Reset the breach count."""
        self.breach_count = 0
        self.last_breach_timestamp = None
        self.updated_at = datetime.utcnow()
    
    def get_limit_summary(self) -> Dict[str, Any]:
        """Get a summary of the risk limit configuration."""
        return {
            "limit_type": self.limit_type.value,
            "limit_description": self.limit_description,
            "limit_value": self.limit_value,
            "limit_unit": self.limit_unit,
            "current_value": self.current_value,
            "utilization_pct": self.get_utilization_percentage(),
            "status": self.check_limit_status()["status"],
            "enforcement_action": self.enforcement_action.value,
            "is_active": self.is_active,
            "breach_count": self.breach_count
        }
    
    def __str__(self) -> str:
        """String representation of RiskLimits."""
        return (f"RiskLimits(type={self.limit_type.value}, "
                f"limit={self.limit_value:.2f}, "
                f"current={self.current_value:.2f}, "
                f"status={self.check_limit_status()['status']})")
    
    def __repr__(self) -> str:
        """Detailed string representation of RiskLimits."""
        return (f"RiskLimits("
                f"risk_limits_id={self.risk_limits_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"limit_type={self.limit_type.value}, "
                f"limit_value={self.limit_value}, "
                f"current_value={self.current_value}, "
                f"is_active={self.is_active})")



