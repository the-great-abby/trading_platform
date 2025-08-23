import asyncio
import aiohttp

async def test_ollama():
    try:
        async with aiohttp.ClientSession() as session:
            # Test internal Kubernetes service
            url = "http://ollama:11434/api/v1/health"
            print(f"Testing connection to: {url}")
            
            async with session.get(url, timeout=10) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    print(f"Success: {result}")
