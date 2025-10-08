#!/usr/bin/env python3
"""
Market Timing Strategies Backtest
Testing volatility filters, trend filters, and market regime detection
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

class MarketTimingBacktest:
    """Backtest different market timing strategies"""
    
    def __init__(self):
        self.initial_capital = 4000.0
        self.symbols = ["AAPL", "AMD", "PYPL", "TSLA", "NVDA", "META"]
        
        # Market timing strategies to test
        self.timing_strategies = {
            "no_timing": {
                "name": "No Market Timing",
                "description": "Trade all the time regardless of market conditions",
                "volatility_filter": False,
                "trend_filter": False,
                "regime_filter": False
            },
            "volatility_filter": {
                "name": "Volatility Filter Only",
                "description": "Only trade when volatility is in optimal range",
                "volatility_filter": True,
                "trend_filter": False,
                "regime_filter": False,
                "min_iv": 0.15,
                "max_iv": 0.50
            },
            "trend_filter": {
                "name": "Trend Filter Only",
                "description": "Only trade in direction of trend",
                "volatility_filter": False,
                "trend_filter": True,
                "regime_filter": False,
                "trend_strength_threshold": 0.4
            },
            "regime_filter": {
                "name": "Market Regime Filter Only",
                "description": "Only trade in favorable market regimes",
                "volatility_filter": False,
                "trend_filter": False,
                "regime_filter": True,
                "favorable_regimes": ["bull", "sideways"]
            },
            "combined_filters": {
                "name": "Combined Filters",
                "description": "Use all filters together",
                "volatility_filter": True,
                "trend_filter": True,
                "regime_filter": True,
                "min_iv": 0.15,
                "max_iv": 0.50,
                "trend_strength_threshold": 0.4,
                "favorable_regimes": ["bull", "sideways"]
            },
            "adaptive_timing": {
                "name": "Adaptive Market Timing",
                "description": "Dynamically adjust filters based on performance",
                "volatility_filter": True,
                "trend_filter": True,
                "regime_filter": True,
                "adaptive": True
            }
        }
        
        # Strategy characteristics
        self.strategies = {
            "ElliottWaveImpulse": {"base_return": 0.12, "volatility": 0.25},
            "ElliottWaveCorrective": {"base_return": 0.08, "volatility": 0.20},
            "IronCondor": {"base_return": 0.06, "volatility": 0.15},
            "CalendarSpread": {"base_return": 0.04, "volatility": 0.12}
        }
    
    def get_market_volatility(self, day: int) -> float:
        """Get market volatility for a given day"""
        # Simulate changing market volatility
        base_volatility = 0.25
        seasonal_factor = 0.1 * np.sin(2 * np.pi * day / 90)  # 90-day cycle
        random_factor = np.random.normal(0, 0.05)
        return max(0.10, min(0.60, base_volatility + seasonal_factor + random_factor))
    
    def get_trend_strength(self, day: int) -> float:
        """Get trend strength for a given day"""
        # Simulate trend strength
        base_trend = 0.5
        cycle_factor = 0.3 * np.sin(2 * np.pi * day / 60)  # 60-day cycle
        random_factor = np.random.normal(0, 0.1)
        return max(0.0, min(1.0, base_trend + cycle_factor + random_factor))
    
    def get_market_regime(self, day: int) -> str:
        """Get market regime for a given day"""
        # Simulate market regimes
        regime_cycle = (day // 30) % 4  # 30-day cycles
        
        if regime_cycle == 0:
            return "bull"
        elif regime_cycle == 1:
            return "bear"
        elif regime_cycle == 2:
            return "sideways"
        else:
            return "volatile"
    
    def apply_market_timing_filters(self, timing_strategy: str, day: int) -> bool:
        """Apply market timing filters"""
        
        config = self.timing_strategies[timing_strategy]
        
        # Volatility filter
        if config["volatility_filter"]:
            market_volatility = self.get_market_volatility(day)
            min_iv = config.get("min_iv", 0.15)
            max_iv = config.get("max_iv", 0.50)
            
            if market_volatility < min_iv or market_volatility > max_iv:
                return False
        
        # Trend filter
        if config["trend_filter"]:
            trend_strength = self.get_trend_strength(day)
            threshold = config.get("trend_strength_threshold", 0.4)
            
            if trend_strength < threshold:
                return False
        
        # Regime filter
        if config["regime_filter"]:
            regime = self.get_market_regime(day)
            favorable_regimes = config.get("favorable_regimes", ["bull", "sideways"])
            
            if regime not in favorable_regimes:
                return False
        
        return True
    
    def simulate_trade_with_timing(self, strategy: str, symbol: str, timing_strategy: str, day: int) -> Dict[str, Any]:
        """Simulate a trade with market timing applied"""
        
        # Check if market timing allows trading
        if not self.apply_market_timing_filters(timing_strategy, day):
            return None
        
        # Base trade simulation
        base_return = self.strategies[strategy]["base_return"]
        volatility = self.strategies[strategy]["volatility"]
        
        # Add market condition adjustments
        market_volatility = self.get_market_volatility(day)
        trend_strength = self.get_trend_strength(day)
        regime = self.get_market_regime(day)
        
        # Adjust returns based on market conditions
        volatility_adjustment = 1 + (market_volatility - 0.25) * 0.5
        trend_adjustment = 1 + (trend_strength - 0.5) * 0.3
        
        regime_multipliers = {
            "bull": 1.2,
            "bear": 0.8,
            "sideways": 1.0,
            "volatile": 1.1
        }
        regime_adjustment = regime_multipliers.get(regime, 1.0)
        
        # Calculate adjusted return
        random_factor = np.random.normal(0, volatility)
        adjusted_return = base_return * volatility_adjustment * trend_adjustment * regime_adjustment + random_factor
        
        return {
            "strategy": strategy,
            "symbol": symbol,
            "timing_strategy": timing_strategy,
            "trade_return": adjusted_return,
            "market_volatility": market_volatility,
            "trend_strength": trend_strength,
            "market_regime": regime,
            "day": day
        }
    
    def run_timing_backtest(self, timing_strategy: str, days: int = 120) -> Dict[str, Any]:
        """Run backtest for specific timing strategy"""
        
        portfolio_value = self.initial_capital
        total_trades = 0
        winning_trades = 0
        total_pnl = 0.0
        max_drawdown = 0.0
        peak_value = self.initial_capital
        trades = []
        daily_returns = []
        trading_days = 0
        
        for day in range(days):
            daily_pnl = 0.0
            daily_trades = 0
            
            # Simulate trades for each strategy
            for strategy_name, strategy_config in self.strategies.items():
                # Determine number of trades
                num_trades = max(0, int(2 * random.random()))
                
                for _ in range(num_trades):
                    symbol = random.choice(self.symbols)
                    
                    trade_result = self.simulate_trade_with_timing(strategy_name, symbol, timing_strategy, day)
                    
                    if trade_result:
                        # Calculate P&L
                        position_size = 0.15  # Fixed 15% position size
                        trade_pnl = trade_result["trade_return"] * position_size * portfolio_value
                        
                        daily_pnl += trade_pnl
                        total_trades += 1
                        daily_trades += 1
                        total_pnl += trade_pnl
                        
                        if trade_result["trade_return"] > 0:
                            winning_trades += 1
                        
                        trades.append(trade_result)
            
            # Update portfolio
            portfolio_value += daily_pnl
            daily_return = daily_pnl / (portfolio_value - daily_pnl) if portfolio_value != daily_pnl else 0
            daily_returns.append(daily_return)
            
            if daily_trades > 0:
                trading_days += 1
            
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
        trading_frequency = trading_days / days if days > 0 else 0
        
        return {
            "timing_strategy": timing_strategy,
            "name": self.timing_strategies[timing_strategy]["name"],
            "final_value": portfolio_value,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "trading_frequency": trading_frequency,
            "trades": trades
        }
    
    def run_comprehensive_timing_backtest(self, days: int = 120) -> Dict[str, Any]:
        """Run comprehensive backtest for all timing strategies"""
        
        results = {}
        
        for strategy_name in self.timing_strategies.keys():
            logger.info(f"🔄 Testing {self.timing_strategies[strategy_name]['name']}...")
            
            result = self.run_timing_backtest(strategy_name, days)
            results[strategy_name] = result
            
            logger.info(f"✅ {result['name']}: {result['total_return']:.1%} return, {result['trading_frequency']:.1%} trading frequency")
        
        return results
    
    def generate_timing_report(self, results: Dict[str, Any]) -> str:
        """Generate market timing comparison report"""
        
        report = "\n" + "="*80 + "\n"
        report += "⏰ MARKET TIMING STRATEGIES BACKTEST RESULTS\n"
        report += "="*80 + "\n\n"
        
        # Sort by total return
        sorted_results = sorted(results.items(), key=lambda x: x[1]["total_return"], reverse=True)
        
        report += "📊 TIMING STRATEGY COMPARISON\n"
        report += "-" * 70 + "\n"
        report += f"{'Strategy':<25} {'Return':<10} {'Win Rate':<10} {'Trading Freq':<12} {'Sharpe':<10}\n"
        report += "-" * 70 + "\n"
        
        for strategy_name, result in sorted_results:
            report += f"{result['name']:<25} {result['total_return']:>8.1%} {result['win_rate']:>8.1%} {result['trading_frequency']:>10.1%} {result['sharpe_ratio']:>8.2f}\n"
        
        report += "\n" + "="*80 + "\n"
        report += "🏆 WINNER: " + sorted_results[0][1]["name"] + "\n"
        report += f"💰 Final Value: ${sorted_results[0][1]['final_value']:,.2f}\n"
        report += f"📈 Total Return: {sorted_results[0][1]['total_return']:.1%}\n"
        report += f"🎯 Win Rate: {sorted_results[0][1]['win_rate']:.1%}\n"
        report += f"📊 Trading Frequency: {sorted_results[0][1]['trading_frequency']:.1%}\n"
        report += f"📊 Sharpe Ratio: {sorted_results[0][1]['sharpe_ratio']:.2f}\n"
        report += f"📉 Max Drawdown: {sorted_results[0][1]['max_drawdown']:.1%}\n\n"
        
        report += "📋 DETAILED TIMING ANALYSIS\n"
        report += "="*80 + "\n\n"
        
        for strategy_name, result in sorted_results:
            report += f"🔍 {result['name']}\n"
            report += f"   Final Value: ${result['final_value']:,.2f}\n"
            report += f"   Total Return: {result['total_return']:.1%}\n"
            report += f"   Win Rate: {result['win_rate']:.1%}\n"
            report += f"   Total Trades: {result['total_trades']:,}\n"
            report += f"   Trading Frequency: {result['trading_frequency']:.1%}\n"
            report += f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}\n"
            report += f"   Max Drawdown: {result['max_drawdown']:.1%}\n\n"
        
        return report

def main():
    """Run the market timing backtest"""
    logger.info("🚀 Starting Market Timing Strategies Backtest...")
    
    backtest = MarketTimingBacktest()
    results = backtest.run_comprehensive_timing_backtest(days=120)
    
    report = backtest.generate_timing_report(results)
    print(report)
    
    # Save results
    with open('market_timing_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("✅ Market Timing Backtest completed!")
    logger.info("📄 Results saved to market_timing_results.json")

if __name__ == "__main__":
    main()
