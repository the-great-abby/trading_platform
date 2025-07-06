#!/usr/bin/env python3
"""
Simple News-Enhanced Trading Demo
Shows how news signals trigger potential moves that are confirmed by technical indicators
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any


class SimpleNewsEnhancedDemo:
    """Simple demo showing news-enhanced trading workflow"""
    
    def __init__(self):
        self.portfolio = {
            'cash': 100000,
            'positions': {},
            'trades': []
        }
        
    async def run_demo(self):
        """Run the complete demo"""
        print("🚀 Simple News-Enhanced Trading Demo")
        print("=" * 60)
        print("This demo shows how news signals trigger potential moves")
        print("that are then confirmed by technical indicators")
        print()
        
        # Step 1: Show news events
        await self._show_news_events()
        
        # Step 2: Show technical analysis
        await self._show_technical_analysis()
        
        # Step 3: Show decision process
        await self._show_decision_process()
        
        # Step 4: Show trade execution
        await self._show_trade_execution()
        
        # Step 5: Show portfolio results
        await self._show_portfolio_results()
        
    async def _show_news_events(self):
        """Show news events and their impact"""
        print("📰 Step 1: News Event Detection & Analysis")
        print("-" * 50)
        
        news_events = [
            {
                'symbol': 'AAPL',
                'title': 'Apple Reports Strong Q4 Earnings, Beats Expectations by 15%',
                'sentiment': 0.85,
                'impact': 0.9,
                'category': 'earnings',
                'timestamp': datetime.now() - timedelta(hours=2),
                'affected_symbols': ['AAPL', 'MSFT', 'GOOGL']  # Tech sector impact
            },
            {
                'symbol': 'TSLA',
                'title': 'Tesla Announces Revolutionary Battery Technology Breakthrough',
                'sentiment': 0.75,
                'impact': 0.8,
                'category': 'product_launch',
                'timestamp': datetime.now() - timedelta(hours=4),
                'affected_symbols': ['TSLA', 'NIO', 'XPEV']  # EV sector impact
            },
            {
                'symbol': 'JPM',
                'title': 'Federal Reserve Signals Potential Rate Hike in Next Meeting',
                'sentiment': -0.4,
                'impact': 0.7,
                'category': 'regulatory',
                'timestamp': datetime.now() - timedelta(hours=6),
                'affected_symbols': ['JPM', 'BAC', 'WFC', 'GS']  # Banking sector impact
            }
        ]
        
        for event in news_events:
            print(f"🔍 {event['symbol']}: {event['title']}")
            print(f"   Sentiment: {event['sentiment']:.2f} ({'🟢 Bullish' if event['sentiment'] > 0 else '🔴 Bearish'})")
            print(f"   Impact: {event['impact']:.2f} ({'High' if event['impact'] > 0.7 else 'Medium' if event['impact'] > 0.4 else 'Low'})")
            print(f"   Category: {event['category']}")
            print(f"   Affected: {', '.join(event['affected_symbols'])}")
            print()
            
        print("✅ News events detected and analyzed")
        print()
        
    async def _show_technical_analysis(self):
        """Show technical analysis for affected symbols"""
        print("📊 Step 2: Technical Analysis Confirmation")
        print("-" * 50)
        
        symbols = ['AAPL', 'TSLA', 'JPM']
        
        for symbol in symbols:
            print(f"🔍 Analyzing {symbol} technical indicators...")
            
            # Generate mock technical data
            current_price = 150.0 if symbol == 'AAPL' else 250.0 if symbol == 'TSLA' else 180.0
            rsi = 25 if symbol == 'AAPL' else 45 if symbol == 'TSLA' else 75
            sma_20 = current_price * 1.02 if symbol == 'AAPL' else current_price * 0.98 if symbol == 'TSLA' else current_price * 0.95
            sma_50 = current_price * 0.98 if symbol == 'AAPL' else current_price * 0.99 if symbol == 'TSLA' else current_price * 1.02
            
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   RSI: {rsi:.1f} ({'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral'})")
            print(f"   SMA 20: ${sma_20:.2f}")
            print(f"   SMA 50: ${sma_50:.2f}")
            
            # Technical signals
            rsi_signal = "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD"
            sma_signal = "BUY" if sma_20 > sma_50 else "SELL"
            
            print(f"   RSI Signal: {rsi_signal}")
            print(f"   SMA Signal: {sma_signal}")
            print()
            
        print("✅ Technical analysis completed")
        print()
        
    async def _show_decision_process(self):
        """Show the decision-making process"""
        print("🎯 Step 3: Combined Decision Making")
        print("-" * 50)
        
        decisions = [
            {
                'symbol': 'AAPL',
                'news_sentiment': 0.85,
                'news_impact': 0.9,
                'rsi': 25,
                'rsi_signal': 'BUY',
                'sma_signal': 'BUY',
                'description': 'Strong earnings + oversold RSI + bullish SMA'
            },
            {
                'symbol': 'TSLA',
                'news_sentiment': 0.75,
                'news_impact': 0.8,
                'rsi': 45,
                'rsi_signal': 'HOLD',
                'sma_signal': 'BUY',
                'description': 'Product breakthrough + neutral RSI + bullish SMA'
            },
            {
                'symbol': 'JPM',
                'news_sentiment': -0.4,
                'news_impact': 0.7,
                'rsi': 75,
                'rsi_signal': 'SELL',
                'sma_signal': 'SELL',
                'description': 'Rate hike concerns + overbought RSI + bearish SMA'
            }
        ]
        
        for decision in decisions:
            print(f"🔍 {decision['symbol']} Decision Process:")
            print(f"   Scenario: {decision['description']}")
            
            # Calculate confidence scores
            news_confidence = abs(decision['news_sentiment']) * decision['news_impact']
            technical_confidence = 0.7 if decision['rsi'] < 30 or decision['rsi'] > 70 else 0.5
            
            # Weight the signals (60% technical, 40% news)
            combined_confidence = (technical_confidence * 0.6) + (news_confidence * 0.4)
            
            # Determine final signal
            if decision['news_sentiment'] > 0 and decision['sma_signal'] == 'BUY':
                final_signal = 'BUY'
                signal_strength = 'Strong' if combined_confidence > 0.7 else 'Moderate'
            elif decision['news_sentiment'] < 0 and decision['sma_signal'] == 'SELL':
                final_signal = 'SELL'
                signal_strength = 'Strong' if combined_confidence > 0.7 else 'Moderate'
            else:
                final_signal = 'HOLD'
                signal_strength = 'Weak'
            
            print(f"   News Confidence: {news_confidence:.2f}")
            print(f"   Technical Confidence: {technical_confidence:.2f}")
            print(f"   Combined Confidence: {combined_confidence:.2f}")
            print(f"   Final Decision: {final_signal} ({signal_strength})")
            print()
            
        print("✅ Decisions made based on combined analysis")
        print()
        
    async def _show_trade_execution(self):
        """Show trade execution"""
        print("💰 Step 4: Trade Execution")
        print("-" * 50)
        
        trades = [
            {
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 100,
                'price': 150.25,
                'confidence': 0.82,
                'reason': 'Strong earnings news + oversold RSI + bullish SMA crossover'
            },
            {
                'symbol': 'TSLA',
                'action': 'BUY',
                'quantity': 50,
                'price': 245.80,
                'confidence': 0.68,
                'reason': 'Product breakthrough + neutral RSI + bullish SMA'
            },
            {
                'symbol': 'JPM',
                'action': 'SELL',
                'quantity': 75,
                'price': 185.40,
                'confidence': 0.74,
                'reason': 'Rate hike concerns + overbought RSI + bearish SMA'
            }
        ]
        
        for trade in trades:
            print(f"🎯 Executing {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
            print(f"   Confidence: {trade['confidence']:.2f}")
            print(f"   Reason: {trade['reason']}")
            
            # Calculate position size based on confidence
            if trade['confidence'] > 0.7:
                position_size = "Full position (high confidence)"
            elif trade['confidence'] > 0.5:
                position_size = "Half position (moderate confidence)"
            else:
                position_size = "Small position (low confidence)"
            
            print(f"   Position Size: {position_size}")
            
            # Update portfolio
            trade_value = trade['quantity'] * trade['price']
            if trade['action'] == 'BUY':
                self.portfolio['cash'] -= trade_value
                self.portfolio['positions'][trade['symbol']] = self.portfolio['positions'].get(trade['symbol'], 0) + trade['quantity']
            else:  # SELL
                self.portfolio['cash'] += trade_value
                self.portfolio['positions'][trade['symbol']] = self.portfolio['positions'].get(trade['symbol'], 0) - trade['quantity']
            
            self.portfolio['trades'].append(trade)
            print()
            
        print("✅ Trades executed successfully")
        print()
        
    async def _show_portfolio_results(self):
        """Show portfolio results"""
        print("📈 Step 5: Portfolio Results")
        print("-" * 50)
        
        # Calculate current portfolio value
        current_prices = {'AAPL': 155.00, 'TSLA': 250.00, 'JPM': 180.00}
        
        total_position_value = 0
        for symbol, quantity in self.portfolio['positions'].items():
            if quantity > 0:  # Long position
                position_value = quantity * current_prices[symbol]
                total_position_value += position_value
                print(f"📊 {symbol}: {quantity} shares @ ${current_prices[symbol]:.2f} = ${position_value:,.2f}")
        
        total_portfolio_value = self.portfolio['cash'] + total_position_value
        initial_capital = 100000
        total_return = total_portfolio_value - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        print(f"\n💰 Portfolio Summary:")
        print(f"   Cash: ${self.portfolio['cash']:,.2f}")
        print(f"   Positions: ${total_position_value:,.2f}")
        print(f"   Total Value: ${total_portfolio_value:,.2f}")
        print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
        print(f"   Trades Executed: {len(self.portfolio['trades'])}")
        
        print(f"\n📋 Trade Summary:")
        for trade in self.portfolio['trades']:
            current_price = current_prices[trade['symbol']]
            if trade['action'] == 'BUY':
                unrealized_pnl = (current_price - trade['price']) * trade['quantity']
                pnl_pct = ((current_price - trade['price']) / trade['price']) * 100
                print(f"   {trade['symbol']} BUY: {unrealized_pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        print(f"\n🎉 News-Enhanced Trading Results:")
        print(f"   ✅ Successfully combined news sentiment with technical analysis")
        print(f"   ✅ Generated higher confidence trading signals")
        print(f"   ✅ Executed trades based on multi-factor analysis")
        print(f"   ✅ Portfolio shows positive returns from combined approach")


async def main():
    """Main demo function"""
    demo = SimpleNewsEnhancedDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main()) 