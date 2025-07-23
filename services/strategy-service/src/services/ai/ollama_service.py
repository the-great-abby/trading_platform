"""
Ollama AI Service - Provides AI-powered market analysis and sentiment enhancement
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.utils.enhanced_logging import get_trading_logger
logger = get_trading_logger()

import os
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
    
    def __init__(self, base_url: str = "", model: str = ""):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "gemma3:1b")
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=float(os.environ.get("OLLAMA_TIMEOUT", "120.0")))
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def verify_model_availability(self) -> Dict[str, Any]:
        """Verify if the Ollama model is available and ready"""
        try:
            logger.info(f"[OllamaService] 🔍 Verifying model availability for: {self.model}")
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=float(os.environ.get("OLLAMA_TIMEOUT", "120.0")))
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Check if Ollama service is running
            logger.info(f"[OllamaService] 📡 Checking Ollama service at {self.base_url}/api/tags")
            async with self.session.get(f"{self.base_url}/api/tags", timeout=10) as response:
                logger.info(f"[OllamaService] 📥 Tags response: status={response.status}")
                
                if response.status == 200:
                    models_data = await response.json()
                    models = models_data.get('models', [])
                    logger.info(f"[OllamaService] 📊 Found {len(models)} available models")
                    
                    # Check if our target model is available
                    target_model = self.model
                    # Check for exact match first, then fallback to startswith
                    target_available = any(
                        model.get('name', '') == target_model or 
                        model.get('name', '').startswith(target_model.split(':')[0])
                        for model in models
                    )
                    
                    logger.info(f"[OllamaService] 🎯 Target model '{target_model}' available: {target_available}")
                    if not target_available:
                        logger.warning(f"[OllamaService] ⚠️ Available models: {[model.get('name', '') for model in models]}")
                    
                    return {
                        'available': True,
                        'total_models': len(models),
                        'target_available': target_available,
                        'target_model': target_model,
                        'available_models': [model.get('name', '') for model in models]
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"[OllamaService] ❌ Ollama service error: {response.status} - {error_text}")
                    return {
                        'available': False,
                        'error': f"Ollama service returned status {response.status}: {error_text}"
                    }
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Failed to connect to Ollama: {type(e).__name__}: {str(e)}")
            return {
                'available': False,
                'error': f"Failed to connect to Ollama: {str(e)}"
            }
    
    async def test_model_response(self) -> Dict[str, Any]:
        """Test if the model can generate a response"""
        try:
            logger.info(f"[OllamaService] 🧪 Testing model response for: {self.model}")
            test_prompt = "Respond with 'OK' if you can read this message."
            logger.info(f"[OllamaService] 📝 Test prompt: '{test_prompt}'")
            
            response = await self._call_ollama(test_prompt)
            
            if response and len(response.strip()) > 0:
                logger.info(f"[OllamaService] ✅ Model test successful: '{response.strip()}'")
                return {
                    'success': True,
                    'model_used': self.model,
                    'response': response.strip()
                }
            else:
                logger.error(f"[OllamaService] ❌ Model test failed: Empty response")
                return {
                    'success': False,
                    'error': 'Empty response from model'
                }
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Model test failed: {type(e).__name__}: {str(e)}")
            return {
                'success': False,
                'error': f"Model test failed: {str(e)}"
            }
    
    async def analyze_market_sentiment(self, news_events, technical_signals, market_data):
        logger.info(f"[OllamaService] 🤖 Starting LLM analysis for {market_data.get('symbol', 'unknown')}...")
        logger.info(f"[OllamaService] Technical signals: {len(technical_signals)} | News events: {len(news_events)} | Market data keys: {list(market_data.keys())}")
        prompt = self._build_analysis_prompt(news_events, technical_signals, market_data)
        logger.info(f"[OllamaService] 📤 Sending prompt to Ollama (length: {len(prompt)} chars)...")
        try:
            response = await self._call_ollama(prompt)
            logger.info(f"[OllamaService] 📥 Received response from Ollama (length: {len(response)} chars)")
            analysis = self._parse_ai_response(response)
            logger.info(f"[OllamaService] ✅ LLM analysis completed: Sentiment={getattr(analysis, 'sentiment_score', None)}, Confidence={getattr(analysis, 'confidence', None)}, Action={getattr(analysis, 'recommended_action', None)}")
            return analysis
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Error in AI analysis: {e}")
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
        """Call Ollama API with exponential backoff retry"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=float(os.environ.get("OLLAMA_TIMEOUT", "120.0")))
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Get timeout and retry settings from environment variables
        timeout = float(os.environ.get("OLLAMA_TIMEOUT", "30.0"))
        max_retries = int(os.environ.get("OLLAMA_MAX_RETRIES", "3"))
        base_delay = float(os.environ.get("OLLAMA_BASE_DELAY", "10.0"))
        max_delay = float(os.environ.get("OLLAMA_MAX_DELAY", "300.0"))
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        
        for attempt in range(max_retries + 1):
            start_time = datetime.now()
            logger.info(f"[OllamaService] 📤 Making API call to {self.base_url}/api/generate (attempt {attempt + 1}/{max_retries + 1})")
            logger.info(f"[OllamaService] 📊 Request details: model={self.model}, prompt_length={len(prompt)}, timeout={timeout}s")
            logger.debug(f"[OllamaService] 📝 Full prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
            logger.debug(f"[OllamaService] 📦 Request payload: {json.dumps(payload, indent=2)}")
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[OllamaService] 📥 Response received: status={response.status}, time={response_time:.2f}s")
                    
                    if response.status == 200:
                        response_data = await response.json()
                        response_text = response_data.get('response', '')
                        logger.info(f"[OllamaService] ✅ Success: response_length={len(response_text)}")
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"[OllamaService] ❌ HTTP {response.status}: {error_text}")
                        logger.error(f"[OllamaService] 📊 Response headers: {dict(response.headers)}")
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status < 500:
                            raise Exception(f"Ollama API client error: {response.status} - {error_text}")
                        
                        # Retry on server errors (5xx) and other errors
                        if attempt < max_retries:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            logger.warning(f"[OllamaService] ⏳ Retrying in {delay:.1f}s due to server error...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise Exception(f"Ollama API error after {max_retries + 1} attempts: {response.status} - {error_text}")
                        
            except asyncio.TimeoutError:
                response_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"[OllamaService] ⏰ Timeout after {response_time:.2f}s (limit: {timeout}s)")
                
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"[OllamaService] ⏳ Retrying in {delay:.1f}s due to timeout...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Ollama API timeout after {max_retries + 1} attempts ({timeout} seconds each)")
                    
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"[OllamaService] ❌ Exception after {response_time:.2f}s: {type(e).__name__}: {str(e)}")
                
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"[OllamaService] ⏳ Retrying in {delay:.1f}s due to exception...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Ollama API call failed after {max_retries + 1} attempts: {str(e)}")
        
        # This should never be reached, but just in case
        raise Exception(f"Ollama API call failed after {max_retries + 1} attempts")
    
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

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("[OllamaService] ✅ Session closed")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if self.session and not self.session.closed:
            logger.warning("[OllamaService] ⚠️ Session not properly closed in destructor") 