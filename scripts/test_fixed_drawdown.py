#!/usr/bin/env python3
"""
Test Fixed Drawdown Calculation
"""

import requests
import json

def test_fixed_drawdown():
    """Test with fixed drawdown calculation"""
    
    payload = {
        'initial_capital': 4000.0,
        'start_date': '2023-01-01',
        'end_date': '2023-06-01',
        'symbols': ['AAPL'],
        'strategies': ['BollingerBandsStrategy'],
        'data_source': 'real',
        'use_public_com_pricing': False
    }
    
    print("🔧 Testing with FIXED drawdown calculation...")
    try:
        response = requests.post('http://localhost:11080/api/backtest/run', json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('results') and len(result['results']) > 0:
                backtest_result = result['results'][0]
                trades = backtest_result.get('total_trades', 0)
                return_pct = backtest_result.get('total_return', 0)
                sharpe = backtest_result.get('sharpe_ratio', 0)
                max_dd = backtest_result.get('max_drawdown', 0)
                win_rate = backtest_result.get('win_rate', 0)
                
                print("✅ FIXED RESULTS:")
                print(f"  Return: {return_pct:.2f}%")
                print(f"  Trades: {trades}")
                print(f"  Sharpe: {sharpe:.2f}")
                print(f"  Max DD: {max_dd:.2f}%")
                print(f"  Win Rate: {win_rate:.1f}%")
                
                # Calculate actual dollar amounts
                final_value = 4000 * (1 + return_pct/100)
                max_loss = 4000 * (max_dd/100)
                
                print("\n💰 DOLLAR IMPACT ON $4,000 ACCOUNT:")
                print(f"  Final Value: ${final_value:.2f}")
                print(f"  Profit/Loss: ${final_value - 4000:.2f}")
                print(f"  Max Drawdown: ${max_loss:.2f}")
                
                if max_dd < 20:  # Less than 20% drawdown
                    print("\n✅ ACCEPTABLE RISK for $4,000 account")
                else:
                    print("\n❌ STILL TOO RISKY for $4,000 account")
                    
            else:
                print("❌ No results returned")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_fixed_drawdown()

