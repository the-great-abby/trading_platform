#!/usr/bin/env python3
"""
Public.com 2-Year Backtest with Cost Optimization
Run 2-year backtest with Public.com API cost structure and rebates
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

class PublicComTwoYearBacktest:
    """Run 2-year backtest with Public.com cost optimization"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # Realistic symbol characteristics
        self.symbols = {
            "TSLA": {"volatility": 0.45, "avg_daily_range": 0.08, "liquidity": "high"},
            "NVDA": {"volatility": 0.38, "avg_daily_range": 0.06, "liquidity": "high"},
            "AMD": {"volatility": 0.35, "avg_daily_range": 0.05, "liquidity": "high"},
            "META": {"volatility": 0.30, "avg_daily_range": 0.04, "liquidity": "high"},
            "PYPL": {"volatility": 0.28, "avg_daily_range": 0.04, "liquidity": "medium"},
            "AAPL": {"volatility": 0.22, "avg_daily_range": 0.03, "liquidity": "high"}
        }
        
        # Strategy characteristics
        self.strategies = {
            "ElliottWaveImpulse": {
                "base_return": 0.08,
                "volatility": 0.20,
                "win_rate": 0.65,
                "avg_win": 0.12,
                "avg_loss": 0.08,
                "trade_frequency": 0.3
            },
            "ElliottWaveCorrective": {
                "base_return": 0.06,
                "volatility": 0.15,
                "win_rate": 0.60,
                "avg_win": 0.10,
                "avg_loss": 0.07,
                "trade_frequency": 0.25
            },
            "ButterflySpread": {
                "base_return": 0.05,
                "volatility": 0.12,
                "win_rate": 0.55,
                "avg_win": 0.08,
                "avg_loss": 0.06,
                "trade_frequency": 0.20
            },
            "SectorRotation": {
                "base_return": 0.07,
                "volatility": 0.18,
                "win_rate": 0.58,
                "avg_win": 0.11,
                "avg_loss": 0.08,
                "trade_frequency": 0.15
            },
            "VolatilityTrading": {
                "base_return": 0.06,
                "volatility": 0.25,
                "win_rate": 0.52,
                "avg_win": 0.09,
                "avg_loss": 0.07,
                "trade_frequency": 0.18
            }
        }
        
        # OLD Trading costs (for comparison)
        self.old_trading_costs = {
            "commission_per_trade": 0.65,
            "commission_per_contract": 0.50,
            "bid_ask_spread": 0.02,
            "slippage": 0.005,
            "financing_cost": 0.0001,
            "max_daily_trades": 2,  # Old limit
            "min_trade_size": 100,
            "max_position_size": 0.20
        }
        
        # NEW Public.com Trading costs (optimized)
        self.new_trading_costs = {
            "commission_per_trade": 0.0,           # Commission-free
            "commission_per_contract": 0.0,        # Commission-free
            "options_rebate_per_contract": 0.06,   # $0.06 rebate per contract
            "bid_ask_spread": 0.01,                # Reduced spread
            "slippage": 0.0005,                    # Reduced slippage
            "financing_cost": 0.0001,
            "max_daily_trades": 15,                # Increased limit
            "min_trade_size": 100,
            "max_position_size": 0.20,
            "contracts_per_trade": 3               # Average contracts per trade
        }
    
    def run_backtest(self, use_new_costs=True, days=730):
        """Run a single backtest"""
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_old_costs = 0.0
        total_new_costs = 0.0
        
        # Market cycle simulation
        market_cycles = self._generate_market_cycles(days)
        
        for day in range(days):
            daily_trade_pnl = 0
            daily_trades = 0
            daily_contracts = 0
            daily_rebates = 0.0
            daily_old_costs = 0.0
            daily_new_costs = 0.0
            
            # Skip weekends (simplified)
            if day % 7 in [5, 6]:
                daily_pnl.append(0)
                continue
            
            # Get current market cycle
            current_cycle = market_cycles[day]
            
            # Run strategies for the day
            for strategy_name, strategy_config in self.strategies.items():
                # Check if strategy generates a signal
                if random.random() > strategy_config["trade_frequency"]:
                    continue
                
                # Check daily trade limit
                costs = self.new_trading_costs if use_new_costs else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence based on market cycle
                cycle_multiplier = current_cycle["multiplier"]
                confidence_multiplier = 0.8 + (random.random() * 0.4)
                
                # Volatility adjustment
                volatility_adjustment = 1.0 + (symbol_config["volatility"] - 0.3) * 0.5
                
                # Position sizing
                base_size = 0.10
                position_size = min(0.20, max(0.05, base_size * confidence_multiplier * volatility_adjustment))
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < costs["min_trade_size"]:
                    continue
                
                # Calculate return with market cycle adjustments
                expected_return = strategy_config["base_return"] * cycle_multiplier
                
                # Determine if trade is profitable
                is_win = random.random() < strategy_config["win_rate"]
                
                # Apply market cycle to win rate
                if current_cycle["type"] == "bear":
                    is_win = is_win and random.random() > 0.2  # 20% less likely to win in bear market
                elif current_cycle["type"] == "bull":
                    is_win = is_win or random.random() < 0.1  # 10% more likely to win in bull market
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.01, np.random.normal(strategy_config["avg_win"], 0.02))
                else:
                    trade_return = -min(0.15, abs(np.random.normal(strategy_config["avg_loss"], 0.02)))
                
                # Calculate contracts traded
                contracts_traded = costs.get("contracts_per_trade", 1)
                daily_contracts += contracts_traded
                
                # Apply OLD trading costs (for comparison)
                old_commission_cost = self.old_trading_costs["commission_per_trade"]
                old_contract_cost = self.old_trading_costs["commission_per_contract"] * contracts_traded
                old_spread_cost = trade_size * self.old_trading_costs["bid_ask_spread"]
                old_slippage_cost = trade_size * self.old_trading_costs["slippage"]
                old_total_costs = old_commission_cost + old_contract_cost + old_spread_cost + old_slippage_cost
                
                # Apply NEW trading costs (Public.com optimized)
                new_commission_cost = self.new_trading_costs["commission_per_trade"]
                new_contract_cost = self.new_trading_costs["commission_per_contract"] * contracts_traded
                new_rebate = self.new_trading_costs["options_rebate_per_contract"] * contracts_traded
                new_spread_cost = trade_size * self.new_trading_costs["bid_ask_spread"]
                new_slippage_cost = trade_size * self.new_trading_costs["slippage"]
                new_total_costs = new_commission_cost + new_contract_cost + new_spread_cost + new_slippage_cost - new_rebate
                
                # Use appropriate costs based on configuration
                if use_new_costs:
                    net_return = trade_return - (new_total_costs / trade_size)
                    daily_new_costs += new_total_costs
                    daily_rebates += new_rebate
                else:
                    net_return = trade_return - (old_total_costs / trade_size)
                    daily_old_costs += old_total_costs
                
                trade_pnl = net_return * trade_size
                daily_trade_pnl += trade_pnl
                total_trades += 1
                daily_trades += 1
                
                # Track costs for comparison
                total_old_costs += old_total_costs
                total_new_costs += new_total_costs
                total_rebates += new_rebate
            
            # Update portfolio
            portfolio_value += daily_trade_pnl
            daily_pnl.append(daily_trade_pnl)
            total_contracts += daily_contracts
            
            # Apply daily financing cost
            portfolio_value *= (1 - self.new_trading_costs["financing_cost"])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.20:  # 20% max drawdown
                    logger.warning(f"Max drawdown reached on day {day}: {drawdown:.2%}")
                    break
        
        # Calculate final metrics
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # Calculate drawdown
        max_drawdown = 0
        running_max = self.initial_capital
        for pnl in daily_pnl:
            running_max += pnl
            if running_max > peak_value:
                peak_value = running_max
            drawdown = (peak_value - running_max) / peak_value
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "final_value": portfolio_value,
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "total_trades": total_trades,
            "total_contracts": total_contracts,
            "total_rebates": total_rebates,
            "total_old_costs": total_old_costs,
            "total_new_costs": total_new_costs,
            "cost_savings": total_old_costs - total_new_costs,
            "net_rebate_benefit": total_rebates,
            "daily_pnl": daily_pnl
        }
    
    def _generate_market_cycles(self, days):
        """Generate realistic market cycles"""
        cycles = []
        current_cycle_length = 0
        current_cycle_type = "bull"
        
        for day in range(days):
            if current_cycle_length > 0:
                current_cycle_length -= 1
            else:
                # Start new cycle
                cycle_types = ["bull", "bear", "sideways"]
                weights = [0.4, 0.2, 0.4]  # Bull markets more common
                current_cycle_type = np.random.choice(cycle_types, p=weights)
                current_cycle_length = random.randint(30, 120)  # 1-4 months
            
            # Cycle multipliers
            multipliers = {
                "bull": 1.2,
                "bear": 0.8,
                "sideways": 1.0
            }
            
            cycles.append({
                "type": current_cycle_type,
                "multiplier": multipliers[current_cycle_type],
                "remaining_days": current_cycle_length
            })
        
        return cycles
    
    def run_comparison_backtest(self, num_runs=10):
        """Run comparison between old and new cost structures"""
        logger.info("🚀 Starting Public.com Cost Optimization Backtest")
        logger.info(f"Running {num_runs} iterations for statistical significance")
        
        old_results = []
        new_results = []
        
        for i in range(num_runs):
            logger.info(f"Running iteration {i+1}/{num_runs}")
            
            # Run with old costs
            old_result = self.run_backtest(use_new_costs=False)
            old_results.append(old_result)
            
            # Run with new costs
            new_result = self.run_backtest(use_new_costs=True)
            new_results.append(new_result)
        
        return old_results, new_results
    
    def generate_report(self, old_results, new_results):
        """Generate comprehensive comparison report"""
        # Calculate averages
        old_avg_return = np.mean([r["annual_return"] for r in old_results])
        new_avg_return = np.mean([r["annual_return"] for r in new_results])
        old_avg_drawdown = np.mean([r["max_drawdown"] for r in old_results])
        new_avg_drawdown = np.mean([r["max_drawdown"] for r in new_results])
        
        old_avg_trades = np.mean([r["total_trades"] for r in old_results])
        new_avg_trades = np.mean([r["total_trades"] for r in new_results])
        
        old_avg_costs = np.mean([r["total_old_costs"] for r in old_results])
        new_avg_costs = np.mean([r["total_new_costs"] for r in new_results])
        avg_rebates = np.mean([r["total_rebates"] for r in new_results])
        avg_savings = np.mean([r["cost_savings"] for r in new_results])
        
        report = "\n" + "="*80 + "\n"
        report += "🎯 PUBLIC.COM COST OPTIMIZATION BACKTEST RESULTS\n"
        report += "="*80 + "\n\n"
        
        report += f"📊 BACKTEST SUMMARY:\n"
        report += f"   • Period: 2 years (730 days)\n"
        report += f"   • Initial Capital: ${self.initial_capital:,.2f}\n"
        report += f"   • Iterations: {len(old_results)}\n"
        report += f"   • Symbols: {len(self.symbols)}\n"
        report += f"   • Strategies: {len(self.strategies)}\n\n"
        
        report += f"💰 COST COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Commission per trade: ${self.old_trading_costs['commission_per_trade']:.2f}\n"
        report += f"     • Commission per contract: ${self.old_trading_costs['commission_per_contract']:.2f}\n"
        report += f"     • Max daily trades: {self.old_trading_costs['max_daily_trades']}\n"
        report += f"     • Average annual costs: ${old_avg_costs:,.2f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Commission per trade: ${self.new_trading_costs['commission_per_trade']:.2f}\n"
        report += f"     • Commission per contract: ${self.new_trading_costs['commission_per_contract']:.2f}\n"
        report += f"     • Options rebate per contract: ${self.new_trading_costs['options_rebate_per_contract']:.2f}\n"
        report += f"     • Max daily trades: {self.new_trading_costs['max_daily_trades']}\n"
        report += f"     • Average annual costs: ${new_avg_costs:,.2f}\n"
        report += f"     • Average annual rebates: ${avg_rebates:,.2f}\n"
        report += f"     • Net cost savings: ${avg_savings:,.2f}\n\n"
        
        report += f"📈 PERFORMANCE COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Average Annual Return: {old_avg_return:.2%}\n"
        report += f"     • Average Max Drawdown: {old_avg_drawdown:.2%}\n"
        report += f"     • Average Total Trades: {old_avg_trades:.0f}\n"
        report += f"     • Average Final Value: ${np.mean([r['final_value'] for r in old_results]):,.2f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Average Annual Return: {new_avg_return:.2%}\n"
        report += f"     • Average Max Drawdown: {new_avg_drawdown:.2%}\n"
        report += f"     • Average Total Trades: {new_avg_trades:.0f}\n"
        report += f"     • Average Final Value: ${np.mean([r['final_value'] for r in new_results]):,.2f}\n\n"
        
        report += f"🎉 IMPROVEMENT SUMMARY:\n"
        return_improvement = new_avg_return - old_avg_return
        cost_improvement = avg_savings
        trade_improvement = new_avg_trades - old_avg_trades
        
        report += f"     • Return Improvement: {return_improvement:+.2%}\n"
        report += f"     • Cost Savings: ${cost_improvement:,.2f} per year\n"
        report += f"     • Additional Trades: {trade_improvement:+.0f} per year\n"
        report += f"     • Rebate Earnings: ${avg_rebates:,.2f} per year\n"
        report += f"     • Total Benefit: ${cost_improvement + avg_rebates:,.2f} per year\n\n"
        
        report += f"💡 KEY INSIGHTS:\n"
        report += f"     • Commission-free trading eliminates ${old_avg_costs - new_avg_costs:,.2f} in annual costs\n"
        report += f"     • Options rebates provide ${avg_rebates:,.2f} in additional income\n"
        report += f"     • Increased trading frequency ({new_avg_trades:.0f} vs {old_avg_trades:.0f}) captures more opportunities\n"
        report += f"     • Net benefit: ${cost_improvement + avg_rebates:,.2f} annually ({((cost_improvement + avg_rebates) / self.initial_capital) * 100:.1f}% of capital)\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = PublicComTwoYearBacktest()
    
    # Run comparison backtest
    old_results, new_results = backtest.run_comparison_backtest(num_runs=10)
    
    # Generate report
    report = backtest.generate_report(old_results, new_results)
    
    # Print report
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"public_com_backtest_results_{timestamp}.json"
    
    results = {
        "timestamp": timestamp,
        "old_results": old_results,
        "new_results": new_results,
        "summary": {
            "old_avg_return": np.mean([r["annual_return"] for r in old_results]),
            "new_avg_return": np.mean([r["annual_return"] for r in new_results]),
            "old_avg_costs": np.mean([r["total_old_costs"] for r in old_results]),
            "new_avg_costs": np.mean([r["total_new_costs"] for r in new_results]),
            "avg_rebates": np.mean([r["total_rebates"] for r in new_results]),
            "avg_savings": np.mean([r["cost_savings"] for r in new_results])
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {results_file}")

if __name__ == "__main__":
    main()









