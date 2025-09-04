#!/usr/bin/env python3
import aiohttp
import asyncio

async def test_news_method():
    rss_feed_url = "http://rss-feed-service:11004"
    symbol = "NVDA"
    
    print("Testing _get_real_news_sentiment method...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{rss_feed_url}/api/news/{symbol}"
            params = {"hours_back": 24}
            
            print(f"Calling URL: {url}")
            
            async with session.get(url, params=params, timeout=10) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Articles found: {len(data.get('articles', []))}")
                    
                    articles = data.get("articles", [])
                    if articles:
                        sentiment_scores = [article.get("sentiment_score", 0) for article in articles]
                        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                        
                        if avg_sentiment > 0.3:
                            sentiment = "POSITIVE"
                        elif avg_sentiment < -0.3:
                            sentiment = "NEGATIVE"
                        else:
                            sentiment = "NEUTRAL"
                        
                        result = {
                            "sentiment": sentiment,
                            "sentiment_score": round(avg_sentiment, 2),
                            "news_items": articles[:5],
                            "confidence": min(95, len(articles) * 10)
                        }
                        
                        print(f"SUCCESS - Analysis result: {result}")
                        return result
                    else:
                        print("No articles found")
                        return {"sentiment": "NEUTRAL", "sentiment_score": 0.0, "news_items": [], "confidence": 50}
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
                    return {"sentiment": "NEUTRAL", "sentiment_score": 0.0, "news_items": [], "confidence": 50}
    except Exception as e:
        print(f"Exception: {e}")
        return {"sentiment": "NEUTRAL", "sentiment_score": 0.0, "news_items": [], "confidence": 50}

if __name__ == "__main__":
    result = asyncio.run(test_news_method())
    print(f"Final result: {result}") 