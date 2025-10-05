"""
OptimizationResult Entity Model
Result of portfolio optimization
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid


class OptimizationMethod(Enum):
    """Optimization method enumeration"""
    MPT = "MPT"  # Modern Portfolio Theory
    BLACK_LITTERMAN = "BLACK_LITTERMAN"
    RISK_PARITY = "RISK_PARITY"
    MEAN_VARIANCE = "MEAN_VARIANCE"
    MAXIMUM_SHARPE = "MAXIMUM_SHARPE"
    MINIMUM_VARIANCE = "MINIMUM_VARIANCE"


@dataclass
class EfficientFrontierPoint:
    """Point on the efficient frontier"""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    asset_weights: Dict[str, float]


@dataclass
class OptimizationResult:
    """Result of portfolio optimization"""
    
    # Primary identifiers
    optimization_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str = ""
    
    # Optimization parameters
    optimization_method: OptimizationMethod = OptimizationMethod.MPT
    risk_free_rate: float = 0.02
    optimization_date: datetime = field(default_factory=datetime.now)
    
    # Optimization results
    expected_return: float = 0.0
    expected_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Optimal weights
    asset_weights: Dict[str, float] = field(default_factory=dict)
    sector_weights: Dict[str, float] = field(default_factory=dict)
    asset_class_weights: Dict[str, float] = field(default_factory=dict)
    
    # Risk metrics
    portfolio_var: float = 0.0  # Value at Risk (95%)
    portfolio_cvar: float = 0.0  # Conditional VaR (95%)
    max_drawdown: float = 0.0
    beta: float = 1.0
    
    # Optimization metadata
    convergence_status: bool = False
    optimization_time: float = 0.0  # Time taken in seconds
    iteration_count: int = 0
    constraint_violations: List[str] = field(default_factory=list)
    
    # Relationships
    efficient_frontier: List[EfficientFrontierPoint] = field(default_factory=list)
    risk_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Additional metrics
    information_ratio: float = 0.0
    tracking_error: float = 0.0
    turnover: float = 0.0
    transaction_costs: float = 0.0
    
    def __post_init__(self):
        """Post-initialization validation and calculation"""
        self.validate_optimization_result()
        self.calculate_additional_metrics()
    
    def validate_optimization_result(self) -> None:
        """Validate optimization result data integrity"""
        if not self.portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if self.expected_volatility < 0:
            raise ValueError("Expected volatility cannot be negative")
        
        if self.risk_free_rate < 0 or self.risk_free_rate > 1:
            raise ValueError("Risk-free rate must be between 0 and 1")
        
        if self.optimization_time < 0:
            raise ValueError("Optimization time cannot be negative")
        
        if self.iteration_count < 0:
            raise ValueError("Iteration count cannot be negative")
    
    def calculate_additional_metrics(self) -> None:
        """Calculate additional optimization metrics"""
        # Calculate Sharpe ratio if not provided
        if self.sharpe_ratio == 0.0 and self.expected_volatility > 0:
            self.sharpe_ratio = (self.expected_return - self.risk_free_rate) / self.expected_volatility
        
        # Validate asset weights sum to 1.0
        if self.asset_weights:
            total_weight = sum(self.asset_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                self.constraint_violations.append(f"Asset weights sum to {total_weight:.4f}, not 1.0")
    
    def validate_weights(self) -> bool:
        """Validate that asset weights are valid"""
        if not self.asset_weights:
            return False
        
        # Check weights sum to 1.0
        total_weight = sum(self.asset_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            return False
        
        # Check all weights are non-negative (for long-only portfolios)
        if any(weight < 0 for weight in self.asset_weights.values()):
            return False
        
        return True
    
    def get_weight(self, asset_id: str) -> float:
        """Get weight for specific asset"""
        return self.asset_weights.get(asset_id, 0.0)
    
    def set_weight(self, asset_id: str, weight: float) -> None:
        """Set weight for specific asset"""
        if weight < 0:
            raise ValueError("Asset weight cannot be negative")
        
        self.asset_weights[asset_id] = weight
        self.calculate_additional_metrics()
    
    def get_top_holdings(self, n: int = 10) -> List[tuple]:
        """Get top N holdings by weight"""
        sorted_holdings = sorted(self.asset_weights.items(), 
                               key=lambda x: x[1], reverse=True)
        return sorted_holdings[:n]
    
    def calculate_concentration_metrics(self) -> Dict[str, float]:
        """Calculate portfolio concentration metrics"""
        if not self.asset_weights:
            return {}
        
        weights = list(self.asset_weights.values())
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(w ** 2 for w in weights)
        
        # Effective number of assets
        effective_assets = 1 / hhi if hhi > 0 else 0
        
        # Largest position weight
        max_weight = max(weights) if weights else 0
        
        # Number of assets with weight > 5%
        large_positions = sum(1 for w in weights if w > 0.05)
        
        return {
            "hhi": hhi,
            "effective_assets": effective_assets,
            "max_weight": max_weight,
            "large_positions": large_positions,
            "total_assets": len(weights)
        }
    
    def get_risk_contribution(self, asset_id: str) -> float:
        """Get risk contribution for specific asset"""
        return self.risk_contributions.get(asset_id, 0.0)
    
    def set_risk_contribution(self, asset_id: str, contribution: float) -> None:
        """Set risk contribution for specific asset"""
        self.risk_contributions[asset_id] = contribution
    
    def validate_risk_contributions(self) -> bool:
        """Validate that risk contributions sum to 1.0"""
        if not self.risk_contributions:
            return False
        
        total_contribution = sum(self.risk_contributions.values())
        return abs(total_contribution - 1.0) < 0.01
    
    def add_efficient_frontier_point(self, 
                                   expected_return: float, 
                                   volatility: float, 
                                   asset_weights: Dict[str, float]) -> None:
        """Add a point to the efficient frontier"""
        sharpe_ratio = (expected_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        point = EfficientFrontierPoint(
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            asset_weights=asset_weights
        )
        
        self.efficient_frontier.append(point)
    
    def get_optimal_portfolio_for_volatility(self, target_volatility: float) -> Optional[EfficientFrontierPoint]:
        """Find optimal portfolio for target volatility"""
        if not self.efficient_frontier:
            return None
        
        # Find point with closest volatility to target
        closest_point = min(self.efficient_frontier, 
                          key=lambda x: abs(x.volatility - target_volatility))
        
        return closest_point
    
    def get_optimal_portfolio_for_return(self, target_return: float) -> Optional[EfficientFrontierPoint]:
        """Find optimal portfolio for target return"""
        if not self.efficient_frontier:
            return None
        
        # Find point with closest return to target
        closest_point = min(self.efficient_frontier, 
                          key=lambda x: abs(x.expected_return - target_return))
        
        return closest_point
    
    def calculate_expected_transaction_costs(self, 
                                          current_weights: Dict[str, float], 
                                          cost_rate: float = 0.001) -> float:
        """Calculate expected transaction costs for rebalancing"""
        if not self.asset_weights or not current_weights:
            return 0.0
        
        total_cost = 0.0
        for asset_id in set(self.asset_weights.keys()) | set(current_weights.keys()):
            target_weight = self.asset_weights.get(asset_id, 0.0)
            current_weight = current_weights.get(asset_id, 0.0)
            weight_change = abs(target_weight - current_weight)
            total_cost += weight_change * cost_rate
        
        return total_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert optimization result to dictionary representation"""
        return {
            "optimization_id": self.optimization_id,
            "portfolio_id": self.portfolio_id,
            "optimization_method": self.optimization_method.value,
            "risk_free_rate": self.risk_free_rate,
            "optimization_date": self.optimization_date.isoformat(),
            "expected_return": self.expected_return,
            "expected_volatility": self.expected_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "asset_weights": self.asset_weights,
            "sector_weights": self.sector_weights,
            "asset_class_weights": self.asset_class_weights,
            "portfolio_var": self.portfolio_var,
            "portfolio_cvar": self.portfolio_cvar,
            "max_drawdown": self.max_drawdown,
            "beta": self.beta,
            "convergence_status": self.convergence_status,
            "optimization_time": self.optimization_time,
            "iteration_count": self.iteration_count,
            "constraint_violations": self.constraint_violations,
            "efficient_frontier": [
                {
                    "expected_return": point.expected_return,
                    "volatility": point.volatility,
                    "sharpe_ratio": point.sharpe_ratio,
                    "asset_weights": point.asset_weights
                }
                for point in self.efficient_frontier
            ],
            "risk_contributions": self.risk_contributions,
            "information_ratio": self.information_ratio,
            "tracking_error": self.tracking_error,
            "turnover": self.turnover,
            "transaction_costs": self.transaction_costs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationResult':
        """Create optimization result from dictionary representation"""
        result = cls()
        result.optimization_id = data.get("optimization_id", str(uuid.uuid4()))
        result.portfolio_id = data.get("portfolio_id", "")
        result.optimization_method = OptimizationMethod(data.get("optimization_method", "MPT"))
        result.risk_free_rate = data.get("risk_free_rate", 0.02)
        result.expected_return = data.get("expected_return", 0.0)
        result.expected_volatility = data.get("expected_volatility", 0.0)
        result.sharpe_ratio = data.get("sharpe_ratio", 0.0)
        result.asset_weights = data.get("asset_weights", {})
        result.sector_weights = data.get("sector_weights", {})
        result.asset_class_weights = data.get("asset_class_weights", {})
        result.portfolio_var = data.get("portfolio_var", 0.0)
        result.portfolio_cvar = data.get("portfolio_cvar", 0.0)
        result.max_drawdown = data.get("max_drawdown", 0.0)
        result.beta = data.get("beta", 1.0)
        result.convergence_status = data.get("convergence_status", False)
        result.optimization_time = data.get("optimization_time", 0.0)
        result.iteration_count = data.get("iteration_count", 0)
        result.constraint_violations = data.get("constraint_violations", [])
        result.risk_contributions = data.get("risk_contributions", {})
        result.information_ratio = data.get("information_ratio", 0.0)
        result.tracking_error = data.get("tracking_error", 0.0)
        result.turnover = data.get("turnover", 0.0)
        result.transaction_costs = data.get("transaction_costs", 0.0)
        
        # Parse datetime
        optimization_date = data.get("optimization_date")
        result.optimization_date = datetime.fromisoformat(optimization_date) if optimization_date else datetime.now()
        
        # Parse efficient frontier
        efficient_frontier_data = data.get("efficient_frontier", [])
        result.efficient_frontier = [
            EfficientFrontierPoint(
                expected_return=point["expected_return"],
                volatility=point["volatility"],
                sharpe_ratio=point["sharpe_ratio"],
                asset_weights=point["asset_weights"]
            )
            for point in efficient_frontier_data
        ]
        
        return result
    
    def __str__(self) -> str:
        return f"OptimizationResult({self.optimization_method.value}, Return: {self.expected_return:.2%}, Vol: {self.expected_volatility:.2%})"
    
    def __repr__(self) -> str:
        return self.__str__()












