# API Contracts: Comprehensive Risk Management Framework

## Service Overview

The Risk Management Service provides comprehensive risk assessment, monitoring, and reporting capabilities for algorithmic trading portfolios. All endpoints follow RESTful conventions and return JSON responses.

**Base URL**: `http://localhost:11182/api/risk`

## Authentication

All endpoints require API key authentication:
```
Authorization: Bearer <api_key>
```

## Rate Limiting

- **Standard endpoints**: 100 requests/minute
- **Heavy computation endpoints** (VaR, stress testing): 10 requests/minute
- **Monitoring endpoints**: 1000 requests/minute

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-12-01T10:00:00Z",
  "request_id": "uuid"
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "RISK_CALCULATION_FAILED",
    "message": "Insufficient historical data for VaR calculation",
    "details": { ... }
  },
  "timestamp": "2024-12-01T10:00:00Z",
  "request_id": "uuid"
}
```

## Endpoints

### 1. VaR Calculation
**POST** `/var-calculation`

Calculate Value at Risk and Expected Shortfall for a portfolio.

### 2. Stress Testing
**POST** `/stress-test`

Run stress testing scenarios on portfolio positions.

### 3. Correlation Analysis
**POST** `/correlation-analysis`

Analyze portfolio correlations and concentration risks.

### 4. Compliance Reporting
**GET** `/compliance-report`

Generate regulatory compliance reports.

### 5. Risk Monitoring
**GET** `/monitoring`

Get current risk metrics and monitoring status.

### 6. Risk Limits Configuration
**PUT** `/limits`

Configure risk limits and thresholds.

### 7. Risk Alerts
**GET** `/alerts`

Get active risk alerts and notifications.

## Data Models

All request/response schemas are defined in the individual contract files:
- `var-calculation.yaml` - VaR calculation schemas
- `stress-testing.yaml` - Stress testing schemas  
- `correlation-analysis.yaml` - Correlation analysis schemas
- `compliance-reporting.yaml` - Compliance reporting schemas
- `risk-monitoring.yaml` - Risk monitoring schemas
- `risk-limits.yaml` - Risk limits configuration schemas
- `risk-alerts.yaml` - Risk alerts schemas

## Error Codes

| Code | Description |
|------|-------------|
| `INSUFFICIENT_DATA` | Not enough historical data for calculation |
| `INVALID_PORTFOLIO` | Portfolio configuration is invalid |
| `CALCULATION_FAILED` | Risk calculation encountered an error |
| `LIMIT_BREACH` | Risk limit has been breached |
| `SERVICE_UNAVAILABLE` | Risk service is temporarily unavailable |
| `INVALID_PARAMETERS` | Request parameters are invalid |
| `RATE_LIMIT_EXCEEDED` | Rate limit has been exceeded |
| `AUTHENTICATION_FAILED` | API key authentication failed |
| `AUTHORIZATION_FAILED` | Insufficient permissions for operation |

## Performance Requirements

- **VaR Calculation**: <5 seconds for 50+ assets
- **Stress Testing**: <30 seconds for comprehensive scenarios
- **Correlation Analysis**: <10 seconds for rolling correlations
- **Compliance Reports**: <60 seconds for report generation
- **Risk Monitoring**: <1 second for current metrics

## Monitoring and Observability

All endpoints provide:
- Request/response logging with structured JSON
- Performance metrics (latency, throughput)
- Error rate tracking
- Health check endpoints

Health check: **GET** `/health`



