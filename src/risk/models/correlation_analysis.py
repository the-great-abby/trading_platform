"""
Correlation Analysis Data Model

Represents asset correlation matrices and concentration risk analysis for the
comprehensive risk management framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID
import json


@dataclass
class CorrelationAnalysis:
    """
    Asset correlation matrices and concentration risk analysis.
    
    This model represents the results of correlation analysis including
    correlation matrices, concentration risks, and diversification recommendations.
    """
    
    # Primary key
    correlation_analysis_id: UUID = field(default_factory=uuid4)
    
    # Portfolio reference
    portfolio_id: UUID = field()
    
    # Analysis metadata
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    rolling_correlation_period: int = field(default=30)
    analysis_method: str = field(default="pearson_correlation")
    
    # Correlation data
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    sector_correlations: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Concentration analysis
    concentration_risk_score: float = field(default=0.0)
    sector_concentration: Dict[str, float] = field(default_factory=dict)
    
    # Diversification metrics
    diversification_ratio: float = field(default=0.0)
    effective_number_of_assets: float = field(default=0.0)
    
    # Correlation stability
    correlation_stability_score: float = field(default=0.0)
    correlation_regime: str = field(default="normal")
    
    # Top correlations
    top_correlations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Risk attribution
    risk_attribution: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate correlation analysis data."""
        if not isinstance(self.portfolio_id, UUID):
            raise ValueError("Portfolio ID must be a valid UUID")
        
        if not (0 <= self.concentration_risk_score <= 1):
            raise ValueError("Concentration risk score must be between 0 and 1")
        
        if self.diversification_ratio <= 0:
            raise ValueError("Diversification ratio must be positive")
        
        if self.effective_number_of_assets < 1:
            raise ValueError("Effective number of assets must be at least 1")
        
        if not (0 <= self.correlation_stability_score <= 1):
            raise ValueError("Correlation stability score must be between 0 and 1")
        
        if self.rolling_correlation_period <= 0:
            raise ValueError("Rolling correlation period must be positive")
        
        # Validate correlation matrix is symmetric
        self._validate_correlation_matrix()
        
        # Validate sector concentrations sum to 1 (approximately)
        if self.sector_concentration:
            total_concentration = sum(self.sector_concentration.values())
            if not (0.95 <= total_concentration <= 1.05):
                raise ValueError("Sector concentrations should sum to approximately 1")
    
    def _validate_correlation_matrix(self) -> None:
        """Validate correlation matrix structure and values."""
        if not self.correlation_matrix:
            return
        
        assets = list(self.correlation_matrix.keys())
        
        for asset1 in assets:
            if asset1 not in self.correlation_matrix[asset1]:
                raise ValueError(f"Correlation matrix missing diagonal entry for {asset1}")
            
            # Check diagonal is 1.0
            if abs(self.correlation_matrix[asset1][asset1] - 1.0) > 0.001:
                raise ValueError(f"Correlation matrix diagonal for {asset1} should be 1.0")
            
            for asset2 in assets:
                if asset2 not in self.correlation_matrix[asset1]:
                    raise ValueError(f"Correlation matrix missing entry for {asset1}-{asset2}")
                
                # Check correlation values are in valid range
                corr_value = self.correlation_matrix[asset1][asset2]
                if not (-1.0 <= corr_value <= 1.0):
                    raise ValueError(f"Correlation value for {asset1}-{asset2} must be between -1 and 1")
                
                # Check symmetry
                if abs(corr_value - self.correlation_matrix[asset2][asset1]) > 0.001:
                    raise ValueError(f"Correlation matrix not symmetric for {asset1}-{asset2}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CorrelationAnalysis to dictionary."""
        return {
            "correlation_analysis_id": str(self.correlation_analysis_id),
            "portfolio_id": str(self.portfolio_id),
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "rolling_correlation_period": self.rolling_correlation_period,
            "analysis_method": self.analysis_method,
            "correlation_matrix": self.correlation_matrix,
            "sector_correlations": self.sector_correlations,
            "concentration_risk_score": self.concentration_risk_score,
            "sector_concentration": self.sector_concentration,
            "diversification_ratio": self.diversification_ratio,
            "effective_number_of_assets": self.effective_number_of_assets,
            "correlation_stability_score": self.correlation_stability_score,
            "correlation_regime": self.correlation_regime,
            "top_correlations": self.top_correlations,
            "risk_attribution": self.risk_attribution,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrelationAnalysis":
        """Create CorrelationAnalysis from dictionary."""
        # Convert UUID strings back to UUID objects
        if isinstance(data.get("correlation_analysis_id"), str):
            data["correlation_analysis_id"] = UUID(data["correlation_analysis_id"])
        if isinstance(data.get("portfolio_id"), str):
            data["portfolio_id"] = UUID(data["portfolio_id"])
        
        # Convert datetime strings back to datetime objects
        if isinstance(data.get("analysis_timestamp"), str):
            data["analysis_timestamp"] = datetime.fromisoformat(data["analysis_timestamp"].replace("Z", "+00:00"))
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def get_correlation_summary(self) -> Dict[str, Any]:
        """Get a summary of correlation analysis results."""
        return {
            "concentration_risk_score": self.concentration_risk_score,
            "diversification_ratio": self.diversification_ratio,
            "effective_number_of_assets": self.effective_number_of_assets,
            "correlation_stability_score": self.correlation_stability_score,
            "correlation_regime": self.correlation_regime,
            "num_assets": len(self.correlation_matrix) if self.correlation_matrix else 0,
            "num_sectors": len(self.sector_concentration),
            "num_recommendations": len(self.recommendations)
        }
    
    def get_high_correlations(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Get asset pairs with high correlations above threshold."""
        high_correlations = []
        
        if not self.correlation_matrix:
            return high_correlations
        
        assets = list(self.correlation_matrix.keys())
        
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets[i+1:], i+1):
                correlation = abs(self.correlation_matrix[asset1][asset2])
                if correlation >= threshold:
                    high_correlations.append({
                        "asset1": asset1,
                        "asset2": asset2,
                        "correlation": self.correlation_matrix[asset1][asset2],
                        "abs_correlation": correlation
                    })
        
        # Sort by absolute correlation (descending)
        high_correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)
        return high_correlations
    
    def get_sector_concentration_risk(self) -> Dict[str, Any]:
        """Get sector concentration risk analysis."""
        if not self.sector_concentration:
            return {"risk_level": "unknown", "top_sectors": [], "concentration_score": 0.0}
        
        # Calculate Herfindahl-Hirschman Index for sector concentration
        hhi = sum(weight ** 2 for weight in self.sector_concentration.values())
        
        # Determine risk level based on HHI
        if hhi > 0.25:  # HHI > 0.25 indicates high concentration
            risk_level = "high"
        elif hhi > 0.15:  # HHI > 0.15 indicates moderate concentration
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        # Get top sectors by concentration
        top_sectors = sorted(
            self.sector_concentration.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "risk_level": risk_level,
            "hhi": hhi,
            "top_sectors": top_sectors,
            "concentration_score": self.concentration_risk_score
        }
    
    def is_well_diversified(self) -> bool:
        """Check if portfolio is well diversified."""
        return (
            self.concentration_risk_score < 0.3 and
            self.effective_number_of_assets >= 10 and
            self.diversification_ratio > 1.5
        )
    
    def get_diversification_recommendations(self) -> List[str]:
        """Get specific diversification recommendations based on analysis."""
        recommendations = []
        
        # High concentration risk
        if self.concentration_risk_score > 0.5:
            recommendations.append("Portfolio has high concentration risk - consider diversifying across more assets")
        
        # Low effective number of assets
        if self.effective_number_of_assets < 10:
            recommendations.append(f"Effective number of assets ({self.effective_number_of_assets:.1f}) is low - add more assets")
        
        # Low diversification ratio
        if self.diversification_ratio < 1.2:
            recommendations.append("Low diversification ratio - consider adding uncorrelated assets")
        
        # High correlations
        high_corrs = self.get_high_correlations(0.8)
        if len(high_corrs) > 0:
            recommendations.append(f"Found {len(high_corrs)} asset pairs with very high correlations (>0.8)")
        
        # Sector concentration
        sector_risk = self.get_sector_concentration_risk()
        if sector_risk["risk_level"] == "high":
            recommendations.append("High sector concentration - diversify across more sectors")
        
        return recommendations
    
    def __str__(self) -> str:
        """String representation of CorrelationAnalysis."""
        return (f"CorrelationAnalysis(portfolio_id={self.portfolio_id}, "
                f"concentration_risk={self.concentration_risk_score:.3f}, "
                f"diversification_ratio={self.diversification_ratio:.2f}, "
                f"effective_assets={self.effective_number_of_assets:.1f})")
    
    def __repr__(self) -> str:
        """Detailed string representation of CorrelationAnalysis."""
        return (f"CorrelationAnalysis("
                f"correlation_analysis_id={self.correlation_analysis_id}, "
                f"portfolio_id={self.portfolio_id}, "
                f"analysis_timestamp={self.analysis_timestamp}, "
                f"concentration_risk_score={self.concentration_risk_score}, "
                f"diversification_ratio={self.diversification_ratio}, "
                f"effective_number_of_assets={self.effective_number_of_assets})")












