#!/usr/bin/env python3
"""
Demo: All AI-Enhanced Trading Strategies
Shows how to use all the AI-enhanced strategies with LLM integration
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import sys
import json
import os
import logging

# Add src to path
sys.path.append('src')

from src.services.ai.ollama_service import OllamaService, AIAnalysis
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.core.types import TradeSignal
from src.services.database.market_data_service import MarketDataService
from src.utils.config import get_config
from src.utils.trading_config import get_symbols


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime and numpy types"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'dtype'):  # numpy types
            if hasattr(obj, 'item'):
                return obj.item()
            else:
                return str(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)


class AIStrategyManager:
    """Manager for all AI-enhanced trading strategies"""
    
    def __init__(self):
        self.ollama_service = None
        self.strategies = {}
        self.ai_available = False
        
    async def initialize(self, ollama_url: str = None):
        """Initialize all strategies with AI service"""
        print("🧠 Initializing AI-Enhanced Trading Strategies")
        print("=" * 50)
        
        if ollama_url is None:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        # Initialize Ollama service
        try:
            self.ollama_service = OllamaService(base_url=ollama_url)
            self.ai_available = True
            print("✅ Ollama AI service initialized successfully")
        except Exception as e:
            print(f"⚠️  Ollama AI service not available: {e}")
            print("   Strategies will run without AI enhancement")
            self.ai_available = False
        
        # Initialize all strategies
        self.strategies = {
            'RSI': RSIStrategy(period=14, oversold=30, overbought=70),
            'BollingerBands': BollingerBandsStrategy(period=20, std_dev=2.0),
            'MACD': MACDStrategy(fast_period=12, slow_period=26, signal_period=9),
            'SMACrossover': SMACrossoverStrategy(short_window=20, long_window=50),
            'NewsEnhanced': NewsEnhancedStrategy(technical_weight=0.6, news_weight=0.4)
        }
        
        # Initialize News-Enhanced strategy with AI
        if self.ai_available:
            await self.strategies['NewsEnhanced'].initialize(ollama_url)
        
        print(f"✅ Initialized {len(self.strategies)} strategies")
        print(f"🤖 AI Enhancement: {'Available' if self.ai_available else 'Not Available'}")
    
    async def generate_all_signals(self, symbol: str, data: pd.DataFrame) -> Dict[str, TradeSignal]:
        """Generate signals from all strategies"""
        signals = {}
        
        print(f"\n📊 Generating signals for {symbol}")
        print("-" * 40)
        
        for strategy_name, strategy in self.strategies.items():
            try:
                signal = await strategy.generate_signal(symbol, data)
                if signal:
                    signals[strategy_name] = signal
                    ai_enhanced = signal.metadata.get('ai_enhanced', False)
                    confidence = signal.confidence
                    confidence_str = f"{confidence:.2f}" if confidence is not None else "N/A"
                    
                    print(f"📈 {strategy_name}: {signal.action} (confidence: {confidence_str}) {'🤖' if ai_enhanced else ''}")
                    
                    if ai_enhanced:
                        ai_sentiment = signal.metadata.get('ai_sentiment', 0)
                        confidence_boost = signal.metadata.get('signal_enhancement', {}).get('confidence_boost', 0)
                        ai_sentiment_str = f"{ai_sentiment:.2f}" if ai_sentiment is not None else "N/A"
                        confidence_boost_str = f"{confidence_boost:.2f}" if confidence_boost is not None else "N/A"
                        print(f"   AI Sentiment: {ai_sentiment_str}, Confidence Boost: {confidence_boost_str}")
                else:
                    print(f"❌ {strategy_name}: No signal generated")
                    
            except Exception as e:
                print(f"❌ {strategy_name}: Error - {e}")
        
        return signals
    
    async def generate_ai_consensus(self, symbol: str, signals: Dict[str, TradeSignal], data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate AI consensus signal from all strategy signals"""
        
        if not self.ai_available or not signals:
            return None
        
        try:
            # Prepare technical signals for AI analysis
            technical_signals = []
            for strategy_name, signal in signals.items():
                tech_signal = {
                    'strategy': strategy_name,
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'price': signal.price
                }
                
                # Add strategy-specific data
                if strategy_name == 'RSI' and 'rsi' in signal.metadata:
                    tech_signal['rsi_value'] = signal.metadata['rsi']
                elif strategy_name == 'BollingerBands' and 'percent_b' in signal.metadata:
                    tech_signal['percent_b'] = signal.metadata['percent_b']
                elif strategy_name == 'MACD' and 'macd' in signal.metadata:
                    tech_signal['macd_value'] = signal.metadata['macd']
                
                technical_signals.append(tech_signal)
            
            # Prepare market context
            current_price = data['Close'].iloc[-1]
            volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000
            price_change_24h = (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0
            volatility = data['Close'].rolling(window=20).std().iloc[-1] / current_price if len(data) >= 20 else 0
            
            market_context = {
                'symbol': symbol,
                'current_price': current_price,
                'volume': volume,
                'price_change_24h': price_change_24h,
                'volatility': volatility,
                'signal_count': len(signals),
                'buy_signals': len([s for s in signals.values() if s.action == 'BUY']),
                'sell_signals': len([s for s in signals.values() if s.action == 'SELL'])
            }
            
            # Generate AI consensus
            if self.ollama_service:
                ai_analysis = await self.ollama_service.analyze_market_sentiment(
                    news_events=[],
                    technical_signals=technical_signals,
                    market_data=market_context
                )
            else:
                return None
            
            # Determine consensus action
            buy_signals = [s for s in signals.values() if s.action == 'BUY']
            sell_signals = [s for s in signals.values() if s.action == 'SELL']
            
            if len(buy_signals) > len(sell_signals):
                consensus_action = 'BUY'
                consensus_signals = buy_signals
            elif len(sell_signals) > len(buy_signals):
                consensus_action = 'SELL'
                consensus_signals = sell_signals
            else:
                # Tie - use AI sentiment to break
                consensus_action = 'BUY' if ai_analysis.sentiment_score > 0 else 'SELL'
                consensus_signals = buy_signals if consensus_action == 'BUY' else sell_signals
            
            # Calculate consensus confidence
            if consensus_signals:
                avg_confidence = sum(s.confidence for s in consensus_signals) / len(consensus_signals)
                consensus_confidence = (avg_confidence * 0.6 + ai_analysis.confidence * 0.4)
            else:
                consensus_confidence = ai_analysis.confidence
            
            # Create consensus signal
            consensus_signal = TradeSignal(
                symbol=symbol,
                action=consensus_action,
                quantity=1000 / current_price,  # $1000 position
                price=current_price,
                timestamp=datetime.now(),
                strategy="AI_CONSENSUS",
                confidence=consensus_confidence,
                metadata={
                    'ai_enhanced': True,
                    'ai_sentiment': ai_analysis.sentiment_score,
                    'ai_confidence': ai_analysis.confidence,
                    'ai_reasoning': ai_analysis.reasoning,
                    'ai_risk_assessment': ai_analysis.risk_assessment,
                    'consensus_breakdown': {
                        'total_signals': len(signals),
                        'buy_signals': len(buy_signals),
                        'sell_signals': len(sell_signals),
                        'consensus_action': consensus_action
                    },
                    'individual_signals': {
                        name: {
                            'action': signal.action,
                            'confidence': signal.confidence,
                            'ai_enhanced': signal.metadata.get('ai_enhanced', False)
                        } for name, signal in signals.items()
                    }
                }
            )
            
            return consensus_signal
            
        except Exception as e:
            print(f"Error generating AI consensus: {e}")
            return None
    
    async def get_strategy_insights(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get insights from all strategies"""
        
        insights = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'ai_available': self.ai_available,
            'strategies': {}
        }
        
        for strategy_name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, 'get_strategy_insights'):
                    strategy_insights = await strategy.get_strategy_insights(symbol, data)
                    insights['strategies'][strategy_name] = strategy_insights
                else:
                    # Generate basic insights for strategies without AI insights
                    signal = await strategy.generate_signal(symbol, data)
                    insights['strategies'][strategy_name] = {
                        'signal_generated': signal is not None,
                        'signal_action': signal.action if signal else None,
                        'signal_confidence': signal.confidence if signal else None
                    }
            except Exception as e:
                insights['strategies'][strategy_name] = {'error': str(e)}
        
        return insights


async def demo_all_ai_strategies():
    """Demo all AI strategies with real market data"""
    config = get_config()
    
    # Initialize services
    market_data_service = MarketDataService(config.database_url)
    
    # Use centralized symbol list (small set for demo)
    symbols = get_symbols()[:3]  # Limit for demo
    
    # Calculate date range (6 months ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"📊 Running AI strategies demo for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize strategy manager
    manager = AIStrategyManager()
    await manager.initialize()
    
    # Test symbols
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"🎯 ANALYZING {symbol}")
        print(f"{'='*60}")
        
        # Get real market data for this symbol
        try:
            data = market_data_service.get_historical_data(symbol, start_date, end_date)
            if data is None or data.empty:
                print(f"⚠️  No data found for {symbol} in last 180 days. Trying last 2 years...")
                start_date = end_date - timedelta(days=730)
                data = market_data_service.get_historical_data(symbol, start_date, end_date)
            if data is None or data.empty:
                print(f"❌ No data available for {symbol} in last 2 years. Skipping...")
                continue
            print(f"📊 Using real data for {symbol}: {len(data)} records")
            print(f"   Date range: {data.index.min()} to {data.index.max()}")
            print(f"   Latest price: ${data['Close'].iloc[-1]:.2f}")
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            continue
        
        if data is None or data.empty:
            print(f"❌ No data available for {symbol} after all attempts. Skipping...")
            continue
        
        # Add technical indicators to the data
        try:
            from src.backtesting.backtest_engine import BacktestEngine
            backtest_engine = BacktestEngine()
            data = backtest_engine._add_technical_indicators(data)
            print(f"📈 Added technical indicators to {symbol} data")
            print(f"   Available indicators: {[col for col in data.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]}")
        except Exception as e:
            print(f"⚠️  Warning: Could not add technical indicators for {symbol}: {e}")
            # Continue with original data if indicators can't be added
        # Generate signals from all strategies
        signals = await manager.generate_all_signals(symbol, data)
        
        if signals:
            print(f"\n📋 Signal Summary for {symbol}:")
            print(f"   Total signals: {len(signals)}")
            print(f"   Buy signals: {len([s for s in signals.values() if s.action == 'BUY'])}")
            print(f"   Sell signals: {len([s for s in signals.values() if s.action == 'SELL'])}")
            print(f"   AI-enhanced: {len([s for s in signals.values() if s.metadata.get('ai_enhanced', False)])}")
            
            # Generate AI consensus
            consensus = await manager.generate_ai_consensus(symbol, signals, data)
            if consensus:
                print(f"\n🤖 AI Consensus Signal:")
                print(f"   Action: {consensus.action}")
                confidence = consensus.confidence
                confidence_str = f"{confidence:.2f}" if confidence is not None else "N/A"
                print(f"   Confidence: {confidence_str}")
                ai_sentiment = consensus.metadata.get('ai_sentiment', 0)
                ai_sentiment_str = f"{ai_sentiment:.2f}" if ai_sentiment is not None else "N/A"
                print(f"   AI Sentiment: {ai_sentiment_str}")
                print(f"   AI Reasoning: {consensus.metadata.get('ai_reasoning', 'N/A')[:100]}...")
                
                # Show consensus breakdown
                breakdown = consensus.metadata.get('consensus_breakdown', {})
                print(f"   Consensus: {breakdown.get('buy_signals', 0)} buy vs {breakdown.get('sell_signals', 0)} sell signals")
            
            # Get strategy insights
            insights = await manager.get_strategy_insights(symbol, data)
            print(f"\n📊 Strategy Insights:")
            for strategy_name, insight in insights['strategies'].items():
                if 'error' not in insight:
                    confidence = insight.get('signal_confidence', 0)
                    confidence_str = f"{confidence:.2f}" if confidence is not None else "N/A"
                    print(f"   {strategy_name}: {insight.get('signal_action', 'No signal')} (confidence: {confidence_str})")
                else:
                    print(f"   {strategy_name}: Error - {insight['error']}")
        else:
            print(f"❌ No signals generated for {symbol}")
    
    print(f"\n{'='*60}")
    print("✅ AI-Enhanced Strategies Demo Complete!")
    print(f"{'='*60}")
    
    print("\n📋 Key Features Demonstrated:")
    print("1. ✅ All strategies enhanced with AI capabilities")
    print("2. ✅ Individual strategy signal generation with AI enhancement")
    print("3. ✅ AI consensus signal from multiple strategies")
    print("4. ✅ Strategy insights and performance analysis")
    print("5. ✅ Graceful fallback when AI is unavailable")
    print("6. ✅ Comprehensive metadata and confidence boosting")
    
    print("\n🎯 Available AI-Enhanced Strategies:")
    print("   • RSI Strategy + AI")
    print("   • Bollinger Bands Strategy + AI")
    print("   • MACD Strategy + AI")
    print("   • SMA Crossover Strategy + AI")
    print("   • News-Enhanced Strategy (built-in AI)")
    print("   • AI Consensus (combines all strategies)")
    
    # Run backtest to show trading performance statistics
    print("\n" + "=" * 60)
    print("📊 TRADING PERFORMANCE STATISTICS")
    print("=" * 60)
    
    try:
        from src.backtesting.backtest_engine import BacktestEngine
        
        # Initialize backtest engine
        backtest_engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest on the same symbols we analyzed
        print(f"🎯 Running backtest on symbols: {symbols}")
        
        backtest_results = await backtest_engine.run_backtest(
            symbols=symbols,
            start_date='2024-01-01',
            end_date='2024-12-31',
            strategies=['RSI_Strategy', 'MACD_Strategy', 'BollingerBands_Strategy']
        )
        
        if backtest_results:
            print(f"\n📈 BACKTEST PERFORMANCE RESULTS")
            print("-" * 50)
            
            for strategy_name, result in backtest_results.items():
                print(f"\n🎯 {strategy_name}:")
                print(f"   📈 Total Return: {result.total_return_pct:.2f}% (${result.total_return:,.2f})")
                print(f"   📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
                print(f"   📊 Sharpe Ratio: {result.sharpe_ratio:.3f}")
                print(f"   🔄 Total Trades: {result.total_trades}")
                print(f"   ✅ Winning Trades: {result.winning_trades}")
                print(f"   ❌ Losing Trades: {result.losing_trades}")
                print(f"   🎯 Win Rate: {result.win_rate:.1%}")
                print(f"   💰 Profit Factor: {result.profit_factor:.2f}")
                print(f"   📈 Avg Win: ${result.avg_win:.2f}")
                print(f"   📉 Avg Loss: ${result.avg_loss:.2f}")
                
                # Show some trade details if available
                if result.trades and len(result.trades) > 0:
                    print(f"   📋 Sample Trades:")
                    for i, trade in enumerate(result.trades[:3]):  # Show first 3 trades
                        print(f"      {i+1}. {trade.symbol} {trade.action} @ ${trade.price:.2f} (P&L: ${trade.pnl:.2f})")
        else:
            print("❌ No backtest results generated")
            
    except Exception as e:
        print(f"⚠️  Could not run backtest: {e}")
    
    print("\n🚀 Next Steps:")
    print("1. Start Ollama service for full AI functionality")
    print("2. Add these strategies to your backtest configuration")
    print("3. Monitor AI-enhanced performance vs base strategies")
    print("4. Adjust AI weights based on market conditions")


if __name__ == "__main__":
    asyncio.run(demo_all_ai_strategies()) 