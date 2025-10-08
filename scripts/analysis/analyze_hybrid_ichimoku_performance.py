#!/usr/bin/env python3
"""
HybridIchimokuStrategy Performance Analysis
==========================================

Analyzes the performance of different versions of the HybridIchimokuStrategy
to understand the impact of trailing stops and other enhancements.
"""

import json
from typing import Dict, List, Any

def analyze_strategy_performance():
    """Analyze HybridIchimokuStrategy performance across different versions"""
    
    # Results from the backtest API
    results = [
        {
            "name": "HybridIchimokuStrategy_v1",
            "description": "Original version (no trailing stops)",
            "total_return": 0.3459389730594276,  # 34.59%
            "sharpe_ratio": 0.5132718468749113,
            "max_drawdown": 0.06552950082747076,  # 6.55%
            "win_rate": 0.46096278691331577,  # 46.1%
            "total_trades": 90,
            "profit_factor": 1.4881661532334898
        },
        {
            "name": "HybridIchimokuStrategy_v2",
            "description": "With trailing stops (3% + ATR)",
            "total_return": 0.20058298581499123,  # 20.06%
            "sharpe_ratio": -0.14415325743583307,
            "max_drawdown": 0.14941348299489765,  # 14.94%
            "win_rate": 0.5583391914555584,  # 55.8%
            "total_trades": 91,
            "profit_factor": 1.0640326308124661
        },
        {
            "name": "HybridIchimokuStrategy_v3",
            "description": "Latest version (tightened stops)",
            "total_return": -0.1909096784238451,  # -19.09%
            "sharpe_ratio": -0.22902966124717405,
            "max_drawdown": 0.1295011755617278,  # 12.95%
            "win_rate": 0.4727431852378548,  # 47.3%
            "total_trades": 42,
            "profit_factor": 1.428619777884271
        }
    ]
    
    print("🎯 HYBRID ICHIMOKU STRATEGY PERFORMANCE ANALYSIS")
    print("=" * 70)
    print()
    
    # Performance comparison table
    print("📊 PERFORMANCE COMPARISON")
    print("-" * 70)
    print(f"{'Version':<25} {'Return':<10} {'Drawdown':<12} {'Win Rate':<10} {'Trades':<8} {'Sharpe':<8}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['name']:<25} "
              f"{result['total_return']*100:+7.2f}% "
              f"{result['max_drawdown']*100:8.2f}% "
              f"{result['win_rate']*100:7.1f}% "
              f"{result['total_trades']:6d} "
              f"{result['sharpe_ratio']:6.2f}")
    
    print("-" * 70)
    print()
    
    # Analysis of trailing stops impact
    print("🛑 TRAILING STOPS IMPACT ANALYSIS")
    print("-" * 70)
    
    v1 = results[0]  # Original
    v2 = results[1]  # With trailing stops
    
    return_change = (v2['total_return'] - v1['total_return']) / v1['total_return'] * 100
    drawdown_change = (v2['max_drawdown'] - v1['max_drawdown']) / v1['max_drawdown'] * 100
    win_rate_change = (v2['win_rate'] - v1['win_rate']) / v1['win_rate'] * 100
    
    print(f"📈 Return Change: {return_change:+.1f}% ({v1['total_return']*100:.2f}% → {v2['total_return']*100:.2f}%)")
    print(f"📉 Drawdown Change: {drawdown_change:+.1f}% ({v1['max_drawdown']*100:.2f}% → {v2['max_drawdown']*100:.2f}%)")
    print(f"🎯 Win Rate Change: {win_rate_change:+.1f}% ({v1['win_rate']*100:.1f}% → {v2['win_rate']*100:.1f}%)")
    print(f"📊 Trade Count: {v1['total_trades']} → {v2['total_trades']} ({v2['total_trades'] - v1['total_trades']:+d})")
    print()
    
    # Key insights
    print("💡 KEY INSIGHTS")
    print("-" * 70)
    
    if return_change < 0:
        print("❌ Trailing stops REDUCED returns")
        print("   • More conservative exits")
        print("   • May be cutting profits too early")
        print("   • Need to optimize stop parameters")
    else:
        print("✅ Trailing stops IMPROVED returns")
        print("   • Better profit protection")
        print("   • More efficient exits")
    
    if drawdown_change > 0:
        print("⚠️  Trailing stops INCREASED drawdown")
        print("   • Stops may be too tight")
        print("   • Need wider stop distances")
    else:
        print("✅ Trailing stops REDUCED drawdown")
        print("   • Better risk management")
        print("   • Improved capital preservation")
    
    if win_rate_change > 0:
        print("✅ Trailing stops IMPROVED win rate")
        print("   • Better exit timing")
        print("   • More profitable trades")
    else:
        print("❌ Trailing stops REDUCED win rate")
        print("   • May be exiting too early")
        print("   • Need to adjust stop logic")
    
    print()
    
    # Recommendations
    print("🔧 OPTIMIZATION RECOMMENDATIONS")
    print("-" * 70)
    
    print("1. 📊 Stop Distance Optimization:")
    print("   • Current: 3% + ATR(2x)")
    print("   • Try: 5% + ATR(1.5x) for wider stops")
    print("   • Test: 2% + ATR(2.5x) for tighter stops")
    print()
    
    print("2. 🎯 Profit Threshold Adjustment:")
    print("   • Current: 5% minimum profit before trailing")
    print("   • Try: 3% for earlier trailing")
    print("   • Test: 7% for later trailing")
    print()
    
    print("3. 🛑 Maximum Loss Optimization:")
    print("   • Current: 8% maximum loss")
    print("   • Try: 6% for tighter risk control")
    print("   • Test: 10% for more room")
    print()
    
    print("4. 📈 Hybrid Approach:")
    print("   • Use wider stops for high-confidence patterns")
    print("   • Use tighter stops for low-confidence patterns")
    print("   • Adjust based on Elliott Wave pattern type")
    print()
    
    # Best performing version
    best_return = max(results, key=lambda x: x['total_return'])
    best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
    best_drawdown = min(results, key=lambda x: x['max_drawdown'])
    
    print("🏆 BEST PERFORMING VERSIONS")
    print("-" * 70)
    print(f"📈 Highest Return: {best_return['name']} ({best_return['total_return']*100:.2f}%)")
    print(f"📊 Best Sharpe: {best_sharpe['name']} ({best_sharpe['sharpe_ratio']:.2f})")
    print(f"🛡️  Lowest Drawdown: {best_drawdown['name']} ({best_drawdown['max_drawdown']*100:.2f}%)")
    print()
    
    # Conclusion
    print("🎯 CONCLUSION")
    print("-" * 70)
    
    if v2['total_return'] > v1['total_return']:
        print("✅ Trailing stops are BENEFICIAL")
        print("   • Improved returns and risk management")
        print("   • Continue with current implementation")
    else:
        print("⚠️  Trailing stops need OPTIMIZATION")
        print("   • Current parameters may be too aggressive")
        print("   • Recommend testing wider stop distances")
        print("   • Consider pattern-specific stop logic")
    
    print()
    print("🚀 NEXT STEPS:")
    print("   1. Test wider trailing stop parameters")
    print("   2. Implement pattern-specific stop logic")
    print("   3. Add volatility-based stop adjustment")
    print("   4. Monitor live paper trading performance")

if __name__ == "__main__":
    analyze_strategy_performance()





