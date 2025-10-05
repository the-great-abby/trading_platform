#!/usr/bin/env python3
"""
Elliott Wave Filtering Analysis
==============================

Analyzes whether Elliott Wave filtering is limiting our stock selection
and impacting performance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_data(symbol: str, days: int = 100) -> pd.DataFrame:
    """Create mock market data for testing"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='D')
    
    # Create realistic price data with some volatility
    base_price = 100 if symbol == 'AAPL' else 200 if symbol == 'MSFT' else 150
    prices = []
    current_price = base_price
    
    for i in range(days):
        # Add some random walk with trend
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        current_price *= (1 + change)
        prices.append(current_price)
    
    # Create OHLC data
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': [np.random.randint(1000000, 10000000) for _ in range(days)]
    })
    
    return data

def test_elliott_wave_filtering():
    """Test Elliott Wave filtering behavior"""
    
    print("🏴‍☠️ ELLIOTT WAVE FILTERING ANALYSIS!")
    print("=" * 70)
    print()
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print("📊 TESTING ELLIOTT WAVE FILTERING")
    print("-" * 70)
    
    try:
        from src.strategies.hybrid_ichimoku_strategy import HybridIchimokuStrategy
        
        # Create strategy instance
        strategy = HybridIchimokuStrategy(
            enable_elliott_filtering=True,
            min_pattern_confidence=0.65
        )
        
        print(f"✅ Strategy created successfully")
        print(f"📊 Elliott Wave filtering: {strategy.enable_elliott_filtering}")
        print(f"🎯 Min pattern confidence: {strategy.min_pattern_confidence}")
        print()
        
        # Test each symbol
        symbol_results = {}
        
        for symbol in symbols:
            print(f"🔍 Testing {symbol}:")
            
            # Create mock data
            data = create_mock_data(symbol)
            
            # Test Elliott Wave pattern analysis
            elliott_pattern = strategy._analyze_elliott_wave_patterns(data)
            
            if elliott_pattern:
                pattern_type = elliott_pattern['pattern_type']
                confidence = elliott_pattern['confidence']
                direction = elliott_pattern['direction']
                
                print(f"   📈 Pattern detected: {pattern_type}")
                print(f"   🎯 Confidence: {confidence:.2f}")
                print(f"   📊 Direction: {direction}")
                
                # Test symbol qualification
                is_qualified = strategy._is_symbol_qualified_for_pattern(symbol, pattern_type)
                print(f"   ✅ Qualified: {is_qualified}")
                
                symbol_results[symbol] = {
                    'pattern': pattern_type,
                    'confidence': confidence,
                    'qualified': is_qualified
                }
            else:
                print(f"   ❌ No pattern detected")
                symbol_results[symbol] = {
                    'pattern': None,
                    'confidence': 0,
                    'qualified': False
                }
            
            print()
        
        # Analysis
        print("📊 FILTERING ANALYSIS")
        print("-" * 70)
        
        qualified_symbols = [s for s, r in symbol_results.items() if r['qualified']]
        unqualified_symbols = [s for s, r in symbol_results.items() if not r['qualified']]
        
        print(f"✅ Qualified symbols: {qualified_symbols}")
        print(f"❌ Unqualified symbols: {unqualified_symbols}")
        print(f"📊 Qualification rate: {len(qualified_symbols)}/{len(symbols)} ({len(qualified_symbols)/len(symbols)*100:.1f}%)")
        print()
        
        # Pattern distribution
        pattern_counts = {}
        for result in symbol_results.values():
            pattern = result['pattern']
            if pattern:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        print("📈 PATTERN DISTRIBUTION")
        print("-" * 70)
        for pattern, count in pattern_counts.items():
            print(f"   {pattern}: {count} symbols")
        print()
        
        # Performance impact analysis
        print("🎯 PERFORMANCE IMPACT ANALYSIS")
        print("-" * 70)
        
        if len(qualified_symbols) < len(symbols):
            print(f"⚠️ Elliott Wave filtering is reducing symbol selection!")
            print(f"   • Available symbols: {len(symbols)}")
            print(f"   • Qualified symbols: {len(qualified_symbols)}")
            print(f"   • Reduction: {len(symbols) - len(qualified_symbols)} symbols")
            print(f"   • Impact: {((len(symbols) - len(qualified_symbols)) / len(symbols)) * 100:.1f}% fewer opportunities")
            print()
            
            print("🔍 POTENTIAL CAUSES:")
            print("   1. Pattern performance data not initialized")
            print("   2. Symbol history not available")
            print("   3. Pattern confidence thresholds too high")
            print("   4. Market conditions don't match historical patterns")
            print()
            
            print("🚀 SOLUTIONS:")
            print("   1. Disable Elliott Wave filtering temporarily")
            print("   2. Lower pattern confidence threshold")
            print("   3. Initialize pattern performance data")
            print("   4. Use all symbols regardless of pattern qualification")
            print()
        else:
            print("✅ All symbols are qualified - filtering not limiting selection")
            print()
        
        # Test without filtering
        print("🧪 TESTING WITHOUT ELLIOTT WAVE FILTERING")
        print("-" * 70)
        
        strategy_no_filter = HybridIchimokuStrategy(
            enable_elliott_filtering=False,
            min_pattern_confidence=0.65
        )
        
        print(f"📊 Elliott Wave filtering disabled: {not strategy_no_filter.enable_elliott_filtering}")
        print("✅ This would allow all symbols to be traded")
        print()
        
        return {
            'qualified_symbols': qualified_symbols,
            'unqualified_symbols': unqualified_symbols,
            'pattern_counts': pattern_counts,
            'filtering_impact': len(qualified_symbols) < len(symbols)
        }
        
    except ImportError as e:
        print(f"❌ Could not import strategy: {e}")
        return None
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_performance_impact():
    """Analyze the performance impact of Elliott Wave filtering"""
    
    print("📊 PERFORMANCE IMPACT ANALYSIS")
    print("-" * 70)
    
    # Simulate performance with and without filtering
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    # Mock performance data (based on our backtest results)
    symbol_performance = {
        'AAPL': {'return': 0.15, 'trades': 20},
        'MSFT': {'return': 0.12, 'trades': 18},
        'GOOGL': {'return': 0.08, 'trades': 15},
        'TSLA': {'return': 0.25, 'trades': 25},
        'NVDA': {'return': 0.18, 'trades': 22}
    }
    
    print("📈 SYMBOL PERFORMANCE (Mock Data)")
    print("-" * 70)
    print(f"{'Symbol':<8} {'Return':<10} {'Trades':<8} {'Contribution':<12}")
    print("-" * 70)
    
    total_return_all = 0
    total_trades_all = 0
    
    for symbol in symbols:
        perf = symbol_performance[symbol]
        contribution = perf['return'] * (1/len(symbols))  # Equal weight
        total_return_all += contribution
        total_trades_all += perf['trades']
        
        print(f"{symbol:<8} {perf['return']*100:+7.2f}%   {perf['trades']:6d}   {contribution*100:+8.2f}%")
    
    print("-" * 70)
    print(f"{'TOTAL':<8} {total_return_all*100:+7.2f}%   {total_trades_all:6d}   {total_return_all*100:+8.2f}%")
    print()
    
    # Simulate filtering impact
    print("🔍 FILTERING IMPACT SIMULATION")
    print("-" * 70)
    
    # Scenario 1: Only 2 symbols qualified
    qualified_symbols_1 = ['AAPL', 'TSLA']
    filtered_return_1 = sum(symbol_performance[s]['return'] * (1/len(qualified_symbols_1)) for s in qualified_symbols_1)
    filtered_trades_1 = sum(symbol_performance[s]['trades'] for s in qualified_symbols_1)
    
    print(f"Scenario 1: Only {len(qualified_symbols_1)} symbols qualified")
    print(f"   Qualified: {qualified_symbols_1}")
    print(f"   Return: {filtered_return_1*100:.2f}% (vs {total_return_all*100:.2f}% all symbols)")
    print(f"   Trades: {filtered_trades_1} (vs {total_trades_all} all symbols)")
    print(f"   Impact: {(filtered_return_1/total_return_all - 1)*100:+.1f}% return change")
    print()
    
    # Scenario 2: Only 1 symbol qualified
    qualified_symbols_2 = ['TSLA']
    filtered_return_2 = symbol_performance['TSLA']['return']
    filtered_trades_2 = symbol_performance['TSLA']['trades']
    
    print(f"Scenario 2: Only {len(qualified_symbols_2)} symbol qualified")
    print(f"   Qualified: {qualified_symbols_2}")
    print(f"   Return: {filtered_return_2*100:.2f}% (vs {total_return_all*100:.2f}% all symbols)")
    print(f"   Trades: {filtered_trades_2} (vs {total_trades_all} all symbols)")
    print(f"   Impact: {(filtered_return_2/total_return_all - 1)*100:+.1f}% return change")
    print()
    
    print("🎯 CONCLUSION:")
    print("   Elliott Wave filtering could significantly impact performance by:")
    print("   1. Reducing the number of trading opportunities")
    print("   2. Limiting diversification")
    print("   3. Missing profitable symbols")
    print("   4. Creating concentration risk")
    print()
    
    print("🚀 RECOMMENDATION:")
    print("   Consider disabling Elliott Wave filtering or lowering thresholds")
    print("   to allow more symbols to be traded and improve diversification!")

if __name__ == "__main__":
    # Test Elliott Wave filtering
    results = test_elliott_wave_filtering()
    
    if results and results['filtering_impact']:
        print("⚠️ ELLIOTT WAVE FILTERING IS LIMITING SYMBOL SELECTION!")
        print("   This could be causing our performance decline!")
        print()
    
    # Analyze performance impact
    analyze_performance_impact()





