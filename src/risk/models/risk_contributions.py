"""
Risk Contributions Data Model

Represents individual asset and factor contributions to portfolio risk for the
comprehensive risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID


@dataclass
class RiskContributions:
    """
    Individual asset and factor contributions to portfolio risk.
    
    This model represents the risk contribution analysis showing how much
    each asset, sector, or risk factor contributes to overall portfolio risk.
    """
    
    # Primary key
    risk_contributions_id: UUID = field(default_factory=uuid4)
    
    # Portfolio reference
    portfolio_id: UUID = field()
    
    # Analysis metadata
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    risk_metrics_id: UUID = field()  # Reference to associated risk metrics
    
    # Asset contributions
    asset_contributions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Sector contributions
    sector_contributions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Factor contributions
    factor_contributions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Risk decomposition
    systematic_risk: float = field(default=0.0)
    idiosyncratic_risk: float = field(default=0.0)
    
    # Top contributors
    top_risk_contributors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analysis metadata
    total_portfolio_risk: float = field(default=0.0)
    risk_decomposition_method: str = field(default="variance_decomposition")
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate risk contributions data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if not isinstance(self.risk_metrics_id, UUID):
            raise ValueError("Risk metrics ID must be a valid UUID")
        
        if self.total_portfolio_risk < 0:
            raise ValueError("Total portfolio risk must be non-negative")
        
        if self.systematic_risk < 0:
            raise ValueError("Systematic risk must be non-negative")
        
        if self.idiosyncratic_risk < 0:
            raise ValueError("Idiosyncratic risk must be non-negative")
        
        if not self.risk_decomposition_method:
            raise ValueError("Risk decomposition method is required")
        
        # Validate that systematic and idiosyncratic risk sum to total (approximately)
        if self.total_portfolio_risk > 0:
            total_decomposed = self.systematic_risk + self.idiosyncratic_risk
            if abs(total_decomposed - self.total_portfolio_risk) / self.total_portfolio_risk > 0.05:
                raise ValueError("Systematic and idiosyncratic risk should sum to total portfolio risk")
        
        # Validate asset contributions
        self._validate_contributions(self.asset_contributions, "asset")
        
        # Validate sector contributions
        self._validate_contributions(self.sector_contributions, "sector")
        
        # Validate factor contributions
        self._validate_contributions(self.factor_contributions, "factor")
    
    def _validate_contributions(self, contributions: Dict[str, Dict[str, float]], contribution_type: str) -> None:
        """Validate contribution data structure and values."""
        for entity, metrics in contributions.items():
            if not isinstance(entity, str):
                raise ValueError(f"{contribution_type} name must be a string")
            
            if not isinstance(metrics, dict):
                raise ValueError(f"{contribution_type} contributions must be a dictionary")
            
            # Validate contribution metrics
            for metric_name, value in metrics.items():
                if not isinstance(metric_name, str):
                    raise ValueError(f"{contribution_type} metric name must be a string")
                
                if not isinstance(value, (int, float)):
                    raise ValueError(f"{contribution_type} metric value must be numeric")
                
                # Validate specific metrics
                if metric_name in ["risk_contribution", "weight", "marginal_contribution"]:
                    if not (0 <= value <= 1):
                        raise ValueError(f"{contribution_type} {metric_name} must be between 0 and 1")
                
                if metric_name == "contribution_pct":
                    if not (0 <= value <= 100):
                        raise ValueError(f"{contribution_type} contribution percentage must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RiskContributions to dictionary."""
        return {
            "risk_contributions_id": str(self.risk_contributions_id),
            "portfolio_id": str(self.portfolio_id),
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "risk_metrics_id": str(self.risk_metrics_id),
            "asset_contributions": self.asset_contributions,
            "sector_contributions": self.sector_contributions,
            "factor_contributions": self.factor_contributions,
            "systematic_risk": self.systematic_risk,
            "idiosyncratic_risk": self.idiosyncratic_risk,
            "top_risk_contributors": self.top_risk_contributors,
            "total_portfolio_risk": self.total_portfolio_risk,
            "risk_decomposition_method": self.risk_decomposition_method,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskContributions":
        """Create RiskContributions from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("risk_contributions_id"), str):
            data["risk_contributions_id"] = UUID(data["risk_contributions_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        if isinstance(data.get("risk_metrics_id"), str):
            data["risk_metrics_id"] = UUID(data["risk_metrics_id"])
        
        # Convert datetime strings back to datetime objects
        if isinstance(data.get("analysis_timestamp"), str):
            data["analysis_timestamp"] = datetime.fromisoformat(data["analysis_timestamp"].replace("Z", "+00:00"))
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def get_risk_attribution_summary(self) -> Dict[str, Any]:
        """Get a summary of risk attribution analysis."""
        return {
            "total_portfolio_risk": self.total_portfolio_risk,
            "systematic_risk": self.systematic_risk,
            "idiosyncratic_risk": self.idiosyncratic_risk,
            "systematic_risk_pct": (self.systematic_risk / self.total_portfolio_risk * 100) if self.total_portfolio_risk > 0 else 0,
            "idiosyncratic_risk_pct": (self.idiosyncratic_risk / self.total_portfolio_risk * 100) if self.total_portfolio_risk > 0 else 0,
            "num_assets": len(self.asset_contributions),
            "num_sectors": len(self.sector_contributions),
            "num_factors": len(self.factor_contributions),
            "risk_decomposition_method": self.risk_decomposition_method
        }
    
    def get_top_asset_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top asset risk contributors."""
        contributors = []
        
        for asset, metrics in self.asset_contributions.items():
            contributors.append({
                "entity": asset,
                "entity_type": "asset",
                "risk_contribution": metrics.get("risk_contribution", 0.0),
                "weight": metrics.get("weight", 0.0),
                "marginal_contribution": metrics.get("marginal_contribution", 0.0),
                "contribution_pct": metrics.get("contribution_pct", 0.0)
            })
        
        # Sort by risk contribution (descending)
        contributors.sort(key=lambda x: x["risk_contribution"], reverse=True)
        return contributors[:limit]
    
    def get_top_sector_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top sector risk contributors."""
        contributors = []
        
        for sector, metrics in self.sector_contributions.items():
            contributors.append({
                "entity": sector,
                "entity_type": "sector",
                "risk_contribution": metrics.get("risk_contribution", 0.0),
                "weight": metrics.get("weight", 0.0),
                "marginal_contribution": metrics.get("marginal_contribution", 0.0),
                "contribution_pct": metrics.get("contribution_pct", 0.0)
            })
        
        # Sort by risk contribution (descending)
        contributors.sort(key=lambda x: x["risk_contribution"], reverse=True)
        return contributors[:limit]
    
    def get_top_factor_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top factor risk contributors."""
        contributors = []
        
        for factor, metrics in self.factor_contributions.items():
            contributors.append({
                "entity": factor,
                "entity_type": "factor",
                "risk_contribution": metrics.get("risk_contribution", 0.0),
                "weight": metrics.get("weight", 0.0),
                "marginal_contribution": metrics.get("marginal_contribution", 0.0),
                "contribution_pct": metrics.get("contribution_pct", 0.0)
            })
        
        # Sort by risk contribution (descending)
        contributors.sort(key=lambda x: x["risk_contribution"], reverse=True)
        return contributors[:limit]
    
    def get_concentration_analysis(self) -> Dict[str, Any]:
        """Get concentration analysis based on risk contributions."""
        # Asset concentration
        asset_contributions = [metrics.get("contribution_pct", 0.0) for metrics in self.asset_contributions.values()]
        asset_hhi = sum(contrib ** 2 for contrib in asset_contributions) / 10000  # Normalize to 0-1 scale
        
        # Sector concentration
        sector_contributions = [metrics.get("contribution_pct", 0.0) for metrics in self.sector_contributions.values()]
        sector_hhi = sum(contrib ** 2 for contrib in sector_contributions) / 10000  # Normalize to 0-1 scale
        
        # Factor concentration
        factor_contributions = [metrics.get("contribution_pct", 0.0) for metrics in self.factor_contributions.values()]
        factor_hhi = sum(contrib ** 2 for contrib in factor_contributions) / 10000  # Normalize to 0-1 scale
        
        return {
            "asset_concentration_hhi": asset_hhi,
            "sector_concentration_hhi": sector_hhi,
            "factor_concentration_hhi": factor_hhi,
            "overall_concentration_risk": (asset_hhi + sector_hhi + factor_hhi) / 3,
            "top_5_assets_contribution_pct": sum(sorted(asset_contributions, reverse=True)[:5]),
            "top_3_sectors_contribution_pct": sum(sorted(sector_contributions, reverse=True)[:3]),
            "top_3_factors_contribution_pct": sum(sorted(factor_contributions, reverse=True)[:3])
        }
    
    def get_risk_diversification_ratio(self) -> float:
        """Calculate the risk diversification ratio."""
        if not self.asset_contributions:
            return 1.0
        
        # Calculate weighted average risk contribution
        weighted_avg_contribution = sum(
            metrics.get("weight", 0.0) * metrics.get("risk_contribution", 0.0)
            for metrics in self.asset_contributions.values()
        )
        
        # Calculate equal-weighted average risk contribution
        num_assets = len(self.asset_contributions)
        equal_weight = 1.0 / num_assets if num_assets > 0 else 0
        equal_weighted_avg_contribution = sum(
            equal_weight * metrics.get("risk_contribution", 0.0)
            for metrics in self.asset_contributions.values()
        )
        
        # Risk diversification ratio = equal-weighted / weighted
        if weighted_avg_contribution > 0:
            return equal_weighted_avg_contribution / weighted_avg_contribution
        else:
            return 1.0
    
    def add_asset_contribution(self, asset_name: str, contribution_data: Dict[str, float]) -> None:
        """Add asset risk contribution data."""
        self.asset_contributions[asset_name] = contribution_data
    
    def add_sector_contribution(self, sector_name: str, contribution_data: Dict[str, float]) -> None:
        """Add sector risk contribution data."""
        self.sector_contributions[sector_name] = contribution_data
    
    def add_factor_contribution(self, factor_name: str, contribution_data: Dict[str, float]) -> None:
        """Add factor risk contribution data."""
        self.factor_contributions[factor_name] = contribution_data
    
    def update_top_contributors(self) -> None:
        """Update the top risk contributors list."""
        all_contributors = []
        
        # Add asset contributors
        all_contributors.extend(self.get_top_asset_contributors(20))
        
        # Add sector contributors
        all_contributors.extend(self.get_top_sector_contributors(10))
        
        # Add factor contributors
        all_contributors.extend(self.get_top_factor_contributors(10))
        
        # Sort all contributors by risk contribution
        all_contributors.sort(key=lambda x: x["risk_contribution"], reverse=True)
        
        # Update top contributors
        self.top_risk_contributors = all_contributors[:20]  # Keep top 20 overall
    
    def __str__(self) -> str:
        """String representation of RiskContributions."""
        return (f"RiskContributions(portfolio_id={self.portfolio_id}, "
                f"total_risk={self.total_portfolio_risk:.4f}, "
                f"assets={len(self.asset_contributions)}, "
                f"sectors={len(self.sector_contributions)})")
    
    def __repr__(self) -> str:
        """Detailed string representation of RiskContributions."""
        return (f"RiskContributions("
                f"risk_contributions_id={self.risk_contributions_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"analysis_timestamp={self.analysis_timestamp}, "
                f"total_portfolio_risk={self.total_portfolio_risk}, "
                f"systematic_risk={self.systematic_risk}, "
                f"idiosyncratic_risk={self.idiosyncratic_risk})")

