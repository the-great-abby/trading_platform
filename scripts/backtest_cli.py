#!/usr/bin/env python3
"""
Backtest Results CLI - View and manage backtest results from the database
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# Add src to path - handle both local and container environments
if os.path.exists('src'):
    sys.path.append('src')
elif os.path.exists('/app/src'):
    sys.path.append('/app/src')
else:
    # Try to find src relative to current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(os.path.dirname(current_dir), 'src')
    if os.path.exists(src_path):
        sys.path.append(src_path)

from services.database.backtest_results_service import BacktestResultsService

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.2f}%" if value is not None else "N/A"

def format_currency(value: float) -> str:
    """Format currency values"""
    return f"${value:,.2f}" if value is not None else "N/A"

def format_number(value: float) -> str:
    """Format number values"""
    return f"{value:,.0f}" if value is not None else "N/A"

def display_runs_table(runs: List[Dict], show_details: bool = False):
    """Display backtest runs in a formatted table"""
    if not runs:
        print("No backtest runs found.")
        return
    
    print(f"\n📊 Found {len(runs)} backtest run(s)")
    print("=" * 120)
    
    # Header
    if show_details:
        print(f"{'Run ID':<25} {'Strategy':<20} {'Date Range':<20} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate':<10} {'Max DD %':<10} {'DB Only':<8}")
        print("-" * 120)
    else:
        print(f"{'Run ID':<25} {'Strategy':<20} {'Date Range':<20} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 100)
    
    # Rows
    for run in runs:
        date_range = f"{run['start_date'][:10]} to {run['end_date'][:10]}"
        return_pct = format_percentage(run['total_return_pct'])
        sharpe = f"{run['sharpe_ratio']:.2f}" if run['sharpe_ratio'] is not None else "N/A"
        trades = format_number(run['total_trades'])
        win_rate = format_percentage(run['win_rate'] * 100)
        
        if show_details:
            max_dd = format_percentage(run['max_drawdown_pct'])
            db_only = "Yes" if run['database_only'] else "No"
            print(f"{run['run_id']:<25} {run['strategy_name']:<20} {date_range:<20} {return_pct:<10} {sharpe:<8} {trades:<8} {win_rate:<10} {max_dd:<10} {db_only:<8}")
        else:
            print(f"{run['run_id']:<25} {run['strategy_name']:<20} {date_range:<20} {return_pct:<10} {sharpe:<8} {trades:<8} {win_rate:<10}")

def display_run_details(run: Dict):
    """Display detailed information about a specific backtest run"""
    print(f"\n📊 BACKTEST RUN DETAILS")
    print("=" * 50)
    print(f"Run ID: {run['run_id']}")
    print(f"Strategy: {run['strategy_name']}")
    print(f"Date Range: {run['start_date']} to {run['end_date']}")
    print(f"Symbols: {', '.join(run['symbols'])}")
    print(f"Database Only: {'Yes' if run['database_only'] else 'No'}")
    print(f"Data Provider: {run['data_provider'] or 'N/A'}")
    print(f"Created: {run['created_at']}")
    print(f"Completed: {run['completed_at'] or 'N/A'}")
    
    print(f"\n💰 PERFORMANCE METRICS")
    print("-" * 30)
    print(f"Initial Capital: {format_currency(run['initial_capital'])}")
    print(f"Final Capital: {format_currency(run['final_capital'])}")
    print(f"Total Return: {format_currency(run['total_return'])} ({format_percentage(run['total_return_pct'])})")
    print(f"Max Drawdown: {format_percentage(run['max_drawdown_pct'])}")
    print(f"Sharpe Ratio: {run['sharpe_ratio']:.3f}")
    
    print(f"\n📈 TRADING METRICS")
    print("-" * 30)
    print(f"Total Trades: {format_number(run['total_trades'])}")
    print(f"Winning Trades: {format_number(run['winning_trades'])}")
    print(f"Losing Trades: {format_number(run['losing_trades'])}")
    print(f"Win Rate: {format_percentage(run['win_rate'] * 100)}")
    print(f"Profit Factor: {run['profit_factor']:.2f}")
    print(f"Average Win: {format_currency(run['avg_win'])}")
    print(f"Average Loss: {format_currency(run['avg_loss'])}")

def display_trades_table(trades: List[Dict], limit: int = 20):
    """Display trades in a formatted table"""
    if not trades:
        print("No trades found for this run.")
        return
    
    print(f"\n📊 TRADES (showing first {min(limit, len(trades))} of {len(trades)})")
    print("=" * 100)
    print(f"{'Date':<20} {'Symbol':<8} {'Action':<6} {'Quantity':<10} {'Price':<10} {'Value':<12} {'P&L':<10} {'Confidence':<10}")
    print("-" * 100)
    
    for trade in trades[:limit]:
        date = trade['timestamp'][:19]  # Remove timezone info
        action = trade['action']
        quantity = format_number(trade['quantity'])
        price = format_currency(trade['price'])
        value = format_currency(trade['value'])
        pnl = format_currency(trade['pnl'])
        confidence = f"{trade['confidence']:.2f}"
        
        print(f"{date:<20} {trade['symbol']:<8} {action:<6} {quantity:<10} {price:<10} {value:<12} {pnl:<10} {confidence:<10}")

def display_equity_curve(equity_data: List[Dict], limit: int = 20):
    """Display equity curve data"""
    if not equity_data:
        print("No equity curve data found for this run.")
        return
    
    print(f"\n📈 EQUITY CURVE (showing first {min(limit, len(equity_data))} of {len(equity_data)} points)")
    print("=" * 80)
    print(f"{'Date':<12} {'Portfolio Value':<15} {'Cash':<12} {'Positions':<12} {'Total P&L':<12}")
    print("-" * 80)
    
    for point in equity_data[:limit]:
        date = point['date']
        portfolio_value = format_currency(point['portfolio_value'])
        cash = format_currency(point['cash'])
        positions = format_currency(point['positions_value'])
        total_pnl = format_currency(point['total_pnl'])
        
        print(f"{date:<12} {portfolio_value:<15} {cash:<12} {positions:<12} {total_pnl:<12}")

def list_runs(args):
    """List backtest runs with optional filtering"""
    service = BacktestResultsService()
    
    runs = service.get_backtest_runs(
        strategy_name=args.strategy,
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit
    )
    
    display_runs_table(runs, show_details=args.details)

def show_run(args):
    """Show detailed information about a specific backtest run"""
    service = BacktestResultsService()
    
    # Get run details
    runs = service.get_backtest_runs(limit=1000)  # Get all runs to find the specific one
    target_run = None
    
    for run in runs:
        if run['run_id'] == args.run_id:
            target_run = run
            break
    
    if not target_run:
        print(f"❌ Backtest run '{args.run_id}' not found.")
        return
    
    display_run_details(target_run)
    
    # Show trades if requested
    if args.show_trades:
        trades = service.get_backtest_trades(args.run_id)
        display_trades_table(trades, limit=args.trade_limit)
    
    # Show equity curve if requested
    if args.show_equity:
        equity_data = service.get_equity_curve(args.run_id)
        display_equity_curve(equity_data, limit=args.equity_limit)

def compare_strategies(args):
    """Compare performance of different strategies"""
    service = BacktestResultsService()
    
    # Get recent runs for each strategy
    all_runs = service.get_backtest_runs(limit=1000)
    
    # Group by strategy and get the most recent run for each
    strategy_runs = {}
    for run in all_runs:
        strategy = run['strategy_name']
        if strategy not in strategy_runs or run['created_at'] > strategy_runs[strategy]['created_at']:
            strategy_runs[strategy] = run
    
    if not strategy_runs:
        print("No backtest runs found for comparison.")
        return
    
    print(f"\n📊 STRATEGY COMPARISON (Most Recent Runs)")
    print("=" * 100)
    print(f"{'Strategy':<25} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate':<10} {'Max DD %':<10} {'Profit Factor':<12} {'Date Range':<20}")
    print("-" * 100)
    
    # Sort by return percentage
    sorted_runs = sorted(strategy_runs.values(), key=lambda x: x['total_return_pct'], reverse=True)
    
    for run in sorted_runs:
        date_range = f"{run['start_date'][:10]} to {run['end_date'][:10]}"
        return_pct = format_percentage(run['total_return_pct'])
        sharpe = f"{run['sharpe_ratio']:.2f}" if run['sharpe_ratio'] is not None else "N/A"
        trades = format_number(run['total_trades'])
        win_rate = format_percentage(run['win_rate'] * 100)
        max_dd = format_percentage(run['max_drawdown_pct'])
        profit_factor = f"{run['profit_factor']:.2f}"
        
        print(f"{run['strategy_name']:<25} {return_pct:<10} {sharpe:<8} {trades:<8} {win_rate:<10} {max_dd:<10} {profit_factor:<12} {date_range:<20}")
    
    # Show best and worst performers
    if sorted_runs:
        best = sorted_runs[0]
        worst = sorted_runs[-1]
        
        print(f"\n🏆 BEST PERFORMER: {best['strategy_name']} ({format_percentage(best['total_return_pct'])})")
        print(f"📉 WORST PERFORMER: {worst['strategy_name']} ({format_percentage(worst['total_return_pct'])})")

def delete_run(args):
    """Delete a backtest run and all associated data"""
    service = BacktestResultsService()
    
    if not args.force:
        print(f"⚠️  Are you sure you want to delete backtest run '{args.run_id}'?")
        print("This will permanently delete all associated trades and equity curve data.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return
    
    success = service.delete_backtest_run(args.run_id)
    if success:
        print(f"✅ Successfully deleted backtest run '{args.run_id}'")
    else:
        print(f"❌ Failed to delete backtest run '{args.run_id}'")

def export_results(args):
    """Export backtest results to CSV"""
    service = BacktestResultsService()
    
    # Get runs
    runs = service.get_backtest_runs(
        strategy_name=args.strategy,
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit
    )
    
    if not runs:
        print("No backtest runs found to export.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(runs)
    
    # Flatten symbols list
    df['symbols'] = df['symbols'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    
    # Export to CSV
    filename = args.output or f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Exported {len(runs)} backtest runs to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Backtest Results CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List runs command
    list_parser = subparsers.add_parser('list', help='List backtest runs')
    list_parser.add_argument('--strategy', help='Filter by strategy name')
    list_parser.add_argument('--start-date', help='Filter by start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='Filter by end date (YYYY-MM-DD)')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum number of runs to show')
    list_parser.add_argument('--details', action='store_true', help='Show detailed information')
    list_parser.set_defaults(func=list_runs)
    
    # Show run command
    show_parser = subparsers.add_parser('show', help='Show detailed information about a specific run')
    show_parser.add_argument('run_id', help='Backtest run ID')
    show_parser.add_argument('--show-trades', action='store_true', help='Show trades for this run')
    show_parser.add_argument('--show-equity', action='store_true', help='Show equity curve for this run')
    show_parser.add_argument('--trade-limit', type=int, default=20, help='Maximum number of trades to show')
    show_parser.add_argument('--equity-limit', type=int, default=20, help='Maximum number of equity points to show')
    show_parser.set_defaults(func=show_run)
    
    # Compare strategies command
    compare_parser = subparsers.add_parser('compare', help='Compare performance of different strategies')
    compare_parser.set_defaults(func=compare_strategies)
    
    # Delete run command
    delete_parser = subparsers.add_parser('delete', help='Delete a backtest run')
    delete_parser.add_argument('run_id', help='Backtest run ID')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=delete_run)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export backtest results to CSV')
    export_parser.add_argument('--strategy', help='Filter by strategy name')
    export_parser.add_argument('--start-date', help='Filter by start date (YYYY-MM-DD)')
    export_parser.add_argument('--end-date', help='Filter by end date (YYYY-MM-DD)')
    export_parser.add_argument('--limit', type=int, default=1000, help='Maximum number of runs to export')
    export_parser.add_argument('--output', help='Output filename (default: auto-generated)')
    export_parser.set_defaults(func=export_results)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 