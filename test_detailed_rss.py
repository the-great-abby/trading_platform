#!/usr/bin/env python3
import aiohttp
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rss_detailed():
    """Test the exact same code path as the AI stock dashboard"""
    rss_feed_url = "http://rss-feed-service:11004"
    symbol = "NVDA"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get news from RSS feed service - EXACT same code as AI dashboard
            url = f"{rss_feed_url}/api/news/{symbol}"
            params = {"hours_back": 24}
            
            print(f"Calling URL: {url}")
            print(f"Params: {params}")
            
            async with session.get(url, params=params, timeout=10) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Articles found: {len(data.get('articles', []))}")
                    if data.get('articles'):
                        print(f"First article title: {data['articles'][0].get('title', 'No title')}")
                        print(f"Sentiment score: {data['articles'][0].get('sentiment_score', 'No score')}")
                    
                    # Test the _analyze_news_sentiment function
                    articles = data.get("articles", [])
                    if articles:
                        # Calculate average sentiment score
                        sentiment_scores = [article.get("sentiment_score", 0) for article in articles]
                        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                        
                        # Determine sentiment category
                        if avg_sentiment > 0.3:
                            sentiment = "POSITIVE"
                        elif avg_sentiment < -0.3:
                            sentiment = "NEGATIVE"
                        else:
                            sentiment = "NEUTRAL"
                        
                        result = {
                            "sentiment": sentiment,
                            "sentiment_score": round(avg_sentiment, 2),
                            "news_items": articles[:5],  # Top 5 articles
                            "confidence": min(95, len(articles) * 10)
                        }
                        
                        print(f"Analysis result: {result}")
                    else:
                        print("No articles found")
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_rss_detailed()) 