#!/usr/bin/env python3
"""
Real Data Analysis Script
========================

Runs comprehensive strategy analysis using REAL historical data
from our TimescaleDB database. Designed to run inside the strategy service container.
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
import json

# Add the strategy service path
sys.path.append('/app/src')

# Import our fixed components
from src.backtesting.engine.backtest_engine import BacktestEngine

# Configuration
INITIAL_CAPITAL = 2000.0
BACKTEST_PERIOD = "2023-09-19 to 2024-09-19"  # 1 year of real data

# Assets to test - using REAL data from our database
ASSETS = [
    # Top liquid stocks with good options
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "WFC", "GS", "JNJ", "PFE", "UNH", "HD", "CAT", "BA", "DIS",
    "PYPL", "NFLX", "SPY", "QQQ"
]

# Focus on stock strategies that work well with real data
STRATEGIES = [
    "RSI",             # Momentum oscillator - proven performer
    "MACD",            # Trend following - reliable
    "BollingerBands",  # Mean reversion - good for volatile stocks
    "MeanReversion",   # Mean reversion - consistent
    "Momentum",        # Trend following - good returns
]

class RealDataAnalyzer:
    """Analyzer using real historical data."""
    
    def __init__(self):
        # Use REAL data from database
        self.engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        self.results = []
        self.asset_analysis = {}
        
    async def run_analysis(self):
        """Run analysis with real data."""
        
        print("🚀 REAL DATA STRATEGY ANALYSIS")
        print("=" * 50)
        print("📊 USING REAL HISTORICAL DATA FROM TIMESCALEDB")
        print(f"💰 Initial Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"📅 Period: {BACKTEST_PERIOD}")
        print(f"📊 Assets: {len(ASSETS)} symbols")
        print(f"📈 Strategies: {len(STRATEGIES)} stock strategies")
        print(f"🔬 Total Tests: {len(ASSETS) * len(STRATEGIES)} combinations")
        print()
        
        total_tests = len(ASSETS) * len(STRATEGIES)
        completed_tests = 0
        
        # Test each asset with each strategy
        for asset in ASSETS:
            print(f"📈 Analyzing {asset}...")
            
            asset_results = []
            
            for strategy in STRATEGIES:
                print(f"  🔄 Testing {strategy} on {asset}...")
                
                try:
                    # Run backtest with real data
                    results = await self.engine.run_backtest(
                        symbols=[asset],
                        start_date="2023-09-19",
                        end_date="2024-09-19",
                        strategies=[strategy]
                    )
                    
                    if results and strategy in results and results[strategy] is not None:
                        result = results[strategy]
                        
                        # Analyze result
                        analysis = self._analyze_result(asset, strategy, result)
                        asset_results.append(analysis)
                        
                        print(f"    ✅ {strategy}: {result.total_return:.1%} return, {result.total_trades} trades")
                    else:
                        print(f"    ❌ {strategy}: No results")
                        
                except Exception as e:
                    print(f"    ❌ {strategy}: Error - {e}")
                    
                completed_tests += 1
                
                # Progress update
                if completed_tests % 10 == 0:
                    progress = (completed_tests / total_tests) * 100
                    print(f"    📊 Progress: {completed_tests}/{total_tests} ({progress:.1f}%)")
            
            self.asset_analysis[asset] = asset_results
            
        print(f"\n✅ Completed {completed_tests}/{total_tests} tests")
        
        # Analyze results
        await self._analyze_results()
        
    def _analyze_result(self, asset: str, strategy: str, result) -> Dict:
        """Analyze individual backtest result."""
        
        # Calculate metrics
        final_value = INITIAL_CAPITAL * (1 + result.total_return)
        profit_loss = final_value - INITIAL_CAPITAL
        
        # Risk metrics
        max_loss = INITIAL_CAPITAL * abs(result.max_drawdown) if hasattr(result, 'max_drawdown') else 0
        risk_reward_ratio = profit_loss / max_loss if max_loss > 0 else float('inf')
        
        # Consistency metrics
        avg_trade_return = result.total_return / max(result.total_trades, 1)
        trade_frequency = result.total_trades / 252  # trades per trading day
        
        return {
            'asset': asset,
            'strategy': strategy,
            'total_return': result.total_return,
            'total_return_pct': result.total_return * 100,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'max_drawdown_pct': result.max_drawdown * 100,
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'win_rate': result.win_rate,
            'profit_factor': result.profit_factor,
            'avg_win': result.avg_win,
            'avg_loss': result.avg_loss,
            'final_value': final_value,
            'profit_loss': profit_loss,
            'max_loss': max_loss,
            'risk_reward_ratio': risk_reward_ratio,
            'avg_trade_return': avg_trade_return,
            'trade_frequency': trade_frequency,
            'consistency_score': self._calculate_consistency_score(result)
        }
    
    def _calculate_consistency_score(self, result) -> float:
        """Calculate consistency score."""
        
        # Factors for consistency
        win_rate_score = min(result.win_rate * 100, 100)
        sharpe_score = min(max(result.sharpe_ratio * 20, 0), 100)
        drawdown_score = max(100 - (abs(result.max_drawdown) * 400), 0)
        
        # Trade frequency bonus
        frequency_bonus = min(result.total_trades * 2, 20)
        
        consistency = (win_rate_score * 0.4 + sharpe_score * 0.3 + drawdown_score * 0.3) + frequency_bonus
        
        return min(consistency, 100)
    
    async def _analyze_results(self):
        """Analyze and rank all results."""
        
        print("\n📊 REAL DATA ANALYSIS RESULTS")
        print("=" * 50)
        
        # Collect all results
        all_results = []
        for asset_results in self.asset_analysis.values():
            all_results.extend(asset_results)
        
        if not all_results:
            print("❌ No successful backtests to analyze")
            return
        
        # Filter for meaningful results
        meaningful_results = [r for r in all_results if r['total_trades'] > 0]
        
        if not meaningful_results:
            print("⚠️ No strategies generated any trades")
            return
        
        print(f"📈 Found {len(meaningful_results)} strategies with trades out of {len(all_results)} total tests")
        
        # Sort by different criteria
        by_return = sorted(meaningful_results, key=lambda x: x['total_return'], reverse=True)
        by_sharpe = sorted(meaningful_results, key=lambda x: x['sharpe_ratio'], reverse=True)
        by_consistency = sorted(meaningful_results, key=lambda x: x['consistency_score'], reverse=True)
        
        # Display top performers
        self._display_top_performers("💰 HIGHEST RETURNS", by_return, "total_return_pct", "%")
        self._display_top_performers("📈 BEST SHARPE RATIO", by_sharpe, "sharpe_ratio", "")
        self._display_top_performers("🎯 MOST CONSISTENT", by_consistency, "consistency_score", "/100")
        
        # Generate recommendations
        self._generate_recommendations(meaningful_results)
        
        # Save results
        self._save_results(all_results)
    
    def _display_top_performers(self, title: str, results: List[Dict], metric: str, unit: str):
        """Display top performers."""
        
        print(f"\n{title}")
        print("-" * 30)
        
        for i, result in enumerate(results[:5], 1):
            value = result[metric]
            print(f"{i}. {result['asset']} + {result['strategy']}: {value:.2f}{unit}")
            print(f"   Return: {result['total_return_pct']:.1f}%, "
                  f"Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
    
    def _generate_recommendations(self, results: List[Dict]):
        """Generate recommendations."""
        
        print(f"\n🎯 PAPER TRADING RECOMMENDATIONS")
        print("=" * 40)
        
        # Filter for good performance
        good_results = [
            r for r in results 
            if r['total_return'] > -0.2 and r['max_drawdown'] > -0.5 and r['total_trades'] > 5
        ]
        
        if not good_results:
            print("⚠️ No results meet basic performance criteria")
            return
        
        # Sort by composite score
        def composite_score(result):
            return (result['consistency_score'] * 0.4 + 
                   min(result['total_return'] * 100 + 50, 100) * 0.4 + 
                   min(result['sharpe_ratio'] * 20 + 50, 100) * 0.2)
        
        good_results.sort(key=composite_score, reverse=True)
        
        print("🏆 TOP RECOMMENDATIONS:")
        print()
        
        for i, result in enumerate(good_results[:10], 1):
            print(f"{i:2}. {result['asset']} + {result['strategy']}")
            print(f"    💰 Final Value: ${result['final_value']:,.2f} "
                  f"(+${result['profit_loss']:,.2f})")
            print(f"    📊 Return: {result['total_return_pct']:.1f}%, "
                  f"Sharpe: {result['sharpe_ratio']:.2f}, "
                  f"Max DD: {result['max_drawdown_pct']:.1f}%")
            print(f"    🎯 Consistency: {result['consistency_score']:.1f}/100, "
                  f"Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
            print()
        
        # Portfolio recommendation
        print("💼 RECOMMENDED PORTFOLIO:")
        print()
        
        portfolio_value = INITIAL_CAPITAL
        top_3 = good_results[:3]
        
        for i, result in enumerate(top_3, 1):
            allocation = INITIAL_CAPITAL / len(top_3)
            expected_return = result['total_return']
            expected_value = allocation * (1 + expected_return)
            
            print(f"{i}. {result['asset']} + {result['strategy']}: "
                  f"${allocation:,.0f} → ${expected_value:,.0f}")
            
            portfolio_value += (expected_value - allocation)
        
        print(f"\n💡 PORTFOLIO PROJECTION:")
        print(f"   Initial: ${INITIAL_CAPITAL:,.2f}")
        print(f"   Expected: ${portfolio_value:,.2f}")
        print(f"   Profit: ${portfolio_value - INITIAL_CAPITAL:,.2f}")
        print(f"   Return: {((portfolio_value / INITIAL_CAPITAL) - 1):.1%}")
    
    def _save_results(self, all_results: List[Dict]):
        """Save results to JSON."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_data_analysis_{timestamp}.json"
        
        json_data = {
            'timestamp': timestamp,
            'config': {
                'initial_capital': INITIAL_CAPITAL,
                'backtest_period': BACKTEST_PERIOD,
                'assets_tested': ASSETS,
                'strategies_tested': STRATEGIES
            },
            'results': all_results,
            'summary': {
                'total_tests': len(all_results),
                'successful_tests': len([r for r in all_results if r['total_trades'] > 0]),
                'best_return': max([r['total_return'] for r in all_results]) if all_results else 0,
                'best_sharpe': max([r['sharpe_ratio'] for r in all_results]) if all_results else 0
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")


async def main():
    """Run the real data analysis."""
    
    analyzer = RealDataAnalyzer()
    
    try:
        await analyzer.run_analysis()
        print(f"\n🎉 REAL DATA ANALYSIS COMPLETE!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


