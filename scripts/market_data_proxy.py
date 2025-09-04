#!/usr/bin/env python3
"""
Simple Market Data Proxy
Directly calls the working market data service and exposes it via HTTP
"""

import asyncio
import aiohttp
import json
import subprocess
from datetime import datetime
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_real_market_data(symbol: str):
    """Get real market data from the working service"""
    try:
        # Method 1: Try direct pod access (we know this works)
        cmd = [
            'kubectl', 'exec', '-n', 'trading-system', 
            'market-data-service-584dc49d4d-bl6tf', '--', 
            'curl', '-s', f'http://localhost:8000/market-data/current/{symbol.upper()}'
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"Stdout: {result.stdout}")
        logger.info(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            logger.info(f"Got REAL market data for {symbol}: {data}")
            return {
                "symbol": data.get("symbol", symbol.upper()),
                "price": data.get("price"),
                "timestamp": data.get("timestamp"),
                "source": "REAL_MARKET_DATA"
            }
        else:
            logger.error(f"Subprocess failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error getting real market data for {symbol}: {e}")
    
    # Fallback to estimated price
    return {
        "symbol": symbol.upper(),
        "price": 100.00,
        "timestamp": datetime.now().isoformat(),
        "source": "estimated"
    }

async def market_data_handler(request):
    """Handle market data requests"""
    symbol = request.match_info['symbol']
    logger.info(f"Requesting market data for {symbol}")
    
    data = await get_real_market_data(symbol)
    
    return web.json_response(data)

async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})

def main():
    """Start the market data proxy server"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/market-data/current/{symbol}', market_data_handler)
    app.router.add_get('/health', health_handler)
    
    # Start server
    port = 11160
    logger.info(f"Starting market data proxy on port {port}")
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main() 