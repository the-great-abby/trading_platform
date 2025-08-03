#!/usr/bin/env python3
"""
Test: AI Stock Dashboard
This tests the web dashboard for AI stock analysis
"""

import asyncio
import aiohttp
import json

async def test_dashboard():
    """Test the AI stock dashboard"""
    
    print("🧪 Testing AI Stock Dashboard...")
    
    # Test health endpoint
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:11007/api/health"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Health check passed: {result}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test stock analysis
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:11007/api/analyze"
            payload = {
                "symbol": "AAPL",
                "current_price": 150.25,
                "include_news": True,
                "include_technical": True,
                "include_sentiment": True
            }
            
            print("📊 Testing stock analysis...")
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Analysis completed successfully!")
                    print(f"   Symbol: {result.get('symbol')}")
                    print(f"   Recommendation: {result.get('recommendation')}")
                    print(f"   Confidence: {result.get('confidence')}/10")
                    print(f"   Risk Level: {result.get('risk_level')}")
                    print(f"   Analysis Time: {result.get('analysis_time', 0):.2f} seconds")
                    return True
                else:
                    print(f"❌ Analysis failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

async def main():
    """Run dashboard test"""
    
    print("🤖 AI Stock Dashboard Test")
    print("=" * 40)
    
    success = await test_dashboard()
    
    if success:
        print("\n🎉 Dashboard test passed!")
        print("\n🚀 You can now access the dashboard at:")
        print("   http://localhost:11007")
        print("\n💡 Features available:")
        print("   • Interactive stock analysis")
        print("   • Real-time AI recommendations")
        print("   • Technical analysis indicators")
        print("   • News sentiment analysis")
        print("   • Risk assessment and confidence scoring")
        print("\n⏱️  Expected response times:")
        print("   • Simple analysis: 2-3 seconds")
        print("   • Full analysis with news: 3-5 seconds")
        print("   • Complex analysis: 5-8 seconds")
    else:
        print("\n❌ Dashboard test failed!")
        print("Check if the service is running and try again.")

if __name__ == "__main__":
    asyncio.run(main()) 