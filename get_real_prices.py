#!/usr/bin/env python3
"""
Script to get real market prices and update the order entry form
"""

import subprocess
import json
import time

def get_real_price(symbol):
    """Get real price from market data service"""
    try:
        cmd = [
            'kubectl', 'exec', '-n', 'trading-system', 
            'market-data-service-584dc49d4d-th7jv', '--', 
            'curl', '-s', f'http://localhost:8000/market-data/current/{symbol.upper()}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return data.get('price')
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
    
    return None

def main():
    """Get real prices for common symbols"""
    symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'SPY', 'QQQ']
    
    print("🎯 Getting REAL market prices...")
    print("=" * 50)
    
    real_prices = {}
    
    for symbol in symbols:
        price = get_real_price(symbol)
        if price:
            real_prices[symbol] = price
            print(f"✅ {symbol}: ${price}")
        else:
            print(f"❌ {symbol}: Could not get real price")
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print("📊 REAL MARKET PRICES SUMMARY:")
    for symbol, price in real_prices.items():
        print(f"  {symbol}: ${price}")
    
    print(f"\n✅ Got {len(real_prices)} real prices out of {len(symbols)} symbols")
    
    return real_prices

if __name__ == "__main__":
    main() 