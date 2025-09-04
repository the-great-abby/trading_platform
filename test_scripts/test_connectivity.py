#!/usr/bin/env python3
import aiohttp
import asyncio

async def test_connectivity():
    urls = [
        "http://llm-service-simple:11109/health",
        "http://market-data-service:11084/api/market-data/AAPL",
        "http://rss-feed-service:11004/api/news/AAPL"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=5) as response:
                    print(f"✅ {url}: Status {response.status}")
                    if response.status == 200:
                        text = await response.text()
                        print(f"   Response: {text[:100]}...")
                    else:
                        print(f"   Error: {response.status}")
            except Exception as e:
                print(f"❌ {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connectivity()) 