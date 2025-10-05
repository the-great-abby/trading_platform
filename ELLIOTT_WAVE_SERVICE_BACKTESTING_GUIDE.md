# Elliott Wave Service Backtesting Integration Guide

## Overview

The Elliott Wave service has been modified to support backtesting by accepting historical dates. This allows you to:

1. **Trust the Elliott Wave analysis** - Uses the same service for both live trading and backtesting
2. **Get real pattern detection** - Not simulated patterns
3. **Validate strategy performance** - Test with historical data before live trading

## Key Changes Made

### 1. Modified Elliott Wave Service (`services/elliott-wave-service/main.py`)

**New Functions:**
- `get_market_data_for_backtest()` - Fetches historical data up to a specific date
- Enhanced `analyze_single_symbol()` - Accepts `historical_date` parameter
- New `/elliott-wave/backtest/{symbol}` endpoint - Dedicated backtesting endpoint

**New Endpoint:**
```
GET /elliott-wave/backtest/{symbol}?historical_date=YYYY-MM-DD&timeframe=1d
```

### 2. New Service-Based Strategies (`src/strategies/service_based_elliott_wave_strategy.py`)

**Three new strategy classes:**
- `ServiceBasedElliottWaveStrategy` - General Elliott Wave strategy using the service
- `ServiceBasedElliottWaveImpulseStrategy` - Focuses on impulse patterns
- `ServiceBasedElliottWaveCorrectiveStrategy` - Focuses on corrective patterns

## How to Use for Backtesting

### Step 1: Elliott Wave Service Access

**For Kubernetes-based backtesting (recommended):**
```bash
# The service is already running in the cluster
# Use internal Kubernetes address: http://elliott-wave-service.trading-system.svc.cluster.local:8000
# No port forwarding needed when running from within Kubernetes
```

**For local testing:**
```bash
# Port forward the Elliott Wave service
kubectl port-forward svc/elliott-wave-service 11082:8000 -n trading-system

# Or if running locally
cd services/elliott-wave-service
python main.py
```

### Step 2: Test the Service

**For Kubernetes-based testing:**
```bash
# Run the Kubernetes test script
python test_kubernetes_elliott_wave_service.py
```

**For local testing:**
```bash
# Run the local test script (requires port forwarding)
python test_elliott_wave_service_backtest.py
```

### Step 3: Use in Backtesting

**For Kubernetes-based backtesting (recommended):**
```python
from src.strategies.service_based_elliott_wave_strategy import (
    ServiceBasedElliottWaveImpulseStrategy,
    ServiceBasedElliottWaveCorrectiveStrategy
)

# Strategies automatically use internal Kubernetes address:
# http://elliott-wave-service.trading-system.svc.cluster.local:8000
strategies = [
    'ServiceBasedElliottWaveImpulseStrategy',
    'ServiceBasedElliottWaveCorrectiveStrategy'
]

# Run backtest with real Elliott Wave analysis
results = await engine.run_backtest(
    symbols=['SPY', 'QQQ'],
    start_date='2023-01-01',
    end_date='2023-12-31',
    strategies=strategies
)
```

**For local backtesting:**
```python
# Create strategies with local service URL
strategies = [
    ServiceBasedElliottWaveImpulseStrategy(
        service_url="http://localhost:11082"
    ),
    ServiceBasedElliottWaveCorrectiveStrategy(
        service_url="http://localhost:11082"
    )
]
```

## API Endpoints

### Live Trading Endpoint
```
GET /elliott-wave/analyze/{symbol}?timeframe=1d
```

**Response:**
```json
{
    "symbol": "SPY",
    "pattern_found": true,
    "pattern_type": "impulse",
    "confidence": 0.75,
    "waves": [...],
    "fibonacci_levels": [...],
    "target_price": 450.0,
    "invalidation_level": 420.0,
    "analysis_time": 0.123
}
```

### Backtesting Endpoint
```
GET /elliott-wave/backtest/{symbol}?historical_date=2023-06-15&timeframe=1d
```

**Response:**
```json
{
    "symbol": "SPY",
    "pattern_found": true,
    "pattern_type": "impulse",
    "confidence": 0.75,
    "waves": [...],
    "fibonacci_levels": [...],
    "target_price": 450.0,
    "invalidation_level": 420.0,
    "analysis_time": 0.123,
    "historical_date": "2023-06-15",
    "backtest_mode": true,
    "data_points": 250,
    "swing_points": 12
}
```

## Strategy Configuration

### Service-Based Elliott Wave Impulse Strategy

```python
strategy = ServiceBasedElliottWaveImpulseStrategy(
    name="ServiceBasedElliottWaveImpulseStrategy",
    service_url="http://elliott-wave-service.trading-system.svc.cluster.local:8000",  # Internal Kubernetes service URL
    confidence_threshold=0.7,  # Higher threshold for impulse patterns
)
```

**Features:**
- Only trades impulse patterns
- Higher confidence threshold (0.7)
- Conservative position sizing (3% max capital)
- Uses real Elliott Wave service analysis

### Service-Based Elliott Wave Corrective Strategy

```python
strategy = ServiceBasedElliottWaveCorrectiveStrategy(
    name="ServiceBasedElliottWaveCorrectiveStrategy",
    service_url="http://elliott-wave-service.trading-system.svc.cluster.local:8000",  # Internal Kubernetes service URL
    confidence_threshold=0.6,  # Lower threshold for corrective patterns
)
```

**Features:**
- Only trades corrective patterns
- Lower confidence threshold (0.6)
- Moderate position sizing (4% max capital)
- Uses real Elliott Wave service analysis

## Benefits of This Approach

### 1. **Trust and Validation**
- Same analysis logic for live trading and backtesting
- Real pattern detection, not simulated
- Can validate strategy performance historically

### 2. **Consistency**
- Identical Elliott Wave analysis across environments
- Same confidence scoring
- Same pattern recognition logic

### 3. **Flexibility**
- Can test different historical periods
- Can adjust confidence thresholds
- Can test different timeframes

### 4. **Real-World Testing**
- Tests with actual market data
- Tests with real pattern detection
- Tests with actual service performance

### 5. **Kubernetes Integration**
- **Internal service communication** - No port forwarding needed
- **Scalable architecture** - Service can be scaled independently
- **Production-ready** - Same network topology as live trading
- **Service discovery** - Automatic DNS resolution within cluster
- **Security** - Internal cluster communication

## Example Backtesting Results

```python
# Example output from service-based strategy
{
    "symbol": "SPY",
    "action": "BUY",
    "quantity": 5,
    "price": 425.50,
    "confidence": 0.75,
    "metadata": {
        "pattern_type": "impulse",
        "target_price": 450.0,
        "invalidation_level": 420.0,
        "fibonacci_levels": [0.236, 0.382, 0.618],
        "waves_count": 5,
        "backtest_mode": true,
        "service_analysis": {...}
    }
}
```

## Troubleshooting

### Service Not Available
```bash
# Check if service is running
kubectl get pods -l app=elliott-wave-service

# Port forward if needed
kubectl port-forward svc/elliott-wave-service 11082:8000
```

### No Patterns Found
- Check if market data is available for the historical date
- Verify the symbol is tracked (`SPY`, `QQQ`, `AAPL`)
- Check if there are sufficient swing points (minimum 5)

### Low Confidence
- Adjust confidence threshold in strategy configuration
- Check if the pattern detection is working correctly
- Verify market data quality

## Next Steps

1. **Test the service** with the provided test script
2. **Run backtests** with the service-based strategies
3. **Compare results** with simulated strategies
4. **Adjust parameters** based on backtesting results
5. **Deploy to live trading** with confidence

This approach ensures that your Elliott Wave strategies are tested with the same analysis logic that will be used in live trading, providing much higher confidence in the strategy's performance.
