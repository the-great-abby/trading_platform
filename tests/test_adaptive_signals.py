import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.append('src')

from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy

async def test_signal_generation():
    """Test how many signals the adaptive strategy generates"""
    
    # Create test data (90 days)
    dates = pd.date_range(start='2024-01-01', periods=90, freq='D')
    
    # Simulate realistic price data
    base_price = 150.0
    prices = [base_price]
    for i in range(1, 90):
        daily_return = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + daily_return))
    
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 90)
    }, index=dates)
    
    # Test strategy
    strategy = AdaptiveSectorWaveStrategy()
    
    signals = []
    for i in range(50, len(data)):
        current_data = data.iloc[:i+1]
        signal = await strategy.generate_signal('AAPL', current_data)
        if signal:
            signals.append({
                'day': i,
                'action': signal.action,
                'price': signal.price,
                'confidence': signal.confidence,
                'metadata': signal.metadata
            })
    
    print(f"📊 Signal Generation Test (90 days):")
    print(f"   Total signals: {len(signals)}")
    print(f"   Signals per month: {len(signals) / 3:.1f}")
    print(f"   BUY signals: {sum(1 for s in signals if s['action'] == 'BUY')}")
    print(f"   SELL signals: {sum(1 for s in signals if s['action'] == 'SELL')}")
    print()
    
    if signals:
        print("📋 Sample signals:")
        for s in signals[:5]:
            print(f"   Day {s['day']}: {s['action']} @ ${s['price']:.2f} (confidence: {s['confidence']:.2f})")
            print(f"      Strategy: {s['metadata'].get('active_strategy', 'unknown')}")
    else:
        print("⚠️  NO SIGNALS GENERATED - This is the problem!")
        print()
        print("Possible issues:")
        print("  • Conditions are too strict")
        print("  • Not enough market volatility in test data")
        print("  • Elliott Wave confidence threshold too high")

asyncio.run(test_signal_generation())
