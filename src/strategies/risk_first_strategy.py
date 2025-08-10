"""
Risk-First Strategy - Prioritizes risk management and capital preservation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for position sizing"""
    volatility: float
    var_95: float  # 95% Value at Risk
    max_drawdown: float
    correlation: float
    beta: float


class RiskFirstStrategy(BaseStrategy):
    """
    Risk-First Strategy that prioritizes capital preservation and risk management.
    
    Key Principles:
    1. Maximum 1% risk per trade
    2. Portfolio-level position limits (5% max per position)
    3. Dynamic position sizing based on volatility
    4. Correlation-based diversification
    5. Stop-loss at 2% per position
    6. Take-profit at 3:1 risk-reward ratio
    """
    
    def __init__(self, 
                 max_risk_per_trade: float = 0.01,  # 1% max risk per trade
                 max_position_size: float = 0.05,    # 5% max position size
                 stop_loss_pct: float = 0.02,        # 2% stop loss
                 take_profit_ratio: float = 3.0,     # 3:1 risk-reward
                 volatility_lookback: int = 20,      # 20-day volatility
                 correlation_threshold: float = 0.7,  # Max correlation
                 **kwargs):
        super().__init__("Risk_First_Strategy", kwargs)
        
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_ratio = take_profit_ratio
        self.volatility_lookback = volatility_lookback
        self.correlation_threshold = correlation_threshold
        
        # Risk management state
        self.current_positions = {}
        self.portfolio_value = 100000  # Initial capital
        self.daily_returns = []
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signal with strict risk management"""
        try:
            if len(data) < self.volatility_lookback:
                return None
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(data)
            
            # Check if we should avoid this symbol due to high risk
            if self._should_avoid_symbol(risk_metrics):
                return None
            
            # Calculate technical indicators
            signals = self._calculate_technical_signals(data)
            
            # Apply risk filters
            if not self._passes_risk_filters(symbol, signals, risk_metrics):
                return None
            
            # Generate signal with position sizing
            signal = self._generate_risk_managed_signal(symbol, signals, risk_metrics)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _calculate_risk_metrics(self, data: pd.DataFrame) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        try:
            # Calculate returns
            returns = data['Close'].pct_change().dropna()
            
            # Volatility (20-day rolling)
            volatility = returns.rolling(self.volatility_lookback).std().iloc[-1] * np.sqrt(252)
            
            # Value at Risk (95%)
            var_95 = np.percentile(returns, 5)
            
            # Maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Beta (if market data available)
            beta = 1.0  # Default, would calculate vs market if available
            
            # Correlation (placeholder - would calculate vs portfolio)
            correlation = 0.0  # Would calculate vs current portfolio
            
            return RiskMetrics(
                volatility=volatility,
                var_95=var_95,
                max_drawdown=max_drawdown,
                correlation=correlation,
                beta=beta
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0.2, -0.02, -0.1, 0.0, 1.0)
    
    def _should_avoid_symbol(self, risk_metrics: RiskMetrics) -> bool:
        """Check if symbol should be avoided due to excessive risk"""
        
        # Avoid if volatility is too high (>30% annualized)
        if risk_metrics.volatility > 0.30:
            return True
        
        # Avoid if VaR is too negative (<-5%)
        if risk_metrics.var_95 < -0.05:
            return True
        
        # Avoid if correlation with portfolio is too high
        if risk_metrics.correlation > self.correlation_threshold:
            return True
        
        # Avoid if beta is too high (>1.5)
        if risk_metrics.beta > 1.5:
            return True
        
        return False
    
    def _calculate_technical_signals(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators with conservative thresholds"""
        
        signals = {}
        
        try:
            # RSI with conservative thresholds
            rsi = self._calculate_rsi(data['Close'], period=14)
            signals['rsi'] = rsi
            
            # MACD with longer periods for stability
            macd, signal = self._calculate_macd(data['Close'], fast=12, slow=26, signal=9)
            signals['macd'] = macd - signal
            
            # Bollinger Bands with wider bands
            bb_upper, bb_lower = self._calculate_bollinger_bands(data['Close'], period=20, std=2.5)
            current_price = data['Close'].iloc[-1]
            signals['bb_position'] = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            
            # Moving averages
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1]
            signals['sma_trend'] = (sma_20 - sma_50) / sma_50
            
            # Volume analysis
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            signals['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
            
        except Exception as e:
            logger.error(f"Error calculating technical signals: {e}")
        
        return signals
    
    def _passes_risk_filters(self, symbol: str, signals: Dict[str, float], risk_metrics: RiskMetrics) -> bool:
        """Apply strict risk filters"""
        
        # Check if we're already at max positions
        if len(self.current_positions) >= 10:  # Max 10 positions
            return False
        
        # Check if current drawdown is too high
        if self.current_drawdown < -0.15:  # 15% max drawdown
            return False
        
        # Check if RSI is in extreme zones
        if 'rsi' in signals:
            if signals['rsi'] < 20 or signals['rsi'] > 80:
                return False  # Too extreme, avoid
        
        # Check if volatility is acceptable
        if risk_metrics.volatility > 0.25:  # 25% max volatility
            return False
        
        # Check if volume is sufficient
        if 'volume_ratio' in signals and signals['volume_ratio'] < 0.5:
            return False  # Insufficient volume
        
        return True
    
    def _generate_risk_managed_signal(self, symbol: str, signals: Dict[str, float], risk_metrics: RiskMetrics) -> Optional[TradeSignal]:
        """Generate signal with strict position sizing"""
        
        try:
            current_price = signals.get('current_price', 100.0)
            
            # Determine signal direction
            buy_signals = 0
            sell_signals = 0
            
            # RSI signals
            if 'rsi' in signals:
                if signals['rsi'] < 30:
                    buy_signals += 1
                elif signals['rsi'] > 70:
                    sell_signals += 1
            
            # MACD signals
            if 'macd' in signals:
                if signals['macd'] > 0:
                    buy_signals += 1
                else:
                    sell_signals += 1
            
            # Bollinger Bands signals
            if 'bb_position' in signals:
                if signals['bb_position'] < 0.2:
                    buy_signals += 1
                elif signals['bb_position'] > 0.8:
                    sell_signals += 1
            
            # Moving average trend
            if 'sma_trend' in signals:
                if signals['sma_trend'] > 0.02:  # 2% positive trend
                    buy_signals += 1
                elif signals['sma_trend'] < -0.02:  # 2% negative trend
                    sell_signals += 1
            
            # Determine final signal
            if buy_signals >= 2 and sell_signals == 0:
                action = 'BUY'
                confidence = min(0.7, buy_signals / 4.0)  # Cap confidence at 70%
            elif sell_signals >= 2 and buy_signals == 0:
                action = 'SELL'
                confidence = min(0.7, sell_signals / 4.0)
            else:
                return None  # No clear signal
            
            # Calculate position size based on risk
            position_size = self._calculate_position_size(current_price, risk_metrics, confidence)
            
            if position_size <= 0:
                return None
            
            # Prepare metadata
            metadata = {
                'strategy_name': self.name,
                'risk_metrics': {
                    'volatility': risk_metrics.volatility,
                    'var_95': risk_metrics.var_95,
                    'max_drawdown': risk_metrics.max_drawdown,
                    'correlation': risk_metrics.correlation,
                    'beta': risk_metrics.beta
                },
                'technical_signals': signals,
                'position_size_pct': position_size / self.portfolio_value,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.stop_loss_pct * self.take_profit_ratio
            }
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=position_size,
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating risk-managed signal: {e}")
            return None
    
    def _calculate_position_size(self, price: float, risk_metrics: RiskMetrics, confidence: float) -> float:
        """Calculate position size based on risk management rules"""
        
        try:
            # Base position size (1% of portfolio)
            base_size = self.portfolio_value * self.max_risk_per_trade
            
            # Adjust for volatility (lower size for higher volatility)
            volatility_factor = max(0.1, 1.0 - risk_metrics.volatility)
            
            # Adjust for confidence
            confidence_factor = confidence
            
            # Adjust for current drawdown (reduce size if in drawdown)
            drawdown_factor = max(0.5, 1.0 + self.current_drawdown)
            
            # Calculate final position size
            position_value = base_size * volatility_factor * confidence_factor * drawdown_factor
            
            # Convert to shares
            shares = position_value / price
            
            # Apply maximum position size limit
            max_shares = (self.portfolio_value * self.max_position_size) / price
            shares = min(shares, max_shares)
            
            return shares
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            return macd.iloc[-1], signal_line.iloc[-1]
        except:
            return 0.0, 0.0
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std_dev = prices.rolling(window=period).std()
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            return upper_band, lower_band
        except:
            return pd.Series([prices.iloc[-1] * 1.1]), pd.Series([prices.iloc[-1] * 0.9])
    
    def update_portfolio_value(self, new_value: float):
        """Update portfolio value for position sizing"""
        self.portfolio_value = new_value
    
    def update_drawdown(self, current_drawdown: float):
        """Update current drawdown for risk management"""
        self.current_drawdown = current_drawdown
        self.max_drawdown = min(self.max_drawdown, current_drawdown) 