# Quickstart Guide: Active Trade Recovery and Management

**Feature**: Active Trade Recovery and Management  
**Date**: 2025-01-27  
**Phase**: 1 - Design

## Overview

This quickstart guide demonstrates how to use the Active Trade Recovery and Management system to detect and manage active trades after a database failure or system restart.

## Prerequisites

- Trading system running with active trading account
- Trade Recovery Service deployed and accessible
- Valid authentication credentials
- At least one active trade on the trading account

## Step-by-Step Recovery Process

### Step 1: Create Recovery Session

Create a new recovery session to begin the trade recovery process.

```bash
curl -X POST "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "your_account_123",
    "recovery_type": "DATABASE_FAILURE",
    "description": "System recovery after database failure"
  }'
```

**Expected Response**:
```json
{
  "id": "session_123",
  "account_id": "your_account_123",
  "started_at": "2025-01-27T10:00:00Z",
  "status": "IN_PROGRESS",
  "recovery_type": "DATABASE_FAILURE",
  "total_trades_detected": 0,
  "trades_processed": 0,
  "trades_assigned": 0
}
```

### Step 2: Detect Active Trades

Retrieve all active trades from your trading account.

```bash
curl -X GET "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/trades/active?account_id=your_account_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response**:
```json
{
  "account_id": "your_account_123",
  "detected_at": "2025-01-27T10:00:00Z",
  "trades": [
    {
      "id": "trade_123",
      "account_id": "your_account_123",
      "symbol": "AAPL",
      "quantity": 100.0,
      "side": "BUY",
      "entry_price": 150.00,
      "current_price": 155.00,
      "current_value": 15500.00,
      "unrealized_pnl": 500.00,
      "entry_date": "2025-01-20T09:30:00Z",
      "detected_at": "2025-01-27T10:00:00Z",
      "position_type": "STOCK",
      "option_details": null
    }
  ],
  "total_count": 1
}
```

### Step 3: Get Available Strategies

Retrieve all available trading strategies for assignment.

```bash
curl -X GET "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/strategies/available" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response**:
```json
{
  "strategies": [
    {
      "name": "BollingerBands",
      "description": "Mean reversion strategy using Bollinger Bands",
      "category": "MEAN_REVERSION",
      "enabled": true,
      "min_position_size": 100.0,
      "max_position_size": 10000.0,
      "supported_symbols": ["AAPL", "TSLA", "NVDA"],
      "supported_position_types": ["STOCK"]
    },
    {
      "name": "MACD",
      "description": "Moving Average Convergence Divergence strategy",
      "category": "MOMENTUM",
      "enabled": true,
      "min_position_size": 100.0,
      "max_position_size": 10000.0,
      "supported_symbols": ["AAPL", "TSLA", "NVDA"],
      "supported_position_types": ["STOCK"]
    }
  ],
  "total_count": 2
}
```

### Step 4: Get Strategy Recommendations

Get intelligent strategy recommendations for a specific trade.

```bash
curl -X POST "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/strategies/match" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trade": {
      "id": "trade_123",
      "symbol": "AAPL",
      "quantity": 100.0,
      "side": "BUY",
      "entry_price": 150.00,
      "current_price": 155.00,
      "position_type": "STOCK"
    },
    "market_conditions": {
      "volatility": 0.25,
      "trend": "BULLISH",
      "volume": 1000000
    }
  }'
```

**Expected Response**:
```json
{
  "trade_id": "trade_123",
  "matches": [
    {
      "strategy_name": "BollingerBands",
      "confidence_score": 0.85,
      "match_reason": "High volatility, mean reversion opportunity",
      "expected_performance": 0.12,
      "risk_level": "MEDIUM",
      "estimated_duration": "SHORT_TERM"
    },
    {
      "strategy_name": "MACD",
      "confidence_score": 0.72,
      "match_reason": "Strong momentum signal",
      "expected_performance": 0.08,
      "risk_level": "LOW",
      "estimated_duration": "MEDIUM_TERM"
    }
  ],
  "total_count": 2
}
```

### Step 5: Assign Strategy to Trade

Assign a strategy to manage the recovered trade.

```bash
curl -X POST "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/assign-strategy" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_session_id": "session_123",
    "active_trade_id": "trade_123",
    "strategy_name": "BollingerBands",
    "assigned_by": "user_123",
    "confidence_score": 0.85,
    "assignment_reason": "High volatility, mean reversion opportunity",
    "strategy_parameters": {
      "period": 20,
      "std_dev": 2.0
    }
  }'
```

**Expected Response**:
```json
{
  "id": "assignment_123",
  "recovery_session_id": "session_123",
  "active_trade_id": "trade_123",
  "strategy_name": "BollingerBands",
  "assigned_at": "2025-01-27T10:00:00Z",
  "assigned_by": "user_123",
  "confidence_score": 0.85,
  "assignment_reason": "High volatility, mean reversion opportunity",
  "status": "PENDING",
  "strategy_parameters": {
    "period": 20,
    "std_dev": 2.0
  }
}
```

### Step 6: Monitor Recovery Progress

Check the status of your recovery session.

```bash
curl -X GET "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/sessions/session_123/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response**:
```json
{
  "session_id": "session_123",
  "status": "IN_PROGRESS",
  "progress": {
    "total_trades_detected": 1,
    "trades_processed": 1,
    "trades_assigned": 1,
    "completion_percentage": 100.0
  },
  "last_updated": "2025-01-27T10:00:00Z"
}
```

### Step 7: Complete Recovery Session

Mark the recovery session as completed.

```bash
curl -X PATCH "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/sessions/session_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "COMPLETED"
  }'
```

## Error Handling Examples

### Invalid Account ID
```bash
curl -X GET "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/trades/active?account_id=invalid" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Error Response**:
```json
{
  "error": "Invalid account ID",
  "code": "INVALID_ACCOUNT",
  "message": "Account ID must be a valid string"
}
```

### Existing Recovery Session
```bash
curl -X POST "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "your_account_123",
    "recovery_type": "DATABASE_FAILURE"
  }'
```

**Error Response**:
```json
{
  "error": "Active recovery session exists",
  "code": "SESSION_CONFLICT",
  "message": "Account already has an active recovery session"
}
```

## Integration with Trading Dashboard

The recovery system integrates with the existing trading dashboard to provide a user-friendly interface:

1. **Recovery Status Widget**: Shows current recovery session status
2. **Active Trades Panel**: Displays detected trades with management options
3. **Strategy Selection Interface**: Allows users to choose strategies for each trade
4. **Progress Tracking**: Real-time updates on recovery progress

## Best Practices

### Recovery Session Management
- Always create a recovery session before detecting trades
- Monitor session progress regularly
- Complete sessions when all trades are processed
- Handle errors gracefully with proper error messages

### Strategy Assignment
- Review strategy recommendations before assignment
- Consider market conditions when selecting strategies
- Use confidence scores to guide decisions
- Document assignment reasons for audit purposes

### Error Handling
- Implement retry logic for API calls
- Handle network timeouts gracefully
- Validate all input data before API calls
- Log all recovery actions for audit purposes

## Troubleshooting

### Common Issues

1. **No Active Trades Detected**
   - Verify account ID is correct
   - Check if trades are actually open
   - Ensure broker API is accessible

2. **Strategy Assignment Fails**
   - Verify strategy name is valid
   - Check if strategy is enabled
   - Ensure trade meets strategy requirements

3. **Recovery Session Stuck**
   - Check session status
   - Verify all required fields are provided
   - Review error messages in logs

### Debug Mode

Enable debug mode for detailed logging:

```bash
curl -X GET "http://trade-recovery-service.trading-system.svc.cluster.local:10001/api/v1/recovery/sessions/session_123/status?debug=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

This will return additional debugging information including:
- Detailed error messages
- Processing timestamps
- Strategy matching details
- Performance metrics




















