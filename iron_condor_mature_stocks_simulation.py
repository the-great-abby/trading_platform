#!/usr/bin/env python3
"""
Iron Condor Simulation: INTC, AAPL, MSFT
Test Iron Condor performance on mature tech stocks
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IronCondorMatureStocksSimulator:
    """Simulate Iron Condor strategies on mature tech stocks"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        self.current_capital = self.initial_capital
        self.trades = []
        self.daily_returns = []
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital
        
        # Risk management rules
        self.max_position_size = 0.10  # 10% max position size
        self.max_daily_loss = 100.0    # $100 max daily loss
        self.max_total_exposure = 0.40  # 40% max total exposure
        self.min_cash_reserve = 0.30    # 30% min cash reserve
        
        # Mature tech stock configurations
        self.stocks = {
            "INTC": {
                "current_price": 45.0,      # Intel around $45
                "volatility": 0.35,         # 35% annual volatility
                "daily_volatility": 0.022,  # 2.2% daily volatility
                "iron_condor_config": {
                    "annual_return": 0.08,    # 8% annual return
                    "win_rate": 0.68,         # 68% win rate
                    "avg_win": 0.012,        # 1.2% average win
                    "avg_loss": -0.030,        # 3.0% average loss
                    "max_position_size": 0.10,
                    "max_daily_trades": 1,
                    "description": "Intel Iron Condor - moderate volatility, stable range"
                }
            },
            "AAPL": {
                "current_price": 180.0,     # Apple around $180
                "volatility": 0.25,         # 25% annual volatility (lower)
                "daily_volatility": 0.016,  # 1.6% daily volatility
                "iron_condor_config": {
                    "annual_return": 0.06,    # 6% annual return (conservative)
                    "win_rate": 0.72,         # 72% win rate (high win rate)
                    "avg_win": 0.010,        # 1.0% average win (small wins)
                    "avg_loss": -0.025,        # 2.5% average loss
                    "max_position_size": 0.10,
                    "max_daily_trades": 1,
                    "description": "Apple Iron Condor - low volatility, very stable"
                }
            },
            "MSFT": {
                "current_price": 380.0,     # Microsoft around $380
                "volatility": 0.28,         # 28% annual volatility
                "daily_volatility": 0.018,  # 1.8% daily volatility
                "iron_condor_config": {
                    "annual_return": 0.07,    # 7% annual return
                    "win_rate": 0.70,         # 70% win rate
                    "avg_win": 0.011,        # 1.1% average win
                    "avg_loss": -0.027,        # 2.7% average loss
                    "max_position_size": 0.10,
                    "max_daily_trades": 1,
                    "description": "Microsoft Iron Condor - low-moderate volatility"
                }
            }
        }
        
        # Market conditions
        self.market_regimes = ["bull", "bear", "volatile", "range_bound"]
        self.current_regime = "bull"
        
        # Trading constraints
        self.daily_trade_count = 0
        self.daily_pnl = 0
        self.total_exposure = 0.0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3
    
    def detect_market_regime(self, day: int) -> str:
        """Detect current market regime"""
        if day % random.randint(60, 120) == 0:
            self.current_regime = random.choice(self.market_regimes)
        return self.current_regime
    
    def get_regime_multiplier(self, regime: str, stock: str) -> float:
        """Get performance multiplier based on market regime and stock characteristics"""
        stock_vol = self.stocks[stock]["volatility"]
        
        # Iron Condor performs better in range-bound markets
        base_multipliers = {
            "bull": 0.95,        # 5% reduction in bull markets
            "bear": 0.90,        # 10% reduction in bear markets
            "volatile": 0.85,    # 15% reduction in volatile markets
            "range_bound": 1.25   # 25% boost in range-bound markets
        }
        
        base_multiplier = base_multipliers.get(regime, 1.0)
        
        # Adjust for stock volatility - lower volatility = better for Iron Condor
        if stock_vol < 0.30:  # Very low volatility stocks (AAPL)
            volatility_adjustment = 1.10  # 10% boost for low vol
        elif stock_vol < 0.35:  # Low-moderate volatility (MSFT)
            volatility_adjustment = 1.05  # 5% boost for low-moderate vol
        else:  # Moderate volatility (INTC)
            volatility_adjustment = 1.0   # No adjustment
        
        return base_multiplier * volatility_adjustment
    
    def calculate_position_size(self, stock: str) -> float:
        """Calculate position size for Iron Condor on specific stock"""
        config = self.stocks[stock]["iron_condor_config"]
        
        # Base position size
        base_size = min(config["max_position_size"], self.max_position_size)
        
        # Reduce position size after consecutive losses
        if self.consecutive_losses > 0:
            reduction_factor = max(0.5, 1.0 - (self.consecutive_losses * 0.2))
            base_size *= reduction_factor
        
        # Ensure we don't exceed total exposure limits
        if self.total_exposure + base_size > self.max_total_exposure:
            remaining_exposure = self.max_total_exposure - self.total_exposure
            base_size = max(0, remaining_exposure)
        
        # Ensure we maintain cash reserve
        min_cash_needed = self.current_capital * self.min_cash_reserve
        available_for_trading = self.current_capital - min_cash_needed
        
        max_position_value = min(available_for_trading * base_size, 
                                self.current_capital * base_size)
        
        return max_position_value
    
    def simulate_iron_condor_trade(self, stock: str, day: int) -> Dict[str, Any]:
        """Simulate Iron Condor trade on specific stock"""
        config = self.stocks[stock]["iron_condor_config"]
        stock_info = self.stocks[stock]
        regime = self.detect_market_regime(day)
        regime_multiplier = self.get_regime_multiplier(regime, stock)
        
        # Calculate position size
        position_size = self.calculate_position_size(stock)
        
        if position_size <= 100:  # Minimum $100 position
            return None
        
        # Determine trade outcome
        is_winner = random.random() < config["win_rate"]
        
        if is_winner:
            # Winning Iron Condor trade
            base_return = config["avg_win"] * random.uniform(0.6, 1.4)
            final_return = base_return * regime_multiplier
            
            # Add stock-specific volatility
            volatility_adjustment = random.gauss(0, stock_info["daily_volatility"] * 0.3)
            final_return += volatility_adjustment
            
            # Cap maximum win at 3% (Iron Condor has limited upside)
            final_return = min(final_return, 0.03)
            
            # Reset consecutive losses
            self.consecutive_losses = 0
            
        else:
            # Losing Iron Condor trade
            base_loss = config["avg_loss"] * random.uniform(0.7, 1.3)
            final_return = base_loss * regime_multiplier
            
            # Add stock-specific volatility
            volatility_adjustment = random.gauss(0, stock_info["daily_volatility"] * 0.3)
            final_return += volatility_adjustment
            
            # Cap maximum loss at 4% (Iron Condor has limited downside)
            final_return = max(final_return, -0.04)
            
            # Track consecutive losses
            self.consecutive_losses += 1
        
        # Calculate P&L
        trade_pnl = position_size * final_return
        
        # Update exposure
        self.total_exposure += config["max_position_size"]
        
        return {
            "strategy": f"IRON_CONDOR_{stock}",
            "stock": stock,
            "day": day,
            "regime": regime,
            "is_winner": is_winner,
            "return": final_return,
            "position_size": position_size,
            "pnl": trade_pnl,
            "total_exposure": self.total_exposure,
            "consecutive_losses": self.consecutive_losses,
            "stock_volatility": stock_info["volatility"],
            "stock_price": stock_info["current_price"]
        }
    
    def reset_daily_counters(self):
        """Reset daily trading counters"""
        self.daily_trade_count = 0
        self.daily_pnl = 0
    
    def check_risk_limits(self) -> bool:
        """Check if we've hit daily risk limits"""
        return (self.daily_pnl <= -self.max_daily_loss or 
                self.daily_trade_count >= 3)  # Max 3 trades per day (one per stock)
    
    def run_simulation(self, days: int = 730) -> Dict[str, Any]:
        """Run Iron Condor simulation on INTC, AAPL, MSFT"""
        logger.info(f"🚀 Starting Iron Condor simulation on INTC, AAPL, MSFT")
        logger.info(f"📊 Stocks: {list(self.stocks.keys())}")
        logger.info(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        
        total_trades = 0
        winning_trades = 0
        days_with_trades = 0
        
        # Track performance by stock
        stock_performance = {stock: {"trades": 0, "pnl": 0, "wins": 0} for stock in self.stocks.keys()}
        
        for day in range(days):
            self.reset_daily_counters()
            daily_trades = []
            
            # Each stock can have one Iron Condor trade per day
            for stock in self.stocks.keys():
                if self.check_risk_limits():
                    break
                
                if self.consecutive_losses >= self.max_consecutive_losses:
                    continue
                
                # 70% chance of trading Iron Condor on any given day
                if random.random() < 0.7:
                    trade = self.simulate_iron_condor_trade(stock, day)
                    if trade:
                        daily_trades.append(trade)
                        self.trades.append(trade)
                        self.daily_pnl += trade["pnl"]
                        self.daily_trade_count += 1
                        total_trades += 1
                        
                        # Track stock performance
                        stock_performance[stock]["trades"] += 1
                        stock_performance[stock]["pnl"] += trade["pnl"]
                        if trade["is_winner"]:
                            stock_performance[stock]["wins"] += 1
                            winning_trades += 1
            
            # Update capital
            self.current_capital += self.daily_pnl
            
            # Track daily returns
            if self.current_capital > 0:
                daily_return = self.daily_pnl / self.current_capital
                self.daily_returns.append(daily_return)
            
            # Update drawdown
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
            
            current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # Reduce exposure over time
            self.total_exposure *= 0.98
            
            if daily_trades:
                days_with_trades += 1
        
        # Calculate final metrics
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        annualized_return = (1 + total_return) ** (365 / days) - 1
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate Sharpe ratio
        if len(self.daily_returns) > 1:
            daily_std = np.std(self.daily_returns)
            sharpe_ratio = np.mean(self.daily_returns) / daily_std * np.sqrt(252) if daily_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate stock-specific metrics
        for stock in stock_performance:
            perf = stock_performance[stock]
            perf["win_rate"] = perf["wins"] / perf["trades"] if perf["trades"] > 0 else 0
            perf["avg_trade_return"] = perf["pnl"] / perf["trades"] if perf["trades"] > 0 else 0
        
        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.current_capital,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "days_simulated": days,
            "days_with_trades": days_with_trades,
            "stock_performance": stock_performance,
            "trades_per_stock": {
                stock: stock_performance[stock]["trades"]
                for stock in self.stocks.keys()
            }
        }

async def main():
    """Run the Iron Condor mature stocks simulation"""
    simulator = IronCondorMatureStocksSimulator()
    
    print("=" * 80)
    print("🚀 IRON CONDOR SIMULATION: INTC, AAPL, MSFT")
    print("=" * 80)
    print()
    
    # Run simulation
    results = simulator.run_simulation(days=730)  # 2 years
    
    # Display results
    print("📊 OVERALL IRON CONDOR RESULTS")
    print("-" * 40)
    print(f"💰 Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"💰 Final Capital: ${results['final_capital']:,.2f}")
    print(f"📈 Total Return: {results['total_return']:.2%}")
    print(f"📈 Annualized Return: {results['annualized_return']:.2%}")
    print(f"📉 Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"📊 Sharpe Ratio: {results['sharpe_ratio']:.3f}")
    print(f"🎯 Overall Win Rate: {results['win_rate']:.1%}")
    print(f"📋 Total Trades: {results['total_trades']}")
    print(f"✅ Winning Trades: {results['winning_trades']}")
    print()
    
    print("📊 STOCK-SPECIFIC PERFORMANCE")
    print("-" * 40)
    for stock, perf in results['stock_performance'].items():
        stock_info = simulator.stocks[stock]
        print(f"• {stock} (${stock_info['current_price']:.0f}, {stock_info['volatility']:.0%} vol):")
        print(f"  - Trades: {perf['trades']}")
        print(f"  - P&L: ${perf['pnl']:,.2f}")
        print(f"  - Win Rate: {perf['win_rate']:.1%}")
        print(f"  - Avg Trade Return: {perf['avg_trade_return']:.2%}")
        print()
    
    print("📊 STOCK BREAKDOWN")
    print("-" * 40)
    for stock, trade_count in results['trades_per_stock'].items():
        stock_info = simulator.stocks[stock]
        print(f"• {stock}: {trade_count} Iron Condor trades")
    print()
    
    print("🎯 PERFORMANCE ANALYSIS")
    print("-" * 40)
    if results['annualized_return'] > 0.075:
        print("✅ EXCELLENT: Annual return > 7.5% target")
    elif results['annualized_return'] > 0.05:
        print("✅ GOOD: Annual return > 5%")
    else:
        print("❌ POOR: Annual return below 5%")
    
    if results['sharpe_ratio'] > 2.0:
        print("✅ EXCELLENT: Sharpe ratio > 2.0 target")
    elif results['sharpe_ratio'] > 1.5:
        print("✅ GOOD: Sharpe ratio > 1.5")
    else:
        print("❌ POOR: Sharpe ratio below 1.5")
    
    if results['max_drawdown'] < 0.11:
        print("✅ EXCELLENT: Max drawdown < 11% target")
    elif results['max_drawdown'] < 0.15:
        print("✅ GOOD: Max drawdown < 15%")
    else:
        print("❌ POOR: Max drawdown > 15%")
    
    print()
    print("=" * 80)
    print("🎯 CONCLUSION: Iron Condor performance on mature tech stocks")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())


















