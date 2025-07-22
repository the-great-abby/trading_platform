#!/usr/bin/env python3
"""
Example: Generate HTML Report from Sample Data
Demonstrates how to create MetaTrader-style HTML reports
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtesting.results.html_report_generator import HTMLReportGenerator
from backtesting.engine.backtest_engine import BacktestResult, BacktestTrade


def create_sample_data():
    """Create sample backtest data for demonstration"""
    
    # Create sample equity curve
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    portfolio_values = []
    current_value = 10000  # Starting capital
    
    for i, date in enumerate(dates):
        # Simulate some volatility
        daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
        current_value *= (1 + daily_return)
        portfolio_values.append(current_value)
    
    equity_curve = pd.DataFrame({
        'portfolio_value': portfolio_values
    }, index=dates)
    
    # Create sample trades
    trades = []
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    for i in range(50):  # 50 sample trades
        trade_date = dates[np.random.randint(0, len(dates))]
        symbol = np.random.choice(symbols)
        action = np.random.choice(['BUY', 'SELL'])
        quantity = np.random.randint(10, 100)
        price = np.random.uniform(100, 500)
        pnl = np.random.normal(50, 200)  # Random P&L
        
        trade = BacktestTrade(
            timestamp=trade_date,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            pnl=pnl,
            confidence=np.random.uniform(0.5, 0.9),
            portfolio_value=portfolio_values[np.random.randint(0, len(portfolio_values))],
            cash=np.random.uniform(1000, 5000),
            position_value=quantity * price,
            total_pnl=np.random.uniform(-1000, 2000),
            trade_pnl=pnl,
            strategy='Sample Strategy'
        )
        trades.append(trade)
    
    # Create BacktestResult
    final_value = portfolio_values[-1]
    total_return = final_value - 10000
    total_return_pct = (total_return / 10000) * 100
    
    result = BacktestResult(
        strategy='Sample Momentum Strategy',
        initial_capital=10000,
        final_capital=final_value,
        total_return=total_return,
        total_return_pct=total_return_pct,
        max_drawdown_pct=15.5,  # Sample drawdown
        sharpe_ratio=1.25,  # Sample Sharpe ratio
        total_trades=50,
        winning_trades=32,
        losing_trades=18,
        win_rate=0.64,  # 64% win rate
        profit_factor=1.85,
        avg_win=125.50,
        avg_loss=-85.30,
        trades=trades,
        equity_curve=equity_curve,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    return result


def create_multiple_strategies():
    """Create multiple sample strategies for comparison"""
    
    strategies = {
        'Momentum Strategy': {
            'return_pct': 25.5,
            'drawdown': 12.3,
            'sharpe': 1.45,
            'trades': 45,
            'win_rate': 0.68
        },
        'Mean Reversion Strategy': {
            'return_pct': 18.2,
            'drawdown': 8.7,
            'sharpe': 1.12,
            'trades': 38,
            'win_rate': 0.72
        },
        'Breakout Strategy': {
            'return_pct': 32.1,
            'drawdown': 18.9,
            'sharpe': 1.78,
            'trades': 52,
            'win_rate': 0.61
        }
    }
    
    results = {}
    
    for strategy_name, params in strategies.items():
        # Create sample equity curve for each strategy
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        portfolio_values = []
        current_value = 10000
        
        for i, date in enumerate(dates):
            # Simulate different volatility for each strategy
            volatility = 0.015 if 'Momentum' in strategy_name else 0.012
            daily_return = np.random.normal(0.001, volatility)
            current_value *= (1 + daily_return)
            portfolio_values.append(current_value)
        
        equity_curve = pd.DataFrame({
            'portfolio_value': portfolio_values
        }, index=dates)
        
        # Create sample trades
        trades = []
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        for i in range(params['trades']):
            trade_date = dates[np.random.randint(0, len(dates))]
            symbol = np.random.choice(symbols)
            action = np.random.choice(['BUY', 'SELL'])
            quantity = np.random.randint(10, 100)
            price = np.random.uniform(100, 500)
            pnl = np.random.normal(50, 200)
            
            trade = BacktestTrade(
                timestamp=trade_date,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                pnl=pnl,
                confidence=np.random.uniform(0.5, 0.9),
                portfolio_value=portfolio_values[np.random.randint(0, len(portfolio_values))],
                cash=np.random.uniform(1000, 5000),
                position_value=quantity * price,
                total_pnl=np.random.uniform(-1000, 2000),
                trade_pnl=pnl,
                strategy=strategy_name
            )
            trades.append(trade)
        
        # Create BacktestResult
        final_value = portfolio_values[-1]
        total_return = final_value - 10000
        total_return_pct = (total_return / 10000) * 100
        
        result = BacktestResult(
            strategy=strategy_name,
            initial_capital=10000,
            final_capital=final_value,
            total_return=total_return,
            total_return_pct=params['return_pct'],
            max_drawdown_pct=params['drawdown'],
            sharpe_ratio=params['sharpe'],
            total_trades=params['trades'],
            winning_trades=int(params['trades'] * params['win_rate']),
            losing_trades=int(params['trades'] * (1 - params['win_rate'])),
            win_rate=params['win_rate'],
            profit_factor=1.85,
            avg_win=125.50,
            avg_loss=-85.30,
            trades=trades,
            equity_curve=equity_curve,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        results[strategy_name] = result
    
    return results


def main():
    """Generate sample HTML reports"""
    
    print("🚀 Generating Sample HTML Reports...")
    
    # Initialize HTML report generator
    generator = HTMLReportGenerator(output_dir="sample_reports")
    
    # Generate single strategy report
    print("\n📊 Generating single strategy report...")
    single_result = create_sample_data()
    
    single_report_path = generator.generate_single_strategy_report(
        strategy_name="Sample Momentum Strategy",
        result=single_result,
        symbols=['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    print(f"✅ Single strategy report: {single_report_path}")
    
    # Generate comparison report
    print("\n📈 Generating comparison report...")
    multiple_results = create_multiple_strategies()
    
    comparison_report_path = generator.generate_report(
        results=multiple_results,
        symbols=['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        start_date='2024-01-01',
        end_date='2024-12-31',
        report_title="Sample Strategy Comparison Report"
    )
    
    print(f"✅ Comparison report: {comparison_report_path}")
    
    print(f"\n🎉 Sample reports generated successfully!")
    print(f"📁 Reports saved to: sample_reports/html/")
    print("💡 Open the HTML files in your web browser to view the reports")
    print("\n📋 Report Features:")
    print("   • MetaTrader-style professional design")
    print("   • Interactive charts with Plotly")
    print("   • Comprehensive performance metrics")
    print("   • Trade-by-trade analysis")
    print("   • Strategy comparison tables")
    print("   • Risk-return scatter plots")
    print("   • Mobile-responsive layout")


if __name__ == "__main__":
    main() 