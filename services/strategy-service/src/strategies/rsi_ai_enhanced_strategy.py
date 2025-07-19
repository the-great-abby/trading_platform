"""
AI-Enhanced RSI Strategy - Combines RSI with AI-powered market analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import os

from .base import BaseStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from ..core.types import TradeSignal
from ..services.ai.ollama_service import OllamaService, AIAnalysis


@dataclass
class RSIEnhancedSignal:
    """Enhanced RSI signal with AI analysis"""
    rsi_value: float
    signal_type: str
    technical_confidence: float
    ai_confidence: float
    ai_reasoning: str
    market_context: Dict[str, Any]
    risk_assessment: str


class RSIEnhancedStrategy(BaseStrategy):
    """RSI Strategy enhanced with AI-powered market analysis"""
    
    def __init__(self, 
                 period: int = 14,
                 oversold: int = 30,
                 overbought: int = 70,
                 ai_weight: float = 0.4,
                 technical_weight: float = 0.6,
                 **kwargs):
        super().__init__(name="RSI_AI_Enhanced", **kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.ai_weight = ai_weight
        self.technical_weight = technical_weight
        self.ollama_service = None
        self.base_rsi_strategy = RSIStrategy(period=period, oversold=oversold, overbought=overbought)
        
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
        """Generate AI-enhanced RSI trading signal"""
        
        if data.empty or len(data) < self.period:
            return None
        
        # Get base RSI signal
        base_signal = await self.base_rsi_strategy.generate_signal(symbol, data)
        
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
        """Enhance RSI signal with AI analysis"""
        
        try:
            # Calculate RSI
            rsi = self._calculate_rsi(data)
            current_rsi = rsi.iloc[-1]
            
            # Prepare market context for AI
            market_context = await self._prepare_market_context(symbol, data, current_rsi)
            
            # Prepare technical signals for AI
            technical_signals = [{
                'indicator': 'RSI',
                'value': current_rsi,
                'signal': base_signal.action,
                'oversold_threshold': self.oversold,
                'overbought_threshold': self.overbought,
                'strength': abs(50 - current_rsi) / 50,  # 0-1 strength
                'confidence': base_signal.confidence
            }]
            
            # Generate AI analysis
            if self.ollama_service:
                ai_analysis = await self.ollama_service.analyze_market_sentiment(
                    news_events=[],  # Could be enhanced with news data
                    technical_signals=technical_signals,
                    market_data=market_context
                )
            else:
                return base_signal
            
            # Combine technical and AI signals
            enhanced_signal = await self._combine_signals(base_signal, ai_analysis, market_context)
            
            return enhanced_signal
            
        except Exception as e:
            print(f"Error enhancing RSI signal with AI for {symbol}: {e}")
            return base_signal  # Fallback to base signal
    
    async def _prepare_market_context(self, symbol: str, data: pd.DataFrame, current_rsi: float) -> Dict[str, Any]:
        """Prepare market context for AI analysis"""
        
        current_price = data['Close'].iloc[-1]
        volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000
        
        # Calculate additional market metrics
        price_change_24h = (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0
        volatility = data['Close'].rolling(window=20).std().iloc[-1] / current_price if len(data) >= 20 else 0
        
        # RSI trend analysis
        rsi_trend = "bullish" if current_rsi > 50 else "bearish"
        rsi_strength = "strong" if abs(50 - current_rsi) > 20 else "weak"
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume': volume,
            'price_change_24h': price_change_24h,
            'volatility': volatility,
            'rsi_value': current_rsi,
            'rsi_trend': rsi_trend,
            'rsi_strength': rsi_strength,
            'market_conditions': {
                'trend': rsi_trend,
                'momentum': "positive" if price_change_24h > 0 else "negative",
                'volatility_level': "high" if volatility > 0.02 else "low"
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
                'signal_enhancement': {
                    'original_confidence': base_signal.confidence,
                    'enhanced_confidence': combined_confidence,
                    'confidence_boost': combined_confidence - base_signal.confidence
                }
            }
        )
        
        return enhanced_signal
    
    def _calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.astype(float)
    
    def _calculate_enhanced_quantity(self, base_quantity: float, confidence: float) -> float:
        """Calculate enhanced position size based on AI confidence"""
        # Adjust position size based on AI confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1x based on confidence
        return base_quantity * confidence_multiplier
    
    async def get_strategy_insights(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get AI-powered insights about the strategy performance"""
        
        if not self.ollama_service or data.empty:
            return {"error": "AI service not available or insufficient data"}
        
        try:
            rsi = self._calculate_rsi(data)
            current_rsi = rsi.iloc[-1]
            
            market_context = await self._prepare_market_context(symbol, data, current_rsi)
            
            # Generate insights prompt
            insights_prompt = f"""
            Analyze the RSI strategy performance for {symbol} and provide insights:
            
            Current RSI: {current_rsi:.2f}
            Market Context: {market_context}
            
            Provide insights on:
            1. Current market conditions for RSI strategy
            2. Risk assessment
            3. Strategy effectiveness
            4. Recommendations for parameter adjustment
            5. Market timing considerations
            
            Respond in JSON format:
            {{
                "market_conditions": "string",
                "risk_assessment": "string",
                "strategy_effectiveness": "string",
                "parameter_recommendations": "string",
                "timing_considerations": "string",
                "confidence": float
            }}
            """
            
            response = await self.ollama_service._call_ollama(insights_prompt)
            insights = json.loads(response)
            
            return {
                "symbol": symbol,
                "current_rsi": current_rsi,
                "market_context": market_context,
                "ai_insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to generate insights: {e}"} 