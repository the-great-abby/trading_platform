"""
LLM Provider Factory
Creates provider instances based on configuration
"""

import os
from typing import Dict, Any, Optional
import logging

from .base import LLMProvider, LLMProviderType
from .ollama_provider import OllamaProvider
from .lmstudio_provider import LMStudioProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    _providers = {
        LLMProviderType.OLLAMA: OllamaProvider,
        LLMProviderType.LMSTUDIO: LMStudioProvider,
        LLMProviderType.OPENAI: OpenAIProvider,
    }
    
    @classmethod
    def create(cls, provider_type: str, config: Optional[Dict[str, Any]] = None) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ('ollama', 'lmstudio', 'openai')
            config: Provider-specific configuration. If None, loads from environment.
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider_type is not supported
        """
        # Normalize provider type
        provider_type_enum = LLMProviderType(provider_type.lower())
        
        # Get provider class
        provider_class = cls._providers.get(provider_type_enum)
        if not provider_class:
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types: {list(cls._providers.keys())}"
            )
        
        # Load configuration if not provided
        if config is None:
            config = cls._load_config_from_env(provider_type_enum)
        
        # Create and return provider
        logger.info(f"Creating {provider_type_enum.value} provider")
        return provider_class(config)
    
    @classmethod
    def create_from_env(cls) -> LLMProvider:
        """
        Create provider from environment variables.
        Uses LLM_PROVIDER env var to determine which provider to use.
        
        Environment variables:
            LLM_PROVIDER: Provider type ('ollama', 'lmstudio', 'openai')
            
        Returns:
            Configured LLM provider instance
        """
        provider_type = os.getenv('LLM_PROVIDER', 'ollama').lower()
        logger.info(f"Creating LLM provider from environment: {provider_type}")
        return cls.create(provider_type)
    
    @classmethod
    def _load_config_from_env(cls, provider_type: LLMProviderType) -> Dict[str, Any]:
        """
        Load provider configuration from environment variables.
        
        Args:
            provider_type: The provider type
            
        Returns:
            Configuration dictionary
        """
        if provider_type == LLMProviderType.OLLAMA:
            return {
                'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                'model': os.getenv('OLLAMA_MODEL', 'gemma3:1b'),
                'timeout': int(os.getenv('OLLAMA_TIMEOUT', '120')),
                'max_retries': int(os.getenv('OLLAMA_MAX_RETRIES', '3')),
            }
        
        elif provider_type == LLMProviderType.LMSTUDIO:
            return {
                'base_url': os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1'),
                'model': os.getenv('LMSTUDIO_MODEL', 'local-model'),
                'timeout': int(os.getenv('LMSTUDIO_TIMEOUT', '120')),
                'max_retries': int(os.getenv('LMSTUDIO_MAX_RETRIES', '3')),
                'api_key': os.getenv('LMSTUDIO_API_KEY'),  # Optional
            }
        
        elif provider_type == LLMProviderType.OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
            
            return {
                'api_key': api_key,
                'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                'organization': os.getenv('OPENAI_ORGANIZATION'),
                'timeout': int(os.getenv('OPENAI_TIMEOUT', '60')),
                'max_retries': int(os.getenv('OPENAI_MAX_RETRIES', '3')),
            }
        
        else:
            raise ValueError(f"No environment configuration for provider: {provider_type}")
    
    @classmethod
    def register_provider(cls, provider_type: LLMProviderType, provider_class: type):
        """
        Register a custom provider type.
        
        Args:
            provider_type: The provider type enum
            provider_class: The provider class (must inherit from LLMProvider)
        """
        if not issubclass(provider_class, LLMProvider):
            raise ValueError(f"Provider class must inherit from LLMProvider")
        
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered custom provider: {provider_type.value}")
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider types"""
        return [p.value for p in cls._providers.keys()]








