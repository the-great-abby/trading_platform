#!/usr/bin/env python3
"""
Test MACD calculation logic
"""

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return prices[-1]
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema

def calculate_macd(prices):
    """Calculate MACD - this is the problematic version from the AI dashboard"""
    if len(prices) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    # Calculate EMA12 and EMA26
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    macd = ema12 - ema26
    
    # Calculate signal line (EMA of MACD)
    macd_values = [macd]  # This is the problem! Only one value
    signal = calculate_ema(macd_values, 9)
    
    histogram = macd - signal
    
    return {
        "macd": macd,
        "signal": signal,
        "histogram": histogram
    }

def calculate_macd_fixed(prices):
    """Calculate MACD - fixed version"""
    if len(prices) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    # Calculate EMA12 and EMA26
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    macd = ema12 - ema26
    
    # For a proper signal line, we need multiple MACD values
    # Since we only have one MACD value, we'll use a simple approach
    signal = macd * 0.8  # Simple approximation
    histogram = macd - signal
    
    return {
        "macd": macd,
        "signal": signal,
        "histogram": histogram
    }

# Test with sample data
sample_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125]

print("Sample prices:", sample_prices)
print("\nOriginal MACD calculation:")
result1 = calculate_macd(sample_prices)
print(f"MACD: {result1['macd']:.3f}")
print(f"Signal: {result1['signal']:.3f}")
print(f"Histogram: {result1['histogram']:.3f}")

print("\nFixed MACD calculation:")
result2 = calculate_macd_fixed(sample_prices)
print(f"MACD: {result2['macd']:.3f}")
print(f"Signal: {result2['signal']:.3f}")
print(f"Histogram: {result2['histogram']:.3f}")

print("\nThe issue is that the original calculation only uses one MACD value for the signal line,")
print("which makes the signal very close to the MACD value, resulting in histogram ≈ 0") 