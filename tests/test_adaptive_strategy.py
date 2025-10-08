#!/usr/bin/env python3
"""
Test AdaptiveSectorWaveStrategy Performance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
import pandas as pd
import numpy as np
from datetime import datetime

def test_adaptive_strategy():
    print('🚀 Testing AdaptiveSectorWaveStrategy Performance')
    print('=' * 60)
    
    # Initialize strategy
    strategy = AdaptiveSectorWaveStrategy()
    
    # Generate mock market data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Create realistic price data
    base_price = 150.0
    prices = [base_price]
    for i in range(1, 100):
        daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
        prices.append(prices[-1] * (1 + daily_return))
    
    data = pd.DataFrame({
        'Close': prices,
        'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    print(f'📊 Generated {len(data)} days of market data')
    print(f'💰 Price range: ${data["Close"].min():.2f} - ${data["Close"].max():.2f}')
    print()
    
    # Test strategy signals
    signals_generated = 0
    buy_signals = 0
    sell_signals = 0
    
    for i in range(10, len(data)):  # Test last 90 days
        try:
            signal = strategy.generate_signal(data.iloc[:i+1], 'AAPL')
            if signal:
                signals_generated += 1
                if signal.action == 'BUY':
                    buy_signals += 1
                elif signal.action == 'SELL':
                    sell_signals += 1
        except Exception as e:
            continue
    
    print('📈 ADAPTIVE SECTOR WAVE STRATEGY TEST RESULTS')
    print('=' * 60)
    print(f'🎯 Total Signals Generated: {signals_generated}')
    print(f'📈 Buy Signals: {buy_signals}')
    print(f'📉 Sell Signals: {sell_signals}')
    print(f'📊 Signal Frequency: {signals_generated/90*100:.1f}% of days')
    
    if signals_generated > 0:
        print(f'✅ Strategy is generating signals!')
        print(f'🔄 Strategy switches: {len(strategy.strategy_switches)}')
        
        # Show recent strategy switches
        if strategy.strategy_switches:
            print('   Recent switches:')
            for switch in list(strategy.strategy_switches.items())[-3:]:
                print(f'   - {switch[0]}: {switch[1]}')
    else:
        print('⚠️ No signals generated - may need more data or different conditions')

if __name__ == "__main__":
    test_adaptive_strategy()







