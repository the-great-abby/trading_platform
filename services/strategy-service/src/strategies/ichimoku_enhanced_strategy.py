"""
Enhanced Ichimoku Strategy with AI Integration
=============================================

Combines Ichimoku Cloud analysis with AI enhancement and other strategies
for comprehensive trading signals with entry/exit price levels.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

from .base import BaseStrategy
from .ichimoku_strategy import IchimokuStrategy
from ..core.types import TradeSignal
from ..services.ai.ollama_service import OllamaService
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class AIAnalysis:
    """AI analysis result"""
    def __init__(self, sentiment_score: float, confidence: float, reasoning: str):
        self.sentiment_score = sentiment_score
        self.confidence = confidence
        self.reasoning = reasoning

class IchimokuEnhancedStrategy(BaseStrategy):
    """
    Enhanced Ichimoku Strategy with AI Integration
    
    Features:
    - Ichimoku Cloud analysis with entry/exit levels
    - AI sentiment analysis integration
    - Multi-strategy confirmation
    - Advanced risk management
    - Portfolio integration
    """
    
    def __init__(self, 
                 ai_weight: float = 0.3,
                 technical_weight: float = 0.7,
                 min_confidence: float = 0.6,
                 use_llm_evaluation: bool = True,
                 **kwargs):
        super().__init__(name="Ichimoku_Enhanced_Strategy", **kwargs)
        
        # Weights for signal combination
        self.ai_weight = ai_weight
        self.technical_weight = technical_weight
        self.min_confidence = min_confidence
        self.use_llm_evaluation = use_llm_evaluation
        
        # Initialize base Ichimoku strategy
        self.ichimoku_strategy = IchimokuStrategy(**kwargs)
        
        # AI service
        self.ollama_service = None
        
        # Market context
        self.market_context = {}
    
    async def initialize(self, ollama_url: str = "http://ollama:11434"):
        """Initialize the strategy with AI service"""
        try:
            self.ollama_service = OllamaService(base_url=ollama_url)
            logger.info("✅ Initialized Ichimoku Enhanced Strategy with AI")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize AI service: {e}")
            self.ollama_service = None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate enhanced Ichimoku trading signal"""
        
        if len(data) < 60:  # Need sufficient data for Ichimoku
            return None
        
        # Get base Ichimoku signal
        base_signal = await self.ichimoku_strategy.generate_signal(symbol, data)
        if not base_signal:
            return None
        
        # Get AI analysis if available
        ai_analysis = None
        if self.ollama_service:
            ai_analysis = await self._get_ai_analysis(symbol, data, base_signal)
        
        # Get market context
        market_context = self._get_market_context(data)
        
        # Combine signals
        if ai_analysis:
            enhanced_signal = await self._combine_signals(base_signal, ai_analysis, market_context)
        else:
            enhanced_signal = base_signal
        
        # Apply LLM evaluation if enabled
        if self.use_llm_evaluation and self.ollama_service:
            enhanced_signal = await self._evaluate_with_llm(enhanced_signal, symbol, data)
        
        return enhanced_signal
    
    async def _get_ai_analysis(self, symbol: str, data: pd.DataFrame, base_signal: TradeSignal) -> Optional[AIAnalysis]:
        """Get AI analysis for the signal"""
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(symbol, data, base_signal)
            
            # Get AI analysis
            response = await self.ollama_service.analyze_trading_signal(
                symbol=symbol,
                signal_type="ichimoku_enhanced",
                context=context
            )
            
            if response and 'analysis' in response:
                analysis = response['analysis']
                return AIAnalysis(
                    sentiment_score=analysis.get('sentiment_score', 0.0),
                    confidence=analysis.get('confidence', 0.5),
                    reasoning=analysis.get('reasoning', '')
                )
            
        except Exception as e:
            logger.error(f"AI analysis failed for {symbol}: {e}")
        
        return None
    
    def _prepare_ai_context(self, symbol: str, data: pd.DataFrame, base_signal: TradeSignal) -> Dict[str, Any]:
        """Prepare context for AI analysis"""
        
        # Get Ichimoku levels
        ichimoku_data = self.ichimoku_strategy.calculate_ichimoku(data)
        current_price = data['Close'].iloc[-1]
        
        # Get cloud analysis
        cloud_analysis = self.ichimoku_strategy.analyze_cloud_position(ichimoku_data)
        crossover_analysis = self.ichimoku_strategy.analyze_tenkan_kijun_crossover(ichimoku_data)
        chikou_analysis = self.ichimoku_strategy.analyze_chikou_position(ichimoku_data)
        support_resistance = self.ichimoku_strategy.calculate_support_resistance(ichimoku_data)
        
        # Calculate technical indicators
        rsi = self._calculate_rsi(data)
        macd = self._calculate_macd(data)
        bb_position = self._calculate_bollinger_position(data)
        
        context = {
            'symbol': symbol,
            'current_price': current_price,
            'signal_action': base_signal.action,
            'signal_confidence': base_signal.confidence,
            'ichimoku_levels': {
                'tenkan': ichimoku_data['Tenkan'].iloc[-1] if not pd.isna(ichimoku_data['Tenkan'].iloc[-1]) else None,
                'kijun': ichimoku_data['Kijun'].iloc[-1] if not pd.isna(ichimoku_data['Kijun'].iloc[-1]) else None,
                'senkou_a': ichimoku_data['Senkou_A'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_A'].iloc[-1]) else None,
                'senkou_b': ichimoku_data['Senkou_B'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_B'].iloc[-1]) else None,
                'chikou': ichimoku_data['Chikou'].iloc[-1] if not pd.isna(ichimoku_data['Chikou'].iloc[-1]) else None
            },
            'cloud_analysis': cloud_analysis,
            'crossover_analysis': crossover_analysis,
            'chikou_analysis': chikou_analysis,
            'support_resistance': support_resistance,
            'technical_indicators': {
                'rsi': rsi,
                'macd': macd,
                'bollinger_position': bb_position
            },
            'price_action': {
                'price_change_1d': (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0,
                'price_change_5d': (current_price - data['Close'].iloc[-6]) / data['Close'].iloc[-6] if len(data) > 5 else 0,
                'volume_ratio': data['Volume'].iloc[-1] / data['Volume'].rolling(20).mean().iloc[-1] if len(data) > 20 else 1
            }
        }
        
        return context
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI"""
        if len(data) < period + 1:
            return 50.0
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD"""
        if len(data) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'macd': macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0,
            'signal': signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0,
            'histogram': histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0
        }
    
    def _calculate_bollinger_position(self, data: pd.DataFrame, period: int = 20, std: int = 2) -> float:
        """Calculate position within Bollinger Bands"""
        if len(data) < period:
            return 0.5
        
        sma = data['Close'].rolling(window=period).mean()
        std_dev = data['Close'].rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        current_price = data['Close'].iloc[-1]
        upper = upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else current_price
        lower = lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else current_price
        
        if upper == lower:
            return 0.5
        
        return (current_price - lower) / (upper - lower)
    
    def _get_market_context(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get market context for signal combination"""
        if len(data) < 20:
            return {}
        
        current_price = data['Close'].iloc[-1]
        
        # Calculate volatility
        returns = data['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Calculate trend
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) > 50 else sma_20
        
        trend = "bullish" if sma_20 > sma_50 else "bearish" if sma_20 < sma_50 else "neutral"
        
        return {
            'volatility': volatility,
            'trend': trend,
            'price_level': current_price,
            'volume_trend': data['Volume'].iloc[-5:].mean() / data['Volume'].iloc[-20:].mean() if len(data) > 20 else 1
        }
    
    async def _combine_signals(self, 
                              base_signal: TradeSignal, 
                              ai_analysis: AIAnalysis,
                              market_context: Dict[str, Any]) -> TradeSignal:
        """Combine technical and AI signals"""
        
        # Calculate combined confidence
        technical_confidence = base_signal.confidence
        ai_confidence = ai_analysis.confidence
        
        combined_confidence = (technical_confidence * self.technical_weight + 
                              ai_confidence * self.ai_weight)
        
        # Adjust action based on AI sentiment if significant
        action = base_signal.action
        if abs(ai_analysis.sentiment_score) > 0.3:
            if ai_analysis.sentiment_score > 0 and base_signal.action == "BUY":
                combined_confidence = min(combined_confidence * 1.2, 0.95)  # Boost confidence
            elif ai_analysis.sentiment_score < 0 and base_signal.action == "SELL":
                combined_confidence = min(combined_confidence * 1.2, 0.95)  # Boost confidence
            elif ai_analysis.sentiment_score < 0 and base_signal.action == "BUY":
                combined_confidence *= 0.8  # Reduce confidence
            elif ai_analysis.sentiment_score > 0 and base_signal.action == "SELL":
                combined_confidence *= 0.8  # Reduce confidence
        
        # Adjust for market context
        if market_context.get('volatility', 0) > 0.3:  # High volatility
            combined_confidence *= 0.9  # Reduce confidence in high volatility
        
        # Create enhanced signal
        enhanced_signal = TradeSignal(
            symbol=base_signal.symbol,
            action=action,
            quantity=base_signal.quantity,
            price=base_signal.price,
            timestamp=base_signal.timestamp,
            strategy=self.name,
            confidence=combined_confidence,
            metadata={
                **base_signal.metadata,
                'ai_analysis': {
                    'sentiment_score': ai_analysis.sentiment_score,
                    'ai_confidence': ai_analysis.confidence,
                    'reasoning': ai_analysis.reasoning
                },
                'market_context': market_context,
                'signal_type': 'ichimoku_enhanced'
            }
        )
        
        return enhanced_signal
    
    async def _evaluate_with_llm(self, signal: TradeSignal, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Evaluate signal with LLM"""
        try:
            # Prepare evaluation context
            context = {
                'symbol': symbol,
                'signal_action': signal.action,
                'signal_confidence': signal.confidence,
                'current_price': data['Close'].iloc[-1],
                'ichimoku_levels': signal.metadata.get('ichimoku_levels', {}),
                'market_context': signal.metadata.get('market_context', {}),
                'ai_analysis': signal.metadata.get('ai_analysis', {})
            }
            
            # Get LLM evaluation
            evaluation = await self.ollama_service.evaluate_trade_signal(
                symbol=symbol,
                signal=signal,
                context=context
            )
            
            if evaluation and evaluation.get('approved', False):
                # Update signal with LLM reasoning
                signal.metadata['llm_evaluation'] = {
                    'approved': True,
                    'reasoning': evaluation.get('reasoning', ''),
                    'confidence_adjustment': evaluation.get('confidence_adjustment', 0)
                }
                
                # Apply confidence adjustment
                if 'confidence_adjustment' in evaluation:
                    signal.confidence = min(signal.confidence + evaluation['confidence_adjustment'], 0.95)
                
                return signal
            else:
                # Signal rejected by LLM
                logger.info(f"LLM rejected signal for {symbol}: {evaluation.get('reasoning', 'No reason provided')}")
                return None
                
        except Exception as e:
            logger.error(f"LLM evaluation failed for {symbol}: {e}")
            return signal  # Return original signal if LLM fails
    
    def get_entry_exit_prices(self, data: pd.DataFrame) -> Dict[str, float]:
        """Get recommended entry and exit prices"""
        return self.ichimoku_strategy.get_entry_exit_prices(data)
    
    def get_ichimoku_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive Ichimoku analysis"""
        ichimoku_data = self.ichimoku_strategy.calculate_ichimoku(data)
        
        return {
            'cloud_analysis': self.ichimoku_strategy.analyze_cloud_position(ichimoku_data),
            'crossover_analysis': self.ichimoku_strategy.analyze_tenkan_kijun_crossover(ichimoku_data),
            'chikou_analysis': self.ichimoku_strategy.analyze_chikou_position(ichimoku_data),
            'support_resistance': self.ichimoku_strategy.calculate_support_resistance(ichimoku_data),
            'ichimoku_levels': {
                'tenkan': ichimoku_data['Tenkan'].iloc[-1] if not pd.isna(ichimoku_data['Tenkan'].iloc[-1]) else None,
                'kijun': ichimoku_data['Kijun'].iloc[-1] if not pd.isna(ichimoku_data['Kijun'].iloc[-1]) else None,
                'senkou_a': ichimoku_data['Senkou_A'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_A'].iloc[-1]) else None,
                'senkou_b': ichimoku_data['Senkou_B'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_B'].iloc[-1]) else None,
                'chikou': ichimoku_data['Chikou'].iloc[-1] if not pd.isna(ichimoku_data['Chikou'].iloc[-1]) else None
            }
        } 