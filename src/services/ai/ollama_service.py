"""
Ollama AI Service - Provides AI-powered market analysis and sentiment enhancement
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from ...core.types import TradeSignal


@dataclass
class AIAnalysis:
    """AI analysis result"""
    sentiment_score: float
    confidence: float
    reasoning: str
    risk_assessment: str
    market_impact: str
    recommended_action: str
    metadata: Dict[str, Any]


class OllamaService:
    """Ollama AI service for enhanced market analysis"""
    
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_market_sentiment(self, 
                                     news_events: List[Dict[str, Any]], 
                                     technical_signals: List[Dict[str, Any]],
                                     market_data: Dict[str, Any]) -> AIAnalysis:
        """Analyze market sentiment using AI"""
        
        prompt = self._build_analysis_prompt(news_events, technical_signals, market_data)
        
        try:
            response = await self._call_ollama(prompt)
            return self._parse_ai_response(response)
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._fallback_analysis()
    
    async def enhance_news_sentiment(self, news_event: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance news sentiment analysis with AI"""
        
        prompt = f"""
        Analyze this financial news event and provide enhanced sentiment analysis:
        
        Title: {news_event.get('title', '')}
        Content: {news_event.get('content', '')}
        Source: {news_event.get('source', '')}
        Event Type: {news_event.get('event_type', '')}
        Affected Symbols: {news_event.get('affected_symbols', [])}
        
        Please provide:
        1. Enhanced sentiment score (-1.0 to 1.0)
        2. Market impact assessment (low/medium/high)
        3. Risk level (low/medium/high)
        4. Reasoning for the analysis
        5. Potential trading implications
        
        Respond in JSON format:
        {{
            "enhanced_sentiment": float,
            "market_impact": "string",
            "risk_level": "string", 
            "reasoning": "string",
            "trading_implications": "string"
        }}
        """
        
        try:
            response = await self._call_ollama(prompt)
            enhanced_data = json.loads(response)
            return {**news_event, **enhanced_data}
        except Exception as e:
            logger.error(f"Error enhancing news sentiment: {e}")
            return news_event
    
    async def generate_multi_factor_signal(self, 
                                         symbol: str,
                                         technical_signals: List[Dict[str, Any]],
                                         news_sentiment: Dict[str, Any],
                                         market_context: Dict[str, Any]) -> Optional[TradeSignal]:
        """Generate multi-factor trading signal combining technical and fundamental analysis"""
        
        prompt = f"""
        Generate a trading signal for {symbol} based on the following factors:
        
        Technical Signals: {json.dumps(technical_signals, indent=2)}
        News Sentiment: {json.dumps(news_sentiment, indent=2)}
        Market Context: {json.dumps(market_context, indent=2)}
        
        Consider:
        1. Technical indicator strength and consistency
        2. News sentiment impact and timing
        3. Market conditions and volatility
        4. Risk-reward ratio
        5. Position sizing recommendations
        
        Respond with a trading decision in JSON format:
        {{
            "action": "BUY/SELL/HOLD",
            "confidence": float (0.0-1.0),
            "reasoning": "string",
            "risk_level": "low/medium/high",
            "position_size": "percentage of portfolio",
            "stop_loss": "percentage",
            "take_profit": "percentage"
        }}
        """
        
        try:
            response = await self._call_ollama(prompt)
            signal_data = json.loads(response)
            
            if signal_data.get('action') in ['BUY', 'SELL']:
                return TradeSignal(
                    symbol=symbol,
                    action=signal_data['action'],
                    quantity=self._calculate_quantity(signal_data),
                    price=market_context.get('current_price', 0),
                    timestamp=datetime.now(),
                    strategy="AI_MULTI_FACTOR",
                    confidence=signal_data.get('confidence', 0.5),
                    metadata={
                        "reasoning": signal_data.get('reasoning', ''),
                        "risk_level": signal_data.get('risk_level', 'medium'),
                        "position_size": signal_data.get('position_size', '5%'),
                        "stop_loss": signal_data.get('stop_loss', '2%'),
                        "take_profit": signal_data.get('take_profit', '10%'),
                        "ai_enhanced": True
                    }
                )
        except Exception as e:
            logger.error(f"Error generating multi-factor signal: {e}")
        
        return None
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=30
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('response', '')
            else:
                raise Exception(f"Ollama API error: {response.status}")
    
    def _build_analysis_prompt(self, 
                              news_events: List[Dict[str, Any]], 
                              technical_signals: List[Dict[str, Any]],
                              market_data: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt"""
        
        return f"""
        Analyze the current market situation and provide AI-powered insights:
        
        NEWS EVENTS ({len(news_events)} events):
        {json.dumps(news_events, indent=2)}
        
        TECHNICAL SIGNALS ({len(technical_signals)} signals):
        {json.dumps(technical_signals, indent=2)}
        
        MARKET DATA:
        {json.dumps(market_data, indent=2)}
        
        Provide analysis in JSON format:
        {{
            "overall_sentiment": float (-1.0 to 1.0),
            "confidence": float (0.0 to 1.0),
            "reasoning": "string",
            "risk_assessment": "low/medium/high",
            "market_impact": "bullish/bearish/neutral",
            "recommended_action": "string",
            "key_factors": ["factor1", "factor2", ...],
            "market_volatility": "low/medium/high"
        }}
        """
    
    def _parse_ai_response(self, response: str) -> AIAnalysis:
        """Parse AI response into structured format"""
        try:
            data = json.loads(response)
            return AIAnalysis(
                sentiment_score=data.get('overall_sentiment', 0.0),
                confidence=data.get('confidence', 0.5),
                reasoning=data.get('reasoning', ''),
                risk_assessment=data.get('risk_assessment', 'medium'),
                market_impact=data.get('market_impact', 'neutral'),
                recommended_action=data.get('recommended_action', ''),
                metadata={
                    'key_factors': data.get('key_factors', []),
                    'market_volatility': data.get('market_volatility', 'medium')
                }
            )
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return self._fallback_analysis()
    
    def _fallback_analysis(self) -> AIAnalysis:
        """Fallback analysis when AI fails"""
        return AIAnalysis(
            sentiment_score=0.0,
            confidence=0.3,
            reasoning="AI analysis unavailable, using fallback",
            risk_assessment="medium",
            market_impact="neutral",
            recommended_action="Hold positions, monitor market",
            metadata={'fallback': True}
        )
    
    def _calculate_quantity(self, signal_data: Dict[str, Any]) -> float:
        """Calculate position size based on AI recommendations"""
        position_size = signal_data.get('position_size', '5%')
        try:
            # Extract percentage and convert to decimal
            percentage = float(position_size.replace('%', '')) / 100
            return percentage
        except:
            return 0.05  # Default 5% 