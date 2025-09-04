# MCP Playwright Server Setup

This project is configured with a **Docker-based** Playwright MCP (Model Context Protocol) server for browser automation capabilities. The setup uses the official `mcp/playwright` Docker image for consistent and isolated browser automation.

## Configuration

The MCP server is configured in `.cursor/mcp.json`:

```json
{
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
}
```

## Features

The Playwright MCP server provides the following browser automation capabilities:

- **Navigation**: Navigate to URLs
- **Element Interaction**: Click, fill forms, wait for elements
- **Screenshots**: Capture page screenshots
- **Content Extraction**: Get page content and titles
- **Browser Control**: Manage browser sessions

## Usage

### In Cursor

1. **Restart Cursor** to load the new MCP configuration
2. The Playwright tools will be available in AI conversations
3. You can ask the AI to perform browser automation tasks

### Example Commands

You can ask the AI to:
- "Navigate to https://example.com and take a screenshot"
- "Fill out a form on a website"
- "Click on a specific element and wait for a page to load"
- "Extract content from a webpage"

## Testing

Run the test script to verify the setup:

```bash
python3 test_mcp_playwright.py
```

Or use the Makefile:

```bash
make mcp-test
```

## Docker Image

The setup uses the official `mcp/playwright` Docker image which includes:
- Playwright browser automation framework
- Chromium browser
- All necessary system dependencies
- MCP protocol implementation

## Troubleshooting

### If the server doesn't work:

1. **Check Docker**: Ensure Docker is running
2. **Pull Image**: Run `docker pull mcp/playwright`
3. **Test Manually**: Run `docker run --rm -i mcp/playwright --help`
4. **Restart Cursor**: Restart Cursor to reload the MCP configuration

### Common Issues:

- **Permission Denied**: Ensure Docker has proper permissions
- **Image Not Found**: Pull the image with `docker pull mcp/playwright`
- **Cursor Not Loading**: Restart Cursor completely

## Advanced Configuration

You can modify the Docker run arguments in `.cursor/mcp.json` to add:
- Volume mounts for persistent data
- Environment variables
- Network configuration
- Resource limits

Example with additional options:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/tmp/screenshots:/app/screenshots",
        "-e", "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
        "mcp/playwright"
      ]
    }
  }
}
```

## Resources

- [Playwright MCP Documentation](https://executeautomation.github.io/mcp-playwright/docs/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Playwright Browser Automation](https://playwright.dev/) 