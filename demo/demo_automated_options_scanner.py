#!/usr/bin/env python3
"""
Automated Options Scanner Demo
==============================
Demonstrates how to use automated methods to identify profitable options positions.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionsOpportunity:
    """Represents a profitable options opportunity"""
    
    def __init__(self, symbol: str, strategy: str, confidence: float, 
                 expected_return: float, max_risk: float, risk_reward_ratio: float,
                 iv_percentile: float, metadata: Dict[str, Any]):
        self.symbol = symbol
        self.strategy = strategy
        self.confidence = confidence
        self.expected_return = expected_return
        self.max_risk = max_risk
        self.risk_reward_ratio = risk_reward_ratio
        self.iv_percentile = iv_percentile
        self.metadata = metadata
        self.timestamp = datetime.now()

class AutomatedOptionsScanner:
    """Demo automated options scanner"""
    
    def __init__(self):
        # Use centralized symbol configuration
        try:
            from src.utils.trading_config import get_options_symbols
            self.symbols = get_options_symbols()
        except ImportError:
            # Fallback to default options symbols
            self.symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV', 'USO', 'UNG', 'XLE', 'XLF'
            ]
        
        self.min_confidence = 0.6
        self.min_risk_reward_ratio = 0.3
        self.min_iv_percentile = 0.2
        self.max_iv_percentile = 0.8
        
        # Opportunity tracking
        self.opportunities = []
        self.scanned_symbols = set()
        
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
        
        # Sort by confidence and risk/reward ratio
        opportunities.sort(key=lambda x: (x.confidence, x.risk_reward_ratio), reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} opportunities across {len(self.scanned_symbols)} symbols")
        
        return opportunities
    
    async def scan_symbol(self, symbol: str) -> List[OptionsOpportunity]:
        """Scan a single symbol for opportunities"""
        
        opportunities = []
        
        # Simulate market data
        market_data = self.generate_market_data(symbol)
        options_chain = self.generate_options_chain(symbol)
        
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
        
        return opportunities
    
    def scan_iv_percentile_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                       options_chain: Dict) -> List[OptionsOpportunity]:
        """Scan for IV percentile-based opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        iv_percentile = options_chain.get('iv_percentile', 0.5)
        
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
                                  options_chain: Dict) -> List[OptionsOpportunity]:
        """Scan for earnings-based opportunities"""
        
        opportunities = []
        
        # Check if earnings are coming up (simulated)
        earnings_date = self.get_earnings_date(symbol)
        if not earnings_date:
            return opportunities
        
        days_to_earnings = (earnings_date - datetime.now()).days
        
        # Look for opportunities 3-7 days before earnings
        if 3 <= days_to_earnings <= 7:
            current_price = market_data['Close'].iloc[-1]
            iv_expansion = options_chain.get('iv_expansion', 0.0)
            
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
                                           options_chain: Dict) -> List[OptionsOpportunity]:
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
        
        return opportunities
    
    def scan_greeks_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                options_chain: Dict) -> List[OptionsOpportunity]:
        """Scan for Greeks-based opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Check for high gamma opportunities
        gamma = options_chain.get('gamma', 0.0)
        if gamma > 0.1:
            gamma_opportunity = self.create_gamma_scalping_opportunity(symbol, current_price, options_chain)
            if gamma_opportunity:
                opportunities.append(gamma_opportunity)
        
        # Check for high theta opportunities
        theta = options_chain.get('theta', 0.0)
        if abs(theta) > 0.02:
            theta_opportunity = self.create_theta_decay_opportunity(symbol, current_price, options_chain)
            if theta_opportunity:
                opportunities.append(theta_opportunity)
        
        return opportunities
    
    def scan_technical_breakout_opportunities(self, symbol: str, market_data: pd.DataFrame, 
                                            options_chain: Dict) -> List[OptionsOpportunity]:
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
                                         options_chain: Dict) -> List[OptionsOpportunity]:
        """Scan for calendar spread opportunities"""
        
        opportunities = []
        current_price = market_data['Close'].iloc[-1]
        
        # Find calendar spread opportunities
        calendar_opportunity = self.create_calendar_spread_opportunity(symbol, current_price, options_chain)
        if calendar_opportunity:
            opportunities.append(calendar_opportunity)
        
        return opportunities
    
    # Opportunity creation methods
    def create_iron_condor_opportunity(self, symbol: str, current_price: float, 
                                     options_chain: Dict, iv_percentile: float) -> Optional[OptionsOpportunity]:
        """Create Iron Condor opportunity"""
        
        max_profit = 2.50  # Simulated
        max_risk = 7.50    # Simulated
        risk_reward_ratio = max_profit / max_risk if max_risk > 0 else 0
        
        if risk_reward_ratio < self.min_risk_reward_ratio:
            return None
        
        confidence = 0.6 + (iv_percentile - 0.7) * 0.4
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Iron Condor",
            confidence=confidence,
            expected_return=max_profit,
            max_risk=max_risk,
            risk_reward_ratio=risk_reward_ratio,
            iv_percentile=iv_percentile,
            metadata={
                'strategy_type': 'iron_condor',
                'max_profit': max_profit,
                'max_risk': max_risk,
                'strikes': {'short_call': current_price + 5, 'long_call': current_price + 10,
                           'short_put': current_price - 5, 'long_put': current_price - 10}
            }
        )
    
    def create_long_straddle_opportunity(self, symbol: str, current_price: float, 
                                       options_chain: Dict, iv_percentile: float) -> Optional[OptionsOpportunity]:
        """Create long straddle opportunity"""
        
        total_cost = 3.50  # Simulated
        confidence = 0.6 + (0.3 - iv_percentile) * 0.4
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Long Straddle",
            confidence=confidence,
            expected_return=float('inf'),
            max_risk=total_cost,
            risk_reward_ratio=float('inf'),
            iv_percentile=iv_percentile,
            metadata={
                'strategy_type': 'long_straddle',
                'total_cost': total_cost,
                'breakeven_up': current_price + total_cost,
                'breakeven_down': current_price - total_cost
            }
        )
    
    def create_earnings_straddle_opportunity(self, symbol: str, current_price: float, 
                                           options_chain: Dict, iv_expansion: float) -> Optional[OptionsOpportunity]:
        """Create earnings straddle opportunity"""
        
        total_cost = 4.50  # Higher cost due to earnings
        confidence = 0.7 + iv_expansion * 0.2
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Earnings Straddle",
            confidence=confidence,
            expected_return=float('inf'),
            max_risk=total_cost,
            risk_reward_ratio=float('inf'),
            iv_percentile=0.8,  # High IV during earnings
            metadata={
                'strategy_type': 'earnings_straddle',
                'iv_expansion': iv_expansion,
                'total_cost': total_cost,
                'earnings_play': True
            }
        )
    
    def create_gamma_scalping_opportunity(self, symbol: str, current_price: float, 
                                        options_chain: Dict) -> Optional[OptionsOpportunity]:
        """Create gamma scalping opportunity"""
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Gamma Scalping",
            confidence=0.65,
            expected_return=1.50,
            max_risk=2.00,
            risk_reward_ratio=0.75,
            iv_percentile=0.6,
            metadata={
                'strategy_type': 'gamma_scalping',
                'gamma': options_chain.get('gamma', 0.0),
                'requires_hedging': True
            }
        )
    
    def create_bullish_call_opportunity(self, symbol: str, current_price: float, 
                                      options_chain: Dict) -> Optional[OptionsOpportunity]:
        """Create bullish call opportunity"""
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Bullish Call Spread",
            confidence=0.7,
            expected_return=3.00,
            max_risk=2.00,
            risk_reward_ratio=1.5,
            iv_percentile=0.5,
            metadata={
                'strategy_type': 'bullish_call_spread',
                'breakout_type': 'bullish',
                'strikes': {'long_call': current_price, 'short_call': current_price + 5}
            }
        )
    
    def create_calendar_spread_opportunity(self, symbol: str, current_price: float, 
                                         options_chain: Dict) -> Optional[OptionsOpportunity]:
        """Create calendar spread opportunity"""
        
        return OptionsOpportunity(
            symbol=symbol,
            strategy="Calendar Spread",
            confidence=0.75,
            expected_return=1.50,
            max_risk=1.00,
            risk_reward_ratio=1.5,
            iv_percentile=0.4,
            metadata={
                'strategy_type': 'calendar_spread',
                'short_dte': 30,
                'long_dte': 60,
                'theta_advantage': True
            }
        )
    
    # Helper methods for other opportunity types
    def create_short_strangle_opportunity(self, symbol: str, current_price: float, 
                                        options_chain: Dict, iv_percentile: float) -> Optional[OptionsOpportunity]:
        return None  # Placeholder
    
    def create_long_strangle_opportunity(self, symbol: str, current_price: float, 
                                       options_chain: Dict, iv_percentile: float) -> Optional[OptionsOpportunity]:
        return None  # Placeholder
    
    def create_earnings_strangle_opportunity(self, symbol: str, current_price: float, 
                                           options_chain: Dict, iv_expansion: float) -> Optional[OptionsOpportunity]:
        return None  # Placeholder
    
    def create_theta_decay_opportunity(self, symbol: str, current_price: float, 
                                     options_chain: Dict) -> Optional[OptionsOpportunity]:
        return None  # Placeholder
    
    def create_bearish_put_opportunity(self, symbol: str, current_price: float, 
                                     options_chain: Dict) -> Optional[OptionsOpportunity]:
        return None  # Placeholder
    
    # Market data and analysis methods
    def generate_market_data(self, symbol: str) -> pd.DataFrame:
        """Generate simulated market data"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        # Generate price data
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Add technical indicators
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['ATR'] = data['Close'].rolling(14).std()
        
        return data
    
    def generate_options_chain(self, symbol: str) -> Dict:
        """Generate simulated options chain data"""
        np.random.seed(hash(symbol) % 2**32)
        
        return {
            'iv_percentile': np.random.uniform(0.1, 0.9),
            'iv_expansion': np.random.uniform(0.1, 0.5),
            'gamma': np.random.uniform(0.05, 0.15),
            'theta': np.random.uniform(-0.05, -0.01),
            'vega': np.random.uniform(0.05, 0.15),
            'volume': np.random.randint(50, 500),
            'open_interest': np.random.randint(100, 1000)
        }
    
    def detect_volatility_regime(self, market_data: pd.DataFrame) -> str:
        """Detect volatility regime"""
        if len(market_data) < 20:
            return "unknown"
        
        volatility = market_data['Close'].pct_change().rolling(20).std().iloc[-1]
        
        if volatility > 0.03:
            return "high_volatility"
        elif volatility < 0.015:
            return "low_volatility"
        else:
            return "moderate_volatility"
    
    def detect_breakout(self, market_data: pd.DataFrame) -> str:
        """Detect technical breakout"""
        if len(market_data) < 50:
            return "no_breakout"
        
        current_price = market_data['Close'].iloc[-1]
        sma_20 = market_data['SMA_20'].iloc[-1]
        sma_50 = market_data['SMA_50'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            return "bullish_breakout"
        elif current_price < sma_20 < sma_50:
            return "bearish_breakout"
        else:
            return "no_breakout"
    
    def get_earnings_date(self, symbol: str) -> Optional[datetime]:
        """Get earnings date (simulated)"""
        # Simulate earnings dates
        earnings_dates = {
            'AAPL': datetime.now() + timedelta(days=5),
            'MSFT': datetime.now() + timedelta(days=3),
            'GOOGL': datetime.now() + timedelta(days=7),
            'AMZN': datetime.now() + timedelta(days=10),
            'TSLA': datetime.now() + timedelta(days=2)
        }
        
        return earnings_dates.get(symbol)
    
    def get_opportunities_summary(self, opportunities: List[OptionsOpportunity]) -> Dict[str, Any]:
        """Get summary of opportunities"""
        if not opportunities:
            return {}
        
        strategies = {}
        for opp in opportunities:
            strategy = opp.strategy
            if strategy not in strategies:
                strategies[strategy] = 0
            strategies[strategy] += 1
        
        return {
            'total_opportunities': len(opportunities),
            'strategies': strategies,
            'avg_confidence': np.mean([opp.confidence for opp in opportunities]),
            'avg_risk_reward': np.mean([opp.risk_reward_ratio for opp in opportunities]),
            'high_confidence_count': len([opp for opp in opportunities if opp.confidence > 0.8])
        }

async def main():
    """Main demo function"""
    
    print("🚀 Automated Options Scanner Demo")
    print("=" * 50)
    
    # Initialize scanner with centralized configuration
    scanner = AutomatedOptionsScanner()
    
    print(f"📊 Scanning symbols from centralized configuration...")
    
    # Scan for opportunities (uses centralized symbols by default)
    opportunities = await scanner.scan_for_opportunities()
    
    if not opportunities:
        print("❌ No opportunities found")
        return
    
    # Get summary
    summary = scanner.get_opportunities_summary(opportunities)
    
    print(f"\n✅ Found {summary['total_opportunities']} opportunities")
    print(f"📈 Average confidence: {summary['avg_confidence']:.3f}")
    print(f"⚖️ Average risk/reward: {summary['avg_risk_reward']:.3f}")
    print(f"🎯 High confidence opportunities: {summary['high_confidence_count']}")
    
    print(f"\n📊 Opportunities by strategy:")
    for strategy, count in summary['strategies'].items():
        print(f"  {strategy}: {count}")
    
    print(f"\n🏆 Top 5 Opportunities:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"{i}. {opp.symbol} - {opp.strategy}")
        print(f"   Confidence: {opp.confidence:.3f}")
        print(f"   Risk/Reward: {opp.risk_reward_ratio:.3f}")
        print(f"   IV Percentile: {opp.iv_percentile:.1%}")
        print(f"   Expected Return: ${opp.expected_return:.2f}")
        print(f"   Max Risk: ${opp.max_risk:.2f}")
        print()
    
    print("🎯 Automated scanning complete!")
    print("\nKey Features Demonstrated:")
    print("✅ IV Percentile Analysis")
    print("✅ Earnings Event Scanning") 
    print("✅ Volatility Regime Detection")
    print("✅ Greeks-Based Opportunities")
    print("✅ Technical Breakout Detection")
    print("✅ Calendar Spread Opportunities")
    print("✅ Risk/Reward Optimization")
    print("✅ Confidence Scoring")
    print("✅ Centralized Symbol Configuration")

if __name__ == "__main__":
    asyncio.run(main()) 