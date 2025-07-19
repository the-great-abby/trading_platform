#!/bin/bash

# Playwright MCP Server Setup Script

echo "Setting up Playwright MCP Server..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Not in a virtual environment. Consider activating one first."
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Make server executable
echo "Making server executable..."
chmod +x server.py

# Create screenshots directory
echo "Creating screenshots directory..."
mkdir -p screenshots

echo "Setup complete!"
echo ""
echo "To run the server:"
echo "  python server.py"
echo ""
echo "To test the server, you can use an MCP client or run it directly." 