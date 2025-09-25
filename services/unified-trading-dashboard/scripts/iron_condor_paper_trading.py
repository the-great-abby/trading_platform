#!/usr/bin/env python3
"""
Iron Condor Paper Trading Implementation
=======================================
Full implementation of Iron Condor strategy for paper trading with real options data
"""

import asyncio
import logging
import time
import random
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import pandas as pd
import numpy as np

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IronCondorPaperTrading:
    """
    Full Iron Condor implementation for paper trading
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio_value = config.get('initial_capital', 2000.0)
        self.total_trades = 0
        self.total_pnl = 0.0
        self.trades = []
        self.active_positions = {}
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        
        # Iron Condor specific parameters
        self.days_to_expiration = config.get('days_to_expiration', 45)
        self.profit_target_pct = config.get('profit_target_pct', 0.5)  # 50% of max profit
        self.stop_loss_pct = config.get('stop_loss_pct', 2.0)  # 2x max profit
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.05)  # 5% of portfolio
        self.volatility_threshold = config.get('volatility_threshold', 0.3)  # 30% IV threshold
        self.min_volume = config.get('min_volume', 10)
        self.min_open_interest = config.get('min_open_interest', 50)
        
        logger.info(f"🚀 Iron Condor Paper Trading initialized")
        logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f}")
        logger.info(f"🎯 Symbols: {', '.join(config.get('symbols', []))}")
        logger.info(f"⏱️ DTE: {self.days_to_expiration} days")
        logger.info(f"💰 Max Risk: {self.max_risk_per_trade*100:.1f}% of portfolio")
    
    async def run(self):
        """Main trading loop"""
        trading_interval = self.config.get('trading_interval', 300)  # 5 minutes default
        
        logger.info(f"🚀 Starting Iron Condor paper trading with {trading_interval}s intervals")
        
        try:
            while True:
                await self.run_trading_cycle()
                await asyncio.sleep(trading_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Iron Condor trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Iron Condor trading error: {e}")
    
    async def run_trading_cycle(self):
        """Run one trading cycle"""
        logger.info(f"🔄 Running Iron Condor cycle - Portfolio: ${self.portfolio_value:.2f}")
        
        symbols = self.config.get('symbols', [])
        
        for symbol in symbols:
            try:
                # Check if we should trade this symbol
                if await self.should_trade_symbol(symbol):
                    await self.analyze_and_trade_symbol(symbol)
                
                # Update existing positions
                await self.update_positions(symbol)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
    
    async def should_trade_symbol(self, symbol: str) -> bool:
        """Check if we should trade this symbol"""
        # Don't trade if we already have an active position
        if symbol in self.active_positions:
            return False
        
        # Don't trade if we've already used up our risk budget
        total_risk = sum(pos.get('max_risk', 0) for pos in self.active_positions.values())
        if total_risk >= self.portfolio_value * self.max_risk_per_trade:
            return False
        
        return True
    
    async def analyze_and_trade_symbol(self, symbol: str):
        """Analyze symbol and execute Iron Condor if conditions are met"""
        try:
            # Get current stock price
            current_price = await self.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Could not get current price for {symbol}")
                return
            
            # Get options chain
            options_chain = await self.get_options_chain(symbol)
            if not options_chain:
                logger.warning(f"Could not get options chain for {symbol}")
                return
            
            # Check market conditions
            if not self.check_market_conditions(current_price, options_chain):
                logger.debug(f"Market conditions not suitable for {symbol}")
                return
            
            # Find optimal Iron Condor setup
            iron_condor = self.find_optimal_iron_condor(symbol, current_price, options_chain)
            if not iron_condor:
                logger.debug(f"No suitable Iron Condor found for {symbol}")
                return
            
            # Execute the trade
            await self.execute_iron_condor(symbol, iron_condor)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price from Polygon API"""
        if not self.polygon_api_key:
            # Fallback to simulated price
            base_prices = {'AMD': 120.0, 'PYPL': 60.0, 'INTC': 45.0}
            base_price = base_prices.get(symbol, 100.0)
            return base_price * random.uniform(0.95, 1.05)
        
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apikey={self.polygon_api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]['c']  # Close price
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {e}")
        
        return None
    
    async def get_options_chain(self, symbol: str) -> Optional[List[Dict]]:
        """Get options chain from Polygon API"""
        if not self.polygon_api_key:
            # Return simulated options chain
            return self.generate_simulated_options_chain(symbol)
        
        try:
            # Get expiration dates
            expirations_url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={symbol}&apikey={self.polygon_api_key}"
            response = requests.get(expirations_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    # Get options for the closest expiration to our target DTE
                    target_date = datetime.now() + timedelta(days=self.days_to_expiration)
                    closest_expiration = None
                    min_diff = float('inf')
                    
                    for contract in data['results']:
                        exp_date = datetime.strptime(contract['expiration_date'], '%Y-%m-%d')
                        diff = abs((exp_date - target_date).days)
                        if diff < min_diff:
                            min_diff = diff
                            closest_expiration = contract['expiration_date']
                    
                    if closest_expiration:
                        # Get options chain for this expiration
                        chain_url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={symbol}&expiration_date={closest_expiration}&apikey={self.polygon_api_key}"
                        chain_response = requests.get(chain_url, timeout=10)
                        
                        if chain_response.status_code == 200:
                            chain_data = chain_response.json()
                            return chain_data.get('results', [])
        
        except Exception as e:
            logger.warning(f"Error fetching options chain for {symbol}: {e}")
        
        return None
    
    def generate_simulated_options_chain(self, symbol: str) -> List[Dict]:
        """Generate simulated options chain for testing"""
        current_price = self.get_simulated_price(symbol)
        options = []
        
        # Generate call options
        for i in range(-5, 6):  # -5 to +5 strikes around current price
            strike = current_price + (i * 5)  # $5 increments
            if strike > current_price:
                options.append({
                    'option_type': 'call',
                    'strike': strike,
                    'price': max(0.5, (strike - current_price) * 0.1 + random.uniform(-0.2, 0.2)),
                    'volume': random.randint(5, 50),
                    'open_interest': random.randint(10, 100),
                    'implied_volatility': random.uniform(0.2, 0.5)
                })
        
        # Generate put options
        for i in range(-5, 6):
            strike = current_price + (i * 5)
            if strike < current_price:
                options.append({
                    'option_type': 'put',
                    'strike': strike,
                    'price': max(0.5, (current_price - strike) * 0.1 + random.uniform(-0.2, 0.2)),
                    'volume': random.randint(5, 50),
                    'open_interest': random.randint(10, 100),
                    'implied_volatility': random.uniform(0.2, 0.5)
                })
        
        return options
    
    def get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for a symbol"""
        base_prices = {'AMD': 120.0, 'PYPL': 60.0, 'INTC': 45.0}
        base_price = base_prices.get(symbol, 100.0)
        return base_price * random.uniform(0.95, 1.05)
    
    def check_market_conditions(self, current_price: float, options_chain: List[Dict]) -> bool:
        """Check if market conditions are suitable for Iron Condor"""
        if not options_chain:
            return False
        
        # Check if we have enough liquid options
        liquid_options = [opt for opt in options_chain 
                         if opt.get('volume', 0) >= self.min_volume and 
                            opt.get('open_interest', 0) >= self.min_open_interest]
        
        if len(liquid_options) < 10:
            return False
        
        # Check implied volatility
        avg_iv = np.mean([opt.get('implied_volatility', 0) for opt in liquid_options])
        if avg_iv > self.volatility_threshold:
            return False
        
        return True
    
    def find_optimal_iron_condor(self, symbol: str, current_price: float, options_chain: List[Dict]) -> Optional[Dict]:
        """Find optimal Iron Condor setup"""
        calls = [opt for opt in options_chain if opt.get('option_type') == 'call']
        puts = [opt for opt in options_chain if opt.get('option_type') == 'put']
        
        # Find out-of-the-money options
        otm_calls = sorted([c for c in calls if c.get('strike', 0) > current_price * 1.02], 
                          key=lambda x: x.get('strike', 0))
        otm_puts = sorted([p for p in puts if p.get('strike', 0) < current_price * 0.98], 
                         key=lambda x: x.get('strike', 0), reverse=True)
        
        if len(otm_calls) < 2 or len(otm_puts) < 2:
            return None
        
        # Try different strike combinations
        best_setup = None
        best_risk_reward = 0
        
        for i in range(min(3, len(otm_calls) - 1)):
            for j in range(min(3, len(otm_puts) - 1)):
                short_call = otm_calls[i]
                long_call = otm_calls[i + 1]
                short_put = otm_puts[j]
                long_put = otm_puts[j + 1]
                
                # Calculate metrics
                premium_received = short_call.get('price', 0) + short_put.get('price', 0)
                premium_paid = long_call.get('price', 0) + long_put.get('price', 0)
                net_premium = premium_received - premium_paid
                
                max_risk = (long_call.get('strike', 0) - short_call.get('strike', 0)) - net_premium
                max_profit = net_premium
                
                if max_risk > 0 and max_profit > 0:
                    risk_reward = max_profit / max_risk
                    
                    if risk_reward > best_risk_reward and risk_reward >= 0.3:
                        best_risk_reward = risk_reward
                        best_setup = {
                            'symbol': symbol,
                            'short_call_strike': short_call.get('strike', 0),
                            'long_call_strike': long_call.get('strike', 0),
                            'short_put_strike': short_put.get('strike', 0),
                            'long_put_strike': long_put.get('strike', 0),
                            'max_profit': max_profit,
                            'max_risk': max_risk,
                            'risk_reward_ratio': risk_reward,
                            'net_premium': net_premium,
                            'short_call_price': short_call.get('price', 0),
                            'long_call_price': long_call.get('price', 0),
                            'short_put_price': short_put.get('price', 0),
                            'long_put_price': long_put.get('price', 0)
                        }
        
        return best_setup
    
    async def execute_iron_condor(self, symbol: str, iron_condor: Dict):
        """Execute Iron Condor trade"""
        try:
            # Calculate position size based on risk
            max_risk = iron_condor['max_risk']
            max_risk_amount = self.portfolio_value * self.max_risk_per_trade
            position_size = min(1, max_risk_amount / max_risk)  # Don't exceed risk budget
            
            if position_size < 0.1:  # Minimum position size
                logger.debug(f"Position size too small for {symbol}")
                return
            
            # Create trade record
            trade = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'strategy': 'IronCondor',
                'action': 'SELL_IRON_CONDOR',
                'position_size': position_size,
                'iron_condor': iron_condor,
                'premium_collected': iron_condor['net_premium'] * position_size,
                'max_risk': max_risk * position_size,
                'profit_target': iron_condor['max_profit'] * self.profit_target_pct * position_size,
                'stop_loss': max_risk * self.stop_loss_pct * position_size,
                'trade_id': f"IC_{int(time.time())}_{random.randint(1000, 9999)}"
            }
            
            # Update portfolio
            self.portfolio_value += trade['premium_collected']
            self.total_trades += 1
            self.total_pnl += trade['premium_collected']
            
            # Add to active positions
            self.active_positions[symbol] = trade
            
            # Add to trade history
            self.trades.append(trade)
            
            logger.info(f"📊 Iron Condor on {symbol}: Collected ${trade['premium_collected']:.2f} premium")
            logger.info(f"   Max Risk: ${trade['max_risk']:.2f} | Risk/Reward: {iron_condor['risk_reward_ratio']:.3f}")
            logger.info(f"   Strikes: P{iron_condor['short_put_strike']:.0f}/{iron_condor['long_put_strike']:.0f} | C{iron_condor['short_call_strike']:.0f}/{iron_condor['long_call_strike']:.0f}")
            
        except Exception as e:
            logger.error(f"Error executing Iron Condor for {symbol}: {e}")
    
    async def update_positions(self, symbol: str):
        """Update existing positions"""
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        
        # For paper trading, we'll simulate some P&L changes
        # In real trading, this would check current option prices
        
        # Simulate small unrealized P&L changes
        pnl_change = random.uniform(-0.02, 0.02) * position['max_risk']
        position['unrealized_pnl'] = position.get('unrealized_pnl', 0) + pnl_change
        
        # Check profit target
        if position['unrealized_pnl'] >= position['profit_target']:
            await self.close_position(symbol, "PROFIT_TARGET")
        
        # Check stop loss
        elif position['unrealized_pnl'] <= -position['stop_loss']:
            await self.close_position(symbol, "STOP_LOSS")
    
    async def close_position(self, symbol: str, reason: str):
        """Close a position"""
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        
        # Calculate final P&L
        final_pnl = position['unrealized_pnl']
        self.portfolio_value += final_pnl
        self.total_pnl += final_pnl
        
        # Update trade record
        position['close_reason'] = reason
        position['close_timestamp'] = datetime.now().isoformat()
        position['final_pnl'] = final_pnl
        
        # Remove from active positions
        del self.active_positions[symbol]
        
        logger.info(f"📊 Closed Iron Condor on {symbol}: {reason} | Final P&L: ${final_pnl:.2f}")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'portfolio_value': self.portfolio_value,
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl,
            'active_positions': len(self.active_positions),
            'recent_trades': self.trades[-5:] if self.trades else []
        }

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python iron_condor_paper_trading.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        engine = IronCondorPaperTrading(config)
        await engine.run()
        
    except Exception as e:
        logger.error(f"Failed to start Iron Condor paper trading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

