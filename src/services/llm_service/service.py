"""
LLM Service for Trading Platform Integration
Integrates with remote LLM proxy service with native callback support
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .llm_client import LLMClient, LLMRequest, LLMResponse, LLMError, LLMTaskType, LLMModel, ProxyCallbackConfig
from ...utils.trading_config import get_trading_config

logger = logging.getLogger(__name__)


class SentimentAnalysisRequest(BaseModel):
    """Sentiment analysis request"""
    text: str = Field(..., description="Text to analyze")
    context: str = Field("", description="Additional context")
    model: str = Field("gpt-3.5-turbo", description="LLM model to use")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")


class TradingSignalRequest(BaseModel):
    """Trading signal generation request"""
    symbol: str = Field(..., description="Trading symbol")
    market_data: Dict[str, Any] = Field(..., description="Market data")
    news_data: List[Dict[str, Any]] = Field([], description="News data")
    technical_indicators: Dict[str, Any] = Field({}, description="Technical indicators")
    model: str = Field("gpt-4", description="LLM model to use")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")


class RiskAssessmentRequest(BaseModel):
    """Risk assessment request"""
    portfolio_data: Dict[str, Any] = Field(..., description="Portfolio data")
    market_conditions: Dict[str, Any] = Field(..., description="Market conditions")
    model: str = Field("gpt-4", description="LLM model to use")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")


class MarketAnalysisRequest(BaseModel):
    """Market analysis request"""
    market_data: Dict[str, Any] = Field(..., description="Market data")
    timeframe: str = Field("1d", description="Analysis timeframe")
    model: str = Field("gpt-4", description="LLM model to use")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")


class CustomLLMRequest(BaseModel):
    """Custom LLM request"""
    model: str = Field(..., description="LLM model to use")
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    task_type: str = Field(..., description="Task type")
    temperature: float = Field(0.7, description="Temperature")
    max_tokens: int = Field(1000, description="Max tokens")
    use_cache: bool = Field(True, description="Use caching")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")
    priority: int = Field(1, description="Request priority (1-5)")


class CentralizedLLMRequest(BaseModel):
    """Centralized LLM request for all operations"""
    operation: str = Field(..., description="Operation type: sentiment, signal, risk, market, custom")
    data: Dict[str, Any] = Field(..., description="Operation-specific data")
    model: str = Field("gpt-4", description="LLM model to use")
    proxy_callback: Optional[Dict[str, Any]] = Field(None, description="Proxy callback configuration")
    priority: int = Field(1, description="Request priority (1-5)")
    use_cache: bool = Field(True, description="Use caching")


class ProxyCallbackConfigRequest(BaseModel):
    """Proxy callback configuration request"""
    success_url: Optional[str] = Field(None, description="URL for successful completion callback")
    timeout_url: Optional[str] = Field(None, description="URL for timeout callback")
    timeout_seconds: int = Field(30, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata")


class LLMServiceResponse(BaseModel):
    """LLM service response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: str
    response_time: float
    timestamp: datetime
    callback_urls_configured: bool = False


class LLMService:
    """LLM service for trading platform integration with proxy callback support"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or get_trading_config()
        
        # LLM client configuration
        self.llm_config = self.config.get('llm_service', {})
        self.base_url = self.llm_config.get('base_url', 'http://localhost:8081')
        self.api_key = self.llm_config.get('api_key')
        self.timeout = self.llm_config.get('timeout', 30)
        self.max_retries = self.llm_config.get('max_retries', 3)
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        # Service state
        self.is_initialized = False
        self.health_check_task = None
        
        # Request tracking
        self.request_history = []
        self.max_history = 1000
        
        # Centralized API operations mapping
        self.operations = {
            'sentiment': self._handle_sentiment_operation,
            'signal': self._handle_signal_operation,
            'risk': self._handle_risk_operation,
            'market': self._handle_market_operation,
            'custom': self._handle_custom_operation
        }
        
        logger.info(f"LLM Service initialized for proxy at {self.base_url}")
    
    async def initialize(self):
        """Initialize the LLM service"""
        try:
            # Test connection to LLM proxy service
            is_healthy = await self.llm_client.health_check()
            if not is_healthy:
                logger.warning("LLM proxy service is not healthy during initialization")
            
            self.is_initialized = True
            logger.info("LLM Service initialized successfully")
            
            # Start health check background task
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the LLM service"""
        try:
            if self.health_check_task:
                self.health_check_task.cancel()
            
            await self.llm_client.disconnect()
            self.is_initialized = False
            logger.info("LLM Service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during LLM service shutdown: {e}")
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.llm_client.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def _parse_proxy_callback_config(self, callback_data: Optional[Dict[str, Any]]) -> Optional[ProxyCallbackConfig]:
        """Parse proxy callback configuration from request data"""
        if not callback_data:
            return None
        
        try:
            return ProxyCallbackConfig(
                success_url=callback_data.get('success_url'),
                timeout_url=callback_data.get('timeout_url'),
                timeout_seconds=callback_data.get('timeout_seconds', 30),
                metadata=callback_data.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error parsing proxy callback config: {e}")
            return None
    
    async def _add_to_history(self, request_id: str, request_data: Dict[str, Any], response: Union[LLMResponse, LLMError]):
        """Add request to history"""
        history_entry = {
            'request_id': request_id,
            'timestamp': datetime.utcnow(),
            'request': request_data,
            'response': {
                'success': isinstance(response, LLMResponse),
                'content': response.content if isinstance(response, LLMResponse) else response.error_message,
                'response_time': response.response_time if isinstance(response, LLMResponse) else 0,
                'callback_urls_configured': response.callback_urls_configured if hasattr(response, 'callback_urls_configured') else False
            }
        }
        
        self.request_history.append(history_entry)
        
        # Trim history if too long
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history:]
    
    async def centralized_request(self, request: CentralizedLLMRequest) -> LLMServiceResponse:
        """Handle centralized LLM request"""
        start_time = datetime.utcnow()
        
        try:
            # Get operation handler
            operation_handler = self.operations.get(request.operation.lower())
            if not operation_handler:
                return LLMServiceResponse(
                    success=False,
                    error=f"Unknown operation: {request.operation}",
                    request_id="",
                    response_time=(datetime.utcnow() - start_time).total_seconds(),
                    timestamp=datetime.utcnow()
                )
            
            # Execute operation
            result = await operation_handler(request.data, request.model, request.proxy_callback, request.priority, request.use_cache)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'operation': request.operation, 'data': request.data},
                result
            )
            
            return LLMServiceResponse(
                success=isinstance(result, LLMResponse),
                data=result.content if isinstance(result, LLMResponse) else None,
                error=result.error_message if isinstance(result, LLMError) else None,
                request_id=result.request_id,
                response_time=response_time,
                timestamp=result.timestamp,
                callback_urls_configured=result.callback_urls_configured if hasattr(result, 'callback_urls_configured') else False
            )
            
        except Exception as e:
            logger.error(f"Centralized request error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def _handle_sentiment_operation(self, data: Dict[str, Any], model: str, proxy_callback: Optional[Dict[str, Any]], priority: int, use_cache: bool) -> Union[LLMResponse, LLMError]:
        """Handle sentiment analysis operation"""
        text = data.get('text', '')
        context = data.get('context', '')
        
        callback = self._parse_proxy_callback_config(proxy_callback)
        
        request = LLMRequest(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial sentiment analysis expert."},
                {"role": "user", "content": f"Analyze sentiment: {text}"}
            ],
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            temperature=0.3,
            max_tokens=500,
            metadata={'text_length': len(text), 'context': context},
            proxy_callback=callback,
            priority=priority
        )
        
        return await self.llm_client.generate(request, use_cache=use_cache)
    
    async def _handle_signal_operation(self, data: Dict[str, Any], model: str, proxy_callback: Optional[Dict[str, Any]], priority: int, use_cache: bool) -> Union[LLMResponse, LLMError]:
        """Handle trading signal operation"""
        symbol = data.get('symbol', '')
        market_data = data.get('market_data', {})
        news_data = data.get('news_data', [])
        technical_indicators = data.get('technical_indicators', {})
        
        callback = self._parse_proxy_callback_config(proxy_callback)
        
        request = LLMRequest(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert trading analyst."},
                {"role": "user", "content": f"Generate trading signal for {symbol} based on market data, news, and technical indicators."}
            ],
            task_type=LLMTaskType.SIGNAL_GENERATION,
            temperature=0.2,
            max_tokens=800,
            metadata={
                'symbol': symbol,
                'data_sources': ['market_data', 'news', 'technical']
            },
            proxy_callback=callback,
            priority=priority
        )
        
        return await self.llm_client.generate(request, use_cache=use_cache)
    
    async def _handle_risk_operation(self, data: Dict[str, Any], model: str, proxy_callback: Optional[Dict[str, Any]], priority: int, use_cache: bool) -> Union[LLMResponse, LLMError]:
        """Handle risk assessment operation"""
        portfolio_data = data.get('portfolio_data', {})
        market_conditions = data.get('market_conditions', {})
        
        callback = self._parse_proxy_callback_config(proxy_callback)
        
        request = LLMRequest(
            model=model,
            messages=[
                {"role": "system", "content": "You are a risk management expert."},
                {"role": "user", "content": f"Assess portfolio risk based on portfolio data and market conditions."}
            ],
            task_type=LLMTaskType.RISK_ASSESSMENT,
            temperature=0.1,
            max_tokens=1000,
            metadata={'portfolio_size': len(portfolio_data.get('positions', []))},
            proxy_callback=callback,
            priority=priority
        )
        
        return await self.llm_client.generate(request, use_cache=use_cache)
    
    async def _handle_market_operation(self, data: Dict[str, Any], model: str, proxy_callback: Optional[Dict[str, Any]], priority: int, use_cache: bool) -> Union[LLMResponse, LLMError]:
        """Handle market analysis operation"""
        market_data = data.get('market_data', {})
        timeframe = data.get('timeframe', '1d')
        
        callback = self._parse_proxy_callback_config(proxy_callback)
        
        request = LLMRequest(
            model=model,
            messages=[
                {"role": "system", "content": "You are a market analysis expert."},
                {"role": "user", "content": f"Analyze market conditions for timeframe: {timeframe}"}
            ],
            task_type=LLMTaskType.MARKET_ANALYSIS,
            temperature=0.3,
            max_tokens=800,
            metadata={'timeframe': timeframe},
            proxy_callback=callback,
            priority=priority
        )
        
        return await self.llm_client.generate(request, use_cache=use_cache)
    
    async def _handle_custom_operation(self, data: Dict[str, Any], model: str, proxy_callback: Optional[Dict[str, Any]], priority: int, use_cache: bool) -> Union[LLMResponse, LLMError]:
        """Handle custom LLM operation"""
        messages = data.get('messages', [])
        task_type = data.get('task_type', 'custom')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        callback = self._parse_proxy_callback_config(proxy_callback)
        
        request = LLMRequest(
            model=model,
            messages=messages,
            task_type=LLMTaskType(task_type),
            temperature=temperature,
            max_tokens=max_tokens,
            metadata={'custom_request': True},
            proxy_callback=callback,
            priority=priority
        )
        
        return await self.llm_client.generate(request, use_cache=use_cache)
    
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> LLMServiceResponse:
        """Analyze sentiment of text"""
        start_time = datetime.utcnow()
        
        try:
            callback = self._parse_proxy_callback_config(request.proxy_callback)
            
            response = await self.llm_client.analyze_sentiment(
                text=request.text,
                context=request.context,
                proxy_callback=callback
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(response, LLMResponse):
                result = LLMServiceResponse(
                    success=True,
                    data={'sentiment_analysis': response.content, 'model': response.model, 'usage': response.usage},
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            else:
                result = LLMServiceResponse(
                    success=False,
                    error=response.error_message,
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'type': 'sentiment_analysis', 'text_length': len(request.text)},
                response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def generate_trading_signal(self, request: TradingSignalRequest) -> LLMServiceResponse:
        """Generate trading signal"""
        start_time = datetime.utcnow()
        
        try:
            callback = self._parse_proxy_callback_config(request.proxy_callback)
            
            response = await self.llm_client.generate_trading_signal(
                market_data=request.market_data,
                news_data=request.news_data,
                technical_indicators=request.technical_indicators,
                proxy_callback=callback
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(response, LLMResponse):
                result = LLMServiceResponse(
                    success=True,
                    data={'trading_signal': response.content, 'model': response.model, 'usage': response.usage},
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            else:
                result = LLMServiceResponse(
                    success=False,
                    error=response.error_message,
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'type': 'trading_signal', 'symbol': request.symbol},
                response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Trading signal generation error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def assess_risk(self, request: RiskAssessmentRequest) -> LLMServiceResponse:
        """Assess portfolio risk"""
        start_time = datetime.utcnow()
        
        try:
            callback = self._parse_proxy_callback_config(request.proxy_callback)
            
            response = await self.llm_client.assess_risk(
                portfolio_data=request.portfolio_data,
                market_conditions=request.market_conditions,
                proxy_callback=callback
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(response, LLMResponse):
                result = LLMServiceResponse(
                    success=True,
                    data={'risk_assessment': response.content, 'model': response.model, 'usage': response.usage},
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            else:
                result = LLMServiceResponse(
                    success=False,
                    error=response.error_message,
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'type': 'risk_assessment', 'portfolio_size': len(request.portfolio_data.get('positions', []))},
                response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def analyze_market(self, request: MarketAnalysisRequest) -> LLMServiceResponse:
        """Analyze market conditions"""
        start_time = datetime.utcnow()
        
        try:
            callback = self._parse_proxy_callback_config(request.proxy_callback)
            
            response = await self.llm_client.analyze_market(
                market_data=request.market_data,
                timeframe=request.timeframe,
                proxy_callback=callback
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(response, LLMResponse):
                result = LLMServiceResponse(
                    success=True,
                    data={'market_analysis': response.content, 'model': response.model, 'usage': response.usage},
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            else:
                result = LLMServiceResponse(
                    success=False,
                    error=response.error_message,
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'type': 'market_analysis', 'timeframe': request.timeframe},
                response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def custom_request(self, request: CustomLLMRequest) -> LLMServiceResponse:
        """Handle custom LLM request"""
        start_time = datetime.utcnow()
        
        try:
            callback = self._parse_proxy_callback_config(request.proxy_callback)
            
            llm_request = LLMRequest(
                model=request.model,
                messages=request.messages,
                task_type=LLMTaskType(request.task_type),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                metadata={'custom_request': True},
                proxy_callback=callback,
                priority=request.priority
            )
            
            response = await self.llm_client.generate(llm_request, use_cache=request.use_cache)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(response, LLMResponse):
                result = LLMServiceResponse(
                    success=True,
                    data={
                        'content': response.content,
                        'model': response.model,
                        'usage': response.usage,
                        'finish_reason': response.finish_reason
                    },
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            else:
                result = LLMServiceResponse(
                    success=False,
                    error=response.error_message,
                    request_id=response.request_id,
                    response_time=response_time,
                    timestamp=response.timestamp,
                    callback_urls_configured=response.callback_urls_configured
                )
            
            # Add to history
            await self._add_to_history(
                result.request_id,
                {'type': 'custom_request', 'task_type': request.task_type},
                response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Custom request error: {e}")
            return LLMServiceResponse(
                success=False,
                error=str(e),
                request_id="",
                response_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    async def get_health(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            is_healthy = await self.llm_client.health_check()
            metrics = await self.llm_client.get_metrics()
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'llm_proxy_healthy': is_healthy,
                'base_url': self.llm_client.base_url,
                'metrics': metrics,
                'request_history_size': len(self.request_history),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        try:
            llm_metrics = await self.llm_client.get_metrics()
            
            return {
                'llm_metrics': llm_metrics,
                'service_metrics': {
                    'total_requests': len(self.request_history),
                    'successful_requests': len([r for r in self.request_history if r['response']['success']]),
                    'failed_requests': len([r for r in self.request_history if not r['response']['success']]),
                    'average_response_time': sum(r['response']['response_time'] for r in self.request_history) / len(self.request_history) if self.request_history else 0,
                    'callback_requests': len([r for r in self.request_history if r['response'].get('callback_urls_configured', False)])
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_request_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get request history"""
        return self.request_history[-limit:] if limit > 0 else self.request_history
    
    async def clear_history(self):
        """Clear request history"""
        self.request_history.clear()
        logger.info("Request history cleared")


# FastAPI application
app = FastAPI(
    title="LLM Service",
    description="LLM service for trading platform integration with proxy callback support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
llm_service = None


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    global llm_service
    llm_service = LLMService()
    await llm_service.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    global llm_service
    if llm_service:
        await llm_service.shutdown()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_data = await llm_service.get_health()
    return health_data


@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    metrics = await llm_service.get_metrics()
    return metrics


@app.post("/api/v1/llm")
async def centralized_llm_api(request: CentralizedLLMRequest):
    """Centralized LLM API endpoint"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.centralized_request(request)
    return result


@app.post("/sentiment")
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment of text"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.analyze_sentiment(request)
    return result


@app.post("/signal")
async def generate_trading_signal(request: TradingSignalRequest):
    """Generate trading signal"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.generate_trading_signal(request)
    return result


@app.post("/risk")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess portfolio risk"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.assess_risk(request)
    return result


@app.post("/market")
async def analyze_market(request: MarketAnalysisRequest):
    """Analyze market conditions"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.analyze_market(request)
    return result


@app.post("/custom")
async def custom_request(request: CustomLLMRequest):
    """Handle custom LLM request"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await llm_service.custom_request(request)
    return result


@app.get("/history")
async def get_history(limit: int = 100):
    """Get request history"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    history = await llm_service.get_request_history(limit)
    return {"history": history, "count": len(history)}


@app.delete("/history")
async def clear_history():
    """Clear request history"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    await llm_service.clear_history()
    return {"message": "History cleared"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008) 