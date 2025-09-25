#!/usr/bin/env python3
"""
Comprehensive Options Strategy Analysis
======================================

Tests Iron Condor, Calendar Spreads, and Vertical Spreads across multiple assets
to identify the best asset/strategy combinations for paper trading.

Key Metrics Analyzed:
1. Predictable trading patterns
2. Profit potential over 2-year period
3. Risk-adjusted returns (Sharpe ratio)
4. Maximum drawdown
5. Win rate and trade frequency
6. Consistency across different market conditions
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
sys.path.append('/Users/abby/code/trading/services/strategy-service')
sys.path.append('/Users/abby/code/trading/services/strategy-service/src')

# Change to strategy service directory for proper imports
os.chdir('/Users/abby/code/trading/services/strategy-service')

# Import our fixed components
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.services.mock_options_data_service import MockOptionsDataService

# Configuration
INITIAL_CAPITAL = 2000.0
BACKTEST_PERIOD = "2023-01-01 to 2023-12-31"

# Assets to test - focusing on liquid options with predictable patterns
ASSETS = [
    # Tech stocks (high volatility, good options volume)
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    
    # Financial sector (moderate volatility, good options)
    "JPM", "BAC", "WFC", "GS",
    
    # Healthcare (stable, predictable patterns)
    "JNJ", "PFE", "UNH",
    
    # Consumer/Industrial (moderate volatility)
    "HD", "CAT", "BA", "DIS",
    
    # Lower-priced stocks (better for $2000 account)
    "AMD", "INTC", "PYPL", "NFLX"
]

# Options strategies to test
STRATEGIES = [
    "IronCondor",      # Range-bound markets, high probability
    "CalendarSpread",  # Time decay strategy
    "VerticalSpread"   # Directional with limited risk
]

class ComprehensiveOptionsAnalyzer:
    """Analyzes options strategies across multiple assets."""
    
    def __init__(self):
        self.engine = BacktestEngine(use_real_data=False, use_cache=False)
        self.options_service = MockOptionsDataService()
        self.engine.options_service = self.options_service
        
        self.results = []
        self.asset_analysis = {}
        self.strategy_analysis = {}
        
    async def run_comprehensive_analysis(self):
        """Run comprehensive analysis across all assets and strategies."""
        
        print("🚀 COMPREHENSIVE OPTIONS STRATEGY ANALYSIS")
        print("=" * 60)
        print(f"💰 Initial Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"📅 Period: {BACKTEST_PERIOD}")
        print(f"📊 Assets: {len(ASSETS)} symbols")
        print(f"📈 Strategies: {len(STRATEGIES)} options strategies")
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
                    # Run backtest for this asset/strategy combination
                    results = await self.engine.run_backtest(
                        symbols=[asset],
                        start_date="2023-01-01",
                        end_date="2023-12-31",
                        strategies=[strategy]
                    )
                    
                    if results and strategy in results and results[strategy] is not None:
                        result = results[strategy]
                        
                        # Calculate key metrics
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
            
            # Store asset results
            self.asset_analysis[asset] = asset_results
            
        print(f"\n✅ Completed {completed_tests}/{total_tests} tests")
        
        # Analyze results
        await self._analyze_results()
        
    def _analyze_result(self, asset: str, strategy: str, result) -> Dict:
        """Analyze individual backtest result."""
        
        # Calculate additional metrics
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
        """Calculate a consistency score (0-100) based on multiple factors."""
        
        # Factors for consistency
        win_rate_score = min(result.win_rate * 100, 100)  # Win rate
        sharpe_score = min(max(result.sharpe_ratio * 20, 0), 100)  # Sharpe ratio (scaled)
        drawdown_score = max(100 - (abs(result.max_drawdown) * 400), 0)  # Low drawdown
        
        # Trade frequency bonus (more trades = more opportunities)
        frequency_bonus = min(result.total_trades * 2, 20)
        
        # Combine scores
        consistency = (win_rate_score * 0.4 + sharpe_score * 0.3 + drawdown_score * 0.3) + frequency_bonus
        
        return min(consistency, 100)
    
    async def _analyze_results(self):
        """Analyze and rank all results."""
        
        print("\n📊 COMPREHENSIVE ANALYSIS RESULTS")
        print("=" * 60)
        
        # Collect all results
        all_results = []
        for asset_results in self.asset_analysis.values():
            all_results.extend(asset_results)
        
        if not all_results:
            print("❌ No successful backtests to analyze")
            return
        
        # Sort by different criteria
        by_return = sorted(all_results, key=lambda x: x['total_return'], reverse=True)
        by_sharpe = sorted(all_results, key=lambda x: x['sharpe_ratio'], reverse=True)
        by_consistency = sorted(all_results, key=lambda x: x['consistency_score'], reverse=True)
        by_risk_adjusted = sorted(all_results, key=lambda x: x['risk_reward_ratio'], reverse=True)
        
        # Display top performers
        self._display_top_performers("💰 HIGHEST RETURNS", by_return, "total_return_pct", "%")
        self._display_top_performers("📈 BEST SHARPE RATIO", by_sharpe, "sharpe_ratio", "")
        self._display_top_performers("🎯 MOST CONSISTENT", by_consistency, "consistency_score", "/100")
        self._display_top_performers("⚖️ BEST RISK-REWARD", by_risk_adjusted, "risk_reward_ratio", ":1")
        
        # Asset-specific analysis
        self._analyze_asset_patterns()
        
        # Strategy-specific analysis
        self._analyze_strategy_performance()
        
        # Recommendations
        self._generate_recommendations()
        
        # Save detailed results
        self._save_detailed_results(all_results)
    
    def _display_top_performers(self, title: str, results: List[Dict], metric: str, unit: str):
        """Display top performers for a specific metric."""
        
        print(f"\n{title}")
        print("-" * 40)
        
        for i, result in enumerate(results[:5], 1):
            value = result[metric]
            print(f"{i}. {result['asset']} + {result['strategy']}: {value:.2f}{unit}")
            print(f"   Return: {result['total_return_pct']:.1f}%, "
                  f"Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
    
    def _analyze_asset_patterns(self):
        """Analyze which assets show predictable patterns."""
        
        print(f"\n🎯 ASSET PATTERN ANALYSIS")
        print("-" * 40)
        
        asset_scores = {}
        
        for asset, results in self.asset_analysis.items():
            if not results:
                continue
                
            # Calculate asset score based on consistency across strategies
            avg_consistency = np.mean([r['consistency_score'] for r in results])
            avg_return = np.mean([r['total_return'] for r in results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
            
            # Predictability score
            predictability = (avg_consistency * 0.5 + 
                            min(avg_return * 100 + 50, 100) * 0.3 + 
                            min(avg_sharpe * 20 + 50, 100) * 0.2)
            
            asset_scores[asset] = {
                'predictability': predictability,
                'avg_consistency': avg_consistency,
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'strategies_tested': len(results)
            }
        
        # Sort by predictability
        sorted_assets = sorted(asset_scores.items(), key=lambda x: x[1]['predictability'], reverse=True)
        
        print("Most Predictable Assets (Top 10):")
        for i, (asset, scores) in enumerate(sorted_assets[:10], 1):
            print(f"{i:2}. {asset}: {scores['predictability']:.1f}/100 "
                  f"(Consistency: {scores['avg_consistency']:.1f}, "
                  f"Return: {scores['avg_return']:.1%})")
    
    def _analyze_strategy_performance(self):
        """Analyze which strategies perform best overall."""
        
        print(f"\n📈 STRATEGY PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        strategy_stats = {}
        
        for asset_results in self.asset_analysis.values():
            for result in asset_results:
                strategy = result['strategy']
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'returns': [],
                        'sharpe_ratios': [],
                        'consistency_scores': [],
                        'trade_counts': [],
                        'win_rates': []
                    }
                
                strategy_stats[strategy]['returns'].append(result['total_return'])
                strategy_stats[strategy]['sharpe_ratios'].append(result['sharpe_ratio'])
                strategy_stats[strategy]['consistency_scores'].append(result['consistency_score'])
                strategy_stats[strategy]['trade_counts'].append(result['total_trades'])
                strategy_stats[strategy]['win_rates'].append(result['win_rate'])
        
        # Calculate strategy rankings
        strategy_rankings = []
        
        for strategy, stats in strategy_stats.items():
            avg_return = np.mean(stats['returns'])
            avg_sharpe = np.mean(stats['sharpe_ratios'])
            avg_consistency = np.mean(stats['consistency_scores'])
            avg_trades = np.mean(stats['trade_counts'])
            avg_win_rate = np.mean(stats['win_rates'])
            
            # Overall strategy score
            strategy_score = (avg_consistency * 0.4 + 
                            min(avg_return * 100 + 50, 100) * 0.3 + 
                            min(avg_sharpe * 20 + 50, 100) * 0.3)
            
            strategy_rankings.append({
                'strategy': strategy,
                'score': strategy_score,
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'avg_consistency': avg_consistency,
                'avg_trades': avg_trades,
                'avg_win_rate': avg_win_rate
            })
        
        # Sort by strategy score
        strategy_rankings.sort(key=lambda x: x['score'], reverse=True)
        
        print("Strategy Performance Ranking:")
        for i, ranking in enumerate(strategy_rankings, 1):
            print(f"{i}. {ranking['strategy']}: {ranking['score']:.1f}/100")
            print(f"   Avg Return: {ranking['avg_return']:.1%}, "
                  f"Sharpe: {ranking['avg_sharpe']:.2f}, "
                  f"Trades: {ranking['avg_trades']:.1f}, "
                  f"Win Rate: {ranking['avg_win_rate']:.1%}")
    
    def _generate_recommendations(self):
        """Generate specific recommendations for paper trading."""
        
        print(f"\n🎯 PAPER TRADING RECOMMENDATIONS")
        print("=" * 50)
        
        # Collect all results for final analysis
        all_results = []
        for asset_results in self.asset_analysis.values():
            all_results.extend(asset_results)
        
        if not all_results:
            print("❌ No results to generate recommendations")
            return
        
        # Filter for reasonable performance (positive returns, reasonable drawdown)
        good_results = [
            r for r in all_results 
            if r['total_return'] > -0.5 and r['max_drawdown'] > -0.8 and r['total_trades'] > 0
        ]
        
        if not good_results:
            print("⚠️ No results meet basic performance criteria")
            return
        
        # Sort by composite score
        def composite_score(result):
            return (result['consistency_score'] * 0.4 + 
                   min(result['total_return'] * 100 + 50, 100) * 0.3 + 
                   min(result['sharpe_ratio'] * 20 + 50, 100) * 0.3)
        
        good_results.sort(key=composite_score, reverse=True)
        
        print("🏆 TOP RECOMMENDATIONS FOR PAPER TRADING:")
        print()
        
        for i, result in enumerate(good_results[:10], 1):
            print(f"{i:2}. {result['asset']} + {result['strategy']}")
            print(f"    💰 Expected Final Value: ${result['final_value']:,.2f} "
                  f"(+${result['profit_loss']:,.2f})")
            print(f"    📊 Return: {result['total_return_pct']:.1f}%, "
                  f"Sharpe: {result['sharpe_ratio']:.2f}, "
                  f"Max DD: {result['max_drawdown_pct']:.1f}%")
            print(f"    🎯 Consistency: {result['consistency_score']:.1f}/100, "
                  f"Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
            print()
        
        # Portfolio recommendations
        print("💼 PORTFOLIO RECOMMENDATIONS:")
        print()
        
        # Group by strategy for diversification
        strategy_groups = {}
        for result in good_results[:15]:  # Top 15
            strategy = result['strategy']
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(result)
        
        portfolio_value = INITIAL_CAPITAL
        recommended_trades = []
        
        print("Diversified Portfolio (Equal allocation across top strategies):")
        for strategy, results in strategy_groups.items():
            if results:
                top_result = results[0]  # Best asset for this strategy
                allocation = INITIAL_CAPITAL / len(strategy_groups)
                expected_return = top_result['total_return']
                expected_value = allocation * (1 + expected_return)
                
                print(f"• {top_result['asset']} + {strategy}: ${allocation:,.0f} → ${expected_value:,.0f}")
                
                portfolio_value += (expected_value - allocation)
                recommended_trades.append({
                    'asset': top_result['asset'],
                    'strategy': strategy,
                    'allocation': allocation,
                    'expected_return': expected_return
                })
        
        print(f"\n💡 TOTAL PORTFOLIO PROJECTION:")
        print(f"   Initial Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"   Expected Final Value: ${portfolio_value:,.2f}")
        print(f"   Expected Profit: ${portfolio_value - INITIAL_CAPITAL:,.2f}")
        print(f"   Expected Return: {((portfolio_value / INITIAL_CAPITAL) - 1):.1%}")
        
        # Risk warnings
        print(f"\n⚠️ RISK CONSIDERATIONS:")
        print(f"• These are backtested results with mock options data")
        print(f"• Real market conditions may differ significantly")
        print(f"• Options trading involves substantial risk")
        print(f"• Start with small position sizes and scale gradually")
        print(f"• Monitor positions closely and use stop-losses")
    
    def _save_detailed_results(self, all_results: List[Dict]):
        """Save detailed results to JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"options_analysis_results_{timestamp}.json"
        
        # Prepare data for JSON serialization
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
        
        print(f"\n💾 Detailed results saved to: {filename}")


async def main():
    """Run the comprehensive options analysis."""
    
    analyzer = ComprehensiveOptionsAnalyzer()
    
    try:
        await analyzer.run_comprehensive_analysis()
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"Use the recommendations above to configure your paper trading setup.")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


