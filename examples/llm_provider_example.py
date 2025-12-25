#!/usr/bin/env python3
"""
LLM Provider Example
Demonstrates how to use the new multi-provider system
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_providers import (
    LLMProviderFactory,
    LLMRequest,
    LLMResponse,
    LLMError
)


async def example_basic_usage():
    """Example 1: Basic usage with environment-based provider"""
    print("="*70)
    print("Example 1: Basic Usage")
    print("="*70)
    
    # Create provider from environment (LLM_PROVIDER env var)
    provider = LLMProviderFactory.create_from_env()
    
    print(f"Provider: {provider.provider_type}")
    print(f"Config: {provider.config}")
    
    # Use as context manager
    async with provider:
        # Check health
        is_healthy = await provider.health_check()
        print(f"Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        if is_healthy:
            # Generate response
            request = LLMRequest(
                prompt="Explain the concept of moving averages in trading in one sentence.",
                temperature=0.3,
                max_tokens=100
            )
            
            response = await provider.generate(request)
            
            print(f"\nResponse: {response.text}")
            print(f"Tokens: {response.tokens_used}")
            print(f"Latency: {response.latency_ms:.2f}ms")


async def example_specific_provider():
    """Example 2: Create specific provider"""
    print("\n" + "="*70)
    print("Example 2: Specific Provider (LM Studio)")
    print("="*70)
    
    # Create LM Studio provider explicitly
    provider = LLMProviderFactory.create('lmstudio', {
        'base_url': 'http://localhost:1234/v1',
        'model': 'local-model',
        'timeout': 60
    })
    
    async with provider:
        # List available models
        models = await provider.list_models()
        print(f"Available models: {models}")
        
        # Generate
        request = LLMRequest(
            prompt="What is RSI in technical analysis?",
            temperature=0.5,
            max_tokens=50
        )
        
        try:
            response = await provider.generate(request)
            print(f"\nResponse: {response.text}")
        except LLMError as e:
            print(f"Error: {e.message}")


async def example_provider_comparison():
    """Example 3: Compare providers"""
    print("\n" + "="*70)
    print("Example 3: Provider Comparison")
    print("="*70)
    
    providers_config = [
        ('ollama', {'base_url': 'http://localhost:11434', 'model': 'gemma3:1b'}),
        ('lmstudio', {'base_url': 'http://localhost:1234/v1', 'model': 'local-model'}),
    ]
    
    prompt = "What is a bull market?"
    
    for provider_type, config in providers_config:
        try:
            provider = LLMProviderFactory.create(provider_type, config)
            
            async with provider:
                is_healthy = await provider.health_check()
                
                if is_healthy:
                    request = LLMRequest(prompt=prompt, temperature=0.3, max_tokens=50)
                    response = await provider.generate(request)
                    
                    print(f"\n{provider_type.upper()}:")
                    print(f"  Response: {response.text[:100]}...")
                    print(f"  Latency: {response.latency_ms:.2f}ms")
                    print(f"  Tokens: {response.tokens_used}")
                else:
                    print(f"\n{provider_type.upper()}: ❌ Not available")
                    
        except Exception as e:
            print(f"\n{provider_type.upper()}: ❌ Error: {e}")


async def example_streaming():
    """Example 4: Streaming responses"""
    print("\n" + "="*70)
    print("Example 4: Streaming Response")
    print("="*70)
    
    provider = LLMProviderFactory.create_from_env()
    
    async with provider:
        request = LLMRequest(
            prompt="Explain the concept of support and resistance levels.",
            temperature=0.5,
            max_tokens=200,
            stream=True
        )
        
        print("Streaming response:\n")
        
        try:
            async for chunk in provider.generate_stream(request):
                print(chunk, end='', flush=True)
            print("\n")
        except LLMError as e:
            print(f"Streaming error: {e.message}")


async def example_fallback():
    """Example 5: Fallback between providers"""
    print("\n" + "="*70)
    print("Example 5: Provider Fallback")
    print("="*70)
    
    fallback_chain = ['lmstudio', 'ollama']
    
    request = LLMRequest(
        prompt="What is volume weighted average price (VWAP)?",
        temperature=0.3,
        max_tokens=100
    )
    
    for provider_type in fallback_chain:
        try:
            print(f"\nTrying {provider_type}...")
            provider = LLMProviderFactory.create(provider_type)
            
            async with provider:
                is_healthy = await provider.health_check()
                
                if is_healthy:
                    response = await provider.generate(request)
                    print(f"✅ Success with {provider_type}!")
                    print(f"Response: {response.text}")
                    return
                else:
                    print(f"❌ {provider_type} not healthy, trying next...")
                    
        except Exception as e:
            print(f"❌ {provider_type} failed: {e}")
            print("Trying next provider...")
    
    print("\n⚠️ All providers failed!")


async def example_metrics():
    """Example 6: Provider metrics"""
    print("\n" + "="*70)
    print("Example 6: Provider Metrics")
    print("="*70)
    
    provider = LLMProviderFactory.create_from_env()
    
    async with provider:
        # Make multiple requests
        for i in range(3):
            request = LLMRequest(
                prompt=f"Trading tip #{i+1}",
                temperature=0.7,
                max_tokens=30
            )
            
            try:
                await provider.generate(request)
            except:
                pass
        
        # Get metrics
        metrics = provider.get_metrics()
        
        print("\nProvider Metrics:")
        print(f"  Provider: {metrics['provider']}")
        print(f"  Total Requests: {metrics['total_requests']}")
        print(f"  Successful: {metrics['successful_requests']}")
        print(f"  Failed: {metrics['failed_requests']}")
        print(f"  Total Tokens: {metrics['total_tokens']}")
        print(f"  Average Latency: {metrics['average_latency_ms']:.2f}ms")


async def main():
    """Run all examples"""
    print("\n🧙 LLM Provider Examples\n")
    print(f"Current LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'ollama')}")
    print(f"Supported providers: {LLMProviderFactory.get_supported_providers()}\n")
    
    # Run examples
    await example_basic_usage()
    await example_specific_provider()
    await example_provider_comparison()
    await example_streaming()
    await example_fallback()
    await example_metrics()
    
    print("\n" + "="*70)
    print("✅ All examples complete!")
    print("="*70)


if __name__ == "__main__":
    # Set default provider if not set
    if 'LLM_PROVIDER' not in os.environ:
        os.environ['LLM_PROVIDER'] = 'ollama'
    
    asyncio.run(main())








