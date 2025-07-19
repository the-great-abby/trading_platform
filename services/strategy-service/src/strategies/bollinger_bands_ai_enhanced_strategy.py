"""
AI-Enhanced Bollinger Bands Strategy - Combines Bollinger Bands with AI-powered market analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import os

from .base import BaseStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
from ..core.types import TradeSignal
from ..services.ai.ollama_service import OllamaService, AIAnalysis


@dataclass
class BollingerEnhancedSignal:
    """Enhanced Bollinger Bands signal with AI analysis"""
    upper_band: float
    lower_band: float
    middle_band: float
    percent_b: float
    bandwidth: float
    signal_type: str
    technical_confidence: float
    ai_confidence: float
    ai_reasoning: str
    market_context: Dict[str, Any]


class BollingerBandsAIEnhancedStrategy(BaseStrategy):
    """Bollinger Bands Strategy enhanced with AI-powered market analysis"""
    
    def __init__(self, 
                 period: int = 20,
                 std_dev: float = 2.0,
                 threshold: float = 0.02,
                 ai_weight: float = 0.4,
                 technical_weight: float = 0.6,
                 **kwargs):
        super().__init__(name="BollingerBands_AI_Enhanced", **kwargs)
        self.period = period
        self.std_dev = std_dev
        self.threshold = threshold
        self.ai_weight = ai_weight
        self.technical_weight = technical_weight
        self.ollama_service = None
        self.base_strategy = BollingerBandsStrategy(period=period, std_dev=std_dev, threshold=threshold)
        
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
        """Generate AI-enhanced Bollinger Bands trading signal"""
        
        if data.empty or len(data) < self.period:
            return None
        
        # Get base Bollinger Bands signal
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
        """Enhance Bollinger Bands signal with AI analysis"""
        
        try:
            # Calculate Bollinger Bands
            sma = data['Close'].rolling(window=self.period).mean()
            std = data['Close'].rolling(window=self.period).std()
            upper_band = sma + (std * self.std_dev)
            lower_band = sma - (std * self.std_dev)
            
            current_price = data['Close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_sma = sma.iloc[-1]
            
            # Calculate bandwidth and %B
            bandwidth = (current_upper - current_lower) / current_sma
            percent_b = (current_price - current_lower) / (current_upper - current_lower)
            
            # Prepare market context for AI
            market_context = await self._prepare_market_context(symbol, data, current_price, current_upper, current_lower, current_sma, percent_b, bandwidth)
            
            # Prepare technical signals for AI
            technical_signals = [{
                'indicator': 'BOLLINGER_BANDS',
                'upper_band': current_upper,
                'lower_band': current_lower,
                'middle_band': current_sma,
                'current_price': current_price,
                'percent_b': percent_b,
                'bandwidth': bandwidth,
                'signal': base_signal.action,
                'strength': abs(percent_b - 0.5) * 2,  # 0-1 strength
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
            print(f"Error enhancing Bollinger Bands signal with AI for {symbol}: {e}")
            return base_signal  # Fallback to base signal
    
    async def _prepare_market_context(self, symbol: str, data: pd.DataFrame, current_price: float, 
                                    upper_band: float, lower_band: float, sma: float, 
                                    percent_b: float, bandwidth: float) -> Dict[str, Any]:
        """Prepare market context for AI analysis"""
        
        volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000
        
        # Calculate additional market metrics
        price_change_24h = (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0
        volatility = data['Close'].rolling(window=20).std().iloc[-1] / current_price if len(data) >= 20 else 0
        
        # Bollinger Bands analysis
        bb_position = "squeeze" if bandwidth < 0.1 else "expansion" if bandwidth > 0.2 else "normal"
        bb_signal_strength = "strong" if abs(percent_b - 0.5) > 0.3 else "weak"
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume': volume,
            'price_change_24h': price_change_24h,
            'volatility': volatility,
            'bollinger_bands': {
                'upper_band': upper_band,
                'lower_band': lower_band,
                'middle_band': sma,
                'percent_b': percent_b,
                'bandwidth': bandwidth,
                'position': bb_position,
                'signal_strength': bb_signal_strength
            },
            'market_conditions': {
                'trend': "bullish" if current_price > sma else "bearish",
                'momentum': "positive" if price_change_24h > 0 else "negative",
                'volatility_level': "high" if volatility > 0.02 else "low",
                'bb_squeeze': bb_position == "squeeze"
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
                'bollinger_analysis': {
                    'percent_b': market_context['bollinger_bands']['percent_b'],
                    'bandwidth': market_context['bollinger_bands']['bandwidth'],
                    'position': market_context['bollinger_bands']['position'],
                    'signal_strength': market_context['bollinger_bands']['signal_strength']
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
        """Get AI-powered insights about the Bollinger Bands strategy performance"""
        
        if not self.ollama_service or data.empty:
            return {"error": "AI service not available or insufficient data"}
        
        try:
            # Calculate Bollinger Bands
            sma = data['Close'].rolling(window=self.period).mean()
            std = data['Close'].rolling(window=self.period).std()
            upper_band = sma + (std * self.std_dev)
            lower_band = sma - (std * self.std_dev)
            
            current_price = data['Close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_sma = sma.iloc[-1]
            
            bandwidth = (current_upper - current_lower) / current_sma
            percent_b = (current_price - current_lower) / (current_upper - current_lower)
            
            market_context = await self._prepare_market_context(symbol, data, current_price, current_upper, current_lower, current_sma, percent_b, bandwidth)
            
            # Generate insights prompt
            insights_prompt = f"""
            Analyze the Bollinger Bands strategy performance for {symbol} and provide insights:
            
            Current Price: ${current_price:.2f}
            Upper Band: ${current_upper:.2f}
            Lower Band: ${current_lower:.2f}
            Middle Band (SMA): ${current_sma:.2f}
            %B: {percent_b:.3f}
            Bandwidth: {bandwidth:.3f}
            Market Context: {market_context}
            
            Provide insights on:
            1. Current Bollinger Bands position and implications
            2. Volatility assessment and squeeze potential
            3. Strategy effectiveness in current market conditions
            4. Risk assessment and position sizing recommendations
            5. Market timing considerations
            
            Respond in JSON format:
            {{
                "bb_position": "string",
                "volatility_assessment": "string",
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
                "current_price": current_price,
                "bollinger_bands": {
                    "upper": current_upper,
                    "lower": current_lower,
                    "middle": current_sma,
                    "percent_b": percent_b,
                    "bandwidth": bandwidth
                },
                "market_context": market_context,
                "ai_insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to generate insights: {e}"} 