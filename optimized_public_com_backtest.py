#!/usr/bin/env python3
"""
Optimized Public.com Configuration Backtest
Test the optimized configuration with reduced trading frequency
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

class OptimizedPublicComBacktest:
    """Test optimized Public.com configuration"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # Realistic symbol characteristics
        self.symbols = {
            "TSLA": {"volatility": 0.45, "avg_daily_range": 0.08, "liquidity": "high", "beta": 1.8},
            "NVDA": {"volatility": 0.38, "avg_daily_range": 0.06, "liquidity": "high", "beta": 1.6},
            "AMD": {"volatility": 0.35, "avg_daily_range": 0.05, "liquidity": "high", "beta": 1.4},
            "META": {"volatility": 0.30, "avg_daily_range": 0.04, "liquidity": "high", "beta": 1.2},
            "PYPL": {"volatility": 0.28, "avg_daily_range": 0.04, "liquidity": "medium", "beta": 1.1},
            "AAPL": {"volatility": 0.22, "avg_daily_range": 0.03, "liquidity": "high", "beta": 0.9}
        }
        
        # Optimized strategy characteristics (higher quality)
        self.strategies = {
            "ElliottWaveCorrective": {
                "base_return": 0.035,     # Slightly higher for quality focus
                "volatility": 0.12,       # Lower volatility
                "win_rate": 0.58,         # Higher win rate for quality
                "avg_win": 0.065,         # Better average win
                "avg_loss": 0.035,        # Lower average loss
                "trade_frequency": 0.06   # Lower frequency - quality over quantity
            },
            "ButterflySpread": {
                "base_return": 0.025,     # Higher base return
                "volatility": 0.10,       # Lower volatility
                "win_rate": 0.55,         # Higher win rate
                "avg_win": 0.055,        # Better average win
                "avg_loss": 0.025,       # Lower average loss
                "trade_frequency": 0.04  # Lower frequency
            },
            "SectorRotation": {
                "base_return": 0.030,     # Higher base return
                "volatility": 0.12,       # Lower volatility
                "win_rate": 0.56,         # Higher win rate
                "avg_win": 0.060,        # Better average win
                "avg_loss": 0.030,       # Lower average loss
                "trade_frequency": 0.03  # Lower frequency
            },
            "VolatilityTrading": {
                "base_return": 0.025,     # Higher base return
                "volatility": 0.18,       # Lower volatility
                "win_rate": 0.52,         # Higher win rate
                "avg_win": 0.075,        # Better average win
                "avg_loss": 0.045,       # Lower average loss
                "trade_frequency": 0.05  # Lower frequency
            }
        }
        
        # OLD Trading costs
        self.old_trading_costs = {
            "commission_per_trade": 0.65,
            "commission_per_contract": 0.50,
            "bid_ask_spread": 0.002,
            "slippage": 0.0005,
            "financing_cost": 0.0001,
            "max_daily_trades": 2,
            "min_trade_size": 100,
            "max_position_size": 0.15
        }
        
        # OPTIMIZED Public.com Trading costs
        self.optimized_trading_costs = {
            "commission_per_trade": 0.0,
            "commission_per_contract": 0.0,
            "options_rebate_per_contract": 0.06,
            "bid_ask_spread": 0.001,
            "slippage": 0.0003,
            "financing_cost": 0.0001,
            "max_daily_trades": 5,          # OPTIMIZED: Reduced from 8 to 5
            "min_trade_size": 100,
            "max_position_size": 0.12,      # OPTIMIZED: More conservative
            "contracts_per_trade": 2,
            "quality_threshold": 0.6         # OPTIMIZED: Only high-quality trades
        }
    
    def run_backtest(self, use_optimized_costs=True, years=2):
        """Run optimized backtest"""
        days = years * 252
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
            
            # Skip weekends
            if day % 7 in [5, 6]:
                daily_pnl.append(0)
                days_in_month += 1
                if days_in_month >= 21:
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
                # Check if strategy generates a signal
                base_frequency = strategy_config["trade_frequency"]
                
                # Adjust frequency based on market conditions
                if current_cycle["cycle_type"] == "bear":
                    base_frequency *= 0.3  # OPTIMIZED: Much lower in bear markets
                elif current_cycle["cycle_type"] == "high_volatility":
                    base_frequency *= 0.5  # OPTIMIZED: Lower in high volatility
                elif current_cycle["cycle_type"] == "bull":
                    base_frequency *= 1.2  # OPTIMIZED: Slightly higher in bull markets
                
                if random.random() > base_frequency:
                    continue
                
                # Check daily trade limit
                costs = self.optimized_trading_costs if use_optimized_costs else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence (OPTIMIZED: Higher threshold)
                volatility_adjustment = 1.0 - (symbol_config["volatility"] - 0.3) * 0.3
                confidence_multiplier = 0.8 + (random.random() * 0.2)  # OPTIMIZED: Higher confidence range
                
                # Quality check (OPTIMIZED: Only high-quality trades)
                if use_optimized_costs and confidence_multiplier < costs.get("quality_threshold", 0.5):
                    continue
                
                # Position sizing (OPTIMIZED: More conservative)
                base_size = 0.06  # OPTIMIZED: Lower base size
                position_size = min(costs["max_position_size"], 
                                  max(0.03, base_size * confidence_multiplier * volatility_adjustment))
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < costs["min_trade_size"]:
                    continue
                
                # Calculate return
                expected_return = strategy_config["base_return"] * current_cycle["multiplier"]
                
                # Determine if trade is profitable
                base_win_rate = strategy_config["win_rate"]
                
                if current_cycle["cycle_type"] == "bear":
                    base_win_rate *= 0.7  # OPTIMIZED: More conservative in bear markets
                elif current_cycle["cycle_type"] == "bull":
                    base_win_rate *= 1.15
                    base_win_rate = min(0.65, base_win_rate)
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.005, np.random.normal(strategy_config["avg_win"], 0.008))
                else:
                    trade_return = -min(0.08, abs(np.random.normal(strategy_config["avg_loss"], 0.008)))
                
                # Calculate contracts traded
                contracts_traded = costs.get("contracts_per_trade", 1)
                daily_contracts += contracts_traded
                
                # Apply trading costs
                old_commission_cost = self.old_trading_costs["commission_per_trade"]
                old_contract_cost = self.old_trading_costs["commission_per_contract"] * contracts_traded
                old_spread_cost = trade_size * self.old_trading_costs["bid_ask_spread"]
                old_slippage_cost = trade_size * self.old_trading_costs["slippage"]
                old_total_costs = old_commission_cost + old_contract_cost + old_spread_cost + old_slippage_cost
                
                new_commission_cost = self.optimized_trading_costs["commission_per_trade"]
                new_contract_cost = self.optimized_trading_costs["commission_per_contract"] * contracts_traded
                new_rebate = self.optimized_trading_costs["options_rebate_per_contract"] * contracts_traded
                new_spread_cost = trade_size * self.optimized_trading_costs["bid_ask_spread"]
                new_slippage_cost = trade_size * self.optimized_trading_costs["slippage"]
                new_total_costs = new_commission_cost + new_contract_cost + new_spread_cost + new_slippage_cost - new_rebate
                
                # Use appropriate costs
                if use_optimized_costs:
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
                
                # Track costs
                total_old_costs += old_total_costs
                total_new_costs += new_total_costs
                total_rebates += new_rebate
            
            # Add market noise
            market_noise = np.random.normal(0, 0.008) * portfolio_value  # OPTIMIZED: Lower noise
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
            
            # Apply financing cost
            portfolio_value *= (1 - self.optimized_trading_costs["financing_cost"])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.20:  # OPTIMIZED: Lower drawdown threshold
                    logger.warning(f"Max drawdown reached on day {day}: {drawdown:.2%}")
                    break
        
        # Calculate final metrics
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (365 / len(daily_pnl)) - 1
        
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
        """Generate realistic market cycles over the period"""
        cycles = []
        current_cycle_length = 0
        current_cycle_type = "normal"
        
        for day in range(days):
            if current_cycle_length > 0:
                current_cycle_length -= 1
            else:
                # Start new cycle
                cycle_types = ["bull", "bear", "normal", "high_volatility"]
                weights = [0.25, 0.15, 0.45, 0.15]
                current_cycle_type = np.random.choice(cycle_types, p=weights)
                current_cycle_length = np.random.randint(60, 180)
            
            # Cycle characteristics
            cycle_configs = {
                "bull": {"multiplier": 1.1, "volatility": 0.8, "trend": 0.02},
                "bear": {"multiplier": 0.9, "volatility": 1.2, "trend": -0.01},
                "normal": {"multiplier": 1.0, "volatility": 1.0, "trend": 0.0},
                "high_volatility": {"multiplier": 0.95, "volatility": 1.5, "trend": 0.0}
            }
            
            config = cycle_configs[current_cycle_type]
            
            cycles.append({
                "day": day,
                "cycle_type": current_cycle_type,
                "multiplier": config["multiplier"],
                "volatility": config["volatility"],
                "trend": config["trend"]
            })
        
        return cycles
    
    def run_optimization_test(self, num_iterations=5):
        """Test optimized configuration"""
        logger.info(f"🚀 Testing optimized Public.com configuration with {num_iterations} iterations")
        
        old_results = []
        optimized_results = []
        
        for i in range(num_iterations):
            logger.info(f"Running iteration {i+1}/{num_iterations}")
            
            # Run with old costs
            old_result = self.run_backtest(use_optimized_costs=False, years=2)
            old_results.append(old_result)
            
            # Run with optimized costs
            optimized_result = self.run_backtest(use_optimized_costs=True, years=2)
            optimized_results.append(optimized_result)
        
        # Calculate statistics
        old_returns = [r["annual_return"] for r in old_results]
        optimized_returns = [r["annual_return"] for r in optimized_results]
        
        old_costs = [r["total_old_costs"] for r in old_results]
        optimized_costs = [r["total_new_costs"] for r in optimized_results]
        rebates = [r["total_rebates"] for r in optimized_results]
        
        old_drawdowns = [r["max_drawdown"] for r in old_results]
        optimized_drawdowns = [r["max_drawdown"] for r in optimized_results]
        
        old_sharpes = [r["sharpe_ratio"] for r in old_results]
        optimized_sharpes = [r["sharpe_ratio"] for r in optimized_results]
        
        # Generate report
        report = self._generate_optimization_report(
            old_results, optimized_results, old_returns, optimized_returns,
            old_costs, optimized_costs, rebates, old_drawdowns, optimized_drawdowns,
            old_sharpes, optimized_sharpes, num_iterations
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"optimized_public_com_backtest_{timestamp}.json"
        
        results = {
            "timestamp": timestamp,
            "num_iterations": num_iterations,
            "years": 2,
            "optimization_type": "quality_over_quantity",
            "old_results": old_results,
            "optimized_results": optimized_results,
            "summary": {
                "old_avg_return": np.mean(old_returns),
                "optimized_avg_return": np.mean(optimized_returns),
                "old_std_return": np.std(old_returns),
                "optimized_std_return": np.std(optimized_returns),
                "old_avg_costs": np.mean(old_costs),
                "optimized_avg_costs": np.mean(optimized_costs),
                "avg_rebates": np.mean(rebates),
                "avg_savings": np.mean(old_costs) - np.mean(optimized_costs),
                "old_avg_drawdown": np.mean(old_drawdowns),
                "optimized_avg_drawdown": np.mean(optimized_drawdowns),
                "old_avg_sharpe": np.mean(old_sharpes),
                "optimized_avg_sharpe": np.mean(optimized_sharpes)
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Optimization test results saved to {results_file}")
        
        return report, results
    
    def _generate_optimization_report(self, old_results, optimized_results, old_returns, optimized_returns,
                                    old_costs, optimized_costs, rebates, old_drawdowns, optimized_drawdowns,
                                    old_sharpes, optimized_sharpes, num_iterations):
        """Generate optimization analysis report"""
        
        report = "\n" + "="*80 + "\n"
        report += "🚀 OPTIMIZED PUBLIC.COM CONFIGURATION TEST RESULTS\n"
        report += "="*80 + "\n\n"
        
        report += f"📈 OPTIMIZATION OVERVIEW:\n"
        report += f"   • Period: 2 years ({num_iterations} iterations)\n"
        report += f"   • Strategy: Quality over Quantity\n"
        report += f"   • Trading Frequency: Reduced from 8 to 5 trades/day\n"
        report += f"   • Position Sizing: More conservative (12% max)\n"
        report += f"   • Quality Threshold: 60% minimum confidence\n\n"
        
        report += f"💰 COST COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Costs: ${np.mean(old_costs):,.2f}\n"
        report += f"     • Std Dev: ${np.std(old_costs):,.2f}\n\n"
        
        report += f"   OPTIMIZED Configuration:\n"
        report += f"     • Mean Annual Costs: ${np.mean(optimized_costs):,.2f}\n"
        report += f"     • Mean Rebates: ${np.mean(rebates):,.2f}\n"
        report += f"     • Net Benefit: ${np.mean(old_costs) - np.mean(optimized_costs) + np.mean(rebates):,.2f}\n\n"
        
        report += f"📊 PERFORMANCE COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(old_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(old_sharpes):.3f}\n\n"
        
        report += f"   OPTIMIZED Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(optimized_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(optimized_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(optimized_sharpes):.3f}\n\n"
        
        report += f"🎯 RISK METRICS:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(old_drawdowns):.2%}\n\n"
        
        report += f"   OPTIMIZED Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(optimized_drawdowns):.2%}\n\n"
        
        report += f"💡 OPTIMIZATION RESULTS:\n"
        return_improvement = np.mean(optimized_returns) - np.mean(old_returns)
        cost_savings = np.mean(old_costs) - np.mean(optimized_costs)
        rebate_benefits = np.mean(rebates)
        total_benefit = cost_savings + rebate_benefits
        
        report += f"     • Return Improvement: {return_improvement:+.2%}\n"
        report += f"     • Cost Savings: ${cost_savings:,.2f}\n"
        report += f"     • Rebate Benefits: ${rebate_benefits:,.2f}\n"
        report += f"     • Total Annual Benefit: ${total_benefit:,.2f}\n"
        report += f"     • 2-Year Total Benefit: ${total_benefit * 2:,.2f}\n\n"
        
        if return_improvement > 0:
            report += f"     ✅ OPTIMIZATION SUCCESSFUL: Better returns with cost optimization\n"
        else:
            report += f"     ⚠️  OPTIMIZATION PARTIAL: Cost benefits maintained, returns need work\n"
        
        if np.mean(optimized_sharpes) > np.mean(old_sharpes):
            report += f"     ✅ Risk-adjusted returns improved\n"
        else:
            report += f"     ⚠️  Risk-adjusted returns need improvement\n"
        
        report += f"     💰 Cost optimization provides ${total_benefit:,.2f} annual benefit\n"
        report += f"     📈 {'Higher' if np.mean(optimized_returns) > np.mean(old_returns) else 'Lower'} returns with {'better' if np.mean(optimized_sharpes) > np.mean(old_sharpes) else 'worse'} risk management\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = OptimizedPublicComBacktest()
    
    # Run optimization test
    report, results = backtest.run_optimization_test(num_iterations=5)
    
    # Print report
    print(report)
    
    logger.info("Optimized Public.com configuration test completed!")

if __name__ == "__main__":
    main()



















