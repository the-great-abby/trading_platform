#!/usr/bin/env python3
"""
Improved Capital Allocation for Options Trading
==============================================
Implements advanced capital allocation strategies to maximize options trading efficiency
"""

import asyncio
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedCapitalAllocator:
    """Advanced capital allocation system for options trading"""
    
    def __init__(self, initial_capital: float = 4000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.allocated_capital = 0.0  # Capital tied up in positions
        self.available_capital = initial_capital
        self.trades = []
        self.active_positions = []
        
        # Capital allocation parameters
        self.max_portfolio_utilization = 0.80  # Use max 80% of portfolio
        self.min_cash_reserve = 0.20  # Keep 20% in cash
        self.max_position_size = 0.15  # Max 15% per position
        self.max_risk_per_trade = 0.05  # Max 5% risk per trade
        
        # Dynamic sizing parameters
        self.capital_efficiency_threshold = 0.70  # Increase sizing when utilization > 70%
        self.capital_scarcity_threshold = 0.30  # Decrease sizing when utilization < 30%
        
        logger.info(f"🚀 Advanced Capital Allocator initialized with ${initial_capital:,.2f}")

    def calculate_available_capital(self) -> float:
        """Calculate available capital for new trades"""
        self.allocated_capital = sum(pos['trade_value'] for pos in self.active_positions)
        self.available_capital = self.current_capital - self.allocated_capital
        
        # Ensure minimum cash reserve
        min_cash = self.current_capital * self.min_cash_reserve
        self.available_capital = max(0, self.available_capital - min_cash)
        
        return self.available_capital

    def calculate_dynamic_position_size(self, symbol: str, strategy: str, premium: float) -> int:
        """Calculate position size based on available capital and market conditions"""
        
        available_capital = self.calculate_available_capital()
        
        if available_capital <= 0:
            return 0
        
        # Base position sizing
        max_position_value = min(
            self.current_capital * self.max_position_size,
            available_capital * 0.5  # Use max 50% of available capital
        )
        
        max_risk_value = self.current_capital * self.max_risk_per_trade
        
        # Calculate max contracts
        max_contracts_position = int(max_position_value / (premium * 100))
        max_contracts_risk = int(max_risk_value / (premium * 100))
        
        max_contracts = min(max_contracts_position, max_contracts_risk)
        
        if max_contracts < 1:
            return 0
        
        # Dynamic sizing based on capital utilization
        utilization = self.allocated_capital / self.current_capital
        
        if utilization > self.capital_efficiency_threshold:
            # High utilization - be more conservative
            contracts = random.randint(1, min(max_contracts, 2))
        elif utilization < self.capital_scarcity_threshold:
            # Low utilization - can be more aggressive
            contracts = random.randint(1, min(max_contracts, 4))
        else:
            # Normal utilization
            contracts = random.randint(1, min(max_contracts, 3))
        
        return contracts

    def can_open_new_position(self) -> bool:
        """Check if we can open a new position"""
        available_capital = self.calculate_available_capital()
        
        # Need minimum capital for a meaningful trade
        min_trade_capital = self.current_capital * 0.05  # 5% minimum
        
        return (
            available_capital >= min_trade_capital and
            len(self.active_positions) < 5  # Max 5 positions
        )

    def optimize_capital_allocation(self):
        """Optimize capital allocation by closing low-performing positions early"""
        
        if len(self.active_positions) < 3:
            return  # Don't optimize with few positions
        
        # Find positions that are close to profit targets
        positions_to_close = []
        
        for position in self.active_positions:
            # Calculate current P&L percentage
            current_pnl_pct = (position['pnl'] / (position['trade_value'] * 0.1))
            
            # Close positions that are close to profit target (8% instead of 10%)
            if current_pnl_pct >= 0.08:  # 8% profit target
                positions_to_close.append(position)
                logger.info(f"🎯 Early exit for capital optimization: {position['symbol']} {position['strategy']} - {current_pnl_pct:.1%} profit")
        
        # Close positions to free up capital
        for position in positions_to_close:
            self.close_position(position, "capital_optimization")

    def close_position(self, position: Dict, reason: str):
        """Close a position and free up capital"""
        position['status'] = 'closed'
        position['exit_reason'] = reason
        position['exit_timestamp'] = datetime.now().isoformat()
        
        # Update capital
        self.current_capital += position['pnl']
        
        # Remove from active positions
        self.active_positions.remove(position)
        
        logger.info(f"📤 Position closed ({reason}): {position['strategy']} {position['contracts']} contracts {position['symbol']} | P&L: ${position['pnl']:+.2f}")

class ImprovedOptionsBacktestEngine:
    """Options backtest engine with advanced capital allocation"""
    
    def __init__(self, initial_capital: float = 4000.0):
        self.capital_allocator = AdvancedCapitalAllocator(initial_capital)
        
        # Options strategies
        self.strategies = [
            'IRON_CONDOR',
            'BUTTERFLY_SPREAD', 
            'CALENDAR_SPREAD',
            'STRADDLE',
            'STRANGLE'
        ]
        
        # Symbols to trade
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 
            'SPY', 'QQQ', 'AMZN', 'META', 'NFLX'
        ]
        
        # Historical price ranges
        self.price_ranges = {
            'AAPL': (150, 200), 'MSFT': (300, 450), 'GOOGL': (100, 180), 
            'TSLA': (150, 300), 'NVDA': (200, 900), 'SPY': (400, 600),
            'QQQ': (300, 500), 'AMZN': (100, 200), 'META': (200, 500), 'NFLX': (300, 700)
        }
        
        # Exit strategy configuration
        self.max_holding_days = 30
        self.profit_target_pct = 0.10  # 10% profit target
        self.stop_loss_pct = 0.05  # 5% stop loss
        
        logger.info(f"🚀 Improved Options Backtest Engine initialized")

    def get_realistic_price(self, symbol: str, day: int) -> float:
        """Generate realistic price movement"""
        base_range = self.price_ranges.get(symbol, (100, 200))
        base_price = (base_range[0] + base_range[1]) / 2
        
        daily_change = random.uniform(-0.03, 0.03)
        price = base_price * (1 + daily_change)
        
        return round(price, 2)

    def get_realistic_options_price(self, symbol: str, strategy: str, current_price: float) -> tuple:
        """Generate realistic options premium and Greeks"""
        
        if strategy == 'IRON_CONDOR':
            premium = random.uniform(0.50, 2.00)
        elif strategy == 'BUTTERFLY_SPREAD':
            premium = random.uniform(0.30, 1.50)
        elif strategy == 'CALENDAR_SPREAD':
            premium = random.uniform(0.40, 1.80)
        elif strategy == 'STRADDLE':
            premium = random.uniform(1.00, 4.00)
        elif strategy == 'STRANGLE':
            premium = random.uniform(0.50, 2.50)
        else:
            premium = random.uniform(0.50, 2.00)
        
        greeks = {
            'delta': random.uniform(-0.5, 0.5),
            'gamma': random.uniform(0.01, 0.05),
            'theta': random.uniform(-0.05, -0.01),
            'vega': random.uniform(0.1, 0.3)
        }
        
        return round(premium, 2), greeks

    def simulate_pnl(self, strategy: str, contracts: int, premium: float, greeks: Dict) -> float:
        """Simulate realistic P&L for options trade with proper win/loss ratios"""
        
        # Realistic win rates by strategy (from paper_trading_strategies.yaml)
        win_rates = {
            'IRON_CONDOR': 0.65,        # 65% win rate - high probability
            'STRADDLE': 0.55,           # 55% win rate
            'STRANGLE': 0.55,           # 55% win rate  
            'CALENDAR_SPREAD': 0.62,    # 62% win rate - steady income
            'BUTTERFLY': 0.60,          # 60% win rate
            'DEFAULT': 0.50             # 50% win rate
        }
        
        win_rate = win_rates.get(strategy, 0.50)
        is_winner = random.random() < win_rate
        
        if is_winner:
            # Winning trade - profit from premium/theta decay
            if strategy in ['IRON_CONDOR', 'STRADDLE', 'STRANGLE']:
                base_pnl = premium * contracts * 100 * random.uniform(0.1, 0.4)
            else:
                base_pnl = premium * contracts * 100 * random.uniform(0.05, 0.3)
        else:
            # Losing trade - realistic loss patterns
            if strategy == 'IRON_CONDOR':
                # Iron condor has defined max loss (spread width)
                base_pnl = -premium * contracts * 100 * random.uniform(0.8, 1.5)
            elif strategy in ['STRADDLE', 'STRANGLE']:
                # Straddles/strangles can lose premium + adverse price movement
                base_pnl = -premium * contracts * 100 * random.uniform(0.5, 1.2)
            else:
                # Other strategies - moderate losses
                base_pnl = -premium * contracts * 100 * random.uniform(0.3, 0.8)
        
        random_factor = random.uniform(0.8, 1.2)
        total_pnl = base_pnl * random_factor
        
        # Cap P&L to be realistic (max 5% of capital per trade)
        max_realistic_pnl = self.capital_allocator.current_capital * 0.05
        min_realistic_loss = -self.capital_allocator.current_capital * 0.08  # Max 8% loss
        total_pnl = max(min(total_pnl, max_realistic_pnl), min_realistic_loss)
        
        return round(total_pnl, 2)

    def generate_options_trade(self, day: int) -> Optional[Dict]:
        """Generate a realistic options trade with improved capital allocation"""
        
        # Check if we can open a new position
        if not self.capital_allocator.can_open_new_position():
            return None
        
        # Select random strategy and symbol
        strategy = random.choice(self.strategies)
        symbol = random.choice(self.symbols)
        
        # Get realistic current price
        current_price = self.get_realistic_price(symbol, day)
        
        # Generate realistic options pricing
        premium, greeks = self.get_realistic_options_price(symbol, strategy, current_price)
        
        # Calculate position size using advanced capital allocation
        contracts = self.capital_allocator.calculate_dynamic_position_size(symbol, strategy, premium)
        
        if contracts == 0:
            return None
        
        # Simulate P&L
        pnl = self.simulate_pnl(strategy, contracts, premium, greeks)
        
        # Calculate trade value
        trade_value = contracts * premium * 100
        position_pct = (trade_value / self.capital_allocator.current_capital) * 100
        
        # Create trade record
        trade = {
            'day': day,
            'symbol': symbol,
            'strategy': strategy,
            'contracts': contracts,
            'premium': premium,
            'current_price': current_price,
            'trade_value': trade_value,
            'pnl': pnl,
            'position_pct': position_pct,
            'greeks': greeks,
            'status': 'open',
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to active positions
        self.capital_allocator.active_positions.append(trade)
        
        logger.info(f"Day {day}: {strategy} {contracts} contracts {symbol} @ ${current_price:.2f} | Premium: ${premium:.2f} | P&L: ${pnl:+.2f} | Capital Util: {(self.capital_allocator.allocated_capital / self.capital_allocator.current_capital) * 100:.1f}%")
        
        return trade

    def check_exit_conditions(self, trade: Dict, current_day: int) -> bool:
        """Check if a trade should be exited"""
        holding_days = current_day - trade['day']
        
        current_pnl_pct = (trade['pnl'] / (trade['trade_value'] * 0.1))
        
        if holding_days >= self.max_holding_days:
            logger.info(f"Day {current_day}: Exiting {trade['symbol']} {trade['strategy']} - Max holding period ({holding_days} days)")
            return True
        elif current_pnl_pct >= self.profit_target_pct:
            logger.info(f"Day {current_day}: Exiting {trade['symbol']} {trade['strategy']} - Profit target reached ({current_pnl_pct:.1%})")
            return True
        elif current_pnl_pct <= -self.stop_loss_pct:
            logger.info(f"Day {current_day}: Exiting {trade['symbol']} {trade['strategy']} - Stop loss triggered ({current_pnl_pct:.1%})")
            return True
        
        return False

    def run_backtest(self, days: int = 730) -> Dict:
        """Run options backtest with improved capital allocation"""
        logger.info(f"🚀 Starting improved options backtest for {days} days")
        
        for day in range(1, days + 1):
            # Process exits first
            trades_to_close = []
            for trade in self.capital_allocator.active_positions:
                if self.check_exit_conditions(trade, day):
                    trades_to_close.append(trade)
            
            # Close positions
            for trade in trades_to_close:
                self.capital_allocator.close_position(trade, "exit_conditions")
            
            # Optimize capital allocation every 10 days
            if day % 10 == 0:
                self.capital_allocator.optimize_capital_allocation()
            
            # Generate new trade
            new_trade = self.generate_options_trade(day)
            if new_trade:
                self.capital_allocator.trades.append(new_trade)
            
            # Progress update
            if day % 100 == 0:
                util = (self.capital_allocator.allocated_capital / self.capital_allocator.current_capital) * 100
                logger.info(f"Day {day}: Portfolio: ${self.capital_allocator.current_capital:,.2f} | Active: {len(self.capital_allocator.active_positions)} | Utilization: {util:.1f}% | Total Trades: {len(self.capital_allocator.trades)}")
        
        # Close any remaining positions
        for trade in self.capital_allocator.active_positions:
            self.capital_allocator.close_position(trade, "end_of_backtest")
        
        # Calculate final metrics
        total_pnl = self.capital_allocator.current_capital - self.capital_allocator.initial_capital
        total_return = total_pnl / self.capital_allocator.initial_capital
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # Calculate Sharpe ratio
        daily_returns = []
        for i in range(1, len(self.capital_allocator.trades)):
            prev_capital = self.capital_allocator.initial_capital + sum(t['pnl'] for t in self.capital_allocator.trades[:i])
            curr_capital = self.capital_allocator.initial_capital + sum(t['pnl'] for t in self.capital_allocator.trades[:i+1])
            daily_return = (curr_capital - prev_capital) / prev_capital
            daily_returns.append(daily_return)
        
        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            std_return = math.sqrt(sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns))
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        max_drawdown = 0
        peak_capital = self.capital_allocator.initial_capital
        for trade in self.capital_allocator.trades:
            if self.capital_allocator.current_capital > peak_capital:
                peak_capital = self.capital_allocator.current_capital
            drawdown = (peak_capital - self.capital_allocator.current_capital) / peak_capital
            max_drawdown = max(max_drawdown, drawdown)
        
        results = {
            'initial_capital': self.capital_allocator.initial_capital,
            'final_capital': self.capital_allocator.current_capital,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.capital_allocator.trades),
            'winning_trades': len([t for t in self.capital_allocator.trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in self.capital_allocator.trades if t['pnl'] < 0]),
            'win_rate': len([t for t in self.capital_allocator.trades if t['pnl'] > 0]) / len(self.capital_allocator.trades) if self.capital_allocator.trades else 0,
            'avg_trade_pnl': sum(t['pnl'] for t in self.capital_allocator.trades) / len(self.capital_allocator.trades) if self.capital_allocator.trades else 0,
            'capital_utilization': (self.capital_allocator.allocated_capital / self.capital_allocator.current_capital) * 100,
            'trades': self.capital_allocator.trades
        }
        
        return results

def run_improved_capital_allocation_backtest():
    """Run backtest with improved capital allocation"""
    
    print("🚀 IMPROVED CAPITAL ALLOCATION OPTIONS BACKTEST")
    print("=" * 60)
    
    # Run improved backtest
    print("\n📊 Running Improved Capital Allocation Backtest...")
    engine = ImprovedOptionsBacktestEngine(initial_capital=4000.0)
    results = engine.run_backtest(days=730)  # 2 years
    
    # Display results
    print(f"\n🎯 IMPROVED CAPITAL ALLOCATION RESULTS (2 Years)")
    print("-" * 50)
    print(f"💰 Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"📈 Final Capital: ${results['final_capital']:,.2f}")
    print(f"📊 Total P&L: ${results['total_pnl']:,.2f}")
    print(f"📈 Total Return: {results['total_return']:.1%}")
    print(f"📅 Annual Return: {results['annual_return']:.1%}")
    print(f"📊 Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"📉 Max Drawdown: {results['max_drawdown']:.1%}")
    print(f"🎯 Total Trades: {results['total_trades']}")
    print(f"✅ Win Rate: {results['win_rate']:.1%}")
    print(f"📊 Avg Trade P&L: ${results['avg_trade_pnl']:,.2f}")
    print(f"🔄 Capital Utilization: {results['capital_utilization']:.1f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"improved_capital_allocation_backtest_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    run_improved_capital_allocation_backtest()
