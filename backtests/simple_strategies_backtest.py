#!/usr/bin/env python3
"""
Simple Proven Strategies Backtest
Iron Condor, Elliott Wave Corrective, Elliott Wave Impulse, Calendar Spreads
All with trailing stops and Public.com cost optimization
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleStrategiesBacktest:
    """Backtest with proven simple strategies"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # Focus on high-probability symbols
        self.symbols = {
            "SPY": {"volatility": 0.18, "avg_daily_range": 0.02, "liquidity": "high", "beta": 1.0},
            "QQQ": {"volatility": 0.22, "avg_daily_range": 0.025, "liquidity": "high", "beta": 1.1},
            "TSLA": {"volatility": 0.45, "avg_daily_range": 0.08, "liquidity": "high", "beta": 1.8},
            "NVDA": {"volatility": 0.38, "avg_daily_range": 0.06, "liquidity": "high", "beta": 1.6},
            "AAPL": {"volatility": 0.22, "avg_daily_range": 0.03, "liquidity": "high", "beta": 0.9},
            "MSFT": {"volatility": 0.25, "avg_daily_range": 0.035, "liquidity": "high", "beta": 1.0}
        }
        
        # Proven simple strategies with realistic parameters
        self.strategies = {
            "IronCondor": {
                "base_return": 0.04,        # Higher base return for options strategies
                "volatility": 0.08,           # Lower volatility - defined risk
                "win_rate": 0.65,            # High win rate for iron condors
                "avg_win": 0.08,             # Good average win
                "avg_loss": 0.12,            # Controlled max loss
                "trade_frequency": 0.12,     # Higher frequency - weekly setups
                "max_loss": 0.12,            # Maximum loss per trade
                "profit_target": 0.50,       # Take profit at 50% of max profit
                "trailing_stop": 0.25        # Trail stop at 25% of max profit
            },
            "ElliottWaveCorrective": {
                "base_return": 0.035,        # Good base return
                "volatility": 0.10,          # Moderate volatility
                "win_rate": 0.58,            # Good win rate
                "avg_win": 0.07,             # Solid average win
                "avg_loss": 0.04,            # Controlled losses
                "trade_frequency": 0.08,     # Moderate frequency
                "max_loss": 0.06,            # Maximum loss per trade
                "profit_target": 0.75,       # Take profit at 75% of target
                "trailing_stop": 0.30        # Trail stop at 30% of target
            },
            "ElliottWaveImpulse": {
                "base_return": 0.045,        # Higher return for impulse waves
                "volatility": 0.12,          # Moderate volatility
                "win_rate": 0.55,            # Good win rate
                "avg_win": 0.09,             # Higher average win
                "avg_loss": 0.05,            # Controlled losses
                "trade_frequency": 0.06,     # Lower frequency - wait for setups
                "max_loss": 0.08,            # Maximum loss per trade
                "profit_target": 0.80,       # Take profit at 80% of target
                "trailing_stop": 0.25        # Trail stop at 25% of target
            },
            "CalendarSpreads": {
                "base_return": 0.03,         # Steady return
                "volatility": 0.06,          # Low volatility - time decay
                "win_rate": 0.62,            # High win rate
                "avg_win": 0.06,             # Consistent wins
                "avg_loss": 0.08,            # Controlled losses
                "trade_frequency": 0.10,     # Regular frequency
                "max_loss": 0.10,            # Maximum loss per trade
                "profit_target": 0.60,       # Take profit at 60% of max profit
                "trailing_stop": 0.20        # Trail stop at 20% of max profit
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
        
        # Public.com Trading costs (optimized)
        self.public_com_costs = {
            "commission_per_trade": 0.0,
            "commission_per_contract": 0.0,
            "options_rebate_per_contract": 0.06,
            "bid_ask_spread": 0.001,
            "slippage": 0.0003,
            "financing_cost": 0.0001,
            "max_daily_trades": 4,          # Moderate frequency
            "min_trade_size": 100,
            "max_position_size": 0.12,      # Conservative sizing
            "contracts_per_trade": 2
        }
    
    def run_backtest(self, use_public_com=True, years=2):
        """Run backtest with simple strategies"""
        days = years * 252
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_old_costs = 0.0
        total_new_costs = 0.0
        
        # Track active positions for trailing stops
        active_positions = []
        
        # Generate realistic market cycles
        market_cycles = self._generate_market_cycles(days)
        
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
            
            # Process trailing stops for active positions
            positions_to_close = []
            for i, position in enumerate(active_positions):
                position_pnl = self._calculate_position_pnl(position, current_cycle)
                
                # Check trailing stop
                if self._check_trailing_stop(position, position_pnl):
                    positions_to_close.append(i)
                    daily_trade_pnl += position_pnl
                    logger.info(f"Trailing stop triggered for {position['strategy']} position")
                else:
                    # Update position
                    active_positions[i]['current_pnl'] = position_pnl
                    active_positions[i]['days_held'] += 1
            
            # Close positions that hit trailing stops
            for i in reversed(positions_to_close):
                active_positions.pop(i)
            
            # Run strategies for new positions
            for strategy_name, strategy_config in self.strategies.items():
                # Check if strategy generates a signal
                base_frequency = strategy_config["trade_frequency"]
                
                # Adjust frequency based on market conditions
                if current_cycle["cycle_type"] == "bear":
                    base_frequency *= 0.4  # Lower frequency in bear markets
                elif current_cycle["cycle_type"] == "high_volatility":
                    base_frequency *= 0.6  # Lower frequency in high volatility
                elif current_cycle["cycle_type"] == "bull":
                    base_frequency *= 1.3  # Higher frequency in bull markets
                
                if random.random() > base_frequency:
                    continue
                
                # Check daily trade limit
                costs = self.public_com_costs if use_public_com else self.old_trading_costs
                if daily_trades >= costs["max_daily_trades"]:
                    break
                
                # Check if we already have a position in this strategy
                if any(pos['strategy'] == strategy_name for pos in active_positions):
                    continue
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence
                volatility_adjustment = 1.0 - (symbol_config["volatility"] - 0.2) * 0.2
                confidence_multiplier = 0.7 + (random.random() * 0.3)
                
                # Position sizing
                base_size = 0.08
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
                    base_win_rate *= 0.8
                elif current_cycle["cycle_type"] == "bull":
                    base_win_rate *= 1.1
                    base_win_rate = min(0.75, base_win_rate)
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.005, np.random.normal(strategy_config["avg_win"], 0.01))
                else:
                    trade_return = -min(strategy_config["max_loss"], abs(np.random.normal(strategy_config["avg_loss"], 0.01)))
                
                # Calculate contracts traded
                contracts_traded = costs.get("contracts_per_trade", 1)
                daily_contracts += contracts_traded
                
                # Apply trading costs
                old_commission_cost = self.old_trading_costs["commission_per_trade"]
                old_contract_cost = self.old_trading_costs["commission_per_contract"] * contracts_traded
                old_spread_cost = trade_size * self.old_trading_costs["bid_ask_spread"]
                old_slippage_cost = trade_size * self.old_trading_costs["slippage"]
                old_total_costs = old_commission_cost + old_contract_cost + old_spread_cost + old_slippage_cost
                
                new_commission_cost = self.public_com_costs["commission_per_trade"]
                new_contract_cost = self.public_com_costs["commission_per_contract"] * contracts_traded
                new_rebate = self.public_com_costs["options_rebate_per_contract"] * contracts_traded
                new_spread_cost = trade_size * self.public_com_costs["bid_ask_spread"]
                new_slippage_cost = trade_size * self.public_com_costs["slippage"]
                new_total_costs = new_commission_cost + new_contract_cost + new_spread_cost + new_slippage_cost - new_rebate
                
                # Use appropriate costs
                if use_public_com:
                    net_return = trade_return - (new_total_costs / trade_size)
                    daily_new_costs += new_total_costs
                    daily_rebates += new_rebate
                else:
                    net_return = trade_return - (old_total_costs / trade_size)
                    daily_old_costs += old_total_costs
                
                trade_pnl = net_return * trade_size
                
                # Create position for trailing stop management
                position = {
                    'strategy': strategy_name,
                    'symbol': symbol,
                    'entry_price': trade_size,
                    'entry_day': day,
                    'current_pnl': trade_pnl,
                    'days_held': 0,
                    'max_profit': trade_pnl,
                    'trailing_stop_level': trade_pnl * (1 - strategy_config["trailing_stop"]),
                    'profit_target': trade_pnl * strategy_config["profit_target"],
                    'max_loss': trade_pnl * (1 - strategy_config["max_loss"])
                }
                
                # Check if we should take profit immediately
                if trade_pnl >= position['profit_target']:
                    daily_trade_pnl += trade_pnl
                    logger.info(f"Profit target hit for {strategy_name} position")
                else:
                    # Add to active positions
                    active_positions.append(position)
                
                total_trades += 1
                daily_trades += 1
                
                # Track costs
                total_old_costs += old_total_costs
                total_new_costs += new_total_costs
                total_rebates += new_rebate
            
            # Add market noise
            market_noise = np.random.normal(0, 0.005) * portfolio_value
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
            portfolio_value *= (1 - self.public_com_costs["financing_cost"])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.15:  # Lower drawdown threshold for options
                    logger.warning(f"Max drawdown reached on day {day}: {drawdown:.2%}")
                    break
        
        # Close any remaining positions
        for position in active_positions:
            daily_trade_pnl += position['current_pnl']
        
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
    
    def _calculate_position_pnl(self, position: Dict, current_cycle: Dict) -> float:
        """Calculate current P&L for a position"""
        # Simulate position performance based on market cycle
        cycle_multiplier = current_cycle["multiplier"]
        volatility_factor = current_cycle["volatility"]
        
        # Add some randomness based on days held
        days_factor = min(1.0, position['days_held'] / 30)  # Decay over time
        
        # Calculate P&L change
        pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(0, 0.1))
        
        return position['current_pnl'] + pnl_change
    
    def _check_trailing_stop(self, position: Dict, current_pnl: float) -> bool:
        """Check if trailing stop should be triggered"""
        # Update max profit
        if current_pnl > position['max_profit']:
            position['max_profit'] = current_pnl
            position['trailing_stop_level'] = current_pnl * (1 - 0.25)  # 25% trailing stop
        
        # Check if current P&L is below trailing stop level
        if current_pnl <= position['trailing_stop_level']:
            return True
        
        # Check if we hit profit target
        if current_pnl >= position['profit_target']:
            return True
        
        # Check if we hit max loss
        if current_pnl <= position['max_loss']:
            return True
        
        return False
    
    def _generate_market_cycles(self, days: int) -> List[Dict]:
        """Generate realistic market cycles"""
        cycles = []
        current_cycle_length = 0
        current_cycle_type = "normal"
        
        for day in range(days):
            if current_cycle_length > 0:
                current_cycle_length -= 1
            else:
                # Start new cycle
                cycle_types = ["bull", "bear", "normal", "high_volatility"]
                weights = [0.3, 0.2, 0.4, 0.1]  # More bull markets for options
                current_cycle_type = np.random.choice(cycle_types, p=weights)
                current_cycle_length = np.random.randint(60, 180)
            
            # Cycle characteristics
            cycle_configs = {
                "bull": {"multiplier": 1.15, "volatility": 0.8, "trend": 0.02},
                "bear": {"multiplier": 0.85, "volatility": 1.3, "trend": -0.015},
                "normal": {"multiplier": 1.0, "volatility": 1.0, "trend": 0.0},
                "high_volatility": {"multiplier": 0.9, "volatility": 1.6, "trend": 0.0}
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
    
    def run_comprehensive_test(self, num_iterations=5):
        """Run comprehensive test with simple strategies"""
        logger.info(f"🚀 Testing simple proven strategies with {num_iterations} iterations")
        
        old_results = []
        public_com_results = []
        
        for i in range(num_iterations):
            logger.info(f"Running iteration {i+1}/{num_iterations}")
            
            # Run with old costs
            old_result = self.run_backtest(use_public_com=False, years=2)
            old_results.append(old_result)
            
            # Run with Public.com costs
            public_com_result = self.run_backtest(use_public_com=True, years=2)
            public_com_results.append(public_com_result)
        
        # Calculate statistics
        old_returns = [r["annual_return"] for r in old_results]
        public_com_returns = [r["annual_return"] for r in public_com_results]
        
        old_costs = [r["total_old_costs"] for r in old_results]
        public_com_costs = [r["total_new_costs"] for r in public_com_results]
        rebates = [r["total_rebates"] for r in public_com_results]
        
        old_drawdowns = [r["max_drawdown"] for r in old_results]
        public_com_drawdowns = [r["max_drawdown"] for r in public_com_results]
        
        old_sharpes = [r["sharpe_ratio"] for r in old_results]
        public_com_sharpes = [r["sharpe_ratio"] for r in public_com_results]
        
        # Generate report
        report = self._generate_simple_strategies_report(
            old_results, public_com_results, old_returns, public_com_returns,
            old_costs, public_com_costs, rebates, old_drawdowns, public_com_drawdowns,
            old_sharpes, public_com_sharpes, num_iterations
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"simple_strategies_backtest_{timestamp}.json"
        
        results = {
            "timestamp": timestamp,
            "num_iterations": num_iterations,
            "years": 2,
            "strategies": list(self.strategies.keys()),
            "old_results": old_results,
            "public_com_results": public_com_results,
            "summary": {
                "old_avg_return": np.mean(old_returns),
                "public_com_avg_return": np.mean(public_com_returns),
                "old_std_return": np.std(old_returns),
                "public_com_std_return": np.std(public_com_returns),
                "old_avg_costs": np.mean(old_costs),
                "public_com_avg_costs": np.mean(public_com_costs),
                "avg_rebates": np.mean(rebates),
                "avg_savings": np.mean(old_costs) - np.mean(public_com_costs),
                "old_avg_drawdown": np.mean(old_drawdowns),
                "public_com_avg_drawdown": np.mean(public_com_drawdowns),
                "old_avg_sharpe": np.mean(old_sharpes),
                "public_com_avg_sharpe": np.mean(public_com_sharpes)
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Simple strategies backtest results saved to {results_file}")
        
        return report, results
    
    def _generate_simple_strategies_report(self, old_results, public_com_results, old_returns, public_com_returns,
                                         old_costs, public_com_costs, rebates, old_drawdowns, public_com_drawdowns,
                                         old_sharpes, public_com_sharpes, num_iterations):
        """Generate simple strategies analysis report"""
        
        report = "\n" + "="*80 + "\n"
        report += "🎯 SIMPLE PROVEN STRATEGIES BACKTEST RESULTS\n"
        report += "="*80 + "\n\n"
        
        report += f"📈 STRATEGY OVERVIEW:\n"
        report += f"   • Period: 2 years ({num_iterations} iterations)\n"
        report += f"   • Strategies: {', '.join(self.strategies.keys())}\n"
        report += f"   • Features: Trailing stops, profit targets, risk management\n"
        report += f"   • Symbols: {len(self.symbols)} high-probability options symbols\n\n"
        
        report += f"💰 COST COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Costs: ${np.mean(old_costs):,.2f}\n"
        report += f"     • Std Dev: ${np.std(old_costs):,.2f}\n\n"
        
        report += f"   PUBLIC.COM Configuration:\n"
        report += f"     • Mean Annual Costs: ${np.mean(public_com_costs):,.2f}\n"
        report += f"     • Mean Rebates: ${np.mean(rebates):,.2f}\n"
        report += f"     • Net Benefit: ${np.mean(old_costs) - np.mean(public_com_costs) + np.mean(rebates):,.2f}\n\n"
        
        report += f"📊 PERFORMANCE COMPARISON:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(old_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(old_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(old_sharpes):.3f}\n\n"
        
        report += f"   PUBLIC.COM Configuration:\n"
        report += f"     • Mean Annual Return: {np.mean(public_com_returns):.2%}\n"
        report += f"     • Std Dev: {np.std(public_com_returns):.2%}\n"
        report += f"     • Mean Sharpe: {np.mean(public_com_sharpes):.3f}\n\n"
        
        report += f"🎯 RISK METRICS:\n"
        report += f"   OLD Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(old_drawdowns):.2%}\n\n"
        
        report += f"   PUBLIC.COM Configuration:\n"
        report += f"     • Mean Max Drawdown: {np.mean(public_com_drawdowns):.2%}\n\n"
        
        report += f"💡 STRATEGY PERFORMANCE:\n"
        return_improvement = np.mean(public_com_returns) - np.mean(old_returns)
        cost_savings = np.mean(old_costs) - np.mean(public_com_costs)
        rebate_benefits = np.mean(rebates)
        total_benefit = cost_savings + rebate_benefits
        
        report += f"     • Return Improvement: {return_improvement:+.2%}\n"
        report += f"     • Cost Savings: ${cost_savings:,.2f}\n"
        report += f"     • Rebate Benefits: ${rebate_benefits:,.2f}\n"
        report += f"     • Total Annual Benefit: ${total_benefit:,.2f}\n"
        report += f"     • 2-Year Total Benefit: ${total_benefit * 2:,.2f}\n\n"
        
        if return_improvement > 0:
            report += f"     ✅ SIMPLE STRATEGIES SUCCESS: Better returns with cost optimization\n"
        else:
            report += f"     ⚠️  SIMPLE STRATEGIES PARTIAL: Cost benefits maintained\n"
        
        if np.mean(public_com_sharpes) > np.mean(old_sharpes):
            report += f"     ✅ Risk-adjusted returns improved\n"
        else:
            report += f"     ⚠️  Risk-adjusted returns need improvement\n"
        
        report += f"     💰 Cost optimization provides ${total_benefit:,.2f} annual benefit\n"
        report += f"     📈 {'Higher' if np.mean(public_com_returns) > np.mean(old_returns) else 'Lower'} returns with {'better' if np.mean(public_com_sharpes) > np.mean(old_sharpes) else 'worse'} risk management\n\n"
        
        report += f"🎯 STRATEGY INSIGHTS:\n"
        report += f"     • Iron Condor: High win rate ({self.strategies['IronCondor']['win_rate']:.0%}) with defined risk\n"
        report += f"     • Elliott Wave Corrective: Good risk/reward ({self.strategies['ElliottWaveCorrective']['win_rate']:.0%} win rate)\n"
        report += f"     • Elliott Wave Impulse: Higher returns ({self.strategies['ElliottWaveImpulse']['win_rate']:.0%} win rate)\n"
        report += f"     • Calendar Spreads: Steady income ({self.strategies['CalendarSpreads']['win_rate']:.0%} win rate)\n"
        report += f"     • Trailing Stops: Risk management and profit protection\n\n"
        
        report += "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    backtest = SimpleStrategiesBacktest()
    
    # Run comprehensive test
    report, results = backtest.run_comprehensive_test(num_iterations=5)
    
    # Print report
    print(report)
    
    logger.info("Simple proven strategies backtest completed!")

if __name__ == "__main__":
    main()





















