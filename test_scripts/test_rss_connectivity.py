#!/usr/bin/env python3
import aiohttp
import asyncio

async def test_rss():
    url = "http://rss-feed-service:11004/api/news/NVDA?hours_back=24"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Articles found: {len(data.get('articles', []))}")
                    if data.get('articles'):
                        print(f"First article title: {data['articles'][0].get('title', 'No title')}")
                        print(f"Sentiment score: {data['articles'][0].get('sentiment_score', 'No score')}")
                else:
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_rss()) 