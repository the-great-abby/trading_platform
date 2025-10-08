# Strategy Engine Testing Framework - Quickstart Guide

**Feature**: Strategy Engine Testing Framework  
**Date**: 2025-01-01  
**Status**: Ready for Implementation

## Overview

This quickstart guide demonstrates how to use the Strategy Engine Testing Framework to validate trading strategies, with a focus on Elliott Wave, Adaptive Wave, Ichimoku, and other advanced strategies.

## Prerequisites

- Trading system running with strategy service accessible
- Python 3.11+ environment
- Access to the testing API endpoints
- Basic understanding of trading strategies

## Quick Start Examples

### 1. List Available Strategies

First, let's see what strategies are available for testing:

```bash
curl -X GET "http://localhost:11080/api/testing/strategies" \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "strategies": [
    {
      "name": "ElliottWaveImpulseStrategy",
      "category": "advanced",
      "description": "Elliott Wave Impulse Pattern Strategy",
      "is_active": true,
      "test_coverage": 85.5
    },
    {
      "name": "AdaptiveSectorWaveStrategy", 
      "category": "advanced",
      "description": "Adaptive Sector Wave Strategy",
      "is_active": true,
      "test_coverage": 92.3
    },
    {
      "name": "IchimokuStrategy",
      "category": "basic", 
      "description": "Ichimoku Cloud Strategy",
      "is_active": true,
      "test_coverage": 78.9
    }
  ]
}
```

### 2. Validate Elliott Wave Strategy

Test the Elliott Wave Impulse Strategy with comprehensive validation:

```bash
curl -X POST "http://localhost:11080/api/testing/strategies/ElliottWaveImpulseStrategy/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "test_types": ["interface", "signal", "performance", "edge_case"],
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "timeframes": ["1h", "4h", "1d"],
    "market_regimes": ["bull", "bear", "sideways", "volatile"],
    "timeout_seconds": 300
  }'
```

**Expected Response**:
```json
{
  "test_id": "test_ew_impulse_20250101_001",
  "strategy_name": "ElliottWaveImpulseStrategy",
  "overall_status": "passed",
  "execution_time_ms": 2450,
  "test_results": [
    {
      "test_type": "interface",
      "status": "passed",
      "execution_time_ms": 45,
      "details": {
        "interface_compliance": true,
        "required_methods": ["generate_signal", "calculate_position_size"],
        "optional_methods": ["get_strategy_info", "activate", "deactivate"]
      }
    },
    {
      "test_type": "signal",
      "status": "passed", 
      "execution_time_ms": 1200,
      "details": {
        "signals_generated": 156,
        "valid_signals": 142,
        "accuracy_rate": 0.91
      }
    },
    {
      "test_type": "performance",
      "status": "passed",
      "execution_time_ms": 800,
      "details": {
        "average_execution_time_ms": 12.5,
        "memory_peak_mb": 45.2,
        "cpu_average_percent": 15.3
      }
    },
    {
      "test_type": "edge_case",
      "status": "passed",
      "execution_time_ms": 405,
      "details": {
        "insufficient_data_handled": true,
        "extreme_volatility_handled": true,
        "parameter_boundaries_respected": true
      }
    }
  ],
  "summary": {
    "total_tests": 4,
    "passed_tests": 4,
    "failed_tests": 0,
    "skipped_tests": 0,
    "coverage_percentage": 91.2
  }
}
```

### 3. Test Ichimoku Strategy Signal Generation

Test signal generation specifically for the Ichimoku strategy:

```bash
curl -X POST "http://localhost:11080/api/testing/strategies/IchimokuStrategy/test/signals" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "TSLA"],
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "market_regime": "sideways",
    "expected_signals": [
      {
        "symbol": "AAPL",
        "timestamp": "2024-02-15T10:00:00Z",
        "action": "BUY",
        "confidence_min": 0.7,
        "confidence_max": 0.9
      }
    ]
  }'
```

**Expected Response**:
```json
{
  "test_id": "signal_test_ichimoku_20250101_002",
  "strategy_name": "IchimokuStrategy",
  "signals_generated": 89,
  "signals_validated": 89,
  "validation_results": [
    {
      "signal_id": "signal_001",
      "timestamp": "2024-02-15T10:00:00Z",
      "symbol": "AAPL",
      "action": "BUY",
      "confidence": 0.82,
      "validation_status": "valid",
      "expected_action": "BUY",
      "validation_notes": "Signal matches expected action with high confidence"
    }
  ],
  "summary": {
    "total_signals": 89,
    "valid_signals": 78,
    "invalid_signals": 11,
    "accuracy_percentage": 87.6
  }
}
```

### 4. Performance Benchmark for Adaptive Wave Strategy

Run performance benchmarks for the Adaptive Sector Wave Strategy:

```bash
curl -X POST "http://localhost:11080/api/testing/strategies/AdaptiveSectorWaveStrategy/test/performance" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
    "iterations": 500,
    "concurrent_executions": 10,
    "performance_limits": {
      "max_execution_time_ms": 100,
      "max_memory_mb": 1024,
      "max_cpu_percent": 80
    }
  }'
```

**Expected Response**:
```json
{
  "test_id": "perf_test_adaptive_20250101_003",
  "strategy_name": "AdaptiveSectorWaveStrategy",
  "performance_metrics": {
    "total_execution_time_ms": 12500,
    "average_execution_time_ms": 25.0,
    "max_execution_time_ms": 45,
    "min_execution_time_ms": 18,
    "memory_peak_mb": 156.7,
    "memory_average_mb": 142.3,
    "cpu_peak_percent": 35.2,
    "cpu_average_percent": 28.1,
    "signals_per_second": 40.0
  },
  "validation_status": "within_limits",
  "benchmark_comparison": {
    "previous_baseline": 28.5,
    "performance_change_percent": -12.3
  }
}
```

### 5. Ensemble Strategy Testing

Test multiple strategies working together as an ensemble:

```bash
curl -X POST "http://localhost:11080/api/testing/strategies/ensemble/test" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_names": [
      "ElliottWaveImpulseStrategy",
      "AdaptiveSectorWaveStrategy", 
      "IchimokuStrategy"
    ],
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "test_duration_days": 30,
    "conflict_resolution": "highest_confidence",
    "allocation_strategy": "equal"
  }'
```

**Expected Response**:
```json
{
  "test_id": "ensemble_test_20250101_004",
  "ensemble_strategies": [
    "ElliottWaveImpulseStrategy",
    "AdaptiveSectorWaveStrategy",
    "IchimokuStrategy"
  ],
  "conflict_count": 23,
  "resolution_success_rate": 0.87,
  "ensemble_performance": {
    "total_execution_time_ms": 3200,
    "average_execution_time_ms": 35.6,
    "max_execution_time_ms": 52,
    "min_execution_time_ms": 28,
    "memory_peak_mb": 234.5,
    "memory_average_mb": 198.7,
    "cpu_peak_percent": 42.1,
    "cpu_average_percent": 31.8,
    "signals_per_second": 28.1
  },
  "individual_performances": [
    {
      "strategy_name": "ElliottWaveImpulseStrategy",
      "performance": {
        "average_execution_time_ms": 32.1,
        "memory_peak_mb": 89.2,
        "cpu_average_percent": 25.4
      }
    }
  ]
}
```

### 6. Generate Mock Market Data

Create synthetic market data for testing:

```bash
curl -X POST "http://localhost:11080/api/testing/mock-data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "timeframe": "1h",
    "market_regime": "bull",
    "include_technical_indicators": true,
    "include_elliott_wave_patterns": true,
    "include_options_data": false,
    "volatility_level": "medium"
  }'
```

**Expected Response**:
```json
{
  "data_id": "mock_data_20250101_005",
  "symbols": ["AAPL", "MSFT"],
  "timeframe": "1h",
  "market_regime": "bull",
  "data_points": 2160,
  "generated_at": "2025-01-01T12:00:00Z",
  "data_preview": [
    {
      "symbol": "AAPL",
      "timestamp": "2024-01-01T09:30:00Z",
      "open": 185.25,
      "high": 186.89,
      "low": 184.92,
      "close": 186.45,
      "volume": 1250000
    }
  ]
}
```

## Python Client Examples

### Using the Testing Framework in Python

```python
import requests
import json
from datetime import datetime, timedelta

class StrategyTestingClient:
    def __init__(self, base_url="http://localhost:11080/api/testing"):
        self.base_url = base_url
    
    def list_strategies(self):
        """List all available strategies"""
        response = requests.get(f"{self.base_url}/strategies")
        response.raise_for_status()
        return response.json()
    
    def validate_strategy(self, strategy_name, test_config):
        """Validate a specific strategy"""
        response = requests.post(
            f"{self.base_url}/strategies/{strategy_name}/validate",
            json=test_config
        )
        response.raise_for_status()
        return response.json()
    
    def test_signals(self, strategy_name, signal_config):
        """Test signal generation for a strategy"""
        response = requests.post(
            f"{self.base_url}/strategies/{strategy_name}/test/signals",
            json=signal_config
        )
        response.raise_for_status()
        return response.json()
    
    def benchmark_performance(self, strategy_name, perf_config):
        """Benchmark strategy performance"""
        response = requests.post(
            f"{self.base_url}/strategies/{strategy_name}/test/performance",
            json=perf_config
        )
        response.raise_for_status()
        return response.json()

# Example usage
client = StrategyTestingClient()

# Test Elliott Wave strategy
ew_config = {
    "test_types": ["interface", "signal", "performance"],
    "symbols": ["AAPL", "MSFT"],
    "timeframes": ["1h", "4h"],
    "market_regimes": ["bull", "bear", "sideways"]
}

result = client.validate_strategy("ElliottWaveImpulseStrategy", ew_config)
print(f"Elliott Wave Strategy Test Status: {result['overall_status']}")
print(f"Coverage: {result['summary']['coverage_percentage']}%")

# Test Ichimoku signals
ichimoku_config = {
    "symbols": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "market_regime": "sideways"
}

signal_result = client.test_signals("IchimokuStrategy", ichimoku_config)
print(f"Ichimoku Signals Generated: {signal_result['signals_generated']}")
print(f"Signal Accuracy: {signal_result['summary']['accuracy_percentage']}%")
```

## Test Suite Execution

### Run Complete Test Suite

```bash
curl -X POST "http://localhost:11080/api/testing/test-suites/comprehensive/run" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
    "timeframes": ["1h", "4h", "1d"],
    "market_regimes": ["bull", "bear", "sideways", "volatile"],
    "parallel_execution": true,
    "timeout_minutes": 30
  }'
```

## Health Check

Always verify the testing framework is healthy before running tests:

```bash
curl -X GET "http://localhost:11080/api/testing/health"
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

## Best Practices

### 1. Start with Interface Validation
Always begin by validating that strategies implement the BaseStrategy interface correctly:

```json
{
  "test_types": ["interface"],
  "symbols": ["AAPL"],
  "timeframes": ["1h"]
}
```

### 2. Test Multiple Market Regimes
Validate strategies across different market conditions:

```json
{
  "market_regimes": ["bull", "bear", "sideways", "volatile"]
}
```

### 3. Use Appropriate Timeframes
Test strategies on timeframes they're designed for:

- **Elliott Wave**: 4h, 1d (longer-term patterns)
- **Ichimoku**: 1h, 4h (medium-term trends)
- **Adaptive Wave**: 15m, 1h (adaptive to market conditions)

### 4. Set Reasonable Performance Limits
Configure performance limits based on strategy complexity:

```json
{
  "performance_limits": {
    "max_execution_time_ms": 100,
    "max_memory_mb": 1024,
    "max_cpu_percent": 80
  }
}
```

### 5. Monitor Test Results
Track test results over time to detect performance regressions:

```python
# Store test results for trend analysis
test_history = []
result = client.validate_strategy("ElliottWaveImpulseStrategy", config)
test_history.append({
    "timestamp": datetime.now(),
    "strategy": result["strategy_name"],
    "status": result["overall_status"],
    "execution_time": result["execution_time_ms"],
    "coverage": result["summary"]["coverage_percentage"]
})
```

## Troubleshooting

### Common Issues

1. **Strategy Not Found (404)**
   - Verify strategy name is correct
   - Check that strategy is registered in the system

2. **Test Timeout (400)**
   - Increase timeout_seconds parameter
   - Reduce number of symbols or timeframes being tested

3. **Performance Exceeds Limits**
   - Review strategy implementation for optimization opportunities
   - Adjust performance limits if strategy requirements are higher

4. **Low Signal Accuracy**
   - Check strategy parameters
   - Verify market data quality
   - Review strategy logic for edge cases

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
curl -X POST "http://localhost:11080/api/testing/strategies/ElliottWaveImpulseStrategy/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "test_types": ["signal"],
    "symbols": ["AAPL"],
    "timeframes": ["1h"],
    "debug_mode": true,
    "verbose_logging": true
  }'
```

## Next Steps

1. **Run Initial Tests**: Start with interface validation for all strategies
2. **Focus on Priority Strategies**: Test Elliott Wave, Adaptive Wave, and Ichimoku strategies first
3. **Establish Baselines**: Set performance benchmarks for future regression testing
4. **Automate Testing**: Integrate with CI/CD pipeline for continuous validation
5. **Monitor Performance**: Track test results over time to detect issues early

## Support

For questions or issues with the Strategy Engine Testing Framework:

- Check the API documentation at `/api/testing/docs`
- Review test logs for detailed error information
- Contact the trading system team for strategy-specific questions













