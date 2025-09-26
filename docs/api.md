# Elliott Wave Analysis Service API Documentation

## Overview

The Elliott Wave Analysis Service provides advanced Elliott Wave pattern detection with options trading integration. It analyzes 15-minute charts for tracked symbols and generates trading signals based on wave patterns and Fibonacci levels.

## Base URL

```
http://localhost:11085
```

## Authentication

No authentication required for current implementation.

## Endpoints

### Root Endpoint

**GET** `/`

Returns basic service information.

**Response:**
```json
{
  "message": "Elliott Wave Analysis Service",
  "service": "Elliott Wave Analysis",
  "version": "1.0.0",
  "symbols_tracked": 3
}
```

### Get Tracked Symbols

**GET** `/elliott-wave/symbols`

Returns list of symbols being tracked for Elliott Wave analysis.

**Response:**
```json
{
  "symbols": ["SPY", "QQQ", "AAPL"],
  "count": 3
}
```

### Analyze Single Symbol

**GET** `/elliott-wave/analyze/{symbol}`

Analyzes a single symbol for Elliott Wave patterns.

**Parameters:**
- `symbol` (path): Trading symbol to analyze (e.g., "SPY", "QQQ", "AAPL")
- `timeframe` (query, optional): Analysis timeframe (default: "15m")

**Response:**
```json
{
  "symbol": "SPY",
  "pattern_found": true,
  "pattern_type": "impulse",
  "confidence": 0.85,
  "waves": [
    {
      "timestamp": "2024-01-01T00:00:00",
      "price": 100.0,
      "wave_number": 1,
      "direction": "up",
      "confidence": 0.8
    }
  ],
  "fibonacci_levels": {
    "fib_0.618_retracement": 110.0,
    "fib_1.0_extension": 115.0
  },
  "target_price": 120.0,
  "invalidation_level": 95.0,
  "analysis_time": 0.15
}
```

### Analyze All Symbols

**GET** `/elliott-wave/analyze-all`

Analyzes all tracked symbols for Elliott Wave patterns.

**Response:**
```json
{
  "total_symbols": 3,
  "patterns_found": 2,
  "patterns": [
    {
      "symbol": "SPY",
      "pattern_found": true,
      "pattern_type": "impulse",
      "confidence": 0.85
    }
  ],
  "summary": "Found 2 Elliott Wave patterns across 3 symbols"
}
```

### Options Analysis - Single Symbol

**GET** `/elliott-wave/options-analysis/{symbol}`

Analyzes a single symbol for options trading opportunities based on Elliott Wave patterns.

**Parameters:**
- `symbol` (path): Trading symbol to analyze

**Response:**
```json
{
  "symbol": "SPY",
  "options_signals": [],
  "trading_plan": {
    "symbol": "SPY",
    "primary_signal": {
      "signal_type": "wave_completion_entry",
      "confidence": 0.85,
      "description": "5-wave impulse pattern completed"
    },
    "recommended_strategy": "StraddleStrategy",
    "strategy_config": {
      "min_dte": 15,
      "max_dte": 60,
      "profit_target_pct": 0.3,
      "stop_loss_pct": 1.5,
      "max_position_size": 0.05
    },
    "strike_selection": {
      "call_strike": 115,
      "put_strike": 115,
      "atm_strike": 115
    },
    "risk_management": {
      "risk_level": "medium",
      "profit_target": 120.0,
      "stop_loss": 95.0,
      "max_position_size": 0.05
    }
  },
  "analysis_time": 0.25
}
```

### Options Analysis - All Symbols

**GET** `/elliott-wave/options-analysis-all`

Analyzes all tracked symbols for options trading opportunities.

**Response:**
```json
{
  "total_symbols_analyzed": 3,
  "symbols_with_options_signals": 2,
  "options_opportunities": [
    {
      "symbol": "SPY",
      "options_signals": [],
      "trading_plan": {...}
    }
  ],
  "summary": "Found options opportunities for 2 out of 3 symbols"
}
```

### Health Check

**GET** `/elliott-wave/health`

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Elliott Wave Analysis",
  "timestamp": "2024-01-01T12:00:00",
  "market_data_available": true,
  "options_integration": true
}
```

## Error Responses

### 404 Not Found

```json
{
  "detail": "Symbol INVALID_SYMBOL not tracked"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

## Elliott Wave Pattern Types

- **impulse**: 5-wave impulse pattern
- **corrective**: 3-wave corrective pattern (A-B-C)
- **extension**: Extended wave pattern
- **diagonal**: Diagonal triangle pattern
- **triangle**: Triangle consolidation pattern
- **flat**: Flat correction pattern
- **zigzag**: Zigzag correction pattern

## Fibonacci Levels

The service calculates Fibonacci retracement and extension levels:

- **Retracement Levels**: 0.236, 0.382, 0.5, 0.618, 0.786
- **Extension Levels**: 1.0, 1.272, 1.618, 2.618, 4.236

## Options Strategies

The service integrates with 12 options trading strategies:

- **StraddleStrategy**: Long straddle for volatility expansion
- **IronCondorStrategy**: Iron condor for range-bound markets
- **CalendarSpreadStrategy**: Calendar spread for time decay
- **ButterflySpreadStrategy**: Butterfly spread for low volatility
- **VolatilityStrategy**: Volatility-based strategies
- **LongStrangleStrategy**: Long strangle for volatility
- **DiagonalSpreadStrategy**: Diagonal spread for directional plays
- **CoveredCallStrategy**: Covered call for income generation

## Risk Levels

- **high**: High confidence signals (≥0.8), max position size 10%
- **medium**: Medium confidence signals (≥0.6), max position size 5%
- **low**: Low confidence signals (≥0.4), max position size 2%

## Performance Targets

- **Analysis Time**: <30 seconds per symbol
- **Concurrent Symbols**: 3 symbols (SPY, QQQ, AAPL)
- **Memory Usage**: <512MB per service instance
- **Confidence Threshold**: ≥0.6 for signal generation

## Rate Limits

No rate limits currently implemented.

## Examples

### Analyze SPY for Elliott Wave Patterns

```bash
curl -X GET "http://localhost:11085/elliott-wave/analyze/SPY"
```

### Get Options Analysis for QQQ

```bash
curl -X GET "http://localhost:11085/elliott-wave/options-analysis/QQQ"
```

### Check Service Health

```bash
curl -X GET "http://localhost:11085/elliott-wave/health"
```

## Integration Notes

- The service integrates with the existing market data service
- Options signals are generated based on Elliott Wave patterns
- All analysis is performed on 15-minute charts
- Service is containerized and deployed via Kubernetes
- Health checks are available for monitoring
