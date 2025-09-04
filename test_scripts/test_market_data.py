#!/usr/bin/env python3
import aiohttp
import asyncio

async def test_market_data():
    market_data_url = "http://market-data-service:11084"
    symbol = "NVDA"
    
    print("Testing market data service...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{market_data_url}/market-data/current/{symbol}"
            print(f"Calling URL: {url}")
            
            async with session.get(url, timeout=10) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"SUCCESS - Market data: {data}")
                    return data
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
                    return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_market_data())
    print(f"Final result: {result}") 