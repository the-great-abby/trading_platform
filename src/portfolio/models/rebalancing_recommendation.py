"""
RebalancingRecommendation Entity Model
Recommendation for portfolio rebalancing
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid


class RebalancingPriority(Enum):
    """Rebalancing priority enumeration"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class TradeRecommendation:
    """Individual trade recommendation within rebalancing"""
    
    # Primary identifiers
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_id: str = ""
    asset_id: str = ""
    
    # Trade details
    action: str = ""  # BUY, SELL, HOLD
    current_quantity: float = 0.0
    target_quantity: float = 0.0
    trade_quantity: float = 0.0
    
    # Trade metrics
    current_weight: float = 0.0
    target_weight: float = 0.0
    weight_change: float = 0.0
    
    # Price and cost information
    current_price: float = 0.0
    estimated_execution_price: float = 0.0
    estimated_cost: float = 0.0
    estimated_market_impact: float = 0.0
    
    # Tax considerations
    is_tax_loss_harvest: bool = False
    tax_lot_id: Optional[str] = None
    estimated_tax_savings: Optional[float] = None
    
    # Metadata
    priority: int = 1  # Trade priority (1 = highest)
    is_executed: bool = False
    execution_date: Optional[datetime] = None
    actual_execution_price: Optional[float] = None
    
    def __post_init__(self):
        """Post-initialization validation and calculation"""
        self.validate_trade_recommendation()
        self.calculate_trade_metrics()
    
    def validate_trade_recommendation(self) -> None:
        """Validate trade recommendation data integrity"""
        if not self.asset_id:
            raise ValueError("Asset ID is required")
        
        if not self.action:
            raise ValueError("Trade action is required")
        
        if self.action not in ["BUY", "SELL", "HOLD"]:
            raise ValueError("Trade action must be BUY, SELL, or HOLD")
        
        if self.current_quantity < 0:
            raise ValueError("Current quantity cannot be negative")
        
        if self.target_quantity < 0:
            raise ValueError("Target quantity cannot be negative")
        
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")
    
    def calculate_trade_metrics(self) -> None:
        """Calculate trade metrics"""
        # Calculate trade quantity
        if self.action == "BUY":
            self.trade_quantity = self.target_quantity - self.current_quantity
        elif self.action == "SELL":
            self.trade_quantity = self.current_quantity - self.target_quantity
        else:  # HOLD
            self.trade_quantity = 0.0
        
        # Calculate weight change
        self.weight_change = self.target_weight - self.current_weight
        
        # Calculate estimated execution price
        if self.estimated_execution_price == 0.0:
            self.estimated_execution_price = self.current_price
        
        # Calculate estimated cost
        self.estimated_cost = abs(self.trade_quantity) * self.estimated_execution_price
    
    def execute_trade(self, actual_price: float, execution_time: Optional[datetime] = None) -> None:
        """Mark trade as executed"""
        if actual_price <= 0:
            raise ValueError("Execution price must be positive")
        
        self.is_executed = True
        self.actual_execution_price = actual_price
        self.execution_date = execution_time or datetime.now()
        
        # Recalculate cost with actual price
        self.estimated_cost = abs(self.trade_quantity) * actual_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade recommendation to dictionary"""
        return {
            "trade_id": self.trade_id,
            "recommendation_id": self.recommendation_id,
            "asset_id": self.asset_id,
            "action": self.action,
            "current_quantity": self.current_quantity,
            "target_quantity": self.target_quantity,
            "trade_quantity": self.trade_quantity,
            "current_weight": self.current_weight,
            "target_weight": self.target_weight,
            "weight_change": self.weight_change,
            "current_price": self.current_price,
            "estimated_execution_price": self.estimated_execution_price,
            "estimated_cost": self.estimated_cost,
            "estimated_market_impact": self.estimated_market_impact,
            "is_tax_loss_harvest": self.is_tax_loss_harvest,
            "tax_lot_id": self.tax_lot_id,
            "estimated_tax_savings": self.estimated_tax_savings,
            "priority": self.priority,
            "is_executed": self.is_executed,
            "execution_date": self.execution_date.isoformat() if self.execution_date else None,
            "actual_execution_price": self.actual_execution_price
        }


@dataclass
class RebalancingRecommendation:
    """Recommendation for portfolio rebalancing"""
    
    # Primary identifiers
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str = ""
    optimization_id: str = ""
    
    # Recommendation details
    recommendation_date: datetime = field(default_factory=datetime.now)
    target_rebalancing_date: datetime = field(default_factory=datetime.now)
    priority: RebalancingPriority = RebalancingPriority.MEDIUM
    
    # Trade recommendations
    trades: List[TradeRecommendation] = field(default_factory=list)
    
    # Summary metrics
    total_trades: int = 0
    estimated_transaction_cost: float = 0.0
    estimated_market_impact: float = 0.0
    tracking_error_reduction: float = 0.0
    
    # Risk metrics
    expected_risk_reduction: float = 0.0
    expected_return_improvement: float = 0.0
    rebalancing_urgency: float = 0.0
    
    # Metadata
    is_executed: bool = False
    execution_date: Optional[datetime] = None
    execution_cost: Optional[float] = None
    
    def __post_init__(self):
        """Post-initialization validation and calculation"""
        self.validate_rebalancing_recommendation()
        self.calculate_summary_metrics()
    
    def validate_rebalancing_recommendation(self) -> None:
        """Validate rebalancing recommendation data integrity"""
        if not self.portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not self.optimization_id:
            raise ValueError("Optimization ID is required")
        
        if self.rebalancing_urgency < 0.0 or self.rebalancing_urgency > 1.0:
            raise ValueError("Rebalancing urgency must be between 0.0 and 1.0")
    
    def calculate_summary_metrics(self) -> None:
        """Calculate summary metrics from trades"""
        self.total_trades = len([t for t in self.trades if t.action != "HOLD"])
        
        # Calculate total costs
        self.estimated_transaction_cost = sum(
            t.estimated_cost for t in self.trades if t.action != "HOLD"
        )
        
        self.estimated_market_impact = sum(
            t.estimated_market_impact for t in self.trades if t.action != "HOLD"
        )
    
    def add_trade(self, trade: TradeRecommendation) -> None:
        """Add a trade recommendation"""
        trade.recommendation_id = self.recommendation_id
        self.trades.append(trade)
        self.calculate_summary_metrics()
    
    def remove_trade(self, trade_id: str) -> bool:
        """Remove a trade recommendation by ID"""
        for i, trade in enumerate(self.trades):
            if trade.trade_id == trade_id:
                del self.trades[i]
                self.calculate_summary_metrics()
                return True
        return False
    
    def get_trades_by_action(self, action: str) -> List[TradeRecommendation]:
        """Get trades filtered by action"""
        return [t for t in self.trades if t.action == action]
    
    def get_trades_by_priority(self, min_priority: int = 1) -> List[TradeRecommendation]:
        """Get trades with priority >= min_priority"""
        return [t for t in self.trades if t.priority >= min_priority]
    
    def get_tax_loss_harvest_trades(self) -> List[TradeRecommendation]:
        """Get tax-loss harvesting trades"""
        return [t for t in self.trades if t.is_tax_loss_harvest]
    
    def calculate_total_tax_savings(self) -> float:
        """Calculate total estimated tax savings"""
        return sum(
            t.estimated_tax_savings or 0.0 
            for t in self.get_tax_loss_harvest_trades()
        )
    
    def get_execution_status(self) -> Dict[str, int]:
        """Get execution status summary"""
        total_trades = len(self.trades)
        executed_trades = len([t for t in self.trades if t.is_executed])
        pending_trades = total_trades - executed_trades
        
        return {
            "total_trades": total_trades,
            "executed_trades": executed_trades,
            "pending_trades": pending_trades,
            "execution_percentage": (executed_trades / total_trades * 100) if total_trades > 0 else 0
        }
    
    def execute_all_trades(self, execution_prices: Dict[str, float]) -> bool:
        """Execute all trades with provided prices"""
        if self.is_executed:
            raise ValueError("Recommendation has already been executed")
        
        execution_time = datetime.now()
        all_executed = True
        
        for trade in self.trades:
            if trade.action != "HOLD" and trade.asset_id in execution_prices:
                try:
                    trade.execute_trade(execution_prices[trade.asset_id], execution_time)
                except ValueError:
                    all_executed = False
        
        if all_executed:
            self.is_executed = True
            self.execution_date = execution_time
            self.execution_cost = sum(t.estimated_cost for t in self.trades if t.is_executed)
        
        return all_executed
    
    def calculate_actual_performance(self, portfolio_before: 'Portfolio', portfolio_after: 'Portfolio') -> Dict[str, float]:
        """Calculate actual performance impact of rebalancing"""
        # This would be implemented with actual portfolio performance tracking
        return {
            "actual_tracking_error_reduction": 0.0,
            "actual_risk_reduction": 0.0,
            "actual_return_improvement": 0.0,
            "actual_transaction_costs": self.execution_cost or 0.0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rebalancing recommendation to dictionary representation"""
        return {
            "recommendation_id": self.recommendation_id,
            "portfolio_id": self.portfolio_id,
            "optimization_id": self.optimization_id,
            "recommendation_date": self.recommendation_date.isoformat(),
            "target_rebalancing_date": self.target_rebalancing_date.isoformat(),
            "priority": self.priority.value,
            "trades": [trade.to_dict() for trade in self.trades],
            "total_trades": self.total_trades,
            "estimated_transaction_cost": self.estimated_transaction_cost,
            "estimated_market_impact": self.estimated_market_impact,
            "tracking_error_reduction": self.tracking_error_reduction,
            "expected_risk_reduction": self.expected_risk_reduction,
            "expected_return_improvement": self.expected_return_improvement,
            "rebalancing_urgency": self.rebalancing_urgency,
            "is_executed": self.is_executed,
            "execution_date": self.execution_date.isoformat() if self.execution_date else None,
            "execution_cost": self.execution_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RebalancingRecommendation':
        """Create rebalancing recommendation from dictionary representation"""
        recommendation = cls()
        recommendation.recommendation_id = data.get("recommendation_id", str(uuid.uuid4()))
        recommendation.portfolio_id = data.get("portfolio_id", "")
        recommendation.optimization_id = data.get("optimization_id", "")
        recommendation.priority = RebalancingPriority(data.get("priority", "MEDIUM"))
        recommendation.total_trades = data.get("total_trades", 0)
        recommendation.estimated_transaction_cost = data.get("estimated_transaction_cost", 0.0)
        recommendation.estimated_market_impact = data.get("estimated_market_impact", 0.0)
        recommendation.tracking_error_reduction = data.get("tracking_error_reduction", 0.0)
        recommendation.expected_risk_reduction = data.get("expected_risk_reduction", 0.0)
        recommendation.expected_return_improvement = data.get("expected_return_improvement", 0.0)
        recommendation.rebalancing_urgency = data.get("rebalancing_urgency", 0.0)
        recommendation.is_executed = data.get("is_executed", False)
        recommendation.execution_cost = data.get("execution_cost")
        
        # Parse datetime fields
        recommendation_date = data.get("recommendation_date")
        recommendation.recommendation_date = datetime.fromisoformat(recommendation_date) if recommendation_date else datetime.now()
        
        target_date = data.get("target_rebalancing_date")
        recommendation.target_rebalancing_date = datetime.fromisoformat(target_date) if target_date else datetime.now()
        
        execution_date = data.get("execution_date")
        recommendation.execution_date = datetime.fromisoformat(execution_date) if execution_date else None
        
        # Parse trades
        trades_data = data.get("trades", [])
        recommendation.trades = []
        for trade_data in trades_data:
            trade = TradeRecommendation()
            trade.trade_id = trade_data.get("trade_id", str(uuid.uuid4()))
            trade.recommendation_id = recommendation.recommendation_id
            trade.asset_id = trade_data.get("asset_id", "")
            trade.action = trade_data.get("action", "")
            trade.current_quantity = trade_data.get("current_quantity", 0.0)
            trade.target_quantity = trade_data.get("target_quantity", 0.0)
            trade.trade_quantity = trade_data.get("trade_quantity", 0.0)
            trade.current_weight = trade_data.get("current_weight", 0.0)
            trade.target_weight = trade_data.get("target_weight", 0.0)
            trade.weight_change = trade_data.get("weight_change", 0.0)
            trade.current_price = trade_data.get("current_price", 0.0)
            trade.estimated_execution_price = trade_data.get("estimated_execution_price", 0.0)
            trade.estimated_cost = trade_data.get("estimated_cost", 0.0)
            trade.estimated_market_impact = trade_data.get("estimated_market_impact", 0.0)
            trade.is_tax_loss_harvest = trade_data.get("is_tax_loss_harvest", False)
            trade.tax_lot_id = trade_data.get("tax_lot_id")
            trade.estimated_tax_savings = trade_data.get("estimated_tax_savings")
            trade.priority = trade_data.get("priority", 1)
            trade.is_executed = trade_data.get("is_executed", False)
            trade.actual_execution_price = trade_data.get("actual_execution_price")
            
            # Parse execution date
            execution_date = trade_data.get("execution_date")
            trade.execution_date = datetime.fromisoformat(execution_date) if execution_date else None
            
            recommendation.trades.append(trade)
        
        return recommendation
    
    def __str__(self) -> str:
        return f"RebalancingRecommendation({self.recommendation_id}, {self.total_trades} trades, {self.priority.value} priority)"
    
    def __repr__(self) -> str:
        return self.__str__()


# Forward reference for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .portfolio import Portfolio






















