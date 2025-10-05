#!/usr/bin/env python3
"""
Test Ultra-Conservative Risk Settings for $4,000 Account
"""

import requests
import json

def test_ultra_conservative_settings():
    """Test with ultra-conservative settings for $4,000 account"""
    
    print("🛡️ TESTING ULTRA-CONSERVATIVE RISK SETTINGS FOR $4,000 ACCOUNT")
    print("=" * 70)
    print("Ultra-Conservative Risk Parameters:")
    print("✅ Account Size: $4,000")
    print("✅ Max Position Size: 2% ($80)")
    print("✅ Max Risk Per Trade: 0.5% ($20)")
    print("✅ Max Portfolio Risk: 10% ($400)")
    print("✅ Stop Loss: 2% per trade")
    print("✅ Take Profit: 4% per trade")
    print("✅ Maximum positions: 2")
    print("=" * 70)
    
    # Test with ULTRA-CONSERVATIVE settings for $4,000 account
    ultra_conservative_payload = {
        'initial_capital': 4000.0,  # $4,000 account
        'start_date': '2023-01-01',
        'end_date': '2023-03-01',  # 2-month test for safety
        'symbols': ['AAPL'],  # Single symbol for safety
        'strategies': ['BollingerBandsStrategy'],  # Only the safest strategy
        'data_source': 'real',
        'use_public_com_pricing': False,
        # ULTRA-CONSERVATIVE risk management
        'max_position_size': 0.02,  # Only 2% per position ($80 max)
        'max_risk_per_trade': 0.005,  # Only 0.5% risk per trade ($20 max loss)
        'max_portfolio_utilization': 0.10,  # Only 10% of capital at risk ($400 max)
        'stop_loss_pct': 0.02,  # 2% stop loss
        'take_profit_pct': 0.04  # 4% take profit
    }
    
    try:
        response = requests.post('http://localhost:11080/api/backtest/run', json=ultra_conservative_payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('results') and len(result['results']) > 0:
                backtest_result = result['results'][0]
                trades = backtest_result.get('total_trades', 0)
                return_pct = backtest_result.get('total_return', 0)
                sharpe = backtest_result.get('sharpe_ratio', 0)
                max_dd = backtest_result.get('max_drawdown', 0)
                win_rate = backtest_result.get('win_rate', 0)
                
                print("\n📊 ULTRA-CONSERVATIVE RESULTS:")
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
                
                # Risk assessment
                if max_dd < 5:  # Less than 5% drawdown
                    print("\n✅ EXCELLENT RISK MANAGEMENT for $4,000 account")
                    print("🎉 Ultra-conservative settings are working!")
                elif max_dd < 10:  # Less than 10% drawdown
                    print("\n✅ GOOD RISK MANAGEMENT for $4,000 account")
                    print("✅ Conservative settings are working well")
                elif max_dd < 20:  # Less than 20% drawdown
                    print("\n⚠️ ACCEPTABLE RISK for $4,000 account")
                    print("🔧 Risk management needs further tuning")
                else:
                    print("\n❌ STILL TOO RISKY for $4,000 account")
                    print("🚨 Risk management is not working properly")
                    
            else:
                print("❌ No results returned")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_ultra_conservative_settings()

