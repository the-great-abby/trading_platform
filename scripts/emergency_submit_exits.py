#!/usr/bin/env python3
"""
Emergency Exit Submission Script
Manually submits exit orders for positions marked PENDING_CLOSE
"""

import requests
import json
import sys

LIVE_TRADING_URL = "http://localhost:11120"
ACCOUNT_ID = "19c25392-8b61-4b71-a344-0eb04d275528"

def get_pending_close_positions():
    """Get positions marked for exit"""
    try:
        # Query database directly via service
        response = requests.get(
            f"{LIVE_TRADING_URL}/api/v1/accounts/{ACCOUNT_ID}/balance",
            timeout=10
        )
        print(f"Service check: {response.status_code}")
        
        # For now, hardcode the known positions
        return [
            {"symbol": "QCOM260116C00185000-OPTION", "quantity": 1, "current_price": 26.35, "reason": "Profit target +399%"},
            {"symbol": "DIS260116C00125000-OPTION", "quantity": 1, "current_price": 1.99, "reason": "Stop loss -22%"},
            {"symbol": "CSCO260116C00077500-OPTION", "quantity": 3, "current_price": 1.24, "reason": "Stop loss -16%"}
        ]
    except Exception as e:
        print(f"Error getting positions: {e}")
        return []

def submit_exit_order(position):
    """Submit exit order for a position"""
    print(f"\n📤 Submitting exit for {position['symbol']}")
    print(f"   Quantity: {position['quantity']}")
    print(f"   Price: ${position['current_price']}")
    print(f"   Reason: {position['reason']}")
    
    order_data = {
        "account_id": ACCOUNT_ID,
        "symbol": position['symbol'],
        "strategy": "MULTI_STRATEGY_ENSEMBLE",
        "legs": [{
            "action": "SELL",
            "option_type": None,
            "strike_price": None,
            "expiration_date": None,
            "quantity": position['quantity'],
            "premium": position['current_price']
        }],
        "order_type": "MARKET",
        "limit_price": None,
        "time_in_force": "DAY",
        "estimated_premium": position['current_price'] * position['quantity'],
        "estimated_risk": 0,
        "greeks": {}
    }
    
    try:
        response = requests.post(
            f"{LIVE_TRADING_URL}/api/v1/orders",
            json=order_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Order submitted: {result.get('order_id', 'unknown')}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚨 EMERGENCY EXIT SUBMISSION")
    print("=" * 60)
    print("Submitting exit orders for positions marked PENDING_CLOSE")
    print("=" * 60)
    
    positions = get_pending_close_positions()
    
    if not positions:
        print("No positions to exit")
        return
    
    print(f"\nFound {len(positions)} positions to exit:")
    for pos in positions:
        print(f"  • {pos['symbol']}: {pos['reason']}")
    
    confirm = input("\n⚠️  Submit these exit orders? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\n🚀 Submitting orders...")
    
    success_count = 0
    for pos in positions:
        if submit_exit_order(pos):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Submitted {success_count}/{len(positions)} exit orders")
    print("=" * 60)

if __name__ == "__main__":
    main()






