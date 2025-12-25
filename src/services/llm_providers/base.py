"""
Base LLM Provider Interface
Defines the contract that all LLM providers must implement
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, AsyncIterator
import logging

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM provider types"""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class LLMRequest:
    """Standard LLM request format"""
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    system_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Provider-specific options
    provider_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Standard LLM response format"""
    text: str
    model: str
    provider: str
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "complete"
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Cost tracking (if applicable)
    estimated_cost: Optional[float] = None


@dataclass
class LLMError:
    """Standard error format"""
    error_type: str
    message: str
    provider: str
    status_code: Optional[int] = None
    retry_after: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All providers must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.provider_type = self._get_provider_type()
        self.is_initialized = False
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'average_latency_ms': 0.0,
        }
        logger.info(f"Initializing {self.provider_type} provider")
    
    @abstractmethod
    def _get_provider_type(self) -> LLMProviderType:
        """Return the provider type"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider (connect, verify API keys, etc.)
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            request: The LLM request
            
        Returns:
            LLMResponse with the generated text
            
        Raises:
            LLMError if generation fails
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            request: The LLM request with stream=True
            
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        List available models from this provider.
        
        Returns:
            List of model names/IDs
        """
        pass
    
    @abstractmethod
    async def verify_model(self, model: str) -> bool:
        """
        Verify if a specific model is available.
        
        Args:
            model: Model name/ID to verify
            
        Returns:
            True if model is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """
        Cleanup resources (close connections, etc.)
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics"""
        return {
            **self.metrics,
            'provider': self.provider_type.value,
            'is_initialized': self.is_initialized
        }
    
    def _update_metrics(self, success: bool, tokens: int = 0, latency_ms: float = 0.0):
        """Update provider metrics"""
        self.metrics['total_requests'] += 1
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        
        self.metrics['total_tokens'] += tokens
        
        # Update average latency
        total_successful = self.metrics['successful_requests']
        if total_successful > 0:
            current_avg = self.metrics['average_latency_ms']
            self.metrics['average_latency_ms'] = (
                (current_avg * (total_successful - 1) + latency_ms) / total_successful
            )








