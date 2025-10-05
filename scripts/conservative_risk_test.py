#!/usr/bin/env python3
"""
Conservative Risk Management Test for $4,000 Account
"""

import requests
import json

def test_conservative_risk_management():
    """Test with conservative risk management for $4,000 account"""
    
    print("🛡️ TESTING CONSERVATIVE RISK MANAGEMENT FOR $4,000 ACCOUNT")
    print("=" * 70)
    print("Risk Parameters:")
    print("  Account Size: $4,000")
    print("  Max Position Size: 5% ($200)")
    print("  Max Risk Per Trade: 1% ($40)")
    print("  Max Portfolio Risk: 20% ($800)")
    print("  Stop Loss: 5%")
    print("  Take Profit: 10%")
    print("=" * 70)
    
    # Test with CONSERVATIVE risk management for $4,000 account
    conservative_payload = {
        'initial_capital': 4000.0,  # $4,000 account
        'start_date': '2023-01-01',
        'end_date': '2023-06-01',  # 6-month test first
        'symbols': ['AAPL'],  # Single symbol for safety
        'strategies': ['BollingerBandsStrategy'],  # Only the safest strategy
        'data_source': 'real',
        'use_public_com_pricing': False,
        # CONSERVATIVE risk management
        'max_position_size': 0.05,  # Only 5% per position ($200 max)
        'max_risk_per_trade': 0.01,  # Only 1% risk per trade ($40 max loss)
        'max_portfolio_utilization': 0.20,  # Only 20% of capital at risk ($800 max)
        'stop_loss_pct': 0.05,  # 5% stop loss
        'take_profit_pct': 0.10  # 10% take profit
    }
    
    try:
        response = requests.post('http://localhost:11080/api/backtest/run', json=conservative_payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('results') and len(result['results']) > 0:
                backtest_result = result['results'][0]
                trades = backtest_result.get('total_trades', 0)
                return_pct = backtest_result.get('total_return', 0)
                sharpe = backtest_result.get('sharpe_ratio', 0)
                max_dd = backtest_result.get('max_drawdown', 0)
                win_rate = backtest_result.get('win_rate', 0)
                
                print("\n📊 CONSERVATIVE RESULTS:")
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
                    print("\n❌ TOO RISKY for $4,000 account")
                    
            else:
                print("❌ No results returned")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_conservative_risk_management()

