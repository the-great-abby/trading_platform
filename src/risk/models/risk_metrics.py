"""
Risk Metrics Data Model

Represents portfolio-level risk measurements and calculations for the comprehensive
risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4, UUID
import json


@dataclass
class RiskMetrics:
    """
    Portfolio-level risk measurements and calculations.
    
    This model represents comprehensive risk metrics for a portfolio including
    Value at Risk (VaR), Expected Shortfall, volatility, and other risk measures.
    """
    
    # Primary key
    risk_metrics_id: UUID = field(default_factory=uuid4)
    
    # Portfolio reference
    portfolio_id: UUID = field()
    
    # Calculation metadata
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)
    calculation_method: str = field(default="historical_simulation")
    data_period_days: int = field(default=252)
    
    # VaR metrics
    var_95: float = field(default=0.0)
    var_99: float = field(default=0.0)
    expected_shortfall_95: float = field(default=0.0)
    expected_shortfall_99: float = field(default=0.0)
    
    # Portfolio risk metrics
    portfolio_volatility: float = field(default=0.0)
    portfolio_beta: float = field(default=0.0)
    maximum_drawdown: float = field(default=0.0)
    
    # Performance metrics
    sharpe_ratio: float = field(default=0.0)
    sortino_ratio: float = field(default=0.0)
    calmar_ratio: float = field(default=0.0)
    
    # Risk scores
    concentration_risk: float = field(default=0.0)
    correlation_risk: float = field(default=0.0)
    
    # Portfolio composition
    leverage_ratio: float = field(default=0.0)
    cash_ratio: float = field(default=0.0)
    
    # Additional data
    confidence_intervals: Dict[str, float] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate risk metrics data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if self.var_95 < 0:
            raise ValueError("VaR 95% must be non-negative")
        
        if self.var_99 < 0:
            raise ValueError("VaR 99% must be non-negative")
        
        if self.expected_shortfall_95 < 0:
            raise ValueError("Expected Shortfall 95% must be non-negative")
        
        if self.expected_shortfall_99 < 0:
            raise ValueError("Expected Shortfall 99% must be non-negative")
        
        if not (0 <= self.portfolio_volatility <= 10):
            raise ValueError("Portfolio volatility must be between 0 and 10 (1000% max)")
        
        if not (0 <= self.maximum_drawdown <= 1):
            raise ValueError("Maximum drawdown must be between 0 and 1 (100% max)")
        
        if not (-5 <= self.sharpe_ratio <= 5):
            raise ValueError("Sharpe ratio should be reasonable (-5 to +5 range)")
        
        if not (0 <= self.concentration_risk <= 1):
            raise ValueError("Concentration risk must be between 0 and 1")
        
        if not (0 <= self.correlation_risk <= 1):
            raise ValueError("Correlation risk must be between 0 and 1")
        
        if self.leverage_ratio < 0:
            raise ValueError("Leverage ratio must be non-negative")
        
        if not (0 <= self.cash_ratio <= 1):
            raise ValueError("Cash ratio must be between 0 and 1")
        
        if self.data_period_days <= 0:
            raise ValueError("Data period days must be positive")
        
        # Validate VaR ordering
        if self.var_99 < self.var_95:
            raise ValueError("VaR 99% should be greater than or equal to VaR 95%")
        
        # Validate Expected Shortfall ordering
        if self.expected_shortfall_99 < self.expected_shortfall_95:
            raise ValueError("Expected Shortfall 99% should be greater than or equal to Expected Shortfall 95%")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RiskMetrics to dictionary."""
        return {
            "risk_metrics_id": str(self.risk_metrics_id),
            "portfolio_id": str(self.portfolio_id),
            "calculation_timestamp": self.calculation_timestamp.isoformat(),
            "calculation_method": self.calculation_method,
            "data_period_days": self.data_period_days,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "expected_shortfall_95": self.expected_shortfall_95,
            "expected_shortfall_99": self.expected_shortfall_99,
            "portfolio_volatility": self.portfolio_volatility,
            "portfolio_beta": self.portfolio_beta,
            "maximum_drawdown": self.maximum_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "concentration_risk": self.concentration_risk,
            "correlation_risk": self.correlation_risk,
            "leverage_ratio": self.leverage_ratio,
            "cash_ratio": self.cash_ratio,
            "confidence_intervals": self.confidence_intervals,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskMetrics":
        """Create RiskMetrics from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("risk_metrics_id"), str):
            data["risk_metrics_id"] = UUID(data["risk_metrics_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        
        # Convert datetime strings back to datetime objects
        for field in ["calculation_timestamp", "created_at", "updated_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get a summary of key risk metrics."""
        return {
            "var_95": self.var_95,
            "var_99": self.var_99,
            "expected_shortfall_95": self.expected_shortfall_95,
            "expected_shortfall_99": self.expected_shortfall_99,
            "portfolio_volatility": self.portfolio_volatility,
            "maximum_drawdown": self.maximum_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "concentration_risk": self.concentration_risk,
            "correlation_risk": self.correlation_risk
        }
    
    def is_recent(self, max_age_hours: int = 1) -> bool:
        """Check if risk metrics are recent (within specified hours)."""
        age = datetime.utcnow() - self.calculation_timestamp
        return age.total_seconds() < (max_age_hours * 3600)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        """String representation of RiskMetrics."""
        return (f"RiskMetrics(portfolio_id={self.portfolio_id}, "
                f"var_95={self.var_95:.2f}, var_99={self.var_99:.2f}, "
                f"volatility={self.portfolio_volatility:.3f}, "
                f"max_drawdown={self.maximum_drawdown:.3f})")
    
    def __repr__(self) -> str:
        """Detailed string representation of RiskMetrics."""
        return (f"RiskMetrics("
                f"risk_metrics_id={self.risk_metrics_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"calculation_timestamp={self.calculation_timestamp}, "
                f"var_95={self.var_95}, var_99={self.var_99}, "
                f"portfolio_volatility={self.portfolio_volatility}, "
                f"maximum_drawdown={self.maximum_drawdown}, "
                f"sharpe_ratio={self.sharpe_ratio})")

