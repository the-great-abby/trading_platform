#!/usr/bin/env python3
"""
Greeks-Enhanced Comprehensive Backtest
Runs standard strategies on all symbols and Greeks-enhanced strategies on options symbols
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.services.ai.ollama_service import OllamaService
from src.services.database.market_data_service import MarketDataService
from src.services.database.backtest_results_service import BacktestResultsService
from src.strategies.base import BaseStrategy
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.strategies.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.utils.config import get_config
from src.utils.trading_config import get_symbols, get_options_symbols

logger = get_trading_logger()

def get_signal_field(signals, field, default=None):
    if isinstance(signals, dict):
        return signals.get(field, default)
    return getattr(signals, field, default)

class GreeksComprehensiveBacktestRunner:
    """Runner for Greeks-enhanced comprehensive backtest"""
    
    def __init__(self):
        self.config = get_config()
        self.market_data_service = MarketDataService()
        self.backtest_service = BacktestResultsService()
        self.llm_service = OllamaService()
        
        # Initialize symbol lists
        all_symbols = get_symbols() or []
        options_symbols = get_options_symbols() or []
        
        logger.info(f"📊 Total symbols: {len(all_symbols)}")
        logger.info(f"📈 Options symbols: {len(options_symbols)}")
        
        # Initialize strategies
        self.standard_strategies = [
            BollingerBandsStrategy(period=20),
            MACDStrategy(fast_period=12, slow_period=26),
            RSIStrategy(period=14),
            SMACrossoverStrategy(short_window=10, long_window=30),
            MomentumStrategy(momentum_period=10),
            MeanReversionStrategy(short_ma=10, long_ma=30),
            VolatilityBreakoutStrategy(volatility_period=20)
        ]
        
        self.greeks_strategies = [
            GreeksEnhancedStrategy()
        ]
        
        logger.info(f"🎯 Standard strategies: {len(self.standard_strategies)}")
        logger.info(f"📊 Greeks strategies: {len(self.greeks_strategies)}")
        
        # Initialize services
        self.market_data_service = MarketDataService()
        self.backtest_results_service = BacktestResultsService()
        
        # Initialize LLM service
        self.ollama_service = OllamaService()
        
        logger.info("🔧 Greeks-Enhanced Comprehensive Backtest Runner initialized")
    
    async def run_comprehensive_backtest(self):
        """Run comprehensive backtest with both standard and Greeks strategies"""
        logger.info("🚀 Running combined analysis...")
        
        # Initialize symbol lists
        all_symbols = get_symbols() or []
        options_symbols = get_options_symbols() or []
        
        logger.info(f"📊 Total symbols: {len(all_symbols)}")
        logger.info(f"📈 Options symbols: {len(options_symbols)}")
        
        # Verify Ollama model availability
        logger.info("🔍 Verifying Ollama model availability...")
        model_info = await self.ollama_service.verify_model_availability()
        
        if not model_info.get('available'):
            logger.error("❌ Ollama service not available")
            return
        
        logger.info("✅ Model verification successful")
        logger.info(f"   Available models: {model_info.get('total_models', 0)}")
        logger.info(f"   Target model available: {model_info.get('target_available', False)}")
        
        # Test model response
        logger.info("🧪 Testing model response...")
        test_result = await self.ollama_service.test_model_response()
        
        if not test_result.get('success'):
            logger.error(f"❌ Model test failed: {test_result.get('error', 'Unknown error')}")
            logger.error("❌ Model verification failed, aborting backtest")
            return
        
        logger.info("✅ Model test successful - using gemma3:1b")
        
        # Analyze Greeks data coverage
        logger.info("📊 Analyzing Greeks data coverage...")
        real_options_data_count = 0
        mock_options_data_count = 0
        
        for symbol in options_symbols:
            logger.info(f"🔍 Checking Greeks data for {symbol}...")
            try:
                # Check if options data is available
                options_data = self.market_data_service.get_options_data(symbol)
                if options_data:
                    real_options_data_count += 1
                    logger.info(f"✅ Real options data found for {symbol}")
                else:
                    mock_options_data_count += 1
                    logger.info(f"📋 Using mock options data for {symbol}")
            except Exception as e:
                logger.warning(f"⚠️ Error checking options data for {symbol}: {e}")
                mock_options_data_count += 1
        
        # Run standard strategies on all symbols
        logger.info("📈 Running standard strategies on all symbols...")
        standard_results = []
        
        for symbol in all_symbols:
            logger.info(f"📊 Processing {symbol} with standard strategies...")
            
            for strategy in self.standard_strategies:
                try:
                    # Get historical data for the last 30 days
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=30)
                    data = self.market_data_service.get_historical_data(symbol, start_date, end_date)
                    
                    if data is None or data.empty:
                        logger.warning(f"⚠️ No data for {symbol}, skipping")
                        continue
                    
                    # Generate signals
                    signals = await strategy.generate_signal(symbol, data)
                    if signals:
                        # Explicit LLM analysis call for every signal
                        try:
                            action = get_signal_field(signals, 'action', 'HOLD')
                            confidence = get_signal_field(signals, 'confidence', 0.5)
                            price = get_signal_field(signals, 'price', 0)
                            metadata = get_signal_field(signals, 'metadata', {})
                            logger.info(f"[Runner] 🤖 Running LLM analysis for {symbol} {action} signal...")
                            market_context = {'current_price': price, 'symbol': symbol, 'strategy': strategy.name, 'confidence': confidence}
                            analysis = await self.ollama_service.analyze_market_sentiment(
                                news_events=[],
                                technical_signals=[{'strategy': strategy.name, 'action': action, 'confidence': confidence, 'metadata': metadata}],
                                market_data=market_context
                            )
                            if analysis:
                                if isinstance(signals, dict):
                                    signals['llm_analysis'] = {"sentiment_score": getattr(analysis, 'sentiment_score', None), "confidence": getattr(analysis, 'confidence', None), "reasoning": getattr(analysis, 'reasoning', None), "risk_assessment": getattr(analysis, 'risk_assessment', None), "market_impact": getattr(analysis, 'market_impact', None), "recommended_action": getattr(analysis, 'recommended_action', None)}
                                else:
                                    # signals is a TradeSignal object, add llm_analysis to metadata
                                    if not hasattr(signals, 'metadata'):
                                        signals.metadata = {}
                                    signals.metadata['llm_analysis'] = {"sentiment_score": getattr(analysis, 'sentiment_score', None), "confidence": getattr(analysis, 'confidence', None), "reasoning": getattr(analysis, 'reasoning', None), "risk_assessment": getattr(analysis, 'risk_assessment', None), "market_impact": getattr(analysis, 'market_impact', None), "recommended_action": getattr(analysis, 'recommended_action', None)}
                                logger.info(f"[Runner] ✅ LLM analysis completed for {symbol}: {getattr(analysis, 'recommended_action', None)}")
                            else:
                                logger.warning(f"[Runner] ⚠️ LLM analysis returned no result for {symbol}")
                        except Exception as e:
                            logger.error(f"[Runner] ❌ LLM analysis failed for {symbol}: {e}")
                        standard_results.append({'symbol': symbol, 'strategy': strategy.name, 'signals': signals})
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol} with {strategy.__class__.__name__}: {e}")
        
        # Run Greeks strategies on options symbols
        logger.info("📊 Running Greeks strategies on options symbols...")
        greeks_results = []
        
        for symbol in options_symbols:
            logger.info(f"📊 Processing {symbol} with Greeks strategies...")
            
            for strategy in self.greeks_strategies:
                try:
                    # Get options data (use mock if not available)
                    try:
                        options_data = self.market_data_service.get_options_data(symbol)
                        if not options_data:
                            logger.info(f"📋 Using mock options data for {symbol}")
                            # Create mock options data
                            options_data = self._create_mock_options_data(symbol)
                    except Exception as e:
                        logger.info(f"📋 Using mock options data for {symbol}")
                        options_data = self._create_mock_options_data(symbol)
                    
                    # Generate signals
                    signals = await strategy.generate_signal(symbol, options_data)
                    
                    if signals:
                        greeks_results.append({
                            'symbol': symbol,
                            'strategy': strategy.name,
                            'signals': signals
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol} with {strategy.__class__.__name__}: {e}")
        
        # Print summary
        logger.info("📊 Backtest Summary:")
        logger.info(f"   Standard strategies: {len(standard_results)} results")
        logger.info(f"   Greeks strategies: {len(greeks_results)} results")
        logger.info(f"   Real options data: {real_options_data_count}")
        logger.info(f"   Mock options data: {mock_options_data_count}")
        
        logger.info("✅ Greeks-Enhanced Comprehensive Backtest completed!")
    
    def _create_mock_options_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Create mock options data for testing"""
        return [
            {
                'symbol': symbol,
                'strike': 150.0,
                'expiration': '2024-01-19',
                'option_type': 'call',
                'delta': 0.6,
                'gamma': 0.02,
                'theta': -0.05,
                'vega': 0.1,
                'price': 5.0,
                'volume': 100
            },
            {
                'symbol': symbol,
                'strike': 160.0,
                'expiration': '2024-01-19',
                'option_type': 'call',
                'delta': 0.4,
                'gamma': 0.03,
                'theta': -0.06,
                'vega': 0.12,
                'price': 3.0,
                'volume': 80
            }
        ]

    async def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'ollama_service'):
                await self.ollama_service.cleanup()
            logger.info("✅ Resources cleaned up")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

async def main():
    """Main entry point"""
    runner = None
    try:
        async with GreeksComprehensiveBacktestRunner() as runner:
            await runner.run_comprehensive_backtest()
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    finally:
        if runner:
            await runner.cleanup()
        logger.info("🏁 Backtest completed")

if __name__ == "__main__":
    asyncio.run(main()) 