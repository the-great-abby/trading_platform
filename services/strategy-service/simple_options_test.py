#!/usr/bin/env python3
"""
Simple Options Strategy Test
===========================
Tests Iron Condor, Butterfly Spread, and Calendar Spread strategies
on a few key symbols using mock data to avoid market data issues.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add the parent directory of src to the Python path
sys.path.append('/app/src')
sys.path.append('/app')

from src.backtesting.engine.backtest_engine import BacktestEngine

# Focus on a few key symbols for testing
SYMBOLS = ['AAPL', 'MSFT', 'AMD', 'PYPL', 'INTC']

# Your new strategies
STRATEGIES = [
    'IronCondor',
    'ButterflySpread', 
    'CalendarSpread'
]

INITIAL_CAPITAL = 2000.0

async def run_simple_options_test():
    """Run simple test on key symbols with mock data"""
    
    print("🚀 SIMPLE OPTIONS STRATEGY TEST")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: ${INITIAL_CAPITAL}")
    print(f"📈 Testing {len(STRATEGIES)} strategies on {len(SYMBOLS)} symbols")
    print(f"📊 Using Mock Data (avoiding market data issues)")
    print()
    
    # Initialize backtest engine with mock data
    engine = BacktestEngine(use_real_data=False, use_cache=False)
    
    # Calculate date range (2 years back)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    print(f"📊 Date Range: {start_date} to {end_date}")
    print()
    
    all_results = []
    
    for symbol in SYMBOLS:
        print(f"📈 Testing {symbol}...")
        
        for strategy_name in STRATEGIES:
            try:
                print(f"  🔄 Running {strategy_name}...")
                
                # Run backtest for this symbol/strategy combination
                result = await engine.run_backtest(
                    symbols=[symbol],
                    start_date=start_date,
                    end_date=end_date,
                    strategies=[strategy_name]
                )
                
                if result and strategy_name in result:
                    strategy_result = result[strategy_name]
                    if strategy_result:
                        all_results.append({
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'total_return': strategy_result.total_return,
                            'sharpe_ratio': strategy_result.sharpe_ratio,
                            'max_drawdown': strategy_result.max_drawdown_pct,
                            'win_rate': strategy_result.win_rate,
                            'total_trades': strategy_result.total_trades,
                            'profit_factor': strategy_result.profit_factor,
                            'final_value': INITIAL_CAPITAL * (1 + strategy_result.total_return)
                        })
                        
                        print(f"  ✅ {strategy_name}: {strategy_result.total_return:.2%} return, {strategy_result.sharpe_ratio:.2f} Sharpe, {strategy_result.total_trades} trades")
                    else:
                        print(f"  ❌ {strategy_name}: No results")
                else:
                    print(f"  ❌ {strategy_name}: Failed - no result")
                    
            except Exception as e:
                print(f"  ❌ {strategy_name}: Error - {e}")
    
    if not all_results:
        print("❌ No successful backtests completed!")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(all_results)
    
    print(f"\n📊 BACKTEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"✅ Successful Tests: {len(df)}")
    print(f"📈 Total Combinations: {len(STRATEGIES) * len(SYMBOLS)}")
    print(f"🎯 Success Rate: {len(df)/(len(STRATEGIES) * len(SYMBOLS)):.1%}")
    
    # Analyze by strategy
    print(f"\n📈 STRATEGY PERFORMANCE SUMMARY")
    print("-" * 40)
    
    for strategy in STRATEGIES:
        strategy_data = df[df['strategy'] == strategy]
        if not strategy_data.empty:
            avg_return = strategy_data['total_return'].mean()
            avg_sharpe = strategy_data['sharpe_ratio'].mean()
            avg_win_rate = strategy_data['win_rate'].mean()
            avg_trades = strategy_data['total_trades'].mean()
            
            print(f"{strategy:15} | Return: {avg_return:6.1%} | Sharpe: {avg_sharpe:5.2f} | Win Rate: {avg_win_rate:5.1%} | Trades: {avg_trades:4.0f}")
    
    # Find best performing combinations
    print(f"\n🏆 TOP PERFORMING COMBINATIONS")
    print("-" * 50)
    top_performers = df.nlargest(10, 'total_return')
    
    for idx, row in top_performers.iterrows():
        print(f"{row['symbol']:6} + {row['strategy']:15} | "
              f"Return: {row['total_return']:6.1%} | "
              f"Sharpe: {row['sharpe_ratio']:5.2f} | "
              f"Win Rate: {row['win_rate']:5.1%} | "
              f"Final Value: ${row['final_value']:7.0f}")
    
    # Find assets with best performance
    print(f"\n🎯 ASSETS WITH BEST PERFORMANCE")
    print("-" * 50)
    
    symbol_performance = df.groupby('symbol').agg({
        'total_return': ['mean', 'max'],
        'sharpe_ratio': 'mean',
        'win_rate': 'mean',
        'total_trades': 'mean'
    }).round(3)
    
    # Sort by average return
    symbol_scores = []
    for symbol in SYMBOLS:
        symbol_data = df[df['symbol'] == symbol]
        if not symbol_data.empty:
            avg_return = symbol_data['total_return'].mean()
            max_return = symbol_data['total_return'].max()
            avg_sharpe = symbol_data['sharpe_ratio'].mean()
            avg_win_rate = symbol_data['win_rate'].mean()
            avg_trades = symbol_data['total_trades'].mean()
            strategy_count = len(symbol_data)
            
            symbol_scores.append({
                'symbol': symbol,
                'avg_return': avg_return,
                'max_return': max_return,
                'avg_sharpe': avg_sharpe,
                'avg_win_rate': avg_win_rate,
                'avg_trades': avg_trades,
                'strategy_count': strategy_count,
                'best_strategy': symbol_data.loc[symbol_data['total_return'].idxmax(), 'strategy']
            })
    
    # Sort by average return
    symbol_scores.sort(key=lambda x: x['avg_return'], reverse=True)
    
    print("Asset Performance Ranking:")
    for i, score in enumerate(symbol_scores, 1):
        print(f"{i}. {score['symbol']:6} | "
              f"Avg Return: {score['avg_return']:6.1%} | "
              f"Max Return: {score['max_return']:6.1%} | "
              f"Sharpe: {score['avg_sharpe']:5.2f} | "
              f"Win Rate: {score['avg_win_rate']:5.1%} | "
              f"Best Strategy: {score['best_strategy']}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR PAPER TRADING")
    print("-" * 50)
    
    if symbol_scores:
        top_3_assets = [score['symbol'] for score in symbol_scores[:3]]
        print(f"🥇 Top 3 Recommended Assets: {', '.join(top_3_assets)}")
        
        # Find best strategy for each top asset
        for asset in top_3_assets:
            asset_data = df[df['symbol'] == asset]
            if not asset_data.empty:
                best_strategy = asset_data.loc[asset_data['total_return'].idxmax()]
                print(f"   {asset}: Best with {best_strategy['strategy']} ({best_strategy['total_return']:.1%} return)")
        
        print(f"\n🎯 Suggested Paper Trading Configuration:")
        print(f"   Assets: {', '.join(top_3_assets[:3])}")
        print(f"   Strategies: {', '.join(STRATEGIES)}")
        print(f"   Expected Performance: {symbol_scores[0]['avg_return']:.1%} - {symbol_scores[2]['avg_return']:.1%} returns")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_simple_options_test())