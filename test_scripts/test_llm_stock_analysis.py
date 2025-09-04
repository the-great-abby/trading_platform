#!/usr/bin/env python3
"""
Test: LLM-Powered Stock Analysis Service
This tests the AI service that analyzes if it's a good time to buy a stock
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_vector_storage():
    """Test the PostgreSQL vector storage service"""
    
    print("🧪 Testing PostgreSQL Vector Storage Service...")
    
    # Test health endpoint
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:11006/health"
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Health check passed: {result}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test vectorizing market data
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:11006/api/vectorize/market-data"
            payload = {
                "symbol": "AAPL",
                "market_data": {
                    "price": 150.25,
                    "volume": 45000000,
                    "change_percent": 2.5,
                    "market_cap": "2.5T",
                    "technical_indicators": {
                        "rsi": 65,
                        "macd": "positive"
                    }
                }
            }
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Market data vectorized: {result}")
                else:
                    print(f"❌ Market data vectorization failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Market data vectorization error: {e}")
        return False
    
    # Test searching similar patterns
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:11006/api/search/similar"
            params = {
                "query": "AAPL stock analysis",
                "vector_type": "market_data",
                "top_k": 3
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Similar search working: {len(result)} results")
                else:
                    print(f"❌ Similar search failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Similar search error: {e}")
        return False
    
    print("✅ PostgreSQL Vector Storage Service is working!")
    return True

async def test_llm_proxy():
    """Test the LLM proxy service"""
    
    print("\n🧪 Testing LLM Proxy Service...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:12001/api/chat"
            payload = {
                "prompt": "Analyze if AAPL at $150 is a good buy. Keep it brief.",
                "max_tokens": 100,
                "temperature": 0.3
            }
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ LLM analysis working: {result.get('response', '')[:100]}...")
                    return True
                else:
                    print(f"❌ LLM analysis failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ LLM analysis error: {e}")
        return False

async def test_integrated_analysis():
    """Test the integrated stock analysis"""
    
    print("\n🧪 Testing Integrated Stock Analysis...")
    
    # Test the demo script
    try:
        from demo_llm_stock_analysis import LLMStockAnalyzer
        
        analyzer = LLMStockAnalyzer()
        
        # Test with sample data
        market_data = {
            "price": 150.25,
            "volume": 45000000,
            "change_percent": 2.5,
            "market_cap": "2.5T",
            "technical_indicators": {
                "rsi": 65,
                "macd": "positive",
                "sma_20": 148.50,
                "sma_50": 145.75
            }
        }
        
        analysis = await analyzer.analyze_stock_opportunity("AAPL", 150.25, market_data)
        
        print(f"✅ Integrated analysis completed:")
        print(f"   Recommendation: {analysis.get('recommendation', 'N/A')}")
        print(f"   Confidence: {analysis.get('confidence', 'N/A')}/10")
        print(f"   Risk Level: {analysis.get('risk_level', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated analysis error: {e}")
        return False

async def main():
    """Run all tests"""
    
    print("🤖 LLM-Powered Stock Analysis Service Test")
    print("=" * 50)
    
    # Test vector storage
    vector_ok = await test_vector_storage()
    
    # Test LLM proxy
    llm_ok = await test_llm_proxy()
    
    # Test integrated analysis
    integrated_ok = await test_integrated_analysis()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Vector Storage: {'✅ PASS' if vector_ok else '❌ FAIL'}")
    print(f"   LLM Proxy: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    print(f"   Integrated Analysis: {'✅ PASS' if integrated_ok else '❌ FAIL'}")
    
    if vector_ok and llm_ok and integrated_ok:
        print("\n🎉 All tests passed! The LLM-powered AI service is working correctly.")
        print("\n🚀 You can now:")
        print("   • Run: python demo_llm_stock_analysis.py")
        print("   • Access vector storage at: http://localhost:11006")
        print("   • Use the AI service for stock analysis")
    else:
        print("\n⚠️  Some tests failed. Check the service status and try again.")

if __name__ == "__main__":
    asyncio.run(main()) 