#!/usr/bin/env python3
"""
Short Backtesting Script - Test strategies with 1 year of real data
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.results_exporter import BacktestResultsExporter


async def main():
    """Run backtesting for all strategies with 1 year of data"""
    
    print("🚀 Starting Short Backtesting Analysis (1 Year)")
    print("=" * 60)
    
    # Configuration - 1 year period
    initial_capital = 100000.0  # $100k starting capital
    end_date = datetime.now() - timedelta(days=30)  # 30 days ago to avoid future dates
    start_date = (end_date - timedelta(days=365)).strftime("%Y-%m-%d")  # 1 year before
    end_date = end_date.strftime("%Y-%m-%d")
    
    # Reduced set of major stocks for testing
    symbols = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "INTC", "AMD"
    ]
    
    # Available strategies
    strategies = [
        "sma_crossover",
        "rsi", 
        "macd",
        "bollinger_bands"
    ]
    
    print(f"📊 Test Configuration:")
    print(f"   Initial Capital: ${initial_capital:,.2f}")
    print(f"   Test Period: {start_date} to {end_date}")
    print(f"   Symbols: {len(symbols)} stocks")
    print(f"   Strategies: {', '.join(strategies)}")
    print()
    
    # Initialize backtesting engine
    print("🔧 Initializing Backtesting Engine...")
    engine = BacktestEngine(use_real_data=True)
    
    # Run backtests
    print("🏃 Running Backtests...")
    print("-" * 40)
    
    results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=strategies
    )
    
    print()
    print("✅ Backtesting Complete!")
    print("-" * 40)
    
    # Display quick summary
    print("📈 Quick Results Summary:")
    for strategy_name, result in results.items():
        status = "🟢" if result.total_return_pct > 0 else "🔴"
        print(f"   {status} {strategy_name:15} {result.total_return_pct:6.2f}% return, {result.total_trades:3d} trades")
    
    print()
    
    # Export results
    print("📤 Exporting Results...")
    exporter = BacktestResultsExporter()
    
    # Export all results
    exporter.export_results(results, symbols, start_date, end_date)
    
    # Generate comprehensive report
    report_path = exporter.generate_summary_report(results, symbols, start_date, end_date)
    
    print()
    print("🎯 Analysis Complete!")
    print("=" * 60)
    print(f"📄 Comprehensive Report: {report_path}")
    print(f"📁 All Results: {exporter.output_dir}")
    print()
    
    # Display key insights
    print("🔍 Key Insights:")
    
    # Best performing strategy
    best_strategy = max(results.items(), key=lambda x: x[1].total_return_pct)
    print(f"   🏆 Best Strategy: {best_strategy[0]} ({best_strategy[1].total_return_pct:.2f}% return)")
    
    # Most active strategy
    most_active = max(results.items(), key=lambda x: x[1].total_trades)
    print(f"   📊 Most Active: {most_active[0]} ({most_active[1].total_trades} trades)")
    
    # Best risk-adjusted return
    best_sharpe = max(results.items(), key=lambda x: x[1].sharpe_ratio)
    print(f"   ⚖️  Best Risk-Adjusted: {best_sharpe[0]} (Sharpe: {best_sharpe[1].sharpe_ratio:.3f})")
    
    # Profitable strategies
    profitable = [name for name, result in results.items() if result.total_return_pct > 0]
    if profitable:
        print(f"   💰 Profitable Strategies: {', '.join(profitable)}")
    else:
        print("   ⚠️  No strategies were profitable in this period")
    
    print()
    print("📋 Next Steps:")
    print("   1. Review the detailed CSV files in the backtest_results/csv/ directory")
    print("   2. Check the markdown reports in backtest_results/markdown/ directory")
    print("   3. Analyze individual trade details for each strategy")
    print("   4. Consider parameter optimization for the best performing strategies")
    print("   5. Test with different time periods or market conditions")
    
    return results


if __name__ == "__main__":
    import asyncio
    try:
        results = asyncio.run(main())
        print("\n✅ Backtesting completed successfully!")
    except Exception as e:
        print(f"\n❌ Backtesting failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 