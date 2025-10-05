#!/usr/bin/env python3
"""
Test script to debug Elliott Wave Corrective Strategy
"""

import sys
import os
sys.path.append('/app')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the strategy
from src.strategies.enhanced_elliott_wave_strategies import ElliottWaveCorrectiveStrategy

def create_test_data():
    """Create simple test data"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    np.random.seed(42)  # For reproducible results
    
    # Create realistic price data with some volatility
    base_price = 180.0
    prices = []
    current_price = base_price
    
    for i in range(len(dates)):
        # Add some random walk with mean reversion
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        current_price = current_price * (1 + change)
        prices.append(current_price)
    
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': [np.random.randint(1000000, 5000000) for _ in range(len(dates))]
    })
    
    data.set_index('Date', inplace=True)
    return data

async def test_strategy():
    """Test the Elliott Wave Corrective Strategy"""
    print("🧪 Testing Elliott Wave Corrective Strategy")
    print("=" * 50)
    
    # Create test data
    data = create_test_data()
    print(f"📊 Created test data: {len(data)} days")
    print(f"📈 Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    # Create strategy instance
    strategy = ElliottWaveCorrectiveStrategy()
    print(f"🎯 Strategy: {strategy.name}")
    print(f"⚙️  Confidence threshold: {strategy.confidence_threshold}")
    print(f"📅 Lookback period: {strategy.lookback_period}")
    print(f"📊 Volatility threshold: {strategy.volatility_threshold}")
    
    # Test signal generation
    print("\n🔄 Testing signal generation...")
    
    signals_generated = 0
    for i in range(5, len(data)):  # Start from day 5 to have enough data
        test_data = data.iloc[:i+1]  # Data up to current day
        
        try:
            signal = await strategy.generate_signal("AAPL", test_data)
            if signal:
                signals_generated += 1
                print(f"✅ Day {i}: Generated {signal.action} signal (confidence: {signal.confidence:.3f})")
            else:
                print(f"❌ Day {i}: No signal generated")
        except Exception as e:
            print(f"💥 Day {i}: Error - {e}")
    
    print(f"\n📊 Summary: Generated {signals_generated} signals out of {len(data)-5} attempts")
    
    # Test individual components
    print("\n🔍 Testing individual components...")
    
    # Test swing point detection
    swing_points = strategy.detect_swing_points(data)
    print(f"📍 Swing points detected: {len(swing_points['highs'])} highs, {len(swing_points['lows'])} lows")
    
    # Test pattern analysis
    pattern_analysis = strategy.analyze_corrective_pattern(swing_points, data)
    print(f"🔍 Pattern analysis: {pattern_analysis}")
    
    # Test mean reversion signal
    mean_reversion_signal = strategy.calculate_mean_reversion_signal(data)
    print(f"📈 Mean reversion signal: {mean_reversion_signal}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_strategy())

