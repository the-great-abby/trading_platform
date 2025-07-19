# Playwright MCP Server

A Model Context Protocol (MCP) server that provides web automation capabilities using Playwright.

## Features

- Navigate to URLs
- Click elements using CSS selectors
- Fill form inputs
- Take screenshots
- Extract page content
- Wait for elements to appear
- Get page title and URL

## Setup

1. Install dependencies:
```bash
cd mcp-servers/playwright
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Make the server executable:
```bash
chmod +x server.py
```

## Usage

### Running the server directly:
```bash
python server.py
```

### Using with MCP client:
The server communicates via stdio and can be used with any MCP-compatible client.

## Available Tools

### navigate_to_url
Navigate to a specific URL.

**Parameters:**
- `url` (string): The URL to navigate to

### click_element
Click on an element using a selector.

**Parameters:**
- `selector` (string): CSS selector or XPath to find the element
- `waitForSelector` (boolean, optional): Whether to wait for the element to be visible (default: true)

### fill_input
Fill a form input field.

**Parameters:**
- `selector` (string): CSS selector for the input field
- `value` (string): The value to fill in the input field

### screenshot
Take a screenshot of the current page.

**Parameters:**
- `path` (string): Path to save the screenshot
- `fullPage` (boolean, optional): Whether to capture the full page (default: false)

### get_page_content
Get the text content of the current page.

**Parameters:**
- `selector` (string, optional): CSS selector to get content from specific element

### wait_for_element
Wait for an element to appear on the page.

**Parameters:**
- `selector` (string): CSS selector for the element to wait for
- `timeout` (number, optional): Timeout in milliseconds (default: 30000)

### get_page_title
Get the current page title.

**Parameters:** None

### get_page_url
Get the current page URL.

**Parameters:** None

## Configuration

The server runs in non-headless mode by default. To run in headless mode, modify the `headless` parameter in the `ensure_browser` method in `server.py`.

## Error Handling

The server includes comprehensive error handling and will return error messages as text content when operations fail.

## Security Notes

- The server runs with browser automation capabilities
- Ensure proper access controls when deploying
- Consider running in headless mode for production use 