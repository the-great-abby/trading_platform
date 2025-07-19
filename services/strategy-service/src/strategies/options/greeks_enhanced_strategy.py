"""
Greeks-Enhanced Trading Strategy
Uses options Greeks data (delta, gamma, theta, vega) to enhance trading decisions
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.services.ai.ollama_service import OllamaService

logger = logging.getLogger(__name__)


@dataclass
class GreeksData:
    """Container for options Greeks data"""
    delta: float
    gamma: float
    theta: float
    vega: float
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'


class GreeksEnhancedStrategy(BaseStrategy):
    """
    Trading strategy that uses options Greeks data to enhance trading decisions.
    Combines traditional technical indicators with Greeks-based risk metrics.
    """
    
    def __init__(self, 
                 name: str = "GreeksEnhanced",
                 delta_threshold: float = 0.3,
                 gamma_threshold: float = 0.1,
                 theta_threshold: float = -0.05,
                 vega_threshold: float = 0.2,
                 greeks_weight: float = 0.4,
                 technical_weight: float = 0.6):
        """
        Initialize Greeks-enhanced strategy
        
        Args:
            name: Strategy name
            delta_threshold: Delta threshold for position sizing
            gamma_threshold: Gamma threshold for volatility adjustment
            theta_threshold: Theta threshold for time decay consideration
            vega_threshold: Vega threshold for implied volatility sensitivity
            greeks_weight: Weight given to Greeks-based signals (0-1)
            technical_weight: Weight given to technical indicators (0-1)
        """
        super().__init__(name=name)
        self.delta_threshold = delta_threshold
        self.gamma_threshold = gamma_threshold
        self.theta_threshold = theta_threshold
        self.vega_threshold = vega_threshold
        self.greeks_weight = greeks_weight
        self.technical_weight = technical_weight
        self.ollama_service = None
        
        # Greeks data cache
        self.greeks_cache: Dict[str, GreeksData] = {}
        
        logger.info(f"Initialized {name} strategy with Greeks thresholds: "
                   f"delta={delta_threshold}, gamma={gamma_threshold}, "
                   f"theta={theta_threshold}, vega={vega_threshold}")
    
    async def initialize(self, ollama_url: str = None):
        """Initialize the strategy with Ollama service"""
        import os
        if ollama_url is None:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        try:
            self.ollama_service = OllamaService(base_url=ollama_url)
            logger.info(f"Initialized Ollama service for {self.name} strategy")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {e}")
            self.ollama_service = None
    
    def calculate_greeks_score(self, greeks: GreeksData) -> float:
        """
        Calculate a composite score based on Greeks data
        
        Args:
            greeks: Greeks data object
            
        Returns:
            Score between -1 and 1 (negative = bearish, positive = bullish)
        """
        if not greeks:
            return 0.0
        
        # Normalize Greeks to -1 to 1 range
        delta_score = np.clip(greeks.delta, -1, 1)
        gamma_score = np.clip(greeks.gamma / self.gamma_threshold, -1, 1)
        theta_score = np.clip(greeks.theta / self.theta_threshold, -1, 1)
        vega_score = np.clip(greeks.vega / self.vega_threshold, -1, 1)
        
        # Weighted combination
        greeks_score = (
            delta_score * 0.4 +
            gamma_score * 0.2 +
            theta_score * 0.2 +
            vega_score * 0.2
        )
        
        return np.clip(greeks_score, -1, 1)
    
    def get_greeks_data(self, symbol: str, current_price: float, historical_date: Optional[str] = None) -> Optional[GreeksData]:
        """
        Get Greeks data for a symbol at a specific historical date
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            historical_date: Historical date (YYYY-MM-DD) for backtesting, or None for current date
            
        Returns:
            GreeksData object or None if not available
        """
        try:
            # Try to get real options data
            from src.services.market_data.options_data_service import get_options_service
            options_service = get_options_service()
            
            # If we have a historical date, we need to simulate what options were available then
            if historical_date:
                logger.info(f"[GreeksStrategy] Looking for options data for {symbol} on historical date {historical_date}")
                
                # For historical backtesting, we need to find options that were available on that date
                # This is a simplified approach - in a real system, you'd need historical options data
                
                # Calculate what expiration dates would have been available on the historical date
                # Typically, options expire on the third Friday of each month
                from datetime import datetime, timedelta
                import calendar
                
                hist_date = datetime.strptime(historical_date, "%Y-%m-%d")
                
                # Find the next few expiration dates that would have been available
                available_expirations = []
                for i in range(1, 4):  # Look for next 3 months
                    future_date = hist_date + timedelta(days=30*i)
                    # Find the third Friday of that month
                    c = calendar.monthcalendar(future_date.year, future_date.month)
                    third_friday = None
                    for week in c:
                        if week[calendar.FRIDAY] != 0:
                            if third_friday is None:
                                third_friday = week[calendar.FRIDAY]
                            elif third_friday is not None:
                                third_friday = week[calendar.FRIDAY]
                                break
                    
                    if third_friday:
                        exp_date = datetime(future_date.year, future_date.month, third_friday)
                        if exp_date > hist_date:
                            available_expirations.append(exp_date.strftime("%Y-%m-%d"))
                
                logger.info(f"[GreeksStrategy] Historical expirations for {symbol} on {historical_date}: {available_expirations}")
                
                # Try to get options for the nearest historical expiration
                liquid_contracts = None
                for exp_date in available_expirations:
                    try:
                        contracts = options_service.get_options_chain(symbol, expiration_date=exp_date)
                        if contracts and len(contracts) > 0:
                            # Filter for liquid contracts
                            liquid_contracts = [c for c in contracts if c.volume >= 1]
                            if liquid_contracts:
                                logger.info(f"[GreeksStrategy] Found {len(liquid_contracts)} liquid contracts for {symbol} expiring {exp_date}")
                                break
                    except Exception as e:
                        logger.warning(f"[GreeksStrategy] Error getting options for {symbol} expiring {exp_date}: {e}")
                        continue
                
                if not liquid_contracts:
                    logger.warning(f"[GreeksStrategy] No historical options data found for {symbol} on {historical_date}, using mock data")
                    # Generate mock Greeks based on historical context
                    mock_greeks = GreeksData(
                        delta=0.6,  # Slightly bullish
                        gamma=0.08,  # Moderate gamma
                        theta=-0.03,  # Time decay
                        vega=0.15,   # Volatility sensitivity
                        strike=current_price * 1.05,  # 5% OTM
                        expiration=available_expirations[0] if available_expirations else "2024-12-20",
                        option_type="call"
                    )
                    self.greeks_cache[f"{symbol}_{historical_date}"] = mock_greeks
                    return mock_greeks
            else:
                # Current date - use existing logic
                liquid_contracts = options_service.get_liquid_options(symbol, min_volume=1)
            
            if liquid_contracts and len(liquid_contracts) > 0:
                # Calculate weighted average Greeks from liquid contracts
                total_volume = sum(c.volume for c in liquid_contracts if c.volume > 0)
                
                if total_volume > 0:
                    avg_delta = 0.0
                    avg_gamma = 0.0
                    avg_theta = 0.0
                    avg_vega = 0.0
                    valid_contracts = 0
                    
                    for contract in liquid_contracts:
                        if contract.volume > 0:
                            weight = contract.volume / total_volume
                            
                            # Use Greeks if available, otherwise use reasonable defaults
                            delta = contract.delta if contract.delta is not None else 0.5
                            gamma = contract.gamma if contract.gamma is not None else 0.02
                            theta = contract.theta if contract.theta is not None else -0.05
                            vega = contract.vega if contract.vega is not None else 0.1
                            
                            avg_delta += delta * weight
                            avg_gamma += gamma * weight
                            avg_theta += theta * weight
                            avg_vega += vega * weight
                            valid_contracts += 1
                    
                    if valid_contracts > 0:
                        # Use the most liquid contract for strike and expiration
                        most_liquid = max(liquid_contracts, key=lambda x: x.volume)
                        
                        real_greeks = GreeksData(
                            delta=avg_delta,
                            gamma=avg_gamma,
                            theta=avg_theta,
                            vega=avg_vega,
                            strike=most_liquid.strike,
                            expiration=most_liquid.expiration,
                            option_type=most_liquid.option_type
                        )
                        
                        cache_key = f"{symbol}_{historical_date}" if historical_date else symbol
                        self.greeks_cache[cache_key] = real_greeks
                        logger.info(f"[GreeksStrategy] ✅ Using REAL Greeks data for {symbol} on {historical_date or 'current date'}: delta={avg_delta:.3f}, gamma={avg_gamma:.3f}, theta={avg_theta:.3f}, vega={avg_vega:.3f}")
                        return real_greeks
            
            # Fallback to mock data if no real options data available
            logger.warning(f"[GreeksStrategy] ⚠️ No real options data available for {symbol} on {historical_date or 'current date'}, using mock data")
            
            cache_key = f"{symbol}_{historical_date}" if historical_date else symbol
            if cache_key in self.greeks_cache:
                return self.greeks_cache[cache_key]
            
            # Generate mock Greeks based on price movement
            # In a real implementation, this would come from options data provider
            mock_greeks = GreeksData(
                delta=0.6,  # Slightly bullish
                gamma=0.08,  # Moderate gamma
                theta=-0.03,  # Time decay
                vega=0.15,   # Volatility sensitivity
                strike=current_price * 1.05,  # 5% OTM
                expiration="2024-12-20",
                option_type="call"
            )
            
            self.greeks_cache[cache_key] = mock_greeks
            return mock_greeks
            
        except Exception as e:
            logger.error(f"[GreeksStrategy] ❌ Error getting Greeks data for {symbol} on {historical_date or 'current date'}: {e}")
            
            # Fallback to mock data
            cache_key = f"{symbol}_{historical_date}" if historical_date else symbol
            if cache_key in self.greeks_cache:
                return self.greeks_cache[cache_key]
            
            mock_greeks = GreeksData(
                delta=0.6,
                gamma=0.08,
                theta=-0.03,
                vega=0.15,
                strike=current_price * 1.05,
                expiration="2024-12-20",
                option_type="call"
            )
            
            self.greeks_cache[cache_key] = mock_greeks
            return mock_greeks
    
    def calculate_technical_score(self, data: pd.DataFrame) -> float:
        """
        Calculate technical analysis score
        
        Args:
            data: OHLCV data
            
        Returns:
            Technical score between -1 and 1
        """
        if len(data) < 20:
            return 0.0
        
        # Simple moving averages
        sma_20 = data['Close'].rolling(window=20).mean()
        sma_50 = data['Close'].rolling(window=50).mean()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Current values
        current_price = data['Close'].iloc[-1]
        current_sma_20 = sma_20.iloc[-1] if not sma_20.empty else current_price
        current_sma_50 = sma_50.iloc[-1] if not sma_50.empty else current_price
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50.0
        
        # Handle NaN values
        if pd.isna(current_sma_20):
            current_sma_20 = current_price
        if pd.isna(current_sma_50):
            current_sma_50 = current_price
        if pd.isna(current_rsi):
            current_rsi = 50.0
        
        # Calculate scores
        sma_score = 1.0 if current_price > current_sma_20 > current_sma_50 else -1.0
        rsi_score = (current_rsi - 50) / 50  # Normalize to -1 to 1
        
        # Combined technical score
        technical_score = (sma_score * 0.6 + rsi_score * 0.4)
        return np.clip(technical_score, -1, 1)
    
    async def generate_signal(self, symbol: str, data, historical_date: Optional[str] = None) -> Dict:
        """
        Generate trading signal using Greeks and technical analysis
        Args:
            symbol: Stock symbol
            data: OHLCV data (DataFrame) or options data (list)
            historical_date: Historical date (YYYY-MM-DD) for backtesting, or None for current date
        Returns:
            Signal dictionary with action, confidence, and metadata
        """
        try:
            # Handle different data types
            if isinstance(data, list):
                current_price = 150.0  # Mock price for options symbols
                logger.info(f"[GreeksStrategy] Using mock price {current_price} for {symbol} options data (type: list)")
            elif isinstance(data, pd.DataFrame):
                if data.empty:
                    logger.warning(f"[GreeksStrategy] Empty DataFrame for {symbol}")
                    return {"action": "HOLD", "confidence": 0.1, "price": 0, "timestamp": datetime.now(), "metadata": {"error": "Empty data"}}
                current_price = data['Close'].iloc[-1]
            else:
                logger.error(f"[GreeksStrategy] Unsupported data type for {symbol}: {type(data)}")
                return {"action": "HOLD", "confidence": 0.1, "price": 0, "timestamp": datetime.now(), "metadata": {"error": f"Unsupported data type: {type(data)}"}}
            
            greeks = self.get_greeks_data(symbol, current_price, historical_date)
            greeks_score = self.calculate_greeks_score(greeks) if greeks else 0.0
            technical_score = self.calculate_technical_score(data) if isinstance(data, pd.DataFrame) else 0.0
            combined_score = (greeks_score * self.greeks_weight + technical_score * self.technical_weight)
            if combined_score > 0.3:
                action = "BUY"
                confidence = min(abs(combined_score), 0.9)
            elif combined_score < -0.3:
                action = "SELL"
                confidence = min(abs(combined_score), 0.9)
            else:
                action = "HOLD"
                confidence = 0.1
            metadata = {"greeks_score": greeks_score, "technical_score": technical_score, "combined_score": combined_score, "data_type": "options" if isinstance(data, list) else "ohlcv", "historical_date": historical_date, "greeks_data": {"delta": greeks.delta if greeks else None, "gamma": greeks.gamma if greeks else None, "theta": greeks.theta if greeks else None, "vega": greeks.vega if greeks else None} if greeks else None}
            if self.ollama_service:
                try:
                    logger.info(f"[GreeksStrategy] 🤖 Running LLM analysis for {symbol} {action} signal on {historical_date or 'current date'}...")
                    market_context = {'current_price': current_price, 'symbol': symbol, 'greeks_score': greeks_score, 'technical_score': technical_score, 'combined_score': combined_score, 'historical_date': historical_date}
                    analysis = await self.ollama_service.analyze_market_sentiment(news_events=[], technical_signals=[{'strategy': 'GreeksEnhanced', 'action': action, 'confidence': confidence, 'metadata': metadata}], market_data=market_context)
                    if analysis:
                        metadata["llm_analysis"] = {"sentiment_score": getattr(analysis, 'sentiment_score', None), "confidence": getattr(analysis, 'confidence', None), "reasoning": getattr(analysis, 'reasoning', None), "risk_assessment": getattr(analysis, 'risk_assessment', None), "market_impact": getattr(analysis, 'market_impact', None), "recommended_action": getattr(analysis, 'recommended_action', None)}
                        logger.info(f"[GreeksStrategy] ✅ LLM analysis completed for {symbol}: {getattr(analysis, 'recommended_action', None)}")
                    else:
                        logger.warning(f"[GreeksStrategy] ⚠️ LLM analysis returned no result for {symbol}")
                except Exception as e:
                    logger.error(f"[GreeksStrategy] ❌ LLM analysis failed for {symbol}: {e}")
            return {"action": action, "confidence": confidence, "price": current_price, "timestamp": datetime.now(), "metadata": metadata}
        except Exception as e:
            logger.error(f"[GreeksStrategy] ❌ Error generating signal for {symbol}: {e}")
            return {"action": "HOLD", "confidence": 0.1, "price": 0, "timestamp": datetime.now(), "metadata": {"error": str(e)}}
    
    def get_position_size(self, signal: Dict, available_capital: float) -> float:
        """
        Calculate position size based on Greeks and confidence
        
        Args:
            signal: Trading signal
            available_capital: Available capital
            
        Returns:
            Position size in dollars
        """
        base_size = available_capital * 0.1  # 10% base position
        
        # Adjust based on confidence
        confidence_multiplier = signal.get("confidence", 0.5)
        
        # Adjust based on Greeks volatility
        metadata = signal.get("metadata", {})
        greeks_data = metadata.get("greeks_data", {})
        
        if greeks_data and greeks_data.get("gamma"):
            # Higher gamma = more volatile = smaller position
            gamma_adjustment = 1.0 / (1.0 + abs(greeks_data["gamma"]))
        else:
            gamma_adjustment = 1.0
        
        position_size = base_size * confidence_multiplier * gamma_adjustment
        return min(position_size, available_capital * 0.2)  # Max 20%
    
    def get_stop_loss(self, signal: Dict) -> float:
        """
        Calculate stop loss based on Greeks
        
        Args:
            signal: Trading signal
            
        Returns:
            Stop loss price
        """
        current_price = signal.get("price", 0)
        metadata = signal.get("metadata", {})
        greeks_data = metadata.get("greeks_data", {})
        
        # Base stop loss
        if signal.get("action") == "BUY":
            base_stop = current_price * 0.95  # 5% stop loss
        else:
            base_stop = current_price * 1.05  # 5% stop loss
        
        # Adjust based on gamma (volatility)
        if greeks_data and greeks_data.get("gamma"):
            gamma_adjustment = 1.0 + abs(greeks_data["gamma"])
            if signal.get("action") == "BUY":
                base_stop *= gamma_adjustment
            else:
                base_stop /= gamma_adjustment
        
        return base_stop 

    async def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'ollama_service') and self.ollama_service:
                await self.ollama_service.cleanup()
            logger.info(f"[GreeksStrategy] ✅ Resources cleaned up for {self.name}")
        except Exception as e:
            logger.error(f"[GreeksStrategy] ❌ Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'ollama_service') and self.ollama_service and hasattr(self.ollama_service, 'session'):
            if self.ollama_service.session and not self.ollama_service.session.closed:
                logger.warning(f"[GreeksStrategy] ⚠️ Session not properly closed in destructor for {self.name}") 