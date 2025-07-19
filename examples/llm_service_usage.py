"""
LLM Service Usage Examples
Demonstrates centralized API and callback functionality
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any
from datetime import datetime


class LLMServiceClient:
    """Client for interacting with the LLM service"""
    
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
        """Make a centralized LLM request"""
        payload = {
            "operation": operation,
            "data": data,
            "model": kwargs.get("model", "gpt-4"),
            "callback_config": kwargs.get("callback_config"),
            "priority": kwargs.get("priority", 1),
            "use_cache": kwargs.get("use_cache", True)
        }
        
        async with self.session.post(f"{self.base_url}/api/v1/llm", json=payload) as response:
            return await response.json()
    
    async def sentiment_analysis(self, text: str, context: str = "", **kwargs) -> Dict[str, Any]:
        """Analyze sentiment with callback support"""
        return await self.centralized_request("sentiment", {
            "text": text,
            "context": context
        }, **kwargs)
    
    async def trading_signal(self, symbol: str, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate trading signal with callback support"""
        return await self.centralized_request("signal", {
            "symbol": symbol,
            "market_data": market_data,
            "news_data": kwargs.get("news_data", []),
            "technical_indicators": kwargs.get("technical_indicators", {})
        }, **kwargs)
    
    async def risk_assessment(self, portfolio_data: Dict[str, Any], market_conditions: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Assess risk with callback support"""
        return await self.centralized_request("risk", {
            "portfolio_data": portfolio_data,
            "market_conditions": market_conditions
        }, **kwargs)
    
    async def market_analysis(self, market_data: Dict[str, Any], timeframe: str = "1d", **kwargs) -> Dict[str, Any]:
        """Analyze market with callback support"""
        return await self.centralized_request("market", {
            "market_data": market_data,
            "timeframe": timeframe
        }, **kwargs)
    
    async def custom_request(self, messages: list, task_type: str, **kwargs) -> Dict[str, Any]:
        """Make custom LLM request with callback support"""
        return await self.centralized_request("custom", {
            "messages": messages,
            "task_type": task_type,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }, **kwargs)


def create_http_webhook_callback(url: str, method: str = "POST", headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Create HTTP webhook callback configuration"""
    return {
        "callback_type": "http_webhook",
        "url": url,
        "method": method,
        "headers": headers or {},
        "timeout": 30,
        "retries": 3,
        "retry_delay": 1.0,
        "metadata": {"source": "trading_platform"}
    }


def create_rabbitmq_callback(queue_name: str) -> Dict[str, Any]:
    """Create RabbitMQ callback configuration"""
    return {
        "callback_type": "rabbitmq_queue",
        "queue_name": queue_name,
        "timeout": 30,
        "retries": 3,
        "retry_delay": 1.0,
        "metadata": {"source": "trading_platform"}
    }


def create_trading_action_callback() -> Dict[str, Any]:
    """Create trading action callback configuration"""
    return {
        "callback_type": "trading_action",
        "timeout": 30,
        "retries": 3,
        "retry_delay": 1.0,
        "metadata": {"source": "trading_platform", "auto_execute": True}
    }


def create_notification_callback() -> Dict[str, Any]:
    """Create notification callback configuration"""
    return {
        "callback_type": "notification",
        "timeout": 30,
        "retries": 3,
        "retry_delay": 1.0,
        "metadata": {"source": "trading_platform", "priority": "medium"}
    }


async def example_sentiment_analysis_with_webhook():
    """Example: Sentiment analysis with HTTP webhook callback"""
    print("=== Sentiment Analysis with Webhook Callback ===")
    
    async with LLMServiceClient() as client:
        # Create webhook callback
        callback_config = create_http_webhook_callback(
            url="http://localhost:8080/webhook/sentiment",
            headers={"Authorization": "Bearer your-webhook-token"}
        )
        
        # Analyze sentiment
        result = await client.sentiment_analysis(
            text="Apple reported strong Q4 earnings with 15% revenue growth, beating analyst expectations.",
            context="Technology sector earnings season",
            model="gpt-3.5-turbo",
            callback_config=callback_config,
            priority=3
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback Queued: {result['callback_queued']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Sentiment Analysis: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_trading_signal_with_trading_action():
    """Example: Trading signal with automatic trading action callback"""
    print("\n=== Trading Signal with Trading Action Callback ===")
    
    async with LLMServiceClient() as client:
        # Create trading action callback
        callback_config = create_trading_action_callback()
        
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
            callback_config=callback_config,
            priority=5  # High priority for trading signals
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback Queued: {result['callback_queued']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Trading Signal: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_risk_assessment_with_notification():
    """Example: Risk assessment with notification callback"""
    print("\n=== Risk Assessment with Notification Callback ===")
    
    async with LLMServiceClient() as client:
        # Create notification callback
        callback_config = create_notification_callback()
        
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
            callback_config=callback_config,
            priority=4
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback Queued: {result['callback_queued']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Risk Assessment: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_market_analysis_with_rabbitmq():
    """Example: Market analysis with RabbitMQ callback"""
    print("\n=== Market Analysis with RabbitMQ Callback ===")
    
    async with LLMServiceClient() as client:
        # Create RabbitMQ callback
        callback_config = create_rabbitmq_callback("market.analysis.results")
        
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
            callback_config=callback_config,
            priority=2
        )
        
        print(f"Request ID: {result['request_id']}")
        print(f"Success: {result['success']}")
        print(f"Callback Queued: {result['callback_queued']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        
        if result['success']:
            print(f"Market Analysis: {result['data']}")
        else:
            print(f"Error: {result['error']}")


async def example_custom_request_with_multiple_callbacks():
    """Example: Custom request with multiple callbacks"""
    print("\n=== Custom Request with Multiple Callbacks ===")
    
    async with LLMServiceClient() as client:
        # Create multiple callbacks
        webhook_callback = create_http_webhook_callback("http://localhost:8080/webhook/custom")
        notification_callback = create_notification_callback()
        
        # Custom messages
        messages = [
            {"role": "system", "content": "You are a financial analyst expert."},
            {"role": "user", "content": "Analyze the current market conditions and provide investment recommendations for tech stocks."}
        ]
        
        # Make custom request with webhook callback
        result1 = await client.custom_request(
            messages=messages,
            task_type="market_analysis",
            model="gpt-4",
            callback_config=webhook_callback,
            priority=3,
            temperature=0.3,
            max_tokens=800
        )
        
        print("Webhook Callback Result:")
        print(f"Request ID: {result1['request_id']}")
        print(f"Success: {result1['success']}")
        print(f"Callback Queued: {result1['callback_queued']}")
        
        # Make custom request with notification callback
        result2 = await client.custom_request(
            messages=messages,
            task_type="market_analysis",
            model="gpt-4",
            callback_config=notification_callback,
            priority=3,
            temperature=0.3,
            max_tokens=800
        )
        
        print("\nNotification Callback Result:")
        print(f"Request ID: {result2['request_id']}")
        print(f"Success: {result2['success']}")
        print(f"Callback Queued: {result2['callback_queued']}")


async def example_batch_requests_with_callbacks():
    """Example: Batch requests with different callbacks"""
    print("\n=== Batch Requests with Callbacks ===")
    
    async with LLMServiceClient() as client:
        # Create different callbacks for different operations
        sentiment_callback = create_http_webhook_callback("http://localhost:8080/webhook/sentiment")
        signal_callback = create_trading_action_callback()
        risk_callback = create_notification_callback()
        
        # Batch of requests
        tasks = [
            # Sentiment analysis
            client.sentiment_analysis(
                text="Tesla announces new battery technology breakthrough",
                callback_config=sentiment_callback,
                priority=2
            ),
            # Trading signal
            client.trading_signal(
                symbol="TSLA",
                market_data={"price": 250.50, "volume": 30000000},
                callback_config=signal_callback,
                priority=5
            ),
            # Risk assessment
            client.risk_assessment(
                portfolio_data={"total_value": 50000, "positions": []},
                market_conditions={"volatility": "medium"},
                callback_config=risk_callback,
                priority=3
            )
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i+1} failed: {result}")
            else:
                print(f"Request {i+1} - ID: {result['request_id']}, Success: {result['success']}, Callback: {result['callback_queued']}")


async def example_callback_monitoring():
    """Example: Monitor callback execution"""
    print("\n=== Callback Monitoring ===")
    
    async with LLMServiceClient() as client:
        # Get service metrics
        async with client.session.get(f"{client.base_url}/metrics") as response:
            metrics = await response.json()
        
        print("Service Metrics:")
        print(f"Total Requests: {metrics['service_metrics']['total_requests']}")
        print(f"Successful Requests: {metrics['service_metrics']['successful_requests']}")
        print(f"Failed Requests: {metrics['service_metrics']['failed_requests']}")
        print(f"Callbacks Executed: {metrics['service_metrics']['callbacks_executed']}")
        print(f"Callback Support: {metrics['callback_support']}")
        
        # Get LLM metrics
        llm_metrics = metrics['llm_metrics']
        print(f"\nLLM Metrics:")
        print(f"Total LLM Requests: {llm_metrics['total_requests']}")
        print(f"Successful LLM Requests: {llm_metrics['successful_requests']}")
        print(f"Failed LLM Requests: {llm_metrics['failed_requests']}")
        print(f"Callbacks Executed: {llm_metrics['callbacks_executed']}")
        print(f"Callback Failures: {llm_metrics['callback_failures']}")
        print(f"Average Callback Time: {llm_metrics['average_callback_time']:.2f}s")
        print(f"Callback Queue Size: {llm_metrics['callback_queue_size']}")
        print(f"Callback Workers Active: {llm_metrics['callback_workers_active']}")


async def main():
    """Run all examples"""
    print("🤖 LLM Service Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_sentiment_analysis_with_webhook()
        await example_trading_signal_with_trading_action()
        await example_risk_assessment_with_notification()
        await example_market_analysis_with_rabbitmq()
        await example_custom_request_with_multiple_callbacks()
        await example_batch_requests_with_callbacks()
        await example_callback_monitoring()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure the LLM service is running on http://localhost:8008")


if __name__ == "__main__":
    asyncio.run(main()) 