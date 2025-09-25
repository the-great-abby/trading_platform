#!/usr/bin/env python3
"""
Enhanced Comprehensive Strategy Analysis
========================================

Tests both options and stock strategies across multiple assets to identify
the best combinations for paper trading with $2000 account.

Includes:
- Options strategies: Iron Condor, Calendar Spread
- Stock strategies: RSI, MACD, Bollinger Bands, Mean Reversion, Momentum
- Comprehensive metrics and recommendations
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
BACKTEST_PERIOD = "2023-09-19 to 2025-09-19"  # Actual data range we have

# Assets to test - using REAL data from our database (66 symbols available)
# Focusing on liquid options with predictable patterns and good volatility
ASSETS = [
    # Tech stocks (high volatility, excellent options volume)
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "AMD", "INTC",
    
    # Financial sector (moderate volatility, good options)
    "JPM", "BAC", "WFC", "GS", "AXP", "C",
    
    # Healthcare (stable, predictable patterns)
    "JNJ", "PFE", "UNH", "LLY", "MRK",
    
    # Consumer/Industrial (moderate volatility)
    "HD", "CAT", "BA", "DIS", "MCD", "NKE", "SBUX", "WMT",
    
    # Energy & Materials (volatile, good for options)
    "XOM", "CVX", "COP", "EOG", "SLB",
    
    # Lower-priced stocks (better for $2000 account)
    "PYPL", "NFLX", "CRM", "ADBE", "ORCL",
    
    # ETFs (diversified, lower volatility)
    "SPY", "QQQ", "VTI", "VOO"
]

# Mixed strategies - options and stock strategies
STRATEGIES = [
    # Options strategies
    "IronCondor",      # Range-bound markets, high probability
    "CalendarSpread",  # Time decay strategy
    
    # Stock strategies (proven performers)
    "RSI",             # Momentum oscillator
    "MACD",            # Trend following
    "BollingerBands",  # Mean reversion
    "MeanReversion",   # Mean reversion
    "Momentum",        # Trend following
]

class EnhancedComprehensiveAnalyzer:
    """Enhanced analyzer for both options and stock strategies."""
    
    def __init__(self):
        # Use REAL historical data from our database
        self.engine = BacktestEngine(use_real_data=True, use_cache=True)
        self.options_service = MockOptionsDataService()
        self.engine.options_service = self.options_service
        
        self.results = []
        self.asset_analysis = {}
        self.strategy_analysis = {}
        
    async def run_comprehensive_analysis(self):
        """Run comprehensive analysis across all assets and strategies."""
        
        print("🚀 ENHANCED COMPREHENSIVE STRATEGY ANALYSIS")
        print("=" * 60)
        print("📊 USING REAL HISTORICAL DATA FROM OUR DATABASE")
        print(f"💰 Initial Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"📅 Period: {BACKTEST_PERIOD}")
        print(f"📊 Assets: {len(ASSETS)} symbols (from 66 available in database)")
        print(f"📈 Strategies: {len(STRATEGIES)} strategies ({len([s for s in STRATEGIES if 'Condor' in s or 'Spread' in s])} options, {len([s for s in STRATEGIES if s not in ['IronCondor', 'CalendarSpread']])} stock)")
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
                    # Run backtest for this asset/strategy combination using REAL data
                    results = await self.engine.run_backtest(
                        symbols=[asset],
                        start_date="2023-09-19",
                        end_date="2024-09-19",  # Use 1 year of real data for testing
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
                if completed_tests % 15 == 0:
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
        
        # Strategy type classification
        strategy_type = "Options" if strategy in ["IronCondor", "CalendarSpread"] else "Stock"
        
        return {
            'asset': asset,
            'strategy': strategy,
            'strategy_type': strategy_type,
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
            'consistency_score': self._calculate_consistency_score(result),
            'capital_efficiency': self._calculate_capital_efficiency(result)
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
    
    def _calculate_capital_efficiency(self, result) -> float:
        """Calculate capital efficiency score."""
        
        if result.total_trades == 0:
            return 0
        
        # Capital efficiency = return per trade / max drawdown
        return_per_trade = result.total_return / result.total_trades
        max_dd = abs(result.max_drawdown)
        
        if max_dd == 0:
            return 100
        
        efficiency = (return_per_trade / max_dd) * 100
        return min(max(efficiency, 0), 100)
    
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
        
        # Filter for meaningful results (at least some trades)
        meaningful_results = [r for r in all_results if r['total_trades'] > 0]
        
        if not meaningful_results:
            print("⚠️ No strategies generated any trades")
            print("This suggests the strategies need better market data or parameter tuning")
            return
        
        print(f"📈 Found {len(meaningful_results)} strategies with trades out of {len(all_results)} total tests")
        
        # Sort by different criteria
        by_return = sorted(meaningful_results, key=lambda x: x['total_return'], reverse=True)
        by_sharpe = sorted(meaningful_results, key=lambda x: x['sharpe_ratio'], reverse=True)
        by_consistency = sorted(meaningful_results, key=lambda x: x['consistency_score'], reverse=True)
        by_capital_efficiency = sorted(meaningful_results, key=lambda x: x['capital_efficiency'], reverse=True)
        
        # Display top performers
        self._display_top_performers("💰 HIGHEST RETURNS", by_return, "total_return_pct", "%")
        self._display_top_performers("📈 BEST SHARPE RATIO", by_sharpe, "sharpe_ratio", "")
        self._display_top_performers("🎯 MOST CONSISTENT", by_consistency, "consistency_score", "/100")
        self._display_top_performers("⚡ CAPITAL EFFICIENT", by_capital_efficiency, "capital_efficiency", "/100")
        
        # Strategy type analysis
        self._analyze_strategy_types(meaningful_results)
        
        # Asset-specific analysis
        self._analyze_asset_patterns(meaningful_results)
        
        # Recommendations
        self._generate_recommendations(meaningful_results)
        
        # Save detailed results
        self._save_detailed_results(all_results)
    
    def _display_top_performers(self, title: str, results: List[Dict], metric: str, unit: str):
        """Display top performers for a specific metric."""
        
        print(f"\n{title}")
        print("-" * 40)
        
        for i, result in enumerate(results[:5], 1):
            value = result[metric]
            print(f"{i}. {result['asset']} + {result['strategy']} ({result['strategy_type']}): {value:.2f}{unit}")
            print(f"   Return: {result['total_return_pct']:.1f}%, "
                  f"Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
    
    def _analyze_strategy_types(self, results: List[Dict]):
        """Analyze performance by strategy type."""
        
        print(f"\n📊 STRATEGY TYPE ANALYSIS")
        print("-" * 40)
        
        strategy_types = {}
        for result in results:
            strategy_type = result['strategy_type']
            if strategy_type not in strategy_types:
                strategy_types[strategy_type] = []
            strategy_types[strategy_type].append(result)
        
        for strategy_type, type_results in strategy_types.items():
            avg_return = np.mean([r['total_return'] for r in type_results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in type_results])
            avg_trades = np.mean([r['total_trades'] for r in type_results])
            avg_win_rate = np.mean([r['win_rate'] for r in type_results])
            
            print(f"{strategy_type} Strategies ({len(type_results)} combinations):")
            print(f"  Avg Return: {avg_return:.1%}")
            print(f"  Avg Sharpe: {avg_sharpe:.2f}")
            print(f"  Avg Trades: {avg_trades:.1f}")
            print(f"  Avg Win Rate: {avg_win_rate:.1%}")
            print()
    
    def _analyze_asset_patterns(self, results: List[Dict]):
        """Analyze which assets show predictable patterns."""
        
        print(f"🎯 ASSET PATTERN ANALYSIS")
        print("-" * 40)
        
        asset_scores = {}
        
        # Group results by asset
        asset_groups = {}
        for result in results:
            asset = result['asset']
            if asset not in asset_groups:
                asset_groups[asset] = []
            asset_groups[asset].append(result)
        
        for asset, asset_results in asset_groups.items():
            # Calculate asset score based on consistency across strategies
            avg_consistency = np.mean([r['consistency_score'] for r in asset_results])
            avg_return = np.mean([r['total_return'] for r in asset_results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in asset_results])
            avg_capital_efficiency = np.mean([r['capital_efficiency'] for r in asset_results])
            
            # Predictability score
            predictability = (avg_consistency * 0.3 + 
                            min(avg_return * 100 + 50, 100) * 0.3 + 
                            min(avg_sharpe * 20 + 50, 100) * 0.2 +
                            avg_capital_efficiency * 0.2)
            
            asset_scores[asset] = {
                'predictability': predictability,
                'avg_consistency': avg_consistency,
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'avg_capital_efficiency': avg_capital_efficiency,
                'strategies_tested': len(asset_results)
            }
        
        # Sort by predictability
        sorted_assets = sorted(asset_scores.items(), key=lambda x: x[1]['predictability'], reverse=True)
        
        print("Most Predictable Assets (Top 10):")
        for i, (asset, scores) in enumerate(sorted_assets[:10], 1):
            print(f"{i:2}. {asset}: {scores['predictability']:.1f}/100")
            print(f"    Consistency: {scores['avg_consistency']:.1f}, "
                  f"Return: {scores['avg_return']:.1%}, "
                  f"Capital Efficiency: {scores['avg_capital_efficiency']:.1f}")
    
    def _generate_recommendations(self, results: List[Dict]):
        """Generate specific recommendations for paper trading."""
        
        print(f"\n🎯 PAPER TRADING RECOMMENDATIONS")
        print("=" * 50)
        
        # Filter for reasonable performance
        good_results = [
            r for r in results 
            if r['total_return'] > -0.3 and r['max_drawdown'] > -0.6 and r['total_trades'] > 5
        ]
        
        if not good_results:
            print("⚠️ No results meet basic performance criteria")
            print("Consider:")
            print("- Using different strategy parameters")
            print("- Testing with different time periods")
            print("- Focusing on stock strategies instead of options")
            return
        
        # Sort by composite score
        def composite_score(result):
            return (result['consistency_score'] * 0.3 + 
                   min(result['total_return'] * 100 + 50, 100) * 0.3 + 
                   min(result['sharpe_ratio'] * 20 + 50, 100) * 0.2 +
                   result['capital_efficiency'] * 0.2)
        
        good_results.sort(key=composite_score, reverse=True)
        
        print("🏆 TOP RECOMMENDATIONS FOR PAPER TRADING:")
        print()
        
        for i, result in enumerate(good_results[:10], 1):
            print(f"{i:2}. {result['asset']} + {result['strategy']} ({result['strategy_type']})")
            print(f"    💰 Expected Final Value: ${result['final_value']:,.2f} "
                  f"(+${result['profit_loss']:,.2f})")
            print(f"    📊 Return: {result['total_return_pct']:.1f}%, "
                  f"Sharpe: {result['sharpe_ratio']:.2f}, "
                  f"Max DD: {result['max_drawdown_pct']:.1f}%")
            print(f"    🎯 Consistency: {result['consistency_score']:.1f}/100, "
                  f"Capital Efficiency: {result['capital_efficiency']:.1f}/100")
            print(f"    📈 Trades: {result['total_trades']}, "
                  f"Win Rate: {result['win_rate']:.1%}")
            print()
        
        # Portfolio recommendations
        print("💼 PORTFOLIO RECOMMENDATIONS:")
        print()
        
        # Group by strategy type for diversification
        strategy_groups = {}
        for result in good_results[:15]:  # Top 15
            strategy_type = result['strategy_type']
            if strategy_type not in strategy_groups:
                strategy_groups[strategy_type] = []
            strategy_groups[strategy_type].append(result)
        
        portfolio_value = INITIAL_CAPITAL
        recommended_trades = []
        
        print("Diversified Portfolio (Equal allocation across strategy types):")
        for strategy_type, type_results in strategy_groups.items():
            if type_results:
                top_result = type_results[0]  # Best asset for this strategy type
                allocation = INITIAL_CAPITAL / len(strategy_groups)
                expected_return = top_result['total_return']
                expected_value = allocation * (1 + expected_return)
                
                print(f"• {top_result['asset']} + {top_result['strategy']} ({strategy_type}): "
                      f"${allocation:,.0f} → ${expected_value:,.0f}")
                
                portfolio_value += (expected_value - allocation)
                recommended_trades.append({
                    'asset': top_result['asset'],
                    'strategy': top_result['strategy'],
                    'strategy_type': strategy_type,
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
        print(f"• These are backtested results - past performance doesn't guarantee future results")
        print(f"• Options strategies involve significant risk and may require margin")
        print(f"• Start with small position sizes and scale gradually")
        print(f"• Monitor positions closely and use stop-losses")
        print(f"• Consider paper trading first to validate strategies")
    
    def _save_detailed_results(self, all_results: List[Dict]):
        """Save detailed results to JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_strategy_analysis_{timestamp}.json"
        
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
    """Run the enhanced comprehensive analysis."""
    
    analyzer = EnhancedComprehensiveAnalyzer()
    
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
