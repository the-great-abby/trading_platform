"""
LM Studio Provider Implementation
LM Studio provides an OpenAI-compatible API
"""

import aiohttp
import time
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


class LMStudioProvider(LLMProvider):
    """
    LM Studio provider implementation.
    Uses OpenAI-compatible API that LM Studio exposes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LM Studio provider.
        
        Config keys:
            - base_url: LM Studio server URL (default: http://localhost:1234/v1)
            - model: Default model name (optional, LM Studio auto-selects)
            - timeout: Request timeout in seconds (default: 120)
            - max_retries: Maximum retry attempts (default: 3)
            - api_key: Optional API key (LM Studio doesn't require it by default)
        """
        super().__init__(config)
        
        self.base_url = config.get('base_url', 'http://localhost:1234/v1').rstrip('/')
        self.model = config.get('model', 'local-model')  # LM Studio uses loaded model
        self.timeout = config.get('timeout', 120)
        self.max_retries = config.get('max_retries', 3)
        self.api_key = config.get('api_key')  # Optional
        
        self.session: aiohttp.ClientSession = None
        
        logger.info(f"LM Studio provider configured for {self.base_url}")
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.LMSTUDIO
    
    async def initialize(self) -> bool:
        """Initialize LM Studio provider"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            is_healthy = await self.health_check()
            if not is_healthy:
                logger.warning(f"LM Studio at {self.base_url} is not responsive")
                return False
            
            self.is_initialized = True
            logger.info(f"✅ LM Studio provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LM Studio provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if LM Studio is healthy"""
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # LM Studio exposes /v1/models endpoint
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    logger.info(f"LM Studio health check passed, {len(models)} models available")
                    return True
                else:
                    logger.warning(f"LM Studio health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.warning(f"LM Studio health check failed: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using LM Studio OpenAI-compatible API"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Build OpenAI-compatible request
            payload = {
                "model": request.model or self.model,
                "messages": [],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stream": False
            }
            
            # Add system message if provided
            if request.system_message:
                payload["messages"].append({
                    "role": "system",
                    "content": request.system_message
                })
            
            # Add user prompt
            payload["messages"].append({
                "role": "user",
                "content": request.prompt
            })
            
            # Add stop sequences if provided
            if request.stop_sequences:
                payload["stop"] = request.stop_sequences
            
            # Add any provider-specific options
            payload.update(request.provider_options)
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Make request with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    async with self.session.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract response
                            choice = data['choices'][0]
                            text = choice['message']['content']
                            
                            # Calculate latency
                            latency_ms = (time.time() - start_time) * 1000
                            
                            # Extract token usage
                            usage = data.get('usage', {})
                            prompt_tokens = usage.get('prompt_tokens', 0)
                            completion_tokens = usage.get('completion_tokens', 0)
                            total_tokens = usage.get('total_tokens', 0)
                            
                            # Update metrics
                            self._update_metrics(True, total_tokens, latency_ms)
                            
                            return LLMResponse(
                                text=text,
                                model=data.get('model', request.model or self.model),
                                provider=self.provider_type.value,
                                tokens_used=total_tokens,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                finish_reason=choice.get('finish_reason', 'complete'),
                                latency_ms=latency_ms,
                                metadata={
                                    'lmstudio_id': data.get('id'),
                                    'created': data.get('created'),
                                    **request.metadata
                                }
                            )
                        else:
                            error_text = await response.text()
                            last_error = f"HTTP {response.status}: {error_text}"
                            logger.warning(f"LM Studio request failed (attempt {attempt + 1}): {last_error}")
                            
                except aiohttp.ClientError as e:
                    last_error = str(e)
                    logger.warning(f"LM Studio connection error (attempt {attempt + 1}): {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            # All retries failed
            self._update_metrics(False)
            raise LLMError(
                error_type="generation_failed",
                message=f"Failed after {self.max_retries} attempts: {last_error}",
                provider=self.provider_type.value,
                details={'last_error': last_error}
            )
            
        except Exception as e:
            self._update_metrics(False)
            logger.error(f"LM Studio generation error: {e}")
            raise LLMError(
                error_type="unexpected_error",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Generate streaming response using LM Studio"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Build OpenAI-compatible streaming request
            payload = {
                "model": request.model or self.model,
                "messages": [],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stream": True
            }
            
            if request.system_message:
                payload["messages"].append({
                    "role": "system",
                    "content": request.system_message
                })
            
            payload["messages"].append({
                "role": "user",
                "content": request.prompt
            })
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str == '[DONE]':
                                    break
                                try:
                                    import json
                                    data = json.loads(data_str)
                                    delta = data['choices'][0]['delta']
                                    if 'content' in delta:
                                        yield delta['content']
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_text = await response.text()
                    logger.error(f"LM Studio streaming failed: {error_text}")
                    raise LLMError(
                        error_type="streaming_failed",
                        message=error_text,
                        provider=self.provider_type.value,
                        status_code=response.status
                    )
                    
        except Exception as e:
            logger.error(f"LM Studio streaming error: {e}")
            raise LLMError(
                error_type="streaming_error",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def list_models(self) -> List[str]:
        """List available models in LM Studio"""
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['id'] for model in data.get('data', [])]
                    return models
                else:
                    logger.warning(f"Failed to list LM Studio models: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing LM Studio models: {e}")
            return []
    
    async def verify_model(self, model: str) -> bool:
        """Verify if a model is available in LM Studio"""
        models = await self.list_models()
        return model in models
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
        logger.info("LM Studio provider cleaned up")


# Add missing import
import asyncio








