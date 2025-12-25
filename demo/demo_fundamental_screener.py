#!/usr/bin/env python3
"""
Demo: Fundamental Stock Screener
Focus on screening capabilities with different strategies
"""

import os
import sys
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print(f"   Set POLYGON_API_KEY environment variable or create .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")
    print("   Install with: pip install python-dotenv")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.analysis.fundamental_screener import (
    FundamentalScreener,
    ScreenerCriteria,
    ScreenerCondition
)
from src.utils.trading_config import SYMBOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def screen_value_stocks():
    """Find value stocks from our watchlist"""
    print("\n" + "="*80)
    print("VALUE STOCK SCREENING")
    print("="*80)
    
    screener = FundamentalScreener()
    
    # Use smaller subset for demo
    tickers = SYMBOLS[:20]
    
    print(f"\nScreening {len(tickers)} stocks for value characteristics...")
    results = screener.screen_with_preset(tickers, "value_stocks", min_score=70.0)
    
    print(f"\nFound {len(results)} value stocks (score >= 70%):\n")
    
    for result in results:
        r = result.ratios
        print(f"{result.ticker} - Score: {result.score:.0f}%")
        print(f"  Price: ${r.price:.2f}")
        print(f"  P/E: {r.price_to_earnings:.2f}" if r.price_to_earnings else "  P/E: N/A")
        print(f"  P/B: {r.price_to_book:.2f}" if r.price_to_book else "  P/B: N/A")
        print(f"  ROE: {r.return_on_equity*100:.1f}%" if r.return_on_equity else "  ROE: N/A")
        print(f"  D/E: {r.debt_to_equity:.2f}" if r.debt_to_equity is not None else "  D/E: N/A")
        print()


def screen_dividend_stocks():
    """Find high dividend yield stocks"""
    print("\n" + "="*80)
    print("DIVIDEND STOCK SCREENING")
    print("="*80)
    
    screener = FundamentalScreener()
    
    tickers = SYMBOLS[:20]
    
    print(f"\nScreening {len(tickers)} stocks for dividend characteristics...")
    results = screener.screen_with_preset(tickers, "dividend_stocks", min_score=70.0)
    
    print(f"\nFound {len(results)} dividend stocks (score >= 70%):\n")
    
    for result in results:
        r = result.ratios
        print(f"{result.ticker} - Score: {result.score:.0f}%")
        print(f"  Dividend Yield: {r.dividend_yield*100:.2f}%" if r.dividend_yield else "  Dividend Yield: 0.00%")
        print(f"  Payout Ratio: Stable" if r.current and r.current > 1.0 else "  Payout Ratio: Review")
        print(f"  Current Ratio: {r.current:.2f}" if r.current else "  Current Ratio: N/A")
        print(f"  D/E: {r.debt_to_equity:.2f}" if r.debt_to_equity is not None else "  D/E: N/A")
        print()


def screen_quality_stocks():
    """Find high quality stocks (Buffett-style)"""
    print("\n" + "="*80)
    print("QUALITY STOCK SCREENING (BUFFETT STYLE)")
    print("="*80)
    
    screener = FundamentalScreener()
    
    tickers = SYMBOLS[:20]
    
    print(f"\nScreening {len(tickers)} stocks for quality characteristics...")
    results = screener.screen_with_preset(tickers, "buffett_style", min_score=60.0)
    
    print(f"\nFound {len(results)} quality stocks (score >= 60%):\n")
    
    for result in results:
        r = result.ratios
        print(f"{result.ticker} - Score: {result.score:.0f}%")
        print(f"  ROE: {r.return_on_equity*100:.1f}%" if r.return_on_equity else "  ROE: N/A")
        print(f"  D/E: {r.debt_to_equity:.2f}" if r.debt_to_equity is not None else "  D/E: N/A")
        print(f"  Current Ratio: {r.current:.2f}" if r.current else "  Current Ratio: N/A")
        print(f"  P/E: {r.price_to_earnings:.2f}" if r.price_to_earnings else "  P/E: N/A")
        print()


def custom_screening_example():
    """Example of custom screening criteria"""
    print("\n" + "="*80)
    print("CUSTOM SCREENING EXAMPLE")
    print("="*80)
    
    screener = FundamentalScreener()
    
    # Define custom criteria: Low P/E, High ROE, Low Debt
    criteria = [
        ScreenerCriteria("price_to_earnings", ScreenerCondition.LESS_THAN, 20),
        ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.18),
        ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.0),
        ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.5),
    ]
    
    tickers = SYMBOLS[:15]
    
    print(f"\nCustom Criteria:")
    print("  - P/E < 20")
    print("  - ROE > 18%")
    print("  - D/E < 1.0")
    print("  - Current Ratio > 1.5")
    
    print(f"\nScreening {len(tickers)} stocks...")
    results = screener.screen_stocks(tickers, criteria, min_score=75.0)
    
    print(f"\nFound {len(results)} stocks meeting criteria (score >= 75%):\n")
    
    for result in results:
        print(f"{result.ticker} - Score: {result.score:.0f}%")
        print(f"  Passed: {', '.join(result.passed_criteria)}")
        print()


def main():
    """Run screening demos"""
    print("\n" + "="*80)
    print("FUNDAMENTAL SCREENER DEMOS")
    print("="*80)
    
    try:
        screen_value_stocks()
        screen_dividend_stocks()
        screen_quality_stocks()
        custom_screening_example()
        
        print("\n" + "="*80)
        print("SCREENING COMPLETE!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

