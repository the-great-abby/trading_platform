#!/usr/bin/env python3
"""
Paper Trading Setup Script
Handles the actual paper trading execution based on configuration
"""

import sys
import json
import time
import logging
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperTradingEngine:
    """Simple paper trading engine for demonstration"""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.portfolio_value = self.config.get('initial_capital', 2000.0)
        self.total_trades = 0
        self.total_pnl = 0.0
        self.active_positions = {}
        self.trade_history = []
        
        logger.info(f"🚀 Paper Trading Engine initialized with ${self.portfolio_value}")
        logger.info(f"📊 Strategies: {self.config.get('strategies', [])}")
        logger.info(f"📈 Symbols: {self.config.get('symbols', [])}")
    
    def calculate_strategy_signal(self, symbol: str, strategy: str) -> str:
        """Calculate trading signal based on strategy"""
        
        if strategy == "IronCondor":
            # Iron Condor: Look for range-bound, low volatility conditions
            # Increased probability for better testing
            if random.random() < 0.3:  # 30% chance of signal (increased from 10%)
                return "SELL_IRON_CONDOR"
        
        elif strategy == "ButterflySpread":
            # Butterfly Spread: Limited risk/reward strategy
            if random.random() < 0.25:  # 25% chance of signal
                return "SELL_BUTTERFLY_SPREAD"
        
        elif strategy == "CalendarSpread":
            # Calendar Spread: Time decay strategy
            if random.random() < 0.2:  # 20% chance of signal
                return "SELL_CALENDAR_SPREAD"
        
        elif strategy == "RegimeSwitching":
            # Regime Switching: Adaptive based on market conditions
            if random.random() < 0.15:  # 15% chance of signal
                return "BUY" if random.random() > 0.5 else "SELL"
        
        elif strategy == "BollingerBands":
            # Bollinger Bands: Mean reversion strategy
            if random.random() < 0.12:  # 12% chance of signal
                return "BUY" if random.random() > 0.5 else "SELL"
        
        return "HOLD"
    
    def execute_trade(self, symbol: str, action: str, strategy: str):
        """Execute a paper trade"""
        try:
            if action == "HOLD":
                return
            
            # Simulate trade execution
            current_price = random.uniform(50, 200)  # Simulate price
            
            if action == "SELL_IRON_CONDOR":
                # Iron Condor trade
                max_risk = self.portfolio_value * 0.05  # 5% of portfolio
                premium_collected = max_risk * 0.3  # Collect 30% of max risk as premium
                
                trade = {
                    'symbol': symbol,
                    'action': action,
                    'strategy': strategy,
                    'price': current_price,
                    'quantity': 1,  # 1 contract
                    'premium': premium_collected,
                    'max_risk': max_risk,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.portfolio_value += premium_collected
                self.total_trades += 1
                self.total_pnl += premium_collected
                
                logger.info(f"📊 {strategy} on {symbol}: Collected ${premium_collected:.2f} premium")
            
            elif action == "SELL_BUTTERFLY_SPREAD":
                # Butterfly Spread trade
                max_risk = self.portfolio_value * 0.03  # 3% of portfolio
                premium_collected = max_risk * 0.4  # Collect 40% of max risk as premium
                
                trade = {
                    'symbol': symbol,
                    'action': action,
                    'strategy': strategy,
                    'price': current_price,
                    'quantity': 1,  # 1 contract
                    'premium': premium_collected,
                    'max_risk': max_risk,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.portfolio_value += premium_collected
                self.total_trades += 1
                self.total_pnl += premium_collected
                
                logger.info(f"📊 {strategy} on {symbol}: Collected ${premium_collected:.2f} premium")
            
            elif action == "SELL_CALENDAR_SPREAD":
                # Calendar Spread trade
                max_risk = self.portfolio_value * 0.04  # 4% of portfolio
                premium_collected = max_risk * 0.35  # Collect 35% of max risk as premium
                
                trade = {
                    'symbol': symbol,
                    'action': action,
                    'strategy': strategy,
                    'price': current_price,
                    'quantity': 1,  # 1 contract
                    'premium': premium_collected,
                    'max_risk': max_risk,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.portfolio_value += premium_collected
                self.total_trades += 1
                self.total_pnl += premium_collected
                
                logger.info(f"📊 {strategy} on {symbol}: Collected ${premium_collected:.2f} premium")
            
            elif action in ["BUY", "SELL"]:
                # Stock trade
                position_size = self.portfolio_value * 0.1  # 10% of portfolio
                shares = int(position_size / current_price)
                
                if shares > 0:
                    trade = {
                        'symbol': symbol,
                        'action': action,
                        'strategy': strategy,
                        'price': current_price,
                        'quantity': shares,
                        'value': shares * current_price,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if action == "BUY":
                        self.portfolio_value -= shares * current_price
                        self.active_positions[symbol] = shares
                        logger.info(f"📈 {strategy} on {symbol}: Bought {shares} shares at ${current_price:.2f}")
                    else:  # SELL
                        if symbol in self.active_positions:
                            shares_to_sell = min(shares, self.active_positions[symbol])
                            self.portfolio_value += shares_to_sell * current_price
                            self.active_positions[symbol] -= shares_to_sell
                            if self.active_positions[symbol] == 0:
                                del self.active_positions[symbol]
                            logger.info(f"📉 {strategy} on {symbol}: Sold {shares_to_sell} shares at ${current_price:.2f}")
                    
                    self.total_trades += 1
            
            self.trade_history.append(trade)
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    async def run_trading_cycle(self):
        """Run one trading cycle"""
        logger.info(f"🔄 Running trading cycle - Portfolio: ${self.portfolio_value:.2f}")
        
        strategies = self.config.get('strategies', [])
        symbols = self.config.get('symbols', [])
        
        for symbol in symbols:
            for strategy in strategies:
                signal = self.calculate_strategy_signal(symbol, strategy)
                self.execute_trade(symbol, signal, strategy)
        
        # Update portfolio value with any unrealized gains/losses
        for symbol, shares in self.active_positions.items():
            current_price = random.uniform(50, 200)  # Simulate price movement
            unrealized_pnl = shares * (current_price - 100) * 0.01  # Small random movement
            self.portfolio_value += unrealized_pnl
    
    async def run(self):
        """Main trading loop"""
        trading_interval = self.config.get('trading_interval', 300)  # 5 minutes default
        
        logger.info(f"🚀 Starting paper trading with {trading_interval}s intervals")
        
        try:
            while True:
                await self.run_trading_cycle()
                await asyncio.sleep(trading_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Paper trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Paper trading error: {e}")

async def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_paper_trading.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        engine = PaperTradingEngine(config_file)
        await engine.run()
    except Exception as e:
        logger.error(f"Failed to start paper trading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


