#!/usr/bin/env python3
"""
Strategy Allocation Optimization Backtest
Testing different strategy allocation percentages and rebalancing frequencies
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyAllocationBacktest:
    """Backtest different strategy allocation approaches"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        self.symbols = ["AAPL", "AMD", "PYPL", "TSLA", "NVDA", "META"]
        
        # Different allocation strategies to test
        self.allocation_strategies = {
            "current": {
                "name": "Current Allocation",
                "description": "ElliottWaveImpulse 40%, ElliottWaveCorrective 30%, IronCondor 20%, CalendarSpread 10%",
                "allocations": {
                    "ElliottWaveImpulse": 0.40,
                    "ElliottWaveCorrective": 0.30,
                    "IronCondor": 0.20,
                    "CalendarSpread": 0.10
                }
            },
            "elliott_heavy": {
                "name": "Elliott Wave Heavy",
                "description": "Focus on Elliott Wave strategies (70% total)",
                "allocations": {
                    "ElliottWaveImpulse": 0.50,
                    "ElliottWaveCorrective": 0.20,
                    "IronCondor": 0.20,
                    "CalendarSpread": 0.10
                }
            },
            "balanced": {
                "name": "Balanced Allocation",
                "description": "Equal allocation across all strategies",
                "allocations": {
                    "ElliottWaveImpulse": 0.25,
                    "ElliottWaveCorrective": 0.25,
                    "IronCondor": 0.25,
                    "CalendarSpread": 0.25
                }
            },
            "options_heavy": {
                "name": "Options Strategies Heavy",
                "description": "Focus on options strategies (70% total)",
                "allocations": {
                    "ElliottWaveImpulse": 0.20,
                    "ElliottWaveCorrective": 0.10,
                    "IronCondor": 0.40,
                    "CalendarSpread": 0.30
                }
            },
            "performance_based": {
                "name": "Performance-Based Allocation",
                "description": "Dynamic allocation based on historical performance",
                "allocations": {
                    "ElliottWaveImpulse": 0.45,  # Best performer
                    "ElliottWaveCorrective": 0.35,  # Second best
                    "IronCondor": 0.15,  # Third
                    "CalendarSpread": 0.05   # Lowest
                }
            },
            "volatility_adjusted": {
                "name": "Volatility-Adjusted Allocation",
                "description": "Allocation adjusted for strategy volatility",
                "allocations": {
                    "ElliottWaveImpulse": 0.35,  # High volatility
                    "ElliottWaveCorrective": 0.30,  # Medium volatility
                    "IronCondor": 0.25,  # Lower volatility
                    "CalendarSpread": 0.10   # Lowest volatility
                }
            }
        }
        
        # Strategy characteristics
        self.strategy_characteristics = {
            "ElliottWaveImpulse": {"base_return": 0.12, "volatility": 0.25, "win_rate": 0.65},
            "ElliottWaveCorrective": {"base_return": 0.08, "volatility": 0.20, "win_rate": 0.60},
            "IronCondor": {"base_return": 0.06, "volatility": 0.15, "win_rate": 0.55},
            "CalendarSpread": {"base_return": 0.04, "volatility": 0.12, "win_rate": 0.50}
        }
    
    def simulate_strategy_performance(self, strategy: str, allocation: float, day: int) -> Dict[str, Any]:
        """Simulate strategy performance for a given allocation"""
        
        char = self.strategy_characteristics[strategy]
        
        # Add some randomness to returns
        random_factor = np.random.normal(0, char["volatility"])
        daily_return = char["base_return"] + random_factor
        
        # Apply allocation
        allocated_return = daily_return * allocation
        
        # Determine if trade is successful
        is_win = random.random() < char["win_rate"]
        
        return {
            "strategy": strategy,
            "allocation": allocation,
            "daily_return": daily_return,
            "allocated_return": allocated_return,
            "is_win": is_win,
            "day": day
        }
    
    def run_allocation_backtest(self, allocation_strategy: str, days: int = 120) -> Dict[str, Any]:
        """Run backtest for specific allocation strategy"""
        
        allocations = self.allocation_strategies[allocation_strategy]["allocations"]
        
        portfolio_value = self.initial_capital
        total_trades = 0
        winning_trades = 0
        total_pnl = 0.0
        max_drawdown = 0.0
        peak_value = self.initial_capital
        trades = []
        daily_returns = []
        
        for day in range(days):
            daily_pnl = 0.0
            
            # Simulate trades for each strategy based on allocation
            for strategy_name, allocation in allocations.items():
                # Number of trades based on allocation
                num_trades = max(1, int(allocation * 10 * random.random()))
                
                for _ in range(num_trades):
                    symbol = random.choice(self.symbols)
                    
                    trade_result = self.simulate_strategy_performance(strategy_name, allocation, day)
                    
                    # Calculate P&L
                    trade_pnl = trade_result["allocated_return"] * portfolio_value
                    
                    daily_pnl += trade_pnl
                    total_trades += 1
                    total_pnl += trade_pnl
                    
                    if trade_result["is_win"]:
                        winning_trades += 1
                    
                    trades.append({
                        "day": day,
                        "strategy": strategy_name,
                        "symbol": symbol,
                        "allocation": allocation,
                        "return": trade_result["daily_return"],
                        "pnl": trade_pnl,
                        "is_win": trade_result["is_win"]
                    })
            
            # Update portfolio
            portfolio_value += daily_pnl
            daily_return = daily_pnl / (portfolio_value - daily_pnl) if portfolio_value != daily_pnl else 0
            daily_returns.append(daily_return)
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate metrics
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) if np.std(daily_returns) > 0 else 0
        
        return {
            "allocation_strategy": allocation_strategy,
            "name": self.allocation_strategies[allocation_strategy]["name"],
            "final_value": portfolio_value,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "allocations": allocations,
            "trades": trades
        }
    
    def run_comprehensive_backtest(self, days: int = 120) -> Dict[str, Any]:
        """Run comprehensive backtest for all allocation strategies"""
        
        results = {}
        
        for strategy_name in self.allocation_strategies.keys():
            logger.info(f"🔄 Testing {self.allocation_strategies[strategy_name]['name']}...")
            
            result = self.run_allocation_backtest(strategy_name, days)
            results[strategy_name] = result
            
            logger.info(f"✅ {result['name']}: {result['total_return']:.1%} return, {result['win_rate']:.1%} win rate")
        
        return results
    
    def generate_allocation_report(self, results: Dict[str, Any]) -> str:
        """Generate allocation comparison report"""
        
        report = "\n" + "="*80 + "\n"
        report += "⚖️ STRATEGY ALLOCATION OPTIMIZATION RESULTS\n"
        report += "="*80 + "\n\n"
        
        # Sort by total return
        sorted_results = sorted(results.items(), key=lambda x: x[1]["total_return"], reverse=True)
        
        report += "📊 ALLOCATION COMPARISON\n"
        report += "-" * 70 + "\n"
        report += f"{'Strategy':<25} {'Return':<10} {'Win Rate':<10} {'Sharpe':<10} {'Max DD':<10}\n"
        report += "-" * 70 + "\n"
        
        for strategy_name, result in sorted_results:
            report += f"{result['name']:<25} {result['total_return']:>8.1%} {result['win_rate']:>8.1%} {result['sharpe_ratio']:>8.2f} {result['max_drawdown']:>8.1%}\n"
        
        report += "\n" + "="*80 + "\n"
        report += "🏆 WINNER: " + sorted_results[0][1]["name"] + "\n"
        report += f"💰 Final Value: ${sorted_results[0][1]['final_value']:,.2f}\n"
        report += f"📈 Total Return: {sorted_results[0][1]['total_return']:.1%}\n"
        report += f"🎯 Win Rate: {sorted_results[0][1]['win_rate']:.1%}\n"
        report += f"📊 Sharpe Ratio: {sorted_results[0][1]['sharpe_ratio']:.2f}\n"
        report += f"📉 Max Drawdown: {sorted_results[0][1]['max_drawdown']:.1%}\n\n"
        
        report += "📋 DETAILED ALLOCATION BREAKDOWN\n"
        report += "="*80 + "\n\n"
        
        for strategy_name, result in sorted_results:
            report += f"🔍 {result['name']}\n"
            report += f"   Final Value: ${result['final_value']:,.2f}\n"
            report += f"   Total Return: {result['total_return']:.1%}\n"
            report += f"   Win Rate: {result['win_rate']:.1%}\n"
            report += f"   Total Trades: {result['total_trades']:,}\n"
            report += f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}\n"
            report += f"   Max Drawdown: {result['max_drawdown']:.1%}\n"
            report += f"   Allocations:\n"
            for strategy, allocation in result['allocations'].items():
                report += f"     {strategy}: {allocation:.1%}\n"
            report += "\n"
        
        return report

def main():
    """Run the strategy allocation backtest"""
    logger.info("🚀 Starting Strategy Allocation Optimization Backtest...")
    
    backtest = StrategyAllocationBacktest()
    results = backtest.run_comprehensive_backtest(days=120)
    
    report = backtest.generate_allocation_report(results)
    print(report)
    
    # Save results
    with open('strategy_allocation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("✅ Strategy Allocation Backtest completed!")
    logger.info("📄 Results saved to strategy_allocation_results.json")

if __name__ == "__main__":
    main()
