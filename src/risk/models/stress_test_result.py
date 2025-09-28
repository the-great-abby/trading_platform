"""
Stress Test Result Data Model

Represents results from stress testing scenarios for the comprehensive
risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID
from enum import Enum


class ScenarioType(Enum):
    """Types of stress test scenarios."""
    MARKET_CRASH = "market_crash"
    RATE_SHOCK = "rate_shock"
    VOLATILITY_SPIKE = "volatility_spike"
    SECTOR_ROTATION = "sector_rotation"
    OPTIONS_DECAY = "options_decay"
    CUSTOM = "custom"


class TestStatus(Enum):
    """Status of stress test execution."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class PositionImpact:
    """Individual position impact from stress testing."""
    asset_id: str
    asset_type: str = "stock"
    initial_value: float = 0.0
    stressed_value: float = 0.0
    position_value_change: float = 0.0
    position_value_change_pct: float = 0.0
    contribution_to_portfolio_change: float = 0.0


@dataclass
class SectorImpact:
    """Sector-level impact from stress testing."""
    sector: str
    initial_value: float = 0.0
    stressed_value: float = 0.0
    sector_value_change: float = 0.0
    sector_value_change_pct: float = 0.0
    weight_in_portfolio: float = 0.0
    contribution_to_portfolio_change: float = 0.0


@dataclass
class StressTestResult:
    """
    Results from stress testing scenarios.
    
    This model represents the results of running stress tests on a portfolio,
    including scenario details, portfolio value changes, and impact analysis.
    """
    
    # Primary key
    stress_test_id: UUID = field(default_factory=uuid4)
    
    # Portfolio reference
    portfolio_id: UUID = field()
    
    # Scenario information
    scenario_name: str = field()
    scenario_type: ScenarioType = field()
    test_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Portfolio values
    initial_portfolio_value: float = field(default=0.0)
    stressed_portfolio_value: float = field(default=0.0)
    portfolio_value_change: float = field(default=0.0)
    portfolio_value_change_pct: float = field(default=0.0)
    
    # Risk impact
    var_impact: float = field(default=0.0)
    volatility_impact: float = field(default=0.0)
    max_drawdown_impact: float = field(default=0.0)
    
    # Impact analysis
    position_impacts: List[PositionImpact] = field(default_factory=list)
    sector_impacts: List[SectorImpact] = field(default_factory=list)
    
    # Scenario parameters
    scenario_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Test metadata
    test_duration_ms: int = field(default=0)
    status: TestStatus = field(default=TestStatus.PENDING)
    error_message: Optional[str] = field(default=None)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate stress test result data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if not self.scenario_name:
            raise ValueError("Scenario name is required")
        
        if not isinstance(self.scenario_type, ScenarioType):
            raise ValueError("Scenario type must be a valid ScenarioType")
        
        if self.initial_portfolio_value <= 0:
            raise ValueError("Initial portfolio value must be positive")
        
        if self.stressed_portfolio_value < 0:
            raise ValueError("Stressed portfolio value must be non-negative")
        
        if not (-1.0 <= self.portfolio_value_change_pct <= 1.0):
            raise ValueError("Portfolio value change percentage must be between -100% and +100%")
        
        if self.test_duration_ms < 0:
            raise ValueError("Test duration must be non-negative")
        
        if not isinstance(self.status, TestStatus):
            raise ValueError("Status must be a valid TestStatus")
        
        # Validate that calculated values are consistent
        calculated_change = self.stressed_portfolio_value - self.initial_portfolio_value
        if abs(calculated_change - self.portfolio_value_change) > 0.01:
            raise ValueError("Portfolio value change is inconsistent with initial and stressed values")
        
        calculated_pct = calculated_change / self.initial_portfolio_value
        if abs(calculated_pct - self.portfolio_value_change_pct) > 0.0001:
            raise ValueError("Portfolio value change percentage is inconsistent with calculated change")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert StressTestResult to dictionary."""
        return {
            "stress_test_id": str(self.stress_test_id),
            "portfolio_id": str(self.portfolio_id),
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type.value,
            "test_timestamp": self.test_timestamp.isoformat(),
            "initial_portfolio_value": self.initial_portfolio_value,
            "stressed_portfolio_value": self.stressed_portfolio_value,
            "portfolio_value_change": self.portfolio_value_change,
            "portfolio_value_change_pct": self.portfolio_value_change_pct,
            "var_impact": self.var_impact,
            "volatility_impact": self.volatility_impact,
            "max_drawdown_impact": self.max_drawdown_impact,
            "position_impacts": [
                {
                    "asset_id": impact.asset_id,
                    "asset_type": impact.asset_type,
                    "initial_value": impact.initial_value,
                    "stressed_value": impact.stressed_value,
                    "position_value_change": impact.position_value_change,
                    "position_value_change_pct": impact.position_value_change_pct,
                    "contribution_to_portfolio_change": impact.contribution_to_portfolio_change
                }
                for impact in self.position_impacts
            ],
            "sector_impacts": [
                {
                    "sector": impact.sector,
                    "initial_value": impact.initial_value,
                    "stressed_value": impact.stressed_value,
                    "sector_value_change": impact.sector_value_change,
                    "sector_value_change_pct": impact.sector_value_change_pct,
                    "weight_in_portfolio": impact.weight_in_portfolio,
                    "contribution_to_portfolio_change": impact.contribution_to_portfolio_change
                }
                for impact in self.sector_impacts
            ],
            "scenario_parameters": self.scenario_parameters,
            "test_duration_ms": self.test_duration_ms,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StressTestResult":
        """Create StressTestResult from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("stress_test_id"), str):
            data["stress_test_id"] = UUID(data["stress_test_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        
        # Convert enum strings back to enum objects
        if isinstance(data.get("scenario_type"), str):
            data["scenario_type"] = ScenarioType(data["scenario_type"])
        if isinstance(data.get("status"), str):
            data["status"] = TestStatus(data["status"])
        
        # Convert datetime strings back to datetime objects
        for field in ["test_timestamp", "created_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        # Convert position impacts
        if "position_impacts" in data:
            data["position_impacts"] = [
                PositionImpact(**impact) for impact in data["position_impacts"]
            ]
        
        # Convert sector impacts
        if "sector_impacts" in data:
            data["sector_impacts"] = [
                SectorImpact(**impact) for impact in data["sector_impacts"]
            ]
        
        return cls(**data)
    
    def get_impact_summary(self) -> Dict[str, Any]:
        """Get a summary of stress test impacts."""
        return {
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type.value,
            "portfolio_value_change_pct": self.portfolio_value_change_pct,
            "var_impact": self.var_impact,
            "volatility_impact": self.volatility_impact,
            "max_drawdown_impact": self.max_drawdown_impact,
            "status": self.status.value,
            "test_duration_ms": self.test_duration_ms
        }
    
    def is_severe(self, threshold_pct: float = -0.20) -> bool:
        """Check if the stress test result represents a severe impact."""
        return self.portfolio_value_change_pct <= threshold_pct
    
    def get_top_position_impacts(self, limit: int = 5) -> List[PositionImpact]:
        """Get the top position impacts by absolute change."""
        return sorted(
            self.position_impacts,
            key=lambda x: abs(x.position_value_change),
            reverse=True
        )[:limit]
    
    def get_top_sector_impacts(self, limit: int = 5) -> List[SectorImpact]:
        """Get the top sector impacts by absolute change."""
        return sorted(
            self.sector_impacts,
            key=lambda x: abs(x.sector_value_change),
            reverse=True
        )[:limit]
    
    def __str__(self) -> str:
        """String representation of StressTestResult."""
        return (f"StressTestResult(scenario={self.scenario_name}, "
                f"change={self.portfolio_value_change_pct:.1%}, "
                f"status={self.status.value})")
    
    def __repr__(self) -> str:
        """Detailed string representation of StressTestResult."""
        return (f"StressTestResult("
                f"stress_test_id={self.stress_test_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"scenario_name='{self.scenario_name}', "
                f"scenario_type={self.scenario_type.value}, "
                f"portfolio_value_change_pct={self.portfolio_value_change_pct:.3f}, "
                f"status={self.status.value})")



