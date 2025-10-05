#!/usr/bin/env python3
"""
Options-Based Paper Trading Engine
This script runs options trading strategies in paper trading mode with realistic pricing
"""

import asyncio
import logging
import time
import random
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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

class OptionsPricingEngine:
    """Simple Black-Scholes approximation for options pricing"""
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 3% risk-free rate
        self.base_iv = 0.25  # 25% base implied volatility
    
    def calculate_option_price(self, 
                              current_price: float,
                              strike: float,
                              dte: int,
                              option_type: str,
                              iv: float = None) -> float:
        """Calculate option price using simplified Black-Scholes"""
        
        if iv is None:
            iv = self.base_iv
        
        # Avoid division by zero
        if dte <= 0:
            dte = 1
        
        # Time to expiration in years
        t = dte / 365.0
        
        # Calculate intrinsic value
        if option_type == 'call':
            intrinsic_value = max(0, current_price - strike)
        else:  # put
            intrinsic_value = max(0, strike - current_price)
        
        # Calculate time value (simplified)
        moneyness = current_price / strike
        
        # Time value based on moneyness and time to expiration
        if option_type == 'call':
            if moneyness > 1.1:  # Deep ITM
                time_value = current_price * 0.02 * math.sqrt(t) * iv
            elif moneyness < 0.9:  # Deep OTM
                time_value = current_price * 0.01 * math.sqrt(t) * iv
            else:  # ATM
                time_value = current_price * 0.05 * math.sqrt(t) * iv
        else:  # put
            if moneyness > 1.1:  # Deep OTM
                time_value = current_price * 0.01 * math.sqrt(t) * iv
            elif moneyness < 0.9:  # Deep ITM
                time_value = current_price * 0.02 * math.sqrt(t) * iv
            else:  # ATM
                time_value = current_price * 0.05 * math.sqrt(t) * iv
        
        return max(0.01, intrinsic_value + time_value)
    
    def calculate_iron_condor_premium(self, current_price: float, dte: int) -> float:
        """Calculate Iron Condor net premium received"""
        # Iron Condor: Sell OTM call spread + Sell OTM put spread
        
        # Call spread strikes (sell higher, buy even higher)
        call_sell_strike = current_price * 1.05  # 5% OTM
        call_buy_strike = current_price * 1.10   # 10% OTM
        
        # Put spread strikes (sell lower, buy even lower)
        put_sell_strike = current_price * 0.95   # 5% OTM
        put_buy_strike = current_price * 0.90    # 10% OTM
        
        # Calculate premiums
        call_sell_premium = self.calculate_option_price(current_price, call_sell_strike, dte, 'call')
        call_buy_premium = self.calculate_option_price(current_price, call_buy_strike, dte, 'call')
        put_sell_premium = self.calculate_option_price(current_price, put_sell_strike, dte, 'put')
        put_buy_premium = self.calculate_option_price(current_price, put_buy_strike, dte, 'put')
        
        # Net premium received
        net_premium = (call_sell_premium + put_sell_premium) - (call_buy_premium + put_buy_premium)
        
        return max(0.10, net_premium)  # Minimum $0.10 premium
    
    def calculate_butterfly_spread_premium(self, current_price: float, dte: int) -> float:
        """Calculate Butterfly Spread net premium paid"""
        # Butterfly: Buy 1 ATM, Sell 2 OTM, Buy 1 further OTM
        
        atm_strike = current_price
        otm_strike = current_price * 1.05  # 5% OTM
        further_otm_strike = current_price * 1.10  # 10% OTM
        
        # Calculate premiums
        atm_premium = self.calculate_option_price(current_price, atm_strike, dte, 'call')
        otm_premium = self.calculate_option_price(current_price, otm_strike, dte, 'call')
        further_otm_premium = self.calculate_option_price(current_price, further_otm_strike, dte, 'call')
        
        # Net premium paid
        net_premium = atm_premium + further_otm_premium - (2 * otm_premium)
        
        return max(0.05, net_premium)  # Minimum $0.05 premium
    
    def calculate_calendar_spread_premium(self, current_price: float, dte: int) -> float:
        """Calculate Calendar Spread net premium paid"""
        # Calendar: Sell near-term ATM, Buy far-term ATM
        
        near_term_premium = self.calculate_option_price(current_price, current_price, dte, 'call')
        far_term_premium = self.calculate_option_price(current_price, current_price, dte + 30, 'call')
        
        # Net premium paid
        net_premium = far_term_premium - near_term_premium
        
        return max(0.05, net_premium)  # Minimum $0.05 premium


class OptionsPaperTradingEngine:
    """Options-based paper trading engine with realistic strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio_value = config.get('initial_capital', 4000.0)
        self.total_trades = 0
        self.total_pnl = 0.0
        self.trades = []
        
        # Options strategies
        self.strategies = config.get('strategies', [
            'IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD'
        ])
        
        # Options symbols (underlying stocks)
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ'])
        
        self.trading_interval = config.get('trading_interval', 60)
        self.is_running = True
        
        # Options pricing engine
        self.pricing_engine = OptionsPricingEngine()
        
        # Strategy performance tracking
        self.strategy_performance = {strategy: {
            'trades': 0,
            'pnl': 0.0,
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0
        } for strategy in self.strategies}
        
        logger.info(f"🚀 Options Paper Trading Engine initialized with {len(self.strategies)} strategies")
        logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f}")
        logger.info(f"🎯 Symbols: {', '.join(self.symbols)}")
        logger.info(f"⏱️ Trading interval: {self.trading_interval} seconds")
    
    async def run(self):
        """Main options paper trading loop"""
        logger.info("🚀 Starting options paper trading engine...")
        
        while self.is_running:
            try:
                # Generate an options trade
                await self.generate_options_trade()
                
                # Update portfolio value
                self.update_portfolio()
                
                # Log status
                logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f} | Trades: {self.total_trades} | P&L: ${self.total_pnl:,.2f}")
                
                # Wait for next trading cycle
                await asyncio.sleep(self.trading_interval)
                
            except Exception as e:
                logger.error(f"Error in options paper trading loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def generate_options_trade(self):
        """Generate a simulated options trade"""
        if not self.is_running:
            return
        
        # Randomly select a strategy and symbol
        strategy = random.choice(self.strategies)
        symbol = random.choice(self.symbols)
        
        # Get current stock price
        current_price = self.get_simulated_price(symbol)
        
        # Calculate options trade parameters
        trade_params = self.calculate_options_trade(strategy, symbol, current_price)
        
        if not trade_params:
            logger.info(f"⏭️ Skipping trade: no valid options trade for {strategy} on {symbol}")
            return
        
        # Calculate P&L
        pnl = self.calculate_options_pnl(strategy, trade_params)
        
        # Create trade record
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': strategy,
            'action': trade_params['action'],
            'contracts': trade_params['contracts'],
            'premium': trade_params['premium'],
            'max_risk': trade_params['max_risk'],
            'dte': trade_params['dte'],
            'current_price': current_price,
            'pnl': pnl,
            'portfolio_value': self.portfolio_value,
            'trade_id': f"OPT_{int(time.time())}_{random.randint(1000, 9999)}"
        }
        
        # Add to trades list
        self.trades.append(trade)
        self.total_trades += 1
        self.total_pnl += pnl
        
        # Update strategy performance
        self.update_strategy_performance(strategy, pnl)
        
        logger.info(f"📈 Options Trade: {strategy} {trade_params['contracts']} contracts {symbol} @ ${current_price:.2f} | Premium: ${trade_params['premium']:.2f} | P&L: ${pnl:.2f}")
    
    def calculate_options_trade(self, strategy: str, symbol: str, current_price: float) -> Optional[Dict]:
        """Calculate options trade parameters based on strategy"""
        
        # Days to expiration (30-45 days for most strategies)
        dte = random.randint(30, 45)
        
        # Calculate number of contracts based on position sizing
        contracts = self.calculate_contracts_size(strategy, current_price)
        
        if contracts < 1:
            return None
        
        # Calculate strategy-specific parameters
        if strategy == 'IRON_CONDOR':
            premium = self.pricing_engine.calculate_iron_condor_premium(current_price, dte)
            max_risk = premium * 2  # Iron Condor max risk is typically 2x premium
            action = 'SELL'  # Net credit strategy
            
        elif strategy == 'BUTTERFLY_SPREAD':
            premium = self.pricing_engine.calculate_butterfly_spread_premium(current_price, dte)
            max_risk = premium  # Butterfly max risk equals premium paid
            action = 'BUY'  # Net debit strategy
            
        elif strategy == 'CALENDAR_SPREAD':
            premium = self.pricing_engine.calculate_calendar_spread_premium(current_price, dte)
            max_risk = premium  # Calendar max risk equals premium paid
            action = 'BUY'  # Net debit strategy
            
        else:
            return None
        
        return {
            'action': action,
            'contracts': contracts,
            'premium': premium,
            'max_risk': max_risk,
            'dte': dte
        }
    
    def calculate_contracts_size(self, strategy: str, current_price: float) -> int:
        """Calculate number of contracts based on portfolio value and risk management"""
        
        # Get max position size from config (default 12%)
        max_position_size = self.config.get('max_position_size', 0.12)
        max_risk_per_trade = self.config.get('max_risk_per_trade', 0.05)
        
        # Calculate maximum position value (12% of portfolio)
        max_position_value = self.portfolio_value * max_position_size
        
        # Calculate maximum risk per trade (5% of portfolio)
        max_risk_value = self.portfolio_value * max_risk_per_trade
        
        # Estimate premium per contract (rough estimate)
        if strategy == 'IRON_CONDOR':
            estimated_premium = current_price * 0.02  # ~2% of stock price
        elif strategy == 'BUTTERFLY_SPREAD':
            estimated_premium = current_price * 0.01  # ~1% of stock price
        elif strategy == 'CALENDAR_SPREAD':
            estimated_premium = current_price * 0.015  # ~1.5% of stock price
        else:
            estimated_premium = current_price * 0.01
        
        # Calculate max contracts by position size
        max_contracts_by_position = int(max_position_value / estimated_premium)
        
        # Calculate max contracts by risk
        max_contracts_by_risk = int(max_risk_value / estimated_premium)
        
        # Use the smaller limit
        max_contracts = min(max_contracts_by_position, max_contracts_by_risk)
        
        # Ensure minimum viable position (at least $50)
        min_position_value = 50.0
        min_contracts = int(min_position_value / estimated_premium)
        
        # Randomly select contracts between min and max
        if max_contracts < min_contracts:
            return 0
        
        contracts = random.randint(min_contracts, max_contracts)
        
        # Ensure we don't exceed available cash
        trade_value = contracts * estimated_premium
        if trade_value > self.portfolio_value * 0.95:  # Leave 5% cash buffer
            contracts = int((self.portfolio_value * 0.95) / estimated_premium)
        
        return max(0, contracts)
    
    def calculate_options_pnl(self, strategy: str, trade_params: Dict) -> float:
        """Calculate P&L for an options trade"""
        
        # Simplified P&L calculation based on strategy type
        base_return = random.uniform(-0.5, 1.0)  # -50% to +100% return
        
        if strategy == 'IRON_CONDOR':
            # Iron Condor: Limited profit, limited loss
            if base_return > 0:
                pnl = trade_params['premium'] * trade_params['contracts'] * min(1.0, base_return)
            else:
                pnl = -trade_params['max_risk'] * trade_params['contracts'] * min(1.0, abs(base_return))
                
        elif strategy == 'BUTTERFLY_SPREAD':
            # Butterfly: Limited profit, limited loss
            if base_return > 0:
                pnl = trade_params['max_risk'] * trade_params['contracts'] * min(1.0, base_return)
            else:
                pnl = -trade_params['premium'] * trade_params['contracts'] * min(1.0, abs(base_return))
                
        elif strategy == 'CALENDAR_SPREAD':
            # Calendar: Time decay benefit
            if base_return > 0:
                pnl = trade_params['max_risk'] * trade_params['contracts'] * min(1.0, base_return)
            else:
                pnl = -trade_params['premium'] * trade_params['contracts'] * min(1.0, abs(base_return))
        
        else:
            pnl = 0.0
        
        return round(pnl, 2)
    
    def get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for a symbol with realistic current prices"""
        # Current realistic prices (as of 2025)
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 308.0,
            'GOOGL': 140.0,
            'TSLA': 200.0,
            'NVDA': 400.0,
            'SPY': 450.0,
            'QQQ': 380.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add small random variation (±1% for more realistic simulation)
        variation = random.uniform(-0.01, 0.01)  # ±1%
        price = base_price * (1 + variation)
        
        return round(price, 2)
    
    def update_portfolio(self):
        """Update portfolio value based on trades"""
        # Simplified portfolio update
        self.portfolio_value = 4000.0 + self.total_pnl
    
    def update_strategy_performance(self, strategy: str, pnl: float):
        """Update strategy performance metrics"""
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
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'initial_capital': 4000.0,
            'current_value': self.portfolio_value,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': (self.total_pnl / 4000.0) * 100,
            'total_trades': self.total_trades,
            'strategies': list(self.strategy_performance.keys()),
            'recent_trades': self.trades[-10:] if self.trades else []
        }


async def main():
    """Main function to run options paper trading"""
    try:
        # Load configuration from command line argument or use defaults
        config = {
            'initial_capital': 4000.0,  # Updated to match live trading
            'max_position_size': 0.12,
            'max_risk_per_trade': 0.05,
            'trading_interval': 60,
            'strategies': ['IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD'],
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ'],
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
        
        # Create and run options paper trading engine
        engine = OptionsPaperTradingEngine(config)
        
        # Run the engine
        await engine.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Options paper trading stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in options paper trading: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())








