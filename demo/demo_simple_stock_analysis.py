#!/usr/bin/env python3
"""
Simple Demo: LLM-Powered Stock Analysis Concept
This demonstrates the AI service concept for analyzing if it's a good time to buy a stock
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any

class SimpleStockAnalyzer:
    """Simple LLM-powered stock analysis demonstration"""
    
    def __init__(self):
        # Use existing services that are running
        self.backtest_api_url = "http://localhost:11031"  # Backtest API
        self.health_dashboard_url = "http://localhost:11002"  # Health Dashboard
        
    async def analyze_stock_opportunity(self, symbol: str, current_price: float, 
                                      market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if it's a good time to buy a stock using available services"""
        
        print(f"🔍 Analyzing {symbol} at ${current_price}")
        
        # Step 1: Check if services are available
        services_status = await self._check_services()
        
        # Step 2: Simulate vector storage (concept demonstration)
        vector_analysis = await self._simulate_vector_analysis(symbol, market_data)
        
        # Step 3: Generate AI analysis using available data
        ai_analysis = await self._generate_ai_analysis(symbol, current_price, market_data)
        
        # Step 4: Create comprehensive analysis
        analysis = {
            "symbol": symbol,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "services_status": services_status,
            "vector_analysis": vector_analysis,
            "ai_analysis": ai_analysis,
            "recommendation": ai_analysis.get("recommendation", "HOLD"),
            "confidence": ai_analysis.get("confidence", 5),
            "reasoning": ai_analysis.get("reasoning", "Analysis in progress"),
            "risk_level": ai_analysis.get("risk_level", "MEDIUM"),
            "technical_indicators": market_data.get("technical_indicators", {}),
            "market_context": {
                "volume": market_data.get("volume", 0),
                "change_percent": market_data.get("change_percent", 0),
                "market_cap": market_data.get("market_cap", "N/A")
            }
        }
        
        return analysis
    
    async def _check_services(self) -> Dict[str, bool]:
        """Check which services are available"""
        services = {}
        
        # Check backtest API
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.backtest_api_url}/health"
                async with session.get(url, timeout=5) as response:
                    services["backtest_api"] = response.status == 200
        except:
            services["backtest_api"] = False
        
        # Check health dashboard
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.health_dashboard_url}/health"
                async with session.get(url, timeout=5) as response:
                    services["health_dashboard"] = response.status == 200
        except:
            services["health_dashboard"] = False
        
        return services
    
    async def _simulate_vector_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate vector storage analysis (concept demonstration)"""
        
        # Simulate finding similar patterns
        similar_patterns = [
            {
                "pattern": "Bullish momentum with high volume",
                "similarity": 0.85,
                "date": "2024-01-15",
                "outcome": "Price increased 15% over 30 days"
            },
            {
                "pattern": "RSI oversold with MACD crossover",
                "similarity": 0.78,
                "date": "2024-02-20",
                "outcome": "Price increased 8% over 14 days"
            }
        ]
        
        # Simulate news sentiment
        news_sentiment = {
            "overall_sentiment": "positive",
            "sentiment_score": 0.7,
            "recent_news": [
                "Strong earnings report",
                "New product launch announced",
                "Analyst upgrades rating"
            ]
        }
        
        return {
            "similar_patterns": similar_patterns,
            "news_sentiment": news_sentiment,
            "vector_storage_status": "simulated"
        }
    
    async def _generate_ai_analysis(self, symbol: str, current_price: float, 
                                  market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis based on available data"""
        
        # Analyze technical indicators
        technical_indicators = market_data.get("technical_indicators", {})
        rsi = technical_indicators.get("rsi", 50)
        macd = technical_indicators.get("macd", "neutral")
        sma_20 = technical_indicators.get("sma_20", current_price)
        sma_50 = technical_indicators.get("sma_50", current_price)
        
        # Simple analysis logic
        signals = []
        confidence = 5
        
        # RSI analysis
        if rsi < 30:
            signals.append("RSI indicates oversold conditions - potential buy signal")
            confidence += 2
        elif rsi > 70:
            signals.append("RSI indicates overbought conditions - potential sell signal")
            confidence -= 1
        
        # MACD analysis
        if macd == "positive":
            signals.append("MACD shows positive momentum")
            confidence += 1
        elif macd == "negative":
            signals.append("MACD shows negative momentum")
            confidence -= 1
        
        # Moving average analysis
        if current_price > sma_20 > sma_50:
            signals.append("Price above both moving averages - bullish trend")
            confidence += 2
        elif current_price < sma_20 < sma_50:
            signals.append("Price below both moving averages - bearish trend")
            confidence -= 2
        
        # Volume analysis
        volume = market_data.get("volume", 0)
        if volume > 50000000:  # High volume
            signals.append("High trading volume - strong market interest")
            confidence += 1
        
        # Determine recommendation
        if confidence >= 7:
            recommendation = "BUY"
        elif confidence <= 3:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        # Risk assessment
        if abs(current_price - sma_20) / sma_20 > 0.1:  # 10% deviation
            risk_level = "HIGH"
        elif abs(current_price - sma_20) / sma_20 > 0.05:  # 5% deviation
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        reasoning = f"""
Analysis for {symbol} at ${current_price}:

Technical Analysis:
- RSI: {rsi} ({'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral'})
- MACD: {macd}
- 20-day SMA: ${sma_20:.2f}
- 50-day SMA: ${sma_50:.2f}
- Volume: {volume:,}

Key Signals:
{chr(10).join(f"• {signal}" for signal in signals)}

Recommendation: {recommendation}
Confidence: {confidence}/10
Risk Level: {risk_level}
        """.strip()
        
        return {
            "recommendation": recommendation,
            "confidence": max(1, min(10, confidence)),
            "reasoning": reasoning,
            "risk_level": risk_level,
            "target_price": current_price * 1.05 if recommendation == "BUY" else current_price * 0.95,
            "stop_loss": current_price * 0.95 if recommendation == "BUY" else current_price * 1.05
        }

async def demo_stock_analysis():
    """Demo the LLM-powered stock analysis concept"""
    
    analyzer = SimpleStockAnalyzer()
    
    # Sample stock data
    stocks_to_analyze = [
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "market_data": {
                "price": 150.25,
                "volume": 45000000,
                "change_percent": 2.5,
                "market_cap": "2.5T",
                "technical_indicators": {
                    "rsi": 65,
                    "macd": "positive",
                    "sma_20": 148.50,
                    "sma_50": 145.75
                }
            }
        },
        {
            "symbol": "TSLA",
            "current_price": 245.80,
            "market_data": {
                "price": 245.80,
                "volume": 35000000,
                "change_percent": -1.2,
                "market_cap": "780B",
                "technical_indicators": {
                    "rsi": 45,
                    "macd": "negative",
                    "sma_20": 250.00,
                    "sma_50": 255.25
                }
            }
        },
        {
            "symbol": "NVDA",
            "current_price": 850.00,
            "market_data": {
                "price": 850.00,
                "volume": 55000000,
                "change_percent": 3.8,
                "market_cap": "2.1T",
                "technical_indicators": {
                    "rsi": 75,
                    "macd": "positive",
                    "sma_20": 820.00,
                    "sma_50": 780.00
                }
            }
        }
    ]
    
    print("🤖 LLM-Powered Stock Analysis Demo")
    print("=" * 50)
    print("This demonstrates the AI service concept for stock analysis")
    print("")
    
    for i, stock in enumerate(stocks_to_analyze, 1):
        print(f"📊 Analysis {i}: {stock['symbol']} at ${stock['current_price']}")
        print("-" * 50)
        
        try:
            analysis = await analyzer.analyze_stock_opportunity(
                stock['symbol'], 
                stock['current_price'], 
                stock['market_data']
            )
            
            print(f"🎯 Recommendation: {analysis['recommendation']}")
            print(f"📈 Confidence: {analysis['confidence']}/10")
            print(f"⚠️  Risk Level: {analysis['risk_level']}")
            print(f"💭 Reasoning:")
            print(analysis['reasoning'])
            
            if analysis.get('target_price'):
                print(f"🎯 Target Price: ${analysis['target_price']:.2f}")
            if analysis.get('stop_loss'):
                print(f"🛑 Stop Loss: ${analysis['stop_loss']:.2f}")
            
            print(f"📊 Services Status: {analysis['services_status']}")
            print()
                
        except Exception as e:
            print(f"❌ Error analyzing {stock['symbol']}: {e}")
            print()
    
    print("✅ Demo completed!")
    print("\n🚀 This demonstrates the LLM-powered AI service concept:")
    print("• Vector storage for pattern recognition")
    print("• Technical analysis with multiple indicators")
    print("• Risk assessment and confidence scoring")
    print("• Buy/sell recommendations with reasoning")
    print("• Target prices and stop losses")
    print("\n💡 To implement the full system:")
    print("• Deploy PostgreSQL with pgvector extension")
    print("• Set up LLM proxy service")
    print("• Integrate with real-time market data")
    print("• Add news sentiment analysis")
    print("• Implement machine learning models")

if __name__ == "__main__":
    asyncio.run(demo_stock_analysis()) 