#!/usr/bin/env python3
"""
Demo: Fundamental Analysis with Polygon Financials API
Demonstrates comprehensive fundamental screening, health scoring, and AI integration
"""

import os
import sys
import logging
from datetime import datetime

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

from src.services.market_data.polygon_financials import PolygonFinancialsClient
from src.services.analysis.fundamental_screener import FundamentalScreener
from src.services.analysis.fundamental_ai_analyzer import FundamentalAIAnalyzer
from src.utils.trading_config import SYMBOLS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_financial_ratios():
    """Demo: Get financial ratios for stocks"""
    print("\n" + "="*80)
    print("DEMO 1: Financial Ratios Analysis")
    print("="*80)
    
    client = PolygonFinancialsClient()
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "JPM"]
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} Financial Ratios ---")
        ratios_list = client.get_ratios(ticker, limit=1)
        
        if ratios_list:
            r = ratios_list[0]
            print(f"Date: {r.date}")
            print(f"Price: ${r.price:.2f}")
            print(f"Market Cap: ${r.market_cap/1e9:.2f}B" if r.market_cap else "N/A")
            print(f"\nValuation:")
            print(f"  P/E Ratio: {r.price_to_earnings:.2f}" if r.price_to_earnings else "  P/E Ratio: N/A")
            print(f"  P/B Ratio: {r.price_to_book:.2f}" if r.price_to_book else "  P/B Ratio: N/A")
            print(f"  EV/EBITDA: {r.ev_to_ebitda:.2f}" if r.ev_to_ebitda else "  EV/EBITDA: N/A")
            print(f"\nProfitability:")
            print(f"  ROE: {r.return_on_equity*100:.2f}%" if r.return_on_equity else "  ROE: N/A")
            print(f"  ROA: {r.return_on_assets*100:.2f}%" if r.return_on_assets else "  ROA: N/A")
            print(f"\nFinancial Health:")
            print(f"  Debt/Equity: {r.debt_to_equity:.2f}" if r.debt_to_equity is not None else "  Debt/Equity: N/A")
            print(f"  Current Ratio: {r.current:.2f}" if r.current else "  Current Ratio: N/A")
            print(f"  Quick Ratio: {r.quick:.2f}" if r.quick else "  Quick Ratio: N/A")
        else:
            print(f"No data available for {ticker}")


def demo_screening():
    """Demo: Screen stocks using pre-defined criteria"""
    print("\n" + "="*80)
    print("DEMO 2: Fundamental Stock Screening")
    print("="*80)
    
    screener = FundamentalScreener()
    
    # Show available presets
    print("\nAvailable Screening Presets:")
    for preset in screener.get_available_presets():
        print(f"  - {preset['key']}: {preset['name']}")
        print(f"    {preset['description']}")
    
    # Screen stocks with different presets
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "BAC", "JNJ", "PFE", "NVDA"]
    
    presets_to_test = ["quality_stocks", "value_stocks", "buffett_style"]
    
    for preset_name in presets_to_test:
        print(f"\n--- Screening with '{preset_name}' ---")
        results = screener.screen_with_preset(test_tickers, preset_name, min_score=50.0)
        
        print(f"Stocks that passed (min score 50%):")
        for result in results[:5]:  # Top 5
            print(f"  {result.ticker}: Score {result.score:.1f}% - "
                  f"P/E={result.ratios.price_to_earnings:.1f if result.ratios.price_to_earnings else 'N/A'}, "
                  f"ROE={result.ratios.return_on_equity*100:.1f if result.ratios.return_on_equity else 0:.1f}%")
        
        if not results:
            print("  No stocks passed the screening criteria")


def demo_health_scores():
    """Demo: Calculate financial health scores"""
    print("\n" + "="*80)
    print("DEMO 3: Financial Health Score Analysis")
    print("="*80)
    
    client = PolygonFinancialsClient()
    screener = FundamentalScreener()
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "JPM"]
    
    health_scores = []
    
    for ticker in test_tickers:
        ratios_list = client.get_ratios(ticker, limit=1)
        if ratios_list:
            health_score = screener.calculate_financial_health_score(ratios_list[0])
            health_scores.append({
                "ticker": ticker,
                "score": health_score
            })
    
    # Sort by overall score
    health_scores.sort(key=lambda x: x["score"]["overall_score"], reverse=True)
    
    print("\nFinancial Health Rankings:")
    print(f"{'Rank':<6} {'Ticker':<8} {'Score':<8} {'Rating':<15} {'Components'}")
    print("-" * 80)
    
    for i, item in enumerate(health_scores, 1):
        score = item["score"]
        components = ", ".join([f"{k}:{v}" for k, v in score["component_scores"].items()])
        print(f"{i:<6} {item['ticker']:<8} {score['percentage']:.0f}/100  {score['rating']:<15} {components[:40]}")


def demo_stock_comparison():
    """Demo: Compare multiple stocks"""
    print("\n" + "="*80)
    print("DEMO 4: Stock Comparison")
    print("="*80)
    
    analyzer = FundamentalAIAnalyzer()
    
    # Compare tech stocks
    print("\n--- Tech Stock Comparison ---")
    tech_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    comparison_df = analyzer.compare_stocks(tech_stocks)
    
    if not comparison_df.empty:
        print(comparison_df.to_string(index=False))
    
    # Compare financial stocks
    print("\n--- Financial Stock Comparison ---")
    financial_stocks = ["JPM", "BAC", "WFC", "GS", "MS"]
    comparison_df = analyzer.compare_stocks(financial_stocks)
    
    if not comparison_df.empty:
        print(comparison_df.to_string(index=False))


def demo_ai_integration():
    """Demo: AI-enhanced fundamental analysis"""
    print("\n" + "="*80)
    print("DEMO 5: AI-Enhanced Fundamental Analysis")
    print("="*80)
    
    analyzer = FundamentalAIAnalyzer()
    
    ticker = "AAPL"
    print(f"\n--- Fundamental Context for {ticker} ---")
    
    context = analyzer.get_fundamental_context(ticker)
    
    if context.get("has_data"):
        print(f"\nValuation Metrics:")
        val = context.get("valuation", {})
        print(f"  P/E Ratio: {val.get('pe_ratio', 'N/A')}")
        print(f"  P/B Ratio: {val.get('pb_ratio', 'N/A')}")
        print(f"  EV/EBITDA: {val.get('ev_to_ebitda', 'N/A')}")
        
        print(f"\nProfitability:")
        prof = context.get("profitability", {})
        print(f"  ROE: {prof.get('roe', 0)*100:.2f}%")
        print(f"  ROA: {prof.get('roa', 0)*100:.2f}%")
        
        print(f"\nFinancial Health:")
        health = context.get("financial_health", {})
        print(f"  Debt/Equity: {health.get('debt_to_equity', 'N/A')}")
        print(f"  Current Ratio: {health.get('current_ratio', 'N/A')}")
        
        print(f"\nOverall Health Score:")
        score = context.get("health_score", {})
        print(f"  Score: {score.get('percentage', 0):.0f}/100")
        print(f"  Rating: {score.get('rating', 'N/A')}")
        
        print(f"\n--- Sample LLM Prompt (first 800 characters) ---")
        prompt = analyzer.build_llm_prompt_with_fundamentals(ticker, 175.0)
        print(prompt[:800] + "...\n")
    else:
        print(f"No fundamental data available for {ticker}")


def demo_comprehensive_analysis():
    """Demo: Complete fundamental analysis workflow"""
    print("\n" + "="*80)
    print("DEMO 6: Comprehensive Fundamental Analysis Workflow")
    print("="*80)
    
    ticker = "MSFT"
    print(f"\nAnalyzing {ticker}...")
    
    # Step 1: Get ratios
    client = PolygonFinancialsClient()
    ratios_list = client.get_ratios(ticker, limit=1)
    
    if not ratios_list:
        print(f"No data available for {ticker}")
        return
    
    ratios = ratios_list[0]
    
    # Step 2: Calculate health score
    screener = FundamentalScreener()
    health_score = screener.calculate_financial_health_score(ratios)
    
    # Step 3: Screen against multiple presets
    print(f"\n--- Screening Results ---")
    presets = ["quality_stocks", "growth_stocks", "buffett_style"]
    
    for preset_name in presets:
        results = screener.screen_with_preset([ticker], preset_name, min_score=0)
        if results:
            result = results[0]
            print(f"{preset_name}: {result.score:.0f}% ({len(result.passed_criteria)}/{len(result.passed_criteria) + len(result.failed_criteria)} criteria)")
    
    # Step 4: Get financial statements
    print(f"\n--- Income Statement (TTM) ---")
    income_stmts = client.get_income_statements(ticker, timeframe="trailing_twelve_months", limit=1)
    if income_stmts:
        inc = income_stmts[0]
        print(f"Revenue: ${inc.revenue/1e9:.2f}B" if inc.revenue else "Revenue: N/A")
        print(f"Operating Income: ${inc.operating_income/1e9:.2f}B" if inc.operating_income else "Operating Income: N/A")
        print(f"Net Income: ${inc.net_income_loss_attributable_common_shareholders/1e9:.2f}B" if inc.net_income_loss_attributable_common_shareholders else "Net Income: N/A")
        print(f"EPS: ${inc.diluted_earnings_per_share:.2f}" if inc.diluted_earnings_per_share else "EPS: N/A")
    
    # Step 5: Summary
    print(f"\n--- Summary for {ticker} ---")
    print(f"Price: ${ratios.price:.2f}")
    print(f"Health Score: {health_score['percentage']:.0f}/100 ({health_score['rating']})")
    print(f"Investment Grade: {'✅ High Quality' if health_score['percentage'] >= 70 else '⚠️ Medium Quality' if health_score['percentage'] >= 50 else '❌ Low Quality'}")


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("POLYGON FINANCIALS API - COMPREHENSIVE DEMO")
    print("Demonstrating fundamental analysis capabilities")
    print("="*80)
    
    try:
        demo_financial_ratios()
        demo_screening()
        demo_health_scores()
        demo_stock_comparison()
        demo_ai_integration()
        demo_comprehensive_analysis()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✅ Financial ratios (valuation, profitability, liquidity)")
        print("✅ Pre-defined screening presets")
        print("✅ Financial health scoring")
        print("✅ Stock comparison")
        print("✅ AI-enhanced analysis with LLM prompts")
        print("✅ Comprehensive analysis workflow")
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

