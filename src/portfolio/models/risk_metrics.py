"""
RiskMetrics Entity Model
Portfolio risk calculations and metrics
"""
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, field
import uuid


@dataclass
class RiskMetrics:
    """Portfolio risk calculations and metrics"""
    
    # Primary identifiers
    risk_metrics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str = ""
    
    # Calculation metadata
    calculation_date: datetime = field(default_factory=datetime.now)
    lookback_period: int = 252  # Days of historical data used
    
    # Value at Risk metrics
    var_95: float = 0.0  # 95% Value at Risk
    var_99: float = 0.0  # 99% Value at Risk
    cvar_95: float = 0.0  # 95% Conditional VaR
    cvar_99: float = 0.0  # 99% Conditional VaR
    
    # Risk decomposition
    systematic_risk: float = 0.0  # Systematic (market) risk
    idiosyncratic_risk: float = 0.0  # Idiosyncratic (specific) risk
    risk_contributions: Dict[str, float] = field(default_factory=dict)  # Risk contribution by asset
    
    # Factor exposures
    market_beta: float = 1.0  # Market beta
    size_factor_exposure: float = 0.0  # Size factor exposure
    value_factor_exposure: float = 0.0  # Value factor exposure
    momentum_factor_exposure: float = 0.0  # Momentum factor exposure
    quality_factor_exposure: float = 0.0  # Quality factor exposure
    
    # Correlation metrics
    average_correlation: float = 0.0  # Average pairwise correlation
    max_correlation: float = 0.0  # Maximum pairwise correlation
    min_correlation: float = 0.0  # Minimum pairwise correlation
    
    # Stress test results
    stress_test_results: Dict[str, float] = field(default_factory=dict)  # Stress scenario -> portfolio return
    
    # Risk-adjusted metrics
    information_ratio: float = 0.0  # Information ratio
    tracking_error: float = 0.0  # Tracking error vs benchmark
    max_drawdown: float = 0.0  # Maximum drawdown
    calmar_ratio: float = 0.0  # Calmar ratio
    sortino_ratio: float = 0.0  # Sortino ratio
    
    def __post_init__(self):
        """Post-initialization validation"""
        self.validate_risk_metrics()
    
    def validate_risk_metrics(self) -> None:
        """Validate risk metrics data integrity"""
        if not self.portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if self.lookback_period <= 0:
            raise ValueError("Lookback period must be positive")
        
        # VaR values should be negative (representing losses)
        if self.var_95 > 0:
            raise ValueError("VaR values should be negative (representing losses)")
        
        if self.var_99 > 0:
            raise ValueError("VaR values should be negative (representing losses)")
        
        # CVaR should be more negative than corresponding VaR
        if self.cvar_95 > self.var_95:
            raise ValueError("CVaR should be more negative than corresponding VaR")
        
        if self.cvar_99 > self.var_99:
            raise ValueError("CVaR should be more negative than corresponding VaR")
        
        # Beta should be reasonable
        if abs(self.market_beta) > 10:
            raise ValueError("Market beta should be between -10 and 10")
        
        # Correlation values should be between -1 and 1
        if not (-1 <= self.average_correlation <= 1):
            raise ValueError("Average correlation must be between -1 and 1")
        
        if not (-1 <= self.max_correlation <= 1):
            raise ValueError("Maximum correlation must be between -1 and 1")
        
        if not (-1 <= self.min_correlation <= 1):
            raise ValueError("Minimum correlation must be between -1 and 1")
    
    def get_risk_contribution(self, asset_id: str) -> float:
        """Get risk contribution for specific asset"""
        return self.risk_contributions.get(asset_id, 0.0)
    
    def set_risk_contribution(self, asset_id: str, contribution: float) -> None:
        """Set risk contribution for specific asset"""
        if contribution < 0 or contribution > 1:
            raise ValueError("Risk contribution must be between 0 and 1")
        
        self.risk_contributions[asset_id] = contribution
    
    def validate_risk_contributions(self) -> bool:
        """Validate that risk contributions sum to 1.0"""
        if not self.risk_contributions:
            return False
        
        total_contribution = sum(self.risk_contributions.values())
        return abs(total_contribution - 1.0) < 0.01
    
    def get_top_risk_contributors(self, n: int = 5) -> List[tuple]:
        """Get top N assets by risk contribution"""
        sorted_contributors = sorted(
            self.risk_contributions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_contributors[:n]
    
    def add_stress_test_result(self, scenario_name: str, portfolio_return: float) -> None:
        """Add stress test result"""
        self.stress_test_results[scenario_name] = portfolio_return
    
    def get_stress_test_result(self, scenario_name: str) -> float:
        """Get stress test result for scenario"""
        return self.stress_test_results.get(scenario_name, 0.0)
    
    def calculate_total_factor_exposure(self) -> float:
        """Calculate total factor exposure magnitude"""
        return (abs(self.market_beta) + 
                abs(self.size_factor_exposure) + 
                abs(self.value_factor_exposure) + 
                abs(self.momentum_factor_exposure) + 
                abs(self.quality_factor_exposure))
    
    def get_factor_exposure_summary(self) -> Dict[str, float]:
        """Get summary of factor exposures"""
        return {
            "market_beta": self.market_beta,
            "size_factor": self.size_factor_exposure,
            "value_factor": self.value_factor_exposure,
            "momentum_factor": self.momentum_factor_exposure,
            "quality_factor": self.quality_factor_exposure,
            "total_exposure": self.calculate_total_factor_exposure()
        }
    
    def calculate_diversification_ratio(self) -> float:
        """Calculate diversification ratio (weighted average vol / portfolio vol)"""
        if not self.risk_contributions:
            return 1.0
        
        # This would be calculated with actual asset volatilities
        # For now, return a placeholder calculation
        num_assets = len(self.risk_contributions)
        if num_assets <= 1:
            return 1.0
        
        # Simplified diversification ratio
        return min(num_assets / 2.0, 3.0)  # Cap at 3.0
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            "portfolio_id": self.portfolio_id,
            "calculation_date": self.calculation_date.isoformat(),
            "lookback_period": self.lookback_period,
            "value_at_risk": {
                "var_95": self.var_95,
                "var_99": self.var_99,
                "cvar_95": self.cvar_95,
                "cvar_99": self.cvar_99
            },
            "risk_decomposition": {
                "systematic_risk": self.systematic_risk,
                "idiosyncratic_risk": self.idiosyncratic_risk,
                "total_risk": self.systematic_risk + self.idiosyncratic_risk
            },
            "factor_exposures": self.get_factor_exposure_summary(),
            "correlation_metrics": {
                "average_correlation": self.average_correlation,
                "max_correlation": self.max_correlation,
                "min_correlation": self.min_correlation,
                "correlation_range": self.max_correlation - self.min_correlation
            },
            "risk_adjusted_metrics": {
                "information_ratio": self.information_ratio,
                "tracking_error": self.tracking_error,
                "max_drawdown": self.max_drawdown,
                "calmar_ratio": self.calmar_ratio,
                "sortino_ratio": self.sortino_ratio
            },
            "diversification": {
                "diversification_ratio": self.calculate_diversification_ratio(),
                "num_assets": len(self.risk_contributions),
                "top_risk_contributors": self.get_top_risk_contributors(3)
            },
            "stress_tests": self.stress_test_results
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert risk metrics to dictionary representation"""
        return {
            "risk_metrics_id": self.risk_metrics_id,
            "portfolio_id": self.portfolio_id,
            "calculation_date": self.calculation_date.isoformat(),
            "lookback_period": self.lookback_period,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "cvar_95": self.cvar_95,
            "cvar_99": self.cvar_99,
            "systematic_risk": self.systematic_risk,
            "idiosyncratic_risk": self.idiosyncratic_risk,
            "risk_contributions": self.risk_contributions,
            "market_beta": self.market_beta,
            "size_factor_exposure": self.size_factor_exposure,
            "value_factor_exposure": self.value_factor_exposure,
            "momentum_factor_exposure": self.momentum_factor_exposure,
            "quality_factor_exposure": self.quality_factor_exposure,
            "average_correlation": self.average_correlation,
            "max_correlation": self.max_correlation,
            "min_correlation": self.min_correlation,
            "stress_test_results": self.stress_test_results,
            "information_ratio": self.information_ratio,
            "tracking_error": self.tracking_error,
            "max_drawdown": self.max_drawdown,
            "calmar_ratio": self.calmar_ratio,
            "sortino_ratio": self.sortino_ratio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskMetrics':
        """Create risk metrics from dictionary representation"""
        metrics = cls()
        metrics.risk_metrics_id = data.get("risk_metrics_id", str(uuid.uuid4()))
        metrics.portfolio_id = data.get("portfolio_id", "")
        metrics.lookback_period = data.get("lookback_period", 252)
        metrics.var_95 = data.get("var_95", 0.0)
        metrics.var_99 = data.get("var_99", 0.0)
        metrics.cvar_95 = data.get("cvar_95", 0.0)
        metrics.cvar_99 = data.get("cvar_99", 0.0)
        metrics.systematic_risk = data.get("systematic_risk", 0.0)
        metrics.idiosyncratic_risk = data.get("idiosyncratic_risk", 0.0)
        metrics.risk_contributions = data.get("risk_contributions", {})
        metrics.market_beta = data.get("market_beta", 1.0)
        metrics.size_factor_exposure = data.get("size_factor_exposure", 0.0)
        metrics.value_factor_exposure = data.get("value_factor_exposure", 0.0)
        metrics.momentum_factor_exposure = data.get("momentum_factor_exposure", 0.0)
        metrics.quality_factor_exposure = data.get("quality_factor_exposure", 0.0)
        metrics.average_correlation = data.get("average_correlation", 0.0)
        metrics.max_correlation = data.get("max_correlation", 0.0)
        metrics.min_correlation = data.get("min_correlation", 0.0)
        metrics.stress_test_results = data.get("stress_test_results", {})
        metrics.information_ratio = data.get("information_ratio", 0.0)
        metrics.tracking_error = data.get("tracking_error", 0.0)
        metrics.max_drawdown = data.get("max_drawdown", 0.0)
        metrics.calmar_ratio = data.get("calmar_ratio", 0.0)
        metrics.sortino_ratio = data.get("sortino_ratio", 0.0)
        
        # Parse calculation date
        calculation_date = data.get("calculation_date")
        metrics.calculation_date = datetime.fromisoformat(calculation_date) if calculation_date else datetime.now()
        
        return metrics
    
    def __str__(self) -> str:
        return f"RiskMetrics({self.portfolio_id}, VaR95: {self.var_95:.2%}, Beta: {self.market_beta:.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()



