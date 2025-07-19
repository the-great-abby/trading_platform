"""
LLM Client Service for Remote LLM Proxy Integration
Connects to remotely hosted LLM proxy service with native callback support
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib
import uuid

logger = logging.getLogger(__name__)


class LLMModel(Enum):
    """Available LLM models"""
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE = "claude-3"
    MISTRAL = "mistral"
    LLAMA2 = "llama2"
    CODELLAMA = "codellama"
    CUSTOM = "custom"


class LLMTaskType(Enum):
    """LLM task types"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SIGNAL_GENERATION = "signal_generation"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    NEWS_ANALYSIS = "news_analysis"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    TRADE_EVALUATION = "trade_evaluation"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    ALERT_GENERATION = "alert_generation"


@dataclass
class ProxyCallbackConfig:
    """Proxy callback configuration using native proxy callback URLs"""
    success_url: Optional[str] = None
    timeout_url: Optional[str] = None
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """LLM request structure with proxy callback support"""
    model: str
    messages: List[Dict[str, str]]
    task_type: LLMTaskType
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = None
    proxy_callback: Optional[ProxyCallbackConfig] = None
    priority: int = 1  # 1=low, 5=high
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())


@dataclass
class LLMResponse:
    """LLM response structure"""
    request_id: str
    model: str
    content: str
    task_type: LLMTaskType
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback_urls_configured: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class LLMError:
    """LLM error structure"""
    request_id: str
    error_type: str
    error_message: str
    status_code: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback_urls_configured: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class LLMClient:
    """LLM client for remote LLM proxy service integration with native callback support"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8081",
                 api_key: str = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_check_interval = 60  # seconds
        self.last_health_check = 0
        self.is_healthy = False
        
        # Rate limiting
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.request_timestamps = []
        
        # Caching
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'callback_requests': 0,
            'timeout_requests': 0
        }
        
        logger.info(f"LLM Client initialized for proxy at {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to LLM proxy service"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'TradingPlatform-LLM-Client/1.0'
                }
            )
            logger.info("LLM Client session established")
    
    async def disconnect(self):
        """Close connection to LLM proxy service"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("LLM Client session closed")
    
    async def health_check(self) -> bool:
        """Check if LLM proxy service is healthy"""
        current_time = time.time()
        
        # Cache health check result for 60 seconds
        if current_time - self.last_health_check < self.health_check_interval:
            return self.is_healthy
        
        try:
            await self.connect()
            
            # Check proxy root endpoint
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    self.is_healthy = True
                    logger.debug("LLM proxy health check passed")
                else:
                    self.is_healthy = False
                    logger.warning(f"LLM proxy health check failed: {response.status}")
            
            # Check OpenAPI spec if available
            try:
                async with self.session.get(f"{self.base_url}/openapi.json") as response:
                    if response.status == 200:
                        openapi_data = await response.json()
                        logger.debug(f"LLM proxy OpenAPI spec available: {openapi_data.get('info', {}).get('title', 'Unknown')}")
            except Exception as e:
                logger.debug(f"OpenAPI spec not available: {e}")
            
            self.last_health_check = current_time
            return self.is_healthy
            
        except Exception as e:
            self.is_healthy = False
            logger.error(f"LLM proxy health check error: {e}")
            return False
    
    async def _rate_limit_check(self) -> bool:
        """Check rate limiting"""
        current_time = time.time()
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check if we're under the limit
        if len(self.request_timestamps) >= self.rate_limit_requests:
            return False
        
        self.request_timestamps.append(current_time)
        return True
    
    async def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
        cache_data = {
            'model': request.model,
            'messages': request.messages,
            'task_type': request.task_type.value,
            'temperature': request.temperature,
            'max_tokens': request.max_tokens
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Get cached response if available"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.utcnow() - cached_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                self.metrics['cache_hits'] += 1
                return cached_data['response']
        
        self.metrics['cache_misses'] += 1
        return None
    
    async def _cache_response(self, cache_key: str, response: LLMResponse):
        """Cache response"""
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.utcnow()
        }
    
    async def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time - data['timestamp'] > timedelta(seconds=self.cache_ttl)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    async def generate(self, request: LLMRequest, use_cache: bool = True) -> Union[LLMResponse, LLMError]:
        """Generate response from LLM proxy with native callback support"""
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            # Health check
            if not await self.health_check():
                return LLMError(
                    request_id=request.request_id,
                    error_type="service_unavailable",
                    error_message="LLM proxy service is not available",
                    status_code=503,
                    timestamp=datetime.utcnow(),
                    metadata={'base_url': self.base_url}
                )
            
            # Rate limiting check
            if not await self._rate_limit_check():
                return LLMError(
                    request_id=request.request_id,
                    error_type="rate_limit_exceeded",
                    error_message="Rate limit exceeded",
                    status_code=429,
                    timestamp=datetime.utcnow(),
                    metadata={'rate_limit': self.rate_limit_requests}
                )
            
            # Cache check
            if use_cache:
                cache_key = await self._get_cache_key(request)
                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    logger.debug(f"Cache hit for request {request.request_id}")
                    return cached_response
            
            # Prepare request payload for proxy
            payload = {
                'model': request.model,
                'messages': request.messages,
                'temperature': request.temperature,
                'max_tokens': request.max_tokens,
                'top_p': request.top_p,
                'frequency_penalty': request.frequency_penalty,
                'presence_penalty': request.presence_penalty,
                'stream': request.stream,
                'metadata': {
                    **request.metadata,
                    'task_type': request.task_type.value,
                    'request_id': request.request_id,
                    'priority': request.priority
                }
            }
            
            # Add proxy callback URL if configured
            if request.proxy_callback:
                if request.proxy_callback.success_url:
                    payload['callback_url'] = request.proxy_callback.success_url
                    self.metrics['callback_requests'] += 1
                
                if request.proxy_callback.timeout_seconds:
                    payload['timeout_seconds'] = request.proxy_callback.timeout_seconds
                
                # Add callback metadata as headers
                if request.proxy_callback.metadata:
                    payload['callback_headers'] = request.proxy_callback.metadata
            
            # Add API key if provided
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    await self.connect()
                    
                    # Use the working proxy endpoint
                    endpoint = f"{self.base_url}/api/generate"
                    
                    # Convert chat format to generate format
                    if len(request.messages) > 0:
                        # Use the last user message as prompt
                        prompt = ""
                        for msg in request.messages:
                            if msg.get('role') == 'user':
                                prompt += msg.get('content', '') + "\n"
                        
                        generate_payload = {
                            'model': request.model,
                            'prompt': prompt.strip(),
                            'options': {
                                'temperature': request.temperature,
                                'num_predict': request.max_tokens,
                                'top_p': request.top_p,
                                'frequency_penalty': request.frequency_penalty,
                                'presence_penalty': request.presence_penalty
                            }
                        }
                        
                        # Add proxy callback URL if configured
                        if request.proxy_callback and request.proxy_callback.success_url:
                            generate_payload['callback_url'] = request.proxy_callback.success_url
                            self.metrics['callback_requests'] += 1
                        
                        if request.proxy_callback and request.proxy_callback.timeout_seconds:
                            generate_payload['timeout_seconds'] = request.proxy_callback.timeout_seconds
                        
                        # Add callback metadata as headers
                        if request.proxy_callback and request.proxy_callback.metadata:
                            # Convert all metadata values to strings for callback_headers
                            callback_headers = {}
                            for key, value in request.proxy_callback.metadata.items():
                                callback_headers[str(key)] = str(value)
                            generate_payload['callback_headers'] = callback_headers
                        
                        # Add priority
                        if request.priority > 1:
                            generate_payload['priority'] = 'high' if request.priority >= 4 else 'medium'
                    else:
                        generate_payload = payload
                    
                    async with self.session.post(
                        endpoint,
                        json=generate_payload,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # Handle async response from proxy
                            if 'request_id' in data:
                                # This is an async response - return immediately with request ID
                                llm_response = LLMResponse(
                                    request_id=data['request_id'],
                                    model=request.model,
                                    content=f"Request queued: {data['request_id']}",
                                    task_type=request.task_type,
                                    usage={},
                                    finish_reason='async_queued',
                                    response_time=time.time() - start_time,
                                    timestamp=datetime.utcnow(),
                                    metadata={
                                        **request.metadata,
                                        'async_request': True,
                                        'proxy_request_id': data['request_id'],
                                        'status_url': data.get('status_url'),
                                        'queue_position': data.get('queue_position'),
                                        'estimated_completion': data.get('estimated_completion'),
                                        'proxy_endpoint': endpoint
                                    },
                                    callback_urls_configured=bool(request.proxy_callback and request.proxy_callback.success_url)
                                )
                            else:
                                # This is a direct response (shouldn't happen with this proxy)
                                llm_response = LLMResponse(
                                    request_id=request.request_id,
                                    model=request.model,
                                    content=data.get('response', 'No response'),
                                    task_type=request.task_type,
                                    usage=data.get('usage', {}),
                                    finish_reason=data.get('finish_reason', 'stop'),
                                    response_time=time.time() - start_time,
                                    timestamp=datetime.utcnow(),
                                    metadata={
                                        **request.metadata,
                                        'response_metadata': data.get('metadata', {}),
                                        'proxy_endpoint': endpoint
                                    },
                                    callback_urls_configured=bool(request.proxy_callback and request.proxy_callback.success_url)
                                )
                            
                            # Cache response
                            if use_cache:
                                cache_key = await self._get_cache_key(request)
                                await self._cache_response(cache_key, llm_response)
                            
                            # Update metrics
                            self.metrics['successful_requests'] += 1
                            self.metrics['average_response_time'] = (
                                (self.metrics['average_response_time'] * (self.metrics['successful_requests'] - 1) + 
                                 llm_response.response_time) / self.metrics['successful_requests']
                            )
                            
                            logger.info(f"LLM request {request.request_id} completed in {llm_response.response_time:.2f}s")
                            if llm_response.callback_urls_configured:
                                logger.info(f"Callback URLs configured for request {request.request_id}")
                            
                            return llm_response
                            
                        else:
                            error_data = await response.text()
                            logger.error(f"LLM request failed: {response.status} - {error_data}")
                            
                            if response.status == 429:  # Rate limit
                                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                continue
                            elif response.status >= 500:  # Server error
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                    continue
                            
                            return LLMError(
                                request_id=request.request_id,
                                error_type="http_error",
                                error_message=f"HTTP {response.status}: {error_data}",
                                status_code=response.status,
                                timestamp=datetime.utcnow(),
                                metadata={'attempt': attempt + 1},
                                callback_urls_configured=bool(request.proxy_callback and (request.proxy_callback.success_url or request.proxy_callback.timeout_url))
                            )
                
                except asyncio.TimeoutError:
                    logger.warning(f"LLM request timeout on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return LLMError(
                            request_id=request.request_id,
                            error_type="timeout",
                            error_message="Request timeout",
                            status_code=408,
                            timestamp=datetime.utcnow(),
                            metadata={'attempts': attempt + 1},
                            callback_urls_configured=bool(request.proxy_callback and (request.proxy_callback.success_url or request.proxy_callback.timeout_url))
                        )
                
                except Exception as e:
                    logger.error(f"LLM request error on attempt {attempt + 1}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return LLMError(
                            request_id=request.request_id,
                            error_type="connection_error",
                            error_message=str(e),
                            status_code=0,
                            timestamp=datetime.utcnow(),
                            metadata={'attempts': attempt + 1},
                            callback_urls_configured=bool(request.proxy_callback and (request.proxy_callback.success_url or request.proxy_callback.timeout_url))
                        )
            
            return LLMError(
                request_id=request.request_id,
                error_type="max_retries_exceeded",
                error_message="Maximum retries exceeded",
                status_code=0,
                timestamp=datetime.utcnow(),
                metadata={'max_retries': self.max_retries},
                callback_urls_configured=bool(request.proxy_callback and (request.proxy_callback.success_url or request.proxy_callback.timeout_url))
            )
        
        except Exception as e:
            self.metrics['failed_requests'] += 1
            logger.error(f"Unexpected error in LLM request: {e}")
            return LLMError(
                request_id=request.request_id,
                error_type="unexpected_error",
                error_message=str(e),
                status_code=0,
                timestamp=datetime.utcnow(),
                metadata={'error_type': type(e).__name__},
                callback_urls_configured=bool(request.proxy_callback and (request.proxy_callback.success_url or request.proxy_callback.timeout_url))
            )
    
    async def analyze_sentiment(self, text: str, context: str = "", proxy_callback: Optional[ProxyCallbackConfig] = None) -> Union[LLMResponse, LLMError]:
        """Analyze sentiment of text with proxy callback support"""
        messages = [
            {"role": "system", "content": "You are a financial sentiment analysis expert. Analyze the sentiment of the given text and provide a structured response with sentiment score (-1 to 1), confidence level, and key insights."},
            {"role": "user", "content": f"Context: {context}\n\nText to analyze: {text}"}
        ]
        
        request = LLMRequest(
            model=LLMModel.GPT35.value,
            messages=messages,
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            temperature=0.3,
            max_tokens=500,
            metadata={'text_length': len(text), 'context': context},
            proxy_callback=proxy_callback
        )
        
        return await self.generate(request)
    
    async def generate_trading_signal(self, 
                                    market_data: Dict[str, Any],
                                    news_data: List[Dict[str, Any]] = None,
                                    technical_indicators: Dict[str, Any] = None,
                                    proxy_callback: Optional[ProxyCallbackConfig] = None) -> Union[LLMResponse, LLMError]:
        """Generate trading signal based on market data with proxy callback support"""
        # Prepare market analysis
        market_summary = f"""
Symbol: {market_data.get('symbol', 'Unknown')}
Current Price: {market_data.get('price', 0)}
Volume: {market_data.get('volume', 0)}
24h Change: {market_data.get('change_24h', 0)}%
Market Cap: {market_data.get('market_cap', 0)}
        """
        
        # Add news context
        news_context = ""
        if news_data:
            news_context = "\nRecent News:\n" + "\n".join([
                f"- {news.get('title', '')}: {news.get('sentiment', 'neutral')}"
                for news in news_data[:5]
            ])
        
        # Add technical indicators
        technical_context = ""
        if technical_indicators:
            technical_context = "\nTechnical Indicators:\n" + "\n".join([
                f"- {indicator}: {value}"
                for indicator, value in technical_indicators.items()
            ])
        
        messages = [
            {"role": "system", "content": """You are an expert trading analyst. Based on the provided market data, news, and technical indicators, generate a trading signal with the following structure:
{
  "signal": "BUY|SELL|HOLD",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation",
  "risk_level": "LOW|MEDIUM|HIGH",
  "target_price": "Price target if applicable",
  "stop_loss": "Stop loss if applicable",
  "timeframe": "Short-term|Medium-term|Long-term"
}"""},
            {"role": "user", "content": f"Market Data:{market_summary}{news_context}{technical_context}"}
        ]
        
        request = LLMRequest(
            model=LLMModel.GPT4.value,
            messages=messages,
            task_type=LLMTaskType.SIGNAL_GENERATION,
            temperature=0.2,
            max_tokens=800,
            metadata={
                'symbol': market_data.get('symbol'),
                'data_sources': ['market_data', 'news', 'technical']
            },
            proxy_callback=proxy_callback
        )
        
        return await self.generate(request)
    
    async def assess_risk(self, 
                         portfolio_data: Dict[str, Any],
                         market_conditions: Dict[str, Any],
                         proxy_callback: Optional[ProxyCallbackConfig] = None) -> Union[LLMResponse, LLMError]:
        """Assess portfolio risk with proxy callback support"""
        portfolio_summary = f"""
Portfolio Value: {portfolio_data.get('total_value', 0)}
Number of Positions: {len(portfolio_data.get('positions', []))}
Largest Position: {portfolio_data.get('largest_position', {})}
Current Drawdown: {portfolio_data.get('drawdown', 0)}%
        """
        
        market_summary = f"""
Market Volatility: {market_conditions.get('volatility', 'Unknown')}
Market Trend: {market_conditions.get('trend', 'Unknown')}
Economic Indicators: {market_conditions.get('economic_indicators', [])}
        """
        
        messages = [
            {"role": "system", "content": """You are a risk management expert. Assess the portfolio risk based on the provided data and market conditions. Provide a structured risk assessment with:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_score": 0.0-1.0,
  "key_risks": ["List of main risks"],
  "recommendations": ["Risk mitigation actions"],
  "var_estimate": "Estimated Value at Risk",
  "stress_test_scenarios": ["Potential stress scenarios"]
}"""},
            {"role": "user", "content": f"Portfolio:{portfolio_summary}\nMarket Conditions:{market_summary}"}
        ]
        
        request = LLMRequest(
            model=LLMModel.GPT4.value,
            messages=messages,
            task_type=LLMTaskType.RISK_ASSESSMENT,
            temperature=0.1,
            max_tokens=1000,
            metadata={'portfolio_size': len(portfolio_data.get('positions', []))},
            proxy_callback=proxy_callback
        )
        
        return await self.generate(request)
    
    async def analyze_market(self, 
                           market_data: Dict[str, Any],
                           timeframe: str = "1d",
                           proxy_callback: Optional[ProxyCallbackConfig] = None) -> Union[LLMResponse, LLMError]:
        """Analyze market conditions with proxy callback support"""
        market_summary = f"""
Market: {market_data.get('market', 'Unknown')}
Timeframe: {timeframe}
Price Action: {market_data.get('price_action', {})}
Volume Analysis: {market_data.get('volume_analysis', {})}
Support/Resistance: {market_data.get('support_resistance', {})}
        """
        
        messages = [
            {"role": "system", "content": """You are a market analysis expert. Provide a comprehensive market analysis including:
{
  "market_trend": "BULLISH|BEARISH|SIDEWAYS",
  "trend_strength": "WEAK|MODERATE|STRONG",
  "key_levels": {"support": [], "resistance": []},
  "volume_analysis": "Volume interpretation",
  "momentum": "Momentum analysis",
  "outlook": "Short-term and medium-term outlook",
  "key_events": ["Important events to watch"]
}"""},
            {"role": "user", "content": f"Market Data:{market_summary}"}
        ]
        
        request = LLMRequest(
            model=LLMModel.GPT4.value,
            messages=messages,
            task_type=LLMTaskType.MARKET_ANALYSIS,
            temperature=0.3,
            max_tokens=800,
            metadata={'market': market_data.get('market'), 'timeframe': timeframe},
            proxy_callback=proxy_callback
        )
        
        return await self.generate(request)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get LLM client metrics"""
        await self._cleanup_cache()
        
        return {
            **self.metrics,
            'cache_size': len(self.cache),
            'is_healthy': self.is_healthy,
            'rate_limit_remaining': max(0, self.rate_limit_requests - len(self.request_timestamps)),
            'uptime': time.time() - self.last_health_check if self.last_health_check > 0 else 0
        }
    
    async def reset_metrics(self):
        """Reset metrics"""
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'callback_requests': 0,
            'timeout_requests': 0
        }
        logger.info("LLM client metrics reset") 