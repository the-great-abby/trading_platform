#!/usr/bin/env python3
"""
Backtest Results Viewer - Interactive analysis of backtest results
"""

import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse


def view_results(results_dir: str = "backtest_results"):
    """View backtest results interactively"""
    
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_dir}")
        print("Run 'make run-backtest' first to generate results")
        return
    
    print("📊 Backtest Results Viewer")
    print("=" * 50)
    
    # Find latest results
    csv_dir = results_path / "csv"
    markdown_dir = results_path / "markdown"
    
    if not csv_dir.exists():
        print("❌ No CSV results found")
        return
    
    # List available files
    csv_files = list(csv_dir.glob("*.csv"))
    markdown_files = list(markdown_dir.glob("*.md"))
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files and {len(markdown_files)} markdown files")
    print()
    
    # Show summary if available
    summary_files = [f for f in csv_files if "summary" in f.name]
    if summary_files:
        latest_summary = max(summary_files, key=lambda x: x.stat().st_mtime)
        print("📈 Latest Summary Results:")
        print("-" * 30)
        
        try:
            df = pd.read_csv(latest_summary)
            print(df.to_string(index=False))
            print()
        except Exception as e:
            print(f"Error reading summary: {e}")
    
    # Show comparison if available
    comparison_files = [f for f in csv_files if "comparison" in f.name]
    if comparison_files:
        latest_comparison = max(comparison_files, key=lambda x: x.stat().st_mtime)
        print("🔄 Strategy Comparison:")
        print("-" * 30)
        
        try:
            df = pd.read_csv(latest_comparison)
            # Show key metrics
            key_metrics = ['Strategy', 'Total Return %', 'Max Drawdown %', 'Sharpe Ratio', 'Total Trades', 'Win Rate %']
            available_metrics = [col for col in key_metrics if col in df.columns]
            
            if available_metrics:
                display_df = df[available_metrics]
                print(display_df.to_string(index=False))
                print()
        except Exception as e:
            print(f"Error reading comparison: {e}")
    
    # Show individual strategy results
    strategy_files = [f for f in csv_files if any(strategy in f.name for strategy in ['sma_crossover', 'rsi', 'macd', 'bollinger_bands'])]
    
    if strategy_files:
        print("📊 Individual Strategy Results:")
        print("-" * 30)
        
        for strategy_file in strategy_files:
            strategy_name = strategy_file.stem.split('_')[0]
            print(f"\n🎯 {strategy_name.upper()} Strategy:")
            
            try:
                df = pd.read_csv(strategy_file)
                if 'performance' in strategy_file.name:
                    # Performance summary
                    if 'Metric' in df.columns and 'Value' in df.columns:
                        for _, row in df.iterrows():
                            print(f"   {row['Metric']}: {row['Value']}")
                else:
                    # Trade details (show first few)
                    print(f"   Total trades: {len(df)}")
                    if len(df) > 0:
                        print(f"   First trade: {df.iloc[0]['Date'] if 'Date' in df.columns else 'N/A'}")
                        print(f"   Last trade: {df.iloc[-1]['Date'] if 'Date' in df.columns else 'N/A'}")
            except Exception as e:
                print(f"   Error reading {strategy_name}: {e}")
    
    # Show available files
    print("\n📋 Available Files:")
    print("-" * 30)
    
    print("CSV Files:")
    for file in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True):
        size = file.stat().st_size
        mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"   📄 {file.name} ({size:,} bytes, {mod_time})")
    
    print("\nMarkdown Files:")
    for file in sorted(markdown_files, key=lambda x: x.stat().st_mtime, reverse=True):
        size = file.stat().st_size
        mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"   📝 {file.name} ({size:,} bytes, {mod_time})")
    
    print("\n💡 Tips:")
    print("   - Open CSV files in Excel/Google Sheets for detailed analysis")
    print("   - View markdown files in any markdown viewer")
    print("   - Use 'make run-backtest' to generate new results")
    print("   - Check the 'backtest_results' directory for all files")


def analyze_strategy(strategy_name: str, results_dir: str = "backtest_results"):
    """Analyze a specific strategy in detail"""
    
    results_path = Path(results_dir)
    csv_dir = results_path / "csv"
    
    if not csv_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    # Find strategy files
    strategy_files = [f for f in csv_dir.glob(f"{strategy_name}_*.csv")]
    
    if not strategy_files:
        print(f"❌ No results found for strategy: {strategy_name}")
        return
    
    print(f"🔍 Detailed Analysis: {strategy_name.upper()}")
    print("=" * 50)
    
    for file in strategy_files:
        print(f"\n📄 File: {file.name}")
        print("-" * 30)
        
        try:
            df = pd.read_csv(file)
            
            if 'performance' in file.name:
                print("Performance Metrics:")
                for _, row in df.iterrows():
                    print(f"   {row['Metric']}: {row['Value']}")
            
            elif 'trades' in file.name:
                print(f"Trade Details (showing first 10 of {len(df)} trades):")
                if len(df) > 0:
                    # Show key columns
                    key_cols = ['Date', 'Symbol', 'Action', 'Price', 'Quantity', 'Value', 'Trade P&L']
                    available_cols = [col for col in key_cols if col in df.columns]
                    
                    if available_cols:
                        display_df = df[available_cols].head(10)
                        print(display_df.to_string(index=False))
                    
                    # Summary stats
                    if 'Trade P&L' in df.columns:
                        total_pnl = df['Trade P&L'].sum()
                        avg_pnl = df['Trade P&L'].mean()
                        winning_trades = len(df[df['Trade P&L'] > 0])
                        losing_trades = len(df[df['Trade P&L'] < 0])
                        
                        print(f"\nTrade Summary:")
                        print(f"   Total P&L: ${total_pnl:,.2f}")
                        print(f"   Average P&L: ${avg_pnl:,.2f}")
                        print(f"   Winning trades: {winning_trades}")
                        print(f"   Losing trades: {losing_trades}")
                        print(f"   Win rate: {winning_trades/len(df)*100:.1f}%")
            
            elif 'equity_curve' in file.name:
                print("Equity Curve Data:")
                print(f"   Total data points: {len(df)}")
                if len(df) > 0:
                    print(f"   Date range: {df.iloc[0]['Date']} to {df.iloc[-1]['Date']}")
                    if 'Portfolio Value' in df.columns:
                        initial_value = df.iloc[0]['Portfolio Value']
                        final_value = df.iloc[-1]['Portfolio Value']
                        total_return = ((final_value - initial_value) / initial_value) * 100
                        print(f"   Initial value: ${initial_value:,.2f}")
                        print(f"   Final value: ${final_value:,.2f}")
                        print(f"   Total return: {total_return:.2f}%")
        
        except Exception as e:
            print(f"Error reading file: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="View backtest results")
    parser.add_argument("--results-dir", default="backtest_results", help="Results directory")
    parser.add_argument("--strategy", help="Analyze specific strategy")
    
    args = parser.parse_args()
    
    if args.strategy:
        analyze_strategy(args.strategy, args.results_dir)
    else:
        view_results(args.results_dir)


if __name__ == "__main__":
    main() 