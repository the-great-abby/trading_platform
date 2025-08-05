#!/usr/bin/env python3
"""
Simple script to get real market data
"""

import subprocess
import json
import sys

def get_real_market_data(symbol):
    """Get real market data directly from the working service"""
    try:
        cmd = [
            'kubectl', 'exec', '-n', 'trading-system', 
            'market-data-service-584dc49d4d-bl6tf', '--', 
            'curl', '-s', f'http://localhost:8000/market-data/current/{symbol.upper()}'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            print(f"✅ REAL market data for {symbol}: {data}")
            return data
        else:
            print(f"❌ Failed to get market data: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    data = get_real_market_data(symbol)
    
    if data:
        print(f"\n🎯 REAL MARKET DATA:")
        print(f"Symbol: {data.get('symbol')}")
        print(f"Price: ${data.get('price')}")
        print(f"Timestamp: {data.get('timestamp')}")
    else:
        print(f"\n❌ Could not get market data for {symbol}") 