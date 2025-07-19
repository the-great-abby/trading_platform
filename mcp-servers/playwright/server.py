#!/usr/bin/env python3
"""
Playwright MCP Server for web automation
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)


class PlaywrightMCPServer:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.current_page: Optional[Page] = None
        self.playwright = None

    async def ensure_browser(self):
        """Ensure browser is launched"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(
                headless=False  # Set to True for headless mode
            )

    async def ensure_page(self):
        """Ensure page is created"""
        await self.ensure_browser()
        if not self.current_page:
            self.current_page = await self.browser.new_page()

    async def navigate_to_url(self, url: str) -> List[TextContent]:
        """Navigate to a specific URL"""
        await self.ensure_page()
        await self.current_page.goto(url)
        return [TextContent(type="text", text=f"Successfully navigated to {url}")]

    async def click_element(self, selector: str, wait_for_selector: bool = True) -> List[TextContent]:
        """Click on an element using a selector"""
        await self.ensure_page()
        if wait_for_selector:
            await self.current_page.wait_for_selector(selector)
        await self.current_page.click(selector)
        return [TextContent(type="text", text=f"Successfully clicked element: {selector}")]

    async def fill_input(self, selector: str, value: str) -> List[TextContent]:
        """Fill a form input field"""
        await self.ensure_page()
        await self.current_page.fill(selector, value)
        return [TextContent(type="text", text=f"Successfully filled input {selector} with value: {value}")]

    async def take_screenshot(self, path: str, full_page: bool = False) -> List[TextContent]:
        """Take a screenshot of the current page"""
        await self.ensure_page()
        await self.current_page.screenshot(path=path, full_page=full_page)
        return [TextContent(type="text", text=f"Screenshot saved to: {path}")]

    async def get_page_content(self, selector: Optional[str] = None) -> List[TextContent]:
        """Get the text content of the current page"""
        await self.ensure_page()
        if selector:
            content = await self.current_page.text_content(selector) or ""
        else:
            content = await self.current_page.text_content("body") or ""
        return [TextContent(type="text", text=content)]

    async def wait_for_element(self, selector: str, timeout: int = 30000) -> List[TextContent]:
        """Wait for an element to appear on the page"""
        await self.ensure_page()
        await self.current_page.wait_for_selector(selector, timeout=timeout)
        return [TextContent(type="text", text=f"Element {selector} appeared within {timeout}ms")]

    async def get_page_title(self) -> List[TextContent]:
        """Get the page title"""
        await self.ensure_page()
        title = await self.current_page.title()
        return [TextContent(type="text", text=f"Page title: {title}")]

    async def get_page_url(self) -> List[TextContent]:
        """Get the current page URL"""
        await self.ensure_page()
        url = self.current_page.url
        return [TextContent(type="text", text=f"Current URL: {url}")]

    async def cleanup(self):
        """Clean up browser resources"""
        if self.current_page:
            await self.current_page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    """Main function to run the MCP server"""
    server = PlaywrightMCPServer()
    
    # Create MCP server
    mcp_server = Server("playwright-mcp-server")
    
    @mcp_server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools"""
        return [
            Tool(
                name="navigate_to_url",
                description="Navigate to a specific URL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to"
                        }
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="click_element",
                description="Click on an element using a selector",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath to find the element"
                        },
                        "waitForSelector": {
                            "type": "boolean",
                            "description": "Whether to wait for the element to be visible",
                            "default": True
                        }
                    },
                    "required": ["selector"]
                }
            ),
            Tool(
                name="fill_input",
                description="Fill a form input field",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for the input field"
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to fill in the input field"
                        }
                    },
                    "required": ["selector", "value"]
                }
            ),
            Tool(
                name="screenshot",
                description="Take a screenshot of the current page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to save the screenshot"
                        },
                        "fullPage": {
                            "type": "boolean",
                            "description": "Whether to capture the full page",
                            "default": False
                        }
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="get_page_content",
                description="Get the text content of the current page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "Optional CSS selector to get content from specific element"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="wait_for_element",
                description="Wait for an element to appear on the page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for the element to wait for"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in milliseconds",
                            "default": 30000
                        }
                    },
                    "required": ["selector"]
                }
            ),
            Tool(
                name="get_page_title",
                description="Get the current page title",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_page_url",
                description="Get the current page URL",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a specific tool"""
        try:
            if name == "navigate_to_url":
                return await server.navigate_to_url(arguments["url"])
            elif name == "click_element":
                return await server.click_element(
                    arguments["selector"], 
                    arguments.get("waitForSelector", True)
                )
            elif name == "fill_input":
                return await server.fill_input(arguments["selector"], arguments["value"])
            elif name == "screenshot":
                return await server.take_screenshot(
                    arguments["path"], 
                    arguments.get("fullPage", False)
                )
            elif name == "get_page_content":
                return await server.get_page_content(arguments.get("selector"))
            elif name == "wait_for_element":
                return await server.wait_for_element(
                    arguments["selector"], 
                    arguments.get("timeout", 30000)
                )
            elif name == "get_page_title":
                return await server.get_page_title()
            elif name == "get_page_url":
                return await server.get_page_url()
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Handle cleanup on exit
    async def cleanup_handler():
        await server.cleanup()

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            cleanup_handler=cleanup_handler
        )


if __name__ == "__main__":
    asyncio.run(main()) 