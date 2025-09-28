"""
Risk Alert Data Model

Represents risk limit breach notifications and alerts for the comprehensive
risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4, UUID
from enum import Enum


class AlertType(Enum):
    """Types of risk alerts."""
    WARNING = "warning"
    BREACH = "breach"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Severity levels for risk alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status of risk alerts."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class RiskAlert:
    """
    Risk limit breach notifications and alerts.
    
    This model represents alerts generated when risk limits are breached
    or when risk metrics exceed predefined thresholds.
    """
    
    # Primary key
    risk_alert_id: UUID = field(default_factory=uuid4)
    
    # References
    portfolio_id: UUID = field()
    risk_limits_id: UUID = field()
    
    # Alert details
    alert_timestamp: datetime = field(default_factory=datetime.utcnow)
    alert_type: AlertType = field()
    alert_severity: AlertSeverity = field()
    
    # Limit information
    limit_name: str = field()
    limit_value: float = field()
    current_value: float = field()
    breach_percentage: float = field()
    
    # Alert content
    alert_message: str = field()
    recommended_action: str = field()
    
    # Status tracking
    alert_status: AlertStatus = field(default=AlertStatus.ACTIVE)
    acknowledged_by: Optional[str] = field(default=None)
    acknowledged_at: Optional[datetime] = field(default=None)
    resolved_at: Optional[datetime] = field(default=None)
    
    # Escalation
    escalation_level: int = field(default=0)
    notification_sent: bool = field(default=False)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate risk alert data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if not isinstance(self.risk_limits_id, UUID):
            raise ValueError("Risk limits ID must be a valid UUID")
        
        if not isinstance(self.alert_type, AlertType):
            raise ValueError("Alert type must be a valid AlertType")
        
        if not isinstance(self.alert_severity, AlertSeverity):
            raise ValueError("Alert severity must be a valid AlertSeverity")
        
        if not isinstance(self.alert_status, AlertStatus):
            raise ValueError("Alert status must be a valid AlertStatus")
        
        if not self.limit_name:
            raise ValueError("Limit name is required")
        
        if self.limit_value <= 0:
            raise ValueError("Limit value must be positive")
        
        if self.current_value < 0:
            raise ValueError("Current value must be non-negative")
        
        if self.breach_percentage < 0:
            raise ValueError("Breach percentage must be non-negative")
        
        if not self.alert_message:
            raise ValueError("Alert message is required")
        
        if not self.recommended_action:
            raise ValueError("Recommended action is required")
        
        if not (0 <= self.escalation_level <= 5):
            raise ValueError("Escalation level must be between 0 and 5")
        
        if self.acknowledged_at and not self.acknowledged_by:
            raise ValueError("Acknowledged by is required when acknowledged_at is set")
        
        if self.acknowledged_by and not self.acknowledged_at:
            raise ValueError("Acknowledged at is required when acknowledged_by is set")
        
        if self.acknowledged_at and self.acknowledged_at < self.alert_timestamp:
            raise ValueError("Acknowledged timestamp must be after alert timestamp")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RiskAlert to dictionary."""
        return {
            "risk_alert_id": str(self.risk_alert_id),
            "portfolio_id": str(self.portfolio_id),
            "risk_limits_id": str(self.risk_limits_id),
            "alert_timestamp": self.alert_timestamp.isoformat(),
            "alert_type": self.alert_type.value,
            "alert_severity": self.alert_severity.value,
            "limit_name": self.limit_name,
            "limit_value": self.limit_value,
            "current_value": self.current_value,
            "breach_percentage": self.breach_percentage,
            "alert_message": self.alert_message,
            "recommended_action": self.recommended_action,
            "alert_status": self.alert_status.value,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalation_level": self.escalation_level,
            "notification_sent": self.notification_sent,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskAlert":
        """Create RiskAlert from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("risk_alert_id"), str):
            data["risk_alert_id"] = UUID(data["risk_alert_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        if isinstance(data.get("risk_limits_id"), str):
            data["risk_limits_id"] = UUID(data["risk_limits_id"])
        
        # Convert enum strings back to enum objects
        if isinstance(data.get("alert_type"), str):
            data["alert_type"] = AlertType(data["alert_type"])
        if isinstance(data.get("alert_severity"), str):
            data["alert_severity"] = AlertSeverity(data["alert_severity"])
        if isinstance(data.get("alert_status"), str):
            data["alert_status"] = AlertStatus(data["alert_status"])
        
        # Convert datetime strings back to datetime objects
        for field in ["alert_timestamp", "acknowledged_at", "resolved_at", "created_at"]:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def acknowledge(self, acknowledged_by: str) -> None:
        """Acknowledge the alert."""
        if self.alert_status != AlertStatus.ACTIVE:
            raise ValueError("Only active alerts can be acknowledged")
        
        self.alert_status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self) -> None:
        """Resolve the alert."""
        if self.alert_status == AlertStatus.RESOLVED:
            raise ValueError("Alert is already resolved")
        
        self.alert_status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
    
    def escalate(self) -> None:
        """Escalate the alert to the next level."""
        if self.escalation_level >= 5:
            raise ValueError("Alert is already at maximum escalation level")
        
        self.escalation_level += 1
        
        # Update severity based on escalation level
        if self.escalation_level >= 3 and self.alert_severity != AlertSeverity.CRITICAL:
            self.alert_severity = AlertSeverity.HIGH
        if self.escalation_level >= 4:
            self.alert_severity = AlertSeverity.CRITICAL
    
    def mark_notification_sent(self) -> None:
        """Mark that notification has been sent."""
        self.notification_sent = True
    
    def is_active(self) -> bool:
        """Check if the alert is active."""
        return self.alert_status == AlertStatus.ACTIVE
    
    def is_acknowledged(self) -> bool:
        """Check if the alert has been acknowledged."""
        return self.alert_status == AlertStatus.ACKNOWLEDGED
    
    def is_resolved(self) -> bool:
        """Check if the alert has been resolved."""
        return self.alert_status == AlertStatus.RESOLVED
    
    def is_critical(self) -> bool:
        """Check if the alert is critical severity."""
        return self.alert_severity == AlertSeverity.CRITICAL
    
    def get_age_minutes(self) -> float:
        """Get the age of the alert in minutes."""
        age = datetime.utcnow() - self.alert_timestamp
        return age.total_seconds() / 60
    
    def get_resolution_time_minutes(self) -> Optional[float]:
        """Get the resolution time in minutes if resolved."""
        if not self.is_resolved() or not self.resolved_at:
            return None
        
        resolution_time = self.resolved_at - self.alert_timestamp
        return resolution_time.total_seconds() / 60
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get a summary of the alert."""
        return {
            "alert_id": str(self.risk_alert_id),
            "portfolio_id": str(self.portfolio_id),
            "alert_type": self.alert_type.value,
            "alert_severity": self.alert_severity.value,
            "alert_status": self.alert_status.value,
            "limit_name": self.limit_name,
            "limit_value": self.limit_value,
            "current_value": self.current_value,
            "breach_percentage": self.breach_percentage,
            "escalation_level": self.escalation_level,
            "age_minutes": self.get_age_minutes(),
            "notification_sent": self.notification_sent,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def requires_immediate_attention(self) -> bool:
        """Check if the alert requires immediate attention."""
        return (
            self.is_critical() or
            self.escalation_level >= 3 or
            (self.is_active() and self.get_age_minutes() > 60)
        )
    
    def get_priority_score(self) -> int:
        """Get a priority score for the alert (higher = more urgent)."""
        base_score = {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4
        }[self.alert_severity]
        
        # Add points for escalation
        escalation_bonus = self.escalation_level * 2
        
        # Add points for age (if active)
        if self.is_active():
            age_bonus = min(int(self.get_age_minutes() / 30), 5)  # Max 5 points for age
        else:
            age_bonus = 0
        
        return base_score + escalation_bonus + age_bonus
    
    def __str__(self) -> str:
        """String representation of RiskAlert."""
        return (f"RiskAlert(type={self.alert_type.value}, "
                f"severity={self.alert_severity.value}, "
                f"status={self.alert_status.value}, "
                f"limit={self.limit_name}, "
                f"breach={self.breach_percentage:.1f}%)")
    
    def __repr__(self) -> str:
        """Detailed string representation of RiskAlert."""
        return (f"RiskAlert("
                f"risk_alert_id={self.risk_alert_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"alert_type={self.alert_type.value}, "
                f"alert_severity={self.alert_severity.value}, "
                f"alert_status={self.alert_status.value}, "
                f"limit_name='{self.limit_name}', "
                f"breach_percentage={self.breach_percentage:.2f})")



