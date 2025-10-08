#!/usr/bin/env python3
"""
Symbol Optimization & Sector Rotation Backtest
Testing different symbol combinations and sector rotation strategies
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

class SymbolOptimizationBacktest:
    """Backtest different symbol combinations and sector rotations"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        
        # Different symbol sets to test
        self.symbol_sets = {
            "current": {
                "name": "Current Optimized Mix",
                "description": "AAPL, AMD, PYPL, TSLA, NVDA, META",
                "symbols": ["AAPL", "AMD", "PYPL", "TSLA", "NVDA", "META"],
                "sectors": ["tech", "fintech", "automotive"]
            },
            "tech_heavy": {
                "name": "Tech Heavy Portfolio",
                "description": "Focus on technology stocks",
                "symbols": ["AAPL", "AMD", "NVDA", "META", "GOOGL", "MSFT"],
                "sectors": ["tech"]
            },
            "high_volatility": {
                "name": "High Volatility Mix",
                "description": "Focus on high volatility stocks",
                "symbols": ["TSLA", "NVDA", "AMD", "META", "PYPL", "AAPL"],
                "sectors": ["tech", "fintech", "automotive"]
            },
            "balanced_sectors": {
                "name": "Balanced Sector Mix",
                "description": "Equal representation across sectors",
                "symbols": ["AAPL", "JPM", "TSLA", "JNJ", "NVDA", "PYPL"],
                "sectors": ["tech", "financial", "automotive", "healthcare", "fintech"]
            },
            "momentum_stocks": {
                "name": "Momentum Stocks",
                "description": "Focus on momentum-driven stocks",
                "symbols": ["NVDA", "TSLA", "AMD", "META", "AAPL", "GOOGL"],
                "sectors": ["tech", "automotive"]
            },
            "value_stocks": {
                "name": "Value Stocks",
                "description": "Focus on value-oriented stocks",
                "symbols": ["AAPL", "JPM", "JNJ", "PG", "KO", "WMT"],
                "sectors": ["tech", "financial", "healthcare", "consumer"]
            }
        }
        
        # Symbol characteristics
        self.symbol_characteristics = {
            "AAPL": {"volatility": 0.22, "sector": "tech", "momentum": 0.6, "value": 0.7},
            "AMD": {"volatility": 0.35, "sector": "tech", "momentum": 0.8, "value": 0.4},
            "PYPL": {"volatility": 0.28, "sector": "fintech", "momentum": 0.5, "value": 0.6},
            "TSLA": {"volatility": 0.45, "sector": "automotive", "momentum": 0.9, "value": 0.2},
            "NVDA": {"volatility": 0.38, "sector": "tech", "momentum": 0.9, "value": 0.3},
            "META": {"volatility": 0.30, "sector": "tech", "momentum": 0.7, "value": 0.5},
            "GOOGL": {"volatility": 0.25, "sector": "tech", "momentum": 0.6, "value": 0.6},
            "MSFT": {"volatility": 0.20, "sector": "tech", "momentum": 0.5, "value": 0.8},
            "JPM": {"volatility": 0.18, "sector": "financial", "momentum": 0.4, "value": 0.8},
            "JNJ": {"volatility": 0.15, "sector": "healthcare", "momentum": 0.3, "value": 0.9},
            "PG": {"volatility": 0.12, "sector": "consumer", "momentum": 0.2, "value": 0.9},
            "KO": {"volatility": 0.14, "sector": "consumer", "momentum": 0.2, "value": 0.8},
            "WMT": {"volatility": 0.16, "sector": "consumer", "momentum": 0.3, "value": 0.7}
        }
        
        # Strategy characteristics
        self.strategies = {
            "ElliottWaveImpulse": {"base_return": 0.12, "volatility": 0.25},
            "ElliottWaveCorrective": {"base_return": 0.08, "volatility": 0.20},
            "IronCondor": {"base_return": 0.06, "volatility": 0.15},
            "CalendarSpread": {"base_return": 0.04, "volatility": 0.12}
        }
    
    def get_sector_performance(self, sector: str, day: int) -> float:
        """Get sector performance for a given day"""
        # Simulate sector rotation
        sector_cycles = {
            "tech": 0.1 * np.sin(2 * np.pi * day / 60),      # 60-day cycle
            "financial": 0.08 * np.sin(2 * np.pi * day / 45), # 45-day cycle
            "healthcare": 0.06 * np.sin(2 * np.pi * day / 90), # 90-day cycle
            "consumer": 0.04 * np.sin(2 * np.pi * day / 120), # 120-day cycle
            "automotive": 0.12 * np.sin(2 * np.pi * day / 30), # 30-day cycle
            "fintech": 0.09 * np.sin(2 * np.pi * day / 75)    # 75-day cycle
        }
        
        base_performance = 0.05
        cycle_performance = sector_cycles.get(sector, 0.05)
        random_factor = np.random.normal(0, 0.02)
        
        return base_performance + cycle_performance + random_factor
    
    def calculate_symbol_return(self, symbol: str, strategy: str, day: int) -> float:
        """Calculate symbol return based on characteristics and market conditions"""
        
        char = self.symbol_characteristics[symbol]
        strategy_config = self.strategies[strategy]
        
        # Base return from strategy
        base_return = strategy_config["base_return"]
        
        # Volatility adjustment
        volatility_factor = 1 + (char["volatility"] - 0.25) * 0.5
        
        # Sector performance
        sector_performance = self.get_sector_performance(char["sector"], day)
        
        # Momentum factor
        momentum_factor = 1 + (char["momentum"] - 0.5) * 0.3
        
        # Random factor
        random_factor = np.random.normal(0, char["volatility"])
        
        # Calculate final return
        final_return = (base_return * volatility_factor * momentum_factor + 
                       sector_performance + random_factor)
        
        return final_return
    
    def run_symbol_backtest(self, symbol_set: str, days: int = 120) -> Dict[str, Any]:
        """Run backtest for specific symbol set"""
        
        symbols = self.symbol_sets[symbol_set]["symbols"]
        
        portfolio_value = self.initial_capital
        total_trades = 0
        winning_trades = 0
        total_pnl = 0.0
        max_drawdown = 0.0
        peak_value = self.initial_capital
        trades = []
        daily_returns = []
        sector_performance = {}
        
        for day in range(days):
            daily_pnl = 0.0
            
            # Simulate trades for each strategy
            for strategy_name, strategy_config in self.strategies.items():
                # Number of trades based on strategy allocation
                allocation = 0.25  # Equal allocation for simplicity
                num_trades = max(1, int(allocation * 4 * random.random()))
                
                for _ in range(num_trades):
                    symbol = random.choice(symbols)
                    
                    # Calculate symbol return
                    symbol_return = self.calculate_symbol_return(symbol, strategy_name, day)
                    
                    # Calculate P&L
                    position_size = 0.15  # Fixed 15% position size
                    trade_pnl = symbol_return * position_size * portfolio_value
                    
                    daily_pnl += trade_pnl
                    total_trades += 1
                    total_pnl += trade_pnl
                    
                    if symbol_return > 0:
                        winning_trades += 1
                    
                    trades.append({
                        "day": day,
                        "strategy": strategy_name,
                        "symbol": symbol,
                        "return": symbol_return,
                        "pnl": trade_pnl,
                        "sector": self.symbol_characteristics[symbol]["sector"]
                    })
                    
                    # Track sector performance
                    sector = self.symbol_characteristics[symbol]["sector"]
                    if sector not in sector_performance:
                        sector_performance[sector] = []
                    sector_performance[sector].append(symbol_return)
            
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
        
        # Calculate sector performance metrics
        sector_metrics = {}
        for sector, returns in sector_performance.items():
            sector_metrics[sector] = {
                "avg_return": np.mean(returns),
                "volatility": np.std(returns),
                "total_trades": len(returns)
            }
        
        return {
            "symbol_set": symbol_set,
            "name": self.symbol_sets[symbol_set]["name"],
            "symbols": symbols,
            "final_value": portfolio_value,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "sector_metrics": sector_metrics,
            "trades": trades
        }
    
    def run_comprehensive_symbol_backtest(self, days: int = 120) -> Dict[str, Any]:
        """Run comprehensive backtest for all symbol sets"""
        
        results = {}
        
        for symbol_set_name in self.symbol_sets.keys():
            logger.info(f"🔄 Testing {self.symbol_sets[symbol_set_name]['name']}...")
            
            result = self.run_symbol_backtest(symbol_set_name, days)
            results[symbol_set_name] = result
            
            logger.info(f"✅ {result['name']}: {result['total_return']:.1%} return, {result['win_rate']:.1%} win rate")
        
        return results
    
    def generate_symbol_report(self, results: Dict[str, Any]) -> str:
        """Generate symbol optimization comparison report"""
        
        report = "\n" + "="*80 + "\n"
        report += "📊 SYMBOL OPTIMIZATION & SECTOR ROTATION RESULTS\n"
        report += "="*80 + "\n\n"
        
        # Sort by total return
        sorted_results = sorted(results.items(), key=lambda x: x[1]["total_return"], reverse=True)
        
        report += "📊 SYMBOL SET COMPARISON\n"
        report += "-" * 70 + "\n"
        report += f"{'Symbol Set':<25} {'Return':<10} {'Win Rate':<10} {'Sharpe':<10} {'Max DD':<10}\n"
        report += "-" * 70 + "\n"
        
        for symbol_set_name, result in sorted_results:
            report += f"{result['name']:<25} {result['total_return']:>8.1%} {result['win_rate']:>8.1%} {result['sharpe_ratio']:>8.2f} {result['max_drawdown']:>8.1%}\n"
        
        report += "\n" + "="*80 + "\n"
        report += "🏆 WINNER: " + sorted_results[0][1]["name"] + "\n"
        report += f"💰 Final Value: ${sorted_results[0][1]['final_value']:,.2f}\n"
        report += f"📈 Total Return: {sorted_results[0][1]['total_return']:.1%}\n"
        report += f"🎯 Win Rate: {sorted_results[0][1]['win_rate']:.1%}\n"
        report += f"📊 Sharpe Ratio: {sorted_results[0][1]['sharpe_ratio']:.2f}\n"
        report += f"📉 Max Drawdown: {sorted_results[0][1]['max_drawdown']:.1%}\n\n"
        
        report += "📋 DETAILED SYMBOL ANALYSIS\n"
        report += "="*80 + "\n\n"
        
        for symbol_set_name, result in sorted_results:
            report += f"🔍 {result['name']}\n"
            report += f"   Symbols: {', '.join(result['symbols'])}\n"
            report += f"   Final Value: ${result['final_value']:,.2f}\n"
            report += f"   Total Return: {result['total_return']:.1%}\n"
            report += f"   Win Rate: {result['win_rate']:.1%}\n"
            report += f"   Total Trades: {result['total_trades']:,}\n"
            report += f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}\n"
            report += f"   Max Drawdown: {result['max_drawdown']:.1%}\n"
            report += f"   Sector Performance:\n"
            for sector, metrics in result['sector_metrics'].items():
                report += f"     {sector}: {metrics['avg_return']:.2%} avg return, {metrics['volatility']:.2%} volatility\n"
            report += "\n"
        
        return report

def main():
    """Run the symbol optimization backtest"""
    logger.info("🚀 Starting Symbol Optimization & Sector Rotation Backtest...")
    
    backtest = SymbolOptimizationBacktest()
    results = backtest.run_comprehensive_symbol_backtest(days=120)
    
    report = backtest.generate_symbol_report(results)
    print(report)
    
    # Save results
    with open('symbol_optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("✅ Symbol Optimization Backtest completed!")
    logger.info("📄 Results saved to symbol_optimization_results.json")

if __name__ == "__main__":
    main()
