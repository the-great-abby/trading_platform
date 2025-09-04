#!/usr/bin/env python3
import aiohttp
import asyncio
import json

async def test_llm_request():
    url = "http://llm-service-simple:11109/api/v1/llm"
    
    # Same request format as AI stock dashboard
    llm_request = {
        "operation": "custom",
        "data": {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert stock analyst."},
                {"role": "user", "content": "Analyze AAPL stock"}
            ],
            "task_type": "stock_analysis",
            "temperature": 0.3,
            "max_tokens": 800,
            "use_cache": True
        },
        "model": "gpt-3.5-turbo",
        "priority": 1,
        "use_cache": True
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=llm_request, timeout=30) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_request()) 