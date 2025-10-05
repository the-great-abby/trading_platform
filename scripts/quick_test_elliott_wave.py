#!/usr/bin/env python3
"""
Quick Test of Elliott Wave Strategies
"""

import requests
import json

def quick_test_elliott_wave():
    """Quick test of Elliott Wave strategies"""
    
    print("🌊 QUICK TEST: ELLIOTT WAVE STRATEGIES")
    print("=" * 50)
    
    # Test ElliottWaveImpulseStrategy (we know this was working)
    test_payload = {
        'initial_capital': 4000.0,
        'start_date': '2023-01-01',
        'end_date': '2023-02-01',  # 1-month test
        'symbols': ['AAPL'],
        'strategies': ['ElliottWaveImpulseStrategy'],
        'data_source': 'real',
        'use_public_com_pricing': False
    }
    
    try:
        print("🎯 Testing ElliottWaveImpulseStrategy...")
        response = requests.post('http://localhost:11080/api/backtest/run', json=test_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('results') and len(result['results']) > 0:
                backtest_result = result['results'][0]
                trades = backtest_result.get('total_trades', 0)
                return_pct = backtest_result.get('total_return', 0)
                max_dd = backtest_result.get('max_drawdown', 0)
                
                print(f"✅ ElliottWaveImpulseStrategy:")
                print(f"  📊 Trades: {trades}")
                print(f"  📈 Return: {return_pct:.2f}%")
                print(f"  📉 Max DD: {max_dd:.2f}%")
                
                if trades > 0:
                    print("🎉 Elliott Wave strategy is working!")
                    return True
                else:
                    print("❌ Elliott Wave strategy not generating signals")
                    return False
            else:
                print("❌ No results returned")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    quick_test_elliott_wave()

