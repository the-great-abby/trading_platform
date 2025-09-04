#!/usr/bin/env python3
"""
Test script to verify technical indicator calculations
"""

import json
import requests
from typing import List, Dict, Any

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI"""
    if len(prices) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return prices[-1]
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema

def calculate_macd(prices: List[float]) -> Dict[str, float]:
    """Calculate MACD"""
    if len(prices) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    # Calculate EMA12 and EMA26
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    macd = ema12 - ema26
    
    # Calculate signal line (EMA of MACD)
    macd_values = [macd]  # Simplified - in real implementation you'd track MACD values
    signal = calculate_ema(macd_values, 9)
    
    histogram = macd - signal
    
    return {
        "macd": macd,
        "signal": signal,
        "histogram": histogram
    }

def calculate_technical_indicators(historical_data: List[Dict]) -> Dict[str, Any]:
    """Calculate technical indicators from historical data"""
    if not historical_data or len(historical_data) < 20:
        return {}
    
    # Extract close prices and volumes from the historical data
    prices = [float(d["close"]) for d in historical_data]
    volumes = [int(d["volume"]) for d in historical_data]
    
    print(f"Processing {len(prices)} data points")
    print(f"Price range: {min(prices):.2f} - {max(prices):.2f}")
    print(f"Volume range: {min(volumes):,} - {max(volumes):,}")
    
    # Calculate RSI
    rsi = calculate_rsi(prices, 14)
    
    # Calculate MACD
    macd_data = calculate_macd(prices)
    
    # Calculate Moving Averages
    sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
    sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else prices[-1]
    
    # Calculate volume SMA
    volume_sma = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
    
    return {
        "rsi": round(rsi, 1),
        "macd": {
            "value": round(macd_data["macd"], 3),
            "signal": round(macd_data["signal"], 3),
            "histogram": round(macd_data["histogram"], 3)
        },
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "volume_sma": round(volume_sma, 0),
        "price_trend": "bullish" if sma_20 > sma_50 else "bearish"
    }

def test_with_real_data():
    """Test with real data from the market data service"""
    try:
        # Get historical data for NVDA
        response = requests.post(
            "http://localhost:11084/market-data/historical",
            json={
                "symbol": "NVDA",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data.get('data', []))} data points")
            
            if data.get("data") and len(data["data"]) >= 20:
                result = calculate_technical_indicators(data["data"])
                print("\nTechnical Indicators:")
                print(json.dumps(result, indent=2))
            else:
                print("Insufficient data points")
        else:
            print(f"Failed to get data: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_with_real_data() 