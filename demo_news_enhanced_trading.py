#!/usr/bin/env python3
"""
Demo: News-Enhanced Trading Strategy
Shows how news signals trigger potential moves that are confirmed by technical indicators
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional

from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.core.types import TradeSignal
from src.services.news.news_scanner import NewsScanner
from src.services.ai.ollama_service import OllamaService
from src.utils.config import Config


class NewsEnhancedTradingDemo:
    """Demo class to show news-enhanced trading workflow"""
    
    def __init__(self):
        config = Config()
        self.news_scanner = NewsScanner(config=config)
        self.ollama_service = OllamaService()
        self.strategy = NewsEnhancedStrategy(
            technical_weight=0.6,
            news_weight=0.4,
            sentiment_threshold=0.3
        )
        
    async def run_demo(self):
        """Run the complete news-enhanced trading demo"""
        print("🚀 News-Enhanced Trading Strategy Demo")
        print("=" * 60)
        print("This demo shows how news signals trigger potential moves")
        print("that are then confirmed by technical indicators")
        print()
        
        # Step 1: Simulate news events
        await self._demo_news_events()
        
        # Step 2: Show technical confirmation
        await self._demo_technical_confirmation()
        
        # Step 3: Show combined signal generation
        await self._demo_combined_signals()
        
        # Step 4: Show trade execution logic
        await self._demo_trade_execution()
        
    async def _demo_news_events(self):
        """Demo news event detection and scoring"""
        print("📰 Step 1: News Event Detection")
        print("-" * 40)
        
        # Simulate news events
        news_events = [
            {
                'symbol': 'AAPL',
                'title': 'Apple Reports Strong Q4 Earnings, Beats Expectations',
                'sentiment': 0.85,
                'impact': 0.9,
                'timestamp': datetime.now() - timedelta(hours=1),
                'category': 'earnings'
            },
            {
                'symbol': 'TSLA',
                'title': 'Tesla Announces New Battery Technology Breakthrough',
                'sentiment': 0.75,
                'impact': 0.8,
                'timestamp': datetime.now() - timedelta(hours=2),
                'category': 'product_launch'
            },
            {
                'symbol': 'JPM',
                'title': 'Federal Reserve Signals Potential Rate Hike',
                'sentiment': -0.4,
                'impact': 0.7,
                'timestamp': datetime.now() - timedelta(hours=3),
                'category': 'regulatory'
            }
        ]
        
        for event in news_events:
            print(f"🔍 Detected: {event['title']}")
            print(f"   Symbol: {event['symbol']}")
            print(f"   Sentiment: {event['sentiment']:.2f} ({'🟢 Bullish' if event['sentiment'] > 0 else '🔴 Bearish'})")
            print(f"   Impact: {event['impact']:.2f} ({'High' if event['impact'] > 0.7 else 'Medium' if event['impact'] > 0.4 else 'Low'})")
            print(f"   Category: {event['category']}")
            print()
            
        print("✅ News events detected and scored")
        print()
        
    async def _demo_technical_confirmation(self):
        """Demo technical indicator confirmation"""
        print("📊 Step 2: Technical Indicator Confirmation")
        print("-" * 40)
        
        # Generate mock price data
        symbols = ['AAPL', 'TSLA', 'JPM']
        
        for symbol in symbols:
            print(f"🔍 Analyzing {symbol} technical indicators...")
            
            # Generate mock data with trend
            dates = pd.date_range(start='2025-01-01', end='2025-07-02', freq='D')
            np.random.seed(hash(symbol) % 1000)  # Consistent data per symbol
            
            # Create trend based on symbol
            if symbol == 'AAPL':
                trend = 0.001  # Slight uptrend
            elif symbol == 'TSLA':
                trend = 0.002  # Stronger uptrend
            else:  # JPM
                trend = -0.0005  # Slight downtrend
                
            prices = [100.0]
            for i in range(1, len(dates)):
                change = np.random.normal(trend, 0.02)
                prices.append(prices[-1] * (1 + change))
            
            data = pd.DataFrame({
                'Date': dates,
                'Close': prices,
                'Volume': np.random.randint(1000000, 5000000, len(dates))
            })
            
            # Calculate technical indicators
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # Get latest values
            current_price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   RSI: {rsi:.1f} ({'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral'})")
            print(f"   SMA 20: ${sma_20:.2f}")
            print(f"   SMA 50: ${sma_50:.2f}")
            
            # Determine technical signal
            technical_signals = []
            
            # RSI signal
            if rsi < 30:
                technical_signals.append("RSI: BUY (oversold)")
            elif rsi > 70:
                technical_signals.append("RSI: SELL (overbought)")
            else:
                technical_signals.append("RSI: HOLD (neutral)")
            
            # SMA crossover signal
            if sma_20 > sma_50:
                technical_signals.append("SMA: BUY (bullish crossover)")
            else:
                technical_signals.append("SMA: SELL (bearish crossover)")
            
            print(f"   Technical Signals: {', '.join(technical_signals)}")
            print()
            
        print("✅ Technical indicators calculated and analyzed")
        print()
        
    async def _demo_combined_signals(self):
        """Demo combined news + technical signal generation"""
        print("🎯 Step 3: Combined Signal Generation")
        print("-" * 40)
        
        # Simulate the decision process
        scenarios = [
            {
                'symbol': 'AAPL',
                'news_sentiment': 0.85,
                'news_impact': 0.9,
                'rsi': 25,
                'sma_signal': 'BUY',
                'description': 'Strong earnings news + oversold RSI + bullish SMA'
            },
            {
                'symbol': 'TSLA',
                'news_sentiment': 0.75,
                'news_impact': 0.8,
                'rsi': 45,
                'sma_signal': 'BUY',
                'description': 'Product breakthrough + neutral RSI + bullish SMA'
            },
            {
                'symbol': 'JPM',
                'news_sentiment': -0.4,
                'news_impact': 0.7,
                'rsi': 75,
                'sma_signal': 'SELL',
                'description': 'Rate hike concerns + overbought RSI + bearish SMA'
            }
        ]
        
        for scenario in scenarios:
            print(f"🔍 Analyzing {scenario['symbol']}...")
            print(f"   Scenario: {scenario['description']}")
            
            # Calculate combined confidence
            news_confidence = abs(scenario['news_sentiment']) * scenario['news_impact']
            technical_confidence = 0.7 if scenario['rsi'] < 30 or scenario['rsi'] > 70 else 0.5
            
            # Weight the signals
            combined_confidence = (news_confidence * 0.4) + (technical_confidence * 0.6)
            
            # Determine final signal
            if scenario['news_sentiment'] > 0 and scenario['sma_signal'] == 'BUY':
                final_signal = 'BUY'
                signal_strength = 'Strong' if combined_confidence > 0.7 else 'Moderate'
            elif scenario['news_sentiment'] < 0 and scenario['sma_signal'] == 'SELL':
                final_signal = 'SELL'
                signal_strength = 'Strong' if combined_confidence > 0.7 else 'Moderate'
            else:
                final_signal = 'HOLD'
                signal_strength = 'Weak'
            
            print(f"   News Confidence: {news_confidence:.2f}")
            print(f"   Technical Confidence: {technical_confidence:.2f}")
            print(f"   Combined Confidence: {combined_confidence:.2f}")
            print(f"   Final Signal: {final_signal} ({signal_strength})")
            print()
            
        print("✅ Combined signals generated")
        print()
        
    async def _demo_trade_execution(self):
        """Demo trade execution logic"""
        print("💰 Step 4: Trade Execution Logic")
        print("-" * 40)
        
        # Show how trades would be executed
        trades = [
            {
                'symbol': 'AAPL',
                'signal': 'BUY',
                'confidence': 0.82,
                'reason': 'Strong earnings news + oversold RSI + bullish SMA crossover',
                'entry_price': 148.25,
                'stop_loss': 142.50,
                'take_profit': 158.00,
                'position_size': 'Full position (high confidence)'
            },
            {
                'symbol': 'TSLA',
                'signal': 'BUY',
                'confidence': 0.68,
                'reason': 'Product breakthrough + neutral RSI + bullish SMA',
                'entry_price': 245.80,
                'stop_loss': 235.00,
                'take_profit': 265.00,
                'position_size': 'Half position (moderate confidence)'
            },
            {
                'symbol': 'JPM',
                'signal': 'SELL',
                'confidence': 0.74,
                'reason': 'Rate hike concerns + overbought RSI + bearish SMA',
                'entry_price': 185.40,
                'stop_loss': 192.00,
                'take_profit': 175.00,
                'position_size': 'Full position (high confidence)'
            }
        ]
        
        for trade in trades:
            print(f"🎯 {trade['symbol']} Trade Signal")
            print(f"   Signal: {trade['signal']}")
            print(f"   Confidence: {trade['confidence']:.2f}")
            print(f"   Reason: {trade['reason']}")
            print(f"   Entry Price: ${trade['entry_price']:.2f}")
            print(f"   Stop Loss: ${trade['stop_loss']:.2f}")
            print(f"   Take Profit: ${trade['take_profit']:.2f}")
            print(f"   Position Size: {trade['position_size']}")
            print()
            
        print("✅ Trade execution logic demonstrated")
        print()
        
        # Summary
        print("📋 Summary: News-Enhanced Trading Workflow")
        print("=" * 60)
        print("1. 📰 News events are detected and scored for sentiment/impact")
        print("2. 📊 Technical indicators confirm or contradict news signals")
        print("3. 🎯 Combined signals are generated with weighted confidence")
        print("4. 💰 Trades are executed based on signal strength and risk management")
        print()
        print("🎉 Demo Complete! This shows how news can trigger potential moves")
        print("that are then confirmed by technical analysis for higher confidence trades.")
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


async def main():
    """Main demo function"""
    demo = NewsEnhancedTradingDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main()) 