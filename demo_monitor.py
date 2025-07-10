#!/usr/bin/env python3
"""
Demo script for Space Trading Station Monitor
Shows how the monitor works with simulated trading data
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

# Add the src directory to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.space_station_monitor import SpaceStationMonitor
from src.core.types import TradeSignal, Trade


@dataclass
class SimulatedTrade:
    """Simulated trade for demo"""
    symbol: str
    action: str
    quantity: float
    price: float
    pnl: float
    strategy: str
    timestamp: datetime


@dataclass
class SimulatedSignal:
    """Simulated signal for demo"""
    symbol: str
    action: str
    quantity: float
    price: float
    strategy: str
    confidence: float
    timestamp: datetime


class SpaceStationDemo:
    """Demo class for Space Trading Station Monitor"""
    
    def __init__(self):
        self.monitor = SpaceStationMonitor(refresh_interval=2)
        self.is_running = False
        
        # Demo data
        self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
        self.strategies = [
            'RSI_AI_Enhanced',
            'MACD_AI_Enhanced', 
            'BollingerBands_AI_Enhanced',
            'News_Enhanced_Strategy',
            'SMA_Crossover_AI_Enhanced'
        ]
        
    async def start_demo(self):
        """Start the demo with simulated data"""
        print("🚀 SPACE TRADING STATION DEMO")
        print("=" * 50)
        print("This is ORION, Mission Control.")
        print("Demonstrating real-time trading performance monitoring...")
        print()
        
        self.is_running = True
        
        # Start the monitor
        await self.monitor.start_monitoring()
        
        # Start generating simulated data
        await self._generate_simulated_data()
    
    async def stop_demo(self):
        """Stop the demo"""
        self.is_running = False
        await self.monitor.stop_monitoring()
    
    async def _generate_simulated_data(self):
        """Generate simulated trading data"""
        trade_id = 1
        
        while self.is_running:
            try:
                # Generate random trades
                if random.random() < 0.3:  # 30% chance of trade
                    trade = self._generate_random_trade(trade_id)
                    self.monitor.add_trade(trade)
                    trade_id += 1
                
                # Generate random signals
                if random.random() < 0.5:  # 50% chance of signal
                    signal = self._generate_random_signal()
                    self.monitor.add_signal(signal)
                
                # Wait before next iteration
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Error generating demo data: {e}")
                break
    
    def _generate_random_trade(self, trade_id: int) -> SimulatedTrade:
        """Generate a random trade"""
        symbol = random.choice(self.symbols)
        action = random.choice(['BUY', 'SELL'])
        quantity = random.uniform(10, 100)
        price = random.uniform(50, 500)
        pnl = random.uniform(-1000, 1000)  # Random P&L
        strategy = random.choice(self.strategies)
        
        return SimulatedTrade(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            pnl=pnl,
            strategy=strategy,
            timestamp=datetime.now()
        )
    
    def _generate_random_signal(self) -> SimulatedSignal:
        """Generate a random trading signal"""
        symbol = random.choice(self.symbols)
        action = random.choice(['BUY', 'SELL'])
        quantity = random.uniform(10, 100)
        price = random.uniform(50, 500)
        strategy = random.choice(self.strategies)
        confidence = random.uniform(0.5, 0.95)
        
        return SimulatedSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            strategy=strategy,
            confidence=confidence,
            timestamp=datetime.now()
        )


async def main():
    """Main demo function"""
    demo = SpaceStationDemo()
    
    try:
        await demo.start_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo shutdown initiated by user")
        await demo.stop_demo()
    except Exception as e:
        print(f"❌ Demo error: {e}")
        await demo.stop_demo()


if __name__ == "__main__":
    print("🚀 Starting Space Trading Station Monitor Demo...")
    print("This will show simulated trading data in real-time.")
    print("Press Ctrl+C to exit.")
    print()
    
    asyncio.run(main()) 