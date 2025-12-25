"""
OpenAI Provider Implementation
For completeness and future OpenAI integration
"""

import time
import asyncio
from typing import Dict, Any, List, AsyncIterator
import logging

from .base import (
    LLMProvider,
    LLMProviderType,
    LLMRequest,
    LLMResponse,
    LLMError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider implementation.
    Requires openai package: pip install openai
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.
        
        Config keys:
            - api_key: OpenAI API key (required)
            - model: Default model name (default: 'gpt-3.5-turbo')
            - organization: Optional organization ID
            - timeout: Request timeout in seconds (default: 60)
            - max_retries: Maximum retry attempts (default: 3)
        """
        super().__init__(config)
        
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("OpenAI provider requires 'api_key' in config")
        
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.organization = config.get('organization')
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)
        
        self.client = None
        
        logger.info(f"OpenAI provider configured with model {self.model}")
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI
    
    async def initialize(self) -> bool:
        """Initialize OpenAI provider"""
        try:
            # Import openai here to make it optional
            try:
                from openai import AsyncOpenAI
            except ImportError:
                logger.error("openai package not installed. Install with: pip install openai")
                return False
            
            # Initialize async client
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
            
            # Test connection
            is_healthy = await self.health_check()
            if not is_healthy:
                logger.warning("OpenAI API is not responsive")
                return False
            
            self.is_initialized = True
            logger.info(f"✅ OpenAI provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is healthy"""
        try:
            if not self.client:
                return False
            
            # Try to list models as health check
            await self.client.models.list()
            logger.info("OpenAI API health check passed")
            return True
                    
        except Exception as e:
            logger.warning(f"OpenAI API health check failed: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if request.system_message:
                messages.append({
                    "role": "system",
                    "content": request.system_message
                })
            
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=request.model or self.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                **request.provider_options
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response
            choice = response.choices[0]
            text = choice.message.content
            
            # Extract token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Update metrics
            self._update_metrics(True, total_tokens, latency_ms)
            
            return LLMResponse(
                text=text,
                model=response.model,
                provider=self.provider_type.value,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=choice.finish_reason,
                latency_ms=latency_ms,
                metadata={
                    'openai_id': response.id,
                    'created': response.created,
                    **request.metadata
                }
            )
            
        except Exception as e:
            self._update_metrics(False)
            logger.error(f"OpenAI generation error: {e}")
            raise LLMError(
                error_type="generation_failed",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Generate streaming response using OpenAI"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            messages = []
            if request.system_message:
                messages.append({
                    "role": "system",
                    "content": request.system_message
                })
            
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            stream = await self.client.chat.completions.create(
                model=request.model or self.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise LLMError(
                error_type="streaming_error",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def list_models(self) -> List[str]:
        """List available OpenAI models"""
        try:
            if not self.client:
                return []
            
            models = await self.client.models.list()
            return [model.id for model in models.data]
                    
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {e}")
            return []
    
    async def verify_model(self, model: str) -> bool:
        """Verify if a model is available"""
        try:
            if not self.client:
                return False
            
            await self.client.models.retrieve(model)
            return True
        except:
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()
            self.client = None
        self.is_initialized = False
        logger.info("OpenAI provider cleaned up")








