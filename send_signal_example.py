#!/usr/bin/env python3
"""
Example script to send trading signals to the algorithmic trading bot
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any


class TradingSignalClient:
    """Client for sending trading signals to the bot"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def start_engine(self) -> Dict[str, Any]:
        """Start the trading engine"""
        response = await self.client.post(f"{self.base_url}/engine/start")
        return response.json()
    
    async def stop_engine(self) -> Dict[str, Any]:
        """Stop the trading engine"""
        response = await self.client.post(f"{self.base_url}/engine/stop")
        return response.json()
    
    async def set_trading_mode(self, mode: str) -> Dict[str, Any]:
        """Set trading mode (paper/live)"""
        response = await self.client.post(
            f"{self.base_url}/engine/mode",
            json=mode
        )
        return response.json()
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get trading engine status"""
        response = await self.client.get(f"{self.base_url}/engine/status")
        return response.json()
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        response = await self.client.get(f"{self.base_url}/portfolio")
        return response.json()
    
    async def get_trade_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent trade history"""
        response = await self.client.get(f"{self.base_url}/trades?limit={limit}")
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Main function demonstrating signal sending"""
    client = TradingSignalClient()
    
    try:
        print("🤖 AlgoTrader Signal Client")
        print("=" * 40)
        
        # Check if engine is running
        status = await client.get_engine_status()
        print(f"Engine Status: {status}")
        
        # Start the engine if not running
        if not status.get("is_running"):
            print("Starting trading engine...")
            result = await client.start_engine()
            print(f"Start result: {result}")
        
        # Set to paper trading mode (safe for testing)
        print("Setting to paper trading mode...")
        mode_result = await client.set_trading_mode("paper")
        print(f"Mode result: {mode_result}")
        
        # Get portfolio info
        portfolio = await client.get_portfolio()
        print(f"Portfolio: {json.dumps(portfolio, indent=2)}")
        
        # Get recent trades
        trades = await client.get_trade_history(5)
        print(f"Recent trades: {json.dumps(trades, indent=2)}")
        
        print("\n✅ Trading system is ready to receive signals!")
        print("\nTo send signals, you can:")
        print("1. Use the REST API endpoints")
        print("2. Create custom Python scripts")
        print("3. Use the CQRS command system")
        print("4. Let the automated strategies generate signals")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the trading bot API is running on http://localhost:8000")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main()) 