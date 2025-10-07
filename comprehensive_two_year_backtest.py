#!/usr/bin/env python3
"""
Comprehensive 2-Year Public.com Cost Optimization Backtest
Multiple iterations with detailed analysis
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

class ComprehensiveTwoYearBacktest:
    """Comprehensive 2-year backtest with multiple iterations"""
    
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
        
        # Conservative strategy characteristics
        self.strategies = {
            "ElliottWaveCorrective": {
                "base_return": 0.03,
                "volatility": 0.15,
                "win_rate": 0.55,
                "avg_win": 0.06,
                "avg_loss": 0.04,
                "trade_frequency": 0.08
            },
            "ButterflySpread": {
                "base_return": 0.02,
                "volatility": 0.12,
                "win_rate": 0.52,
                "avg_win": 0.05,
                "avg_loss": 0.03,
                "trade_frequency": 0.06
            },
            "SectorRotation": {
                "base_return": 0.025,
                "volatility": 0.14,
                "win_rate": 0.53,
                "avg_win": 0.055,
                "avg_loss": 0.035,
                "trade_frequency": 0.05
            },
            "VolatilityTrading": {
                "base_return": 0.02,
                "volatility": 0.20,
                "win_rate": 0.48,
                "avg_win": 0.07,
                "avg_loss": 0.05,
                "trade_frequency": 0.07
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
        
        # NEW Public.com Trading costs
        self.new_trading_costs = {
            "commission_per_trade": 0.0,
            "commission_per_contract": 0.0,
            "options_rebate_per_contract": 0.06,
            "bid_ask_spread": 0.001,
            "slippage": 0.0003,
            "financing_cost": 0.0001,
            "max_daily_trades": 8,
            "min_trade_size": 100,
            "max_position_size": 0.15,
            "contracts_per_trade": 2
        }
    
    def run_backtest(self, use_new_costs=True, years=2):
        """Run a 2-year backtest"""
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
                    base_frequency *= 0.5
                elif current_cycle["cycle_type"] == "high_volatility":
                    base_frequency *= 0.7
                
                if random.random() > base_frequency:
                    continue
                
                # Check daily trade limit
                costs = self.new_trading_costs if use_new_costs else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence
                volatility_adjustment = 1.0 - (symbol_config["volatility"] - 0.3) * 0.3
                confidence_multiplier = 0.7 + (random.random() * 0.3)
                
                # Position sizing
                base_size = 0.05
                position_size = min(costs["max_position_size"], 
                                  max(0.02, base_size * confidence_multiplier * volatility_adjustment))
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < costs["min_trade_size"]:
                    continue
                
                # Calculate return
                expected_return = strategy_config["base_return"] * current_cycle["multiplier"]
                
                # Determine if trade is profitable
                base_win_rate = strategy_config["win_rate"]
                
                if current_cycle["cycle_type"] == "bear":
                    base_win_rate *= 0.8
                elif current_cycle["cycle_type"] == "bull":
                    base_win_rate *= 1.1
                    base_win_rate = min(0.7, base_win_rate)
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.005, np.random.normal(strategy_config["avg_win"], 0.01))
                else:
                    trade_return = -min(0.10, abs(np.random.normal(strategy_config["avg_loss"], 0.01)))
                
                # Calculate contracts traded
                contracts_traded = costs.get("contracts_per_trade", 1)
                daily_contracts += contracts_traded
                
                # Apply trading costs
                old_commission_cost = self.old_trading_costs["commission_per_trade"]
                old_contract_cost = self.old_trading_costs["commission_per_contract"] * contracts_traded
                old_spread_cost = trade_size * self.old_trading_costs["bid_ask_spread"]
                old_slippage_cost = trade_size * self.old_trading_costs["slippage"]
                old_total_costs = old_commission_cost + old_contract_cost + old_spread_cost + old_slippage_cost
                
                new_commission_cost = self.new_trading_costs["commission_per_trade"]
                new_contract_cost = self.new_trading_costs["commission_per_contract"] * contracts_traded
                new_rebate = self.new_trading_costs["options_rebate_per_contract"] * contracts_traded
                new_spread_cost = trade_size * self.new_trading_costs["bid_ask_spread"]
                new_slippage_cost = trade_size * self.new_trading_costs["slippage"]
                new_total_costs = new_commission_cost + new_contract_cost + new_spread_cost + new_slippage_cost - new_rebate
                
                # Use appropriate costs
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
                
                # Track costs
                total_old_costs += old_total_costs
                total_new_costs += new_total_costs
                total_rebates += new_rebate
            
            # Add market noise
            market_noise = np.random.normal(0, 0.01) * portfolio_value
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
            portfolio_value *= (1 - self.new_trading_costs["financing_cost"])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.25:
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
    
    def run_comprehensive_analysis(self, num_iterations=10):
        """Run comprehensive 2-year analysis with multiple iterations"""
        logger.info(f"🚀 Running comprehensive 2-year analysis with {num_iterations} iterations")
        
        old_results = []
        new_results = []
        
        for i in range(num_iterations):
            logger.info(f"Running iteration {i+1}/{num_iterations}")
            
            # Run with old costs
            old_result = self.run_backtest(use_new_costs=False, years=2)
            old_results.append(old_result)
            
            # Run with new costs
            new_result = self.run_backtest(use_new_costs=True, years=2)
            new_results.append(new_result)
        
        # Calculate statistics
        old_returns = [r["annual_return"] for r in old_results]
        new_returns = [r["annual_return"] for r in new_results]
        
        old_costs = [r["total_old_costs"] for r in old_results]
        new_costs = [r["total_new_costs"] for r in new_results]
        rebates = [r["total_rebates"] for r in new_results]
        
        old_drawdowns = [r["max_drawdown"] for r in old_results]
        new_drawdowns = [r["max_drawdown"] for r in new_results]
        
        old_sharpes = [r["sharpe_ratio"] for r in old_results]
        new_sharpes = [r["sharpe_ratio"] for r in new_results]
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(
            old_results, new_results, old_returns, new_returns,
            old_costs, new_costs, rebates, old_drawdowns, new_drawdowns,
            old_sharpes, new_sharpes, num_iterations
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"comprehensive_two_year_backtest_{timestamp}.json"
        
        results = {
            "timestamp": timestamp,
            "num_iterations": num_iterations,
            "years": 2,
            "old_results": old_results,
            "new_results": new_results,
            "summary": {
                "old_avg_return": np.mean(old_returns),
                "new_avg_return": np.mean(new_returns),
                "old_std_return": np.std(old_returns),
                "new_std_return": np.std(new_returns),
                "old_avg_costs": np.mean(old_costs),
                "new_avg_costs": np.mean(new_costs),
                "avg_rebates": np.mean(rebates),
                "avg_savings": np.mean(old_costs) - np.mean(new_costs),
                "old_avg_drawdown": np.mean(old_drawdowns),
                "new_avg_drawdown": np.mean(new_drawdowns),
                "old_avg_sharpe": np.mean(old_sharpes),
                "new_avg_sharpe": np.mean(new_sharpes)
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_file}")
        
        return report, results
    
    def _generate_comprehensive_report(self, old_results, new_results, old_returns, new_returns,
                                     old_costs, new_costs, rebates, old_drawdowns, new_drawdowns,
                                     old_sharpes, new_sharpes, num_iterations):
        """Generate comprehensive analysis report"""
        
        report = "\n" + "="*80 + "\n"
        report += "📊 COMPREHENSIVE 2-YEAR PUBLIC.COM COST OPTIMIZATION ANALYSIS\n"
        report += "="*80 + "\n\n"
        
        report += f"📈 ANALYSIS OVERVIEW:\n"
        report += f"   • Period: 2 years ({num_iterations} iterations)\n"
        report += f"   • Initial Capital: ${self.initial_capital:,.2f}\n"
        report += f"   • Strategies: {len(self.strategies)} advanced strategies\n"
        report += f"   • Symbols: {len(self.symbols)} high-volatility stocks\n\n"
        
        report += f"💰 COST COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Costs: ${np.mean(old_costs):,.2f}\n"
        report += f"     • Std Dev: ${np.std(old_costs):,.2f}\n"
        report += f"     • Min: ${np.min(old_costs):,.2f}\n"
        report += f"     • Max: ${np.max(old_costs):,.2f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Annual Costs: ${np.mean(new_costs):,.2f}\n"
        report += f"     • Std Dev: ${np.std(new_costs):,.2f}\n"
        report += f"     • Mean Rebates: ${np.mean(rebates):,.2f}\n"
        report += f"     • Std Dev Rebates: ${np.std(rebates):,.2f}\n"
        report += f"     • Net Benefit: ${np.mean(old_costs) - np.mean(new_costs) + np.mean(rebates):,.2f}\n\n"
        
        report += f"📊 PERFORMANCE COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(old_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_returns):.2%}\n"
        report += f"     • Min: {np.min(old_returns):.2%}\n"
        report += f"     • Max: {np.max(old_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(old_sharpes):.3f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Annual Return: {np.mean(new_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(new_returns):.2%}\n"
        report += f"     • Min: {np.min(new_returns):.2%}\n"
        report += f"     • Max: {np.max(new_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(new_sharpes):.3f}\n\n"
        
        report += f"🎯 RISK METRICS:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(old_drawdowns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_drawdowns):.2%}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Max Drawdown: {np.mean(new_drawdowns):.2%}\n"
        report += f"     • Std Dev: {np.std(new_drawdowns):.2%}\n\n"
        
        report += f"💡 KEY INSIGHTS:\n"
        return_improvement = np.mean(new_returns) - np.mean(old_returns)
        cost_savings = np.mean(old_costs) - np.mean(new_costs)
        rebate_benefits = np.mean(rebates)
        total_benefit = cost_savings + rebate_benefits
        
        report += f"     • Return Improvement: {return_improvement:+.2%}\n"
        report += f"     • Cost Savings: ${cost_savings:,.2f}\n"
        report += f"     • Rebate Benefits: ${rebate_benefits:,.2f}\n"
        report += f"     • Total Annual Benefit: ${total_benefit:,.2f}\n"
        report += f"     • 2-Year Total Benefit: ${total_benefit * 2:,.2f}\n\n"
        
        if return_improvement > 0:
            report += f"     ✅ Public.com optimization improves returns\n"
        else:
            report += f"     ⚠️  Public.com optimization may hurt returns due to increased trading\n"
        
        if np.mean(new_sharpes) > np.mean(old_sharpes):
            report += f"     ✅ Risk-adjusted returns improve\n"
        else:
            report += f"     ⚠️  Risk-adjusted returns may decrease\n"
        
        report += f"     💰 Cost optimization provides consistent ${total_benefit:,.2f} annual benefit\n"
        report += f"     📈 {'Higher' if np.mean(new_returns) > np.mean(old_returns) else 'Lower'} returns with {'better' if np.mean(new_sharpes) > np.mean(old_sharpes) else 'worse'} risk management\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = ComprehensiveTwoYearBacktest()
    
    # Run comprehensive analysis
    report, results = backtest.run_comprehensive_analysis(num_iterations=10)
    
    # Print report
    print(report)
    
    logger.info("Comprehensive 2-year backtest analysis completed!")

if __name__ == "__main__":
    main()



















