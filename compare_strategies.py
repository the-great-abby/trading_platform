#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/src')
from src.backtesting.engine.backtest_engine import BacktestEngine
import asyncio
import pandas as pd

async def compare_strategies():
    print('🚀 Running Comprehensive Strategy Comparison...')
    print('=' * 80)
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    
    # Available strategies (using the correct names from the mapping)
    strategies = [
        'SMACrossover',
        'Momentum', 
        'RSI',
        'MACD',
        'Ichimoku',
        'RegimeSwitching',
        'BollingerBands',
        'MeanReversion',
        'VolatilityBreakout'
    ]
    
    results = []
    
    for strategy in strategies:
        try:
            print(f'\n📊 Testing {strategy}...')
            
            # Run backtest
            backtest_results = await engine.run_backtest(
                symbols=symbols,
                start_date='2023-09-19',
                end_date='2024-09-19',
                strategies=[strategy]
            )
            
            if backtest_results and strategy in backtest_results:
                result = backtest_results[strategy]
                
                # Calculate average performance across symbols
                total_return = result.total_return_pct
                sharpe_ratio = result.sharpe_ratio
                max_drawdown = result.max_drawdown_pct
                win_rate = result.win_rate
                total_trades = result.total_trades
                
                results.append({
                    'Strategy': strategy,
                    'Total Return %': round(total_return, 2),
                    'Sharpe Ratio': round(sharpe_ratio, 2),
                    'Max Drawdown %': round(max_drawdown, 2),
                    'Win Rate %': round(win_rate * 100, 1),
                    'Total Trades': total_trades,
                    'Final Capital': round(result.final_capital, 2)
                })
                
                print(f'   ✅ Total Return: {total_return:.2f}%')
                print(f'   ✅ Sharpe Ratio: {sharpe_ratio:.2f}')
                print(f'   ✅ Max Drawdown: {max_drawdown:.2f}%')
                print(f'   ✅ Win Rate: {win_rate*100:.1f}%')
                print(f'   ✅ Total Trades: {total_trades}')
                
            else:
                print(f'   ❌ No results for {strategy}')
                results.append({
                    'Strategy': strategy,
                    'Total Return %': 'N/A',
                    'Sharpe Ratio': 'N/A',
                    'Max Drawdown %': 'N/A',
                    'Win Rate %': 'N/A',
                    'Total Trades': 'N/A',
                    'Final Capital': 'N/A'
                })
                
        except Exception as e:
            print(f'   ❌ Error with {strategy}: {e}')
            results.append({
                'Strategy': strategy,
                'Total Return %': 'ERROR',
                'Sharpe Ratio': 'ERROR',
                'Max Drawdown %': 'ERROR',
                'Win Rate %': 'ERROR',
                'Total Trades': 'ERROR',
                'Final Capital': 'ERROR'
            })
    
    # Create results DataFrame and display
    if results:
        df = pd.DataFrame(results)
        
        print('\n' + '=' * 80)
        print('📈 STRATEGY COMPARISON RESULTS')
        print('=' * 80)
        print(df.to_string(index=False))
        
        # Find best performers
        print('\n🏆 TOP PERFORMERS:')
        print('-' * 40)
        
        # Sort by total return (excluding errors and N/A)
        valid_results = df[df['Total Return %'].apply(lambda x: isinstance(x, (int, float)))]
        if not valid_results.empty:
            best_return = valid_results.loc[valid_results['Total Return %'].idxmax()]
            print(f'🥇 Best Total Return: {best_return["Strategy"]} ({best_return["Total Return %"]}%)')
            
            # Sort by Sharpe ratio
            valid_sharpe = valid_results[valid_results['Sharpe Ratio'].apply(lambda x: isinstance(x, (int, float)))]
            if not valid_sharpe.empty:
                best_sharpe = valid_sharpe.loc[valid_sharpe['Sharpe Ratio'].idxmax()]
                print(f'🥇 Best Sharpe Ratio: {best_sharpe["Strategy"]} ({best_sharpe["Sharpe Ratio"]})')
            
            # Sort by win rate
            valid_winrate = valid_results[valid_results['Win Rate %'].apply(lambda x: isinstance(x, (int, float)))]
            if not valid_winrate.empty:
                best_winrate = valid_winrate.loc[valid_winrate['Win Rate %'].idxmax()]
                print(f'🥇 Best Win Rate: {best_winrate["Strategy"]} ({best_winrate["Win Rate %"]}%)')
    
    print('\n' + '=' * 80)
    print('✅ Strategy comparison complete!')

if __name__ == "__main__":
    asyncio.run(compare_strategies())


