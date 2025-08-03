#!/usr/bin/env python3
"""
Demo: LLM-Powered Stock Analysis with Vector Storage
This demonstrates how the AI service analyzes if it's a good time to buy a stock
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class LLMStockAnalyzer:
    """LLM-powered stock analysis using vector storage"""
    
    def __init__(self):
        self.vector_storage_url = "http://localhost:11006"  # Postgres vector storage
        self.llm_proxy_url = "http://localhost:12001"  # LLM proxy service
        
    async def analyze_stock_opportunity(self, symbol: str, current_price: float, 
                                      market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if it's a good time to buy a stock"""
        
        # Step 1: Vectorize current market data
        market_vector_id = await self._vectorize_market_data(symbol, market_data)
        
        # Step 2: Search for similar historical patterns
        similar_patterns = await self._search_similar_patterns(symbol, market_data)
        
        # Step 3: Search for relevant news and sentiment
        news_context = await self._search_news_context(symbol)
        
        # Step 4: Search for previous investment decisions
        decision_context = await self._search_decision_context(symbol)
        
        # Step 5: Generate AI analysis using LLM
        analysis = await self._generate_ai_analysis(
            symbol, current_price, market_data, 
            similar_patterns, news_context, decision_context
        )
        
        # Step 6: Vectorize the analysis for future reference
        analysis_vector_id = await self._vectorize_analysis(symbol, analysis)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "analysis": analysis,
            "recommendation": analysis.get("recommendation"),
            "confidence": analysis.get("confidence"),
            "reasoning": analysis.get("reasoning"),
            "risk_level": analysis.get("risk_level"),
            "similar_patterns": similar_patterns,
            "news_context": news_context,
            "decision_context": decision_context,
            "vector_ids": {
                "market_data": market_vector_id,
                "analysis": analysis_vector_id
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _vectorize_market_data(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Vectorize current market data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.vector_storage_url}/api/vectorize/market-data"
                payload = {
                    "symbol": symbol,
                    "market_data": market_data
                }
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("embedding_id")
        except Exception as e:
            print(f"Error vectorizing market data: {e}")
        return "market_data_fallback"
    
    async def _search_similar_patterns(self, symbol: str, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for similar historical market patterns"""
        try:
            async with aiohttp.ClientSession() as session:
                query = f"market data pattern for {symbol} with price {market_data.get('price')} and volume {market_data.get('volume')}"
                url = f"{self.vector_storage_url}/api/search/similar"
                params = {
                    "query": query,
                    "vector_type": "market_data",
                    "top_k": 3
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error searching similar patterns: {e}")
        return []
    
    async def _search_news_context(self, symbol: str) -> List[Dict[str, Any]]:
        """Search for relevant news and sentiment"""
        try:
            async with aiohttp.ClientSession() as session:
                query = f"news and sentiment about {symbol}"
                url = f"{self.vector_storage_url}/api/search/similar"
                params = {
                    "query": query,
                    "vector_type": "news",
                    "top_k": 5
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error searching news context: {e}")
        return []
    
    async def _search_decision_context(self, symbol: str) -> List[Dict[str, Any]]:
        """Search for previous investment decisions"""
        try:
            async with aiohttp.ClientSession() as session:
                query = f"investment decision for {symbol}"
                url = f"{self.vector_storage_url}/api/search/similar"
                params = {
                    "query": query,
                    "vector_type": "decision",
                    "top_k": 3
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error searching decision context: {e}")
        return []
    
    async def _generate_ai_analysis(self, symbol: str, current_price: float, 
                                  market_data: Dict[str, Any], similar_patterns: List[Dict[str, Any]],
                                  news_context: List[Dict[str, Any]], 
                                  decision_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI analysis using LLM"""
        
        # Prepare context for LLM
        context = self._prepare_llm_context(symbol, current_price, market_data, 
                                          similar_patterns, news_context, decision_context)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.llm_proxy_url}/api/chat"
                payload = {
                    "prompt": context,
                    "max_tokens": 500,
                    "temperature": 0.3,
                    "system_prompt": """You are an expert stock analyst. Analyze the given data and provide a clear recommendation on whether to buy, hold, or sell the stock. Include confidence level, reasoning, and risk assessment."""
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_llm_analysis(result.get("response", ""))
                    else:
                        return self._generate_fallback_analysis(symbol, current_price, market_data)
                        
        except Exception as e:
            print(f"Error generating AI analysis: {e}")
            return self._generate_fallback_analysis(symbol, current_price, market_data)
    
    def _prepare_llm_context(self, symbol: str, current_price: float, market_data: Dict[str, Any],
                            similar_patterns: List[Dict[str, Any]], news_context: List[Dict[str, Any]],
                            decision_context: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM analysis"""
        
        context = f"""
STOCK ANALYSIS REQUEST: {symbol}

CURRENT MARKET DATA:
- Price: ${current_price}
- Volume: {market_data.get('volume', 0):,}
- Change: {market_data.get('change_percent', 0):.2f}%
- Market Cap: {market_data.get('market_cap', 'N/A')}
- Technical Indicators: {market_data.get('technical_indicators', {})}

SIMILAR HISTORICAL PATTERNS:
"""
        
        for pattern in similar_patterns[:2]:
            context += f"- {pattern.get('content', '')}\n"
        
        context += "\nRECENT NEWS AND SENTIMENT:\n"
        for news in news_context[:3]:
            context += f"- {news.get('content', '')}\n"
        
        context += "\nPREVIOUS INVESTMENT DECISIONS:\n"
        for decision in decision_context[:2]:
            context += f"- {decision.get('content', '')}\n"
        
        context += f"""

Based on this data, analyze if it's a good time to buy {symbol} at ${current_price}. 
Provide:
1. Recommendation (BUY/HOLD/SELL)
2. Confidence level (1-10)
3. Detailed reasoning
4. Risk level (LOW/MEDIUM/HIGH)
5. Target price and stop loss if applicable
"""
        
        return context
    
    def _parse_llm_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        try:
            # Simple parsing - in production, use more sophisticated parsing
            lines = response.split('\n')
            analysis = {
                "recommendation": "HOLD",
                "confidence": 5,
                "reasoning": response,
                "risk_level": "MEDIUM",
                "target_price": None,
                "stop_loss": None
            }
            
            for line in lines:
                line = line.strip().lower()
                if "buy" in line and "sell" not in line:
                    analysis["recommendation"] = "BUY"
                elif "sell" in line:
                    analysis["recommendation"] = "SELL"
                elif "confidence" in line:
                    # Extract confidence number
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        analysis["confidence"] = min(10, max(1, int(numbers[0])))
                elif "risk" in line:
                    if "high" in line:
                        analysis["risk_level"] = "HIGH"
                    elif "low" in line:
                        analysis["risk_level"] = "LOW"
            
            return analysis
            
        except Exception as e:
            print(f"Error parsing LLM analysis: {e}")
            return self._generate_fallback_analysis("UNKNOWN", 0, {})
    
    def _generate_fallback_analysis(self, symbol: str, current_price: float, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when LLM fails"""
        return {
            "recommendation": "HOLD",
            "confidence": 3,
            "reasoning": f"Limited data available for {symbol}. Recommend holding until more information is available.",
            "risk_level": "MEDIUM",
            "target_price": current_price * 1.05,
            "stop_loss": current_price * 0.95
        }
    
    async def _vectorize_analysis(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """Vectorize the analysis for future reference"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.vector_storage_url}/api/vectorize/decision"
                payload = {
                    "symbol": symbol,
                    "action": analysis.get("recommendation", "HOLD"),
                    "confidence": analysis.get("confidence", 5),
                    "reasoning": analysis.get("reasoning", ""),
                    "risk_level": analysis.get("risk_level", "MEDIUM"),
                    "target_price": analysis.get("target_price"),
                    "stop_loss": analysis.get("stop_loss"),
                    "created_at": datetime.now().isoformat()
                }
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("embedding_id")
        except Exception as e:
            print(f"Error vectorizing analysis: {e}")
        return "analysis_fallback"

async def demo_stock_analysis():
    """Demo the LLM-powered stock analysis"""
    
    analyzer = LLMStockAnalyzer()
    
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
        }
    ]
    
    print("🤖 LLM-Powered Stock Analysis Demo")
    print("=" * 50)
    
    for stock in stocks_to_analyze:
        print(f"\n📊 Analyzing {stock['symbol']} at ${stock['current_price']}")
        print("-" * 40)
        
        try:
            analysis = await analyzer.analyze_stock_opportunity(
                stock['symbol'], 
                stock['current_price'], 
                stock['market_data']
            )
            
            print(f"🎯 Recommendation: {analysis['recommendation']}")
            print(f"📈 Confidence: {analysis['confidence']}/10")
            print(f"⚠️  Risk Level: {analysis['risk_level']}")
            print(f"💭 Reasoning: {analysis['reasoning'][:200]}...")
            
            if analysis.get('target_price'):
                print(f"🎯 Target Price: ${analysis['target_price']:.2f}")
            if analysis.get('stop_loss'):
                print(f"🛑 Stop Loss: ${analysis['stop_loss']:.2f}")
                
        except Exception as e:
            print(f"❌ Error analyzing {stock['symbol']}: {e}")
    
    print("\n✅ Demo completed! The AI service can now:")
    print("• Vectorize market data for pattern recognition")
    print("• Search similar historical patterns")
    print("• Analyze news sentiment and context")
    print("• Learn from previous investment decisions")
    print("• Provide AI-powered buy/sell recommendations")

if __name__ == "__main__":
    asyncio.run(demo_stock_analysis()) 