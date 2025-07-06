#!/usr/bin/env python3
"""
Strategy Manager - Control and manage trading strategies
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List


class StrategyManager:
    """Manager for trading strategies"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_strategies(self) -> Dict[str, Any]:
        """Get all registered strategies"""
        response = await self.client.get(f"{self.base_url}/strategies")
        return response.json()
    
    async def activate_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """Activate a strategy"""
        response = await self.client.post(f"{self.base_url}/strategies/{strategy_name}/activate")
        return response.json()
    
    async def deactivate_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """Deactivate a strategy"""
        response = await self.client.post(f"{self.base_url}/strategies/{strategy_name}/deactivate")
        return response.json()
    
    async def update_strategy(self, strategy_name: str, is_active: bool = None, parameters: Dict = None) -> Dict[str, Any]:
        """Update strategy parameters or activation status"""
        update_data = {}
        if is_active is not None:
            update_data["is_active"] = is_active
        if parameters:
            update_data["parameters"] = parameters
        
        response = await self.client.put(
            f"{self.base_url}/strategies/{strategy_name}/update",
            json=update_data
        )
        return response.json()
    
    async def send_manual_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a manual trading signal"""
        response = await self.client.post(
            f"{self.base_url}/signals",
            json=signal_data
        )
        return response.json()
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get trading engine status"""
        response = await self.client.get(f"{self.base_url}/engine/status")
        return response.json()
    
    async def start_engine(self) -> Dict[str, Any]:
        """Start the trading engine"""
        response = await self.client.post(f"{self.base_url}/engine/start")
        return response.json()
    
    async def set_trading_mode(self, mode: str) -> Dict[str, Any]:
        """Set trading mode"""
        response = await self.client.post(
            f"{self.base_url}/engine/mode",
            json=mode
        )
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def demonstrate_strategies():
    """Demonstrate different trading strategies and signal types"""
    manager = StrategyManager()
    
    try:
        print("🎯 Strategy Manager - Trading Signal Demonstrations")
        print("=" * 60)
        
        # Start the engine
        print("1. Starting trading engine...")
        await manager.start_engine()
        await manager.set_trading_mode("paper")  # Safe for testing
        
        # Get current strategies
        print("\n2. Current strategies:")
        strategies = await manager.get_strategies()
        for strategy in strategies.get("strategies", []):
            print(f"   - {strategy['name']}: {'🟢 Active' if strategy['is_active'] else '🔴 Inactive'}")
        
        # Demonstrate different signal types
        print("\n3. Sending different types of trading signals:")
        
        # Signal Type 1: Momentum-based buy signal
        momentum_signal = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 15,
            "price": 150.25,
            "strategy": "momentum",
            "confidence": 0.85,
            "metadata": {
                "signal_type": "momentum_breakout",
                "volume_spike": True,
                "price_momentum": 0.05
            }
        }
        
        print("   📈 Momentum Buy Signal (AAPL)")
        result = await manager.send_manual_signal(momentum_signal)
        print(f"      Result: {result}")
        
        # Signal Type 2: Mean reversion sell signal
        mean_reversion_signal = {
            "symbol": "MSFT",
            "action": "SELL",
            "quantity": 10,
            "price": 320.50,
            "strategy": "mean_reversion",
            "confidence": 0.75,
            "metadata": {
                "signal_type": "mean_reversion",
                "deviation_from_mean": 0.15,
                "rsi": 75
            }
        }
        
        print("   📉 Mean Reversion Sell Signal (MSFT)")
        result = await manager.send_manual_signal(mean_reversion_signal)
        print(f"      Result: {result}")
        
        # Signal Type 3: News-based signal
        news_signal = {
            "symbol": "GOOGL",
            "action": "BUY",
            "quantity": 8,
            "price": 2750.00,
            "strategy": "news_sentiment",
            "confidence": 0.90,
            "metadata": {
                "signal_type": "news_driven",
                "sentiment_score": 0.8,
                "news_impact": "positive_earnings",
                "volume_multiplier": 2.5
            }
        }
        
        print("   📰 News-Based Buy Signal (GOOGL)")
        result = await manager.send_manual_signal(news_signal)
        print(f"      Result: {result}")
        
        # Signal Type 4: Options flow signal
        options_signal = {
            "symbol": "TSLA",
            "action": "BUY",
            "quantity": 25,
            "price": 850.75,
            "strategy": "options_flow",
            "confidence": 0.80,
            "metadata": {
                "signal_type": "options_flow",
                "unusual_activity": True,
                "call_put_ratio": 3.2,
                "strike_price": 900,
                "expiration": "2024-01-19"
            }
        }
        
        print("   🎯 Options Flow Signal (TSLA)")
        result = await manager.send_manual_signal(options_signal)
        print(f"      Result: {result}")
        
        # Signal Type 5: Sector rotation signal
        sector_signal = {
            "symbol": "XLK",  # Technology ETF
            "action": "BUY",
            "quantity": 50,
            "price": 185.30,
            "strategy": "sector_rotation",
            "confidence": 0.70,
            "metadata": {
                "signal_type": "sector_rotation",
                "sector": "technology",
                "relative_strength": 1.15,
                "fund_flow": "positive",
                "rotation_from": "financials"
            }
        }
        
        print("   🔄 Sector Rotation Signal (XLK)")
        result = await manager.send_manual_signal(sector_signal)
        print(f"      Result: {result}")
        
        # Signal Type 6: Risk-off signal (defensive)
        defensive_signal = {
            "symbol": "GLD",  # Gold ETF
            "action": "BUY",
            "quantity": 30,
            "price": 195.80,
            "strategy": "risk_management",
            "confidence": 0.85,
            "metadata": {
                "signal_type": "risk_off",
                "vix_level": 25.5,
                "market_fear": "high",
                "hedge_ratio": 0.3,
                "flight_to_safety": True
            }
        }
        
        print("   🛡️ Risk-Off Signal (GLD)")
        result = await manager.send_manual_signal(defensive_signal)
        print(f"      Result: {result}")
        
        print("\n✅ All signals sent successfully!")
        print("\n📊 Signal Types Demonstrated:")
        print("   1. Momentum Breakout")
        print("   2. Mean Reversion")
        print("   3. News Sentiment")
        print("   4. Options Flow")
        print("   5. Sector Rotation")
        print("   6. Risk Management")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the trading bot API is running on http://localhost:8000")
    
    finally:
        await manager.close()


async def strategy_management_demo():
    """Demonstrate strategy management features"""
    manager = StrategyManager()
    
    try:
        print("\n🎛️ Strategy Management Demo")
        print("=" * 40)
        
        # Get current strategies
        strategies = await manager.get_strategies()
        print("Current strategies:")
        for strategy in strategies.get("strategies", []):
            print(f"  - {strategy['name']}: {'🟢 Active' if strategy['is_active'] else '🔴 Inactive'}")
        
        # Demonstrate strategy activation/deactivation
        print("\nStrategy Control Examples:")
        
        # Activate a strategy
        print("  Activating SMA strategy...")
        result = await manager.activate_strategy("AAPL")
        print(f"    Result: {result}")
        
        # Deactivate a strategy
        print("  Deactivating RSI strategy...")
        result = await manager.deactivate_strategy("MSFT")
        print(f"    Result: {result}")
        
        # Update strategy parameters
        print("  Updating strategy parameters...")
        result = await manager.update_strategy(
            "AAPL",
            is_active=True,
            parameters={"short_window": 15, "long_window": 45}
        )
        print(f"    Result: {result}")
        
        print("\n✅ Strategy management demo completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await manager.close()


async def main():
    """Main function"""
    print("🤖 Advanced Trading Signal Demonstrations")
    print("=" * 60)
    
    # Run strategy demonstrations
    await demonstrate_strategies()
    
    # Run strategy management demo
    await strategy_management_demo()
    
    print("\n🎉 All demonstrations completed!")
    print("\n💡 Next Steps:")
    print("   1. Customize signal parameters")
    print("   2. Add your own strategies")
    print("   3. Implement real-time data feeds")
    print("   4. Set up automated signal generation")


if __name__ == "__main__":
    asyncio.run(main()) 