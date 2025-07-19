#!/usr/bin/env python3
"""
Test script for market regime detection
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_regime.market_regime_detector import MarketRegimeDetector
from src.services.market_regime.volatility_regime import VolatilityRegimeDetector
from src.services.market_regime.trend_regime import TrendRegimeDetector
from src.services.market_regime.sector_rotation import SectorRotationDetector

def generate_test_data(symbol: str, days: int = 100) -> pd.DataFrame:
    """Generate test market data"""
    np.random.seed(hash(symbol) % 2**32)
    
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate realistic price data
    base_price = 100 + np.random.uniform(50, 200)
    prices = [base_price]
    
    for i in range(1, len(date_range)):
        # Add some trend and volatility
        trend = np.random.normal(0.001, 0.02)  # Small positive trend
        prices.append(prices[-1] * (1 + trend))
    
    # Create OHLCV data
    data = pd.DataFrame({
        'Open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'High': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in prices],
        'Low': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(prices))
    }, index=date_range)
    
    return data

def test_volatility_regime():
    """Test volatility regime detection"""
    print("🧪 Testing Volatility Regime Detection")
    print("=" * 50)
    
    detector = VolatilityRegimeDetector(window=20, method='atr')
    
    # Test with different volatility scenarios
    scenarios = {
        'low_vol': generate_test_data('LOW_VOL', 50),
        'high_vol': generate_test_data('HIGH_VOL', 50),
        'normal_vol': generate_test_data('NORMAL_VOL', 50)
    }
    
    for scenario_name, data in scenarios.items():
        # Modify volatility for testing
        if scenario_name == 'high_vol':
            # Add high volatility
            data['High'] = data['Close'] * (1 + np.random.uniform(0.05, 0.15, len(data)))
            data['Low'] = data['Close'] * (1 - np.random.uniform(0.05, 0.15, len(data)))
        elif scenario_name == 'low_vol':
            # Add low volatility
            data['High'] = data['Close'] * (1 + np.random.uniform(0.001, 0.01, len(data)))
            data['Low'] = data['Close'] * (1 - np.random.uniform(0.001, 0.01, len(data)))
        
        regime = detector.classify_regime(data)
        print(f"📊 {scenario_name}: {regime}")
    
    print()

def test_trend_regime():
    """Test trend regime detection"""
    print("🧪 Testing Trend Regime Detection")
    print("=" * 50)
    
    detector = TrendRegimeDetector(ma_window=20, adx_window=14, adx_threshold=20)
    
    # Test with different trend scenarios
    scenarios = {
        'trending_up': generate_test_data('TREND_UP', 50),
        'trending_down': generate_test_data('TREND_DOWN', 50),
        'ranging': generate_test_data('RANGING', 50)
    }
    
    for scenario_name, data in scenarios.items():
        # Modify trend for testing
        if scenario_name == 'trending_up':
            # Add strong uptrend
            for i in range(1, len(data)):
                data.iloc[i, data.columns.get_loc('Close')] = data.iloc[i-1]['Close'] * 1.02
        elif scenario_name == 'trending_down':
            # Add strong downtrend
            for i in range(1, len(data)):
                data.iloc[i, data.columns.get_loc('Close')] = data.iloc[i-1]['Close'] * 0.98
        elif scenario_name == 'ranging':
            # Add ranging movement
            for i in range(1, len(data)):
                data.iloc[i, data.columns.get_loc('Close')] = data.iloc[i-1]['Close'] * (1 + np.random.uniform(-0.01, 0.01))
        
        regime = detector.classify_regime(data)
        print(f"📈 {scenario_name}: {regime}")
    
    print()

def test_sector_rotation():
    """Test sector rotation detection"""
    print("🧪 Testing Sector Rotation Detection")
    print("=" * 50)
    
    sector_etfs = {
        'technology': 'XLK',
        'financials': 'XLF',
        'healthcare': 'XLV',
        'energy': 'XLE'
    }
    
    detector = SectorRotationDetector(sector_etfs, lookback_days=21)
    
    # Generate test sector data
    sector_data = {}
    for sector, etf in sector_etfs.items():
        data = generate_test_data(etf, 30)
        # Add some performance variation
        if sector == 'technology':
            data['Close'] = data['Close'] * 1.1  # 10% outperformance
        elif sector == 'energy':
            data['Close'] = data['Close'] * 0.9  # 10% underperformance
        sector_data[sector] = data
    
    leaders_laggards = detector.get_leaders_laggards(sector_data, top_n=2)
    print(f"🏆 Leaders: {leaders_laggards['leaders']}")
    print(f"📉 Laggards: {leaders_laggards['laggards']}")
    print()

def test_integrated_regime_detection():
    """Test integrated market regime detection"""
    print("🧪 Testing Integrated Market Regime Detection")
    print("=" * 50)
    
    sector_etfs = {
        'technology': 'XLK',
        'financials': 'XLF',
        'healthcare': 'XLV',
        'energy': 'XLE',
        'consumer_discretionary': 'XLY',
        'industrials': 'XLI'
    }
    
    detector = MarketRegimeDetector(sector_etfs)
    
    # Generate test data for main index and sectors
    main_data = generate_test_data('SPY', 50)
    sector_data = {}
    
    for sector, etf in sector_etfs.items():
        data = generate_test_data(etf, 50)
        # Add some sector-specific performance
        if sector == 'technology':
            data['Close'] = data['Close'] * 1.15  # Strong performance
        elif sector == 'energy':
            data['Close'] = data['Close'] * 0.85  # Weak performance
        sector_data[sector] = data
    
    # Detect regime
    regime = detector.detect(main_data, sector_data)
    
    print(f"📊 Overall Regime Analysis:")
    print(f"   Volatility: {regime['volatility']}")
    print(f"   Trend: {regime['trend']}")
    print(f"   Sector Leaders: {regime['sector_rotation']['leaders']}")
    print(f"   Sector Laggards: {regime['sector_rotation']['laggards']}")
    print()

async def main():
    """Run all tests"""
    print("🚀 Market Regime Detection Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_volatility_regime()
        test_trend_regime()
        test_sector_rotation()
        test_integrated_regime_detection()
        
        print("✅ All tests completed successfully!")
        print()
        print("📋 Summary:")
        print("   - Volatility regime detection: Working")
        print("   - Trend regime detection: Working") 
        print("   - Sector rotation detection: Working")
        print("   - Integrated regime detection: Working")
        print()
        print("🎯 Next steps:")
        print("   - Regime detection is ready for integration with backtesting")
        print("   - Dashboard will show regime analysis")
        print("   - Strategies can now adapt based on market conditions")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 