#!/usr/bin/env python3
"""
Realistic Multi-Year Public.com Backtest
More conservative and realistic backtest over multiple years with proper market cycles
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

class RealisticMultiYearBacktest:
    """Run realistic multi-year backtest with Public.com cost optimization"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # More realistic symbol characteristics based on historical data
        self.symbols = {
            "TSLA": {"volatility": 0.45, "avg_daily_range": 0.08, "liquidity": "high", "beta": 1.8},
            "NVDA": {"volatility": 0.38, "avg_daily_range": 0.06, "liquidity": "high", "beta": 1.6},
            "AMD": {"volatility": 0.35, "avg_daily_range": 0.05, "liquidity": "high", "beta": 1.4},
            "META": {"volatility": 0.30, "avg_daily_range": 0.04, "liquidity": "high", "beta": 1.2},
            "PYPL": {"volatility": 0.28, "avg_daily_range": 0.04, "liquidity": "medium", "beta": 1.1},
            "AAPL": {"volatility": 0.22, "avg_daily_range": 0.03, "liquidity": "high", "beta": 0.9}
        }
        
        # More conservative strategy characteristics
        self.strategies = {
            "ElliottWaveCorrective": {
                "base_return": 0.03,      # More realistic 3% base return
                "volatility": 0.15,
                "win_rate": 0.55,        # More realistic 55% win rate
                "avg_win": 0.06,         # 6% average win
                "avg_loss": 0.04,        # 4% average loss
                "trade_frequency": 0.08   # Lower frequency - 8% chance per day
            },
            "ButterflySpread": {
                "base_return": 0.02,     # 2% base return
                "volatility": 0.12,
                "win_rate": 0.52,        # 52% win rate
                "avg_win": 0.05,         # 5% average win
                "avg_loss": 0.03,        # 3% average loss
                "trade_frequency": 0.06   # 6% chance per day
            },
            "SectorRotation": {
                "base_return": 0.025,    # 2.5% base return
                "volatility": 0.14,
                "win_rate": 0.53,        # 53% win rate
                "avg_win": 0.055,        # 5.5% average win
                "avg_loss": 0.035,       # 3.5% average loss
                "trade_frequency": 0.05  # 5% chance per day
            },
            "VolatilityTrading": {
                "base_return": 0.02,     # 2% base return
                "volatility": 0.20,
                "win_rate": 0.48,        # 48% win rate (more volatile)
                "avg_win": 0.07,         # 7% average win
                "avg_loss": 0.05,        # 5% average loss
                "trade_frequency": 0.07  # 7% chance per day
            }
        }
        
        # OLD Trading costs (for comparison)
        self.old_trading_costs = {
            "commission_per_trade": 0.65,
            "commission_per_contract": 0.50,
            "bid_ask_spread": 0.002,     # 0.2% spread
            "slippage": 0.0005,          # 0.05% slippage
            "financing_cost": 0.0001,
            "max_daily_trades": 2,       # Conservative limit
            "min_trade_size": 100,
            "max_position_size": 0.15    # More conservative position sizing
        }
        
        # NEW Public.com Trading costs (optimized)
        self.new_trading_costs = {
            "commission_per_trade": 0.0,           # Commission-free
            "commission_per_contract": 0.0,         # Commission-free
            "options_rebate_per_contract": 0.06,   # $0.06 rebate per contract
            "bid_ask_spread": 0.001,                # Reduced spread
            "slippage": 0.0003,                    # Reduced slippage
            "financing_cost": 0.0001,
            "max_daily_trades": 8,                  # More realistic increase
            "min_trade_size": 100,
            "max_position_size": 0.15,             # Same conservative sizing
            "contracts_per_trade": 2                # More realistic 2 contracts per trade
        }
    
    def run_backtest(self, use_new_costs=True, years=3):
        """Run a realistic multi-year backtest"""
        days = years * 252  # Trading days per year
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_old_costs = 0.0
        total_new_costs = 0.0
        
        # Generate realistic market cycles
        market_cycles = self._generate_realistic_market_cycles(days)
        
        # Track performance metrics
        monthly_returns = []
        current_month_pnl = 0
        days_in_month = 0
        
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
                days_in_month += 1
                if days_in_month >= 21:  # End of month
                    monthly_returns.append(current_month_pnl / portfolio_value)
                    current_month_pnl = 0
                    days_in_month = 0
                continue
            
            # Get current market cycle
            current_cycle = market_cycles[day]
            
            # Market impact on trading
            market_volatility = current_cycle["volatility"]
            market_trend = current_cycle["trend"]
            
            # Run strategies for the day
            for strategy_name, strategy_config in self.strategies.items():
                # Check if strategy generates a signal (reduced frequency)
                base_frequency = strategy_config["trade_frequency"]
                
                # Adjust frequency based on market conditions
                if current_cycle["type"] == "bear":
                    base_frequency *= 0.5  # Reduce trading in bear markets
                elif current_cycle["type"] == "high_volatility":
                    base_frequency *= 0.7  # Reduce trading in high vol
                
                if random.random() > base_frequency:
                    continue
                
                # Check daily trade limit
                costs = self.new_trading_costs if use_new_costs else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence based on market cycle and volatility
                cycle_multiplier = current_cycle["multiplier"]
                volatility_adjustment = 1.0 - (symbol_config["volatility"] - 0.3) * 0.3
                confidence_multiplier = 0.7 + (random.random() * 0.3)  # 0.7-1.0 range
                
                # Position sizing (more conservative)
                base_size = 0.05  # Start with 5%
                position_size = min(costs["max_position_size"], 
                                  max(0.02, base_size * confidence_multiplier * volatility_adjustment))
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < costs["min_trade_size"]:
                    continue
                
                # Calculate return with market cycle adjustments
                expected_return = strategy_config["base_return"] * cycle_multiplier
                
                # Determine if trade is profitable (more realistic)
                base_win_rate = strategy_config["win_rate"]
                
                # Adjust win rate based on market conditions
                if current_cycle["type"] == "bear":
                    base_win_rate *= 0.8  # 20% reduction in bear markets
                elif current_cycle["type"] == "bull":
                    base_win_rate *= 1.1  # 10% increase in bull markets
                    base_win_rate = min(0.7, base_win_rate)  # Cap at 70%
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return (more conservative)
                if is_win:
                    trade_return = max(0.005, np.random.normal(strategy_config["avg_win"], 0.01))
                else:
                    trade_return = -min(0.10, abs(np.random.normal(strategy_config["avg_loss"], 0.01)))
                
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
            
            # Add market noise (daily market movement)
            market_noise = np.random.normal(0, 0.01) * portfolio_value  # 1% daily volatility
            daily_trade_pnl += market_noise
            
            # Update portfolio
            portfolio_value += daily_trade_pnl
            daily_pnl.append(daily_trade_pnl)
            current_month_pnl += daily_trade_pnl
            total_contracts += daily_contracts
            days_in_month += 1
            
            # End of month
            if days_in_month >= 21:
                monthly_returns.append(current_month_pnl / portfolio_value)
                current_month_pnl = 0
                days_in_month = 0
            
            # Apply daily financing cost
            portfolio_value *= (1 - self.new_trading_costs["financing_cost"])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.25:  # 25% max drawdown (more realistic)
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
        
        # Calculate Sharpe ratio
        if len(monthly_returns) > 1:
            monthly_volatility = np.std(monthly_returns)
            if monthly_volatility > 0:
                sharpe_ratio = np.mean(monthly_returns) / monthly_volatility * np.sqrt(12)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            "final_value": portfolio_value,
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": total_trades,
            "total_contracts": total_contracts,
            "total_rebates": total_rebates,
            "total_old_costs": total_old_costs,
            "total_new_costs": total_new_costs,
            "cost_savings": total_old_costs - total_new_costs,
            "net_rebate_benefit": total_rebates,
            "daily_pnl": daily_pnl,
            "monthly_returns": monthly_returns
        }
    
    def _generate_realistic_market_cycles(self, days):
        """Generate realistic market cycles with proper volatility regimes"""
        cycles = []
        current_cycle_length = 0
        current_cycle_type = "normal"
        
        for day in range(days):
            if current_cycle_length > 0:
                current_cycle_length -= 1
            else:
                # Start new cycle with realistic probabilities
                cycle_types = ["bull", "bear", "normal", "high_volatility"]
                weights = [0.25, 0.15, 0.45, 0.15]  # Normal markets most common
                current_cycle_type = np.random.choice(cycle_types, p=weights)
                current_cycle_length = random.randint(60, 180)  # 2-6 months
            
            # Cycle characteristics
            cycle_configs = {
                "bull": {"multiplier": 1.1, "volatility": 0.8, "trend": 0.02},
                "bear": {"multiplier": 0.9, "volatility": 1.2, "trend": -0.01},
                "normal": {"multiplier": 1.0, "volatility": 1.0, "trend": 0.0},
                "high_volatility": {"multiplier": 0.95, "volatility": 1.5, "trend": 0.0}
            }
            
            config = cycle_configs[current_cycle_type]
            
            cycles.append({
                "type": current_cycle_type,
                "multiplier": config["multiplier"],
                "volatility": config["volatility"],
                "trend": config["trend"],
                "remaining_days": current_cycle_length
            })
        
        return cycles
    
    def run_comparison_backtest(self, num_runs=20, years=3):
        """Run comparison between old and new cost structures"""
        logger.info("🚀 Starting Realistic Multi-Year Public.com Cost Optimization Backtest")
        logger.info(f"Running {num_runs} iterations over {years} years for statistical significance")
        
        old_results = []
        new_results = []
        
        for i in range(num_runs):
            logger.info(f"Running iteration {i+1}/{num_runs}")
            
            # Run with old costs
            old_result = self.run_backtest(use_new_costs=False, years=years)
            old_results.append(old_result)
            
            # Run with new costs
            new_result = self.run_backtest(use_new_costs=True, years=years)
            new_results.append(new_result)
        
        return old_results, new_results
    
    def generate_report(self, old_results, new_results, years):
        """Generate comprehensive comparison report"""
        # Calculate averages
        old_avg_return = np.mean([r["annual_return"] for r in old_results])
        new_avg_return = np.mean([r["annual_return"] for r in new_results])
        old_avg_drawdown = np.mean([r["max_drawdown"] for r in old_results])
        new_avg_drawdown = np.mean([r["max_drawdown"] for r in new_results])
        old_avg_sharpe = np.mean([r["sharpe_ratio"] for r in old_results])
        new_avg_sharpe = np.mean([r["sharpe_ratio"] for r in new_results])
        
        old_avg_trades = np.mean([r["total_trades"] for r in old_results])
        new_avg_trades = np.mean([r["total_trades"] for r in new_results])
        
        old_avg_costs = np.mean([r["total_old_costs"] for r in old_results]) / years
        new_avg_costs = np.mean([r["total_new_costs"] for r in new_results]) / years
        avg_rebates = np.mean([r["total_rebates"] for r in new_results]) / years
        avg_savings = np.mean([r["cost_savings"] for r in new_results]) / years
        
        report = "\n" + "="*80 + "\n"
        report += f"🎯 REALISTIC {years}-YEAR PUBLIC.COM COST OPTIMIZATION BACKTEST\n"
        report += "="*80 + "\n\n"
        
        report += f"📊 BACKTEST SUMMARY:\n"
        report += f"   • Period: {years} years ({years * 252} trading days)\n"
        report += f"   • Initial Capital: ${self.initial_capital:,.2f}\n"
        report += f"   • Iterations: {len(old_results)}\n"
        report += f"   • Symbols: {len(self.symbols)}\n"
        report += f"   • Strategies: {len(self.strategies)}\n"
        report += f"   • Conservative Position Sizing: Max 15% per trade\n"
        report += f"   • Realistic Market Cycles: Bull, Bear, Normal, High Vol\n\n"
        
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
        report += f"     • Average Sharpe Ratio: {old_avg_sharpe:.2f}\n"
        report += f"     • Average Total Trades: {old_avg_trades:.0f}\n"
        report += f"     • Average Final Value: ${np.mean([r['final_value'] for r in old_results]):,.2f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Average Annual Return: {new_avg_return:.2%}\n"
        report += f"     • Average Max Drawdown: {new_avg_drawdown:.2%}\n"
        report += f"     • Average Sharpe Ratio: {new_avg_sharpe:.2f}\n"
        report += f"     • Average Total Trades: {new_avg_trades:.0f}\n"
        report += f"     • Average Final Value: ${np.mean([r['final_value'] for r in new_results]):,.2f}\n\n"
        
        report += f"🎉 IMPROVEMENT SUMMARY:\n"
        return_improvement = new_avg_return - old_avg_return
        cost_improvement = avg_savings
        trade_improvement = new_avg_trades - old_avg_trades
        sharpe_improvement = new_avg_sharpe - old_avg_sharpe
        
        report += f"     • Return Improvement: {return_improvement:+.2%}\n"
        report += f"     • Sharpe Ratio Improvement: {sharpe_improvement:+.2f}\n"
        report += f"     • Cost Savings: ${cost_improvement:,.2f} per year\n"
        report += f"     • Additional Trades: {trade_improvement:+.0f} per year\n"
        report += f"     • Rebate Earnings: ${avg_rebates:,.2f} per year\n"
        report += f"     • Total Benefit: ${cost_improvement + avg_rebates:,.2f} per year\n\n"
        
        report += f"💡 KEY INSIGHTS:\n"
        report += f"     • Commission-free trading saves ${old_avg_costs - new_avg_costs:,.2f} annually\n"
        report += f"     • Options rebates provide ${avg_rebates:,.2f} in additional income\n"
        report += f"     • Increased trading frequency ({new_avg_trades:.0f} vs {old_avg_trades:.0f}) captures more opportunities\n"
        report += f"     • Net benefit: ${cost_improvement + avg_rebates:,.2f} annually ({((cost_improvement + avg_rebates) / self.initial_capital) * 100:.1f}% of capital)\n"
        report += f"     • More realistic returns with proper risk management\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = RealisticMultiYearBacktest()
    
    # Run comparison backtest for 3 years
    old_results, new_results = backtest.run_comparison_backtest(num_runs=20, years=3)
    
    # Generate report
    report = backtest.generate_report(old_results, new_results, years=3)
    
    # Print report
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"realistic_public_com_backtest_results_{timestamp}.json"
    
    results = {
        "timestamp": timestamp,
        "years": 3,
        "old_results": old_results,
        "new_results": new_results,
        "summary": {
            "old_avg_return": np.mean([r["annual_return"] for r in old_results]),
            "new_avg_return": np.mean([r["annual_return"] for r in new_results]),
            "old_avg_costs": np.mean([r["total_old_costs"] for r in old_results]) / 3,
            "new_avg_costs": np.mean([r["total_new_costs"] for r in new_results]) / 3,
            "avg_rebates": np.mean([r["total_rebates"] for r in new_results]) / 3,
            "avg_savings": np.mean([r["cost_savings"] for r in new_results]) / 3,
            "old_avg_sharpe": np.mean([r["sharpe_ratio"] for r in old_results]),
            "new_avg_sharpe": np.mean([r["sharpe_ratio"] for r in new_results])
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {results_file}")

if __name__ == "__main__":
    main()









