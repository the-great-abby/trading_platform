#!/usr/bin/env python3
"""
Capital Allocation Analysis for Trading Strategies
Implements 20% cash, 40% stocks, 40% options allocation
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapitalAllocationAnalyzer:
    """Analyze trading strategies with capital allocation"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash_allocation = 0.20  # 20% cash
        self.stock_allocation = 0.40  # 40% stocks
        self.options_allocation = 0.40  # 40% options
        
    def analyze_strategy_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze strategy results with capital allocation"""
        
        logger.info("🏴‍☠️ CAPITAL ALLOCATION ANALYSIS")
        logger.info("=" * 60)
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"Cash Allocation: {self.cash_allocation*100:.0f}% (${self.initial_capital * self.cash_allocation:,.2f})")
        logger.info(f"Stock Allocation: {self.stock_allocation*100:.0f}% (${self.initial_capital * self.stock_allocation:,.2f})")
        logger.info(f"Options Allocation: {self.options_allocation*100:.0f}% (${self.initial_capital * self.options_allocation:,.2f})")
        logger.info("=" * 60)
        
        # Categorize strategies
        stock_strategies = []
        options_strategies = []
        
        for result in results:
            strategy_name = result['name']
            if 'options' in strategy_name.lower() or 'put' in strategy_name.lower() or 'call' in strategy_name.lower():
                options_strategies.append(result)
            else:
                stock_strategies.append(result)
        
        logger.info(f"\n📊 STRATEGY CATEGORIZATION:")
        logger.info(f"Stock Strategies: {len(stock_strategies)}")
        for strategy in stock_strategies:
            logger.info(f"  - {strategy['name']}")
        
        logger.info(f"Options Strategies: {len(options_strategies)}")
        for strategy in options_strategies:
            logger.info(f"  - {strategy['name']}")
        
        # Calculate weighted returns
        total_weighted_return = 0.0
        total_weighted_sharpe = 0.0
        total_weighted_drawdown = 0.0
        total_weighted_trades = 0
        total_weighted_costs = 0.0
        
        logger.info(f"\n📈 WEIGHTED PERFORMANCE ANALYSIS:")
        logger.info("-" * 60)
        
        # Stock strategies (40% allocation)
        if stock_strategies:
            stock_weight = self.stock_allocation / len(stock_strategies)
            logger.info(f"Stock Strategies Weight: {stock_weight*100:.1f}% each")
            
            for strategy in stock_strategies:
                weighted_return = strategy['total_return'] * stock_weight
                weighted_sharpe = strategy['sharpe_ratio'] * stock_weight
                weighted_drawdown = strategy['max_drawdown'] * stock_weight
                weighted_trades = strategy['total_trades'] * stock_weight
                weighted_costs = strategy['net_transaction_costs'] * stock_weight
                
                total_weighted_return += weighted_return
                total_weighted_sharpe += weighted_sharpe
                total_weighted_drawdown += weighted_drawdown
                total_weighted_trades += weighted_trades
                total_weighted_costs += weighted_costs
                
                logger.info(f"  {strategy['name']}:")
                logger.info(f"    Return: {strategy['total_return']:.2f}% → Weighted: {weighted_return:.2f}%")
                logger.info(f"    Sharpe: {strategy['sharpe_ratio']:.3f} → Weighted: {weighted_sharpe:.3f}")
                logger.info(f"    Trades: {strategy['total_trades']} → Weighted: {weighted_trades:.1f}")
        
        # Options strategies (40% allocation)
        if options_strategies:
            options_weight = self.options_allocation / len(options_strategies)
            logger.info(f"Options Strategies Weight: {options_weight*100:.1f}% each")
            
            for strategy in options_strategies:
                weighted_return = strategy['total_return'] * options_weight
                weighted_sharpe = strategy['sharpe_ratio'] * options_weight
                weighted_drawdown = strategy['max_drawdown'] * options_weight
                weighted_trades = strategy['total_trades'] * options_weight
                weighted_costs = strategy['net_transaction_costs'] * options_weight
                
                total_weighted_return += weighted_return
                total_weighted_sharpe += weighted_sharpe
                total_weighted_drawdown += weighted_drawdown
                total_weighted_trades += weighted_trades
                total_weighted_costs += weighted_costs
                
                logger.info(f"  {strategy['name']}:")
                logger.info(f"    Return: {strategy['total_return']:.2f}% → Weighted: {weighted_return:.2f}%")
                logger.info(f"    Sharpe: {strategy['sharpe_ratio']:.3f} → Weighted: {weighted_sharpe:.3f}")
                logger.info(f"    Trades: {strategy['total_trades']} → Weighted: {weighted_trades:.1f}")
        
        # Cash allocation (20% - no return, no risk)
        cash_return = 0.0  # Assuming cash earns no return
        cash_sharpe = 0.0
        cash_drawdown = 0.0
        cash_trades = 0
        cash_costs = 0.0
        
        total_weighted_return += cash_return * self.cash_allocation
        total_weighted_sharpe += cash_sharpe * self.cash_allocation
        total_weighted_drawdown += cash_drawdown * self.cash_allocation
        total_weighted_trades += cash_trades * self.cash_allocation
        total_weighted_costs += cash_costs * self.cash_allocation
        
        logger.info(f"  Cash (20%):")
        logger.info(f"    Return: 0.00% → Weighted: 0.00%")
        logger.info(f"    Sharpe: 0.000 → Weighted: 0.000")
        logger.info(f"    Trades: 0 → Weighted: 0.0")
        
        # Final portfolio metrics
        final_capital = self.initial_capital * (1 + total_weighted_return / 100)
        total_return_dollars = final_capital - self.initial_capital
        
        logger.info(f"\n🎯 PORTFOLIO SUMMARY:")
        logger.info("=" * 60)
        logger.info(f"Total Weighted Return: {total_weighted_return:.2f}%")
        logger.info(f"Total Weighted Sharpe: {total_weighted_sharpe:.3f}")
        logger.info(f"Total Weighted Drawdown: {total_weighted_drawdown:.2f}%")
        logger.info(f"Total Weighted Trades: {total_weighted_trades:.1f}")
        logger.info(f"Total Weighted Costs: ${total_weighted_costs:,.2f}")
        logger.info(f"Final Capital: ${final_capital:,.2f}")
        logger.info(f"Total Return: ${total_return_dollars:,.2f}")
        
        # Risk-adjusted metrics
        risk_free_rate = 0.02  # 2% annual risk-free rate
        excess_return = total_weighted_return - (risk_free_rate * 4.2)  # 4.2 years
        risk_adjusted_return = excess_return / max(total_weighted_drawdown, 0.01)
        
        logger.info(f"\n📊 RISK-ADJUSTED METRICS:")
        logger.info(f"Risk-Free Rate: {risk_free_rate*100:.1f}% annually")
        logger.info(f"Excess Return: {excess_return:.2f}%")
        logger.info(f"Risk-Adjusted Return: {risk_adjusted_return:.3f}")
        
        return {
            'total_weighted_return': total_weighted_return,
            'total_weighted_sharpe': total_weighted_sharpe,
            'total_weighted_drawdown': total_weighted_drawdown,
            'total_weighted_trades': total_weighted_trades,
            'total_weighted_costs': total_weighted_costs,
            'final_capital': final_capital,
            'total_return_dollars': total_return_dollars,
            'risk_adjusted_return': risk_adjusted_return,
            'stock_strategies': len(stock_strategies),
            'options_strategies': len(options_strategies)
        }

def main():
    """Main analysis function"""
    
    # Sample results from our backtest
    sample_results = [
        {
            "name": "MACD",
            "total_return": 29.364498199999968,
            "sharpe_ratio": 0.11097553805289997,
            "max_drawdown": 6.5405799431099725,
            "win_rate": 0.4078014184397163,
            "total_trades": 282,
            "profit_factor": 1.801752261578355,
            "net_transaction_costs": 8325.711688320003
        },
        {
            "name": "RSI",
            "total_return": 191.85927910000004,
            "sharpe_ratio": 0.11156711416676571,
            "max_drawdown": 14.78561061862571,
            "win_rate": 0.7590361445783133,
            "total_trades": 83,
            "profit_factor": 3.9515860367038793,
            "net_transaction_costs": 4312.802281450003
        },
        {
            "name": "BollingerBands",
            "total_return": -25.18299640000003,
            "sharpe_ratio": 0.10011425936617518,
            "max_drawdown": 10.55833708990067,
            "win_rate": 0.728,
            "total_trades": 125,
            "profit_factor": 4.064657832752011,
            "net_transaction_costs": 7452.248883300005
        }
    ]
    
    # Initialize analyzer
    analyzer = CapitalAllocationAnalyzer(initial_capital=100000.0)
    
    # Run analysis
    results = analyzer.analyze_strategy_results(sample_results)
    
    logger.info(f"\n🏴‍☠️ CAPITAL ALLOCATION ANALYSIS COMPLETE!")
    logger.info(f"Portfolio achieved {results['total_weighted_return']:.2f}% return")
    logger.info(f"with {results['total_weighted_sharpe']:.3f} Sharpe ratio")
    logger.info(f"and {results['total_weighted_drawdown']:.2f}% max drawdown")

if __name__ == "__main__":
    main()

