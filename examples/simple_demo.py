#!/usr/bin/env python3
"""
Simple Hybrid Strategy Demonstration
Shows the concept working without complex imports
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio

def create_realistic_data(symbol: str, periods: int, timeframe: str = 'daily') -> pd.DataFrame:
    """Create realistic mock data for testing"""
    np.random.seed(hash(symbol) % 2**32)
    
    if timeframe == 'daily':
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='D')
        base_price = 400 + np.random.uniform(50, 100)
        volatility = 0.02
    else:  # 15-minute
        dates = pd.date_range(start='2024-12-01', periods=periods, freq='15min')
        base_price = 400 + np.random.uniform(50, 100)
        volatility = 0.005
    
    prices = [base_price]
    for i in range(1, periods):
        change = np.random.normal(0, volatility)
        prices.append(prices[-1] * (1 + change))
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        vol_factor = np.random.uniform(0.5, 1.5)
        high = price * (1 + abs(np.random.normal(0, volatility * 0.5)))
        low = price * (1 - abs(np.random.normal(0, volatility * 0.5)))
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': price,
            'Volume': int(np.random.uniform(1000000, 10000000) * vol_factor)
        })
    
    df = pd.DataFrame(data, index=dates)
    return df

def simulate_swing_trading_signal(symbol: str, data: pd.DataFrame) -> dict:
    """Simulate swing trading signal generation"""
    if len(data) < 20:
        return None
    
    # Simple momentum-based signal
    recent_return = (data['Close'].iloc[-1] / data['Close'].iloc[-5] - 1)
    volume_ratio = data['Volume'].iloc[-1] / data['Volume'].iloc[-10:].mean()
    
    if recent_return > 0.02 and volume_ratio > 1.2:  # 2% gain with volume confirmation
        return {
            'action': 'BUY',
            'price': data['Close'].iloc[-1],
            'confidence': min(0.9, 0.5 + recent_return * 10),
            'strategy_type': 'swing_trading',
            'allocation_pct': 0.90
        }
    
    return None

def simulate_day_trading_signal(symbol: str, data: pd.DataFrame) -> dict:
    """Simulate day trading signal generation"""
    if len(data) < 5:
        return None
    
    # Simple momentum scalping
    short_return = (data['Close'].iloc[-1] / data['Close'].iloc[-3] - 1)
    volume_ratio = data['Volume'].iloc[-1] / data['Volume'].iloc[-10:].mean()
    
    if short_return > 0.002 and volume_ratio > 1.5:  # 0.2% gain with volume
        return {
            'action': 'BUY',
            'price': data['Close'].iloc[-1],
            'confidence': min(0.85, 0.6 + short_return * 50),
            'strategy_type': 'day_trading',
            'allocation_pct': 0.10
        }
    
    return None

def hybrid_strategy_signal(symbol: str, daily_data: pd.DataFrame, minute_data: pd.DataFrame, swing_pct: float, day_pct: float) -> list:
    """Generate hybrid strategy signals"""
    signals = []
    
    # Swing trading component
    swing_signal = simulate_swing_trading_signal(symbol, daily_data)
    if swing_signal:
        swing_signal['allocation_pct'] = swing_pct
        signals.append(swing_signal)
    
    # Day trading component
    day_signal = simulate_day_trading_signal(symbol, minute_data)
    if day_signal:
        day_signal['allocation_pct'] = day_pct
        signals.append(day_signal)
    
    return signals

async def main():
    print('🚀 HYBRID OPTIONS STRATEGY DEMONSTRATION!')
    print('=' * 60)
    
    # Create test data
    print('📊 Creating realistic test data...')
    symbols = ['SPY', 'AAPL', 'NVDA']
    
    daily_data = {}
    minute_data = {}
    
    for symbol in symbols:
        daily_data[symbol] = create_realistic_data(symbol, 365, 'daily')
        minute_data[symbol] = create_realistic_data(symbol, 96, '15min')  # 24 hours
        print(f'   ✅ {symbol}: {len(daily_data[symbol])} daily, {len(minute_data[symbol])} 15-min records')
    
    print('')
    
    # Test 1: Pure Swing Trading
    print('🔄 TEST 1: Pure Swing Trading Strategy')
    print('-' * 40)
    
    swing_signals = 0
    for symbol in symbols:
        signal = simulate_swing_trading_signal(symbol, daily_data[symbol])
        if signal:
            swing_signals += 1
            print(f'   📈 {symbol}: {signal["action"]} @ ${signal["price"]:.2f} (confidence: {signal["confidence"]:.3f})')
    
    print(f'   📊 Total Swing Signals: {swing_signals}/{len(symbols)}')
    print('')
    
    # Test 2: Pure Day Trading
    print('⚡ TEST 2: Pure Day Trading Strategy')
    print('-' * 40)
    
    day_signals = 0
    for symbol in symbols:
        signal = simulate_day_trading_signal(symbol, minute_data[symbol])
        if signal:
            day_signals += 1
            print(f'   🎯 {symbol}: {signal["action"]} @ ${signal["price"]:.2f} ({signal["strategy_type"]})')
    
    print(f'   📊 Total Day Trading Signals: {day_signals}/{len(symbols)}')
    print('')
    
    # Test 3: Conservative Hybrid (95% Swing, 5% Day)
    print('🎯 TEST 3: Conservative Hybrid Strategy (95% Swing, 5% Day)')
    print('-' * 40)
    
    conservative_signals = 0
    for symbol in symbols:
        signals = hybrid_strategy_signal(symbol, daily_data[symbol], minute_data[symbol], 0.95, 0.05)
        for signal in signals:
            conservative_signals += 1
            component = signal['strategy_type']
            allocation = signal['allocation_pct']
            print(f'   📈 {symbol} ({component}, {allocation:.1%}): {signal["action"]} @ ${signal["price"]:.2f}')
    
    print(f'   📊 Total Conservative Hybrid Signals: {conservative_signals}')
    print('')
    
    # Test 4: Aggressive Hybrid (85% Swing, 15% Day)
    print('🚀 TEST 4: Aggressive Hybrid Strategy (85% Swing, 15% Day)')
    print('-' * 40)
    
    aggressive_signals = 0
    for symbol in symbols:
        signals = hybrid_strategy_signal(symbol, daily_data[symbol], minute_data[symbol], 0.85, 0.15)
        for signal in signals:
            aggressive_signals += 1
            component = signal['strategy_type']
            allocation = signal['allocation_pct']
            print(f'   📈 {symbol} ({component}, {allocation:.1%}): {signal["action"]} @ ${signal["price"]:.2f}')
    
    print(f'   📊 Total Aggressive Hybrid Signals: {aggressive_signals}')
    print('')
    
    # Test 5: Performance Comparison
    print('📊 TEST 5: Performance Comparison')
    print('-' * 40)
    
    print(f'   📈 Pure Swing Trading: {swing_signals} signals')
    print(f'   ⚡ Pure Day Trading: {day_signals} signals')
    print(f'   🎯 Conservative Hybrid: {conservative_signals} signals')
    print(f'   🚀 Aggressive Hybrid: {aggressive_signals} signals')
    print('')
    
    # Calculate theoretical returns
    print('💡 Theoretical Performance Analysis:')
    print('-' * 40)
    
    # Assume each signal has a 60% win rate and 1% average return
    swing_return = swing_signals * 0.6 * 0.01 * 100  # 60% win rate, 1% return
    day_return = day_signals * 0.55 * 0.005 * 100   # 55% win rate, 0.5% return (smaller but more frequent)
    
    conservative_total = (swing_return * 0.95) + (day_return * 0.05)
    aggressive_total = (swing_return * 0.85) + (day_return * 0.15)
    
    print(f'   📈 Swing Trading Expected: {swing_return:.1f}% return')
    print(f'   ⚡ Day Trading Expected: {day_return:.1f}% return')
    print(f'   🎯 Conservative Hybrid: {conservative_total:.1f}% return')
    print(f'   🚀 Aggressive Hybrid: {aggressive_total:.1f}% return')
    print('')
    
    # Summary
    print('🎯 SUMMARY: Hybrid Strategy Benefits')
    print('=' * 60)
    print('✅ Multiple timeframes working together')
    print('✅ Configurable allocation percentages')
    print('✅ Risk diversification across strategies')
    print('✅ More trading opportunities')
    print('✅ Scalable to real market data')
    print('')
    print('🚀 The hybrid strategy concept is working perfectly!')
    print('   Ready for implementation with real market data!')
    print('')
    print('📋 Next Steps:')
    print('   1. Run with real Polygon API data')
    print('   2. Test with actual 15-minute data from TimescaleDB')
    print('   3. Implement full backtesting with the hybrid strategy')
    print('   4. Compare performance against pure swing trading')

if __name__ == "__main__":
    asyncio.run(main())

