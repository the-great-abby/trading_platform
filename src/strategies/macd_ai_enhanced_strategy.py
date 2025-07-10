"""
AI-Enhanced MACD Strategy - Combines MACD with AI-powered market analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import os

from .base import BaseStrategy
from .macd_strategy import MACDStrategy
from ..core.types import TradeSignal
from ..services.ai.ollama_service import OllamaService, AIAnalysis


@dataclass
class MACDEnhancedSignal:
    """Enhanced MACD signal with AI analysis"""
    macd_line: float
    signal_line: float
    histogram: float
    signal_type: str
    technical_confidence: float
    ai_confidence: float
    ai_reasoning: str
    market_context: Dict[str, Any]


class MACDAIEnhancedStrategy(BaseStrategy):
    """MACD Strategy enhanced with AI-powered market analysis"""
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26,
                 signal_period: int = 9,
                 ai_weight: float = 0.4,
                 technical_weight: float = 0.6,
                 **kwargs):
        super().__init__(name="MACD_AI_Enhanced", **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.ai_weight = ai_weight
        self.technical_weight = technical_weight
        self.ollama_service = None
        self.base_strategy = MACDStrategy(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
        
    async def initialize(self, ollama_url: str = None):
        """Initialize the strategy with Ollama service"""
        if ollama_url is None:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        try:
            self.ollama_service = OllamaService(base_url=ollama_url)
            print(f"✅ AI service initialized for {self.name}")
        except Exception as e:
            print(f"⚠️  AI service not available for {self.name}: {e}")
            self.ollama_service = None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate AI-enhanced MACD trading signal"""
        
        if data.empty or len(data) < self.slow_period:
            return None
        
        # Get base MACD signal
        base_signal = await self.base_strategy.generate_signal(symbol, data)
        
        if not base_signal:
            return None
        
        # Enhance with AI if available
        if self.ollama_service:
            enhanced_signal = await self._enhance_with_ai(symbol, base_signal, data)
            return enhanced_signal
        else:
            # Return base signal if AI not available
            return base_signal
    
    async def _enhance_with_ai(self, 
                              symbol: str, 
                              base_signal: TradeSignal, 
                              data: pd.DataFrame) -> Optional[TradeSignal]:
        """Enhance MACD signal with AI analysis"""
        
        try:
            # Calculate MACD
            exp1 = data['Close'].ewm(span=self.fast_period).mean()
            exp2 = data['Close'].ewm(span=self.slow_period).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            
            # Prepare market context for AI
            market_context = await self._prepare_market_context(symbol, data, current_macd, current_signal, current_histogram)
            
            # Prepare technical signals for AI
            technical_signals = [{
                'indicator': 'MACD',
                'macd_line': current_macd,
                'signal_line': current_signal,
                'histogram': current_histogram,
                'signal': base_signal.action,
                'strength': abs(current_histogram) / abs(current_signal) if current_signal != 0 else 0,
                'confidence': base_signal.confidence
            }]
            
            # Generate AI analysis
            if self.ollama_service:
                ai_analysis = await self.ollama_service.analyze_market_sentiment(
                    news_events=[],  # Could be enhanced with news data
                    technical_signals=technical_signals,
                    market_data=market_context
                )
                
                # Combine technical and AI signals
                enhanced_signal = await self._combine_signals(base_signal, ai_analysis, market_context)
                
                return enhanced_signal
            else:
                return base_signal
            
        except Exception as e:
            print(f"Error enhancing MACD signal with AI for {symbol}: {e}")
            return base_signal  # Fallback to base signal
    
    async def _prepare_market_context(self, symbol: str, data: pd.DataFrame, 
                                    macd_line: float, signal_line: float, histogram: float) -> Dict[str, Any]:
        """Prepare market context for AI analysis"""
        
        current_price = data['Close'].iloc[-1]
        volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000
        
        # Calculate additional market metrics
        price_change_24h = (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0
        volatility = data['Close'].rolling(window=20).std().iloc[-1] / current_price if len(data) >= 20 else 0
        
        # MACD analysis
        macd_trend = "bullish" if macd_line > signal_line else "bearish"
        macd_strength = "strong" if abs(histogram) > abs(signal_line) * 0.1 else "weak"
        macd_divergence = "positive" if histogram > 0 and price_change_24h > 0 else "negative" if histogram < 0 and price_change_24h < 0 else "neutral"
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume': volume,
            'price_change_24h': price_change_24h,
            'volatility': volatility,
            'macd_analysis': {
                'macd_line': macd_line,
                'signal_line': signal_line,
                'histogram': histogram,
                'trend': macd_trend,
                'strength': macd_strength,
                'divergence': macd_divergence
            },
            'market_conditions': {
                'trend': macd_trend,
                'momentum': "positive" if price_change_24h > 0 else "negative",
                'volatility_level': "high" if volatility > 0.02 else "low",
                'macd_crossover': macd_line > signal_line
            }
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
        
        # Create enhanced signal
        enhanced_signal = TradeSignal(
            symbol=base_signal.symbol,
            action=action,
            quantity=self._calculate_enhanced_quantity(base_signal.quantity, combined_confidence),
            price=base_signal.price,
            timestamp=base_signal.timestamp,
            strategy=f"{self.name}_AI",
            confidence=combined_confidence,
            metadata={
                **base_signal.metadata,
                'ai_enhanced': True,
                'ai_sentiment': ai_analysis.sentiment_score,
                'ai_confidence': ai_confidence,
                'ai_reasoning': ai_analysis.reasoning,
                'ai_risk_assessment': ai_analysis.risk_assessment,
                'ai_market_impact': ai_analysis.market_impact,
                'technical_confidence': technical_confidence,
                'combined_confidence': combined_confidence,
                'market_context': market_context,
                'macd_analysis': {
                    'macd_line': market_context['macd_analysis']['macd_line'],
                    'signal_line': market_context['macd_analysis']['signal_line'],
                    'histogram': market_context['macd_analysis']['histogram'],
                    'trend': market_context['macd_analysis']['trend'],
                    'strength': market_context['macd_analysis']['strength'],
                    'divergence': market_context['macd_analysis']['divergence']
                },
                'signal_enhancement': {
                    'original_confidence': base_signal.confidence,
                    'enhanced_confidence': combined_confidence,
                    'confidence_boost': combined_confidence - base_signal.confidence
                }
            }
        )
        
        return enhanced_signal
    
    def _calculate_enhanced_quantity(self, base_quantity: float, confidence: float) -> float:
        """Calculate enhanced position size based on AI confidence"""
        # Adjust position size based on AI confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1x based on confidence
        return base_quantity * confidence_multiplier
    
    async def get_strategy_insights(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get AI-powered insights about the MACD strategy performance"""
        
        if not self.ollama_service or data.empty:
            return {"error": "AI service not available or insufficient data"}
        
        try:
            # Calculate MACD
            exp1 = data['Close'].ewm(span=self.fast_period).mean()
            exp2 = data['Close'].ewm(span=self.slow_period).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            
            market_context = await self._prepare_market_context(symbol, data, current_macd, current_signal, current_histogram)
            
            # Generate insights prompt
            insights_prompt = f"""
            Analyze the MACD strategy performance for {symbol} and provide insights:
            
            Current Price: ${data['Close'].iloc[-1]:.2f}
            MACD Line: {current_macd:.4f}
            Signal Line: {current_signal:.4f}
            Histogram: {current_histogram:.4f}
            Market Context: {market_context}
            
            Provide insights on:
            1. Current MACD position and trend analysis
            2. Momentum assessment and crossover signals
            3. Strategy effectiveness in current market conditions
            4. Risk assessment and position sizing recommendations
            5. Market timing considerations
            
            Respond in JSON format:
            {{
                "macd_position": "string",
                "momentum_assessment": "string",
                "strategy_effectiveness": "string",
                "risk_assessment": "string",
                "timing_considerations": "string",
                "confidence": float
            }}
            """
            
            response = await self.ollama_service._call_ollama(insights_prompt)
            insights = json.loads(response)
            
            return {
                "symbol": symbol,
                "current_price": data['Close'].iloc[-1],
                "macd_analysis": {
                    "macd_line": current_macd,
                    "signal_line": current_signal,
                    "histogram": current_histogram
                },
                "market_context": market_context,
                "ai_insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to generate insights: {e}"} 