#!/usr/bin/env python3
"""
0-DTE Covered Call Screener
===========================
Standalone script for screening 0-DTE covered call opportunities.

Usage:
    # Screen SPY for today's expiration
    python scripts/zero_dte_screener.py screen --symbol SPY
    
    # Screen multiple tickers with custom parameters
    python scripts/zero_dte_screener.py screen --symbols SPY,QQQ,IWM --max-otm-pct 0.05
    
    # Mark realized P&L after close
    python scripts/zero_dte_screener.py mark --csv ./data/0dte_covered_calls_2025-10-21.csv --close-price 444.83
    
    # Screen with custom delta band
    python scripts/zero_dte_screener.py screen --symbol SPY --delta-lo 0.20 --delta-hi 0.40
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    env_locations = [
        project_root / '.env',
        project_root / 'config.env',
        Path.home() / '.trading' / '.env'
    ]
    
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from: {env_path}")
            break
    else:
        # Try loading from current directory
        load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("    Or set POLYGON_API_KEY environment variable manually.")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

import argparse
import logging
from typing import List
import pandas as pd

from src.strategies.options.zero_dte_covered_call_strategy import (
    ZeroDTECoveredCallStrategy,
    CreditSpreadCandidate
)
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


def screen_command(args):
    """Run the 0-DTE screener"""
    # Parse symbols
    if args.symbols:
        tickers = [s.strip().upper() for s in args.symbols.split(',')]
    else:
        tickers = [args.symbol.upper()]
    
    logger.info(f"🚀 Starting 0-DTE screener for: {', '.join(tickers)}")
    
    # Create strategy instance
    strategy = ZeroDTECoveredCallStrategy(
        expiration_days=args.expiration_days,
        min_otm_pct=args.min_otm_pct,
        max_otm_pct=args.max_otm_pct,
        delta_lo=args.delta_lo,
        delta_hi=args.delta_hi,
        min_bid=args.min_bid,
        min_open_interest=args.min_open_interest,
        max_spread_to_mid=args.max_spread_to_mid,
        rank_metric=args.rank_metric,
        target_tickers=tickers
    )
    
    # Run scan
    results_df = strategy.scan_multiple_tickers(tickers)
    
    if results_df.empty:
        logger.warning("❌ No 0-DTE candidates found")
        return 1
    
    # Display results
    print("\n" + "="*100)
    print("📊 0-DTE COVERED CALL CANDIDATES")
    print("="*100)
    
    # Select columns to display
    display_cols = [
        'ticker', 'strike', 'mid', 'premium_yield', 'delta', 
        'max_profit', 'breakeven', 'pop_est', 'open_interest', 'score'
    ]
    
    # Format for display
    display_df = results_df[display_cols].copy()
    display_df['premium_yield'] = display_df['premium_yield'].apply(lambda x: f"{x:.2%}")
    display_df['mid'] = display_df['mid'].apply(lambda x: f"${x:.2f}")
    display_df['strike'] = display_df['strike'].apply(lambda x: f"${x:.2f}")
    display_df['max_profit'] = display_df['max_profit'].apply(lambda x: f"${x:.2f}")
    display_df['breakeven'] = display_df['breakeven'].apply(lambda x: f"${x:.2f}")
    display_df['delta'] = display_df['delta'].apply(lambda x: f"{x:.3f}" if x else "N/A")
    display_df['pop_est'] = display_df['pop_est'].apply(lambda x: f"{x:.1%}" if x else "N/A")
    display_df['score'] = display_df['score'].apply(lambda x: f"{x:.3f}")
    
    print(display_df.to_string(index=False))
    print("="*100)
    
    # Show top 3 recommendations
    print("\n🎯 TOP 3 RECOMMENDATIONS:")
    for i, (idx, row) in enumerate(results_df.head(3).iterrows(), 1):
        print(f"\n{i}. {row['ticker']} ${row['strike']:.2f} strike")
        print(f"   Premium: ${row['mid']:.2f} ({row['premium_yield']:.2%} yield)")
        print(f"   Max Profit: ${row['max_profit']:.2f} | Breakeven: ${row['breakeven']:.2f}")
        delta_str = f"{row['delta']:.3f}" if row['delta'] else 'N/A'
        pop_str = f"{row['pop_est']:.1%}" if row['pop_est'] else 'N/A'
        print(f"   Delta: {delta_str} | POP: {pop_str}")
        print(f"   Open Interest: {row['open_interest']} | Score: {row['score']:.3f}")
    
    # Save results
    if not args.no_save:
        output_path = strategy.save_scan_results(results_df, args.outdir)
        print(f"\n💾 Results saved to: {output_path}")
    
    logger.info(f"✅ Screener completed successfully - found {len(results_df)} candidates")
    return 0


def screen_spreads_command(args):
    """Run the credit spread screener"""
    # Parse symbols
    if args.symbols:
        tickers = [s.strip().upper() for s in args.symbols.split(',')]
    else:
        tickers = [args.symbol.upper()]
    
    logger.info(f"🚀 Starting 0-DTE CREDIT SPREAD screener for: {', '.join(tickers)}")
    logger.info(f"   Spread width: {args.spread_width} points")
    logger.info(f"   Minimum credit: ${args.min_credit:.2f}")
    
    # Create strategy instance
    strategy = ZeroDTECoveredCallStrategy(
        expiration_days=args.expiration_days,
        min_otm_pct=args.min_otm_pct,
        max_otm_pct=args.max_otm_pct,
        delta_lo=args.delta_lo,
        delta_hi=args.delta_hi,
        min_bid=args.min_bid,
        min_open_interest=args.min_open_interest,
        max_spread_to_mid=args.max_spread_to_mid,
        target_tickers=tickers
    )
    
    # Run credit spread scan
    results_df = strategy.scan_credit_spreads_multiple_tickers(
        tickers=tickers,
        spread_width=args.spread_width,
        min_credit=args.min_credit
    )
    
    if results_df.empty:
        logger.warning("❌ No credit spread candidates found")
        return 1
    
    # Display results
    print("\n" + "="*120)
    print("💰 0-DTE CREDIT SPREAD CANDIDATES")
    print("="*120)
    
    # Select columns to display
    display_cols = [
        'ticker', 'short_strike', 'long_strike', 'spread_width',
        'net_credit', 'max_loss', 'max_profit', 'return_on_capital',
        'risk_reward_ratio', 'pop_est', 'score'
    ]
    
    # Format for display
    display_df = results_df[display_cols].copy()
    display_df['short_strike'] = display_df['short_strike'].apply(lambda x: f"${x:.2f}")
    display_df['long_strike'] = display_df['long_strike'].apply(lambda x: f"${x:.2f}")
    display_df['net_credit'] = display_df['net_credit'].apply(lambda x: f"${x:.2f}")
    display_df['max_loss'] = display_df['max_loss'].apply(lambda x: f"${x:.2f}")
    display_df['max_profit'] = display_df['max_profit'].apply(lambda x: f"${x:.2f}")
    display_df['return_on_capital'] = display_df['return_on_capital'].apply(lambda x: f"{x:.1%}")
    display_df['risk_reward_ratio'] = display_df['risk_reward_ratio'].apply(lambda x: f"{x:.1f}:1")
    display_df['pop_est'] = display_df['pop_est'].apply(lambda x: f"{x:.1%}" if x else "N/A")
    display_df['score'] = display_df['score'].apply(lambda x: f"{x:.3f}")
    
    print(display_df.to_string(index=False))
    print("="*120)
    
    # Show top 3 recommendations
    print("\n🎯 TOP 3 CREDIT SPREAD RECOMMENDATIONS:")
    for i, (idx, row) in enumerate(results_df.head(3).iterrows(), 1):
        print(f"\n{i}. {row['ticker']} ${row['short_strike']:.2f}/${row['long_strike']:.2f} spread ({row['spread_width']:.0f}-wide)")
        print(f"   SELL  1x ${row['short_strike']:.2f} call @ ${row['short_mid']:.2f}")
        print(f"   BUY   1x ${row['long_strike']:.2f} call @ ${row['long_mid']:.2f}")
        print(f"   ───────────────────────────────────")
        print(f"   Net Credit: ${row['net_credit']:.2f} × 100 = ${row['net_credit']*100:.0f}")
        print(f"   Max Loss: ${row['max_loss']:.2f} × 100 = ${row['max_loss']*100:.0f}")
        print(f"   Max Profit: ${row['max_profit']:.2f} × 100 = ${row['max_profit']*100:.0f}")
        print(f"   Return on Capital: {row['return_on_capital']:.1%}")
        print(f"   Risk/Reward: {row['risk_reward_ratio']:.1f}:1")
        if row['pop_est']:
            print(f"   POP: {row['pop_est']:.1%}")
        else:
            print(f"   POP: N/A")
        print(f"   Score: {row['score']:.3f}")
    
    # Capital requirement summary
    print(f"\n💵 CAPITAL REQUIREMENTS:")
    print(f"   Per Spread: ${results_df['max_loss'].iloc[0]*100:.0f} (for {results_df['spread_width'].iloc[0]:.0f}-wide)")
    print(f"   For 5 Spreads: ${results_df['max_loss'].iloc[0]*100*5:.0f}")
    print(f"   For 10 Spreads: ${results_df['max_loss'].iloc[0]*100*10:.0f}")
    
    # Save results
    if not args.no_save:
        import os
        from pathlib import Path
        from datetime import datetime
        
        Path(args.outdir).mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"0dte_credit_spreads_{date_str}.csv"
        filepath = os.path.join(args.outdir, filename)
        results_df.to_csv(filepath, index=False)
        print(f"\n💾 Results saved to: {filepath}")
    
    logger.info(f"✅ Credit spread screener completed - found {len(results_df)} candidates")
    return 0


def mark_command(args):
    """Mark realized P&L for a previous scan"""
    if not os.path.exists(args.csv):
        logger.error(f"❌ CSV file not found: {args.csv}")
        return 1
    
    logger.info(f"📊 Marking P&L for {args.csv} with close price ${args.close_price:.2f}")
    
    # Create strategy instance
    strategy = ZeroDTECoveredCallStrategy()
    
    # Mark P&L
    marked_path = strategy.mark_realized_pnl(args.csv, args.close_price)
    
    # Load and display summary
    marked_df = pd.read_csv(marked_path)
    
    print("\n" + "="*100)
    print("📈 REALIZED P&L SUMMARY")
    print("="*100)
    
    total_candidates = len(marked_df)
    assigned_count = marked_df['assigned'].sum()
    avg_pnl = marked_df['pnl_per_contract'].mean()
    total_pnl = marked_df['pnl_per_contract'].sum()
    win_rate = (marked_df['pnl_per_contract'] > 0).mean()
    avg_return = marked_df['return_on_capital'].mean()
    
    print(f"Total Candidates: {total_candidates}")
    print(f"Assigned: {assigned_count} ({assigned_count/total_candidates:.1%})")
    print(f"Average P&L per Contract: ${avg_pnl:.2f}")
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Average Return on Capital: {avg_return:.2%}")
    print("="*100)
    
    # Show top/bottom performers
    print("\n🏆 TOP 3 PERFORMERS:")
    top_3 = marked_df.nlargest(3, 'pnl_per_contract')
    for i, (idx, row) in enumerate(top_3.iterrows(), 1):
        print(f"{i}. {row['ticker']} ${row['strike']:.2f} strike: "
              f"${row['pnl_per_contract']:.2f} "
              f"({'Assigned' if row['assigned'] else 'Expired'})")
    
    print("\n📉 BOTTOM 3 PERFORMERS:")
    bottom_3 = marked_df.nsmallest(3, 'pnl_per_contract')
    for i, (idx, row) in enumerate(bottom_3.iterrows(), 1):
        print(f"{i}. {row['ticker']} ${row['strike']:.2f} strike: "
              f"${row['pnl_per_contract']:.2f} "
              f"({'Assigned' if row['assigned'] else 'Expired'})")
    
    print(f"\n💾 Marked results saved to: {marked_path}")
    
    logger.info("✅ P&L marking completed successfully")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="0-DTE Covered Call Screener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Commands')
    
    # Screen command
    screen_parser = subparsers.add_parser('screen', help='Run the screener')
    screen_parser.add_argument('--symbol', default='SPY', help='Single symbol to screen')
    screen_parser.add_argument('--symbols', help='Comma-separated list of symbols (e.g., SPY,QQQ,IWM)')
    screen_parser.add_argument('--expiration-days', type=int, default=0, 
                              help='Days to expiration (0 for 0-DTE)')
    screen_parser.add_argument('--min-otm-pct', type=float, default=0.00,
                              help='Minimum OTM percentage (default: 0.00)')
    screen_parser.add_argument('--max-otm-pct', type=float, default=0.03,
                              help='Maximum OTM percentage (default: 0.03)')
    screen_parser.add_argument('--delta-lo', type=float, default=0.15,
                              help='Minimum delta (default: 0.15)')
    screen_parser.add_argument('--delta-hi', type=float, default=0.35,
                              help='Maximum delta (default: 0.35)')
    screen_parser.add_argument('--min-bid', type=float, default=0.05,
                              help='Minimum bid price (default: 0.05)')
    screen_parser.add_argument('--min-open-interest', type=int, default=1,
                              help='Minimum open interest (default: 1)')
    screen_parser.add_argument('--max-spread-to-mid', type=float, default=0.75,
                              help='Maximum spread as % of mid (default: 0.75)')
    screen_parser.add_argument('--rank-metric', 
                              choices=['premium_yield', 'max_profit', 'pop_est', 'score'],
                              default='premium_yield',
                              help='Ranking metric (default: premium_yield)')
    screen_parser.add_argument('--outdir', default='./data',
                              help='Output directory for CSV (default: ./data)')
    screen_parser.add_argument('--no-save', action='store_true',
                              help='Do not save results to CSV')
    screen_parser.set_defaults(func=screen_command)
    
    # Credit spreads command
    spreads_parser = subparsers.add_parser('screen-spreads', help='Screen for credit spreads')
    spreads_parser.add_argument('--symbol', default='SPY', help='Single symbol to screen')
    spreads_parser.add_argument('--symbols', help='Comma-separated list of symbols')
    spreads_parser.add_argument('--expiration-days', type=int, default=0,
                                help='Days to expiration (0 for 0-DTE)')
    spreads_parser.add_argument('--spread-width', type=float, default=2.0,
                                help='Spread width in points (default: 2.0)')
    spreads_parser.add_argument('--min-credit', type=float, default=0.10,
                                help='Minimum net credit (default: 0.10)')
    spreads_parser.add_argument('--min-otm-pct', type=float, default=0.00,
                                help='Minimum OTM percentage (default: 0.00)')
    spreads_parser.add_argument('--max-otm-pct', type=float, default=0.03,
                                help='Maximum OTM percentage (default: 0.03)')
    spreads_parser.add_argument('--delta-lo', type=float, default=0.15,
                                help='Minimum delta (default: 0.15)')
    spreads_parser.add_argument('--delta-hi', type=float, default=0.35,
                                help='Maximum delta (default: 0.35)')
    spreads_parser.add_argument('--min-bid', type=float, default=0.05,
                                help='Minimum bid price for short strike (default: 0.05)')
    spreads_parser.add_argument('--min-open-interest', type=int, default=1,
                                help='Minimum open interest (default: 1)')
    spreads_parser.add_argument('--max-spread-to-mid', type=float, default=0.75,
                                help='Maximum spread as % of mid (default: 0.75)')
    spreads_parser.add_argument('--outdir', default='./data',
                                help='Output directory for CSV (default: ./data)')
    spreads_parser.add_argument('--no-save', action='store_true',
                                help='Do not save results to CSV')
    spreads_parser.set_defaults(func=screen_spreads_command)
    
    # Mark command
    mark_parser = subparsers.add_parser('mark', help='Mark realized P&L')
    mark_parser.add_argument('--csv', required=True, help='Path to scan CSV file')
    mark_parser.add_argument('--close-price', type=float, required=True,
                            help='Closing price of underlying')
    mark_parser.set_defaults(func=mark_command)
    
    args = parser.parse_args()
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

