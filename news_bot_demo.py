#!/usr/bin/env python3
"""
News Bot Demo - Demonstrates news scanning and signal generation
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List


class NewsBotDemo:
    """Demo class for news bot functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def run_demo(self):
        """Run the complete news bot demo"""
        print("🚀 News Bot Demo Starting...")
        print("=" * 50)
        
        # 1. Check scanner status
        await self.check_scanner_status()
        
        # 2. Start the news scanner
        await self.start_news_scanner()
        
        # 3. Show news sources
        await self.show_news_sources()
        
        # 4. Show event keywords
        await self.show_event_keywords()
        
        # 5. Show company mappings
        await self.show_company_mappings()
        
        # 6. Get recent news events
        await self.get_recent_events()
        
        # 7. Get events for specific symbols
        await self.get_symbol_events("AAPL")
        await self.get_symbol_events("TSLA")
        
        # 8. Get sentiment analysis
        await self.get_sentiment_analysis("AAPL")
        await self.get_sentiment_analysis("TSLA")
        
        # 9. Trigger manual scan
        await self.trigger_manual_scan()
        
        # 10. Stop scanner
        await self.stop_news_scanner()
        
        print("\n✅ News Bot Demo Completed!")
    
    async def check_scanner_status(self):
        """Check news scanner status"""
        print("\n📊 Checking News Scanner Status...")
        try:
            response = await self.client.get(f"{self.base_url}/news/scanner/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   Scanner Running: {status['is_running']}")
                print(f"   Sources: {len(status['sources'])}")
                print(f"   Event Types: {len(status['event_types'])}")
                print(f"   Processed News: {status['processed_news_count']}")
            else:
                print(f"   ❌ Failed to get status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def start_news_scanner(self):
        """Start the news scanner"""
        print("\n🔄 Starting News Scanner...")
        try:
            response = await self.client.post(f"{self.base_url}/news/scanner/start")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {result['message']}")
            else:
                print(f"   ❌ Failed to start: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def stop_news_scanner(self):
        """Stop the news scanner"""
        print("\n🛑 Stopping News Scanner...")
        try:
            response = await self.client.post(f"{self.base_url}/news/scanner/stop")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {result['message']}")
            else:
                print(f"   ❌ Failed to stop: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def show_news_sources(self):
        """Show configured news sources"""
        print("\n📰 News Sources:")
        try:
            response = await self.client.get(f"{self.base_url}/news/sources")
            if response.status_code == 200:
                sources = response.json()
                for name, url in sources['sources'].items():
                    print(f"   • {name}: {url}")
            else:
                print(f"   ❌ Failed to get sources: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def show_event_keywords(self):
        """Show event keywords by category"""
        print("\n🔍 Event Keywords by Category:")
        try:
            response = await self.client.get(f"{self.base_url}/news/keywords")
            if response.status_code == 200:
                keywords = response.json()
                for event_type, words in keywords['event_keywords'].items():
                    print(f"   • {event_type.upper()}: {', '.join(words[:5])}...")
            else:
                print(f"   ❌ Failed to get keywords: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def show_company_mappings(self):
        """Show company name to symbol mappings"""
        print("\n🏢 Company Mappings (Sample):")
        try:
            response = await self.client.get(f"{self.base_url}/news/companies")
            if response.status_code == 200:
                companies = response.json()
                # Show first 10 companies
                for i, (name, symbol) in enumerate(companies['company_symbols'].items()):
                    if i >= 10:
                        break
                    print(f"   • {name.title()}: {symbol}")
                print(f"   ... and {companies['total_companies'] - 10} more companies")
            else:
                print(f"   ❌ Failed to get companies: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def get_recent_events(self):
        """Get recent news events"""
        print("\n📈 Recent News Events:")
        try:
            response = await self.client.get(f"{self.base_url}/news/events?limit=3")
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    print(f"   📰 {event['title']}")
                    print(f"      Source: {event['source']}")
                    print(f"      Sentiment: {event['sentiment_score']:.2f}")
                    print(f"      Impact: {event['impact_score']:.2f}")
                    print(f"      Symbols: {event['affected_symbols']}")
                    print(f"      Type: {event['event_type']}")
                    print()
            else:
                print(f"   ❌ Failed to get events: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def get_symbol_events(self, symbol: str):
        """Get events for a specific symbol"""
        print(f"\n📊 News Events for {symbol}:")
        try:
            response = await self.client.get(f"{self.base_url}/news/events/{symbol}?limit=2")
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    print(f"   📰 {event['title']}")
                    print(f"      Sentiment: {event['sentiment_score']:.2f}")
                    print(f"      Impact: {event['impact_score']:.2f}")
                    print(f"      Type: {event['event_type']}")
            else:
                print(f"   ❌ Failed to get {symbol} events: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def get_sentiment_analysis(self, symbol: str):
        """Get sentiment analysis for a symbol"""
        print(f"\n😊 Sentiment Analysis for {symbol}:")
        try:
            response = await self.client.get(f"{self.base_url}/news/sentiment/{symbol}")
            if response.status_code == 200:
                sentiment = response.json()
                print(f"   Score: {sentiment['sentiment_score']:.2f}")
                print(f"   Label: {sentiment['sentiment_label']}")
                print(f"   Confidence: {sentiment['confidence']:.2f}")
                print(f"   Recent Events: {sentiment['recent_events_count']}")
            else:
                print(f"   ❌ Failed to get {symbol} sentiment: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def trigger_manual_scan(self):
        """Trigger a manual news scan"""
        print("\n🔍 Triggering Manual News Scan...")
        try:
            response = await self.client.post(f"{self.base_url}/news/scan/trigger")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {result['message']}")
                print(f"   Events Found: {result['events_found']}")
                print(f"   Timestamp: {result['scan_timestamp']}")
            else:
                print(f"   ❌ Failed to trigger scan: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def simulate_news_event(self):
        """Simulate a news event and show how it would generate a signal"""
        print("\n🎯 Simulating News-Driven Trading Signal...")
        
        # Simulate a positive news event
        news_event = {
            "title": "Apple Reports Record Q4 Earnings, Stock Surges 5%",
            "source": "reuters",
            "sentiment_score": 0.8,
            "impact_score": 0.9,
            "affected_symbols": ["AAPL"],
            "event_type": "earnings",
            "confidence": 0.85
        }
        
        print(f"   📰 News: {news_event['title']}")
        print(f"   📊 Sentiment: {news_event['sentiment_score']:.2f}")
        print(f"   💥 Impact: {news_event['impact_score']:.2f}")
        print(f"   🎯 Confidence: {news_event['confidence']:.2f}")
        
        # Determine trading action
        if news_event['sentiment_score'] > 0.3:
            action = "BUY"
            print(f"   🟢 Signal: {action} {news_event['affected_symbols'][0]}")
        elif news_event['sentiment_score'] < -0.3:
            action = "SELL"
            print(f"   🔴 Signal: {action} {news_event['affected_symbols'][0]}")
        else:
            print(f"   🟡 Signal: HOLD (neutral sentiment)")
        
        print(f"   💰 Position Size: ${1000 * news_event['impact_score'] * news_event['confidence']:.0f}")


async def main():
    """Main demo function"""
    demo = NewsBotDemo()
    
    try:
        await demo.run_demo()
        
        # Additional simulation
        await demo.simulate_news_event()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await demo.client.aclose()


if __name__ == "__main__":
    asyncio.run(main()) 