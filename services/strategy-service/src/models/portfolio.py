"""
Portfolio management and tracking
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..utils.config import Config


@dataclass
class Position:
    """Individual position in the portfolio"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    strategy: str
    pnl: float = 0.0
    pnl_percentage: float = 0.0


class Portfolio:
    """Portfolio management and tracking"""
    
    def __init__(self, config: Config):
        self.config = config
        self.initial_capital = config.initial_capital
        self.cash = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        
        # Performance tracking
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = self.initial_capital
    
    @property
    def total_value(self) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(
            pos.quantity * pos.current_price 
            for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    @property
    def total_pnl_percentage(self) -> float:
        """Calculate total P&L percentage"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_pnl / self.initial_capital) * 100
    
    async def update_position(self, trade: Dict):
        """Update portfolio with a new trade"""
        symbol = trade["symbol"]
        action = trade["action"]
        quantity = trade["quantity"]
        price = trade["price"]
        strategy = trade.get("strategy", "unknown")
        
        if action == "BUY":
            await self._buy_position(symbol, quantity, price, strategy)
        elif action == "SELL":
            await self._sell_position(symbol, quantity, price, strategy)
        
        # Record trade
        self.trade_history.append(trade)
    
    async def _buy_position(self, symbol: str, quantity: float, price: float, strategy: str):
        """Buy a new position or add to existing"""
        total_cost = quantity * price
        
        if total_cost > self.cash:
            raise ValueError(f"Insufficient cash for {symbol} purchase")
        
        if symbol in self.positions:
            # Add to existing position
            pos = self.positions[symbol]
            total_quantity = pos.quantity + quantity
            avg_price = ((pos.quantity * pos.entry_price) + total_cost) / total_quantity
            
            pos.quantity = total_quantity
            pos.entry_price = avg_price
        else:
            # Create new position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                current_price=price,
                entry_time=datetime.now(),
                strategy=strategy
            )
        
        self.cash -= total_cost
    
    async def _sell_position(self, symbol: str, quantity: float, price: float, strategy: str):
        """Sell part or all of a position"""
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol} to sell")
        
        pos = self.positions[symbol]
        
        if quantity > pos.quantity:
            raise ValueError(f"Cannot sell more {symbol} than owned")
        
        # Calculate P&L
        pnl = (price - pos.entry_price) * quantity
        pnl_percentage = ((price - pos.entry_price) / pos.entry_price) * 100
        
        # Update cash
        self.cash += quantity * price
        
        # Update position
        pos.quantity -= quantity
        pos.pnl += pnl
        pos.pnl_percentage = pnl_percentage
        
        # Remove position if fully sold
        if pos.quantity == 0:
            del self.positions[symbol]
        
        # Update portfolio P&L
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        # Update peak value and drawdown
        current_value = self.total_value
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        drawdown = (self.peak_value - current_value) / self.peak_value
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    async def update_valuations(self):
        """Update current prices and P&L for all positions"""
        # This would typically fetch current market prices
        # For now, we'll just update the total P&L calculation
        total_positions_pnl = 0.0
        
        for pos in self.positions.values():
            # In a real implementation, you'd fetch current price here
            # pos.current_price = await get_current_price(pos.symbol)
            
            pos.pnl = (pos.current_price - pos.entry_price) * pos.quantity
            pos.pnl_percentage = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100
            total_positions_pnl += pos.pnl
        
        self.total_pnl = total_positions_pnl
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        return {
            "total_value": self.total_value,
            "cash": self.cash,
            "total_pnl": self.total_pnl,
            "total_pnl_percentage": self.total_pnl_percentage,
            "daily_pnl": self.daily_pnl,
            "max_drawdown": self.max_drawdown,
            "num_positions": len(self.positions),
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_percentage": pos.pnl_percentage,
                    "strategy": pos.strategy
                }
                for pos in self.positions.values()
            ]
        }
    
    def reset_daily_pnl(self):
        """Reset daily P&L (call at start of new day)"""
        self.daily_pnl = 0.0 