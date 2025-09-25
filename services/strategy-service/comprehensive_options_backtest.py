#!/usr/bin/env python3
"""
Comprehensive Options Strategy Backtest
======================================
Tests Iron Condor, Butterfly Spread, and Calendar Spread strategies
across multiple assets over 2 years to find the best candidates.
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
from src.services.market_data.cached_market_data_manager import CachedMarketDataManager
from src.services.market_data.market_data_provider import get_market_data_manager

# Expanded list of assets to test for predictable patterns
SYMBOLS = [
    # Tech Stocks (High volatility, good for options)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'PYPL',
    
    # Financial Stocks (Stable, predictable patterns)
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'V', 'MA',
    
    # Healthcare/Biotech (Event-driven, good for earnings strategies)
    'JNJ', 'PFE', 'ABBV', 'MRK', 'UNH', 'CVS', 'LLY',
    
    # Consumer/Retail (Seasonal patterns)
    'WMT', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'SBUX', 'NKE',
    
    # Energy (Commodity-driven patterns)
    'XOM', 'CVX', 'COP', 'EOG', 'SLB',
    
    # Industrial (Economic cycle patterns)
    'CAT', 'BA', 'GE', 'MMM', 'HON', 'UPS', 'FDX'
]

# Your new strategies
STRATEGIES = [
    'IronCondor',
    'ButterflySpread', 
    'CalendarSpread'
]

INITIAL_CAPITAL = 2000.0

async def run_comprehensive_options_backtest():
    """Run comprehensive backtest across all strategies and symbols"""
    
    print("🚀 COMPREHENSIVE OPTIONS STRATEGY BACKTEST")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: ${INITIAL_CAPITAL}")
    print(f"📈 Testing {len(STRATEGIES)} strategies on {len(SYMBOLS)} symbols")
    print(f"⏰ Time Period: 2 years (2023-2025)")
    print()
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Calculate date range (2 years back)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    print(f"📊 Date Range: {start_date} to {end_date}")
    print()
    
    all_results = []
    total_tests = len(STRATEGIES) * len(SYMBOLS)
    completed_tests = 0
    
    # Progress tracking
    print(f"🔄 Progress: 0/{total_tests} tests completed")
    
    for symbol in SYMBOLS:
        print(f"\n📈 Testing {symbol}...")
        
        for strategy_name in STRATEGIES:
            try:
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
                            'max_drawdown': strategy_result.max_drawdown_pct,  # Fixed attribute name
                            'win_rate': strategy_result.win_rate,
                            'total_trades': strategy_result.total_trades,
                            'profit_factor': strategy_result.profit_factor,
                            'final_value': INITIAL_CAPITAL * (1 + strategy_result.total_return)
                        })
                        
                        print(f"  ✅ {strategy_name}: {strategy_result.total_return:.2%} return, {strategy_result.sharpe_ratio:.2f} Sharpe")
                    else:
                        print(f"  ❌ {strategy_name}: No results")
                else:
                    print(f"  ❌ {strategy_name}: Failed")
                    
            except Exception as e:
                print(f"  ❌ {strategy_name}: Error - {e}")
            
            completed_tests += 1
            if completed_tests % 10 == 0:
                print(f"🔄 Progress: {completed_tests}/{total_tests} tests completed")
    
    print(f"✅ Completed all {total_tests} tests")
    
    if not all_results:
        print("❌ No successful backtests completed!")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(all_results)
    
    print(f"\n📊 BACKTEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"✅ Successful Tests: {len(df)}")
    print(f"📈 Total Combinations: {total_tests}")
    print(f"🎯 Success Rate: {len(df)/total_tests:.1%}")
    
    # Analyze by strategy
    print(f"\n📈 STRATEGY PERFORMANCE SUMMARY")
    print("-" * 50)
    strategy_summary = df.groupby('strategy').agg({
        'total_return': ['mean', 'median', 'std'],
        'sharpe_ratio': ['mean', 'median'],
        'win_rate': ['mean', 'median'],
        'total_trades': ['mean', 'median'],
        'max_drawdown': ['mean', 'median']
    }).round(3)
    
    for strategy in STRATEGIES:
        if strategy in strategy_summary.index:
            strategy_data = df[df['strategy'] == strategy]
            avg_return = strategy_data['total_return'].mean()
            avg_sharpe = strategy_data['sharpe_ratio'].mean()
            avg_win_rate = strategy_data['win_rate'].mean()
            avg_trades = strategy_data['total_trades'].mean()
            
            print(f"{strategy:15} | Return: {avg_return:6.1%} | Sharpe: {avg_sharpe:5.2f} | Win Rate: {avg_win_rate:5.1%} | Trades: {avg_trades:4.0f}")
    
    # Find best performing combinations
    print(f"\n🏆 TOP 10 PERFORMING COMBINATIONS")
    print("-" * 70)
    top_performers = df.nlargest(10, 'total_return')
    
    for idx, row in top_performers.iterrows():
        print(f"{row['symbol']:6} + {row['strategy']:15} | "
              f"Return: {row['total_return']:6.1%} | "
              f"Sharpe: {row['sharpe_ratio']:5.2f} | "
              f"Win Rate: {row['win_rate']:5.1%} | "
              f"Final Value: ${row['final_value']:7.0f}")
    
    # Find assets with most predictable patterns
    print(f"\n🎯 ASSETS WITH MOST PREDICTABLE PATTERNS")
    print("-" * 70)
    
    # Group by symbol and analyze consistency
    symbol_analysis = df.groupby('symbol').agg({
        'total_return': ['mean', 'std', 'count'],
        'sharpe_ratio': ['mean', 'std'],
        'win_rate': ['mean', 'std']
    }).round(3)
    
    # Calculate predictability score (higher return, lower std, more strategies worked)
    symbol_scores = []
    for symbol in SYMBOLS:
        symbol_data = df[df['symbol'] == symbol]
        if len(symbol_data) >= 2:  # At least 2 strategies worked
            avg_return = symbol_data['total_return'].mean()
            std_return = symbol_data['total_return'].std()
            avg_sharpe = symbol_data['sharpe_ratio'].mean()
            strategy_count = len(symbol_data)
            
            # Predictability score: high return, low volatility, multiple working strategies
            predictability_score = (avg_return * 100) - (std_return * 50) + (strategy_count * 0.1) + (avg_sharpe * 0.1)
            
            symbol_scores.append({
                'symbol': symbol,
                'avg_return': avg_return,
                'std_return': std_return,
                'avg_sharpe': avg_sharpe,
                'strategy_count': strategy_count,
                'predictability_score': predictability_score,
                'best_strategy': symbol_data.loc[symbol_data['total_return'].idxmax(), 'strategy'],
                'best_return': symbol_data['total_return'].max()
            })
    
    # Sort by predictability score
    symbol_scores.sort(key=lambda x: x['predictability_score'], reverse=True)
    
    print("Top Predictable Assets:")
    for i, score in enumerate(symbol_scores[:15], 1):
        print(f"{i:2}. {score['symbol']:6} | "
              f"Score: {score['predictability_score']:6.2f} | "
              f"Avg Return: {score['avg_return']:6.1%} | "
              f"Volatility: {score['std_return']:6.1%} | "
              f"Strategies: {score['strategy_count']}/3 | "
              f"Best: {score['best_strategy']} ({score['best_return']:5.1%})")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR PAPER TRADING")
    print("-" * 70)
    
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
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_options_backtest())
