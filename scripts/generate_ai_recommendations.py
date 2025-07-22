#!/usr/bin/env python3
"""
Generate AI Trading Recommendations Report
Uses the AI Analysis Service to generate buy/sell recommendations
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backtesting.results.ai_recommendations_report import AIRecommendationsReportGenerator

# Configuration
AI_ANALYSIS_URL = os.getenv("AI_ANALYSIS_URL", "http://localhost:11085")
DEFAULT_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", 
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "NKE", "DIS",
    "JPM", "BAC", "WFC", "GS", "JNJ", "PFE", "UNH", "HD", "PG"
]

async def check_ai_service_health():
    """Check if AI analysis service is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{AI_ANALYSIS_URL}/health", timeout=10) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"❌ AI Analysis Service health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to AI Analysis Service: {e}")
        return False

async def run_batch_analysis(symbols: list, include_news: bool = True, include_technical: bool = True):
    """Run batch analysis on multiple symbols"""
    print(f"🤖 Starting batch analysis for {len(symbols)} symbols...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Start batch analysis
            batch_request = {
                "symbols": symbols,
                "include_news": include_news,
                "include_technical": include_technical,
                "include_sentiment": True
            }
            
            async with session.post(f"{AI_ANALYSIS_URL}/api/analyze/batch", json=batch_request) as response:
                if response.status == 200:
                    result = await response.json()
                    analysis_id = result.get("analysis_id")
                    print(f"✅ Batch analysis started: {analysis_id}")
                    return analysis_id
                else:
                    print(f"❌ Failed to start batch analysis: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Error starting batch analysis: {e}")
        return None

async def wait_for_analysis_completion(analysis_id: str, timeout: int = 300):
    """Wait for batch analysis to complete"""
    print(f"⏳ Waiting for analysis {analysis_id} to complete...")
    
    start_time = datetime.now()
    while (datetime.now() - start_time).seconds < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{AI_ANALYSIS_URL}/api/analysis/{analysis_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("recommendations"):
                            print(f"✅ Analysis completed in {(datetime.now() - start_time).seconds} seconds")
                            return result
                    elif response.status == 404:
                        print("⏳ Analysis still running...")
                    else:
                        print(f"⚠️ Unexpected response: {response.status}")
        except Exception as e:
            print(f"⚠️ Error checking analysis status: {e}")
        
        await asyncio.sleep(10)  # Check every 10 seconds
    
    print(f"❌ Analysis timed out after {timeout} seconds")
    return None

async def get_daily_recommendations():
    """Get daily recommendations if available"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{AI_ANALYSIS_URL}/api/recommendations/daily") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ No daily recommendations available: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Error getting daily recommendations: {e}")
        return None

def generate_report(analysis_data: dict, output_filename: str = None):
    """Generate HTML report from analysis data"""
    print("📊 Generating AI recommendations report...")
    
    generator = AIRecommendationsReportGenerator()
    
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"ai_recommendations_{timestamp}.html"
    
    try:
        report_path = generator.generate_recommendations_report(analysis_data, output_filename)
        print(f"✅ Report generated: {report_path}")
        return report_path
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None

async def main():
    parser = argparse.ArgumentParser(description="Generate AI Trading Recommendations Report")
    parser.add_argument("--symbols", nargs="+", help="List of symbols to analyze")
    parser.add_argument("--daily", action="store_true", help="Use daily recommendations")
    parser.add_argument("--output", help="Output filename for the report")
    parser.add_argument("--include-news", action="store_true", default=True, help="Include news sentiment analysis")
    parser.add_argument("--include-technical", action="store_true", default=True, help="Include technical analysis")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout for analysis completion (seconds)")
    
    args = parser.parse_args()
    
    # Check service health
    print("🔍 Checking AI Analysis Service health...")
    if not await check_ai_service_health():
        print("❌ AI Analysis Service is not available. Please start the service first.")
        print("   Run: make ai-analysis-deploy")
        sys.exit(1)
    
    print("✅ AI Analysis Service is healthy")
    
    analysis_data = None
    
    if args.daily:
        # Get daily recommendations
        print("📅 Getting daily recommendations...")
        analysis_data = await get_daily_recommendations()
        
        if not analysis_data:
            print("⚠️ No daily recommendations available, running new analysis...")
            args.daily = False
    
    if not args.daily:
        # Run new analysis
        symbols = args.symbols or DEFAULT_STOCKS
        print(f"📈 Analyzing {len(symbols)} symbols: {', '.join(symbols)}")
        
        # Start batch analysis
        analysis_id = await run_batch_analysis(
            symbols, 
            include_news=args.include_news,
            include_technical=args.include_technical
        )
        
        if not analysis_id:
            print("❌ Failed to start batch analysis")
            sys.exit(1)
        
        # Wait for completion
        analysis_data = await wait_for_analysis_completion(analysis_id, args.timeout)
        
        if not analysis_data:
            print("❌ Analysis failed or timed out")
            sys.exit(1)
    
    # Generate report
    if analysis_data:
        report_path = generate_report(analysis_data, args.output)
        if report_path:
            print(f"\n🎉 AI Recommendations Report Generated!")
            print(f"📄 Report: {report_path}")
            print(f"🌐 View online: http://localhost:8000/reports/{os.path.basename(report_path)}")
            print(f"📊 Summary:")
            
            summary = analysis_data.get("summary", {})
            print(f"   - Total analyzed: {summary.get('total_analyzed', 0)}")
            print(f"   - Buy signals: {summary.get('buy_recommendations', 0)}")
            print(f"   - Sell signals: {summary.get('sell_recommendations', 0)}")
            print(f"   - Hold signals: {summary.get('hold_recommendations', 0)}")
            print(f"   - Average confidence: {summary.get('average_confidence', 0):.1f}%")
            
            # Show top recommendations
            recommendations = analysis_data.get("recommendations", [])
            if recommendations:
                print(f"\n🏆 Top Recommendations:")
                sorted_recs = sorted(recommendations, key=lambda x: x.get("confidence", 0), reverse=True)
                for i, rec in enumerate(sorted_recs[:5]):
                    symbol = rec.get("symbol", "N/A")
                    action = rec.get("recommendation", "HOLD")
                    confidence = rec.get("confidence", 0)
                    price = rec.get("current_price", 0)
                    print(f"   {i+1}. {symbol}: {action} @ ${price:.2f} (Confidence: {confidence:.1f}%)")
        else:
            print("❌ Failed to generate report")
            sys.exit(1)
    else:
        print("❌ No analysis data available")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 