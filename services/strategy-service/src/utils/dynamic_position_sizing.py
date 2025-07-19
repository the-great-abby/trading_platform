"""
Dynamic Position Sizing System
Advanced position sizing based on multiple factors
"""

import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger

from .economic_calendar import get_market_regime_for_date, is_high_impact_day


@dataclass
class PositionSizingFactors:
    """Factors that influence position sizing"""
    volatility: float = 0.0
    confidence: float = 0.5
    market_regime: str = "normal_volatility"
    volatility_multiplier: float = 1.0
    economic_impact: float = 1.0
    portfolio_heat: float = 0.0  # Current portfolio risk
    correlation_risk: float = 0.0
    sector_concentration: float = 0.0
    momentum_strength: float = 0.0
    trend_strength: float = 0.0
    risk_free_rate: float = 0.05  # 5% risk-free rate


class DynamicPositionSizer:
    """Advanced dynamic position sizing system"""
    
    def __init__(self, 
                 base_risk_per_trade: float = 0.02,  # 2% base risk
                 max_position_size: float = 0.15,     # 15% max position
                 min_position_size: float = 0.01,     # 1% min position
                 kelly_multiplier: float = 0.25,      # Conservative Kelly
                 volatility_adjustment: bool = True,
                 market_regime_adjustment: bool = True,
                 economic_calendar_adjustment: bool = True):
        
        self.base_risk_per_trade = base_risk_per_trade
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.kelly_multiplier = kelly_multiplier
        self.volatility_adjustment = volatility_adjustment
        self.market_regime_adjustment = market_regime_adjustment
        self.economic_calendar_adjustment = economic_calendar_adjustment
        
        # Risk management parameters
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        self.max_sector_concentration = 0.30  # 30% max sector concentration
        self.max_correlation = 0.7  # Max correlation between positions
        
    def calculate_position_size(self, 
                              capital: float,
                              price: float,
                              factors: PositionSizingFactors,
                              target_date: Optional[date] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate optimal position size based on multiple factors
        
        Args:
            capital: Available capital
            price: Current stock price
            factors: Position sizing factors
            target_date: Date for economic calendar lookup
            
        Returns:
            Tuple of (position_size, sizing_details)
        """
        
        # Get market regime if date provided
        if target_date and self.economic_calendar_adjustment:
            market_regime = get_market_regime_for_date(target_date)
            factors.market_regime = market_regime["regime"]
            factors.volatility_multiplier = market_regime["volatility_multiplier"]
            factors.economic_impact = 1.0 if not is_high_impact_day(target_date) else 0.8
        
        # Calculate base position size using Kelly Criterion
        kelly_size = self._calculate_kelly_position_size(factors)
        
        # Apply volatility adjustment
        if self.volatility_adjustment:
            volatility_adjustment = self._calculate_volatility_adjustment(factors.volatility)
            kelly_size *= volatility_adjustment
        
        # Apply market regime adjustment
        if self.market_regime_adjustment:
            regime_adjustment = self._calculate_regime_adjustment(factors.market_regime)
            kelly_size *= regime_adjustment
        
        # Apply economic calendar adjustment
        if self.economic_calendar_adjustment:
            calendar_adjustment = self._calculate_calendar_adjustment(factors)
            kelly_size *= calendar_adjustment
        
        # Apply portfolio risk constraints
        portfolio_adjustment = self._calculate_portfolio_adjustment(factors)
        kelly_size *= portfolio_adjustment
        
        # Apply confidence adjustment
        confidence_adjustment = self._calculate_confidence_adjustment(factors.confidence)
        kelly_size *= confidence_adjustment
        
        # Convert to dollar amount
        position_value = capital * kelly_size
        
        # Convert to shares
        shares = int(position_value / price) if price > 0 else 0
        
        # Ensure minimum position size
        min_value = capital * self.min_position_size
        if position_value < min_value:
            position_value = min_value
            shares = int(position_value / price) if price > 0 else 0
        
        # Ensure maximum position size
        max_value = capital * self.max_position_size
        if position_value > max_value:
            position_value = max_value
            shares = int(position_value / price) if price > 0 else 0
        
        # Prepare sizing details
        sizing_details = {
            "kelly_size": kelly_size,
            "volatility_adjustment": self._calculate_volatility_adjustment(factors.volatility) if self.volatility_adjustment else 1.0,
            "regime_adjustment": self._calculate_regime_adjustment(factors.market_regime) if self.market_regime_adjustment else 1.0,
            "calendar_adjustment": self._calculate_calendar_adjustment(factors) if self.economic_calendar_adjustment else 1.0,
            "portfolio_adjustment": portfolio_adjustment,
            "confidence_adjustment": confidence_adjustment,
            "final_position_value": position_value,
            "shares": shares,
            "position_percentage": (position_value / capital) * 100 if capital > 0 else 0,
            "factors": factors
        }
        
        return shares, sizing_details
    
    def _calculate_kelly_position_size(self, factors: PositionSizingFactors) -> float:
        """Calculate position size using Kelly Criterion"""
        
        # Estimate win rate and average win/loss from confidence
        win_rate = 0.5 + (factors.confidence - 0.5) * 0.3  # 35% to 65%
        avg_win = 0.15  # 15% average win
        avg_loss = 0.08  # 8% average loss
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds received, p = win probability, q = loss probability
        b = avg_win / avg_loss  # odds received
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b if b > 0 else 0
        
        # Apply conservative multiplier
        conservative_kelly = kelly_fraction * self.kelly_multiplier
        
        # Ensure within bounds
        conservative_kelly = max(0, min(conservative_kelly, self.max_position_size))
        
        return conservative_kelly
    
    def _calculate_volatility_adjustment(self, volatility: float) -> float:
        """Adjust position size based on volatility"""
        if volatility <= 0:
            return 1.0
        
        # Higher volatility = smaller position
        # Use inverse relationship: 1 / (1 + volatility)
        adjustment = 1.0 / (1.0 + volatility * 10)
        
        # Ensure reasonable bounds
        return max(0.3, min(1.0, adjustment))
    
    def _calculate_regime_adjustment(self, market_regime: str) -> float:
        """Adjust position size based on market regime"""
        regime_adjustments = {
            "low_volatility": 1.2,      # Larger positions in low volatility
            "normal_volatility": 1.0,    # Normal sizing
            "elevated_volatility": 0.8,  # Smaller positions in elevated volatility
            "high_volatility": 0.6       # Much smaller positions in high volatility
        }
        
        return regime_adjustments.get(market_regime, 1.0)
    
    def _calculate_calendar_adjustment(self, factors: PositionSizingFactors) -> float:
        """Adjust position size based on economic calendar events"""
        base_adjustment = 1.0
        
        # Reduce position size during high-impact economic events
        if factors.economic_impact < 1.0:
            base_adjustment *= factors.economic_impact
        
        # Additional adjustments for specific market conditions
        if factors.volatility_multiplier > 1.0:
            base_adjustment *= (1.0 / factors.volatility_multiplier)
        
        return max(0.5, min(1.0, base_adjustment))
    
    def _calculate_portfolio_adjustment(self, factors: PositionSizingFactors) -> float:
        """Adjust position size based on portfolio risk"""
        adjustment = 1.0
        
        # Reduce size if portfolio heat is high
        if factors.portfolio_heat > 0.15:  # 15% portfolio risk
            heat_adjustment = 1.0 - (factors.portfolio_heat - 0.15) * 2
            adjustment *= max(0.5, heat_adjustment)
        
        # Reduce size for high correlation risk
        if factors.correlation_risk > 0.5:
            correlation_adjustment = 1.0 - (factors.correlation_risk - 0.5) * 2
            adjustment *= max(0.3, correlation_adjustment)
        
        # Reduce size for high sector concentration
        if factors.sector_concentration > 0.2:  # 20% sector concentration
            sector_adjustment = 1.0 - (factors.sector_concentration - 0.2) * 2
            adjustment *= max(0.5, sector_adjustment)
        
        return max(0.3, min(1.0, adjustment))
    
    def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """Adjust position size based on signal confidence"""
        # Linear adjustment: 0.5x to 1.5x based on confidence
        adjustment = 0.5 + confidence
        
        return max(0.3, min(1.5, adjustment))
    
    def calculate_risk_metrics(self, 
                              positions: List[Dict[str, Any]], 
                              capital: float) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        
        if not positions:
            return {
                "total_risk": 0.0,
                "portfolio_heat": 0.0,
                "sector_concentration": {},
                "correlation_risk": 0.0,
                "max_drawdown_risk": 0.0
            }
        
        # Calculate total position value
        total_position_value = sum(pos.get("value", 0) for pos in positions)
        portfolio_heat = total_position_value / capital if capital > 0 else 0
        
        # Calculate sector concentration
        sector_values = {}
        for position in positions:
            sector = position.get("sector", "unknown")
            value = position.get("value", 0)
            sector_values[sector] = sector_values.get(sector, 0) + value
        
        sector_concentration = {
            sector: value / capital for sector, value in sector_values.items()
        }
        
        # Calculate correlation risk (simplified)
        correlation_risk = 0.0
        if len(positions) > 1:
            # Simple correlation estimate based on sector overlap
            tech_positions = sum(1 for pos in positions if pos.get("sector") == "technology")
            if tech_positions > 1:
                correlation_risk = (tech_positions - 1) / len(positions)
        
        # Calculate max drawdown risk
        max_drawdown_risk = sum(pos.get("max_loss", 0) for pos in positions) / capital if capital > 0 else 0
        
        return {
            "total_risk": portfolio_heat,
            "portfolio_heat": portfolio_heat,
            "sector_concentration": sector_concentration,
            "correlation_risk": correlation_risk,
            "max_drawdown_risk": max_drawdown_risk
        }
    
    def get_position_sizing_summary(self) -> Dict[str, Any]:
        """Get position sizing configuration summary"""
        return {
            "base_risk_per_trade": self.base_risk_per_trade,
            "max_position_size": self.max_position_size,
            "min_position_size": self.min_position_size,
            "kelly_multiplier": self.kelly_multiplier,
            "volatility_adjustment": self.volatility_adjustment,
            "market_regime_adjustment": self.market_regime_adjustment,
            "economic_calendar_adjustment": self.economic_calendar_adjustment,
            "max_portfolio_risk": self.max_portfolio_risk,
            "max_sector_concentration": self.max_sector_concentration,
            "max_correlation": self.max_correlation
        }


# Global position sizer instance
position_sizer = DynamicPositionSizer()


def get_position_sizer() -> DynamicPositionSizer:
    """Get the global position sizer instance"""
    return position_sizer


def calculate_position_size(capital: float, 
                          price: float, 
                          confidence: float = 0.5,
                          volatility: float = 0.0,
                          target_date: Optional[date] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate position size using the global position sizer
    
    Args:
        capital: Available capital
        price: Current stock price
        confidence: Signal confidence (0-1)
        volatility: Stock volatility
        target_date: Date for economic calendar lookup
        
    Returns:
        Tuple of (shares, sizing_details)
    """
    
    factors = PositionSizingFactors(
        volatility=volatility,
        confidence=confidence
    )
    
    return position_sizer.calculate_position_size(capital, price, factors, target_date) 