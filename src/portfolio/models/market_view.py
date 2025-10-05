"""
MarketView Entity Model
User-defined market view for Black-Litterman model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid


class ViewType(Enum):
    """Market view type enumeration"""
    ABSOLUTE = "ABSOLUTE"  # "Asset X will return 5%"
    RELATIVE = "RELATIVE"  # "Asset X will outperform Asset Y by 2%"


@dataclass
class MarketView:
    """User-defined market view for Black-Litterman model"""
    
    # Primary identifiers
    view_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str = ""
    
    # View details
    view_type: ViewType = ViewType.ABSOLUTE
    view_description: str = ""
    
    # Absolute views (e.g., "AAPL will return 5%")
    target_asset_id: Optional[str] = None
    expected_return: Optional[float] = None
    
    # Relative views (e.g., "AAPL will outperform MSFT by 2%")
    outperforming_asset_id: Optional[str] = None
    underperforming_asset_id: Optional[str] = None
    relative_return: Optional[float] = None
    
    # Confidence and metadata
    confidence_level: float = 0.5  # 0.0 to 1.0
    view_date: datetime = field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None
    is_active: bool = True
    
    # Relationships (will be populated by services)
    optimization_results: List['OptimizationResult'] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization validation"""
        self.validate_market_view()
    
    def validate_market_view(self) -> None:
        """Validate market view data integrity"""
        if not self.portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not self.view_description:
            raise ValueError("View description is required")
        
        if self.confidence_level < 0.0 or self.confidence_level > 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
        
        # Validate view type specific requirements
        if self.view_type == ViewType.ABSOLUTE:
            if not self.target_asset_id:
                raise ValueError("Target asset ID is required for absolute view")
            if self.expected_return is None:
                raise ValueError("Expected return is required for absolute view")
        elif self.view_type == ViewType.RELATIVE:
            if not self.outperforming_asset_id:
                raise ValueError("Outperforming asset ID is required for relative view")
            if not self.underperforming_asset_id:
                raise ValueError("Underperforming asset ID is required for relative view")
            if self.relative_return is None:
                raise ValueError("Relative return is required for relative view")
            
            # Ensure different assets for relative view
            if self.outperforming_asset_id == self.underperforming_asset_id:
                raise ValueError("Outperforming and underperforming assets must be different")
        
        # Validate expected returns are reasonable
        if self.expected_return is not None:
            if self.expected_return < -1.0 or self.expected_return > 10.0:
                raise ValueError("Expected return must be between -100% and 1000%")
        
        if self.relative_return is not None:
            if abs(self.relative_return) > 1.0:
                raise ValueError("Relative return must be between -100% and 100%")
    
    def is_expired(self) -> bool:
        """Check if view has expired"""
        if self.expiry_date is None:
            return False
        return datetime.now() > self.expiry_date
    
    def is_valid(self) -> bool:
        """Check if view is valid and active"""
        return self.is_active and not self.is_expired()
    
    def get_view_vector(self, asset_ids: List[str]) -> List[float]:
        """Get view vector for Black-Litterman optimization"""
        view_vector = [0.0] * len(asset_ids)
        
        if not self.is_valid():
            return view_vector
        
        try:
            if self.view_type == ViewType.ABSOLUTE:
                asset_index = asset_ids.index(self.target_asset_id)
                view_vector[asset_index] = self.expected_return
            elif self.view_type == ViewType.RELATIVE:
                outperforming_index = asset_ids.index(self.outperforming_asset_id)
                underperforming_index = asset_ids.index(self.underperforming_asset_id)
                view_vector[outperforming_index] = self.relative_return
                view_vector[underperforming_index] = -self.relative_return
        except ValueError:
            # Asset not found in the list
            pass
        
        return view_vector
    
    def get_view_matrix_row(self, asset_ids: List[str]) -> List[float]:
        """Get view matrix row for Black-Litterman optimization"""
        view_row = [0.0] * len(asset_ids)
        
        if not self.is_valid():
            return view_row
        
        try:
            if self.view_type == ViewType.ABSOLUTE:
                asset_index = asset_ids.index(self.target_asset_id)
                view_row[asset_index] = 1.0
            elif self.view_type == ViewType.RELATIVE:
                outperforming_index = asset_ids.index(self.outperforming_asset_id)
                underperforming_index = asset_ids.index(self.underperforming_asset_id)
                view_row[outperforming_index] = 1.0
                view_row[underperforming_index] = -1.0
        except ValueError:
            # Asset not found in the list
            pass
        
        return view_row
    
    def get_uncertainty(self, tau: float = 0.025) -> float:
        """Get uncertainty for this view (Omega matrix diagonal element)"""
        # Higher confidence = lower uncertainty
        # Lower confidence = higher uncertainty
        base_uncertainty = 0.1  # Base uncertainty level
        
        confidence_factor = 1.0 - self.confidence_level
        uncertainty = base_uncertainty * (1.0 + confidence_factor * 4.0)  # 0.1 to 0.5 range
        
        return uncertainty * tau
    
    def update_confidence(self, new_confidence: float) -> None:
        """Update confidence level"""
        if new_confidence < 0.0 or new_confidence > 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
        
        self.confidence_level = new_confidence
    
    def extend_expiry(self, days: int = 30) -> None:
        """Extend view expiry date"""
        if self.expiry_date is None:
            self.expiry_date = datetime.now()
        
        from datetime import timedelta
        self.expiry_date += timedelta(days=days)
    
    def deactivate(self) -> None:
        """Deactivate the view"""
        self.is_active = False
    
    def activate(self) -> None:
        """Activate the view"""
        if self.is_expired():
            raise ValueError("Cannot activate expired view")
        self.is_active = True
    
    def get_impact_summary(self) -> str:
        """Get human-readable summary of view impact"""
        if not self.is_valid():
            return "View is inactive or expired"
        
        if self.view_type == ViewType.ABSOLUTE:
            return f"{self.target_asset_id} expected to return {self.expected_return:.2%} (confidence: {self.confidence_level:.1%})"
        else:
            return f"{self.outperforming_asset_id} expected to outperform {self.underperforming_asset_id} by {self.relative_return:.2%} (confidence: {self.confidence_level:.1%})"
    
    def conflicts_with(self, other_view: 'MarketView') -> bool:
        """Check if this view conflicts with another view"""
        if not (self.is_valid() and other_view.is_valid()):
            return False
        
        # Check for conflicting absolute views on same asset
        if (self.view_type == ViewType.ABSOLUTE and 
            other_view.view_type == ViewType.ABSOLUTE and
            self.target_asset_id == other_view.target_asset_id):
            return True
        
        # Check for conflicting relative views
        if (self.view_type == ViewType.RELATIVE and 
            other_view.view_type == ViewType.RELATIVE):
            # Same outperforming/underperforming pair with opposite directions
            if ((self.outperforming_asset_id == other_view.underperforming_asset_id and
                 self.underperforming_asset_id == other_view.outperforming_asset_id) or
                (self.outperforming_asset_id == other_view.outperforming_asset_id and
                 self.underperforming_asset_id == other_view.underperforming_asset_id and
                 self.relative_return * other_view.relative_return < 0)):
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert market view to dictionary representation"""
        return {
            "view_id": self.view_id,
            "portfolio_id": self.portfolio_id,
            "view_type": self.view_type.value,
            "view_description": self.view_description,
            "target_asset_id": self.target_asset_id,
            "expected_return": self.expected_return,
            "outperforming_asset_id": self.outperforming_asset_id,
            "underperforming_asset_id": self.underperforming_asset_id,
            "relative_return": self.relative_return,
            "confidence_level": self.confidence_level,
            "view_date": self.view_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "is_active": self.is_active,
            "optimization_results": [opt.optimization_id for opt in self.optimization_results]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketView':
        """Create market view from dictionary representation"""
        view = cls()
        view.view_id = data.get("view_id", str(uuid.uuid4()))
        view.portfolio_id = data.get("portfolio_id", "")
        view.view_type = ViewType(data.get("view_type", "ABSOLUTE"))
        view.view_description = data.get("view_description", "")
        view.target_asset_id = data.get("target_asset_id")
        view.expected_return = data.get("expected_return")
        view.outperforming_asset_id = data.get("outperforming_asset_id")
        view.underperforming_asset_id = data.get("underperforming_asset_id")
        view.relative_return = data.get("relative_return")
        view.confidence_level = data.get("confidence_level", 0.5)
        view.is_active = data.get("is_active", True)
        
        # Parse datetime fields
        view_date = data.get("view_date")
        view.view_date = datetime.fromisoformat(view_date) if view_date else datetime.now()
        
        expiry_date = data.get("expiry_date")
        view.expiry_date = datetime.fromisoformat(expiry_date) if expiry_date else None
        
        # Optimization results would be loaded separately by services
        view.optimization_results = []
        
        return view
    
    def __str__(self) -> str:
        return f"MarketView({self.view_type.value}, {self.view_description[:50]}...)"
    
    def __repr__(self) -> str:
        return self.__str__()


# Forward reference for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .optimization_result import OptimizationResult












