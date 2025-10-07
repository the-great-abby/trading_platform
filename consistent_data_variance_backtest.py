#!/usr/bin/env python3
"""
Consistent Data Multi-Run Backtest
Run the same backtest multiple times over identical historical data to measure variance
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

class ConsistentDataBacktest:
    """Run multiple iterations over the same historical data to measure variance"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # Fixed historical data simulation (same for all runs)
        self.historical_data = self._generate_fixed_historical_data()
        
        # Symbol characteristics
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
    
    def _generate_fixed_historical_data(self):
        """Generate fixed historical data that will be the same for all runs"""
        np.random.seed(42)  # Fixed seed for consistent data
        
        days = 756  # 3 years
        historical_data = []
        
        # Generate realistic market cycles
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
            
            # Generate daily market data
            daily_data = {
                "day": day,
                "cycle_type": current_cycle_type,
                "multiplier": config["multiplier"],
                "volatility": config["volatility"],
                "trend": config["trend"],
                "market_return": np.random.normal(config["trend"], 0.01 * config["volatility"]),
                "vix_level": 15 + np.random.normal(0, 5) * config["volatility"],
                "volume_factor": 0.8 + np.random.normal(0, 0.3) * config["volatility"]
            }
            
            historical_data.append(daily_data)
        
        return historical_data
    
    def run_backtest(self, use_new_costs=True, run_id=0):
        """Run a single backtest over the fixed historical data"""
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_old_costs = 0.0
        total_new_costs = 0.0
        
        # Track performance metrics
        monthly_returns = []
        current_month_pnl = 0
        days_in_month = 0
        
        for day_data in self.historical_data:
            day = day_data["day"]
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
            
            # Use fixed market data
            market_volatility = day_data["volatility"]
            market_trend = day_data["trend"]
            cycle_multiplier = day_data["multiplier"]
            cycle_type = day_data["cycle_type"]
            
            # Run strategies for the day
            for strategy_name, strategy_config in self.strategies.items():
                # Check if strategy generates a signal
                base_frequency = strategy_config["trade_frequency"]
                
                # Adjust frequency based on market conditions
                if cycle_type == "bear":
                    base_frequency *= 0.5
                elif cycle_type == "high_volatility":
                    base_frequency *= 0.7
                
                # Use different random seed for each run to see variance
                random.seed(run_id * 1000 + day * 10 + hash(strategy_name))
                if random.random() > base_frequency:
                    continue
                
                # Check daily trade limit
                costs = self.new_trading_costs if use_new_costs else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Select symbol (use deterministic selection based on day)
                symbol_index = (day + hash(strategy_name)) % len(self.symbols)
                symbol = list(self.symbols.keys())[symbol_index]
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence
                volatility_adjustment = 1.0 - (symbol_config["volatility"] - 0.3) * 0.3
                random.seed(run_id * 1000 + day * 10 + hash(strategy_name) + 1)
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
                expected_return = strategy_config["base_return"] * cycle_multiplier
                
                # Determine if trade is profitable
                base_win_rate = strategy_config["win_rate"]
                
                if cycle_type == "bear":
                    base_win_rate *= 0.8
                elif cycle_type == "bull":
                    base_win_rate *= 1.1
                    base_win_rate = min(0.7, base_win_rate)
                
                random.seed(run_id * 1000 + day * 10 + hash(strategy_name) + 2)
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    random.seed(run_id * 1000 + day * 10 + hash(strategy_name) + 3)
                    trade_return = max(0.005, np.random.normal(strategy_config["avg_win"], 0.01))
                else:
                    random.seed(run_id * 1000 + day * 10 + hash(strategy_name) + 4)
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
            random.seed(run_id * 1000 + day + 1000)
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
                    break
        
        # Calculate final metrics
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (365 / len(self.historical_data)) - 1
        
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
            "run_id": run_id,
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
    
    def run_multiple_iterations(self, num_runs=50):
        """Run multiple iterations over the same data to measure variance"""
        logger.info(f"🚀 Running {num_runs} iterations over the same historical data")
        logger.info("This will show the variance in results due to random elements")
        
        old_results = []
        new_results = []
        
        for i in range(num_runs):
            if i % 10 == 0:
                logger.info(f"Running iteration {i+1}/{num_runs}")
            
            # Run with old costs
            old_result = self.run_backtest(use_new_costs=False, run_id=i)
            old_results.append(old_result)
            
            # Run with new costs
            new_result = self.run_backtest(use_new_costs=True, run_id=i)
            new_results.append(new_result)
        
        return old_results, new_results
    
    def generate_variance_report(self, old_results, new_results):
        """Generate report showing variance in results"""
        
        # Calculate statistics
        old_returns = [r["annual_return"] for r in old_results]
        new_returns = [r["annual_return"] for r in new_results]
        
        old_drawdowns = [r["max_drawdown"] for r in old_results]
        new_drawdowns = [r["max_drawdown"] for r in new_results]
        
        old_sharpes = [r["sharpe_ratio"] for r in old_results]
        new_sharpes = [r["sharpe_ratio"] for r in new_results]
        
        old_trades = [r["total_trades"] for r in old_results]
        new_trades = [r["total_trades"] for r in new_results]
        
        old_costs = [r["total_old_costs"] for r in old_results]
        new_costs = [r["total_new_costs"] for r in new_results]
        rebates = [r["total_rebates"] for r in new_results]
        
        report = "\n" + "="*80 + "\n"
        report += "📊 CONSISTENT DATA MULTI-RUN BACKTEST VARIANCE ANALYSIS\n"
        report += "="*80 + "\n\n"
        
        report += f"📈 VARIANCE ANALYSIS OVER {len(old_results)} RUNS:\n"
        report += f"   • Same historical data used for all runs\n"
        report += f"   • Only random elements vary between runs\n"
        report += f"   • Shows reliability of backtest results\n\n"
        
        report += f"💰 COST COMPARISON VARIANCE:\n"
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
        
        report += f"📊 PERFORMANCE VARIANCE:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(old_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_returns):.2%}\n"
        report += f"     • Min: {np.min(old_returns):.2%}\n"
        report += f"     • Max: {np.max(old_returns):.2%}\n"
        report += f"     • Coefficient of Variation: {np.std(old_returns)/abs(np.mean(old_returns)):.2f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Annual Return: {np.mean(new_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(new_returns):.2%}\n"
        report += f"     • Min: {np.min(new_returns):.2%}\n"
        report += f"     • Max: {np.max(new_returns):.2%}\n"
        report += f"     • Coefficient of Variation: {np.std(new_returns)/abs(np.mean(new_returns)):.2f}\n\n"
        
        report += f"🎯 RISK METRICS VARIANCE:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(old_drawdowns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_drawdowns):.2%}\n"
        report += f"     • Mean Sharpe Ratio: {np.mean(old_sharpes):.3f}\n"
        report += f"     • Std Dev Sharpe: {np.std(old_sharpes):.3f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Max Drawdown: {np.mean(new_drawdowns):.2%}\n"
        report += f"     • Std Dev: {np.std(new_drawdowns):.2%}\n"
        report += f"     • Mean Sharpe Ratio: {np.mean(new_sharpes):.3f}\n"
        report += f"     • Std Dev Sharpe: {np.std(new_sharpes):.3f}\n\n"
        
        report += f"📈 TRADING ACTIVITY VARIANCE:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Total Trades: {np.mean(old_trades):.0f}\n"
        report += f"     • Std Dev: {np.std(old_trades):.0f}\n"
        report += f"     • Min: {np.min(old_trades):.0f}\n"
        report += f"     • Max: {np.max(old_trades):.0f}\n\n"
        
        report += f"   NEW Configuration (Public.com):\n"
        report += f"     • Mean Total Trades: {np.mean(new_trades):.0f}\n"
        report += f"     • Std Dev: {np.std(new_trades):.0f}\n"
        report += f"     • Min: {np.min(new_trades):.0f}\n"
        report += f"     • Max: {np.max(new_trades):.0f}\n\n"
        
        report += f"💡 RELIABILITY ANALYSIS:\n"
        old_cv = np.std(old_returns) / abs(np.mean(old_returns)) if np.mean(old_returns) != 0 else float('inf')
        new_cv = np.std(new_returns) / abs(np.mean(new_returns)) if np.mean(new_returns) != 0 else float('inf')
        
        report += f"     • OLD Configuration CV: {old_cv:.2f} {'(High Variance)' if old_cv > 1.0 else '(Low Variance)'}\n"
        report += f"     • NEW Configuration CV: {new_cv:.2f} {'(High Variance)' if new_cv > 1.0 else '(Low Variance)'}\n"
        report += f"     • Return Improvement Consistency: {np.mean(new_returns) - np.mean(old_returns):.2%}\n"
        report += f"     • Cost Savings Consistency: ${np.mean(old_costs) - np.mean(new_costs) + np.mean(rebates):,.2f}\n\n"
        
        report += f"🎯 KEY INSIGHTS:\n"
        report += f"     • {'High' if old_cv > 1.0 else 'Low'} variance in OLD configuration results\n"
        report += f"     • {'High' if new_cv > 1.0 else 'Low'} variance in NEW configuration results\n"
        report += f"     • Cost optimization benefit is {'consistent' if np.std(old_costs) - np.std(new_costs) < 100 else 'variable'}\n"
        report += f"     • Trading frequency increase is {'consistent' if np.std(new_trades) < np.std(old_trades) else 'variable'}\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = ConsistentDataBacktest()
    
    # Run multiple iterations over the same data
    old_results, new_results = backtest.run_multiple_iterations(num_runs=50)
    
    # Generate variance report
    report = backtest.generate_variance_report(old_results, new_results)
    
    # Print report
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"consistent_data_variance_results_{timestamp}.json"
    
    results = {
        "timestamp": timestamp,
        "num_runs": len(old_results),
        "old_results": old_results,
        "new_results": new_results,
        "variance_analysis": {
            "old_return_mean": np.mean([r["annual_return"] for r in old_results]),
            "old_return_std": np.std([r["annual_return"] for r in old_results]),
            "new_return_mean": np.mean([r["annual_return"] for r in new_results]),
            "new_return_std": np.std([r["annual_return"] for r in new_results]),
            "old_cost_mean": np.mean([r["total_old_costs"] for r in old_results]),
            "old_cost_std": np.std([r["total_old_costs"] for r in old_results]),
            "new_cost_mean": np.mean([r["total_new_costs"] for r in new_results]),
            "new_cost_std": np.std([r["total_new_costs"] for r in new_results]),
            "rebate_mean": np.mean([r["total_rebates"] for r in new_results]),
            "rebate_std": np.std([r["total_rebates"] for r in new_results])
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Variance analysis results saved to {results_file}")

if __name__ == "__main__":
    main()



















