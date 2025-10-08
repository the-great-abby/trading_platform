#!/usr/bin/env python3
"""
Test Elliott Wave Service Integration for Backtesting

This script demonstrates how to call the Elliott Wave service directly
for backtesting using Option 2 (direct service calls).
"""

import requests
import asyncio
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service configuration
ELLIOTT_SERVICE_URL = "http://localhost:11082"  # Port-forwarded address
TRACKED_SYMBOLS = ["SPY", "QQQ", "AAPL"]

async def test_elliott_wave_service_integration():
    """Test Elliott Wave service integration for backtesting"""
    
    print("🎯 ELLIOTT WAVE SERVICE INTEGRATION TEST")
    print("=" * 60)
    print(f"📡 Service URL: {ELLIOTT_SERVICE_URL}")
    print(f"📊 Symbols: {', '.join(TRACKED_SYMBOLS)}")
    print()
    
    # Test dates for backtesting
    test_dates = [
        "2023-01-15",  # January 2023
        "2023-06-15",  # June 2023
        "2023-12-15",  # December 2023
    ]
    
    print("🔍 Testing Elliott Wave Service for Backtesting")
    print("-" * 50)
    
    all_results = []
    
    for test_date in test_dates:
        print(f"📅 Historical date: {test_date}")
        
        for symbol in TRACKED_SYMBOLS:
            try:
                # Call the Elliott Wave service backtesting endpoint
                url = f"{ELLIOTT_SERVICE_URL}/elliott-wave/backtest/{symbol}"
                params = {
                    "historical_date": test_date,
                    "timeframe": "1d"
                }
                
                print(f"   🔍 Analyzing {symbol} for {test_date}...")
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                # Store result for analysis
                result['symbol'] = symbol
                result['test_date'] = test_date
                all_results.append(result)
                
                if result.get("pattern_found", False):
                    pattern_type = result.get("pattern_type", "unknown")
                    confidence = result.get("confidence", 0.0)
                    data_points = result.get("data_points", 0)
                    swing_points = result.get("swing_points", 0)
                    
                    print(f"      ✅ Pattern found: {pattern_type}")
                    print(f"      📊 Confidence: {confidence:.2f}")
                    print(f"      📈 Data points: {data_points}")
                    print(f"      🌊 Swing points: {swing_points}")
                    
                    if result.get("target_price"):
                        print(f"      🎯 Target price: ${result.get('target_price', 0):.2f}")
                    if result.get("invalidation_level"):
                        print(f"      🛑 Invalidation level: ${result.get('invalidation_level', 0):.2f}")
                else:
                    message = result.get("message", "No pattern detected")
                    data_points = result.get("data_points", 0)
                    swing_points = result.get("swing_points", 0)
                    
                    print(f"      ❌ No pattern: {message}")
                    print(f"      📈 Data points: {data_points}")
                    print(f"      🌊 Swing points: {swing_points}")
                
                analysis_time = result.get("analysis_time", 0)
                print(f"      ⏱️  Analysis time: {analysis_time:.3f}s")
                
            except requests.exceptions.RequestException as e:
                print(f"      ❌ Error calling service for {symbol}: {e}")
            except Exception as e:
                print(f"      ❌ Unexpected error for {symbol}: {e}")
        
        print()
    
    # Analyze results
    print("📊 ELLIOTT WAVE SERVICE ANALYSIS")
    print("=" * 40)
    
    patterns_found = [r for r in all_results if r.get("pattern_found", False)]
    total_tests = len(all_results)
    
    print(f"📈 Total tests: {total_tests}")
    print(f"✅ Patterns found: {len(patterns_found)}")
    print(f"📊 Success rate: {len(patterns_found)/total_tests*100:.1f}%")
    
    if patterns_found:
        print()
        print("🎯 Pattern Types Found:")
        pattern_types = {}
        for result in patterns_found:
            pattern_type = result.get("pattern_type", "unknown")
            pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
        
        for pattern_type, count in pattern_types.items():
            print(f"   📊 {pattern_type}: {count}")
        
        print()
        print("📊 Confidence Distribution:")
        confidences = [r.get("confidence", 0.0) for r in patterns_found]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        print(f"   📊 Average confidence: {avg_confidence:.2f}")
        print(f"   📊 Min confidence: {min_confidence:.2f}")
        print(f"   📊 Max confidence: {max_confidence:.2f}")
    
    print()
    print("🎉 Elliott Wave service integration test completed!")
    
    return all_results

async def demonstrate_trading_signals():
    """Demonstrate how to generate trading signals from Elliott Wave analysis"""
    
    print("🎯 ELLIOTT WAVE TRADING SIGNAL DEMONSTRATION")
    print("=" * 60)
    
    # Test with a specific date and symbol
    symbol = "SPY"
    test_date = "2023-06-15"
    
    try:
        # Get Elliott Wave analysis
        url = f"{ELLIOTT_SERVICE_URL}/elliott-wave/backtest/{symbol}"
        params = {
            "historical_date": test_date,
            "timeframe": "1d"
        }
        
        print(f"🔍 Getting Elliott Wave analysis for {symbol} on {test_date}...")
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("pattern_found", False):
            pattern_type = result.get("pattern_type", "unknown")
            confidence = result.get("confidence", 0.0)
            target_price = result.get("target_price", 0.0)
            invalidation_level = result.get("invalidation_level", 0.0)
            
            print(f"✅ Pattern found: {pattern_type}")
            print(f"📊 Confidence: {confidence:.2f}")
            print(f"🎯 Target price: ${target_price:.2f}")
            print(f"🛑 Invalidation level: ${invalidation_level:.2f}")
            print()
            
            # Generate trading signal based on Elliott Wave analysis
            print("🎯 TRADING SIGNAL GENERATION:")
            print("-" * 30)
            
            # Assume current price (this would come from market data in real usage)
            current_price = 420.0  # Example current price
            
            if 'impulse' in pattern_type.lower():
                # Impulse patterns suggest trend continuation
                if target_price > current_price:
                    action = "BUY"
                    signal_strength = confidence
                    stop_loss = invalidation_level
                    take_profit = target_price
                else:
                    action = "SELL"
                    signal_strength = confidence
                    stop_loss = invalidation_level
                    take_profit = target_price
                    
                print(f"📈 Action: {action}")
                print(f"💰 Current Price: ${current_price:.2f}")
                print(f"🎯 Take Profit: ${take_profit:.2f}")
                print(f"🛑 Stop Loss: ${stop_loss:.2f}")
                print(f"📊 Signal Strength: {signal_strength:.2f}")
                
            elif 'corrective' in pattern_type.lower():
                # Corrective patterns suggest reversal
                if invalidation_level > current_price:
                    action = "SELL"  # Expecting downward correction
                    signal_strength = confidence
                    stop_loss = invalidation_level
                    take_profit = target_price
                else:
                    action = "BUY"   # Expecting upward correction
                    signal_strength = confidence
                    stop_loss = invalidation_level
                    take_profit = target_price
                    
                print(f"📈 Action: {action}")
                print(f"💰 Current Price: ${current_price:.2f}")
                print(f"🎯 Take Profit: ${take_profit:.2f}")
                print(f"🛑 Stop Loss: ${stop_loss:.2f}")
                print(f"📊 Signal Strength: {signal_strength:.2f}")
            
            # Position sizing example
            print()
            print("💰 POSITION SIZING EXAMPLE:")
            print("-" * 30)
            
            capital = 1000.0  # $1000 position
            risk_percentage = 0.02  # 2% risk
            
            if action == "BUY":
                risk_amount = capital * risk_percentage
                price_diff = current_price - stop_loss
                if price_diff > 0:
                    position_size = risk_amount / price_diff
                    print(f"💰 Capital: ${capital:.2f}")
                    print(f"⚠️  Risk: {risk_percentage*100:.1f}% (${risk_amount:.2f})")
                    print(f"📊 Position Size: {position_size:.2f} shares")
                    print(f"💵 Total Position Value: ${current_price * position_size:.2f}")
            else:
                risk_amount = capital * risk_percentage
                price_diff = stop_loss - current_price
                if price_diff > 0:
                    position_size = risk_amount / price_diff
                    print(f"💰 Capital: ${capital:.2f}")
                    print(f"⚠️  Risk: {risk_percentage*100:.1f}% (${risk_amount:.2f})")
                    print(f"📊 Position Size: {position_size:.2f} shares")
                    print(f"💵 Total Position Value: ${current_price * position_size:.2f}")
        
        else:
            print(f"❌ No pattern found: {result.get('message', 'No pattern')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main function"""
    
    print("🚀 ELLIOTT WAVE SERVICE INTEGRATION TEST SUITE")
    print("=" * 70)
    print("📊 Option 2: Direct Service Calls for Backtesting")
    print()
    
    # Test service integration
    results = await test_elliott_wave_service_integration()
    print()
    
    # Demonstrate trading signal generation
    await demonstrate_trading_signals()
    
    print()
    print("🎉 All tests completed!")
    print()
    print("💡 Next Steps:")
    print("   1. Integrate this service calling logic into your backtesting engine")
    print("   2. Use the trading signal generation logic in your strategies")
    print("   3. Test with different symbols and timeframes")
    print("   4. Adjust confidence thresholds based on results")

if __name__ == "__main__":
    asyncio.run(main())

