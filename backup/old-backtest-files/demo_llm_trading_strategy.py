#!/usr/bin/env python3
"""
Demo: How to Add LLM to Any Trading Strategy
Shows how to integrate Ollama AI with trading strategies
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.append('src')

from src.services.ai.ollama_service import OllamaService, AIAnalysis
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.core.types import TradeSignal


class LLMEnhancedStrategy:
    """Example of how to add LLM to any trading strategy"""
    
    def __init__(self, base_strategy, ai_weight: float = 0.4):
        self.base_strategy = base_strategy
        self.ai_weight = ai_weight
        self.ollama_service = None
        
    async def initialize_ai(self, ollama_url: str = None):
        """Initialize AI service"""
        if ollama_url is None:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        try:
            self.ollama_service = OllamaService(base_url=ollama_url)
            print(f"✅ AI service initialized for {self.base_strategy.name}")
            return True
        except Exception as e:
            print(f"⚠️  AI service not available: {e}")
            return False
    
    async def generate_enhanced_signal(self, symbol: str, data: pd.DataFrame) -> TradeSignal:
        """Generate AI-enhanced trading signal"""
        
        # Get base signal from original strategy
        base_signal = await self.base_strategy.generate_signal(symbol, data)
        
        if not base_signal:
            return None
        
        # Enhance with AI if available
        if self.ollama_service:
            enhanced_signal = await self._enhance_with_ai(symbol, base_signal, data)
            return enhanced_signal
        else:
            return base_signal
    
    async def _enhance_with_ai(self, symbol: str, base_signal: TradeSignal, data: pd.DataFrame) -> TradeSignal:
        """Enhance signal with AI analysis"""
        
        try:
            # Prepare market context
            market_context = {
                'symbol': symbol,
                'current_price': data['Close'].iloc[-1],
                'volume': data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000,
                'price_change_24h': (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0,
                'volatility': data['Close'].rolling(window=20).std().iloc[-1] / data['Close'].iloc[-1] if len(data) >= 20 else 0
            }
            
            # Prepare technical signals
            technical_signals = [{
                'indicator': base_signal.strategy,
                'signal': base_signal.action,
                'confidence': base_signal.confidence,
                'price': base_signal.price
            }]
            
            # Generate AI analysis
            ai_analysis = await self.ollama_service.analyze_market_sentiment(
                news_events=[],  # Could include news data
                technical_signals=technical_signals,
                market_data=market_context
            )
            
            # Combine signals
            enhanced_signal = await self._combine_signals(base_signal, ai_analysis)
            
            return enhanced_signal
            
        except Exception as e:
            print(f"Error enhancing signal with AI: {e}")
            return base_signal
    
    async def _combine_signals(self, base_signal: TradeSignal, ai_analysis: AIAnalysis) -> TradeSignal:
        """Combine technical and AI signals"""
        
        # Calculate combined confidence
        technical_confidence = base_signal.confidence
        ai_confidence = ai_analysis.confidence
        
        combined_confidence = (technical_confidence * (1 - self.ai_weight) + 
                              ai_confidence * self.ai_weight)
        
        # Adjust confidence based on AI sentiment
        if abs(ai_analysis.sentiment_score) > 0.3:
            if ai_analysis.sentiment_score > 0 and base_signal.action == "BUY":
                combined_confidence = min(combined_confidence * 1.2, 0.95)
            elif ai_analysis.sentiment_score < 0 and base_signal.action == "SELL":
                combined_confidence = min(combined_confidence * 1.2, 0.95)
            elif ai_analysis.sentiment_score < 0 and base_signal.action == "BUY":
                combined_confidence *= 0.8
            elif ai_analysis.sentiment_score > 0 and base_signal.action == "SELL":
                combined_confidence *= 0.8
        
        # Create enhanced signal
        enhanced_signal = TradeSignal(
            symbol=base_signal.symbol,
            action=base_signal.action,
            quantity=base_signal.quantity,
            price=base_signal.price,
            timestamp=base_signal.timestamp,
            strategy=f"{base_signal.strategy}_AI_Enhanced",
            confidence=combined_confidence,
            metadata={
                **base_signal.metadata,
                'ai_enhanced': True,
                'ai_sentiment': ai_analysis.sentiment_score,
                'ai_confidence': ai_confidence,
                'ai_reasoning': ai_analysis.reasoning,
                'ai_risk_assessment': ai_analysis.risk_assessment,
                'original_confidence': base_signal.confidence,
                'enhanced_confidence': combined_confidence
            }
        )
        
        return enhanced_signal


async def demo_llm_integration():
    """Demo LLM integration with trading strategies"""
    
    print("🧠 LLM Trading Strategy Integration Demo")
    print("=" * 50)
    
    # Create sample market data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Open': [100 + i * 0.1 + (i % 10) * 0.5 for i in range(len(dates))],
        'High': [100 + i * 0.1 + (i % 10) * 0.5 + 2 for i in range(len(dates))],
        'Low': [100 + i * 0.1 + (i % 10) * 0.5 - 2 for i in range(len(dates))],
        'Close': [100 + i * 0.1 + (i % 10) * 0.5 + 1 for i in range(len(dates))],
        'Volume': [1000000 + i * 1000 for i in range(len(dates))]
    })
    data.set_index('Date', inplace=True)
    
    print(f"📊 Sample data created: {len(data)} days")
    print(f"   Latest price: ${data['Close'].iloc[-1]:.2f}")
    
    # Example 1: Enhance RSI Strategy with AI
    print("\n🔍 Example 1: RSI Strategy + AI")
    print("-" * 30)
    
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    llm_rsi = LLMEnhancedStrategy(rsi_strategy, ai_weight=0.4)
    
    # Try to initialize AI (will fail if Ollama not running)
    ai_available = await llm_rsi.initialize_ai()
    
    # Generate signals
    base_signal = await rsi_strategy.generate_signal("AAPL", data)
    if base_signal:
        print(f"📈 Base RSI Signal: {base_signal.action} (confidence: {base_signal.confidence:.2f})")
        
        if ai_available:
            enhanced_signal = await llm_rsi.generate_enhanced_signal("AAPL", data)
            if enhanced_signal:
                print(f"🤖 AI-Enhanced Signal: {enhanced_signal.action} (confidence: {enhanced_signal.confidence:.2f})")
                print(f"   AI Sentiment: {enhanced_signal.metadata.get('ai_sentiment', 'N/A'):.2f}")
                print(f"   AI Reasoning: {enhanced_signal.metadata.get('ai_reasoning', 'N/A')[:100]}...")
                print(f"   Confidence Boost: {enhanced_signal.metadata.get('enhanced_confidence', 0) - base_signal.confidence:.2f}")
        else:
            print("⚠️  AI not available - using base signal only")
    else:
        print("❌ No RSI signal generated")
    
    # Example 2: News-Enhanced Strategy (already has AI)
    print("\n🔍 Example 2: News-Enhanced Strategy (Built-in AI)")
    print("-" * 50)
    
    news_strategy = NewsEnhancedStrategy(technical_weight=0.6, news_weight=0.4)
    
    # Initialize with AI
    await news_strategy.initialize()
    
    # Generate signal
    news_signal = await news_strategy.generate_signal("AAPL", data)
    if news_signal:
        print(f"📰 News-Enhanced Signal: {news_signal.action} (confidence: {news_signal.confidence:.2f})")
        if news_signal.metadata.get('ai_enhanced'):
            print(f"   ✅ AI-Enhanced: Yes")
            print(f"   🤖 AI Confidence: {news_signal.metadata.get('ai_confidence', 'N/A'):.2f}")
        else:
            print(f"   ⚠️  AI-Enhanced: No (using weighted analysis)")
    else:
        print("❌ No news-enhanced signal generated")
    
    # Example 3: Multi-Factor AI Signal Generation
    print("\n🔍 Example 3: Multi-Factor AI Signal Generation")
    print("-" * 45)
    
    if ai_available:
        try:
            # Prepare comprehensive market data
            market_context = {
                'current_price': data['Close'].iloc[-1],
                'volume': data['Volume'].iloc[-1],
                'price_change_24h': (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2],
                'volatility': data['Close'].rolling(window=20).std().iloc[-1] / data['Close'].iloc[-1]
            }
            
            technical_signals = [
                {'indicator': 'RSI', 'value': 35, 'signal': 'BUY', 'confidence': 0.8},
                {'indicator': 'MACD', 'value': 0.5, 'signal': 'BUY', 'confidence': 0.7},
                {'indicator': 'SMA', 'value': 105, 'signal': 'BUY', 'confidence': 0.6}
            ]
            
            # Generate multi-factor signal
            multi_signal = await llm_rsi.ollama_service.generate_multi_factor_signal(
                "AAPL", technical_signals, {}, market_context
            )
            
            if multi_signal:
                print(f"🎯 Multi-Factor AI Signal: {multi_signal.action}")
                print(f"   Confidence: {multi_signal.confidence:.2f}")
                print(f"   Risk Level: {multi_signal.metadata.get('risk_level', 'N/A')}")
                print(f"   Position Size: {multi_signal.metadata.get('position_size', 'N/A')}")
                print(f"   Stop Loss: {multi_signal.metadata.get('stop_loss', 'N/A')}")
                print(f"   Take Profit: {multi_signal.metadata.get('take_profit', 'N/A')}")
                print(f"   Reasoning: {multi_signal.metadata.get('reasoning', 'N/A')[:100]}...")
            else:
                print("❌ No multi-factor signal generated")
                
        except Exception as e:
            print(f"❌ Error generating multi-factor signal: {e}")
    else:
        print("⚠️  AI not available for multi-factor analysis")
    
    print("\n" + "=" * 50)
    print("✅ LLM Integration Demo Complete!")
    print("\n📋 Key Takeaways:")
    print("1. Any strategy can be enhanced with AI using the LLMEnhancedStrategy wrapper")
    print("2. The News-Enhanced Strategy already has built-in AI capabilities")
    print("3. AI can provide sentiment analysis, risk assessment, and confidence boosting")
    print("4. System gracefully falls back to base signals when AI is unavailable")
    print("5. Multi-factor analysis combines technical, news, and market context")


if __name__ == "__main__":
    asyncio.run(demo_llm_integration()) 