# Quickstart Guide: Comprehensive Risk Management Framework

## Overview

This guide provides step-by-step examples for using the Comprehensive Risk Management Framework. The system provides VaR calculations, stress testing, correlation analysis, compliance reporting, and risk monitoring for algorithmic trading portfolios.

## Prerequisites

- Portfolio with $2,000 initial capital
- Market data available (15-minute delayed)
- Risk Management Service running on port 11182
- Valid API key for authentication

## 1. VaR Calculation

### Basic VaR Calculation
Calculate Value at Risk for your portfolio:

```bash
curl -X POST http://localhost:11182/api/risk/var-calculation \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "confidence_levels": [0.95, 0.99],
    "calculation_method": "historical_simulation",
    "data_period_days": 252,
    "include_expected_shortfall": true,
    "include_risk_contributions": true
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "calculation_timestamp": "2024-12-01T10:00:00Z",
    "var_metrics": {
      "var_95": 125.50,
      "var_99": 180.25,
      "portfolio_volatility": 0.185,
      "confidence_intervals": {
        "0.95": 125.50,
        "0.99": 180.25
      }
    },
    "expected_shortfall": {
      "es_95": 165.75,
      "es_99": 220.30
    },
    "risk_contributions": [
      {
        "asset_id": "AAPL",
        "asset_type": "stock",
        "position_weight": 0.35,
        "var_contribution": 45.20,
        "var_contribution_pct": 0.36
      }
    ]
  }
}
```

### VaR History
Get historical VaR calculations:

```bash
curl "http://localhost:11182/api/risk/var-calculation/history?portfolio_id=550e8400-e29b-41d4-a716-446655440000&limit=30" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 2. Stress Testing

### Standard Stress Test Scenarios
Run comprehensive stress testing:

```bash
curl -X POST http://localhost:11182/api/risk/stress-test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "scenarios": ["market_crash", "volatility_spike", "rate_shock"],
    "include_position_impacts": true,
    "include_sector_impacts": true
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "test_timestamp": "2024-12-01T10:00:00Z",
    "initial_portfolio_value": 2000.00,
    "scenario_results": [
      {
        "scenario_name": "Market Crash (-30%)",
        "scenario_type": "market_crash",
        "stressed_portfolio_value": 1650.00,
        "portfolio_value_change": -350.00,
        "portfolio_value_change_pct": -0.175,
        "var_impact": 45.20,
        "position_impacts": [
          {
            "asset_id": "AAPL",
            "initial_value": 700.00,
            "stressed_value": 490.00,
            "position_value_change_pct": -0.30
          }
        ]
      }
    ]
  }
}
```

### Custom Stress Test Scenario
Create a custom scenario for technology sector decline:

```bash
curl -X POST http://localhost:11182/api/risk/stress-test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "custom_scenarios": [
      {
        "name": "Tech Sector Crash",
        "type": "sector_rotation",
        "parameters": {
          "technology_decline": -25,
          "energy_increase": 15
        }
      }
    ]
  }'
```

## 3. Correlation Analysis

### Portfolio Correlation Analysis
Analyze portfolio correlations and concentration risks:

```bash
curl -X POST http://localhost:11182/api/risk/correlation-analysis \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "rolling_period_days": 30,
    "include_sector_analysis": true,
    "include_diversification_recommendations": true
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_timestamp": "2024-12-01T10:00:00Z",
    "concentration_risk_score": 0.65,
    "sector_concentration": {
      "Technology": 0.45,
      "Healthcare": 0.25,
      "Financial": 0.20,
      "Energy": 0.10
    },
    "diversification_ratio": 1.85,
    "effective_number_of_assets": 12.5,
    "recommendations": [
      "Consider reducing technology sector exposure",
      "Add exposure to uncorrelated sectors",
      "Monitor correlation stability"
    ]
  }
}
```

## 4. Risk Monitoring

### Current Risk Metrics
Get current risk monitoring status:

```bash
curl "http://localhost:11182/api/risk/monitoring?portfolio_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "monitoring_timestamp": "2024-12-01T10:00:00Z",
    "risk_status": "within_limits",
    "current_metrics": {
      "var_95": 125.50,
      "portfolio_volatility": 0.185,
      "max_drawdown": 0.12,
      "concentration_risk": 0.65
    },
    "active_alerts": [],
    "next_monitoring": "2024-12-01T10:15:00Z"
  }
}
```

### Risk Alerts
Check for active risk alerts:

```bash
curl "http://localhost:11182/api/risk/alerts?portfolio_id=550e8400-e29b-41d4-a716-446655440000&status=active" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 5. Risk Limits Configuration

### Set Risk Limits
Configure risk limits for your portfolio:

```bash
curl -X PUT http://localhost:11182/api/risk/limits \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "limits": [
      {
        "limit_type": "position_size",
        "limit_value": 0.15,
        "limit_unit": "percentage",
        "enforcement_action": "alert"
      },
      {
        "limit_type": "daily_loss",
        "limit_value": 100.00,
        "limit_unit": "dollars",
        "enforcement_action": "halt_trading"
      },
      {
        "limit_type": "var_limit",
        "limit_value": 200.00,
        "limit_unit": "dollars",
        "enforcement_action": "reduce_position"
      }
    ]
  }'
```

## 6. Compliance Reporting

### Generate Compliance Report
Generate regulatory compliance report:

```bash
curl "http://localhost:11182/api/risk/compliance-report?portfolio_id=550e8400-e29b-41d4-a716-446655440000&report_type=daily&format=PDF" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "compliance_report_id": "uuid",
    "report_timestamp": "2024-12-01T10:00:00Z",
    "compliance_status": "compliant",
    "report_period_start": "2024-11-30",
    "report_period_end": "2024-12-01",
    "report_file_path": "/reports/compliance_20241201.pdf",
    "violations_detected": [],
    "recommendations": [
      "Continue monitoring position concentrations",
      "Maintain current risk limits"
    ]
  }
}
```

## 7. Complete Risk Assessment Workflow

### End-to-End Risk Assessment
Perform comprehensive risk assessment:

```bash
# Step 1: Calculate VaR
VAR_RESULT=$(curl -s -X POST http://localhost:11182/api/risk/var-calculation \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "confidence_levels": [0.95, 0.99],
    "include_expected_shortfall": true
  }')

# Step 2: Run stress tests
STRESS_RESULT=$(curl -s -X POST http://localhost:11182/api/risk/stress-test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "scenarios": ["market_crash", "volatility_spike"]
  }')

# Step 3: Analyze correlations
CORR_RESULT=$(curl -s -X POST http://localhost:11182/api/risk/correlation-analysis \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000"
  }')

# Step 4: Check monitoring status
MONITOR_RESULT=$(curl -s "http://localhost:11182/api/risk/monitoring?portfolio_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_API_KEY")

echo "Risk Assessment Complete:"
echo "VaR 95%: $(echo $VAR_RESULT | jq '.data.var_metrics.var_95')"
echo "Stress Test Status: $(echo $STRESS_RESULT | jq '.data.scenario_results[0].status')"
echo "Correlation Risk: $(echo $CORR_RESULT | jq '.data.concentration_risk_score')"
echo "Risk Status: $(echo $MONITOR_RESULT | jq '.data.risk_status')"
```

## 8. Error Handling

### Common Error Scenarios

**Insufficient Data Error:**
```json
{
  "status": "error",
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "Not enough historical data for VaR calculation. Minimum 30 days required.",
    "details": {
      "available_days": 15,
      "required_days": 30
    }
  }
}
```

**Rate Limit Exceeded:**
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Maximum 10 stress test requests per minute.",
    "details": {
      "limit": 10,
      "retry_after": 60
    }
  }
}
```

## 9. Performance Expectations

- **VaR Calculation**: <5 seconds for 50+ assets
- **Stress Testing**: <30 seconds for 5 scenarios
- **Correlation Analysis**: <10 seconds for portfolio analysis
- **Risk Monitoring**: <1 second for current metrics
- **Compliance Reports**: <60 seconds for report generation

## 10. Best Practices

1. **Monitor Regularly**: Check risk metrics every 15 minutes
2. **Set Appropriate Limits**: Configure risk limits based on portfolio size and risk tolerance
3. **Validate Calculations**: Compare results with known benchmarks
4. **Review Stress Tests**: Regularly run stress tests to understand portfolio vulnerabilities
5. **Maintain Audit Trails**: Keep records of all risk calculations and decisions

## Troubleshooting

### Service Not Available
```bash
# Check service health
curl http://localhost:11182/health

# Check service logs
kubectl logs -n trading-system deployment/risk-management-service
```

### Authentication Issues
```bash
# Verify API key
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:11182/api/risk/monitoring
```

### Data Issues
```bash
# Check market data availability
curl "http://localhost:11182/api/risk/var-calculation/history?portfolio_id=YOUR_PORTFOLIO_ID&limit=1"
```
























