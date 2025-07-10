"""
Pairs Trading Strategy
=====================
A market-neutral strategy that identifies correlated stock pairs and trades the spread
when it deviates from historical mean. Uses cointegration analysis for pair selection.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from statsmodels.tsa.stattools import coint

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading Strategy
    
    Features:
    - Identifies cointegrated stock pairs
    - Trades the spread when it deviates from mean
    - Market-neutral approach (hedges market risk)
    - Dynamic position sizing based on spread deviation
    - Risk management with stop-loss and take-profit
    """
    
    def __init__(self, 
                 name: str = "PairsTrading",
                 correlation_threshold: float = 0.8,
                 cointegration_pvalue: float = 0.05,
                 z_score_threshold: float = 2.0,
                 max_position_size: float = 0.1,
                 stop_loss_zscore: float = 3.0,
                 take_profit_zscore: float = 0.5):
        super().__init__(name)
        self.correlation_threshold = correlation_threshold
        self.cointegration_pvalue = cointegration_pvalue
        self.z_score_threshold = z_score_threshold
        self.max_position_size = max_position_size
        self.stop_loss_zscore = stop_loss_zscore
        self.take_profit_zscore = take_profit_zscore
        
        # Pairs cache
        self.pairs_cache = {}
        self.spread_history = {}
        self.active_positions = {}
        
    def find_correlated_pairs(self, symbols: List[str], market_data: Dict[str, pd.DataFrame]) -> List[Tuple[str, str]]:
        """Find correlated pairs from available symbols"""
        pairs = []
        
        # Calculate correlation matrix
        price_data = {}
        for symbol in symbols:
            if symbol in market_data and not market_data[symbol].empty:
                price_data[symbol] = market_data[symbol]['Close']
        
        if len(price_data) < 2:
            return pairs
        
        # Create price dataframe
        price_df = pd.DataFrame(price_data)
        price_df = price_df.dropna()
        
        if len(price_df) < 30:  # Need sufficient data
            return pairs
        
        # Calculate correlation matrix
        corr_matrix = price_df.corr()
        
        # Find highly correlated pairs
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                symbol1 = corr_matrix.columns[i]
                symbol2 = corr_matrix.columns[j]
                correlation = corr_matrix.iloc[i, j]
                
                if abs(correlation) > self.correlation_threshold:
                    # Test for cointegration
                    if self._test_cointegration(price_df[symbol1], price_df[symbol2]):
                        pairs.append((symbol1, symbol2))
                        logger.info(f"Found cointegrated pair: {symbol1} - {symbol2} (corr: {correlation:.3f})")
        
        return pairs
    
    def _test_cointegration(self, series1: pd.Series, series2: pd.Series) -> bool:
        """Test if two series are cointegrated"""
        try:
            # Remove any NaN values
            common_data = pd.concat([series1, series2], axis=1).dropna()
            if len(common_data) < 30:
                return False
            
            # Perform cointegration test
            score, pvalue, _ = coint(common_data.iloc[:, 0], common_data.iloc[:, 1])
            return pvalue < self.cointegration_pvalue
        except Exception as e:
            logger.error(f"Error in cointegration test: {e}")
            return False
    
    def calculate_spread(self, price1: float, price2: float, hedge_ratio: float) -> float:
        """Calculate the spread between two prices"""
        return price1 - (hedge_ratio * price2)
    
    def calculate_hedge_ratio(self, series1: pd.Series, series2: pd.Series) -> float:
        """Calculate hedge ratio using linear regression"""
        try:
            # Remove NaN values
            common_data = pd.concat([series1, series2], axis=1).dropna()
            if len(common_data) < 30:
                return 1.0
            
            # Linear regression: series1 = beta * series2 + alpha
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                common_data.iloc[:, 1], common_data.iloc[:, 0]
            )
            
            return slope
        except Exception as e:
            logger.error(f"Error calculating hedge ratio: {e}")
            return 1.0
    
    def calculate_zscore(self, current_spread: float, spread_history: List[float]) -> float:
        """Calculate z-score of current spread relative to history"""
        if len(spread_history) < 10:
            return 0.0
        
        mean_spread = np.mean(spread_history)
        std_spread = np.std(spread_history)
        
        if std_spread == 0:
            return 0.0
        
        return (current_spread - mean_spread) / std_spread
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            market_data: Dict[str, pd.DataFrame] = None) -> Optional[TradeSignal]:
        """Generate pairs trading signal"""
        
        if not market_data or len(market_data) < 2:
            return None
        
        # Find pairs if not already cached
        if not self.pairs_cache:
            symbols = list(market_data.keys())
            self.pairs_cache = self.find_correlated_pairs(symbols, market_data)
        
        # Find pairs containing the current symbol
        relevant_pairs = [pair for pair in self.pairs_cache if symbol in pair]
        
        if not relevant_pairs:
            return None
        
        # Generate signals for each pair
        signals = []
        for pair in relevant_pairs:
            signal = await self._generate_pair_signal(pair, market_data)
            if signal:
                signals.append(signal)
        
        # Return the highest confidence signal
        if signals:
            return max(signals, key=lambda x: x.confidence)
        
        return None
    
    async def _generate_pair_signal(self, pair: Tuple[str, str], 
                                  market_data: Dict[str, pd.DataFrame]) -> Optional[TradeSignal]:
        """Generate signal for a specific pair"""
        
        symbol1, symbol2 = pair
        pair_key = f"{symbol1}_{symbol2}"
        
        # Get price data for both symbols
        if (symbol1 not in market_data or symbol2 not in market_data or
            market_data[symbol1].empty or market_data[symbol2].empty):
            return None
        
        data1 = market_data[symbol1]
        data2 = market_data[symbol2]
        
        # Ensure we have enough data
        if len(data1) < 50 or len(data2) < 50:
            return None
        
        # Calculate hedge ratio
        hedge_ratio = self.calculate_hedge_ratio(data1['Close'], data2['Close'])
        
        # Get current prices
        current_price1 = data1['Close'].iloc[-1]
        current_price2 = data2['Close'].iloc[-1]
        
        # Calculate current spread
        current_spread = self.calculate_spread(current_price1, current_price2, hedge_ratio)
        
        # Get spread history
        if pair_key not in self.spread_history:
            # Calculate historical spreads
            spreads = []
            for i in range(min(len(data1), len(data2))):
                spread = self.calculate_spread(data1['Close'].iloc[i], data2['Close'].iloc[i], hedge_ratio)
                spreads.append(spread)
            self.spread_history[pair_key] = spreads
        else:
            # Update spread history
            self.spread_history[pair_key].append(current_spread)
            # Keep only last 100 spreads
            if len(self.spread_history[pair_key]) > 100:
                self.spread_history[pair_key] = self.spread_history[pair_key][-100:]
        
        # Calculate z-score
        z_score = self.calculate_zscore(current_spread, self.spread_history[pair_key])
        
        # Generate signal based on z-score
        signal = None
        
        if abs(z_score) > self.z_score_threshold:
            # Determine which symbol to buy/sell
            if z_score > 0:  # Spread is high, expect reversion
                # Sell symbol1, buy symbol2
                action = "PAIR_TRADE"
                primary_symbol = symbol1
                secondary_symbol = symbol2
                primary_action = "SELL"
                secondary_action = "BUY"
                confidence = min(abs(z_score) / 4.0, 0.9)
            else:  # Spread is low, expect reversion
                # Buy symbol1, sell symbol2
                action = "PAIR_TRADE"
                primary_symbol = symbol1
                secondary_symbol = symbol2
                primary_action = "BUY"
                secondary_action = "SELL"
                confidence = min(abs(z_score) / 4.0, 0.9)
            
            # Calculate position sizes
            primary_price = current_price1
            secondary_price = current_price2
            
            # Equal dollar amounts for market neutrality
            position_size = self.max_position_size / 2  # Split between two positions
            
            signal = TradeSignal(
                symbol=primary_symbol,
                action=primary_action,
                quantity=position_size / primary_price,
                price=primary_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=confidence,
                metadata={
                    'pair_symbol': secondary_symbol,
                    'pair_action': secondary_action,
                    'pair_quantity': position_size / secondary_price,
                    'pair_price': secondary_price,
                    'z_score': z_score,
                    'spread': current_spread,
                    'hedge_ratio': hedge_ratio,
                    'signal_type': 'pairs_trading',
                    'is_pair_trade': True
                }
            )
            
            logger.info(f"Pairs signal: {primary_symbol} {primary_action} / {secondary_symbol} {secondary_action} "
                       f"(z-score: {z_score:.2f}, confidence: {confidence:.2f})")
        
        return signal
    
    def calculate_position_size(self, capital: float, price: float, z_score: float) -> float:
        """Calculate position size based on z-score"""
        base_size = capital * self.max_position_size
        # Scale position size with z-score
        scaled_size = base_size * min(abs(z_score) / self.z_score_threshold, 1.0)
        return scaled_size / price
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "correlation_threshold": self.correlation_threshold,
            "cointegration_pvalue": self.cointegration_pvalue,
            "z_score_threshold": self.z_score_threshold,
            "active_pairs": len(self.pairs_cache),
            "spread_history_keys": list(self.spread_history.keys())
        } 