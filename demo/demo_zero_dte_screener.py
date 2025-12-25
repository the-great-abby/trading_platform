#!/usr/bin/env python3
"""
Demo: 0-DTE Covered Call Screener
==================================
Demonstrates the 0-DTE covered call screening workflow.

This demo shows:
1. Basic screening for SPY
2. Multi-ticker screening
3. Custom parameter screening
4. Results analysis
5. Mark-to-market P&L calculation

Requirements:
- Polygon.io API key (Options Advanced plan)
- POLYGON_API_KEY environment variable set
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import pandas as pd

from src.strategies.options.zero_dte_covered_call_strategy import (
    ZeroDTECoveredCallStrategy
)
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


def demo_basic_screening():
    """Demo 1: Basic 0-DTE screening for SPY"""
    print("\n" + "="*80)
    print("DEMO 1: Basic 0-DTE Screening for SPY")
    print("="*80)
    
    # Create strategy with default parameters
    strategy = ZeroDTECoveredCallStrategy(
        target_tickers=["SPY"]
    )
    
    # Show strategy info
    info = strategy.get_strategy_info()
    print(f"\n📊 Strategy: {info['name']}")
    print(f"Type: {info['type']}")
    print(f"Description: {info['description']}")
    print(f"\nParameters:")
    for key, value in info['parameters'].items():
        print(f"  • {key}: {value}")
    
    # Run scan
    print("\n🔍 Scanning for 0-DTE opportunities...")
    results = strategy.scan_multiple_tickers(["SPY"])
    
    if not results.empty:
        print(f"\n✅ Found {len(results)} candidates")
        print("\nTop 5 by premium yield:")
        print(results.head()[['ticker', 'strike', 'mid', 'premium_yield', 'delta', 'pop_est']].to_string())
        return results
    else:
        print("\n❌ No candidates found")
        return pd.DataFrame()


def demo_multi_ticker_screening():
    """Demo 2: Multi-ticker screening"""
    print("\n" + "="*80)
    print("DEMO 2: Multi-Ticker Screening (SPY, QQQ, IWM)")
    print("="*80)
    
    tickers = ["SPY", "QQQ", "IWM"]
    
    # Create strategy
    strategy = ZeroDTECoveredCallStrategy(
        target_tickers=tickers,
        rank_metric="premium_yield"
    )
    
    # Run scan
    print(f"\n🔍 Scanning {', '.join(tickers)} for 0-DTE opportunities...")
    results = strategy.scan_multiple_tickers(tickers)
    
    if not results.empty:
        print(f"\n✅ Found {len(results)} total candidates")
        
        # Show breakdown by ticker
        print("\nBreakdown by ticker:")
        for ticker in tickers:
            ticker_results = results[results['ticker'] == ticker]
            print(f"  • {ticker}: {len(ticker_results)} candidates")
        
        # Show top 3 overall
        print("\nTop 3 overall by premium yield:")
        top_3 = results.head(3)
        for i, (idx, row) in enumerate(top_3.iterrows(), 1):
            print(f"\n{i}. {row['ticker']} ${row['strike']:.2f} strike")
            print(f"   Premium: ${row['mid']:.2f} ({row['premium_yield']:.2%} yield)")
            print(f"   Delta: {row['delta']:.3f if row['delta'] else 'N/A'}")
            print(f"   Max Profit: ${row['max_profit']:.2f}")
        
        return results
    else:
        print("\n❌ No candidates found")
        return pd.DataFrame()


def demo_custom_parameters():
    """Demo 3: Custom parameter screening"""
    print("\n" + "="*80)
    print("DEMO 3: Custom Parameter Screening")
    print("="*80)
    
    print("\nScenario: Conservative 0-DTE screening")
    print("  • Tighter delta band (20-30 delta)")
    print("  • Wider OTM range (2-5%)")
    print("  • Higher minimum bid ($0.10)")
    print("  • Rank by probability of profit")
    
    # Create strategy with custom parameters
    strategy = ZeroDTECoveredCallStrategy(
        target_tickers=["SPY"],
        delta_lo=0.20,
        delta_hi=0.30,
        min_otm_pct=0.02,
        max_otm_pct=0.05,
        min_bid=0.10,
        rank_metric="pop_est"
    )
    
    # Run scan
    print("\n🔍 Scanning with custom parameters...")
    results = strategy.scan_multiple_tickers(["SPY"])
    
    if not results.empty:
        print(f"\n✅ Found {len(results)} candidates")
        print("\nTop 5 by probability of profit:")
        display_df = results.head()[['ticker', 'strike', 'mid', 'premium_yield', 'delta', 'pop_est', 'score']]
        print(display_df.to_string())
        return results
    else:
        print("\n❌ No candidates found with these parameters")
        return pd.DataFrame()


def demo_analysis():
    """Demo 4: Results analysis"""
    print("\n" + "="*80)
    print("DEMO 4: Results Analysis")
    print("="*80)
    
    # Run a scan
    strategy = ZeroDTECoveredCallStrategy(target_tickers=["SPY"])
    results = strategy.scan_multiple_tickers(["SPY"])
    
    if results.empty:
        print("\n❌ No results to analyze")
        return
    
    print(f"\n📊 Analyzing {len(results)} candidates...")
    
    # Calculate statistics
    avg_premium_yield = results['premium_yield'].mean()
    avg_max_profit = results['max_profit'].mean()
    avg_delta = results['delta'].mean() if results['delta'].notna().any() else None
    avg_pop = results['pop_est'].mean() if results['pop_est'].notna().any() else None
    
    print(f"\nStatistics:")
    print(f"  • Average Premium Yield: {avg_premium_yield:.2%}")
    print(f"  • Average Max Profit: ${avg_max_profit:.2f}")
    if avg_delta:
        print(f"  • Average Delta: {avg_delta:.3f}")
    if avg_pop:
        print(f"  • Average POP: {avg_pop:.1%}")
    
    # Strike distribution
    print(f"\nStrike Distribution:")
    strike_range = results['strike'].max() - results['strike'].min()
    print(f"  • Range: ${results['strike'].min():.2f} - ${results['strike'].max():.2f}")
    print(f"  • Spread: ${strike_range:.2f}")
    
    # Premium distribution
    print(f"\nPremium Distribution:")
    print(f"  • Min: ${results['mid'].min():.2f}")
    print(f"  • Median: ${results['mid'].median():.2f}")
    print(f"  • Max: ${results['mid'].max():.2f}")
    
    # Open interest analysis
    print(f"\nLiquidity (Open Interest):")
    print(f"  • Min: {results['open_interest'].min()}")
    print(f"  • Median: {results['open_interest'].median():.0f}")
    print(f"  • Max: {results['open_interest'].max()}")


def demo_pnl_marking():
    """Demo 5: Mark-to-market P&L calculation"""
    print("\n" + "="*80)
    print("DEMO 5: Mark-to-Market P&L Calculation")
    print("="*80)
    
    print("\nScenario: Simulating end-of-day P&L marking")
    print("  • Scan performed at market open")
    print("  • Underlying closes at different prices")
    print("  • Calculate realized P&L for each scenario")
    
    # Run a scan
    strategy = ZeroDTECoveredCallStrategy(target_tickers=["SPY"])
    results = strategy.scan_multiple_tickers(["SPY"])
    
    if results.empty:
        print("\n❌ No results to mark")
        return
    
    # Save results to temp CSV
    temp_csv = "./data/demo_0dte_scan.csv"
    os.makedirs("./data", exist_ok=True)
    results.to_csv(temp_csv, index=False)
    
    # Get average spot price
    avg_spot = results['spot'].iloc[0]
    
    # Scenario 1: Stock flat
    print(f"\n📊 Scenario 1: Stock closes FLAT at ${avg_spot:.2f}")
    marked_1 = strategy.mark_realized_pnl(temp_csv, avg_spot)
    df1 = pd.read_csv(marked_1)
    print(f"  • Average P&L: ${df1['pnl_per_contract'].mean():.2f}")
    print(f"  • Win Rate: {(df1['pnl_per_contract'] > 0).mean():.1%}")
    print(f"  • Assignments: {df1['assigned'].sum()} / {len(df1)}")
    
    # Scenario 2: Stock up 1%
    close_up = avg_spot * 1.01
    print(f"\n📊 Scenario 2: Stock closes UP 1% at ${close_up:.2f}")
    marked_2 = strategy.mark_realized_pnl(temp_csv, close_up)
    df2 = pd.read_csv(marked_2)
    print(f"  • Average P&L: ${df2['pnl_per_contract'].mean():.2f}")
    print(f"  • Win Rate: {(df2['pnl_per_contract'] > 0).mean():.1%}")
    print(f"  • Assignments: {df2['assigned'].sum()} / {len(df2)}")
    
    # Scenario 3: Stock down 1%
    close_down = avg_spot * 0.99
    print(f"\n📊 Scenario 3: Stock closes DOWN 1% at ${close_down:.2f}")
    marked_3 = strategy.mark_realized_pnl(temp_csv, close_down)
    df3 = pd.read_csv(marked_3)
    print(f"  • Average P&L: ${df3['pnl_per_contract'].mean():.2f}")
    print(f"  • Win Rate: {(df3['pnl_per_contract'] > 0).mean():.1%}")
    print(f"  • Assignments: {df3['assigned'].sum()} / {len(df3)}")
    
    # Cleanup
    for file in [marked_1, marked_2, marked_3]:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists(temp_csv):
        os.remove(temp_csv)


def main():
    """Run all demos"""
    print("="*80)
    print("🚀 0-DTE Covered Call Screener Demo")
    print("="*80)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases the 0-DTE covered call screening capabilities.")
    print("\nNote: Requires Polygon.io API key with Options Advanced plan.")
    
    # Check for API key
    if not os.getenv('POLYGON_API_KEY'):
        print("\n⚠️ WARNING: POLYGON_API_KEY not found in environment")
        print("Set it with: export POLYGON_API_KEY=your_key_here")
        print("\nContinuing with demo (may fail on live API calls)...\n")
    
    try:
        # Run demos
        demo_basic_screening()
        input("\nPress Enter to continue to next demo...")
        
        demo_multi_ticker_screening()
        input("\nPress Enter to continue to next demo...")
        
        demo_custom_parameters()
        input("\nPress Enter to continue to next demo...")
        
        demo_analysis()
        input("\nPress Enter to continue to next demo...")
        
        demo_pnl_marking()
        
        print("\n" + "="*80)
        print("✅ Demo completed successfully!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Run real screening: make -f makefiles/Makefile.zero-dte screen")
        print("  2. Screen multiple tickers: make -f makefiles/Makefile.zero-dte screen-multi")
        print("  3. Use custom parameters: make -f makefiles/Makefile.zero-dte screen-custom SYMBOL=TSLA")
        print("  4. Mark P&L after close: make -f makefiles/Makefile.zero-dte mark CSV_PATH=... CLOSE_PRICE=...")
        print("\nFor more info: make -f makefiles/Makefile.zero-dte help")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

