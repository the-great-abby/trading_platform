"""
Ollama Provider Implementation
Wraps existing Ollama functionality in the provider interface
"""

import aiohttp
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


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation.
    Uses native Ollama API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider.
        
        Config keys:
            - base_url: Ollama server URL (default: http://localhost:11434)
            - model: Default model name (e.g., 'gemma3:1b', 'llama2:7b')
            - timeout: Request timeout in seconds (default: 120)
            - max_retries: Maximum retry attempts (default: 3)
        """
        super().__init__(config)
        
        self.base_url = config.get('base_url', 'http://localhost:11434').rstrip('/')
        self.model = config.get('model', 'gemma3:1b')
        self.timeout = config.get('timeout', 120)
        self.max_retries = config.get('max_retries', 3)
        
        self.session: aiohttp.ClientSession = None
        
        logger.info(f"Ollama provider configured for {self.base_url} with model {self.model}")
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.OLLAMA
    
    async def initialize(self) -> bool:
        """Initialize Ollama provider"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            is_healthy = await self.health_check()
            if not is_healthy:
                logger.warning(f"Ollama at {self.base_url} is not responsive")
                return False
            
            # Verify model availability
            is_model_available = await self.verify_model(self.model)
            if not is_model_available:
                logger.warning(f"Model {self.model} not found in Ollama")
                # Don't fail initialization, model might be pulled later
            
            self.is_initialized = True
            logger.info(f"✅ Ollama provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy"""
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Ollama exposes /api/tags endpoint
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    logger.info("Ollama health check passed")
                    return True
                else:
                    logger.warning(f"Ollama health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Ollama API"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Build Ollama request
            payload = {
                "model": request.model or self.model,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens,
                }
            }
            
            # Add system message if provided
            if request.system_message:
                payload["system"] = request.system_message
            
            # Add stop sequences if provided
            if request.stop_sequences:
                payload["options"]["stop"] = request.stop_sequences
            
            # Add any provider-specific options
            if request.provider_options:
                payload["options"].update(request.provider_options)
            
            # Make request with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract response
                            text = data.get('response', '')
                            
                            # Calculate latency
                            latency_ms = (time.time() - start_time) * 1000
                            
                            # Extract token counts (Ollama provides eval_count and prompt_eval_count)
                            prompt_tokens = data.get('prompt_eval_count', 0)
                            completion_tokens = data.get('eval_count', 0)
                            total_tokens = prompt_tokens + completion_tokens
                            
                            # Update metrics
                            self._update_metrics(True, total_tokens, latency_ms)
                            
                            return LLMResponse(
                                text=text,
                                model=data.get('model', request.model or self.model),
                                provider=self.provider_type.value,
                                tokens_used=total_tokens,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                finish_reason='stop' if data.get('done') else 'length',
                                latency_ms=latency_ms,
                                metadata={
                                    'load_duration': data.get('load_duration'),
                                    'total_duration': data.get('total_duration'),
                                    **request.metadata
                                }
                            )
                        else:
                            error_text = await response.text()
                            last_error = f"HTTP {response.status}: {error_text}"
                            logger.warning(f"Ollama request failed (attempt {attempt + 1}): {last_error}")
                            
                except aiohttp.ClientError as e:
                    last_error = str(e)
                    logger.warning(f"Ollama connection error (attempt {attempt + 1}): {e}")
                
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
            logger.error(f"Ollama generation error: {e}")
            raise LLMError(
                error_type="unexpected_error",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Generate streaming response using Ollama"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            payload = {
                "model": request.model or self.model,
                "prompt": request.prompt,
                "stream": True,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens,
                }
            }
            
            if request.system_message:
                payload["system"] = request.system_message
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                import json
                                data = json.loads(line)
                                if 'response' in data:
                                    yield data['response']
                                if data.get('done'):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama streaming failed: {error_text}")
                    raise LLMError(
                        error_type="streaming_failed",
                        message=error_text,
                        provider=self.provider_type.value,
                        status_code=response.status
                    )
                    
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise LLMError(
                error_type="streaming_error",
                message=str(e),
                provider=self.provider_type.value
            )
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    return models
                else:
                    logger.warning(f"Failed to list Ollama models: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
    
    async def verify_model(self, model: str) -> bool:
        """Verify if a model is available in Ollama"""
        models = await self.list_models()
        return model in models
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
        logger.info("Ollama provider cleaned up")








