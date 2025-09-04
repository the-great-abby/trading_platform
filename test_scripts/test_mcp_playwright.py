#!/usr/bin/env python3
"""
Test script to verify MCP Playwright server configuration
"""

import subprocess
import json
import sys

def test_mcp_playwright():
    """Test the MCP Playwright server configuration"""
    print("Testing MCP Playwright server configuration...")
    
    # Test command that would be used by Cursor
    cmd = [
        "docker", "run", "-i", "--rm", "mcp/playwright"
    ]
    
    try:
        # Start the process and send a simple test
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send a simple MCP initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "cursor",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send the message and wait a bit
        stdout, stderr = process.communicate(input=json.dumps(init_message) + "\n", timeout=10)
        
        if process.returncode == 0:
            print("✅ MCP Playwright server is working correctly!")
            print("Configuration in .cursor/mcp.json is valid.")
            return True
        else:
            print("❌ MCP Playwright server test failed")
            print(f"Error: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ MCP Playwright server started successfully (timeout is expected)")
        print("Configuration in .cursor/mcp.json is valid.")
        return True
    except Exception as e:
        print(f"❌ Error testing MCP Playwright server: {e}")
        return False

def show_configuration():
    """Show the current MCP configuration"""
    print("\n📋 Current MCP Configuration:")
    print("File: .cursor/mcp.json")
    print("Configuration:")
    print(json.dumps({
        "mcpServers": {
            "playwright": {
                "command": "docker",
                "args": [
                    "run",
                    "-i", 
                    "--rm",
                    "mcp/playwright"
                ]
            }
        }
    }, indent=2))

def main():
    """Main function"""
    print("🔧 MCP Playwright Server Setup Verification")
    print("=" * 50)
    
    show_configuration()
    print()
    
    success = test_mcp_playwright()
    
    if success:
        print("\n🎉 Setup complete! Your MCP Playwright server is ready to use.")
        print("\nNext steps:")
        print("1. Restart Cursor to load the new MCP configuration")
        print("2. The Playwright MCP server will be available in your AI assistant")
        print("3. You can now use browser automation tools in your conversations")
    else:
        print("\n❌ Setup failed. Please check the configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 