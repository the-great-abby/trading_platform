#!/usr/bin/env python3
"""
Test script for various order types and portfolio notifications
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:11080"

def test_order_type(order_data, description):
    """Test a specific order type"""
    print(f"\n🧪 Testing: {description}")
    print(f"Order: {json.dumps(order_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/trading/test/orders",
            json=order_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'Order processed')}")
            print(f"Order ID: {result.get('order_id', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_portfolio_operations():
    """Test portfolio-related operations"""
    print(f"\n📊 Testing Portfolio Operations")
    
    # Test getting portfolio
    try:
        response = requests.get(f"{API_BASE}/api/trading/test/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            print(f"✅ Portfolio retrieved: {json.dumps(portfolio, indent=2)}")
        else:
            print(f"❌ Portfolio error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Portfolio exception: {e}")

def main():
    print("🚀 Testing Various Order Types and Portfolio Operations")
    print("=" * 60)
    
    # Test different order types
    order_tests = [
        {
            "data": {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "order_type": "market",
                "time_in_force": "GTC"
            },
            "description": "Market Buy Order (100 AAPL)"
        },
        {
            "data": {
                "symbol": "TSLA",
                "side": "sell",
                "quantity": 50,
                "order_type": "limit",
                "price": 250.00,
                "time_in_force": "GTC"
            },
            "description": "Limit Sell Order (50 TSLA @ $250)"
        },
        {
            "data": {
                "symbol": "MSFT",
                "side": "buy",
                "quantity": 25,
                "order_type": "limit",
                "price": 300.00,
                "time_in_force": "IOC"
            },
            "description": "Immediate or Cancel Buy Order (25 MSFT @ $300)"
        },
        {
            "data": {
                "symbol": "GOOGL",
                "side": "sell",
                "quantity": 10,
                "order_type": "limit",
                "price": 2800.00,
                "time_in_force": "FOK"
            },
            "description": "Fill or Kill Sell Order (10 GOOGL @ $2800)"
        },
        {
            "data": {
                "symbol": "NVDA",
                "side": "buy",
                "quantity": 5,
                "order_type": "market",
                "time_in_force": "DAY"
            },
            "description": "Day Market Buy Order (5 NVDA)"
        },
        {
            "data": {
                "symbol": "AMZN",
                "side": "sell",
                "quantity": 15,
                "order_type": "limit",
                "price": 3200.00,
                "time_in_force": "GTC"
            },
            "description": "Large Limit Sell Order (15 AMZN @ $3200)"
        }
    ]
    
    # Execute order tests
    successful_orders = []
    for test in order_tests:
        result = test_order_type(test["data"], test["description"])
        if result and result.get("success"):
            successful_orders.append(result.get("order_id"))
        time.sleep(1)  # Small delay between orders
    
    # Test portfolio operations
    test_portfolio_operations()
    
    # Test getting all orders
    print(f"\n📋 Testing Order Retrieval")
    try:
        response = requests.get(f"{API_BASE}/api/trading/test/orders")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Retrieved {len(orders.get('orders', []))} orders")
            for order in orders.get('orders', [])[:3]:  # Show first 3
                print(f"  - {order.get('order_id')}: {order.get('side')} {order.get('quantity')} {order.get('symbol')} @ {order.get('order_type')}")
        else:
            print(f"❌ Orders retrieval error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Orders retrieval exception: {e}")
    
    print(f"\n🎯 Test Summary:")
    print(f"  - Orders placed: {len(successful_orders)}")
    print(f"  - Check Discord for notifications!")
    print(f"  - Check API logs for detailed processing")

if __name__ == "__main__":
    main()
