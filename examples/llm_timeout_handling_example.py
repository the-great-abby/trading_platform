"""
LLM Proxy Timeout Handling Example
Demonstrates how to handle timeouts in the LLM proxy system
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path to import from src
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_service.enhanced_timeout_handler import (
    TradingTimeoutHandler, 
    TimeoutConfig, 
    TimeoutStrategy
)
from src.services.llm_service.llm_client import LLMClient, LLMRequest, LLMTaskType
from src.services.llm_service.llm_client import ProxyCallbackConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMTimeoutExample:
    """Example demonstrating LLM proxy timeout handling"""
    
    def __init__(self):
        # Initialize timeout handler with trading-specific configuration
        self.timeout_config = TimeoutConfig(
            client_timeout=10,      # Short timeout for demo
            service_timeout=15,
            ollama_timeout=30.0,
            max_retries=2,          # Fewer retries for demo
            retry_delay=2.0,
            max_delay=10.0
        )
        
        self.timeout_handler = TradingTimeoutHandler(self.timeout_config)
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            base_url="http://localhost:12001",  # LLM proxy URL
            timeout=self.timeout_config.client_timeout,
            max_retries=self.timeout_config.max_retries
        )
        
        logger.info("LLM Timeout Example initialized")
    
    async def demonstrate_timeout_handling(self):
        """Demonstrate different timeout handling scenarios"""
        
        logger.info("🚀 Starting LLM timeout handling demonstration")
        
        # Example 1: Normal request (should succeed)
        await self._example_normal_request()
        
        # Example 2: Timeout with exponential backoff
        await self._example_timeout_exponential_backoff()
        
        # Example 3: Timeout with fallback strategy
        await self._example_timeout_fallback()
        
        # Example 4: Service unavailable with health check
        await self._example_service_unavailable()
        
        # Example 5: Rate limit exceeded
        await self._example_rate_limit()
        
        # Show metrics
        await self._show_metrics()
    
    async def _example_normal_request(self):
        """Example of a normal request that should succeed"""
        logger.info("\n📋 Example 1: Normal Request")
        
        try:
            request = LLMRequest(
                model="gemma3:1b",
                messages=[{"role": "user", "content": "Analyze this trading signal: AAPL is showing bullish momentum"}],
                task_type=LLMTaskType.SIGNAL_ANALYSIS,
                temperature=0.7,
                max_tokens=200
            )
            
            response = await self.llm_client.generate(request)
            
            if hasattr(response, 'content'):
                logger.info(f"✅ Success: {response.content[:100]}...")
            else:
                logger.warning(f"⚠️  Error: {response.error_message}")
                
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
    
    async def _example_timeout_exponential_backoff(self):
        """Example of timeout with exponential backoff retry"""
        logger.info("\n📋 Example 2: Timeout with Exponential Backoff")
        
        # Simulate a request that might timeout
        request_data = {
            'model': 'gemma3:1b',
            'messages': [{"role": "user", "content": "Complex market analysis with multiple indicators"}],
            'task_type': 'signal_analysis'
        }
        
        try:
            result = await self.timeout_handler.handle_timeout(
                component='client',
                operation='signal_analysis',
                request_data=request_data,
                strategy=TimeoutStrategy.EXPONENTIAL_BACKOFF
            )
            
            logger.info(f"✅ Result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
    
    async def _example_timeout_fallback(self):
        """Example of timeout with fallback strategy"""
        logger.info("\n📋 Example 3: Timeout with Fallback")
        
        request_data = {
            'model': 'gemma3:1b',
            'messages': [{"role": "user", "content": "Sentiment analysis for AAPL"}],
            'task_type': 'sentiment'
        }
        
        try:
            result = await self.timeout_handler.handle_timeout(
                component='service',
                operation='sentiment',
                request_data=request_data,
                strategy=TimeoutStrategy.FALLBACK
            )
            
            logger.info(f"✅ Fallback Result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
    
    async def _example_service_unavailable(self):
        """Example of service unavailable with health check"""
        logger.info("\n📋 Example 4: Service Unavailable with Health Check")
        
        request_data = {
            'model': 'gemma3:1b',
            'messages': [{"role": "user", "content": "Risk assessment for portfolio"}],
            'task_type': 'risk'
        }
        
        try:
            result = await self.timeout_handler.handle_timeout(
                component='ollama',
                operation='risk',
                request_data=request_data,
                strategy=TimeoutStrategy.HEALTH_CHECK
            )
            
            logger.info(f"✅ Health Check Result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
    
    async def _example_rate_limit(self):
        """Example of rate limit exceeded"""
        logger.info("\n📋 Example 5: Rate Limit Exceeded")
        
        request_data = {
            'model': 'gemma3:1b',
            'messages': [{"role": "user", "content": "Market analysis for multiple symbols"}],
            'task_type': 'market'
        }
        
        try:
            result = await self.timeout_handler.handle_timeout(
                component='proxy',
                operation='market',
                request_data=request_data,
                strategy=TimeoutStrategy.RATE_LIMIT
            )
            
            logger.info(f"✅ Rate Limit Result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
    
    async def _show_metrics(self):
        """Show timeout handling metrics"""
        logger.info("\n📊 Timeout Handling Metrics")
        
        metrics = self.timeout_handler.get_metrics()
        
        logger.info(f"Total Timeouts: {metrics['total_timeouts']}")
        logger.info(f"Timeouts by Component: {metrics['timeout_by_component']}")
        logger.info(f"Retry Success Rate: {metrics['retry_success_rate']:.2%}")
        logger.info(f"Fallback Usage: {metrics['fallback_usage']}")
        logger.info(f"Average Timeout Duration: {metrics['average_timeout_duration']:.2f}s")
        logger.info(f"Last Timeout: {metrics['last_timeout']}")
    
    async def demonstrate_callback_timeout(self):
        """Demonstrate callback-based timeout handling"""
        logger.info("\n📋 Example 6: Callback-Based Timeout Handling")
        
        # Configure callback URLs
        callback_config = ProxyCallbackConfig(
            success_url="http://localhost:8080/api/llm/success",
            timeout_url="http://localhost:8080/api/llm/timeout",
            timeout_seconds=30,
            metadata={
                "request_type": "trade_evaluation",
                "priority": "high",
                "user_id": "demo_user"
            }
        )
        
        # Create request with callback
        request = LLMRequest(
            model="gemma3:1b",
            messages=[{"role": "user", "content": "Evaluate this trade signal with detailed analysis"}],
            task_type=LLMTaskType.SIGNAL_ANALYSIS,
            temperature=0.7,
            max_tokens=500,
            proxy_callback=callback_config
        )
        
        try:
            logger.info("🔄 Submitting request with callback URLs...")
            response = await self.llm_client.generate(request)
            
            if hasattr(response, 'callback_urls_configured') and response.callback_urls_configured:
                logger.info("✅ Callback URLs configured successfully")
                logger.info(f"📋 Request ID: {response.request_id}")
                logger.info(f"⏰ Timeout URL: {callback_config.timeout_url}")
                logger.info(f"✅ Success URL: {callback_config.success_url}")
            else:
                logger.warning("⚠️  Callback URLs not configured")
                
        except Exception as e:
            logger.error(f"❌ Callback example failed: {e}")
    
    async def demonstrate_adaptive_timeout(self):
        """Demonstrate adaptive timeout based on request type"""
        logger.info("\n📋 Example 7: Adaptive Timeout Handling")
        
        # Different timeout configurations for different use cases
        timeout_configs = {
            'real_time_trading': TimeoutConfig(
                client_timeout=5,
                service_timeout=10,
                max_retries=2,
                retry_delay=1.0
            ),
            'market_analysis': TimeoutConfig(
                client_timeout=15,
                service_timeout=30,
                max_retries=3,
                retry_delay=2.0
            ),
            'backtesting': TimeoutConfig(
                client_timeout=30,
                service_timeout=60,
                max_retries=5,
                retry_delay=5.0
            )
        }
        
        for use_case, config in timeout_configs.items():
            logger.info(f"\n🎯 {use_case.replace('_', ' ').title()}")
            logger.info(f"   Client Timeout: {config.client_timeout}s")
            logger.info(f"   Service Timeout: {config.service_timeout}s")
            logger.info(f"   Max Retries: {config.max_retries}")
            logger.info(f"   Retry Delay: {config.retry_delay}s")
            
            # Create handler with specific config
            handler = TradingTimeoutHandler(config)
            
            # Simulate request
            request_data = {
                'model': 'gemma3:1b',
                'messages': [{"role": "user", "content": f"Analysis for {use_case}"}],
                'task_type': 'signal_analysis'
            }
            
            try:
                result = await handler.handle_timeout(
                    component='client',
                    operation='signal_analysis',
                    request_data=request_data,
                    strategy=TimeoutStrategy.EXPONENTIAL_BACKOFF
                )
                
                logger.info(f"   ✅ Result: {result.get('success', False)}")
                
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")


async def main():
    """Main demonstration function"""
    example = LLMTimeoutExample()
    
    try:
        # Run all demonstrations
        await example.demonstrate_timeout_handling()
        await example.demonstrate_callback_timeout()
        await example.demonstrate_adaptive_timeout()
        
        logger.info("\n🎉 LLM timeout handling demonstration completed!")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 