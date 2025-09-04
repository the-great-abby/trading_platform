#!/usr/bin/env python3
"""
Test LLM Analysis with Fixed RSI Strategy
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.rsi_strategy import RSIStrategy
from src.services.ai.ollama_service import OllamaService
from src.services.database.market_data_service import MarketDataService
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger(__name__)

async def test_llm_analysis():
    """Test LLM analysis with RSI strategy"""
    logger.info("🧪 Testing LLM Analysis with RSI Strategy")
    
    # Initialize services
    market_data_service = MarketDataService()
    ollama_service = OllamaService()
    
    # Test model availability
    logger.info("🔍 Testing Ollama model availability...")
    model_info = await ollama_service.verify_model_availability()
    
    if not model_info.get('available'):
        logger.error("❌ Ollama service not available")
        return
    
    logger.info("✅ Model verification successful")
    
    # Test model response
    logger.info("🧪 Testing model response...")
    test_result = await ollama_service.test_model_response()
    
    if not test_result.get('success'):
        logger.error(f"❌ Model test failed: {test_result.get('error', 'Unknown error')}")
        return
    
    logger.info("✅ Model test successful")
    
    # Create mock data for testing
    logger.info("📊 Creating mock market data...")
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    mock_data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(110, 220, len(dates)),
        'Low': np.random.uniform(90, 180, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    # Test RSI strategy
    logger.info("📈 Testing RSI strategy...")
    rsi_strategy = RSIStrategy(period=14)
    
    try:
        signal = await rsi_strategy.generate_signal("AAPL", mock_data)
        if signal:
            logger.info(f"✅ RSI Strategy generated signal: {signal.action} at {signal.price}")
            
            # Test LLM analysis on the signal
            logger.info("🤖 Testing LLM analysis on signal...")
            
            # Create market context for LLM analysis
            market_context = {
                'current_price': signal.price,
                'symbol': signal.symbol,
                'volume': mock_data['Volume'].iloc[-1],
                'volatility': mock_data['Close'].pct_change().std()
            }
            
            # Test LLM analysis
            try:
                analysis = await ollama_service.analyze_market_sentiment(
                    news_events=[],  # No news for this test
                    technical_signals=[{
                        'strategy': 'RSI',
                        'action': signal.action,
                        'confidence': signal.confidence,
                        'metadata': signal.metadata
                    }],
                    market_data=market_context
                )
                
                logger.info("✅ LLM Analysis successful!")
                logger.info(f"   Sentiment: {analysis.sentiment_score}")
                logger.info(f"   Confidence: {analysis.confidence}")
                logger.info(f"   Reasoning: {analysis.reasoning}")
                logger.info(f"   Risk Assessment: {analysis.risk_assessment}")
                logger.info(f"   Market Impact: {analysis.market_impact}")
                logger.info(f"   Recommended Action: {analysis.recommended_action}")
                
            except Exception as e:
                logger.error(f"❌ LLM analysis failed: {e}")
                
        else:
            logger.info("ℹ️ No RSI signal generated (this is normal)")
            
    except Exception as e:
        logger.error(f"❌ RSI Strategy failed: {e}")
    
    logger.info("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_llm_analysis()) 