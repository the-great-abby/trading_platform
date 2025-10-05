"""
Advanced Risk Management Module for Strategies
Provides risk management functionality for trading strategies
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float = 0.15  # 15% of portfolio
    max_risk_per_trade: float = 0.05  # 5% risk per trade
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    max_drawdown: float = 0.20  # 20% max drawdown
    volatility_threshold: float = 0.30  # 30% volatility threshold
    correlation_limit: float = 0.70  # 70% correlation limit

class AdvancedRiskManager:
    """Advanced risk management for strategies"""
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        self.risk_params = risk_params or RiskParameters()
        self.position_history = []
        self.risk_metrics = {}
        
    def calculate_position_size(self, 
                              symbol: str, 
                              current_price: float, 
                              portfolio_value: float,
                              confidence: float = 0.5) -> int:
        """Calculate position size based on risk parameters"""
        
        # Base position size calculation
        max_position_value = portfolio_value * self.risk_params.max_position_size
        max_risk_value = portfolio_value * self.risk_params.max_risk_per_trade
        
        # Adjust based on confidence
        confidence_multiplier = min(confidence * 2, 1.0)  # Scale confidence to 0-1
        adjusted_position_value = max_position_value * confidence_multiplier
        
        # Calculate number of shares
        position_value = min(adjusted_position_value, max_risk_value)
        shares = int(position_value / current_price)
        
        # Ensure minimum viable position
        min_position_value = portfolio_value * 0.01  # 1% minimum
        min_shares = int(min_position_value / current_price)
        
        return max(shares, min_shares) if shares > 0 else min_shares
    
    def validate_trade(self, 
                      symbol: str, 
                      action: str, 
                      quantity: int, 
                      price: float,
                      portfolio_value: float) -> Dict[str, Any]:
        """Validate trade against risk limits"""
        
        trade_value = quantity * price
        position_size_pct = trade_value / portfolio_value
        
        validation_result = {
            'approved': True,
            'warnings': [],
            'risk_score': 0.0,
            'recommendations': []
        }
        
        # Check position size limit
        if position_size_pct > self.risk_params.max_position_size:
            validation_result['approved'] = False
            validation_result['warnings'].append(
                f"Position size {position_size_pct:.1%} exceeds limit {self.risk_params.max_position_size:.1%}"
            )
        
        # Check risk per trade
        if trade_value > portfolio_value * self.risk_params.max_risk_per_trade:
            validation_result['approved'] = False
            validation_result['warnings'].append(
                f"Trade value ${trade_value:,.2f} exceeds risk limit ${portfolio_value * self.risk_params.max_risk_per_trade:,.2f}"
            )
        
        # Calculate risk score
        size_risk = position_size_pct / self.risk_params.max_position_size
        value_risk = trade_value / (portfolio_value * self.risk_params.max_risk_per_trade)
        validation_result['risk_score'] = max(size_risk, value_risk)
        
        # Add recommendations
        if validation_result['risk_score'] > 0.8:
            validation_result['recommendations'].append("Consider reducing position size")
        elif validation_result['risk_score'] > 0.6:
            validation_result['recommendations'].append("Monitor position closely")
        
        return validation_result
    
    def calculate_stop_loss(self, entry_price: float, action: str) -> float:
        """Calculate stop loss price"""
        if action == 'BUY':
            return entry_price * (1 - self.risk_params.stop_loss_pct)
        else:  # SELL
            return entry_price * (1 + self.risk_params.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, action: str) -> float:
        """Calculate take profit price"""
        if action == 'BUY':
            return entry_price * (1 + self.risk_params.take_profit_pct)
        else:  # SELL
            return entry_price * (1 - self.risk_params.take_profit_pct)
    
    def update_position_history(self, symbol: str, action: str, quantity: int, price: float):
        """Update position history for risk tracking"""
        self.position_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price
        })
        
        # Keep only recent history (last 100 trades)
        if len(self.position_history) > 100:
            self.position_history = self.position_history[-100:]
    
    def get_portfolio_risk_metrics(self, portfolio_value: float) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        
        if not self.position_history:
            return {
                'total_risk': 0.0,
                'concentration_risk': 0.0,
                'turnover_rate': 0.0,
                'risk_score': 'LOW'
            }
        
        # Calculate basic metrics
        recent_trades = [t for t in self.position_history 
                        if (datetime.now() - t['timestamp']).days <= 30]
        
        total_trade_value = sum(t['quantity'] * t['price'] for t in recent_trades)
        turnover_rate = total_trade_value / portfolio_value if portfolio_value > 0 else 0
        
        # Simple concentration risk (based on number of unique symbols)
        unique_symbols = len(set(t['symbol'] for t in recent_trades))
        concentration_risk = 1.0 / max(unique_symbols, 1)
        
        # Overall risk score
        if turnover_rate > 0.5 or concentration_risk > 0.5:
            risk_score = 'HIGH'
        elif turnover_rate > 0.2 or concentration_risk > 0.3:
            risk_score = 'MEDIUM'
        else:
            risk_score = 'LOW'
        
        return {
            'total_risk': min(turnover_rate + concentration_risk, 1.0),
            'concentration_risk': concentration_risk,
            'turnover_rate': turnover_rate,
            'risk_score': risk_score,
            'unique_symbols': unique_symbols,
            'total_trades': len(recent_trades)
        }

