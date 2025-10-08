"""
Asset Entity Model
Financial asset with market data and metadata
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid


class AssetType(Enum):
    """Asset type enumeration"""
    STOCK = "STOCK"
    BOND = "BOND"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    COMMODITY = "COMMODITY"
    CURRENCY = "CURRENCY"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"
    REAL_ESTATE = "REAL_ESTATE"
    ALTERNATIVE = "ALTERNATIVE"


@dataclass
class Asset:
    """Financial asset with market data and metadata"""
    
    # Primary identifiers
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    name: str = ""
    asset_type: AssetType = AssetType.STOCK
    
    # Asset classification
    sector: str = ""
    industry: str = ""
    country: str = "US"
    currency: str = "USD"
    
    # Market data
    current_price: float = 0.0
    market_cap: float = 0.0
    volume: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    spread: float = 0.0
    
    # Risk metrics
    beta: float = 1.0
    volatility: float = 0.0
    correlation_matrix: Dict[str, float] = field(default_factory=dict)
    
    # Fundamental data
    pe_ratio: Optional[float] = None
    dividend_yield: float = 0.0
    eps: Optional[float] = None
    book_value: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    data_source: str = "unknown"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        self.validate_asset()
        self.calculate_spread()
    
    def validate_asset(self) -> None:
        """Validate asset data integrity"""
        if not self.symbol:
            raise ValueError("Asset symbol is required")
        
        if not self.name:
            raise ValueError("Asset name is required")
        
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")
        
        if self.market_cap < 0:
            raise ValueError("Market cap cannot be negative")
        
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        
        if self.beta < -10 or self.beta > 10:
            raise ValueError("Beta must be between -10 and 10")
        
        if self.volatility < 0:
            raise ValueError("Volatility cannot be negative")
        
        if self.dividend_yield < 0:
            raise ValueError("Dividend yield cannot be negative")
    
    def calculate_spread(self) -> None:
        """Calculate bid-ask spread"""
        if self.bid_price > 0 and self.ask_price > 0:
            self.spread = self.ask_price - self.bid_price
        else:
            self.spread = 0.0
    
    def update_price(self, new_price: float) -> None:
        """Update asset price and recalculate metrics"""
        if new_price < 0:
            raise ValueError("Price cannot be negative")
        
        self.current_price = new_price
        self.last_updated = datetime.now()
        self.calculate_spread()
    
    def update_market_data(self, 
                          price: float, 
                          bid: float = 0.0, 
                          ask: float = 0.0, 
                          volume: float = 0.0) -> None:
        """Update comprehensive market data"""
        self.current_price = price
        self.bid_price = bid
        self.ask_price = ask
        self.volume = volume
        self.last_updated = datetime.now()
        self.calculate_spread()
    
    def update_risk_metrics(self, 
                           beta: float, 
                           volatility: float, 
                           correlations: Dict[str, float] = None) -> None:
        """Update risk metrics"""
        self.beta = beta
        self.volatility = volatility
        if correlations:
            self.correlation_matrix.update(correlations)
        self.last_updated = datetime.now()
    
    def update_fundamental_data(self,
                               pe_ratio: Optional[float] = None,
                               dividend_yield: float = 0.0,
                               eps: Optional[float] = None,
                               book_value: Optional[float] = None,
                               debt_to_equity: Optional[float] = None,
                               return_on_equity: Optional[float] = None) -> None:
        """Update fundamental data"""
        if pe_ratio is not None:
            self.pe_ratio = pe_ratio
        if dividend_yield >= 0:
            self.dividend_yield = dividend_yield
        if eps is not None:
            self.eps = eps
        if book_value is not None:
            self.book_value = book_value
        if debt_to_equity is not None:
            self.debt_to_equity = debt_to_equity
        if return_on_equity is not None:
            self.return_on_equity = return_on_equity
        
        self.last_updated = datetime.now()
    
    def get_correlation(self, other_asset_id: str) -> float:
        """Get correlation with another asset"""
        return self.correlation_matrix.get(other_asset_id, 0.0)
    
    def set_correlation(self, other_asset_id: str, correlation: float) -> None:
        """Set correlation with another asset"""
        if correlation < -1.0 or correlation > 1.0:
            raise ValueError("Correlation must be between -1.0 and 1.0")
        
        self.correlation_matrix[other_asset_id] = correlation
        self.last_updated = datetime.now()
    
    def is_liquid(self, min_volume: float = 1000000) -> bool:
        """Check if asset meets liquidity requirements"""
        return self.volume >= min_volume and self.is_active
    
    def is_large_cap(self, min_market_cap: float = 10000000000) -> bool:
        """Check if asset is large cap"""
        return self.market_cap >= min_market_cap
    
    def get_risk_score(self) -> float:
        """Calculate overall risk score (0-1, higher = riskier)"""
        risk_score = 0.0
        
        # Volatility component (40% weight)
        risk_score += min(self.volatility, 1.0) * 0.4
        
        # Beta component (30% weight)
        beta_risk = abs(self.beta - 1.0) / 2.0  # Normalize beta deviation
        risk_score += min(beta_risk, 1.0) * 0.3
        
        # Liquidity component (20% weight)
        liquidity_risk = max(0, 1.0 - (self.volume / 10000000))  # Lower volume = higher risk
        risk_score += min(liquidity_risk, 1.0) * 0.2
        
        # Fundamental component (10% weight)
        fundamental_risk = 0.0
        if self.pe_ratio and (self.pe_ratio > 50 or self.pe_ratio < 0):
            fundamental_risk += 0.5
        if self.debt_to_equity and self.debt_to_equity > 2.0:
            fundamental_risk += 0.5
        risk_score += fundamental_risk * 0.1
        
        return min(risk_score, 1.0)
    
    def get_expected_return(self, risk_free_rate: float = 0.02) -> float:
        """Calculate expected return using CAPM"""
        market_risk_premium = 0.06  # Assume 6% market risk premium
        return risk_free_rate + (self.beta * market_risk_premium)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary representation"""
        return {
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "sector": self.sector,
            "industry": self.industry,
            "country": self.country,
            "currency": self.currency,
            "current_price": self.current_price,
            "market_cap": self.market_cap,
            "volume": self.volume,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "spread": self.spread,
            "beta": self.beta,
            "volatility": self.volatility,
            "correlation_matrix": self.correlation_matrix,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "eps": self.eps,
            "book_value": self.book_value,
            "debt_to_equity": self.debt_to_equity,
            "return_on_equity": self.return_on_equity,
            "last_updated": self.last_updated.isoformat(),
            "data_source": self.data_source,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """Create asset from dictionary representation"""
        asset = cls()
        asset.asset_id = data.get("asset_id", str(uuid.uuid4()))
        asset.symbol = data.get("symbol", "")
        asset.name = data.get("name", "")
        asset.asset_type = AssetType(data.get("asset_type", "STOCK"))
        asset.sector = data.get("sector", "")
        asset.industry = data.get("industry", "")
        asset.country = data.get("country", "US")
        asset.currency = data.get("currency", "USD")
        asset.current_price = data.get("current_price", 0.0)
        asset.market_cap = data.get("market_cap", 0.0)
        asset.volume = data.get("volume", 0.0)
        asset.bid_price = data.get("bid_price", 0.0)
        asset.ask_price = data.get("ask_price", 0.0)
        asset.spread = data.get("spread", 0.0)
        asset.beta = data.get("beta", 1.0)
        asset.volatility = data.get("volatility", 0.0)
        asset.correlation_matrix = data.get("correlation_matrix", {})
        asset.pe_ratio = data.get("pe_ratio")
        asset.dividend_yield = data.get("dividend_yield", 0.0)
        asset.eps = data.get("eps")
        asset.book_value = data.get("book_value")
        asset.debt_to_equity = data.get("debt_to_equity")
        asset.return_on_equity = data.get("return_on_equity")
        asset.data_source = data.get("data_source", "unknown")
        asset.is_active = data.get("is_active", True)
        
        # Parse datetime fields
        last_updated = data.get("last_updated")
        asset.last_updated = datetime.fromisoformat(last_updated) if last_updated else datetime.now()
        
        created_at = data.get("created_at")
        asset.created_at = datetime.fromisoformat(created_at) if created_at else datetime.now()
        
        return asset
    
    def __str__(self) -> str:
        return f"Asset({self.symbol}, {self.name}, ${self.current_price:.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()






















