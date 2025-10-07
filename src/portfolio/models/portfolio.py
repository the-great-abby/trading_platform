"""
Portfolio Entity Model
Core portfolio entity containing assets and metadata
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid


class PortfolioStatus(Enum):
    """Portfolio status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class RiskTolerance(Enum):
    """Risk tolerance enumeration"""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class RebalancingFrequency(Enum):
    """Rebalancing frequency enumeration"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


@dataclass
class Portfolio:
    """Core portfolio entity containing assets and metadata"""
    
    # Primary identifiers
    portfolio_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    owner_id: str = ""
    
    # Portfolio metadata
    creation_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    status: PortfolioStatus = PortfolioStatus.ACTIVE
    
    # Portfolio configuration
    base_currency: str = "USD"
    rebalancing_frequency: RebalancingFrequency = RebalancingFrequency.MONTHLY
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    
    # Portfolio constraints
    max_single_asset_weight: float = 0.10  # 10% max per asset
    max_sector_weight: float = 0.30  # 30% max per sector
    min_liquidity_requirement: float = 1000000000  # $1B minimum market cap
    long_only: bool = True
    
    # Portfolio state
    total_value: float = 0.0
    cash_balance: float = 0.0
    total_invested: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Performance metrics (calculated)
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    
    # Relationships (will be populated by services)
    positions: List['Position'] = field(default_factory=list)
    optimization_results: List['OptimizationResult'] = field(default_factory=list)
    rebalancing_history: List['RebalancingEvent'] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        self.validate_portfolio()
        self.update_last_modified()
    
    def validate_portfolio(self) -> None:
        """Validate portfolio data integrity"""
        if not self.name:
            raise ValueError("Portfolio name is required")
        
        if not self.owner_id:
            raise ValueError("Portfolio owner_id is required")
        
        if self.max_single_asset_weight <= 0 or self.max_single_asset_weight > 1.0:
            raise ValueError("max_single_asset_weight must be between 0 and 1")
        
        if self.max_sector_weight <= 0 or self.max_sector_weight > 1.0:
            raise ValueError("max_sector_weight must be between 0 and 1")
        
        if self.total_value < 0:
            raise ValueError("total_value cannot be negative")
        
        if self.cash_balance < 0:
            raise ValueError("cash_balance cannot be negative")
    
    def update_last_modified(self) -> None:
        """Update last_updated timestamp"""
        self.last_updated = datetime.now()
    
    def calculate_total_value(self) -> float:
        """Calculate total portfolio value from positions and cash"""
        position_value = sum(pos.market_value for pos in self.positions)
        return position_value + self.cash_balance
    
    def calculate_portfolio_weights(self) -> Dict[str, float]:
        """Calculate current portfolio weights"""
        if self.total_value == 0:
            return {}
        
        weights = {}
        for position in self.positions:
            weights[position.asset_id] = position.market_value / self.total_value
        
        return weights
    
    def validate_weights(self) -> bool:
        """Validate that portfolio weights sum to approximately 1.0"""
        weights = self.calculate_portfolio_weights()
        total_weight = sum(weights.values())
        return abs(total_weight - 1.0) < 0.01
    
    def check_constraints(self) -> List[str]:
        """Check portfolio constraints and return violations"""
        violations = []
        weights = self.calculate_portfolio_weights()
        
        # Check individual asset weight constraints
        for asset_id, weight in weights.items():
            if weight > self.max_single_asset_weight:
                violations.append(f"Asset {asset_id} weight {weight:.2%} exceeds maximum {self.max_single_asset_weight:.2%}")
        
        # Check sector weight constraints (would need sector mapping)
        # This would be implemented with actual sector data
        
        return violations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio to dictionary representation"""
        return {
            "portfolio_id": self.portfolio_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "creation_date": self.creation_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": self.status.value,
            "base_currency": self.base_currency,
            "rebalancing_frequency": self.rebalancing_frequency.value,
            "risk_tolerance": self.risk_tolerance.value,
            "max_single_asset_weight": self.max_single_asset_weight,
            "max_sector_weight": self.max_sector_weight,
            "min_liquidity_requirement": self.min_liquidity_requirement,
            "long_only": self.long_only,
            "total_value": self.total_value,
            "cash_balance": self.cash_balance,
            "total_invested": self.total_invested,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "calmar_ratio": self.calmar_ratio,
            "positions": [pos.to_dict() for pos in self.positions],
            "optimization_results": [opt.to_dict() for opt in self.optimization_results],
            "rebalancing_history": [event.to_dict() for event in self.rebalancing_history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Portfolio':
        """Create portfolio from dictionary representation"""
        portfolio = cls()
        portfolio.portfolio_id = data.get("portfolio_id", str(uuid.uuid4()))
        portfolio.name = data.get("name", "")
        portfolio.description = data.get("description", "")
        portfolio.owner_id = data.get("owner_id", "")
        portfolio.creation_date = datetime.fromisoformat(data.get("creation_date", datetime.now().isoformat()))
        portfolio.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        portfolio.status = PortfolioStatus(data.get("status", "ACTIVE"))
        portfolio.base_currency = data.get("base_currency", "USD")
        portfolio.rebalancing_frequency = RebalancingFrequency(data.get("rebalancing_frequency", "MONTHLY"))
        portfolio.risk_tolerance = RiskTolerance(data.get("risk_tolerance", "MODERATE"))
        portfolio.max_single_asset_weight = data.get("max_single_asset_weight", 0.10)
        portfolio.max_sector_weight = data.get("max_sector_weight", 0.30)
        portfolio.min_liquidity_requirement = data.get("min_liquidity_requirement", 1000000000)
        portfolio.long_only = data.get("long_only", True)
        portfolio.total_value = data.get("total_value", 0.0)
        portfolio.cash_balance = data.get("cash_balance", 0.0)
        portfolio.total_invested = data.get("total_invested", 0.0)
        portfolio.unrealized_pnl = data.get("unrealized_pnl", 0.0)
        portfolio.realized_pnl = data.get("realized_pnl", 0.0)
        portfolio.total_return = data.get("total_return", 0.0)
        portfolio.annualized_return = data.get("annualized_return", 0.0)
        portfolio.volatility = data.get("volatility", 0.0)
        portfolio.sharpe_ratio = data.get("sharpe_ratio", 0.0)
        portfolio.max_drawdown = data.get("max_drawdown", 0.0)
        portfolio.calmar_ratio = data.get("calmar_ratio", 0.0)
        
        # Relationships would be loaded separately by services
        portfolio.positions = []
        portfolio.optimization_results = []
        portfolio.rebalancing_history = []
        
        return portfolio
    
    def __str__(self) -> str:
        return f"Portfolio({self.portfolio_id}, {self.name}, ${self.total_value:,.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .position import Position
    from .optimization_result import OptimizationResult
    from .rebalancing_event import RebalancingEvent






















