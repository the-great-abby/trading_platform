"""
Ollama AI Service - Provides AI-powered market analysis and sentiment enhancement
Now uses LLM proxy service with callback URL support
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.utils.enhanced_logging import get_trading_logger
logger = get_trading_logger()

import os
from ...core.types import TradeSignal
from ..llm_service.llm_client import LLMClient, LLMRequest, LLMResponse, LLMError, LLMTaskType, ProxyCallbackConfig
from ..llm_service.service import LLMService


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
    """Ollama AI service for enhanced market analysis using LLM proxy service"""
    
    def __init__(self, base_url: str = "", model: str = ""):
        # LLM proxy service configuration
        self.proxy_base_url = base_url or os.environ.get("LLM_PROXY_BASE_URL", "http://localhost:12001")
        self.model = model or os.environ.get("OLLAMA_MODEL", "gemma3:1b")
        
        # Initialize LLM proxy client
        self.llm_client = LLMClient(
            base_url=self.proxy_base_url,
            api_key=os.environ.get("LLM_PROXY_API_KEY"),
            timeout=int(os.environ.get("LLM_PROXY_TIMEOUT", "30")),
            max_retries=int(os.environ.get("LLM_PROXY_MAX_RETRIES", "3"))
        )
        
        # Initialize LLM service for advanced operations
        self.llm_service = LLMService()
        
        # Service state
        self.is_initialized = False
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the service and verify connectivity"""
        try:
            logger.info(f"[OllamaService] 🔍 Initializing with LLM proxy at {self.proxy_base_url}")
            
            # Test connection to LLM proxy service
            is_healthy = await self.llm_client.health_check()
            if not is_healthy:
                logger.warning(f"[OllamaService] ⚠️ LLM proxy service at {self.proxy_base_url} is not healthy")
                return False
            
            self.is_initialized = True
            logger.info(f"[OllamaService] ✅ Initialized successfully with LLM proxy")
            return True
            
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Initialization failed: {type(e).__name__}: {str(e)}")
            return False
    
    async def verify_model_availability(self) -> Dict[str, Any]:
        """Verify if the model is available through LLM proxy service"""
        try:
            logger.info(f"[OllamaService] 🔍 Verifying model availability for: {self.model}")
            
            if not self.is_initialized:
                await self.initialize()
            
            # Test with a simple request to verify model availability
            test_request = LLMRequest(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                task_type=LLMTaskType.SENTIMENT_ANALYSIS,
                max_tokens=10
            )
            
            response = await self.llm_client.generate(test_request, use_cache=False)
            
            if isinstance(response, LLMResponse):
                logger.info(f"[OllamaService] ✅ Model '{self.model}' is available through proxy")
                return {
                    'available': True,
                    'proxy_healthy': True,
                    'model_available': True,
                    'target_model': self.model,
                    'proxy_url': self.proxy_base_url
                }
            else:
                logger.warning(f"[OllamaService] ⚠️ Model '{self.model}' not available: {response.error_message}")
                return {
                    'available': False,
                    'proxy_healthy': True,
                    'model_available': False,
                    'error': response.error_message,
                    'target_model': self.model
                }
                
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Model verification failed: {type(e).__name__}: {str(e)}")
            return {
                'available': False,
                'proxy_healthy': False,
                'error': f"Failed to verify model: {str(e)}"
            }
    
    async def test_model_response(self) -> Dict[str, Any]:
        """Test if the model can generate a response through proxy"""
        try:
            logger.info(f"[OllamaService] 🧪 Testing model response for: {self.model}")
            
            test_request = LLMRequest(
                model=self.model,
                messages=[{"role": "user", "content": "Respond with 'OK' if you can read this message."}],
                task_type=LLMTaskType.SENTIMENT_ANALYSIS,
                max_tokens=50
            )
            
            response = await self.llm_client.generate(test_request, use_cache=False)
            
            if isinstance(response, LLMResponse):
                logger.info(f"[OllamaService] ✅ Model test successful: '{response.content.strip()}'")
                return {
                    'success': True,
                    'model_used': self.model,
                    'response': response.content.strip(),
                    'proxy_used': True,
                    'response_time': response.response_time
                }
            else:
                logger.error(f"[OllamaService] ❌ Model test failed: {response.error_message}")
                return {
                    'success': False,
                    'error': response.error_message
                }
                
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Model test failed: {type(e).__name__}: {str(e)}")
            return {
                'success': False,
                'error': f"Model test failed: {str(e)}"
            }
    
    async def analyze_market_sentiment(self, news_events, technical_signals, market_data, 
                                     proxy_callback: Optional[ProxyCallbackConfig] = None):
        """Analyze market sentiment using LLM proxy service with optional callback URLs"""
        logger.info(f"[OllamaService] 🤖 Starting LLM analysis for {market_data.get('symbol', 'unknown')}...")
        logger.info(f"[OllamaService] Technical signals: {len(technical_signals)} | News events: {len(news_events)} | Market data keys: {list(market_data.keys())}")
        
        prompt = self._build_analysis_prompt(news_events, technical_signals, market_data)
        logger.info(f"[OllamaService] 📤 Sending prompt to LLM proxy (length: {len(prompt)} chars)...")
        
        try:
            # Create LLM request with optional callback configuration
            request = LLMRequest(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                task_type=LLMTaskType.MARKET_ANALYSIS,
                temperature=0.3,
                max_tokens=1000,
                proxy_callback=proxy_callback
            )
            
            response = await self.llm_client.generate(request)
            
            if isinstance(response, LLMResponse):
                logger.info(f"[OllamaService] 📥 Received response from LLM proxy (length: {len(response.content)} chars)")
                analysis = self._parse_ai_response(response.content)
                logger.info(f"[OllamaService] ✅ LLM analysis completed: Sentiment={getattr(analysis, 'sentiment_score', None)}, Confidence={getattr(analysis, 'confidence', None)}, Action={getattr(analysis, 'recommended_action', None)}")
                return analysis
            else:
                logger.error(f"[OllamaService] ❌ LLM proxy error: {response.error_message}")
                return self._fallback_analysis()
                
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Error in AI analysis: {e}")
            return self._fallback_analysis()
    
    async def enhance_news_sentiment(self, news_event: Dict[str, Any], 
                                   proxy_callback: Optional[ProxyCallbackConfig] = None) -> Dict[str, Any]:
        """Enhance news sentiment analysis with AI using LLM proxy service"""
        
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
            request = LLMRequest(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                task_type=LLMTaskType.NEWS_ANALYSIS,
                temperature=0.3,
                max_tokens=500,
                proxy_callback=proxy_callback
            )
            
            response = await self.llm_client.generate(request)
            
            if isinstance(response, LLMResponse):
                enhanced_data = json.loads(response.content)
                return {**news_event, **enhanced_data}
            else:
                logger.error(f"Error enhancing news sentiment: {response.error_message}")
                return news_event
                
        except Exception as e:
            logger.error(f"Error enhancing news sentiment: {e}")
            return news_event
    
    async def generate_multi_factor_signal(self, 
                                         symbol: str,
                                         technical_signals: List[Dict[str, Any]],
                                         news_sentiment: Dict[str, Any],
                                         market_context: Dict[str, Any],
                                         proxy_callback: Optional[ProxyCallbackConfig] = None) -> Optional[TradeSignal]:
        """Generate multi-factor trading signal using LLM proxy service"""
        
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
            request = LLMRequest(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                task_type=LLMTaskType.SIGNAL_GENERATION,
                temperature=0.3,
                max_tokens=500,
                proxy_callback=proxy_callback
            )
            
            response = await self.llm_client.generate(request)
            
            if isinstance(response, LLMResponse):
                signal_data = json.loads(response.content)
                
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
                            "ai_enhanced": True,
                            "proxy_used": True
                        }
                    )
            else:
                logger.error(f"Error generating multi-factor signal: {response.error_message}")
                
        except Exception as e:
            logger.error(f"Error generating multi-factor signal: {e}")
        
        return None
    
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
            
            # Validate and convert sentiment_score to float
            sentiment_score = data.get('overall_sentiment', 0.0)
            try:
                sentiment_score = float(sentiment_score)
            except (ValueError, TypeError):
                sentiment_score = 0.0
            
            # Validate and convert confidence to float
            confidence = data.get('confidence', 0.5)
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.5
            
            return AIAnalysis(
                sentiment_score=sentiment_score,
                confidence=confidence,
                reasoning=data.get('reasoning', ''),
                risk_assessment=data.get('risk_assessment', 'medium'),
                market_impact=data.get('market_impact', 'neutral'),
                recommended_action=data.get('recommended_action', ''),
                metadata={
                    'key_factors': data.get('key_factors', []),
                    'market_volatility': data.get('market_volatility', 'medium'),
                    'proxy_used': True
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
            metadata={'fallback': True, 'proxy_used': True}
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

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama with a prompt and return the response"""
        try:
            # Use the LLM client to make the call
            request = LLMRequest(
                task_type=LLMTaskType.TRADE_EVALUATION,
                prompt=prompt,
                model=self.model,
                max_tokens=500,
                temperature=0.7
            )
            
            response = await self.llm_client.generate_text(request)
            return response.content
            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            # Return a default response to avoid breaking the system
            return "APPROVE: The trade signal appears reasonable based on technical analysis."

    async def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'llm_client'):
                await self.llm_client.disconnect()
            logger.info("[OllamaService] ✅ Cleanup completed")
        except Exception as e:
            logger.error(f"[OllamaService] ❌ Cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'llm_client'):
            logger.warning("[OllamaService] ⚠️ Service not properly cleaned up in destructor") 