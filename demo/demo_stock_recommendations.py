#!/usr/bin/env python3
"""
Demo: Stock Recommendations API
==============================

This demo shows how to use the new stock recommendation API to get comprehensive
buy/sell signals with exit strategies, AI analysis, and risk assessment.

The API provides:
- Multi-strategy analysis (RSI, MACD, Bollinger Bands, etc.)
- AI-powered market analysis using Ollama
- News sentiment analysis
- Risk assessment and position sizing
- Entry/exit recommendations with stop-loss and take-profit levels
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

class StockRecommendationDemo:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Check if we're running in Kubernetes
        self.is_kubernetes = os.getenv("KUBERNETES_SERVICE_HOST") is not None
        
        # Auto-detect Kubernetes service URL if running in cluster
        if self.is_kubernetes and api_base_url == "http://localhost:8000":
            self.api_base_url = "http://strategy-service:80"
            print("🔍 Detected Kubernetes environment, using internal service URL")
    
    async def get_stock_recommendation(self, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get comprehensive stock recommendation"""
        
        # Prepare request payload
        payload = {
            "symbol": symbol,
            "include_ai_analysis": kwargs.get("include_ai_analysis", True),
            "include_news_sentiment": kwargs.get("include_news_sentiment", True),
            "include_risk_assessment": kwargs.get("include_risk_assessment", True),
            "strategies": kwargs.get("strategies", None)  # Use all strategies if None
        }
        
        try:
            response = await self.client.post(
                f"{self.api_base_url}/recommendations/stock",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    async def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get list of available strategies"""
        try:
            response = await self.client.get(f"{self.api_base_url}/strategies")
            if response.status_code == 200:
                return response.json()["strategies"]
            else:
                print(f"❌ Error getting strategies: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Failed to get strategies: {e}")
            return []
    
    def print_recommendation(self, recommendation: Optional[Dict[str, Any]]):
        """Pretty print the recommendation"""
        if not recommendation:
            print("❌ No recommendation available")
            return
        
        print("\n" + "="*80)
        print(f"📊 STOCK RECOMMENDATION: {recommendation['symbol']}")
        print("="*80)
        
        # Overall recommendation
        action = recommendation['overall_recommendation']
        confidence = recommendation['confidence']
        current_price = recommendation['current_price']
        
        print(f"\n🎯 OVERALL RECOMMENDATION:")
        print(f"   Action: {action}")
        print(f"   Confidence: {confidence:.1%}")
        print(f"   Current Price: ${current_price:.2f}")
        
        # Price targets
        if recommendation.get('target_price'):
            print(f"   Target Price: ${recommendation['target_price']:.2f}")
        if recommendation.get('stop_loss'):
            print(f"   Stop Loss: ${recommendation['stop_loss']:.2f}")
        if recommendation.get('take_profit'):
            print(f"   Take Profit: ${recommendation['take_profit']:.2f}")
        
        # Risk and position sizing
        print(f"\n⚠️  RISK ASSESSMENT:")
        print(f"   Risk Level: {recommendation['risk_level']}")
        print(f"   Position Size: {recommendation['position_size_recommendation']}")
        
        # Reasoning
        print(f"\n💡 REASONING:")
        print(f"   {recommendation['reasoning']}")
        
        # Strategy analysis
        if recommendation.get('strategies_analysis'):
            print(f"\n📈 STRATEGY ANALYSIS:")
            for strategy in recommendation['strategies_analysis']:
                print(f"   • {strategy['strategy_name']}: {strategy['signal']} "
                      f"(confidence: {strategy['confidence']:.1%})")
        
        # AI analysis
        if recommendation.get('ai_analysis'):
            ai = recommendation['ai_analysis']
            print(f"\n🤖 AI ANALYSIS:")
            print(f"   Sentiment: {ai.get('sentiment_score', 0):.2f}")
            print(f"   Confidence: {ai.get('confidence', 0):.1%}")
            print(f"   Risk Assessment: {ai.get('risk_assessment', 'N/A')}")
            print(f"   Market Impact: {ai.get('market_impact', 'N/A')}")
            print(f"   Reasoning: {ai.get('reasoning', 'N/A')}")
        
        # News sentiment
        if recommendation.get('news_sentiment'):
            news = recommendation['news_sentiment']
            print(f"\n📰 NEWS SENTIMENT:")
            print(f"   Sentiment: {news.get('sentiment_label', 'N/A')} "
                  f"({news.get('sentiment_score', 0):.2f})")
            print(f"   Confidence: {news.get('confidence', 0):.1%}")
            print(f"   Recent Events: {news.get('recent_events_count', 0)}")
            print(f"   Impact Score: {news.get('impact_score', 0):.2f}")
        
        # Risk assessment details
        if recommendation.get('risk_assessment'):
            risk = recommendation['risk_assessment']
            print(f"\n🔒 RISK ASSESSMENT DETAILS:")
            print(f"   Volatility Score: {risk.get('volatility_score', 0):.2f}")
            print(f"   Liquidity Score: {risk.get('liquidity_score', 0):.2f}")
            print(f"   Correlation Risk: {risk.get('correlation_risk', 0):.2f}")
            print(f"   Sector Risk: {risk.get('sector_risk', 0):.2f}")
            print(f"   Max Position Size: {risk.get('max_position_size', 'N/A')}")
            print(f"   Stop Loss: {risk.get('stop_loss_recommendation', 'N/A')}")
            print(f"   Take Profit: {risk.get('take_profit_recommendation', 'N/A')}")
        
        print(f"\n⏰ Generated: {recommendation['timestamp']}")
        print("="*80)
    
    async def demo_single_stock(self, symbol: str):
        """Demo for a single stock"""
        print(f"\n🚀 Getting recommendation for {symbol}...")
        
        recommendation = await self.get_stock_recommendation(symbol)
        self.print_recommendation(recommendation)
    
    async def demo_multiple_stocks(self, symbols: List[str]):
        """Demo for multiple stocks"""
        print(f"\n🚀 Getting recommendations for multiple stocks...")
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol}...")
            recommendation = await self.get_stock_recommendation(symbol)
            self.print_recommendation(recommendation)
            await asyncio.sleep(1)  # Small delay between requests
    
    async def demo_strategy_comparison(self, symbol: str):
        """Demo comparing different strategies"""
        print(f"\n🔍 Comparing strategies for {symbol}...")
        
        # Get available strategies
        strategies = await self.get_available_strategies()
        strategy_names = [s['name'] for s in strategies[:3]]  # Test first 3 strategies
        
        for strategy_name in strategy_names:
            print(f"\n📈 Testing {strategy_name} strategy...")
            recommendation = await self.get_stock_recommendation(
                symbol, 
                strategies=[strategy_name]
            )
            if recommendation:
                print(f"   Result: {recommendation['overall_recommendation']} "
                      f"(confidence: {recommendation['confidence']:.1%})")
    
    async def demo_without_ai(self, symbol: str):
        """Demo without AI analysis"""
        print(f"\n🧮 Getting recommendation without AI analysis for {symbol}...")
        
        recommendation = await self.get_stock_recommendation(
            symbol,
            include_ai_analysis=False
        )
        self.print_recommendation(recommendation)
    
    async def demo_risk_focused(self, symbol: str):
        """Demo focused on risk assessment"""
        print(f"\n⚠️  Getting risk-focused recommendation for {symbol}...")
        
        recommendation = await self.get_stock_recommendation(
            symbol,
            include_ai_analysis=False,
            include_news_sentiment=False,
            include_risk_assessment=True
        )
        self.print_recommendation(recommendation)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main demo function"""
    print("🎯 Stock Recommendations API Demo")
    print("="*50)
    
    # Initialize demo
    demo = StockRecommendationDemo()
    
    try:
        # Demo 1: Single stock recommendation
        await demo.demo_single_stock("AAPL")
        
        # Demo 2: Multiple stocks
        await demo.demo_multiple_stocks(["GOOGL", "MSFT", "TSLA"])
        
        # Demo 3: Strategy comparison
        await demo.demo_strategy_comparison("AAPL")
        
        # Demo 4: Without AI analysis
        await demo.demo_without_ai("GOOGL")
        
        # Demo 5: Risk-focused analysis
        await demo.demo_risk_focused("MSFT")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        await demo.close()

if __name__ == "__main__":
    asyncio.run(main()) 