#!/usr/bin/env python3
"""
Strategy Comparison Tool with Progress Meter
Runs comprehensive backtests on all available strategies to find the best performers
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.append('/app/src')

from src.backtesting.engine.backtest_engine import BacktestEngine

class ProgressMeter:
    """Simple progress meter for tracking backtest progress"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = 0
        
    def update(self, increment: int = 1, status: str = ""):
        """Update progress"""
        self.current += increment
        current_time = time.time()
        
        # Only update display every 0.5 seconds to avoid spam
        if current_time - self.last_update > 0.5 or self.current >= self.total:
            self.last_update = current_time
            self.display(status)
    
    def display(self, status: str = ""):
        """Display current progress"""
        elapsed = time.time() - self.start_time
        percent = (self.current / self.total) * 100
        
        # Calculate ETA
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {eta:.0f}s"
        else:
            eta_str = "ETA: calculating..."
        
        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r{self.description}: [{bar}] {self.current}/{self.total} ({percent:.1f}%) {eta_str} {status}", end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

async def compare_strategies():
    """Run comprehensive strategy comparison with progress tracking"""
    
    print("🚀 STRATEGY COMPARISON TOOL")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💾 Using database-only mode: {os.getenv('DATABASE_ONLY', 'false')}")
    print("=" * 60)
    
    # Initialize backtest engine
    print("\n🔧 Initializing backtest engine...")
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    print("✅ Engine initialized")
    
    # Test configuration
    symbols = ['AMD', 'INTC', 'PYPL']
    start_date = '2023-09-19'
    end_date = '2024-09-19'
    
    # Available strategies (using correct names from mapping)
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
    
    print(f"\n📊 Testing {len(strategies)} strategies on {len(symbols)} symbols")
    print(f"📈 Date range: {start_date} to {end_date}")
    print(f"💰 Symbols: {', '.join(symbols)}")
    
    # Initialize progress meter
    total_tests = len(strategies)
    progress = ProgressMeter(total_tests, "Running backtests")
    
    results = []
    successful_tests = 0
    
    # Run backtests with progress tracking
    for i, strategy in enumerate(strategies):
        try:
            progress.update(status=f"Testing {strategy}")
            
            # Run backtest
            backtest_results = await engine.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                strategies=[strategy]
            )
            
            if backtest_results and strategy in backtest_results:
                result = backtest_results[strategy]
                successful_tests += 1
                
                # Store results
                results.append({
                    'Strategy': strategy,
                    'Total Return %': round(result.total_return_pct, 2),
                    'Sharpe Ratio': round(result.sharpe_ratio, 2),
                    'Max Drawdown %': round(result.max_drawdown_pct, 2),
                    'Win Rate %': round(result.win_rate * 100, 1),
                    'Total Trades': result.total_trades,
                    'Final Capital': round(result.final_capital, 2),
                    'Initial Capital': round(result.initial_capital, 2)
                })
                
                progress.update(status=f"✅ {strategy} completed")
                
            else:
                results.append({
                    'Strategy': strategy,
                    'Total Return %': 'N/A',
                    'Sharpe Ratio': 'N/A',
                    'Max Drawdown %': 'N/A',
                    'Win Rate %': 'N/A',
                    'Total Trades': 'N/A',
                    'Final Capital': 'N/A',
                    'Initial Capital': 'N/A'
                })
                progress.update(status=f"❌ {strategy} failed")
                
        except Exception as e:
            results.append({
                'Strategy': strategy,
                'Total Return %': 'ERROR',
                'Sharpe Ratio': 'ERROR',
                'Max Drawdown %': 'ERROR',
                'Win Rate %': 'ERROR',
                'Total Trades': 'ERROR',
                'Final Capital': 'ERROR',
                'Initial Capital': 'ERROR'
            })
            progress.update(status=f"❌ {strategy} error: {str(e)[:20]}...")
    
    # Display results
    print("\n" + "=" * 80)
    print("📈 STRATEGY COMPARISON RESULTS")
    print("=" * 80)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"⏱️  Total time: {time.time() - progress.start_time:.1f} seconds")
    
    if results:
        # Create formatted table
        print("\n" + "-" * 100)
        print(f"{'Strategy':<20} {'Return %':<10} {'Sharpe':<8} {'Drawdown %':<12} {'Win Rate %':<12} {'Trades':<8} {'Final $':<10}")
        print("-" * 100)
        
        for result in results:
            strategy = result['Strategy']
            return_pct = result['Total Return %']
            sharpe = result['Sharpe Ratio']
            drawdown = result['Max Drawdown %']
            win_rate = result['Win Rate %']
            trades = result['Total Trades']
            final_cap = result['Final Capital']
            
            print(f"{strategy:<20} {str(return_pct):<10} {str(sharpe):<8} {str(drawdown):<12} {str(win_rate):<12} {str(trades):<8} {str(final_cap):<10}")
        
        # Find best performers
        print("\n" + "🏆 TOP PERFORMERS")
        print("-" * 40)
        
        # Filter valid results (exclude errors and N/A)
        valid_results = [r for r in results if isinstance(r['Total Return %'], (int, float))]
        
        if valid_results:
            # Best total return
            best_return = max(valid_results, key=lambda x: x['Total Return %'])
            print(f"🥇 Best Total Return: {best_return['Strategy']} ({best_return['Total Return %']}%)")
            
            # Best Sharpe ratio
            best_sharpe = max(valid_results, key=lambda x: x['Sharpe Ratio'])
            print(f"🥇 Best Sharpe Ratio: {best_sharpe['Strategy']} ({best_sharpe['Sharpe Ratio']})")
            
            # Best win rate
            best_winrate = max(valid_results, key=lambda x: x['Win Rate %'])
            print(f"🥇 Best Win Rate: {best_winrate['Strategy']} ({best_winrate['Win Rate %']}%)")
            
            # Lowest drawdown
            best_drawdown = min(valid_results, key=lambda x: x['Max Drawdown %'])
            print(f"🥇 Lowest Drawdown: {best_drawdown['Strategy']} ({best_drawdown['Max Drawdown %']}%)")
            
            print(f"\n💡 RECOMMENDATION:")
            print(f"   For the past 2 years, the best performing strategy was:")
            print(f"   🎯 {best_return['Strategy']} with {best_return['Total Return %']}% return")
            
        else:
            print("❌ No valid results to analyze")
    
    print("\n" + "=" * 80)
    print(f"✅ Strategy comparison complete! ({time.time() - progress.start_time:.1f}s)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(compare_strategies())


