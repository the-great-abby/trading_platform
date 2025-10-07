"""
Position Entity Model
Individual position within a portfolio
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class Position:
    """Individual position within a portfolio"""
    
    # Primary identifiers
    position_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str = ""
    asset_id: str = ""
    
    # Position details
    quantity: float = 0.0
    average_cost: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    
    # Position metrics
    cost_basis: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    weight: float = 0.0
    
    # Tax information
    holding_period: int = 0  # Days held
    is_long_term: bool = False  # True if held > 1 year
    tax_lot_id: str = ""
    
    # Metadata
    first_purchase_date: Optional[datetime] = None
    last_purchase_date: Optional[datetime] = None
    last_sale_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization validation and calculation"""
        self.validate_position()
        self.calculate_metrics()
        self.update_updated_at()
    
    def validate_position(self) -> None:
        """Validate position data integrity"""
        if not self.portfolio_id:
            raise ValueError("Position portfolio_id is required")
        
        if not self.asset_id:
            raise ValueError("Position asset_id is required")
        
        if self.quantity < 0:
            raise ValueError("Position quantity cannot be negative")
        
        if self.average_cost <= 0:
            raise ValueError("Position average_cost must be positive")
        
        if self.current_price < 0:
            raise ValueError("Position current_price cannot be negative")
    
    def calculate_metrics(self) -> None:
        """Calculate position metrics"""
        # Market value
        self.market_value = self.quantity * self.current_price
        
        # Cost basis
        self.cost_basis = self.quantity * self.average_cost
        
        # Unrealized P&L
        self.unrealized_pnl = self.market_value - self.cost_basis
        
        # Unrealized P&L percentage
        if self.cost_basis > 0:
            self.unrealized_pnl_pct = self.unrealized_pnl / self.cost_basis
        else:
            self.unrealized_pnl_pct = 0.0
        
        # Update holding period and long-term status
        self.update_holding_period()
    
    def update_holding_period(self) -> None:
        """Update holding period and long-term status"""
        if self.first_purchase_date:
            delta = datetime.now() - self.first_purchase_date
            self.holding_period = delta.days
            self.is_long_term = self.holding_period > 365  # More than 1 year
    
    def update_updated_at(self) -> None:
        """Update updated_at timestamp"""
        self.updated_at = datetime.now()
    
    def update_price(self, new_price: float) -> None:
        """Update position with new price and recalculate metrics"""
        if new_price < 0:
            raise ValueError("Price cannot be negative")
        
        self.current_price = new_price
        self.calculate_metrics()
        self.update_updated_at()
    
    def add_shares(self, additional_quantity: float, purchase_price: float) -> None:
        """Add shares to position and update average cost"""
        if additional_quantity <= 0:
            raise ValueError("Additional quantity must be positive")
        
        if purchase_price <= 0:
            raise ValueError("Purchase price must be positive")
        
        # Calculate new average cost
        total_cost = (self.quantity * self.average_cost) + (additional_quantity * purchase_price)
        self.quantity += additional_quantity
        self.average_cost = total_cost / self.quantity
        
        # Update current price and recalculate
        self.current_price = purchase_price
        self.calculate_metrics()
        
        # Update purchase dates
        now = datetime.now()
        if not self.first_purchase_date:
            self.first_purchase_date = now
        self.last_purchase_date = now
        
        self.update_updated_at()
    
    def remove_shares(self, quantity_to_remove: float) -> float:
        """Remove shares from position and return realized P&L"""
        if quantity_to_remove <= 0:
            raise ValueError("Quantity to remove must be positive")
        
        if quantity_to_remove > self.quantity:
            raise ValueError("Cannot remove more shares than owned")
        
        # Calculate realized P&L
        realized_pnl = (self.current_price - self.average_cost) * quantity_to_remove
        
        # Update position
        self.quantity -= quantity_to_remove
        self.calculate_metrics()
        
        # Update sale date
        self.last_sale_date = datetime.now()
        self.update_updated_at()
        
        return realized_pnl
    
    def close_position(self) -> float:
        """Close entire position and return total realized P&L"""
        realized_pnl = self.remove_shares(self.quantity)
        return realized_pnl
    
    def calculate_weight_in_portfolio(self, portfolio_total_value: float) -> float:
        """Calculate position weight in portfolio"""
        if portfolio_total_value == 0:
            return 0.0
        
        self.weight = self.market_value / portfolio_total_value
        return self.weight
    
    def get_tax_lot_info(self) -> Dict[str, Any]:
        """Get tax lot information for tax optimization"""
        return {
            "tax_lot_id": self.tax_lot_id,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "holding_period": self.holding_period,
            "is_long_term": self.is_long_term,
            "unrealized_pnl": self.unrealized_pnl,
            "first_purchase_date": self.first_purchase_date.isoformat() if self.first_purchase_date else None,
            "last_purchase_date": self.last_purchase_date.isoformat() if self.last_purchase_date else None
        }
    
    def is_tax_loss_harvest_candidate(self, min_loss_threshold: float = 0.05) -> bool:
        """Check if position is a candidate for tax-loss harvesting"""
        return (self.unrealized_pnl < 0 and 
                abs(self.unrealized_pnl_pct) >= min_loss_threshold and
                not self.is_long_term)  # Short-term losses are better for tax harvesting
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary representation"""
        return {
            "position_id": self.position_id,
            "portfolio_id": self.portfolio_id,
            "asset_id": self.asset_id,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "weight": self.weight,
            "holding_period": self.holding_period,
            "is_long_term": self.is_long_term,
            "tax_lot_id": self.tax_lot_id,
            "first_purchase_date": self.first_purchase_date.isoformat() if self.first_purchase_date else None,
            "last_purchase_date": self.last_purchase_date.isoformat() if self.last_purchase_date else None,
            "last_sale_date": self.last_sale_date.isoformat() if self.last_sale_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create position from dictionary representation"""
        position = cls()
        position.position_id = data.get("position_id", str(uuid.uuid4()))
        position.portfolio_id = data.get("portfolio_id", "")
        position.asset_id = data.get("asset_id", "")
        position.quantity = data.get("quantity", 0.0)
        position.average_cost = data.get("average_cost", 0.0)
        position.current_price = data.get("current_price", 0.0)
        position.market_value = data.get("market_value", 0.0)
        position.cost_basis = data.get("cost_basis", 0.0)
        position.unrealized_pnl = data.get("unrealized_pnl", 0.0)
        position.unrealized_pnl_pct = data.get("unrealized_pnl_pct", 0.0)
        position.weight = data.get("weight", 0.0)
        position.holding_period = data.get("holding_period", 0)
        position.is_long_term = data.get("is_long_term", False)
        position.tax_lot_id = data.get("tax_lot_id", "")
        
        # Parse datetime fields
        first_purchase = data.get("first_purchase_date")
        position.first_purchase_date = datetime.fromisoformat(first_purchase) if first_purchase else None
        
        last_purchase = data.get("last_purchase_date")
        position.last_purchase_date = datetime.fromisoformat(last_purchase) if last_purchase else None
        
        last_sale = data.get("last_sale_date")
        position.last_sale_date = datetime.fromisoformat(last_sale) if last_sale else None
        
        position.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        position.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        
        return position
    
    def __str__(self) -> str:
        return f"Position({self.asset_id}, {self.quantity:.2f} shares, ${self.market_value:,.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()




















