#!/usr/bin/env python3
"""
RSS Feed System Demo
Demonstrates the RSS feed system for daily trade recommendations
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from loguru import logger

# Configuration
RSS_SERVICE_URL = "http://localhost:8084"
STRATEGY_SERVICE_URL = "http://localhost:8000"

class RSSFeedSystemDemo:
    """Demo class for RSS feed system"""
    
    def __init__(self):
        self.rss_service_url = RSS_SERVICE_URL
        self.strategy_service_url = STRATEGY_SERVICE_URL
        
    async def run_demo(self):
        """Run the complete RSS feed system demo"""
        print("🚀 RSS Feed System Demo")
        print("=" * 50)
        
        try:
            # Step 1: Check RSS service health
            await self.check_rss_service_health()
            
            # Step 2: Test RSS feed endpoints
            await self.test_rss_endpoints()
            
            # Step 3: Demonstrate RSS feed structure
            await self.demonstrate_rss_structure()
            
            # Step 4: Show integration with strategy service
            await self.demonstrate_strategy_integration()
            
            # Step 5: Show RSS feed consumption
            await self.demonstrate_rss_consumption()
            
            print("\n✅ RSS Feed System Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")
            print("💡 Make sure the RSS feed service is running:")
            print("   make rss-deploy-all")
            print("   make rss-port-forward")
    
    async def check_rss_service_health(self):
        """Check RSS service health"""
        print("\n🔍 Step 1: Checking RSS Service Health")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.rss_service_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ RSS Service Status: {health_data.get('status', 'unknown')}")
                    print(f"📅 Timestamp: {health_data.get('timestamp', 'unknown')}")
                else:
                    print(f"❌ RSS Service Health Check Failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Cannot connect to RSS service: {e}")
            print("💡 Make sure the RSS service is running and port-forwarded")
    
    async def test_rss_endpoints(self):
        """Test RSS feed endpoints"""
        print("\n🧪 Step 2: Testing RSS Feed Endpoints")
        print("-" * 40)
        
        endpoints = [
            ("/rss/daily-recommendations", "Daily Recommendations RSS Feed"),
            ("/rss/symbol/AAPL", "AAPL Symbol RSS Feed"),
            ("/api/recommendations", "JSON API")
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint, description in endpoints:
                try:
                    response = await client.get(f"{self.rss_service_url}{endpoint}")
                    
                    if response.status_code == 200:
                        print(f"✅ {description}: Available")
                        
                        if endpoint == "/api/recommendations":
                            data = response.json()
                            count = data.get('count', 0)
                            print(f"   📊 Recommendations: {count}")
                        elif endpoint.startswith("/rss/"):
                            content = response.text
                            if "<rss" in content:
                                print(f"   📰 Valid RSS XML: {len(content)} characters")
                            else:
                                print(f"   ⚠️  Invalid RSS format")
                    else:
                        print(f"❌ {description}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {description}: Error - {e}")
    
    async def demonstrate_rss_structure(self):
        """Demonstrate RSS feed structure"""
        print("\n📊 Step 3: RSS Feed Structure Demonstration")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.rss_service_url}/rss/daily-recommendations")
                
                if response.status_code == 200:
                    # Parse RSS XML
                    root = ET.fromstring(response.text)
                    
                    # Extract channel information
                    channel = root.find('channel')
                    if channel is not None:
                        title = channel.find('title')
                        description = channel.find('description')
                        link = channel.find('link')
                        language = channel.find('language')
                        ttl = channel.find('ttl')
                        
                        print("📰 RSS Channel Information:")
                        print(f"   Title: {title.text if title is not None else 'N/A'}")
                        print(f"   Description: {description.text if description is not None else 'N/A'}")
                        print(f"   Link: {link.text if link is not None else 'N/A'}")
                        print(f"   Language: {language.text if language is not None else 'N/A'}")
                        print(f"   TTL: {ttl.text if ttl is not None else 'N/A'} minutes")
                        
                        # Count items
                        items = channel.findall('item')
                        print(f"   Items: {len(items)}")
                        
                        # Show sample item
                        if items:
                            print("\n📋 Sample RSS Item:")
                            sample_item = items[0]
                            
                            item_title = sample_item.find('title')
                            item_description = sample_item.find('description')
                            item_link = sample_item.find('link')
                            item_guid = sample_item.find('guid')
                            item_pub_date = sample_item.find('pubDate')
                            item_category = sample_item.find('category')
                            
                            print(f"   Title: {item_title.text if item_title is not None else 'N/A'}")
                            print(f"   Link: {item_link.text if item_link is not None else 'N/A'}")
                            print(f"   GUID: {item_guid.text if item_guid is not None else 'N/A'}")
                            print(f"   Published: {item_pub_date.text if item_pub_date is not None else 'N/A'}")
                            print(f"   Category: {item_category.text if item_category is not None else 'N/A'}")
                            
                            # Show description preview
                            if item_description is not None and item_description.text:
                                desc_preview = item_description.text[:100] + "..." if len(item_description.text) > 100 else item_description.text
                                print(f"   Description: {desc_preview}")
                else:
                    print("❌ Cannot retrieve RSS feed for structure demonstration")
                    
        except Exception as e:
            print(f"❌ Error demonstrating RSS structure: {e}")
    
    async def demonstrate_strategy_integration(self):
        """Demonstrate integration with strategy service"""
        print("\n🔗 Step 4: Strategy Service Integration")
        print("-" * 40)
        
        try:
            # Test strategy service
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get a sample recommendation
                response = await client.post(
                    f"{self.strategy_service_url}/recommendations/stock",
                    json={
                        "symbol": "AAPL",
                        "include_ai_analysis": True,
                        "include_news_sentiment": True,
                        "include_risk_assessment": True,
                        "strategies": ["rsi_strategy", "macd_strategy", "bollinger_bands_strategy"]
                    }
                )
                
                if response.status_code == 200:
                    recommendation = response.json()
                    print("✅ Strategy Service Integration:")
                    print(f"   Symbol: {recommendation.get('symbol', 'N/A')}")
                    print(f"   Recommendation: {recommendation.get('overall_recommendation', 'N/A')}")
                    print(f"   Confidence: {recommendation.get('confidence', 0):.1%}")
                    print(f"   Current Price: ${recommendation.get('current_price', 0):.2f}")
                    print(f"   Target Price: ${recommendation.get('target_price', 0):.2f}")
                    print(f"   Risk Level: {recommendation.get('risk_level', 'N/A')}")
                    
                    # Show AI analysis if available
                    ai_analysis = recommendation.get('ai_analysis')
                    if ai_analysis:
                        print(f"   AI Analysis: {ai_analysis.get('reasoning', 'N/A')[:100]}...")
                    
                    # Show news sentiment if available
                    news_sentiment = recommendation.get('news_sentiment')
                    if news_sentiment:
                        sentiment_score = news_sentiment.get('sentiment_score', 0)
                        sentiment_label = news_sentiment.get('sentiment_label', 'neutral')
                        print(f"   News Sentiment: {sentiment_label} ({sentiment_score:.2f})")
                        
                else:
                    print(f"❌ Strategy Service Error: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error testing strategy integration: {e}")
    
    async def demonstrate_rss_consumption(self):
        """Demonstrate RSS feed consumption"""
        print("\n📱 Step 5: RSS Feed Consumption")
        print("-" * 40)
        
        print("📰 RSS Feed URLs for Subscription:")
        print(f"   Daily Recommendations: {self.rss_service_url}/rss/daily-recommendations")
        print(f"   Symbol-Specific (AAPL): {self.rss_service_url}/rss/symbol/AAPL")
        print(f"   JSON API: {self.rss_service_url}/api/recommendations")
        
        print("\n🔧 RSS Reader Integration:")
        print("   • Feedly: Add feed URL to your Feedly account")
        print("   • Inoreader: Subscribe to the RSS feed")
        print("   • RSS.app: Convert RSS to email notifications")
        print("   • Zapier: Connect RSS to Slack, email, or other services")
        
        print("\n📧 Email Integration:")
        print("   • RSS.app: Automatic email delivery")
        print("   • Zapier: Custom email workflows")
        print("   • IFTTT: Automated email notifications")
        
        print("\n📊 Dashboard Integration:")
        print("   • Real-time recommendation updates")
        print("   • Historical recommendation tracking")
        print("   • Performance analytics")
        
        print("\n🔄 Workflow:")
        print("   1. Cron job triggers daily at 9:00 AM (weekdays)")
        print("   2. RabbitMQ job published to daily recommendations queue")
        print("   3. Worker processes job and generates recommendations")
        print("   4. RSS feed automatically updated with new recommendations")
        print("   5. Subscribers receive updates via RSS readers")
        print("   6. Email notifications sent to configured recipients")

async def main():
    """Main demo function"""
    demo = RSSFeedSystemDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 