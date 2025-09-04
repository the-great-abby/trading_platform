#!/usr/bin/env python3
"""
Stock Recommendation CLI Tool
============================

A simple command-line interface for getting stock recommendations.
Usage: python stock_recommendation_cli.py <symbol> [options]
"""

import asyncio
import argparse
import sys
import json
from typing import Dict, Any, Optional
from demo_stock_recommendations import StockRecommendationDemo

def print_usage():
    """Print usage information"""
    print("""
🎯 Stock Recommendation CLI Tool

Usage:
  python stock_recommendation_cli.py <symbol> [options]

Examples:
  python stock_recommendation_cli.py AAPL
  python stock_recommendation_cli.py GOOGL --no-ai
  python stock_recommendation_cli.py MSFT --risk-only
  python stock_recommendation_cli.py TSLA --strategies rsi_strategy,macd_strategy
  python stock_recommendation_cli.py AAPL --strategies ichimoku_strategy

Options:
  --no-ai              Exclude AI analysis
  --no-news            Exclude news sentiment analysis
  --no-risk            Exclude risk assessment
  --risk-only          Only include risk assessment
  --strategies <list>  Comma-separated list of strategies to use
  --format <format>    Output format: text, json, or summary
  --api-url <url>      API base URL (default: http://localhost:8000)
  --help               Show this help message
""")

async def get_recommendation(symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Get stock recommendation"""
    demo = StockRecommendationDemo(kwargs.get('api_url', 'http://localhost:8000'))
    
    try:
        recommendation = await demo.get_stock_recommendation(symbol, **kwargs)
        await demo.close()
        return recommendation
    except Exception as e:
        print(f"❌ Error getting recommendation: {e}")
        await demo.close()
        return None

def print_summary(recommendation: Dict[str, Any]):
    """Print a summary of the recommendation"""
    if not recommendation:
        print("❌ No recommendation available")
        return
    
    symbol = recommendation['symbol']
    action = recommendation['overall_recommendation']
    confidence = recommendation['confidence']
    current_price = recommendation['current_price']
    
    print(f"\n📊 {symbol} Recommendation Summary")
    print(f"   Action: {action}")
    print(f"   Confidence: {confidence:.1%}")
    print(f"   Current Price: ${current_price:.2f}")
    
    if recommendation.get('target_price'):
        print(f"   Target: ${recommendation['target_price']:.2f}")
    if recommendation.get('stop_loss'):
        print(f"   Stop Loss: ${recommendation['stop_loss']:.2f}")
    
    print(f"   Risk Level: {recommendation['risk_level']}")
    print(f"   Position Size: {recommendation['position_size_recommendation']}")

def print_json(recommendation: Dict[str, Any]):
    """Print recommendation as JSON"""
    if recommendation:
        print(json.dumps(recommendation, indent=2))
    else:
        print(json.dumps({"error": "No recommendation available"}))

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Get stock recommendations from the trading system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL
  %(prog)s GOOGL --no-ai
  %(prog)s MSFT --risk-only
  %(prog)s TSLA --strategies rsi_strategy,macd_strategy
        """
    )
    
    parser.add_argument("symbol", help="Stock symbol (e.g., AAPL, GOOGL)")
    parser.add_argument("--no-ai", action="store_true", help="Exclude AI analysis")
    parser.add_argument("--no-news", action="store_true", help="Exclude news sentiment analysis")
    parser.add_argument("--no-risk", action="store_true", help="Exclude risk assessment")
    parser.add_argument("--risk-only", action="store_true", help="Only include risk assessment")
    parser.add_argument("--strategies", help="Comma-separated list of strategies to use")
    parser.add_argument("--format", choices=["text", "json", "summary"], default="text", 
                       help="Output format (default: text)")
    parser.add_argument("--api-url", default="http://localhost:8000", 
                       help="API base URL (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    # Prepare request parameters
    params = {
        "include_ai_analysis": not args.no_ai,
        "include_news_sentiment": not args.no_news,
        "include_risk_assessment": not args.no_risk,
        "api_url": args.api_url
    }
    
    # Handle risk-only mode
    if args.risk_only:
        params["include_ai_analysis"] = False
        params["include_news_sentiment"] = False
        params["include_risk_assessment"] = True
    
    # Handle specific strategies
    if args.strategies:
        params["strategies"] = [s.strip() for s in args.strategies.split(",")]
    
    # Get recommendation
    print(f"🔍 Getting recommendation for {args.symbol}...")
    recommendation = await get_recommendation(args.symbol, **params)
    
    # Print in requested format
    if args.format == "json":
        print_json(recommendation)
    elif args.format == "summary":
        print_summary(recommendation)
    else:  # text format
        if recommendation:
            demo = StockRecommendationDemo(args.api_url)
            demo.print_recommendation(recommendation)
        else:
            print("❌ No recommendation available")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_usage()
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 