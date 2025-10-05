#!/usr/bin/env python3
"""
Test Elliott Wave and Ichimoku Strategies
"""

import requests
import json

def test_elliott_wave_ichimoku():
    """Test Elliott Wave and Ichimoku strategies"""
    
    print("🌊 TESTING ELLIOTT WAVE AND ICHIMOKU STRATEGIES")
    print("=" * 70)
    print("Testing Strategies:")
    print("✅ ElliottWaveImpulseStrategy")
    print("✅ ElliottWaveCorrectiveStrategy") 
    print("✅ IchimokuStrategy")
    print("✅ HybridIchimokuStrategy")
    print("=" * 70)
    
    strategies_to_test = [
        "ElliottWaveImpulseStrategy",
        "ElliottWaveCorrectiveStrategy", 
        "IchimokuStrategy",
        "HybridIchimokuStrategy"
    ]
    
    test_payload = {
        'initial_capital': 4000.0,
        'start_date': '2023-01-01',
        'end_date': '2023-03-01',  # 2-month test
        'symbols': ['AAPL'],
        'data_source': 'real',
        'use_public_com_pricing': False
    }
    
    results = {}
    
    for strategy in strategies_to_test:
        print(f"\n🎯 Testing {strategy}...")
        
        test_payload['strategies'] = [strategy]
        
        try:
            response = requests.post('http://localhost:11080/api/backtest/run', json=test_payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if result.get('results') and len(result['results']) > 0:
                    backtest_result = result['results'][0]
                    trades = backtest_result.get('total_trades', 0)
                    return_pct = backtest_result.get('total_return', 0)
                    sharpe = backtest_result.get('sharpe_ratio', 0)
                    max_dd = backtest_result.get('max_drawdown', 0)
                    win_rate = backtest_result.get('win_rate', 0)
                    
                    results[strategy] = {
                        'trades': trades,
                        'return': return_pct,
                        'sharpe': sharpe,
                        'max_dd': max_dd,
                        'win_rate': win_rate,
                        'status': 'working' if trades > 0 else 'no_signals'
                    }
                    
                    print(f"  📊 Trades: {trades}")
                    print(f"  📈 Return: {return_pct:.2f}%")
                    print(f"  📉 Sharpe: {sharpe:.2f}")
                    print(f"  📉 Max DD: {max_dd:.2f}%")
                    print(f"  🎯 Win Rate: {win_rate:.1f}%")
                    
                    if trades > 0:
                        print(f"  ✅ {strategy} is generating signals!")
                    else:
                        print(f"  ❌ {strategy} is NOT generating signals")
                        
                else:
                    results[strategy] = {'status': 'no_results'}
                    print(f"  ❌ No results returned for {strategy}")
            else:
                results[strategy] = {'status': 'http_error', 'code': response.status_code}
                print(f"  ❌ HTTP Error {response.status_code} for {strategy}")
        except Exception as e:
            results[strategy] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Error testing {strategy}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("📊 ELLIOTT WAVE & ICHIMOKU STRATEGY SUMMARY:")
    print("=" * 70)
    
    working_strategies = []
    non_working_strategies = []
    
    for strategy, result in results.items():
        if result.get('status') == 'working':
            working_strategies.append(strategy)
            print(f"✅ {strategy}: {result['trades']} trades, {result['return']:.2f}% return")
        else:
            non_working_strategies.append(strategy)
            print(f"❌ {strategy}: {result.get('status', 'unknown')}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"  Working Strategies: {len(working_strategies)}")
    print(f"  Non-Working Strategies: {len(non_working_strategies)}")
    
    if working_strategies:
        print(f"\n✅ SUCCESS: {len(working_strategies)} strategies are working!")
        print("🎉 Elliott Wave and Ichimoku strategies are generating signals!")
    else:
        print(f"\n❌ ISSUE: No strategies are generating signals")
        print("🔧 Elliott Wave and Ichimoku strategies need debugging")

if __name__ == "__main__":
    test_elliott_wave_ichimoku()

