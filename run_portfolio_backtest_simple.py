#!/usr/bin/env python3
"""
Portfolio Strategy Backtest - Tests multi-strategy combinations with risk management
"""

import asyncio
import sys
import os
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from backtesting.backtest_engine import BacktestEngine


async def run_portfolio_backtest():
    """Run comprehensive portfolio strategy backtest"""
    
    print("🚀 PORTFOLIO STRATEGY BACKTEST WITH RISK MANAGEMENT")
    print("=" * 70)
    
    # Configuration
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'GS', 'PFE', 'MRK', 'UNH', 'SPY', 'VTI']
    start_date = "2023-07-06"
    end_date = "2025-07-03"
    initial_capital = 100000.0
    
    print(f"📊 Test Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} stocks")
    print(f"   🗄️  Data Source: Real Market Data from Database")
    print()
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Test different strategy combinations
    strategy_combinations = [
        {
            'name': 'Conservative_Combo',
            'description': 'Bollinger Bands + RSI (Best performers)',
            'strategies': ['BollingerBandsStrategy', 'RSIStrategy']
        },
        {
            'name': 'Balanced_Combo',
            'description': 'Bollinger Bands + RSI + Mean Reversion',
            'strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MeanReversionStrategy']
        },
        {
            'name': 'Momentum_Combo',
            'description': 'Bollinger Bands + RSI + Momentum',
            'strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MomentumStrategy']
        },
        {
            'name': 'Risk_Averse_Combo',
            'description': 'Only Bollinger Bands (Most conservative)',
            'strategies': ['BollingerBandsStrategy']
        }
    ]
    
    results = []
    
    print("🏃 RUNNING STRATEGY COMBINATION BACKTESTS")
    print("-" * 50)
    
    for combo in strategy_combinations:
        print(f"\n📊 Testing: {combo['name']}")
        print(f"   📝 {combo['description']}")
        print(f"   🎯 Strategies: {', '.join(combo['strategies'])}")
        
        try:
            # Run backtest for each strategy in the combination
            combo_results = []
            for strategy_name in combo['strategies']:
                result = await engine._run_strategy_backtest(strategy_name, 
                                                           await engine._get_market_data(symbols, start_date, end_date))
                if result:
                    combo_results.append(result)
            
            if combo_results:
                # Calculate combined metrics
                total_return = sum(r.total_return_pct for r in combo_results) / len(combo_results)
                total_trades = sum(r.total_trades for r in combo_results)
                avg_win_rate = sum(r.win_rate for r in combo_results) / len(combo_results)
                avg_sharpe = sum(r.sharpe_ratio for r in combo_results) / len(combo_results)
                avg_max_dd = sum(r.max_drawdown_pct for r in combo_results) / len(combo_results)
                
                results.append({
                    'name': combo['name'],
                    'description': combo['description'],
                    'strategies': combo['strategies'],
                    'total_return': total_return,
                    'total_trades': total_trades,
                    'win_rate': avg_win_rate,
                    'sharpe_ratio': avg_sharpe,
                    'max_drawdown': avg_max_dd,
                    'individual_results': combo_results
                })
                
                print(f"   ✅ Avg Return: {total_return:.2f}%")
                print(f"   📊 Avg Sharpe: {avg_sharpe:.2f}")
                print(f"   🔄 Total Trades: {total_trades}")
                print(f"   🎯 Avg Win Rate: {avg_win_rate*100:.1f}%")
                print(f"   📉 Avg Max DD: {avg_max_dd:.2f}%")
            else:
                print(f"   ❌ No successful results")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue
    
    # Display results summary
    print("\n" + "=" * 70)
    print("📊 STRATEGY COMBINATION RESULTS SUMMARY")
    print("=" * 70)
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"{'Combination':<25} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate %':<12} {'Max DD %':<10}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['name']:<25} {result['total_return']:>8.2f}% {result['sharpe_ratio']:>6.2f} "
                  f"{result['total_trades']:>6} {result['win_rate']*100:>10.1f}% {result['max_drawdown']:>8.2f}%")
        
        # Best performing combination
        best = results[0]
        print(f"\n🏆 BEST PERFORMING COMBINATION: {best['name']}")
        print(f"   📈 Average Return: {best['total_return']:.2f}%")
        print(f"   📊 Average Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        print(f"   🔄 Total Trades: {best['total_trades']}")
        print(f"   ✅ Average Win Rate: {best['win_rate']*100:.1f}%")
        print(f"   📉 Average Max Drawdown: {best['max_drawdown']:.2f}%")
        print(f"   🎯 Strategies: {', '.join(best['strategies'])}")
        
        # Individual strategy performance in best combination
        print(f"\n📊 INDIVIDUAL STRATEGY PERFORMANCE IN BEST COMBINATION:")
        for result in best['individual_results']:
            print(f"   {result.strategy}: {result.total_return_pct:.2f}% return, {result.win_rate*100:.1f}% win rate")
        
        # Risk management recommendations
        print(f"\n🔒 RISK MANAGEMENT RECOMMENDATIONS:")
        print(f"   🎯 Use {best['name']} as primary strategy combination")
        print(f"   📏 Position Size: 5-10% of portfolio per trade")
        print(f"   🛑 Stop Loss: 3-5% per position")
        print(f"   🎯 Take Profit: 10-15% per position")
        print(f"   📊 Diversify across multiple symbols")
        print(f"   ⏰ Monitor and rebalance monthly")
        
    else:
        print("❌ No successful backtest results")
    
    print(f"\n✅ Strategy combination backtest completed!")
    print(f"📈 Total combinations tested: {len(strategy_combinations)}")
    print(f"🎯 Successful backtests: {len(results)}")


if __name__ == "__main__":
    asyncio.run(run_portfolio_backtest()) 