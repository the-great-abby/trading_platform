#!/usr/bin/env python3
"""
Demo All Available Trading Strategies
====================================

This demo shows all available trading strategies in the system,
organized by category with examples and usage.
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List
from datetime import datetime

class AllStrategiesDemo:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_strategies_list(self) -> Dict[str, Any]:
        """Get list of all available strategies"""
        try:
            response = await self.client.get(f"{self.api_base_url}/strategies")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    async def test_strategy(self, symbol: str, strategy: str) -> Dict[str, Any]:
        """Test a single strategy"""
        payload = {
            "symbol": symbol,
            "include_ai_analysis": True,
            "include_news_sentiment": True,
            "include_risk_assessment": True,
            "strategies": [strategy]
        }
        
        try:
            response = await self.client.post(
                f"{self.api_base_url}/recommendations/stock",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"❌ Strategy test failed for {strategy}: {e}")
            return None
    
    def print_strategies_overview(self, strategies_data: Dict[str, Any]):
        """Print overview of all available strategies"""
        if not strategies_data or 'strategies' not in strategies_data:
            print("❌ No strategies data available")
            return
        
        strategies = strategies_data['strategies']
        
        print("\n" + "="*80)
        print("🚀 ALL AVAILABLE TRADING STRATEGIES")
        print("="*80)
        print(f"Total Strategies: {strategies_data.get('count', len(strategies))}")
        
        # Organize by category
        categories = {
            "Basic Technical Analysis": [],
            "Advanced Technical Analysis": [],
            "AI-Enhanced Strategies": [],
            "News & Sentiment": [],
            "Advanced Statistical": [],
            "Options Strategies": [],
            "Advanced Entry/Exit": [],
            "Portfolio & Multi-Strategy": []
        }
        
        for strategy in strategies:
            name = strategy['name']
            display_name = strategy['display_name']
            description = strategy['description']
            
            # Categorize strategies
            if 'ai_enhanced' in name or 'enhanced' in name:
                categories["AI-Enhanced Strategies"].append((name, display_name, description))
            elif 'news' in name or 'sentiment' in name:
                categories["News & Sentiment"].append((name, display_name, description))
            elif 'pairs' in name or 'vwap' in name or 'momentum' in name or 'ml_ensemble' in name or 'kalman' in name:
                categories["Advanced Statistical"].append((name, display_name, description))
            elif 'greeks' in name or 'iron_condor' in name or 'options' in name:
                categories["Options Strategies"].append((name, display_name, description))
            elif 'exit' in name or 'entry' in name or 'fibonacci' in name or 'trailing' in name:
                categories["Advanced Entry/Exit"].append((name, display_name, description))
            elif 'portfolio' in name or 'day_trading' in name:
                categories["Portfolio & Multi-Strategy"].append((name, display_name, description))
            elif 'ichimoku' in name or 'volatility' in name:
                categories["Advanced Technical Analysis"].append((name, display_name, description))
            else:
                categories["Basic Technical Analysis"].append((name, display_name, description))
        
        # Print each category
        for category, strategies_list in categories.items():
            if strategies_list:
                print(f"\n📊 {category.upper()}")
                print("-" * 50)
                for name, display_name, description in strategies_list:
                    print(f"   • {display_name} ({name})")
                    print(f"     {description}")
                    print()
    
    async def demo_basic_strategies(self, symbol: str):
        """Demo basic technical analysis strategies"""
        print(f"\n🎯 TESTING BASIC TECHNICAL ANALYSIS STRATEGIES")
        print("="*60)
        
        basic_strategies = [
            "rsi_strategy",
            "macd_strategy", 
            "bollinger_bands",
            "sma_crossover",
            "momentum_strategy",
            "mean_reversion_strategy"
        ]
        
        for strategy in basic_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
            else:
                print(f"   Result: No signal")
    
    async def demo_advanced_strategies(self, symbol: str):
        """Demo advanced technical analysis strategies"""
        print(f"\n🎯 TESTING ADVANCED TECHNICAL ANALYSIS STRATEGIES")
        print("="*60)
        
        advanced_strategies = [
            "ichimoku_strategy",
            "volatility_breakout_strategy",
            "vwap_strategy"
        ]
        
        for strategy in advanced_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
            else:
                print(f"   Result: No signal")
    
    async def demo_ai_enhanced_strategies(self, symbol: str):
        """Demo AI-enhanced strategies"""
        print(f"\n🎯 TESTING AI-ENHANCED STRATEGIES")
        print("="*60)
        
        ai_strategies = [
            "rsi_ai_enhanced_strategy",
            "macd_ai_enhanced_strategy",
            "bollinger_bands_ai_enhanced_strategy",
            "sma_crossover_ai_enhanced_strategy",
            "ichimoku_enhanced_strategy"
        ]
        
        for strategy in ai_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
                
                # Show AI analysis if available
                if result.get('ai_analysis'):
                    ai = result['ai_analysis']
                    print(f"   AI Sentiment: {ai.get('sentiment_score', 0):.3f}")
                    print(f"   AI Confidence: {ai.get('confidence', 0):.1%}")
            else:
                print(f"   Result: No signal")
    
    async def demo_news_sentiment_strategies(self, symbol: str):
        """Demo news and sentiment strategies"""
        print(f"\n🎯 TESTING NEWS & SENTIMENT STRATEGIES")
        print("="*60)
        
        news_strategies = [
            "news_enhanced",
            "social_media_sentiment_strategy"
        ]
        
        for strategy in news_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
                
                # Show news sentiment if available
                if result.get('news_sentiment'):
                    news = result['news_sentiment']
                    print(f"   News Sentiment: {news.get('sentiment_score', 0):.3f}")
                    print(f"   News Count: {news.get('news_count', 0)}")
            else:
                print(f"   Result: No signal")
    
    async def demo_advanced_statistical_strategies(self, symbol: str):
        """Demo advanced statistical strategies"""
        print(f"\n🎯 TESTING ADVANCED STATISTICAL STRATEGIES")
        print("="*60)
        
        statistical_strategies = [
            "pairs_trading_strategy",
            "cross_sectional_momentum_strategy",
            "ml_ensemble_strategy",
            "kalman_filter_strategy"
        ]
        
        for strategy in statistical_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
            else:
                print(f"   Result: No signal")
    
    async def demo_options_strategies(self, symbol: str):
        """Demo options strategies"""
        print(f"\n🎯 TESTING OPTIONS STRATEGIES")
        print("="*60)
        
        options_strategies = [
            "greeks_enhanced_strategy",
            "iron_condor_strategy"
        ]
        
        for strategy in options_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
            else:
                print(f"   Result: No signal")
    
    async def demo_portfolio_strategies(self, symbol: str):
        """Demo portfolio and multi-strategy approaches"""
        print(f"\n🎯 TESTING PORTFOLIO & MULTI-STRATEGY APPROACHES")
        print("="*60)
        
        portfolio_strategies = [
            "portfolio_strategy",
            "enhanced_day_trading_strategy"
        ]
        
        for strategy in portfolio_strategies:
            print(f"\n📊 Testing {strategy}...")
            result = await self.test_strategy(symbol, strategy)
            
            if result:
                action = result['overall_recommendation']
                confidence = result['confidence']
                print(f"   Result: {action} (Confidence: {confidence:.1%})")
            else:
                print(f"   Result: No signal")
    
    async def demo_strategy_combinations(self, symbol: str):
        """Demo strategy combinations"""
        print(f"\n🎯 TESTING STRATEGY COMBINATIONS")
        print("="*60)
        
        combinations = [
            {
                "name": "Trend Following Combo",
                "strategies": ["ichimoku_strategy", "macd_strategy", "sma_crossover"]
            },
            {
                "name": "Mean Reversion Combo", 
                "strategies": ["rsi_strategy", "bollinger_bands", "mean_reversion_strategy"]
            },
            {
                "name": "AI Enhanced Combo",
                "strategies": ["rsi_ai_enhanced_strategy", "macd_ai_enhanced_strategy", "news_enhanced"]
            },
            {
                "name": "Conservative Combo",
                "strategies": ["bollinger_bands", "rsi_strategy"]
            }
        ]
        
        for combo in combinations:
            print(f"\n📊 Testing {combo['name']}...")
            
            payload = {
                "symbol": symbol,
                "include_ai_analysis": True,
                "include_news_sentiment": True,
                "include_risk_assessment": True,
                "strategies": combo['strategies']
            }
            
            try:
                response = await self.client.post(
                    f"{self.api_base_url}/recommendations/stock",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    action = result['overall_recommendation']
                    confidence = result['confidence']
                    print(f"   Result: {action} (Confidence: {confidence:.1%})")
                    
                    # Show strategy breakdown
                    if result.get('strategies_analysis'):
                        print(f"   Strategy Breakdown:")
                        for strategy in result['strategies_analysis']:
                            strategy_name = strategy['strategy_name']
                            strategy_signal = strategy['signal']
                            strategy_confidence = strategy['confidence']
                            print(f"     {strategy_name}: {strategy_signal} ({strategy_confidence:.1%})")
                else:
                    print(f"   Result: Error")
                    
            except Exception as e:
                print(f"   Result: Error - {e}")
    
    async def demo_performance_comparison(self, symbols: List[str]):
        """Demo performance comparison across strategies"""
        print(f"\n🎯 PERFORMANCE COMPARISON ACROSS STRATEGIES")
        print("="*60)
        
        test_strategies = [
            "rsi_strategy",
            "macd_strategy", 
            "bollinger_bands",
            "ichimoku_strategy",
            "news_enhanced"
        ]
        
        results = {}
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol}...")
            symbol_results = {}
            
            for strategy in test_strategies:
                result = await self.test_strategy(symbol, strategy)
                
                if result:
                    action = result['overall_recommendation']
                    confidence = result['confidence']
                    symbol_results[strategy] = {
                        'action': action,
                        'confidence': confidence
                    }
                else:
                    symbol_results[strategy] = {
                        'action': 'NO_SIGNAL',
                        'confidence': 0.0
                    }
            
            results[symbol] = symbol_results
        
        # Print comparison table
        print(f"\n📈 STRATEGY PERFORMANCE COMPARISON")
        print("-" * 80)
        print(f"{'Symbol':<10} {'RSI':<15} {'MACD':<15} {'Bollinger':<15} {'Ichimoku':<15} {'News':<15}")
        print("-" * 80)
        
        for symbol, symbol_results in results.items():
            rsi = symbol_results.get('rsi_strategy', {})
            macd = symbol_results.get('macd_strategy', {})
            bollinger = symbol_results.get('bollinger_bands', {})
            ichimoku = symbol_results.get('ichimoku_strategy', {})
            news = symbol_results.get('news_enhanced', {})
            
            print(f"{symbol:<10} {rsi.get('action', 'N/A'):<15} {macd.get('action', 'N/A'):<15} "
                  f"{bollinger.get('action', 'N/A'):<15} {ichimoku.get('action', 'N/A'):<15} "
                  f"{news.get('action', 'N/A'):<15}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main demo function"""
    print("🚀 All Trading Strategies Demo")
    print("="*50)
    
    # Initialize demo
    demo = AllStrategiesDemo()
    
    try:
        # 1. Get and display all available strategies
        strategies_data = await demo.get_strategies_list()
        demo.print_strategies_overview(strategies_data)
        
        # 2. Demo different strategy categories
        await demo.demo_basic_strategies("AAPL")
        await demo.demo_advanced_strategies("GOOGL")
        await demo.demo_ai_enhanced_strategies("MSFT")
        await demo.demo_news_sentiment_strategies("TSLA")
        await demo.demo_advanced_statistical_strategies("AMZN")
        await demo.demo_options_strategies("SPY")
        await demo.demo_portfolio_strategies("NVDA")
        
        # 3. Demo strategy combinations
        await demo.demo_strategy_combinations("AAPL")
        
        # 4. Demo performance comparison
        await demo.demo_performance_comparison(["AAPL", "GOOGL", "MSFT", "TSLA"])
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        await demo.close()

if __name__ == "__main__":
    asyncio.run(main()) 