#!/usr/bin/env python3
"""
Strategy Comparison: Iron Condor & Butterfly Spread vs Optimized Strategies
Compare performance of traditional options strategies vs our optimized strategies
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

class StrategyComparisonSimulator:
    """Compare traditional options strategies vs optimized strategies"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        self.current_capital = self.initial_capital
        self.trades = []
        self.daily_returns = []
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital
        
        # REALISTIC Risk management rules
        self.max_position_size = 0.10  # 10% max position size
        self.max_daily_loss = 100.0    # $100 max daily loss
        self.max_total_exposure = 0.40  # 40% max total exposure
        self.min_cash_reserve = 0.30    # 30% min cash reserve
        
        # Traditional Options Strategies (Iron Condor & Butterfly Spread)
        self.traditional_strategies = {
            "IRON_CONDOR": {
                "annual_return": 0.06,    # 6% annual return (conservative)
                "win_rate": 0.65,         # 65% win rate (high win rate, low profit)
                "avg_win": 0.008,        # 0.8% average win (small wins)
                "avg_loss": -0.025,       # 2.5% average loss (larger losses)
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.020,      # 2.0% daily volatility
                "description": "Range-bound strategy, struggles in trending markets"
            },
            "BUTTERFLY_SPREAD": {
                "annual_return": 0.04,    # 4% annual return (very conservative)
                "win_rate": 0.70,         # 70% win rate (very high win rate)
                "avg_win": 0.006,        # 0.6% average win (very small wins)
                "avg_loss": -0.020,       # 2.0% average loss
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.015,      # 1.5% daily volatility
                "description": "Very conservative strategy, limited profit potential"
            }
        }
        
        # Our Optimized Strategies
        self.optimized_strategies = {
            "SECTOR_ROTATION": {
                "annual_return": 0.08,    # 8% annual return
                "win_rate": 0.58,         # 58% win rate
                "avg_win": 0.015,        # 1.5% average win
                "avg_loss": -0.012,       # 1.2% average loss
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.025,      # 2.5% daily volatility
                "description": "Trend-following strategy, captures sector momentum"
            },
            "ELLIOTT_WAVE_IMPULSE": {
                "annual_return": 0.12,    # 12% annual return
                "win_rate": 0.62,         # 62% win rate
                "avg_win": 0.020,        # 2.0% average win
                "avg_loss": -0.015,       # 1.5% average loss
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.030,      # 3.0% daily volatility
                "description": "Trend-following strategy, captures impulse waves"
            },
            "ELLIOTT_WAVE_CORRECTIVE": {
                "annual_return": 0.06,    # 6% annual return
                "win_rate": 0.55,         # 55% win rate
                "avg_win": 0.012,        # 1.2% average win
                "avg_loss": -0.010,       # 1.0% average loss
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.020,      # 2.0% daily volatility
                "description": "Mean reversion strategy, captures corrective waves"
            },
            "VOLATILITY_TRADING": {
                "annual_return": 0.15,    # 15% annual return
                "win_rate": 0.65,         # 65% win rate
                "avg_win": 0.025,        # 2.5% average win
                "avg_loss": -0.018,       # 1.8% average loss
                "max_position_size": 0.10,
                "max_daily_trades": 1,
                "volatility": 0.035,      # 3.5% daily volatility
                "description": "Volatility capture strategy, profits from market moves"
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
        """Detect current market regime with realistic transitions"""
        if day % random.randint(60, 120) == 0:
            self.current_regime = random.choice(self.market_regimes)
        return self.current_regime
    
    def get_regime_multiplier(self, regime: str, strategy_type: str) -> float:
        """Get performance multiplier based on market regime and strategy type"""
        # Traditional options strategies perform better in range-bound markets
        if strategy_type in ["IRON_CONDOR", "BUTTERFLY_SPREAD"]:
            multipliers = {
                "bull": 0.95,        # 5% reduction in bull markets
                "bear": 0.90,        # 10% reduction in bear markets
                "volatile": 0.85,    # 15% reduction in volatile markets
                "range_bound": 1.15   # 15% boost in range-bound markets
            }
        else:
            # Optimized strategies perform better in trending markets
            multipliers = {
                "bull": 1.10,        # 10% boost in bull markets
                "bear": 0.90,        # 10% reduction in bear markets
                "volatile": 1.05,     # 5% boost in volatile markets
                "range_bound": 0.95   # 5% reduction in range-bound markets
            }
        return multipliers.get(regime, 1.0)
    
    def calculate_position_size(self, strategy_name: str) -> float:
        """Calculate realistic position size with proper risk management"""
        if strategy_name in self.traditional_strategies:
            config = self.traditional_strategies[strategy_name]
        else:
            config = self.optimized_strategies[strategy_name]
        
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
    
    def simulate_trade(self, strategy_name: str, day: int) -> Dict[str, Any]:
        """Simulate a realistic trade"""
        if strategy_name in self.traditional_strategies:
            config = self.traditional_strategies[strategy_name]
            strategy_type = "traditional"
        else:
            config = self.optimized_strategies[strategy_name]
            strategy_type = "optimized"
        
        regime = self.detect_market_regime(day)
        regime_multiplier = self.get_regime_multiplier(regime, strategy_name)
        
        # Calculate position size
        position_size = self.calculate_position_size(strategy_name)
        
        if position_size <= 100:  # Minimum $100 position
            return None
        
        # Determine trade outcome
        is_winner = random.random() < config["win_rate"]
        
        if is_winner:
            # Winning trade
            base_return = config["avg_win"] * random.uniform(0.6, 1.4)
            final_return = base_return * regime_multiplier
            
            # Add realistic volatility
            volatility_adjustment = random.gauss(0, config["volatility"] * 0.3)
            final_return += volatility_adjustment
            
            # Cap maximum win at 5%
            final_return = min(final_return, 0.05)
            
            # Reset consecutive losses
            self.consecutive_losses = 0
            
        else:
            # Losing trade
            base_loss = config["avg_loss"] * random.uniform(0.7, 1.3)
            final_return = base_loss * regime_multiplier
            
            # Add realistic volatility
            volatility_adjustment = random.gauss(0, config["volatility"] * 0.3)
            final_return += volatility_adjustment
            
            # Cap maximum loss at 3%
            final_return = max(final_return, -0.03)
            
            # Track consecutive losses
            self.consecutive_losses += 1
        
        # Calculate P&L
        trade_pnl = position_size * final_return
        
        # Update exposure
        self.total_exposure += config["max_position_size"]
        
        return {
            "strategy": strategy_name,
            "strategy_type": strategy_type,
            "day": day,
            "regime": regime,
            "is_winner": is_winner,
            "return": final_return,
            "position_size": position_size,
            "pnl": trade_pnl,
            "total_exposure": self.total_exposure,
            "consecutive_losses": self.consecutive_losses
        }
    
    def reset_daily_counters(self):
        """Reset daily trading counters"""
        self.daily_trade_count = 0
        self.daily_pnl = 0
    
    def check_risk_limits(self) -> bool:
        """Check if we've hit daily risk limits"""
        return (self.daily_pnl <= -self.max_daily_loss or 
                self.daily_trade_count >= 4)
    
    def run_comparison_simulation(self, days: int = 730) -> Dict[str, Any]:
        """Run comparison simulation with both strategy types"""
        logger.info(f"🚀 Starting strategy comparison simulation")
        logger.info(f"📊 Traditional Strategies: {list(self.traditional_strategies.keys())}")
        logger.info(f"📊 Optimized Strategies: {list(self.optimized_strategies.keys())}")
        
        total_trades = 0
        winning_trades = 0
        days_with_trades = 0
        
        # Track performance by strategy type
        traditional_trades = []
        optimized_trades = []
        
        for day in range(days):
            self.reset_daily_counters()
            daily_trades = []
            
            # Test both traditional and optimized strategies
            all_strategies = {**self.traditional_strategies, **self.optimized_strategies}
            
            for strategy_name in all_strategies.keys():
                if self.check_risk_limits():
                    break
                
                if self.consecutive_losses >= self.max_consecutive_losses:
                    continue
                
                # 70% chance of trading
                if random.random() < 0.7:
                    trade = self.simulate_trade(strategy_name, day)
                    if trade:
                        daily_trades.append(trade)
                        self.trades.append(trade)
                        self.daily_pnl += trade["pnl"]
                        self.daily_trade_count += 1
                        total_trades += 1
                        
                        if trade["is_winner"]:
                            winning_trades += 1
                        
                        # Categorize trades
                        if trade["strategy_type"] == "traditional":
                            traditional_trades.append(trade)
                        else:
                            optimized_trades.append(trade)
            
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
        
        # Calculate performance by strategy type
        traditional_pnl = sum(trade["pnl"] for trade in traditional_trades)
        optimized_pnl = sum(trade["pnl"] for trade in optimized_trades)
        
        traditional_win_rate = len([t for t in traditional_trades if t["is_winner"]]) / len(traditional_trades) if traditional_trades else 0
        optimized_win_rate = len([t for t in optimized_trades if t["is_winner"]]) / len(optimized_trades) if optimized_trades else 0
        
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
            "traditional_performance": {
                "trades": len(traditional_trades),
                "pnl": traditional_pnl,
                "win_rate": traditional_win_rate,
                "avg_trade_return": traditional_pnl / len(traditional_trades) if traditional_trades else 0
            },
            "optimized_performance": {
                "trades": len(optimized_trades),
                "pnl": optimized_pnl,
                "win_rate": optimized_win_rate,
                "avg_trade_return": optimized_pnl / len(optimized_trades) if optimized_trades else 0
            },
            "trades_per_strategy": {
                strategy: len([t for t in self.trades if t["strategy"] == strategy])
                for strategy in all_strategies.keys()
            }
        }

async def main():
    """Run the strategy comparison simulation"""
    simulator = StrategyComparisonSimulator()
    
    print("=" * 80)
    print("🚀 STRATEGY COMPARISON: TRADITIONAL vs OPTIMIZED")
    print("=" * 80)
    print()
    
    # Run simulation
    results = simulator.run_comparison_simulation(days=730)  # 2 years
    
    # Display results
    print("📊 OVERALL SIMULATION RESULTS")
    print("-" * 40)
    print(f"💰 Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"💰 Final Capital: ${results['final_capital']:,.2f}")
    print(f"📈 Total Return: {results['total_return']:.2%}")
    print(f"📈 Annualized Return: {results['annualized_return']:.2%}")
    print(f"📉 Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"📊 Sharpe Ratio: {results['sharpe_ratio']:.3f}")
    print(f"🎯 Overall Win Rate: {results['win_rate']:.1%}")
    print(f"📋 Total Trades: {results['total_trades']}")
    print()
    
    print("📊 TRADITIONAL STRATEGIES PERFORMANCE")
    print("-" * 40)
    trad = results['traditional_performance']
    print(f"• Iron Condor & Butterfly Spread Trades: {trad['trades']}")
    print(f"• Total P&L: ${trad['pnl']:,.2f}")
    print(f"• Win Rate: {trad['win_rate']:.1%}")
    print(f"• Average Trade Return: {trad['avg_trade_return']:.2%}")
    print()
    
    print("📊 OPTIMIZED STRATEGIES PERFORMANCE")
    print("-" * 40)
    opt = results['optimized_performance']
    print(f"• Optimized Strategy Trades: {opt['trades']}")
    print(f"• Total P&L: ${opt['pnl']:,.2f}")
    print(f"• Win Rate: {opt['win_rate']:.1%}")
    print(f"• Average Trade Return: {opt['avg_trade_return']:.2%}")
    print()
    
    print("📊 STRATEGY BREAKDOWN")
    print("-" * 40)
    for strategy, trade_count in results['trades_per_strategy'].items():
        strategy_type = "Traditional" if strategy in ["IRON_CONDOR", "BUTTERFLY_SPREAD"] else "Optimized"
        print(f"• {strategy} ({strategy_type}): {trade_count} trades")
    print()
    
    print("🎯 PERFORMANCE COMPARISON")
    print("-" * 40)
    if trad['pnl'] > opt['pnl']:
        print("✅ Traditional strategies outperformed optimized strategies")
        print(f"   Traditional P&L: ${trad['pnl']:,.2f} vs Optimized P&L: ${opt['pnl']:,.2f}")
    else:
        print("✅ Optimized strategies outperformed traditional strategies")
        print(f"   Optimized P&L: ${opt['pnl']:,.2f} vs Traditional P&L: ${trad['pnl']:,.2f}")
    
    print()
    print("=" * 80)
    print("🎯 CONCLUSION: Strategy performance comparison")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())


















