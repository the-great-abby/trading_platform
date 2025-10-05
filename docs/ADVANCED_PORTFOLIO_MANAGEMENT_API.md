# Advanced Portfolio Management System - API Documentation

## Overview

The Advanced Portfolio Management System provides comprehensive portfolio optimization, risk management, and analytics capabilities through a RESTful API. This document describes all available endpoints, request/response formats, and usage examples.

## Base URLs

- **Portfolio Service**: `http://localhost:11180`
- **Risk Management Service**: `http://localhost:11181`

## Authentication

All API endpoints require authentication using API keys:

```http
Authorization: Bearer YOUR_API_KEY
```

## Common Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Portfolio Service API

### Portfolio Management

#### Create Portfolio

```http
POST /api/v1/portfolios
```

**Request Body:**
```json
{
  "name": "My Investment Portfolio",
  "owner_id": "user123",
  "risk_tolerance": "MODERATE",
  "base_currency": "USD",
  "rebalancing_frequency": "MONTHLY",
  "max_single_asset_weight": 0.20,
  "max_sector_weight": 0.40,
  "long_only": true,
  "description": "Diversified investment portfolio"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "portfolio_id": "portfolio-abc123",
    "name": "My Investment Portfolio",
    "owner_id": "user123",
    "status": "ACTIVE",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Get Portfolio

```http
GET /api/v1/portfolios/{portfolio_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "portfolio_id": "portfolio-abc123",
    "name": "My Investment Portfolio",
    "owner_id": "user123",
    "risk_tolerance": "MODERATE",
    "base_currency": "USD",
    "total_value": 100000.0,
    "cash_balance": 5000.0,
    "status": "ACTIVE",
    "positions": [
      {
        "position_id": "pos-001",
        "asset_id": "AAPL",
        "quantity": 100,
        "average_cost": 150.0,
        "current_price": 175.0,
        "unrealized_pnl": 2500.0,
        "unrealized_pnl_percentage": 16.67
      }
    ],
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Update Portfolio

```http
PUT /api/v1/portfolios/{portfolio_id}
```

**Request Body:**
```json
{
  "name": "Updated Portfolio Name",
  "risk_tolerance": "AGGRESSIVE",
  "max_single_asset_weight": 0.25
}
```

#### Delete Portfolio

```http
DELETE /api/v1/portfolios/{portfolio_id}
```

### Position Management

#### Add Position

```http
POST /api/v1/portfolios/{portfolio_id}/positions
```

**Request Body:**
```json
{
  "asset_id": "AAPL",
  "quantity": 100,
  "average_cost": 150.0,
  "current_price": 175.0
}
```

#### Update Position

```http
PUT /api/v1/portfolios/{portfolio_id}/positions/{position_id}
```

#### Delete Position

```http
DELETE /api/v1/portfolios/{portfolio_id}/positions/{position_id}
```

### Portfolio Optimization

#### MPT Optimization

```http
POST /api/v1/optimization/mpt
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "risk_free_rate": 0.02,
  "max_iterations": 1000,
  "convergence_tolerance": 1e-6,
  "max_single_asset_weight": 0.20,
  "min_single_asset_weight": 0.0,
  "enable_short_selling": false,
  "transaction_cost_rate": 0.001
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "optimization_id": "opt-xyz789",
    "portfolio_id": "portfolio-abc123",
    "optimization_type": "MPT",
    "expected_return": 0.12,
    "expected_volatility": 0.18,
    "sharpe_ratio": 0.67,
    "convergence_achieved": true,
    "iterations": 150,
    "optimal_weights": {
      "AAPL": 0.15,
      "GOOGL": 0.20,
      "MSFT": 0.18,
      "TSLA": 0.12,
      "SPY": 0.35
    },
    "risk_contributions": {
      "AAPL": 0.14,
      "GOOGL": 0.19,
      "MSFT": 0.16,
      "TSLA": 0.15,
      "SPY": 0.36
    }
  }
}
```

#### Black-Litterman Optimization

```http
POST /api/v1/optimization/black-litterman
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "risk_aversion": 3.0,
  "confidence_level": 0.7,
  "tau": 0.05,
  "views": [
    {
      "type": "absolute",
      "assets": ["AAPL"],
      "expected_return": 0.15,
      "confidence": 0.8,
      "description": "Apple expected to outperform"
    },
    {
      "type": "relative",
      "assets": ["GOOGL", "MSFT"],
      "expected_return_diff": 0.05,
      "confidence": 0.6,
      "description": "Google expected to outperform Microsoft by 5%"
    }
  ]
}
```

#### Risk Parity Optimization

```http
POST /api/v1/optimization/risk-parity
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "risk_budget_method": "equal",
  "convergence_tolerance": 1e-6,
  "max_iterations": 1000
}
```

#### Efficient Frontier

```http
POST /api/v1/optimization/efficient-frontier
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "num_portfolios": 100,
  "risk_free_rate": 0.02,
  "min_return": 0.05,
  "max_return": 0.25
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "frontier_points": [
      {
        "return": 0.08,
        "volatility": 0.15,
        "sharpe_ratio": 0.40,
        "weights": {
          "AAPL": 0.20,
          "GOOGL": 0.15,
          "MSFT": 0.25,
          "TSLA": 0.10,
          "SPY": 0.30
        }
      }
    ],
    "max_sharpe_portfolio": {
      "return": 0.12,
      "volatility": 0.18,
      "sharpe_ratio": 0.67
    },
    "min_variance_portfolio": {
      "return": 0.08,
      "volatility": 0.15,
      "sharpe_ratio": 0.40
    }
  }
}
```

### Rebalancing

#### Generate Rebalancing Recommendations

```http
POST /api/v1/rebalancing/recommend
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "strategy": "intelligent",
  "drift_threshold": 0.05,
  "tax_aware": true,
  "transaction_cost_rate": 0.001
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec-def456",
    "portfolio_id": "portfolio-abc123",
    "strategy": "intelligent",
    "total_drift": 0.12,
    "number_of_trades": 8,
    "estimated_cost": 150.0,
    "trade_recommendations": [
      {
        "asset_id": "AAPL",
        "action": "BUY",
        "quantity": 50,
        "current_weight": 0.15,
        "target_weight": 0.20,
        "drift": 0.05,
        "estimated_cost": 8750.0
      }
    ],
    "tax_optimization": {
      "tax_loss_harvesting_opportunities": 2,
      "estimated_tax_benefit": 500.0
    }
  }
}
```

#### Execute Rebalancing

```http
POST /api/v1/rebalancing/execute
```

**Request Body:**
```json
{
  "recommendation_id": "rec-def456",
  "execute_trades": true,
  "dry_run": false
}
```

### Tax Optimization

#### Tax-Loss Harvesting

```http
POST /api/v1/tax/optimize
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "optimization_type": "tax_loss_harvesting",
  "min_harvest_amount": 1000.0,
  "max_harvest_percentage": 0.20
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "optimization_id": "tax-ghi789",
    "portfolio_id": "portfolio-abc123",
    "tax_benefit": 2500.0,
    "harvested_losses": 10000.0,
    "wash_sale_violations": [],
    "recommendations": [
      {
        "asset_id": "TSLA",
        "action": "SELL",
        "quantity": 25,
        "realized_loss": 1250.0,
        "replacement_asset": "TSLA-ALT",
        "wash_sale_compliance": true
      }
    ]
  }
}
```

### Backtesting

#### Portfolio Backtesting

```http
POST /api/v1/backtesting/portfolio
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "benchmark_symbol": "SPY",
  "transaction_cost": 0.001,
  "rebalancing_frequency": "MONTHLY"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt-jkl012",
    "portfolio_id": "portfolio-abc123",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "total_return": 0.45,
    "annualized_return": 0.12,
    "volatility": 0.18,
    "sharpe_ratio": 0.67,
    "max_drawdown": -0.15,
    "calmar_ratio": 0.80,
    "sortino_ratio": 0.89,
    "beta": 1.12,
    "alpha": 0.02,
    "r_squared": 0.85,
    "benchmark_comparison": {
      "benchmark_return": 0.38,
      "benchmark_volatility": 0.16,
      "excess_return": 0.07,
      "information_ratio": 0.44
    },
    "performance_attribution": {
      "asset_contributions": {
        "AAPL": 0.15,
        "GOOGL": 0.20,
        "MSFT": 0.18,
        "TSLA": 0.12,
        "SPY": 0.35
      }
    }
  }
}
```

---

## Risk Management Service API

### Risk Assessment

#### Calculate VaR

```http
POST /api/v1/risk/assess
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "confidence_levels": [0.95, 0.99],
  "time_horizons": [1, 10, 30],
  "lookback_period": 252
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "risk_metrics_id": "risk-mno345",
    "portfolio_id": "portfolio-abc123",
    "var_95_1d": 2500.0,
    "var_99_1d": 3500.0,
    "cvar_95_1d": 3200.0,
    "cvar_99_1d": 4200.0,
    "portfolio_volatility": 0.18,
    "portfolio_beta": 1.12,
    "tracking_error": 0.05
  }
}
```

#### Stress Testing

```http
POST /api/v1/risk/stress-test
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "scenarios": [
    {
      "name": "Market Crash",
      "shock_return": -0.20,
      "description": "20% market decline scenario"
    },
    {
      "name": "Interest Rate Shock",
      "shock_return": 0.05,
      "description": "5% interest rate increase"
    },
    {
      "name": "Tech Bubble Burst",
      "shock_return": -0.30,
      "description": "30% tech sector decline"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stress_test_id": "stress-pqr678",
    "portfolio_id": "portfolio-abc123",
    "scenarios": [
      {
        "name": "Market Crash",
        "portfolio_impact": -0.18,
        "impact_value": -18000.0,
        "worst_asset": "TSLA",
        "worst_asset_impact": -0.25
      }
    ],
    "worst_case_scenario": "Market Crash",
    "worst_case_impact": -0.18,
    "total_portfolio_impact": -0.45
  }
}
```

#### Factor Analysis

```http
POST /api/v1/risk/factor-analysis
```

**Request Body:**
```json
{
  "portfolio_id": "portfolio-abc123",
  "factors": ["market", "size", "value", "momentum"],
  "lookback_period": 252
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "factor_analysis_id": "factor-stu901",
    "portfolio_id": "portfolio-abc123",
    "factor_exposures": {
      "market": {
        "exposure": 1.12,
        "contribution": 0.65,
        "significance": "High"
      },
      "size": {
        "exposure": 0.85,
        "contribution": 0.15,
        "significance": "Medium"
      },
      "value": {
        "exposure": -0.45,
        "contribution": 0.10,
        "significance": "Low"
      },
      "momentum": {
        "exposure": 0.25,
        "contribution": 0.10,
        "significance": "Low"
      }
    },
    "concentration_risk": "Medium",
    "diversification_ratio": 0.75
  }
}
```

### Risk Monitoring

#### Risk Limits Monitoring

```http
GET /api/v1/risk/monitor/{portfolio_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "portfolio_id": "portfolio-abc123",
    "risk_limits": {
      "max_var_95": 5000.0,
      "max_volatility": 0.20,
      "max_beta": 1.5,
      "max_single_asset_weight": 0.30
    },
    "current_metrics": {
      "var_95": 2500.0,
      "volatility": 0.18,
      "beta": 1.12,
      "max_weight": 0.20
    },
    "limit_violations": [],
    "compliance_status": "COMPLIANT",
    "risk_score": 0.65
  }
}
```

---

## Market Data Service API

### Asset Information

#### Get Asset Details

```http
GET /api/v1/assets/{asset_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "asset_id": "AAPL",
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_type": "STOCK",
    "exchange": "NASDAQ",
    "currency": "USD",
    "current_price": 175.0,
    "daily_volatility": 0.025,
    "beta": 1.2,
    "market_cap": 2800000000000,
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "last_updated": "2025-01-15T10:30:00Z"
  }
}
```

#### Get Market Data

```http
GET /api/v1/market-data/{asset_id}/history
```

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `frequency`: Data frequency (daily, weekly, monthly)

**Response:**
```json
{
  "success": true,
  "data": {
    "asset_id": "AAPL",
    "frequency": "daily",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "data": [
      {
        "date": "2024-01-01",
        "open": 185.0,
        "high": 187.0,
        "low": 183.0,
        "close": 186.0,
        "volume": 50000000
      }
    ]
  }
}
```

#### Get Correlation Matrix

```http
POST /api/v1/market-data/correlation
```

**Request Body:**
```json
{
  "assets": ["AAPL", "GOOGL", "MSFT", "TSLA"],
  "lookback_period": 252,
  "frequency": "daily"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "assets": ["AAPL", "GOOGL", "MSFT", "TSLA"],
    "correlation_matrix": [
      [1.0, 0.7, 0.6, 0.5],
      [0.7, 1.0, 0.8, 0.4],
      [0.6, 0.8, 1.0, 0.3],
      [0.5, 0.4, 0.3, 1.0]
    ],
    "lookback_period": 252,
    "last_updated": "2025-01-15T10:30:00Z"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `RATE_LIMITED` | Too many requests |
| `OPTIMIZATION_FAILED` | Optimization algorithm failed |
| `MARKET_DATA_ERROR` | Market data unavailable |
| `INTERNAL_ERROR` | Internal server error |

---

## Rate Limits

- **Portfolio Operations**: 100 requests/minute
- **Optimization**: 10 requests/minute
- **Risk Calculations**: 50 requests/minute
- **Market Data**: 1000 requests/minute

---

## Examples

### Complete Portfolio Workflow

```python
import requests

# 1. Create portfolio
portfolio_response = requests.post(
    "http://localhost:11180/api/v1/portfolios",
    json={
        "name": "My Portfolio",
        "owner_id": "user123",
        "risk_tolerance": "MODERATE",
        "base_currency": "USD"
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
portfolio_id = portfolio_response.json()["data"]["portfolio_id"]

# 2. Add positions
requests.post(
    f"http://localhost:11180/api/v1/portfolios/{portfolio_id}/positions",
    json={
        "asset_id": "AAPL",
        "quantity": 100,
        "average_cost": 150.0,
        "current_price": 175.0
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

# 3. Run optimization
optimization_response = requests.post(
    "http://localhost:11180/api/v1/optimization/mpt",
    json={
        "portfolio_id": portfolio_id,
        "risk_free_rate": 0.02
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

# 4. Assess risk
risk_response = requests.post(
    "http://localhost:11181/api/v1/risk/assess",
    json={
        "portfolio_id": portfolio_id,
        "confidence_levels": [0.95, 0.99]
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

# 5. Generate rebalancing recommendations
rebalancing_response = requests.post(
    "http://localhost:11180/api/v1/rebalancing/recommend",
    json={
        "portfolio_id": portfolio_id,
        "strategy": "intelligent"
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const apiClient = axios.create({
  baseURL: 'http://localhost:11180',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
});

async function createOptimizedPortfolio() {
  try {
    // Create portfolio
    const portfolio = await apiClient.post('/api/v1/portfolios', {
      name: 'JavaScript Portfolio',
      owner_id: 'js-user',
      risk_tolerance: 'MODERATE',
      base_currency: 'USD'
    });
    
    const portfolioId = portfolio.data.data.portfolio_id;
    
    // Add positions
    await apiClient.post(`/api/v1/portfolios/${portfolioId}/positions`, {
      asset_id: 'AAPL',
      quantity: 100,
      average_cost: 150.0,
      current_price: 175.0
    });
    
    // Run optimization
    const optimization = await apiClient.post('/api/v1/optimization/mpt', {
      portfolio_id: portfolioId,
      risk_free_rate: 0.02
    });
    
    console.log('Optimization result:', optimization.data.data);
    
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

createOptimizedPortfolio();
```

---

## Support

For API support and questions:
- **Documentation**: See `specs/002-advanced-portfolio-management/`
- **Examples**: See `demo/portfolio-management/`
- **Integration Tests**: See `scripts/test-portfolio-system-integration.py`












