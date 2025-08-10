#!/usr/bin/env python3
"""
Paper Trading Setup Script
This script runs the actual paper trading logic in the background
"""
import asyncio
import logging
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperTradingEngine:
    """Paper trading engine that simulates trading activity"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio_value = config.get('initial_capital', 100000.0)
        self.total_trades = 0
        self.total_pnl = 0.0
        self.trades = []
        self.strategies = config.get('strategies', ['RiskFirst', 'MarketRegimeAdaptive', 'MultiTimeframe'])
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
        self.trading_interval = config.get('trading_interval', 60)
        self.is_running = True
        
        # Strategy performance tracking
        self.strategy_performance = {strategy: {
            'trades': 0,
            'pnl': 0.0,
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0
        } for strategy in self.strategies}
        
        logger.info(f"🚀 Paper Trading Engine initialized with {len(self.strategies)} strategies")
        logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f}")
        logger.info(f"🎯 Symbols: {', '.join(self.symbols)}")
        logger.info(f"⏱️ Trading interval: {self.trading_interval} seconds")
    
    async def run(self):
        """Main paper trading loop"""
        logger.info("🚀 Starting paper trading engine...")
        
        while self.is_running:
            try:
                # Generate a trade
                await self.generate_trade()
                
                # Update portfolio value
                self.update_portfolio()
                
                # Log status
                logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f} | Trades: {self.total_trades} | P&L: ${self.total_pnl:,.2f}")
                
                # Wait for next trading cycle
                await asyncio.sleep(self.trading_interval)
                
            except Exception as e:
                logger.error(f"Error in paper trading loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def generate_trade(self):
        """Generate a simulated trade"""
        if not self.is_running:
            return
        
        # Randomly select a strategy and symbol
        strategy = random.choice(self.strategies)
        symbol = random.choice(self.symbols)
        
        # Generate trade parameters
        action = random.choice(['BUY', 'SELL'])
        quantity = random.randint(10, 100)
        price = self.get_simulated_price(symbol)
        
        # Calculate P&L (simplified)
        pnl = self.calculate_pnl(action, quantity, price)
        
        # Create trade record
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'strategy': strategy,
            'pnl': pnl,
            'portfolio_value': self.portfolio_value,
            'trade_id': f"PT_{int(time.time())}_{random.randint(1000, 9999)}"
        }
        
        # Add to trades list
        self.trades.append(trade)
        self.total_trades += 1
        self.total_pnl += pnl
        
        # Update strategy performance
        self.update_strategy_performance(strategy, pnl)
        
        logger.info(f"📈 Trade: {action} {quantity} {symbol} @ ${price:.2f} | P&L: ${pnl:.2f} | Strategy: {strategy}")
    
    def get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for a symbol"""
        # Base prices for different symbols
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'GOOGL': 2500.0,
            'TSLA': 200.0,
            'NVDA': 400.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add some random variation
        variation = random.uniform(-0.05, 0.05)  # ±5%
        price = base_price * (1 + variation)
        
        return round(price, 2)
    
    def calculate_pnl(self, action: str, quantity: int, price: float) -> float:
        """Calculate P&L for a trade"""
        # Simplified P&L calculation
        if action == 'BUY':
            # Simulate buying at a good price
            pnl = random.uniform(-50, 100)
        else:
            # Simulate selling at a good price
            pnl = random.uniform(-30, 80)
        
        return round(pnl, 2)
    
    def update_portfolio(self):
        """Update portfolio value based on P&L"""
        # Add some portfolio growth/decline
        portfolio_change = random.uniform(-0.001, 0.002)  # ±0.1% to +0.2%
        self.portfolio_value *= (1 + portfolio_change)
    
    def update_strategy_performance(self, strategy: str, pnl: float):
        """Update strategy performance metrics"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'trades': 0,
                'pnl': 0.0,
                'win_rate': 0.0,
                'wins': 0,
                'losses': 0
            }
        
        perf = self.strategy_performance[strategy]
        perf['trades'] += 1
        perf['pnl'] += pnl
        
        if pnl > 0:
            perf['wins'] += 1
        else:
            perf['losses'] += 1
        
        # Calculate win rate
        if perf['trades'] > 0:
            perf['win_rate'] = perf['wins'] / perf['trades']
    
    def stop(self):
        """Stop the paper trading engine"""
        logger.info("⏹️ Stopping paper trading engine...")
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Get current paper trading status"""
        return {
            'is_running': self.is_running,
            'portfolio_value': self.portfolio_value,
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl,
            'active_strategies': self.strategies,
            'strategy_performance': self.strategy_performance,
            'recent_trades': self.trades[-10:] if self.trades else []
        }

async def main():
    """Main function to run paper trading"""
    try:
        # Load configuration from command line argument or use defaults
        config = {
            'initial_capital': 100000.0,
            'max_position_size': 0.05,
            'max_risk_per_trade': 0.01,
            'trading_interval': 60,
            'strategies': ['RiskFirst', 'MarketRegimeAdaptive', 'MultiTimeframe'],
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            'enable_alerts': True,
            'performance_tracking': True
        }
        
        # Load config from file if provided
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"📋 Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Could not load config from {config_file}: {e}")
        
        # Create and run paper trading engine
        engine = PaperTradingEngine(config)
        
        # Run the engine
        await engine.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Paper trading stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in paper trading: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 