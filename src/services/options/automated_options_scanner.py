"""
Automated Options Scanner
=========================
Comprehensive scanner that identifies profitable options opportunities using multiple methods:
- IV percentile analysis
- Volatility regime detection
- Earnings event scanning
- Technical indicator confirmation
- Greeks-based opportunities
- Risk/reward optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

from src.services.market_data.options_data_service import OptionsDataService, OptionContract
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class OpportunityType(Enum):
    """Types of options opportunities"""
    IV_MEAN_REVERSION = "iv_mean_reversion"
    IV_EXPANSION = "iv_expansion"
    EARNINGS_PLAY = "earnings_play"
    VOLATILITY_REGIME = "volatility_regime"
    GREEKS_OPPORTUNITY = "greeks_opportunity"
    TECHNICAL_BREAKOUT = "technical_breakout"
    RISK_REWARD_OPTIMAL = "risk_reward_optimal"
    CALENDAR_SPREAD = "calendar_spread"
    DIAGONAL_SPREAD = "diagonal_spread"

@dataclass
class OptionsOpportunity:
    """Represents a profitable options opportunity"""
    symbol: str
    opportunity_type: OpportunityType
    strategy: str
    confidence: float
    expected_return: float
    max_risk: float
    risk_reward_ratio: float
    iv_percentile: float
    days_to_expiration: int
    strikes: Dict[str, float]
    position_size: float
    entry_price: float
    target_price: float
    stop_loss: float
    metadata: Dict[str, Any]

class AutomatedOptionsScanner:
    """
    Automated scanner for profitable options opportunities
    """
    
    def __init__(self, symbols: Optional[List[str]] = None):
        self.options_service = OptionsDataService()
        
        # Use centralized symbol configuration
        if symbols is None:
            try:
                from src.utils.trading_config import get_options_symbols
                self.symbols = get_options_symbols()
            except ImportError:
                # Fallback to default options symbols
                self.symbols = [
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                    'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV', 'USO', 'UNG', 'XLE', 'XLF'
                ]
        else:
            self.symbols = symbols
        
        # Scanner thresholds
        self.min_confidence = 0.6
        self.min_risk_reward_ratio = 0.3
        self.min_iv_percentile = 0.2
        self.max_iv_percentile = 0.8
        self.min_volume = 10
        self.min_open_interest = 50
        
        # Opportunity tracking
        self.opportunities = []
        self.scanned_symbols = set()
        
        logger.info(f"🔍 Automated Options Scanner initialized with {len(self.symbols)} symbols from centralized configuration")
    
    async def scan_for_opportunities(self, symbols: Optional[List[str]] = None) -> List[OptionsOpportunity]:
        """Scan all symbols for profitable options opportunities"""
        
        # Use default symbols if none provided
        if symbols is None:
            symbols = self.symbols
        
        logger.info(f"🔍 Scanning {len(symbols)} symbols for options opportunities...")
        
        opportunities = []
        
        for symbol in symbols:
            try:
                symbol_opportunities = await self.scan_symbol(symbol)
                opportunities.extend(symbol_opportunities)
                self.scanned_symbols.add(symbol)
                
            except Exception as e:
                logger.error(f"❌ Error scanning {symbol}: {e}")
                continue
        
        # Sort opportunities by confidence and risk/reward ratio
        opportunities.sort(key=lambda x: (x.confidence, x.risk_reward_ratio), reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} opportunities across {len(self.scanned_symbols)} symbols")
        
        return opportunities
    
    async def scan_symbol(self, symbol: str) -> List[OptionsOpportunity]:
        """Scan a single symbol for opportunities"""
        
        opportunities = []
        
        # Get market data
        market_data = await self.get_market_data(symbol)
        if market_data is None:
            return opportunities
        
        # Get options chain
        options_chain = await self.get_options_chain(symbol)
        if not options_chain:
            return opportunities
        
        # 1. IV Percentile Analysis
        iv_opportunities = self.scan_iv_percentile_opportunities(symbol, market_data, options_chain)
        opportunities.extend(iv_opportunities)
        
        # 2. Earnings Event Scanning
        earnings_opportunities = self.scan_earnings_opportunities(symbol, market_data, options_chain)
        opportunities.extend(earnings_opportunities)
        
        # 3. Volatility Regime Detection
        volatility_opportunities = self.scan_volatility_regime_opportunities(symbol, market_data, options_chain)
        opportunities.extend(volatility_opportunities)
        
        # 4. Greeks-Based Opportunities
        greeks_opportunities = self.scan_greeks_opportunities(symbol, market_data, options_chain)
        opportunities.extend(greeks_opportunities)
        
        # 5. Technical Breakout Opportunities
        technical_opportunities = self.scan_technical_breakout_opportunities(symbol, market_data, options_chain)
        opportunities.extend(technical_opportunities)
        
        # 6. Calendar Spread Opportunities
        calendar_opportunities = self.scan_calendar_spread_opportunities(symbol, market_data, options_chain)
        opportunities.extend(calendar_opportunities)
        
        # 7. Diagonal Spread Opportunities
        diagonal_opportunities = self.scan_diagonal_spread_opportunities(symbol, market_data, options_chain)
        opportunities.extend(diagonal_opportunities)
        
        return opportunities
    
    def scan_iv_percentile_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                       options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for IV percentile-based opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Calculate IV percentile
        iv_percentile = self.calculate_iv_percentile(options_chain)
        
        # High IV opportunities (sell premium)
        if iv_percentile > 0.7:
            # Iron Condor opportunity
            iron_condor = self.create_iron_condor_opportunity(symbol, current_price, options_chain, iv_percentile)
            if iron_condor:
                opportunities.append(iron_condor)
            
            # Short Strangle opportunity
            short_strangle = self.create_short_strangle_opportunity(symbol, current_price, options_chain, iv_percentile)
            if short_strangle:
                opportunities.append(short_strangle)
        
        # Low IV opportunities (buy premium)
        elif iv_percentile < 0.3:
            # Long Straddle opportunity
            long_straddle = self.create_long_straddle_opportunity(symbol, current_price, options_chain, iv_percentile)
            if long_straddle:
                opportunities.append(long_straddle)
            
            # Long Strangle opportunity
            long_strangle = self.create_long_strangle_opportunity(symbol, current_price, options_chain, iv_percentile)
            if long_strangle:
                opportunities.append(long_strangle)
        
        return opportunities
    
    def scan_earnings_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                  options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for earnings-based opportunities"""
        
        opportunities = []
        
        # Check if earnings are coming up
        earnings_date = self.get_earnings_date(symbol)
        if not earnings_date:
            return opportunities
        
        days_to_earnings = (earnings_date - datetime.now()).days
        
        # Look for opportunities 3-7 days before earnings
        if 3 <= days_to_earnings <= 7:
            current_price = market_data['Close'].iloc[-1]
            
            # Calculate IV expansion
            iv_expansion = self.calculate_iv_expansion(symbol, options_chain)
            
            if iv_expansion > 0.3:  # 30% IV expansion
                # Straddle opportunity
                straddle = self.create_earnings_straddle_opportunity(symbol, current_price, options_chain, iv_expansion)
                if straddle:
                    opportunities.append(straddle)
                
                # Strangle opportunity
                strangle = self.create_earnings_strangle_opportunity(symbol, current_price, options_chain, iv_expansion)
                if strangle:
                    opportunities.append(strangle)
        
        return opportunities
    
    def scan_volatility_regime_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                           options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for volatility regime opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Calculate volatility regime
        volatility_regime = self.detect_volatility_regime(market_data)
        
        if volatility_regime == "high_volatility":
            # High volatility - look for premium selling opportunities
            iron_condor = self.create_iron_condor_opportunity(symbol, current_price, options_chain, 0.8)
            if iron_condor:
                opportunities.append(iron_condor)
        
        elif volatility_regime == "low_volatility":
            # Low volatility - look for premium buying opportunities
            straddle = self.create_long_straddle_opportunity(symbol, current_price, options_chain, 0.2)
            if straddle:
                opportunities.append(straddle)
        
        elif volatility_regime == "increasing_volatility":
            # Increasing volatility - look for long volatility plays
            strangle = self.create_long_strangle_opportunity(symbol, current_price, options_chain, 0.4)
            if strangle:
                opportunities.append(strangle)
        
        return opportunities
    
    def scan_greeks_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for Greeks-based opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Find options with attractive Greeks
        for option in options_chain:
            if option.volume < self.min_volume or option.open_interest < self.min_open_interest:
                continue
            
            # High gamma opportunities (for gamma scalping)
            if option.gamma and option.gamma > 0.1:
                gamma_opportunity = self.create_gamma_scalping_opportunity(symbol, option, current_price)
                if gamma_opportunity:
                    opportunities.append(gamma_opportunity)
            
            # High theta opportunities (for theta decay)
            if option.theta and abs(option.theta) > 0.02:
                theta_opportunity = self.create_theta_decay_opportunity(symbol, option, current_price)
                if theta_opportunity:
                    opportunities.append(theta_opportunity)
            
            # High vega opportunities (for volatility plays)
            if option.vega and option.vega > 0.1:
                vega_opportunity = self.create_vega_opportunity(symbol, option, current_price)
                if vega_opportunity:
                    opportunities.append(vega_opportunity)
        
        return opportunities
    
    def scan_technical_breakout_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                            options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for technical breakout opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Detect breakouts
        breakout_type = self.detect_breakout(market_data)
        
        if breakout_type == "bullish_breakout":
            # Look for call opportunities
            call_opportunity = self.create_bullish_call_opportunity(symbol, current_price, options_chain)
            if call_opportunity:
                opportunities.append(call_opportunity)
        
        elif breakout_type == "bearish_breakout":
            # Look for put opportunities
            put_opportunity = self.create_bearish_put_opportunity(symbol, current_price, options_chain)
            if put_opportunity:
                opportunities.append(put_opportunity)
        
        return opportunities
    
    def scan_calendar_spread_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                         options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for calendar spread opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Find calendar spread opportunities
        calendar_opportunity = self.create_calendar_spread_opportunity(symbol, current_price, options_chain)
        if calendar_opportunity:
            opportunities.append(calendar_opportunity)
        
        return opportunities
    
    def scan_diagonal_spread_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                         options_chain: List[OptionContract]) -> List[OptionsOpportunity]:
        """Scan for diagonal spread opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Detect trend direction
        trend_direction = self.detect_trend_direction(market_data)
        
        if trend_direction == "bullish":
            # Bullish diagonal spread
            diagonal_opportunity = self.create_bullish_diagonal_opportunity(symbol, current_price, options_chain)
            if diagonal_opportunity:
                opportunities.append(diagonal_opportunity)
        
        elif trend_direction == "bearish":
            # Bearish diagonal spread
            diagonal_opportunity = self.create_bearish_diagonal_opportunity(symbol, current_price, options_chain)
            if diagonal_opportunity:
                opportunities.append(diagonal_opportunity)
        
        return opportunities
    
    # Helper methods for creating specific opportunities
    def create_iron_condor_opportunity(self, symbol: str, current_price: float, 
                                     options_chain: List[OptionContract], iv_percentile: float) -> Optional[OptionsOpportunity]:
        """Create Iron Condor opportunity"""
        
        # Find suitable strikes
        calls = [opt for opt in options_chain if opt.option_type == 'call']
        puts = [opt for opt in options_chain if opt.option_type == 'put']
        
        # Find OTM strikes
        otm_calls = [c for c in calls if c.strike > current_price * 1.02]
        otm_puts = [p for p in puts if p.strike < current_price * 0.98]
        
        if len(otm_calls) < 2 or len(otm_puts) < 2:
            return None
        
        # Select strikes
        short_call = min(otm_calls, key=lambda x: x.strike)
        long_call = min([c for c in otm_calls if c.strike > short_call.strike], key=lambda x: x.strike)
        short_put = max(otm_puts, key=lambda x: x.strike)
        long_put = max([p for p in otm_puts if p.strike < short_put.strike], key=lambda x: x.strike)
        
        # Calculate metrics
        max_profit = (short_call.price + short_put.price) - (long_call.price + long_put.price)
        max_risk = (long_call.strike - short_call.strike) - max_profit
        risk_reward_ratio = max_profit / max_risk if max_risk > 0 else 0
        
        if risk_reward_ratio < self.min_risk_reward_ratio:
            return None
        
        confidence = 0.6 + (iv_percentile - 0.7) * 0.4  # Higher IV = higher confidence
        
        return OptionsOpportunity(
            symbol=symbol,
            opportunity_type=OpportunityType.IV_MEAN_REVERSION,
            strategy="Iron Condor",
            confidence=confidence,
            expected_return=max_profit,
            max_risk=max_risk,
            risk_reward_ratio=risk_reward_ratio,
            iv_percentile=iv_percentile,
            days_to_expiration=45,
            strikes={
                'short_call': short_call.strike,
                'long_call': long_call.strike,
                'short_put': short_put.strike,
                'long_put': long_put.strike
            },
            position_size=0.02,  # 2% of portfolio
            entry_price=current_price,
            target_price=current_price + max_profit,
            stop_loss=current_price - max_risk,
            metadata={
                'strategy_type': 'iron_condor',
                'iv_percentile': iv_percentile,
                'max_profit': max_profit,
                'max_risk': max_risk
            }
        )
    
    def create_long_straddle_opportunity(self, symbol: str, current_price: float, 
                                       options_chain: List[OptionContract], iv_percentile: float) -> Optional[OptionsOpportunity]:
        """Create long straddle opportunity"""
        
        # Find ATM options
        atm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and 
                    abs(opt.strike - current_price) / current_price < 0.02]
        atm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and 
                   abs(opt.strike - current_price) / current_price < 0.02]
        
        if not atm_calls or not atm_puts:
            return None
        
        # Select closest to ATM
        call = min(atm_calls, key=lambda x: abs(x.strike - current_price))
        put = min(atm_puts, key=lambda x: abs(x.strike - current_price))
        
        # Calculate metrics
        total_cost = call.price + put.price
        breakeven_up = call.strike + total_cost
        breakeven_down = put.strike - total_cost
        
        confidence = 0.6 + (0.3 - iv_percentile) * 0.4  # Lower IV = higher confidence
        
        return OptionsOpportunity(
            symbol=symbol,
            opportunity_type=OpportunityType.IV_MEAN_REVERSION,
            strategy="Long Straddle",
            confidence=confidence,
            expected_return=float('inf'),  # Unlimited upside
            max_risk=total_cost,
            risk_reward_ratio=float('inf'),
            iv_percentile=iv_percentile,
            days_to_expiration=30,
            strikes={
                'call_strike': call.strike,
                'put_strike': put.strike
            },
            position_size=0.02,
            entry_price=current_price,
            target_price=breakeven_up,
            stop_loss=current_price - total_cost,
            metadata={
                'strategy_type': 'long_straddle',
                'total_cost': total_cost,
                'breakeven_up': breakeven_up,
                'breakeven_down': breakeven_down
            }
        )
    
    # Additional helper methods would be implemented for other opportunity types...
    
    def calculate_iv_percentile(self, options_chain: List[OptionContract]) -> float:
        """Calculate implied volatility percentile"""
        if not options_chain:
            return 0.5
        
        # Calculate average IV
        ivs = [opt.implied_volatility for opt in options_chain if opt.implied_volatility and opt.implied_volatility > 0]
        if not ivs:
            return 0.5
        
        current_iv = np.mean(ivs)
        
        # Simplified percentile calculation
        if current_iv > 0.4:
            return 0.8
        elif current_iv > 0.3:
            return 0.6
        elif current_iv > 0.2:
            return 0.4
        else:
            return 0.2
    
    def calculate_iv_expansion(self, symbol: str, options_chain: List[OptionContract]) -> float:
        """Calculate IV expansion"""
        if not options_chain:
            return 0.0
        
        current_iv = np.mean([opt.implied_volatility for opt in options_chain if opt.implied_volatility and opt.implied_volatility > 0])
        historical_iv = 0.25  # Simplified historical IV
        
        return (current_iv - historical_iv) / historical_iv
    
    def detect_volatility_regime(self, market_data: pd.DataFrame) -> str:
        """Detect current volatility regime"""
        if len(market_data) < 20:
            return "unknown"
        
        # Calculate volatility
        returns = market_data['Close'].pct_change().dropna()
        volatility = returns.rolling(20).std().iloc[-1]
        
        if volatility > 0.03:
            return "high_volatility"
        elif volatility < 0.015:
            return "low_volatility"
        else:
            return "moderate_volatility"
    
    def detect_breakout(self, market_data: pd.DataFrame) -> str:
        """Detect technical breakout"""
        if len(market_data) < 20:
            return "no_breakout"
        
        current_price = market_data['Close'].iloc[-1]
        sma_20 = market_data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = market_data['Close'].rolling(50).mean().iloc[-1]
        
        # Bullish breakout
        if current_price > sma_20 > sma_50:
            return "bullish_breakout"
        # Bearish breakout
        elif current_price < sma_20 < sma_50:
            return "bearish_breakout"
        else:
            return "no_breakout"
    
    def detect_trend_direction(self, market_data: pd.DataFrame) -> str:
        """Detect trend direction"""
        if len(market_data) < 50:
            return "neutral"
        
        sma_20 = market_data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = market_data['Close'].rolling(50).mean().iloc[-1]
        current_price = market_data['Close'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            return "bullish"
        elif current_price < sma_20 < sma_50:
            return "bearish"
        else:
            return "neutral"
    
    async def get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for symbol"""
        # This would integrate with your market data service
        # For now, return None to indicate no data
        return None
    
    async def get_options_chain(self, symbol: str) -> List[OptionContract]:
        """Get options chain for symbol"""
        # This would integrate with your options data service
        return []
    
    def get_earnings_date(self, symbol: str) -> Optional[datetime]:
        """Get earnings date for symbol"""
        # This would integrate with earnings calendar
        return None
    
    def get_opportunities_summary(self) -> Dict[str, Any]:
        """Get summary of all opportunities"""
        return {
            'total_opportunities': len(self.opportunities),
            'scanned_symbols': len(self.scanned_symbols),
            'opportunities_by_type': self._group_opportunities_by_type(),
            'best_opportunities': self._get_best_opportunities(5)
        }
    
    def _group_opportunities_by_type(self) -> Dict[str, int]:
        """Group opportunities by type"""
        grouped = {}
        for opp in self.opportunities:
            opp_type = opp.opportunity_type.value
            grouped[opp_type] = grouped.get(opp_type, 0) + 1
        return grouped
    
    def _get_best_opportunities(self, count: int) -> List[OptionsOpportunity]:
        """Get best opportunities by confidence and risk/reward"""
        return sorted(self.opportunities, 
                     key=lambda x: (x.confidence, x.risk_reward_ratio), 
                     reverse=True)[:count] 