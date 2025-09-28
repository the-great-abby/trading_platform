#!/usr/bin/env python3
"""
Elliott Wave Options Integration

This module integrates Elliott Wave analysis with options trading strategies,
generating trading signals and comprehensive trading plans based on wave patterns.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from models import (
    ElliottWavePattern, TradingSignal, SignalType, RiskLevel,
    WaveType, WaveDirection
)

logger = logging.getLogger(__name__)


class ElliottWaveOptionsIntegrator:
    """Integrates Elliott Wave analysis with options trading strategies"""
    
    def __init__(self):
        self.risk_levels = {
            "high": {
                "max_position_size": 0.1,
                "min_confidence": 0.8,
                "profit_target_pct": 0.5,
                "stop_loss_pct": 2.0
            },
            "medium": {
                "max_position_size": 0.05,
                "min_confidence": 0.6,
                "profit_target_pct": 0.3,
                "stop_loss_pct": 1.5
            },
            "low": {
                "max_position_size": 0.02,
                "min_confidence": 0.4,
                "profit_target_pct": 0.2,
                "stop_loss_pct": 1.0
            }
        }
        
        self.strategy_mappings = {
            "impulse_completion": {
                "primary": ["StraddleStrategy", "LongStrangleStrategy"],
                "secondary": ["IronCondorStrategy"],
                "description": "High volatility expected at wave completion"
            },
            "corrective_completion": {
                "primary": ["IronCondorStrategy", "ButterflySpreadStrategy"],
                "secondary": ["CalendarSpreadStrategy"],
                "description": "Range-bound trading expected after correction"
            },
            "fibonacci_retracement": {
                "primary": ["CalendarSpreadStrategy", "DiagonalSpreadStrategy"],
                "secondary": ["CoveredCallStrategy"],
                "description": "Support/resistance levels for directional plays"
            },
            "wave_extension": {
                "primary": ["VolatilityStrategy", "StraddleStrategy"],
                "secondary": ["LongStrangleStrategy"],
                "description": "Extended waves indicate strong momentum"
            },
            "pattern_invalidation": {
                "primary": ["ButterflySpreadStrategy", "IronCondorStrategy"],
                "secondary": ["CalendarSpreadStrategy"],
                "description": "Pattern failure suggests reversal or consolidation"
            }
        }
    
    def analyze_for_options(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> List[TradingSignal]:
        """Analyze Elliott Wave pattern for options trading opportunities"""
        signals = []
        
        # Generate wave completion signals
        completion_signals = self._generate_wave_completion_signals(symbol, pattern, current_price)
        signals.extend(completion_signals)
        
        # Generate Fibonacci retracement signals
        fib_signals = self._generate_fibonacci_signals(symbol, pattern, current_price)
        signals.extend(fib_signals)
        
        # Generate volatility expansion signals
        volatility_signals = self._generate_volatility_signals(symbol, pattern, current_price)
        signals.extend(volatility_signals)
        
        # Generate pattern invalidation signals
        invalidation_signals = self._generate_invalidation_signals(symbol, pattern, current_price)
        signals.extend(invalidation_signals)
        
        # Filter and rank signals
        filtered_signals = self._filter_signals(signals)
        
        logger.info(f"Generated {len(filtered_signals)} options signals for {symbol}")
        return filtered_signals
    
    def _generate_wave_completion_signals(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> List[TradingSignal]:
        """Generate signals for wave completion"""
        signals = []
        
        if pattern.pattern_type == WaveType.IMPULSE and len(pattern.waves) == 5:
            # 5-wave impulse completed
            confidence = pattern.confidence * 0.9  # Slightly reduce confidence for signal generation
            
            if confidence >= 0.6:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.WAVE_COMPLETION_ENTRY,
                    wave_pattern=f"5-wave impulse completed",
                    confidence=confidence,
                    recommended_strategy="StraddleStrategy",
                    strike_selection=self._calculate_straddle_strikes(current_price),
                    expiration_preference="30-45 DTE",
                    risk_level=self._determine_risk_level(confidence),
                    profit_target=pattern.target_price,
                    stop_loss=pattern.invalidation_level,
                    description=f"5-wave impulse pattern completed at {current_price:.2f}. Expecting volatility expansion."
                )
                signals.append(signal)
        
        elif pattern.pattern_type == WaveType.CORRECTIVE and len(pattern.waves) == 3:
            # 3-wave corrective completed
            confidence = pattern.confidence * 0.8
            
            if confidence >= 0.6:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.WAVE_COMPLETION_ENTRY,
                    wave_pattern=f"3-wave corrective completed",
                    confidence=confidence,
                    recommended_strategy="IronCondorStrategy",
                    strike_selection=self._calculate_iron_condor_strikes(current_price),
                    expiration_preference="45-60 DTE",
                    risk_level=self._determine_risk_level(confidence),
                    profit_target=pattern.target_price,
                    stop_loss=pattern.invalidation_level,
                    description=f"3-wave corrective pattern completed at {current_price:.2f}. Expecting range-bound trading."
                )
                signals.append(signal)
        
        return signals
    
    def _generate_fibonacci_signals(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> List[TradingSignal]:
        """Generate signals based on Fibonacci levels"""
        signals = []
        
        if not pattern.fibonacci_levels:
            return signals
        
        # Check if current price is near key Fibonacci levels
        key_levels = ["fib_0.618_retracement", "fib_0.5_retracement", "fib_0.382_retracement"]
        
        for level_name in key_levels:
            if level_name in pattern.fibonacci_levels:
                fib_price = pattern.fibonacci_levels[level_name]
                price_distance = abs(current_price - fib_price) / current_price
                
                if price_distance < 0.02:  # Within 2% of Fibonacci level
                    confidence = pattern.confidence * 0.7
                    
                    if confidence >= 0.6:
                        signal = TradingSignal(
                            symbol=symbol,
                            signal_type=SignalType.FIBONACCI_RETRACEMENT,
                            wave_pattern=f"Fibonacci {level_name}",
                            confidence=confidence,
                            recommended_strategy="CalendarSpreadStrategy",
                            strike_selection=self._calculate_calendar_strikes(current_price),
                            expiration_preference="30-45 DTE",
                            risk_level=self._determine_risk_level(confidence),
                            profit_target=fib_price * 1.05 if current_price < fib_price else fib_price * 0.95,
                            stop_loss=fib_price * 0.98 if current_price < fib_price else fib_price * 1.02,
                            description=f"Price approaching {level_name} at {fib_price:.2f}. Support/resistance level."
                        )
                        signals.append(signal)
        
        return signals
    
    def _generate_volatility_signals(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> List[TradingSignal]:
        """Generate signals based on volatility expansion"""
        signals = []
        
        if pattern.enhanced_analysis and pattern.enhanced_analysis.wave_extensions:
            extensions = pattern.enhanced_analysis.wave_extensions.get("extensions", [])
            
            if extensions:
                primary_extension = pattern.enhanced_analysis.wave_extensions.get("primary_extension")
                
                if primary_extension and primary_extension["confidence"] > 0.7:
                    confidence = pattern.confidence * 0.8
                    
                    if confidence >= 0.6:
                        signal = TradingSignal(
                            symbol=symbol,
                            signal_type=SignalType.VOLATILITY_EXPANSION,
                            wave_pattern=f"Wave {primary_extension['wave']} extension detected",
                            confidence=confidence,
                            recommended_strategy="VolatilityStrategy",
                            strike_selection=self._calculate_volatility_strikes(current_price),
                            expiration_preference="30-45 DTE",
                            risk_level=self._determine_risk_level(confidence),
                            profit_target=current_price * 1.1,
                            stop_loss=current_price * 0.95,
                            description=f"Wave {primary_extension['wave']} extension indicates strong momentum and volatility expansion."
                        )
                        signals.append(signal)
        
        return signals
    
    def _generate_invalidation_signals(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> List[TradingSignal]:
        """Generate signals for pattern invalidation"""
        signals = []
        
        if pattern.invalidation_level:
            invalidation_distance = abs(current_price - pattern.invalidation_level) / current_price
            
            if invalidation_distance < 0.03:  # Within 3% of invalidation level
                confidence = pattern.confidence * 0.6
                
                if confidence >= 0.6:
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type=SignalType.PATTERN_INVALIDATION,
                        wave_pattern=f"Pattern approaching invalidation",
                        confidence=confidence,
                        recommended_strategy="ButterflySpreadStrategy",
                        strike_selection=self._calculate_butterfly_strikes(current_price),
                        expiration_preference="45-60 DTE",
                        risk_level=self._determine_risk_level(confidence),
                        profit_target=pattern.invalidation_level,
                        stop_loss=current_price * 1.05,
                        description=f"Pattern approaching invalidation level at {pattern.invalidation_level:.2f}. Prepare for reversal."
                    )
                    signals.append(signal)
        
        return signals
    
    def _calculate_straddle_strikes(self, current_price: float) -> Dict[str, float]:
        """Calculate strike prices for straddle strategy"""
        atm_strike = round(current_price)
        return {
            "call_strike": atm_strike,
            "put_strike": atm_strike,
            "atm_strike": atm_strike
        }
    
    def _calculate_iron_condor_strikes(self, current_price: float) -> Dict[str, float]:
        """Calculate strike prices for iron condor strategy"""
        atm_strike = round(current_price)
        spread_width = max(5, int(current_price * 0.05))  # 5% spread width
        
        return {
            "call_short": atm_strike + spread_width,
            "call_long": atm_strike + spread_width * 2,
            "put_short": atm_strike - spread_width,
            "put_long": atm_strike - spread_width * 2,
            "atm_strike": atm_strike
        }
    
    def _calculate_calendar_strikes(self, current_price: float) -> Dict[str, float]:
        """Calculate strike prices for calendar spread strategy"""
        atm_strike = round(current_price)
        return {
            "short_strike": atm_strike,
            "long_strike": atm_strike,
            "atm_strike": atm_strike
        }
    
    def _calculate_volatility_strikes(self, current_price: float) -> Dict[str, float]:
        """Calculate strike prices for volatility strategy"""
        atm_strike = round(current_price)
        otm_distance = max(5, int(current_price * 0.1))  # 10% OTM
        
        return {
            "call_strike": atm_strike + otm_distance,
            "put_strike": atm_strike - otm_distance,
            "atm_strike": atm_strike
        }
    
    def _calculate_butterfly_strikes(self, current_price: float) -> Dict[str, float]:
        """Calculate strike prices for butterfly spread strategy"""
        atm_strike = round(current_price)
        wing_width = max(5, int(current_price * 0.05))  # 5% wing width
        
        return {
            "call_long": atm_strike - wing_width,
            "call_short": atm_strike,
            "call_long_otm": atm_strike + wing_width,
            "atm_strike": atm_strike
        }
    
    def _determine_risk_level(self, confidence: float) -> RiskLevel:
        """Determine risk level based on confidence"""
        if confidence >= 0.8:
            return RiskLevel.HIGH
        elif confidence >= 0.6:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Filter signals by confidence and relevance"""
        # Filter by minimum confidence
        filtered = [signal for signal in signals if signal.confidence >= 0.6]
        
        # Sort by confidence (highest first)
        filtered.sort(key=lambda x: x.confidence, reverse=True)
        
        # Limit to top 3 signals
        return filtered[:3]
    
    def get_recommended_strategy_config(self, signal: TradingSignal) -> Dict[str, Any]:
        """Get recommended strategy configuration for a signal"""
        risk_config = self.risk_levels[signal.risk_level.value]
        
        return {
            "min_dte": 15,
            "max_dte": 60,
            "profit_target_pct": risk_config["profit_target_pct"],
            "stop_loss_pct": risk_config["stop_loss_pct"],
            "max_position_size": risk_config["max_position_size"],
            "min_confidence": risk_config["min_confidence"]
        }
    
    def generate_options_trading_plan(self, symbol: str, pattern: ElliottWavePattern, current_price: float) -> Dict[str, Any]:
        """Generate comprehensive options trading plan"""
        # Generate all signals
        signals = self.analyze_for_options(symbol, pattern, current_price)
        
        # Select primary signal
        primary_signal = signals[0] if signals else None
        
        if not primary_signal:
            return {
                "symbol": symbol,
                "primary_signal": None,
                "recommended_strategy": "No suitable strategy",
                "strategy_config": {},
                "strike_selection": {},
                "risk_management": {
                    "risk_level": "low",
                    "max_position_size": 0.01,
                    "profit_target": None,
                    "stop_loss": None
                }
            }
        
        # Generate strategy configuration
        strategy_config = self.get_recommended_strategy_config(primary_signal)
        
        # Create trading plan
        trading_plan = {
            "symbol": symbol,
            "primary_signal": {
                "signal_type": primary_signal.signal_type.value,
                "confidence": primary_signal.confidence,
                "description": primary_signal.description
            },
            "recommended_strategy": primary_signal.recommended_strategy,
            "strategy_config": strategy_config,
            "strike_selection": primary_signal.strike_selection,
            "risk_management": {
                "risk_level": primary_signal.risk_level.value,
                "profit_target": primary_signal.profit_target,
                "stop_loss": primary_signal.stop_loss,
                "max_position_size": strategy_config["max_position_size"]
            },
            "alternative_signals": [
                {
                    "signal_type": signal.signal_type.value,
                    "strategy": signal.recommended_strategy,
                    "confidence": signal.confidence
                }
                for signal in signals[1:3]  # Next 2 signals
            ]
        }
        
        return trading_plan