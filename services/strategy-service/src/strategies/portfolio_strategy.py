"""
Portfolio Strategy - Combines multiple strategies with confirmation logic and risk management
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from .base import BaseStrategy
from ..core.types import TradeSignal


@dataclass
class StrategySignal:
    """Individual strategy signal with confidence"""
    strategy_name: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class RiskMetrics:
    """Risk management metrics"""
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    var_95: float  # Value at Risk (95%)
    position_size: float
    stop_loss: float
    take_profit: float


class PortfolioStrategy(BaseStrategy):
    """Multi-strategy portfolio with confirmation logic and risk management"""
    
    def __init__(self, 
                 primary_strategies: List[str] = None,
                 confirmation_strategies: List[str] = None,
                 min_confirmations: int = 2,
                 risk_per_trade: float = 0.02,  # 2% risk per trade
                 max_position_size: float = 0.1,  # 10% max position
                 stop_loss_pct: float = 0.05,  # 5% stop loss
                 take_profit_pct: float = 0.15,  # 15% take profit
                 volatility_threshold: float = 0.03,  # 3% volatility threshold
                 **kwargs):
        super().__init__(name="Portfolio_Strategy", **kwargs)
        
        # Strategy configuration
        self.primary_strategies = primary_strategies or ['BollingerBandsStrategy', 'RSIStrategy']
        self.confirmation_strategies = confirmation_strategies or ['MeanReversionStrategy']
        self.min_confirmations = min_confirmations
        
        # Risk management
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.volatility_threshold = volatility_threshold
        
        # Strategy instances
        self.strategies = {}
        self.signal_history = {}
        
    async def initialize_strategies(self, strategy_classes: Dict[str, Any]):
        """Initialize strategy instances"""
        for strategy_name in self.primary_strategies + self.confirmation_strategies:
            if strategy_name in strategy_classes:
                self.strategies[strategy_name] = strategy_classes[strategy_name]()
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate portfolio signal with confirmation logic"""
        if len(data) < 50:  # Need sufficient data
            return None
            
        # Get signals from all strategies
        strategy_signals = await self._get_all_strategy_signals(symbol, data)
        
        # Check risk conditions first
        risk_metrics = self._calculate_risk_metrics(data)
        if not self._check_risk_conditions(risk_metrics):
            return None
        
        # Generate portfolio signal
        portfolio_signal = await self._generate_portfolio_signal(symbol, strategy_signals, data, risk_metrics)
        
        return portfolio_signal
    
    async def _get_all_strategy_signals(self, symbol: str, data: pd.DataFrame) -> List[StrategySignal]:
        """Get signals from all strategies"""
        signals = []
        
        for strategy_name, strategy in self.strategies.items():
            try:
                signal = await strategy.generate_signal(symbol, data)
                if signal:
                    strategy_signal = StrategySignal(
                        strategy_name=strategy_name,
                        action=signal.action,
                        confidence=signal.confidence,
                        metadata=signal.metadata,
                        timestamp=signal.timestamp
                    )
                    signals.append(strategy_signal)
            except Exception as e:
                print(f"Error getting signal from {strategy_name}: {e}")
                continue
        
        return signals
    
    def _calculate_risk_metrics(self, data: pd.DataFrame) -> RiskMetrics:
        """Calculate risk management metrics"""
        # Volatility (20-day rolling standard deviation)
        returns = data['Close'].pct_change().dropna()
        volatility = returns.rolling(window=20).std().iloc[-1]
        
        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5)
        
        # Position sizing based on volatility
        position_size = min(
            self.risk_per_trade / volatility if volatility > 0 else self.max_position_size,
            self.max_position_size
        )
        
        current_price = data['Close'].iloc[-1]
        stop_loss = current_price * (1 - self.stop_loss_pct)
        take_profit = current_price * (1 + self.take_profit_pct)
        
        return RiskMetrics(
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            var_95=var_95,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _check_risk_conditions(self, risk_metrics: RiskMetrics) -> bool:
        """Check if risk conditions are acceptable"""
        # Skip if volatility is too high
        if risk_metrics.volatility > self.volatility_threshold:
            return False
        
        # Skip if maximum drawdown is too high
        if risk_metrics.max_drawdown > 0.2:  # 20% max drawdown
            return False
        
        # Skip if Sharpe ratio is too low
        if risk_metrics.sharpe_ratio < -0.5:
            return False
        
        return True
    
    async def _generate_portfolio_signal(self, 
                                       symbol: str, 
                                       strategy_signals: List[StrategySignal],
                                       data: pd.DataFrame,
                                       risk_metrics: RiskMetrics) -> Optional[TradeSignal]:
        """Generate final portfolio signal with confirmation logic"""
        
        if not strategy_signals:
            return None
        
        # Separate primary and confirmation signals
        primary_signals = [s for s in strategy_signals if s.strategy_name in self.primary_strategies]
        confirmation_signals = [s for s in strategy_signals if s.strategy_name in self.confirmation_strategies]
        
        # Calculate signal strength
        buy_signals = [s for s in strategy_signals if s.action == 'BUY']
        sell_signals = [s for s in strategy_signals if s.action == 'SELL']
        
        # Calculate weighted scores
        buy_score = sum(s.confidence for s in buy_signals)
        sell_score = sum(s.confidence for s in sell_signals)
        
        # Check confirmation requirements
        primary_buy_count = len([s for s in primary_signals if s.action == 'BUY'])
        primary_sell_count = len([s for s in primary_signals if s.action == 'SELL'])
        confirmation_buy_count = len([s for s in confirmation_signals if s.action == 'BUY'])
        confirmation_sell_count = len([s for s in confirmation_signals if s.action == 'SELL'])
        
        current_price = data['Close'].iloc[-1]
        action = None
        confidence = 0.0
        
        # BUY Signal Logic
        if (buy_score > sell_score and 
            primary_buy_count >= 1 and  # At least one primary strategy agrees
            confirmation_buy_count >= self.min_confirmations):  # Confirmation strategies agree
            
            action = "BUY"
            confidence = min(buy_score / len(strategy_signals), 0.95)
            
        # SELL Signal Logic
        elif (sell_score > buy_score and 
              primary_sell_count >= 1 and  # At least one primary strategy agrees
              confirmation_sell_count >= self.min_confirmations):  # Confirmation strategies agree
            
            action = "SELL"
            confidence = min(sell_score / len(strategy_signals), 0.95)
        
        if action:
            # Calculate position size based on risk management
            position_size = self._calculate_position_size(current_price, confidence, risk_metrics)
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=position_size,
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=confidence,
                metadata={
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'primary_buy_count': primary_buy_count,
                    'primary_sell_count': primary_sell_count,
                    'confirmation_buy_count': confirmation_buy_count,
                    'confirmation_sell_count': confirmation_sell_count,
                    'risk_metrics': {
                        'volatility': risk_metrics.volatility,
                        'max_drawdown': risk_metrics.max_drawdown,
                        'sharpe_ratio': risk_metrics.sharpe_ratio,
                        'var_95': risk_metrics.var_95,
                        'stop_loss': risk_metrics.stop_loss,
                        'take_profit': risk_metrics.take_profit
                    },
                    'strategy_signals': [
                        {
                            'strategy': s.strategy_name,
                            'action': s.action,
                            'confidence': s.confidence
                        } for s in strategy_signals
                    ]
                }
            )
        
        return None
    
    def _calculate_position_size(self, price: float, confidence: float, risk_metrics: RiskMetrics) -> float:
        """Calculate position size based on risk management and confidence"""
        # Base position size from risk management
        base_size = risk_metrics.position_size * 1000 / price  # $1000 base
        
        # Adjust for confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1x
        
        # Adjust for volatility (smaller positions in high volatility)
        volatility_multiplier = 1.0 - (risk_metrics.volatility * 10)  # Reduce size for high volatility
        volatility_multiplier = max(0.3, min(1.0, volatility_multiplier))
        
        final_size = base_size * confidence_multiplier * volatility_multiplier
        
        return final_size
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get strategy configuration summary"""
        return {
            'name': self.name,
            'primary_strategies': self.primary_strategies,
            'confirmation_strategies': self.confirmation_strategies,
            'min_confirmations': self.min_confirmations,
            'risk_per_trade': self.risk_per_trade,
            'max_position_size': self.max_position_size,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'volatility_threshold': self.volatility_threshold
        } 