# Risk Management Framework - API Reference

## Overview

The Comprehensive Risk Management Framework provides a complete set of APIs for portfolio risk assessment, VaR calculations, stress testing, correlation analysis, and compliance reporting.

## Base URL

```
http://localhost:11182
```

## Authentication

All API endpoints require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:11182/api/risk/var-calculation
```

## Core Risk Management APIs

### VaR Calculation

#### POST /api/risk/var-calculation

Calculate Value at Risk for a portfolio.

**Request Body:**
```json
{
  "portfolio_id": "portfolio-123",
  "confidence_levels": [0.95, 0.99],
  "calculation_method": "historical_simulation",
  "data_period_days": 252,
  "include_expected_shortfall": true,
  "include_risk_contributions": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "portfolio-123",
    "var_values": {
      "0.95": -2500.50,
      "0.99": -3200.75
    },
    "expected_shortfall_values": {
      "0.95": -2800.25,
      "0.99": -3800.50
    },
    "calculation_method": "historical_simulation",
    "data_period_days": 252,
    "calculated_at": "2024-01-15T10:30:00Z"
  },
  "request_id": "req-123"
}
```

### Stress Testing

#### POST /api/risk/stress-test

Run stress tests on a portfolio.

**Request Body:**
```json
{
  "portfolio_id": "portfolio-123",
  "scenarios": ["market_crash", "volatility_spike"],
  "include_position_impacts": true,
  "include_sector_impacts": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "portfolio-123",
    "scenario_results": {
      "market_crash": {
        "portfolio_impact": -0.25,
        "position_impacts": [
          {"symbol": "AAPL", "impact": -0.30},
          {"symbol": "GOOGL", "impact": -0.22}
        ],
        "sector_impacts": {
          "technology": -0.28,
          "financial": -0.20
        }
      }
    },
    "tested_at": "2024-01-15T10:30:00Z"
  },
  "request_id": "req-124"
}
```

### Correlation Analysis

#### POST /api/risk/correlation-analysis

Analyze portfolio correlations and concentration risks.

**Request Body:**
```json
{
  "portfolio_id": "portfolio-123",
  "rolling_period_days": 30,
  "include_sector_analysis": true,
  "include_diversification_recommendations": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "portfolio-123",
    "correlation_matrix": {
      "AAPL": {"AAPL": 1.0, "GOOGL": 0.75, "MSFT": 0.68},
      "GOOGL": {"AAPL": 0.75, "GOOGL": 1.0, "MSFT": 0.82},
      "MSFT": {"AAPL": 0.68, "GOOGL": 0.82, "MSFT": 1.0}
    },
    "diversification_metrics": {
      "effective_number_of_stocks": 3.2,
      "concentration_risk": 0.45
    },
    "analyzed_at": "2024-01-15T10:30:00Z"
  },
  "request_id": "req-125"
}
```

## Monitoring and Health APIs

### System Health

#### GET /api/monitoring/health

Get comprehensive system health status.

**Response:**
```json
{
  "status": "success",
  "data": {
    "overall_status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "uptime_seconds": 3600,
    "version": "1.0.0",
    "components": [
      {
        "name": "database",
        "status": "healthy",
        "last_check": "2024-01-15T10:29:45Z",
        "response_time_ms": 15.5,
        "error_message": null
      }
    ],
    "system_metrics": {
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_percent": 30.1
    }
  },
  "request_id": "req-126"
}
```

### Prometheus Metrics

#### GET /metrics

Get Prometheus metrics for monitoring.

**Response:** Prometheus format metrics

## Integration APIs

### Portfolio Integration

#### GET /api/integration/portfolio/{portfolio_id}

Get portfolio data from portfolio service.

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "portfolio-123",
    "positions": [
      {
        "symbol": "AAPL",
        "quantity": 100,
        "current_price": 150.0,
        "current_value": 15000.0,
        "weight": 0.3
      }
    ],
    "total_value": 100000.0,
    "cash_balance": 20000.0,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "request_id": "req-127"
}
```

### Trade Validation

#### POST /api/integration/trade/validate

Validate trade against risk limits.

**Request Body:**
```json
{
  "trade_id": "trade-123",
  "portfolio_id": "portfolio-123",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": 150.0
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "trade_id": "trade-123",
    "approved": true,
    "risk_score": 0.25,
    "risk_factors": [],
    "warnings": [],
    "recommendations": []
  },
  "request_id": "req-128"
}
```

## Error Handling

All APIs return consistent error responses:

```json
{
  "status": "error",
  "error_code": "INVALID_PORTFOLIO_ID",
  "message": "Portfolio ID is required",
  "request_id": "req-129"
}
```

## Rate Limiting

- API calls are limited to 100 requests per minute per API key
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Request limit per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing authentication
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## SDK Examples

### Python

```python
import requests

# VaR Calculation
response = requests.post(
    'http://localhost:11182/api/risk/var-calculation',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        'portfolio_id': 'portfolio-123',
        'confidence_levels': [0.95, 0.99],
        'calculation_method': 'historical_simulation'
    }
)
var_result = response.json()
```

### JavaScript

```javascript
// Stress Testing
const response = await fetch('http://localhost:11182/api/risk/stress-test', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    portfolio_id: 'portfolio-123',
    scenarios: ['market_crash', 'volatility_spike']
  })
});
const stressResult = await response.json();
```

## Webhooks

The system supports webhooks for real-time notifications:

- Risk limit breaches
- System health alerts
- Calculation completions

Configure webhooks via the monitoring APIs.












