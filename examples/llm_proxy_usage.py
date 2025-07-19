"""
LLM Proxy Service Usage Examples
Demonstrates integration with LLM proxy using native callback URLs
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any
from datetime import datetime


class LLMServiceClient:
    """Client for interacting with the LLM service that uses proxy callbacks"""
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def centralized_request(self, operation: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make a centralized LLM request with proxy callback support"""
        payload = {
            "operation": operation,
            "data": data,
            "model": kwargs.get("model", "gpt-4"),
            "proxy_callback": kwargs.get("proxy_callback"),
            "priority": kwargs.get("priority", 1),
            "use_cache": kwargs.get("use_cache", True)
        }
        
        async with self.session.post(f"{self.base_url}/api/v1/llm", json=payload) as response:
            return await response.json()
    
    async def sentiment_analysis(self, text: str, context: str = "", **kwargs) -> Dict[str, Any]:
        """Analyze sentiment with proxy callback support"""
        return await self.centralized_request("sentiment", {
            "text": text,
            "context": context
        }, **kwargs)
    
    async def trading_signal(self, symbol: str, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate trading signal with proxy callback support"""
        return await self.centralized_request("signal", {
            "symbol": symbol,
            "market_data": market_data,
            "news_data": kwargs.get("news_data", []),
            "technical_indicators": kwargs.get("technical_indicators", {})
        }, **kwargs)
    
    async def risk_assessment(self, portfolio_data: Dict[str, Any], market_conditions: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Assess risk with proxy callback support"""
        return await self.centralized_request("risk", {
            "portfolio_data": portfolio_data,
            "market_conditions": market_conditions
        }, **kwargs)
    
    async def market_analysis(self, market_data: Dict[str, Any], timeframe: str = "1d", **kwargs) -> Dict[str, Any]:
        """Analyze market with proxy callback support"""
        return await self.centralized_request("market", {
            "market_data": market_data,
            "timeframe": timeframe
        }, **kwargs)
    
    async def custom_request(self, messages: list, task_type: str, **kwargs) -> Dict[str, Any]:
        """Make custom LLM request with proxy callback support"""
        return await self.centralized_request("custom", {
            "messages": messages,
            "task_type": task_type,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }, **kwargs)


def create_proxy_callback(success_url: str = None, timeout_url: str = None, timeout_seconds: int = 30, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create proxy callback configuration"""
    return {
        "success_url": success_url,
        "timeout_url": timeout_url,
        "timeout_seconds": timeout_seconds,
        "metadata": metadata or {}
    }


async def example_sentiment_with_success_callback():
    """Example: Sentiment analysis with success callback URL"""
    print("=== Sentiment Analysis with Success Callback ===")
    
    async with LLMServiceClient() as client:
        # Create proxy callback with success URL
        proxy_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/sentiment-success",
            timeout_seconds=30,
            metadata={"source": "trading_platform", "priority": "medium"}
        )
        
        # Analyze sentiment
        result = await client.sentiment_analysis(
            text="Apple reported strong Q4 earnings with 15% revenue growth, beating analyst expectations.",
            context="Technology sector earnings season",
            model="gpt-3.5-turbo",
            proxy_callback=proxy_callback,
            priority=3
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback URLs Configured: {result['callback_urls_configured']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Sentiment Analysis: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_trading_signal_with_both_callbacks():
    """Example: Trading signal with both success and timeout callbacks"""
    print("\n=== Trading Signal with Success and Timeout Callbacks ===")
    
    async with LLMServiceClient() as client:
        # Create proxy callback with both success and timeout URLs
        proxy_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/signal-success",
            timeout_url="http://localhost:8080/webhook/signal-timeout",
            timeout_seconds=45,  # Longer timeout for complex analysis
            metadata={"source": "trading_platform", "auto_execute": True}
        )
        
        # Market data
        market_data = {
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 50000000,
            "change_24h": 2.5,
            "market_cap": 2500000000000,
            "rsi": 65,
            "macd": "bullish",
            "sma_20": 148.50
        }
        
        # News data
        news_data = [
            {
                "title": "Apple beats earnings expectations",
                "sentiment": "positive",
                "impact": "high"
            },
            {
                "title": "New iPhone sales strong",
                "sentiment": "positive",
                "impact": "medium"
            }
        ]
        
        # Generate trading signal
        result = await client.trading_signal(
            symbol="AAPL",
            market_data=market_data,
            news_data=news_data,
            model="gpt-4",
            proxy_callback=proxy_callback,
            priority=5  # High priority for trading signals
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback URLs Configured: {result['callback_urls_configured']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Trading Signal: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_risk_assessment_with_timeout_callback():
    """Example: Risk assessment with timeout callback only"""
    print("\n=== Risk Assessment with Timeout Callback ===")
    
    async with LLMServiceClient() as client:
        # Create proxy callback with timeout URL only
        proxy_callback = create_proxy_callback(
            timeout_url="http://localhost:8080/webhook/risk-timeout",
            timeout_seconds=60,  # Longer timeout for risk analysis
            metadata={"source": "trading_platform", "risk_level": "high"}
        )
        
        # Portfolio data
        portfolio_data = {
            "total_value": 100000,
            "positions": [
                {"symbol": "AAPL", "value": 25000, "weight": 0.25},
                {"symbol": "MSFT", "value": 20000, "weight": 0.20},
                {"symbol": "GOOGL", "value": 15000, "weight": 0.15}
            ],
            "drawdown": 2.5,
            "volatility": 0.18
        }
        
        # Market conditions
        market_conditions = {
            "volatility": "high",
            "trend": "bullish",
            "economic_indicators": ["inflation_rising", "fed_hawkish"],
            "market_regime": "growth"
        }
        
        # Assess risk
        result = await client.risk_assessment(
            portfolio_data=portfolio_data,
            market_conditions=market_conditions,
            model="gpt-4",
            proxy_callback=proxy_callback,
            priority=4
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback URLs Configured: {result['callback_urls_configured']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Risk Assessment: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_market_analysis_with_metadata():
    """Example: Market analysis with callback metadata"""
    print("\n=== Market Analysis with Callback Metadata ===")
    
    async with LLMServiceClient() as client:
        # Create proxy callback with rich metadata
        proxy_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/market-success",
            timeout_url="http://localhost:8080/webhook/market-timeout",
            timeout_seconds=30,
            metadata={
                "source": "trading_platform",
                "analysis_type": "market_regime",
                "timeframe": "daily",
                "priority": "high",
                "notify_traders": True,
                "store_in_database": True
            }
        )
        
        # Market data
        market_data = {
            "market": "S&P 500",
            "price_action": {
                "trend": "bullish",
                "support": 4200,
                "resistance": 4500,
                "current_price": 4350
            },
            "volume_analysis": {
                "above_average": True,
                "distribution": "normal",
                "volume_ratio": 1.2
            },
            "support_resistance": {
                "support": [4200, 4150, 4100],
                "resistance": [4500, 4550, 4600]
            }
        }
        
        # Analyze market
        result = await client.market_analysis(
            market_data=market_data,
            timeframe="1d",
            model="gpt-4",
            proxy_callback=proxy_callback,
            priority=2
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback URLs Configured: {result['callback_urls_configured']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Market Analysis: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_custom_request_with_callbacks():
    """Example: Custom request with proxy callbacks"""
    print("\n=== Custom Request with Proxy Callbacks ===")
    
    async with LLMServiceClient() as client:
        # Create proxy callback for custom request
        proxy_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/custom-success",
            timeout_url="http://localhost:8080/webhook/custom-timeout",
            timeout_seconds=40,
            metadata={
                "source": "trading_platform",
                "request_type": "custom_analysis",
                "user_id": "trader_001"
            }
        )
        
        # Custom messages
        messages = [
            {"role": "system", "content": "You are a financial analyst expert."},
            {"role": "user", "content": "Analyze the current market conditions and provide investment recommendations for tech stocks."}
        ]
        
        # Make custom request
        result = await client.custom_request(
            messages=messages,
            task_type="market_analysis",
            model="gpt-4",
            proxy_callback=proxy_callback,
            priority=3,
            temperature=0.3,
            max_tokens=800
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback URLs Configured: {result['callback_urls_configured']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Custom Analysis: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_batch_requests_with_different_callbacks():
    """Example: Batch requests with different callback configurations"""
    print("\n=== Batch Requests with Different Callbacks ===")
    
    async with LLMServiceClient() as client:
        # Different callback configurations for different operations
        sentiment_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/sentiment-batch",
            timeout_seconds=20
        )
        
        signal_callback = create_proxy_callback(
            success_url="http://localhost:8080/webhook/signal-batch",
            timeout_url="http://localhost:8080/webhook/signal-batch-timeout",
            timeout_seconds=45,
            metadata={"batch_processing": True}
        )
        
        risk_callback = create_proxy_callback(
            timeout_url="http://localhost:8080/webhook/risk-batch-timeout",
            timeout_seconds=60,
            metadata={"batch_processing": True, "priority": "high"}
        )
        
        # Batch of requests
        tasks = [
            # Sentiment analysis
            client.sentiment_analysis(
                text="Tesla announces new battery technology breakthrough",
                proxy_callback=sentiment_callback,
                priority=2
            ),
            # Trading signal
            client.trading_signal(
                symbol="TSLA",
                market_data={"price": 250.50, "volume": 30000000},
                proxy_callback=signal_callback,
                priority=5
            ),
            # Risk assessment
            client.risk_assessment(
                portfolio_data={"total_value": 50000, "positions": []},
                market_conditions={"volatility": "medium"},
                proxy_callback=risk_callback,
                priority=3
            )
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i+1} failed: {result}")
            else:
                print(f"Request {i+1} - ID: {result['request_id']}, Success: {result['success']}, Callbacks: {result['callback_urls_configured']}")


async def example_proxy_health_check():
    """Example: Check proxy health and metrics"""
    print("\n=== Proxy Health Check ===")
    
    async with LLMServiceClient() as client:
        # Check service health
        async with client.session.get(f"{client.base_url}/health") as response:
            health = await response.json()
        
        print("Service Health:")
        print(f"Status: {health['status']}")
        print(f"LLM Proxy Healthy: {health['llm_proxy_healthy']}")
        print(f"Base URL: {health['base_url']}")
        print(f"Request History Size: {health['request_history_size']}")
        
        # Check metrics
        async with client.session.get(f"{client.base_url}/metrics") as response:
            metrics = await response.json()
        
        print(f"\nService Metrics:")
        print(f"Total Requests: {metrics['service_metrics']['total_requests']}")
        print(f"Successful Requests: {metrics['service_metrics']['successful_requests']}")
        print(f"Failed Requests: {metrics['service_metrics']['failed_requests']}")
        print(f"Callback Requests: {metrics['service_metrics']['callback_requests']}")
        
        # LLM metrics
        llm_metrics = metrics['llm_metrics']
        print(f"\nLLM Proxy Metrics:")
        print(f"Total LLM Requests: {llm_metrics['total_requests']}")
        print(f"Successful LLM Requests: {llm_metrics['successful_requests']}")
        print(f"Failed LLM Requests: {llm_metrics['failed_requests']}")
        print(f"Callback Requests: {llm_metrics['callback_requests']}")
        print(f"Timeout Requests: {llm_metrics['timeout_requests']}")
        print(f"Average Response Time: {llm_metrics['average_response_time']:.2f}s")
        print(f"Cache Hits: {llm_metrics['cache_hits']}")
        print(f"Cache Misses: {llm_metrics['cache_misses']}")


async def example_proxy_endpoint_discovery():
    """Example: Discover available proxy endpoints"""
    print("\n=== Proxy Endpoint Discovery ===")
    
    async with LLMServiceClient() as client:
        # Try to discover proxy endpoints
        proxy_base = "http://localhost:8081"
        endpoints_to_check = [
            f"{proxy_base}/",
            f"{proxy_base}/openapi.json",
            f"{proxy_base}/health",
            f"{proxy_base}/v1/chat/completions",
            f"{proxy_base}/chat/completions",
            f"{proxy_base}/completions",
            f"{proxy_base}/generate"
        ]
        
        print("Checking proxy endpoints:")
        for endpoint in endpoints_to_check:
            try:
                async with client.session.get(endpoint) as response:
                    if response.status == 200:
                        print(f"✅ {endpoint} - Available")
                        if endpoint.endswith('openapi.json'):
                            data = await response.json()
                            print(f"   API Title: {data.get('info', {}).get('title', 'Unknown')}")
                    else:
                        print(f"❌ {endpoint} - Status: {response.status}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")


async def main():
    """Run all examples"""
    print("🤖 LLM Proxy Service Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_sentiment_with_success_callback()
        await example_trading_signal_with_both_callbacks()
        await example_risk_assessment_with_timeout_callback()
        await example_market_analysis_with_metadata()
        await example_custom_request_with_callbacks()
        await example_batch_requests_with_different_callbacks()
        await example_proxy_health_check()
        await example_proxy_endpoint_discovery()
        
        print("\n✅ All examples completed successfully!")
        print("\n📝 Key Points:")
        print("- The LLM service now uses your proxy's native callback URL support")
        print("- Success URLs are called when the LLM completes successfully")
        print("- Timeout URLs are called when the request times out")
        print("- Callback metadata is passed through to your proxy")
        print("- No custom callback workers needed - proxy handles everything")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure:")
        print("1. The LLM service is running on http://localhost:8008")
        print("2. Your LLM proxy is running on http://localhost:8081")
        print("3. Your callback webhook endpoints are available")


if __name__ == "__main__":
    asyncio.run(main()) 