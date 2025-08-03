"""
Example: Using OllamaService with LLM Proxy Service and Callback URLs
Demonstrates how to use the updated OllamaService with timeout and success callback URLs
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from src.services.ai.ollama_service import OllamaService
from src.services.llm_service.llm_client import ProxyCallbackConfig


async def demonstrate_callback_usage():
    """Demonstrate using OllamaService with callback URLs"""
    
    print("🤖 OllamaService with LLM Proxy and Callback URLs Example")
    print("=" * 60)
    
    # Initialize OllamaService with LLM proxy
    async with OllamaService() as ollama_service:
        
        # Test 1: Basic functionality without callbacks
        print("\n📋 Test 1: Basic Market Sentiment Analysis (No Callbacks)")
        print("-" * 50)
        
        news_events = [
            {
                "title": "Tech Company Reports Strong Earnings",
                "content": "Company XYZ reported Q4 earnings that exceeded analyst expectations",
                "source": "Financial Times",
                "event_type": "earnings",
                "affected_symbols": ["XYZ"]
            }
        ]
        
        technical_signals = [
            {
                "indicator": "RSI",
                "value": 65,
                "signal": "neutral",
                "strength": 0.7
            }
        ]
        
        market_data = {
            "symbol": "XYZ",
            "current_price": 150.25,
            "volume": 1000000,
            "change_1d": 2.5
        }
        
        # Analyze without callbacks
        analysis = await ollama_service.analyze_market_sentiment(
            news_events, technical_signals, market_data
        )
        
        print(f"✅ Analysis completed:")
        print(f"   Sentiment: {analysis.sentiment_score}")
        print(f"   Confidence: {analysis.confidence}")
        print(f"   Action: {analysis.recommended_action}")
        
        # Test 2: Using success callback URL
        print("\n📋 Test 2: Market Analysis with Success Callback")
        print("-" * 50)
        
        # Configure success callback
        success_callback = ProxyCallbackConfig(
            success_url="http://localhost:8080/api/llm/success",
            timeout_seconds=30,
            metadata={
                "request_type": "market_sentiment_analysis",
                "symbol": "XYZ",
                "priority": "high"
            }
        )
        
        try:
            analysis_with_callback = await ollama_service.analyze_market_sentiment(
                news_events, technical_signals, market_data,
                proxy_callback=success_callback
            )
            
            print(f"✅ Analysis with success callback completed:")
            print(f"   Sentiment: {analysis_with_callback.sentiment_score}")
            print(f"   Confidence: {analysis_with_callback.confidence}")
            print(f"   Success URL configured: {success_callback.success_url}")
            
        except Exception as e:
            print(f"❌ Callback test failed: {e}")
        
        # Test 3: Using both success and timeout callbacks
        print("\n📋 Test 3: News Sentiment Enhancement with Full Callbacks")
        print("-" * 50)
        
        news_event = {
            "title": "Federal Reserve Announces Rate Decision",
            "content": "The Federal Reserve maintained interest rates at current levels",
            "source": "Reuters",
            "event_type": "monetary_policy",
            "affected_symbols": ["SPY", "QQQ", "IWM"]
        }
        
        # Configure both success and timeout callbacks
        full_callback = ProxyCallbackConfig(
            success_url="http://localhost:8080/api/llm/success",
            timeout_url="http://localhost:8080/api/llm/timeout",
            timeout_seconds=45,
            metadata={
                "request_type": "news_sentiment_enhancement",
                "event_type": "monetary_policy",
                "priority": "critical"
            }
        )
        
        try:
            enhanced_news = await ollama_service.enhance_news_sentiment(
                news_event, proxy_callback=full_callback
            )
            
            print(f"✅ News enhancement with full callbacks completed:")
            print(f"   Enhanced Sentiment: {enhanced_news.get('enhanced_sentiment', 'N/A')}")
            print(f"   Market Impact: {enhanced_news.get('market_impact', 'N/A')}")
            print(f"   Success URL: {full_callback.success_url}")
            print(f"   Timeout URL: {full_callback.timeout_url}")
            print(f"   Timeout: {full_callback.timeout_seconds}s")
            
        except Exception as e:
            print(f"❌ Full callback test failed: {e}")
        
        # Test 4: Trading Signal Generation with Callbacks
        print("\n📋 Test 4: Multi-Factor Trading Signal with Callbacks")
        print("-" * 50)
        
        market_context = {
            "current_price": 150.25,
            "volume": 1000000,
            "volatility": 0.15,
            "market_condition": "bullish"
        }
        
        news_sentiment = {
            "sentiment_score": 0.3,
            "confidence": 0.8,
            "impact": "positive"
        }
        
        # Configure trading signal callback
        trading_callback = ProxyCallbackConfig(
            success_url="http://localhost:8080/api/trading/signal_success",
            timeout_url="http://localhost:8080/api/trading/signal_timeout",
            timeout_seconds=60,
            metadata={
                "request_type": "trading_signal_generation",
                "symbol": "XYZ",
                "strategy": "AI_MULTI_FACTOR",
                "priority": "high"
            }
        )
        
        try:
            signal = await ollama_service.generate_multi_factor_signal(
                symbol="XYZ",
                technical_signals=technical_signals,
                news_sentiment=news_sentiment,
                market_context=market_context,
                proxy_callback=trading_callback
            )
            
            if signal:
                print(f"✅ Trading signal generated with callbacks:")
                print(f"   Action: {signal.action}")
                print(f"   Confidence: {signal.confidence}")
                print(f"   Quantity: {signal.quantity}")
                print(f"   Strategy: {signal.strategy}")
                print(f"   Success URL: {trading_callback.success_url}")
                print(f"   Timeout URL: {trading_callback.timeout_url}")
            else:
                print("❌ No trading signal generated")
                
        except Exception as e:
            print(f"❌ Trading signal test failed: {e}")
        
        # Test 5: Service Health and Metrics
        print("\n📋 Test 5: Service Health and Verification")
        print("-" * 50)
        
        # Verify model availability
        availability = await ollama_service.verify_model_availability()
        print(f"Model Availability: {availability}")
        
        # Test model response
        test_result = await ollama_service.test_model_response()
        print(f"Model Test Result: {test_result}")


async def demonstrate_timeout_handling():
    """Demonstrate timeout handling with callbacks"""
    
    print("\n⏰ Timeout Handling Demonstration")
    print("=" * 40)
    
    async with OllamaService() as ollama_service:
        
        # Configure a very short timeout to trigger timeout callback
        timeout_callback = ProxyCallbackConfig(
            success_url="http://localhost:8080/api/llm/success",
            timeout_url="http://localhost:8080/api/llm/timeout",
            timeout_seconds=5,  # Very short timeout
            metadata={
                "request_type": "timeout_test",
                "test_type": "short_timeout"
            }
        )
        
        # Create a complex prompt that might take longer than 5 seconds
        complex_prompt = "Please provide a detailed analysis of the current market conditions including technical indicators, fundamental factors, and geopolitical risks. Include specific recommendations for portfolio allocation and risk management strategies."
        
        try:
            # This should trigger the timeout callback
            request = await ollama_service.llm_client.generate(
                await ollama_service.llm_client._create_request(
                    model=ollama_service.model,
                    messages=[{"role": "user", "content": complex_prompt}],
                    task_type="market_analysis",
                    proxy_callback=timeout_callback
                )
            )
            
            print("✅ Request completed (unexpected)")
            
        except Exception as e:
            print(f"⏰ Timeout expected: {e}")
            print("   Timeout callback should have been triggered")


async def main():
    """Main demonstration function"""
    
    print("🚀 Starting OllamaService LLM Proxy Integration Demo")
    print("=" * 60)
    
    try:
        # Demonstrate basic callback usage
        await demonstrate_callback_usage()
        
        # Demonstrate timeout handling
        await demonstrate_timeout_handling()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 