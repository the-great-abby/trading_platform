#!/usr/bin/env python3
"""
Test script for the Playwright MCP Server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


async def test_mcp_server():
    """Test the MCP server functionality"""
    
    # Start the MCP server
    server_path = Path(__file__).parent / "server.py"
    
    print("Starting Playwright MCP Server...")
    process = subprocess.Popen(
        [sys.executable, str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: List tools
        print("\n1. Testing list_tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request = json.dumps(list_tools_request) + "\n"
        process.stdin.write(request)
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response}")
        
        # Test 2: Navigate to a URL
        print("\n2. Testing navigate_to_url...")
        navigate_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "navigate_to_url",
                "arguments": {
                    "url": "https://example.com"
                }
            }
        }
        
        request = json.dumps(navigate_request) + "\n"
        process.stdin.write(request)
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response}")
        
        # Test 3: Get page title
        print("\n3. Testing get_page_title...")
        title_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_page_title",
                "arguments": {}
            }
        }
        
        request = json.dumps(title_request) + "\n"
        process.stdin.write(request)
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response}")
        
        # Test 4: Take screenshot
        print("\n4. Testing screenshot...")
        screenshot_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "path": "screenshots/test_screenshot.png",
                    "fullPage": False
                }
            }
        }
        
        request = json.dumps(screenshot_request) + "\n"
        process.stdin.write(request)
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response}")
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Clean up
        process.terminate()
        process.wait()


if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 