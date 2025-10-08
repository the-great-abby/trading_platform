#!/usr/bin/env python3
"""
Quick Options Strategy Backtest
===============================
Compares options strategies vs stock strategies using the same approach as our paper trading engine
"""

import asyncio
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptionsBacktestEngine:
    """Simple options backtest engine using the same logic as our paper trading engine"""
    
    def __init__(self, initial_capital: float = 4000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        
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
        
        # Historical price ranges (approximate 2023-2024)
        self.price_ranges = {
            'AAPL': (150, 200), 'MSFT': (300, 450), 'GOOGL': (100, 180), 
            'TSLA': (150, 300), 'NVDA': (200, 900), 'SPY': (400, 600),
            'QQQ': (300, 500), 'AMZN': (100, 200), 'META': (200, 500), 'NFLX': (300, 700)
        }
        
        # Exit strategy configuration
        self.max_holding_days = 30
        self.profit_target_pct = 0.10  # 10% profit target
        self.stop_loss_pct = 0.05  # 5% stop loss
        
        logger.info(f"🚀 Options Backtest Engine initialized with ${initial_capital:,.2f}")

    def get_realistic_price(self, symbol: str, day: int) -> float:
        """Generate realistic price movement for a symbol on a given day"""
        base_range = self.price_ranges.get(symbol, (100, 200))
        base_price = (base_range[0] + base_range[1]) / 2
        
        # Add some daily variation
        daily_change = random.uniform(-0.03, 0.03)  # ±3% daily change
        price = base_price * (1 + daily_change)
        
        return round(price, 2)

    def get_realistic_options_price(self, symbol: str, strategy: str, current_price: float) -> tuple:
        """Generate realistic options premium and Greeks"""
        
        # Base premium ranges by strategy
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
        
        # Generate realistic Greeks
        greeks = {
            'delta': random.uniform(-0.5, 0.5),
            'gamma': random.uniform(0.01, 0.05),
            'theta': random.uniform(-0.05, -0.01),
            'vega': random.uniform(0.1, 0.3)
        }
        
        return round(premium, 2), greeks

    def calculate_options_position_size(self, symbol: str, strategy: str, premium: float) -> int:
        """Calculate realistic position size for options with proper portfolio constraints"""
        
        # More conservative position sizing for realistic results
        max_position_value = self.current_capital * 0.08  # 8% max position (was 12%)
        max_risk_value = self.current_capital * 0.03  # 3% max risk (was 5%)
        
        # Calculate max contracts based on position size
        max_contracts_position = int(max_position_value / (premium * 100))
        
        # Calculate max contracts based on risk
        max_contracts_risk = int(max_risk_value / (premium * 100))
        
        # Use the more conservative limit
        max_contracts = min(max_contracts_position, max_contracts_risk)
        min_contracts = 1
        
        if max_contracts < min_contracts:
            return 0
        
        # Much more conservative contract selection
        contracts = random.randint(min_contracts, min(max_contracts, 2))  # Max 2 contracts (was 5)
        
        return contracts

    def simulate_pnl(self, strategy: str, contracts: int, premium: float, greeks: Dict) -> float:
        """Simulate realistic P&L for options trade with proper win/loss ratios"""
        
        # Realistic win rates by strategy
        win_rates = {
            'IRON_CONDOR': 0.65,        # 65% win rate - high probability
            'STRADDLE': 0.55,           # 55% win rate
            'STRANGLE': 0.55,           # 55% win rate
            'BUTTERFLY': 0.60,          # 60% win rate
            'CALENDAR_SPREAD': 0.62     # 62% win rate
        }
        
        win_rate = win_rates.get(strategy, 0.50)
        is_winner = random.random() < win_rate
        
        if is_winner:
            # Winning trade
            if strategy in ['IRON_CONDOR', 'STRADDLE', 'STRANGLE']:
                # Credit strategies - profit from time decay
                base_pnl = premium * contracts * 100 * random.uniform(0.1, 0.4)
            else:
                # Debit strategies - profit from price movement
                base_pnl = premium * contracts * 100 * random.uniform(0.05, 0.3)
        else:
            # Losing trade
            if strategy == 'IRON_CONDOR':
                # Defined risk - max loss is spread width
                base_pnl = -premium * contracts * 100 * random.uniform(0.8, 1.5)
            elif strategy in ['STRADDLE', 'STRANGLE']:
                # Can lose premium + adverse movement
                base_pnl = -premium * contracts * 100 * random.uniform(0.5, 1.2)
            else:
                # Moderate losses
                base_pnl = -premium * contracts * 100 * random.uniform(0.3, 0.8)
        
        # Add realistic randomness
        random_factor = random.uniform(0.8, 1.2)
        total_pnl = base_pnl * random_factor
        
        # Cap P&L to be realistic relative to portfolio size
        max_realistic_pnl = self.current_capital * 0.05  # Max 5% gain per trade
        min_realistic_loss = -self.current_capital * 0.08  # Max 8% loss per trade
        total_pnl = max(min(total_pnl, max_realistic_pnl), min_realistic_loss)
        
        return round(total_pnl, 2)

    def generate_options_trade(self, day: int) -> Dict:
        """Generate a realistic options trade"""
        
        # Select random strategy and symbol
        strategy = random.choice(self.strategies)
        symbol = random.choice(self.symbols)
        
        # Get realistic current price
        current_price = self.get_realistic_price(symbol, day)
        
        # Generate realistic options pricing
        premium, greeks = self.get_realistic_options_price(symbol, strategy, current_price)
        
        # Calculate position size
        contracts = self.calculate_options_position_size(symbol, strategy, premium)
        
        if contracts == 0:
            return None
        
        # Simulate P&L
        pnl = self.simulate_pnl(strategy, contracts, premium, greeks)
        
        # Calculate trade value
        trade_value = contracts * premium * 100
        position_pct = (trade_value / self.current_capital) * 100
        
        # Update portfolio (subtract trade value first, then add P&L)
        self.current_capital -= trade_value  # Reserve capital for the trade
        self.current_capital += pnl  # Add P&L
        
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
            'status': 'open'
        }
        
        self.trades.append(trade)
        
        logger.info(f"Day {day}: {strategy} {contracts} contracts {symbol} @ ${current_price:.2f} | Premium: ${premium:.2f} | P&L: ${pnl:+.2f}")
        
        return trade

    def check_exit_conditions(self, trade: Dict, current_day: int) -> bool:
        """Check if a trade should be exited"""
        holding_days = current_day - trade['day']
        
        # Calculate current P&L percentage
        current_pnl_pct = (trade['pnl'] / (trade['trade_value'] * 0.1))
        
        # Exit conditions
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
        """Run options backtest for specified number of days"""
        logger.info(f"🚀 Starting options backtest for {days} days")
        
        active_trades = []
        
        for day in range(1, days + 1):
            # Process exits first
            trades_to_close = []
            for trade in active_trades:
                if self.check_exit_conditions(trade, day):
                    trade['status'] = 'closed'
                    trade['exit_day'] = day
                    trades_to_close.append(trade)
            
            # Remove closed trades
            for trade in trades_to_close:
                active_trades.remove(trade)
            
            # Generate new trade (if we have capacity and capital)
            if len(active_trades) < 3:  # Max 3 concurrent positions (was 5)
                new_trade = self.generate_options_trade(day)
                if new_trade:
                    # Check if we have enough capital for this trade
                    trade_value = new_trade['trade_value']
                    if trade_value <= self.current_capital * 0.15:  # Max 15% of portfolio per trade
                        active_trades.append(new_trade)
                    else:
                        logger.info(f"Day {day}: Skipping trade - insufficient capital (need ${trade_value:.2f}, have ${self.current_capital:.2f})")
            
            # Progress update
            if day % 100 == 0:
                logger.info(f"Day {day}: Portfolio: ${self.current_capital:,.2f} | Active: {len(active_trades)} | Total Trades: {len(self.trades)}")
        
        # Close any remaining positions
        for trade in active_trades:
            trade['status'] = 'closed'
            trade['exit_day'] = days
        
        # Calculate final metrics
        total_pnl = self.current_capital - self.initial_capital
        total_return = total_pnl / self.initial_capital
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # Calculate Sharpe ratio (simplified)
        daily_returns = []
        for i in range(1, len(self.trades)):
            prev_capital = self.initial_capital + sum(t['pnl'] for t in self.trades[:i])
            curr_capital = self.initial_capital + sum(t['pnl'] for t in self.trades[:i+1])
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
        peak_capital = self.initial_capital
        for trade in self.trades:
            if self.current_capital > peak_capital:
                peak_capital = self.current_capital
            drawdown = (peak_capital - self.current_capital) / peak_capital
            max_drawdown = max(max_drawdown, drawdown)
        
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in self.trades if t['pnl'] < 0]),
            'win_rate': len([t for t in self.trades if t['pnl'] > 0]) / len(self.trades) if self.trades else 0,
            'avg_trade_pnl': sum(t['pnl'] for t in self.trades) / len(self.trades) if self.trades else 0,
            'strategy_breakdown': self._get_strategy_breakdown(),
            'trades': self.trades
        }
        
        return results

    def _get_strategy_breakdown(self) -> Dict:
        """Get performance breakdown by strategy"""
        breakdown = {}
        for strategy in self.strategies:
            strategy_trades = [t for t in self.trades if t['strategy'] == strategy]
            if strategy_trades:
                breakdown[strategy] = {
                    'trades': len(strategy_trades),
                    'total_pnl': sum(t['pnl'] for t in strategy_trades),
                    'avg_pnl': sum(t['pnl'] for t in strategy_trades) / len(strategy_trades),
                    'win_rate': len([t for t in strategy_trades if t['pnl'] > 0]) / len(strategy_trades)
                }
        return breakdown

def run_options_vs_stocks_comparison():
    """Compare options strategies vs stock strategies"""
    
    print("🚀 OPTIONS vs STOCKS BACKTEST COMPARISON")
    print("=" * 60)
    
    # Run options backtest
    print("\n📊 Running Options Strategies Backtest...")
    options_engine = OptionsBacktestEngine(initial_capital=4000.0)
    options_results = options_engine.run_backtest(days=730)  # 2 years
    
    # Display options results
    print(f"\n🎯 OPTIONS STRATEGIES RESULTS (2 Years)")
    print("-" * 50)
    print(f"💰 Initial Capital: ${options_results['initial_capital']:,.2f}")
    print(f"📈 Final Capital: ${options_results['final_capital']:,.2f}")
    print(f"📊 Total P&L: ${options_results['total_pnl']:,.2f}")
    print(f"📈 Total Return: {options_results['total_return']:.1%}")
    print(f"📅 Annual Return: {options_results['annual_return']:.1%}")
    print(f"📊 Sharpe Ratio: {options_results['sharpe_ratio']:.2f}")
    print(f"📉 Max Drawdown: {options_results['max_drawdown']:.1%}")
    print(f"🎯 Total Trades: {options_results['total_trades']}")
    print(f"✅ Win Rate: {options_results['win_rate']:.1%}")
    print(f"📊 Avg Trade P&L: ${options_results['avg_trade_pnl']:,.2f}")
    
    # Strategy breakdown
    print(f"\n📋 Strategy Breakdown:")
    for strategy, stats in options_results['strategy_breakdown'].items():
        print(f"  {strategy}: {stats['trades']} trades, ${stats['total_pnl']:+.2f} P&L, {stats['win_rate']:.1%} win rate")
    
    # Compare with stock results (from comprehensive backtest)
    print(f"\n📊 COMPARISON WITH STOCK STRATEGIES")
    print("-" * 50)
    print(f"Options Annual Return: {options_results['annual_return']:+.1%}")
    print(f"Stock Annual Return:  -23.9% (from comprehensive backtest)")
    print(f"Difference:           {options_results['annual_return'] - (-0.239):+.1%}")
    
    print(f"\nOptions Sharpe Ratio: {options_results['sharpe_ratio']:.2f}")
    print(f"Stock Sharpe Ratio:  -1.24 (from comprehensive backtest)")
    print(f"Difference:          {options_results['sharpe_ratio'] - (-1.24):+.2f}")
    
    print(f"\nOptions Max Drawdown: {options_results['max_drawdown']:.1%}")
    print(f"Stock Max Drawdown:   24.6% (from comprehensive backtest)")
    print(f"Difference:          {options_results['max_drawdown'] - 0.246:+.1%}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"options_vs_stocks_backtest_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'options_results': options_results,
            'stock_comparison': {
                'stock_annual_return': -0.239,
                'stock_sharpe_ratio': -1.24,
                'stock_max_drawdown': 0.246
            }
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return options_results

if __name__ == "__main__":
    run_options_vs_stocks_comparison()
