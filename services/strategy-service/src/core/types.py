from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class TradeSignal:
    """Trade signal data structure"""
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class Trade:
    """Trade execution data structure"""
    symbol: str
    action: str  # "BUY", "SELL"
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    pnl: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MockOptionContract:
    """Mock option contract data structure for backtesting"""
    symbol: str
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: datetime
    price: float
    volume: int
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    bid: float
    ask: float
    open_interest: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'symbol': self.symbol,
            'option_type': self.option_type,
            'strike': self.strike,
            'expiration': self.expiration,
            'price': self.price,
            'volume': self.volume,
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'implied_volatility': self.implied_volatility,
            'bid': self.bid,
            'ask': self.ask,
            'open_interest': self.open_interest
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockOptionContract':
        """Create from dictionary format"""
        return cls(
            symbol=data['symbol'],
            option_type=data['option_type'],
            strike=data['strike'],
            expiration=data['expiration'],
            price=data['price'],
            volume=data['volume'],
            delta=data['delta'],
            gamma=data['gamma'],
            theta=data['theta'],
            vega=data['vega'],
            implied_volatility=data['implied_volatility'],
            bid=data['bid'],
            ask=data['ask'],
            open_interest=data['open_interest']
        ) 