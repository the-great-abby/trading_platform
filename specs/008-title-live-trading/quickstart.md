# Quickstart: Live Trading System

**Feature**: 008-title-live-trading  
**Date**: 2025-09-25  
**Status**: Ready for Implementation

## Overview

This quickstart guide demonstrates the complete workflow for setting up and using the live trading system with Public.com API integration.

## Prerequisites

1. **Public.com Account**: Active brokerage account with API access
2. **Public.com API Token**: Personal access token from Public.com
3. **Live Trading Service**: Deployed and running in Kubernetes
4. **Risk Management**: Understanding of options trading risks

## Step-by-Step Workflow

### 1. Connect to Public.com API

**Objective**: Authenticate with Public.com and establish account connection

**Steps**:
1. Obtain Public.com personal access token from your account settings
2. Call the authentication endpoint with your credentials
3. Verify account connection and balance retrieval

**API Call**:
```bash
curl -X POST http://localhost:11120/api/v1/auth/public-connect \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "access_token": "your-public-token",
    "account_id": "your-public-account-id",
    "account_name": "My Trading Account"
  }'
```

**Expected Response**:
```json
{
  "credential_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "CONNECTED"
}
```

**Validation**:
- ✅ Credentials stored securely
- ✅ Account connection established
- ✅ Real-time balance retrieval working

### 2. Configure Risk Management

**Objective**: Set up risk limits and trading parameters

**Steps**:
1. Retrieve current risk profile
2. Update risk parameters based on account size and risk tolerance
3. Verify emergency stop functionality

**API Call**:
```bash
curl -X PUT http://localhost:11120/api/v1/risk/profile \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "account_id": "660e8400-e29b-41d4-a716-446655440001",
    "max_position_size": 0.1,
    "max_portfolio_risk": 0.15,
    "max_daily_loss": 0.05,
    "max_daily_trades": 50,
    "position_size_limit": 10000,
    "emergency_stop_enabled": true
  }'
```

**Expected Response**:
```json
{
  "profile_id": "770e8400-e29b-41d4-a716-446655440002",
  "account_id": "660e8400-e29b-41d4-a716-446655440001",
  "max_position_size": 0.1,
  "max_portfolio_risk": 0.15,
  "max_daily_loss": 0.05,
  "max_daily_trades": 50,
  "position_size_limit": 10000,
  "emergency_stop_enabled": true,
  "created_at": "2025-09-25T17:00:00Z",
  "updated_at": "2025-09-25T17:00:00Z"
}
```

**Validation**:
- ✅ Risk limits configured appropriately
- ✅ Emergency stop functionality enabled
- ✅ Risk profile persisted in database

### 3. Check Market Hours

**Objective**: Verify system is ready for trading during market hours

**Steps**:
1. Check current market hours status
2. Verify system is operational
3. Confirm trading is allowed

**API Call**:
```bash
curl -X GET http://localhost:11120/api/v1/status/market-hours \
  -H "X-API-Key: your-api-key"
```

**Expected Response** (During Market Hours):
```json
{
  "is_market_open": true,
  "market_opens_at": "2025-09-25T13:30:00Z",
  "market_closes_at": "2025-09-25T20:00:00Z",
  "timezone": "America/New_York"
}
```

**Validation**:
- ✅ Market is open for trading
- ✅ System timezone correctly configured
- ✅ Trading operations allowed

### 4. Execute Iron Condor Trade

**Objective**: Execute a live options trade using Iron Condor strategy

**Steps**:
1. Prepare trade order with Iron Condor parameters
2. Submit order through live trading API
3. Monitor order execution and position creation

**API Call**:
```bash
curl -X POST http://localhost:11120/api/v1/trading/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "account_id": "660e8400-e29b-41d4-a716-446655440001",
    "symbol": "AAPL",
    "action": "SELL",
    "quantity": 1,
    "strategy": "IRON_CONDOR",
    "limit_price": 2.50,
    "time_in_force": "DAY",
    "market_conditions": {
      "short_strike": 180,
      "long_strike": 185,
      "expiry_date": "2025-10-17"
    }
  }'
```

**Expected Response**:
```json
{
  "trade_id": "880e8400-e29b-41d4-a716-446655440003",
  "account_id": "660e8400-e29b-41d4-a716-446655440001",
  "public_order_id": "PUB123456789",
  "symbol": "AAPL",
  "strategy": "IRON_CONDOR",
  "action": "SELL",
  "quantity": 1,
  "price": 2.50,
  "total_value": 250.00,
  "commission": 0.65,
  "status": "PENDING",
  "created_at": "2025-09-25T17:05:00Z"
}
```

**Validation**:
- ✅ Order submitted to Public.com successfully
- ✅ Trade recorded in database
- ✅ Risk limits validated before execution

### 5. Monitor Order Status

**Objective**: Track order execution and position creation

**Steps**:
1. Check order status periodically
2. Verify fill execution
3. Confirm position creation

**API Call**:
```bash
curl -X GET http://localhost:11120/api/v1/trading/orders/880e8400-e29b-41d4-a716-446655440003 \
  -H "X-API-Key: your-api-key"
```

**Expected Response** (After Fill):
```json
{
  "trade_id": "880e8400-e29b-41d4-a716-446655440003",
  "public_order_id": "PUB123456789",
  "status": "FILLED",
  "status_message": "Order filled at market",
  "fill_price": 2.48,
  "fill_quantity": 1,
  "remaining_quantity": 0,
  "timestamp": "2025-09-25T17:05:30Z"
}
```

**Validation**:
- ✅ Order executed successfully
- ✅ Fill price within acceptable range
- ✅ Position created in system

### 6. Monitor Active Positions

**Objective**: Track live positions and real-time P&L

**Steps**:
1. Retrieve active positions
2. Monitor unrealized P&L
3. Check position risk metrics

**API Call**:
```bash
curl -X GET "http://localhost:11120/api/v1/trading/positions?account_id=660e8400-e29b-41d4-a716-446655440001" \
  -H "X-API-Key: your-api-key"
```

**Expected Response**:
```json
{
  "positions": [
    {
      "position_id": "990e8400-e29b-41d4-a716-446655440004",
      "account_id": "660e8400-e29b-41d4-a716-446655440001",
      "symbol": "AAPL",
      "strategy": "IRON_CONDOR",
      "quantity": 1,
      "average_price": 2.48,
      "current_price": 2.45,
      "unrealized_pnl": 3.00,
      "max_risk": 500.00,
      "status": "ACTIVE",
      "opened_at": "2025-09-25T17:05:30Z"
    }
  ]
}
```

**Validation**:
- ✅ Position actively tracked
- ✅ Real-time P&L calculation working
- ✅ Risk metrics properly displayed

### 7. Test Emergency Stop

**Objective**: Verify emergency stop functionality works

**Steps**:
1. Activate emergency stop
2. Attempt to place new order (should be rejected)
3. Verify all trading halted

**API Call**:
```bash
curl -X POST http://localhost:11120/api/v1/risk/emergency-stop \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "account_id": "660e8400-e29b-41d4-a716-446655440001",
    "reason": "Testing emergency stop functionality"
  }'
```

**Expected Response**:
```json
{
  "status": "EMERGENCY_STOP_ACTIVATED",
  "message": "All trading halted for account",
  "timestamp": "2025-09-25T17:10:00Z"
}
```

**Validation**:
- ✅ Emergency stop activated
- ✅ New orders rejected
- ✅ System maintains position tracking

### 8. Close Position

**Objective**: Close active position and realize P&L

**Steps**:
1. Deactivate emergency stop
2. Close active position
3. Verify trade execution and P&L realization

**API Call**:
```bash
curl -X POST http://localhost:11120/api/v1/trading/positions/990e8400-e29b-41d4-a716-446655440004/close \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "quantity": 1,
    "reason": "MANUAL"
  }'
```

**Expected Response**:
```json
{
  "trade_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "account_id": "660e8400-e29b-41d4-a716-446655440001",
  "public_order_id": "PUB123456790",
  "symbol": "AAPL",
  "strategy": "IRON_CONDOR",
  "action": "BUY",
  "quantity": 1,
  "price": 2.42,
  "total_value": 242.00,
  "commission": 0.65,
  "status": "PENDING",
  "created_at": "2025-09-25T17:15:00Z"
}
```

**Validation**:
- ✅ Closing trade submitted
- ✅ Position marked for closure
- ✅ P&L will be realized upon fill

## System Status Verification

### Health Check
```bash
curl -X GET http://localhost:11120/api/v1/status \
  -H "X-API-Key: your-api-key"
```

### Account Balance Check
```bash
curl -X GET http://localhost:11120/api/v1/accounts/660e8400-e29b-41d4-a716-446655440001/balance \
  -H "X-API-Key: your-api-key"
```

## Error Scenarios

### Market Closed
- **Scenario**: Attempt to trade outside market hours
- **Expected**: 409 Conflict with market hours message
- **Action**: Wait for market to open or adjust strategy timing

### Insufficient Buying Power
- **Scenario**: Order exceeds available buying power
- **Expected**: 400 Bad Request with risk limit message
- **Action**: Reduce position size or add funds to account

### API Connection Issues
- **Scenario**: Public.com API unavailable
- **Expected**: 503 Service Unavailable
- **Action**: Retry after delay, check Public.com status

### Risk Limit Breach
- **Scenario**: Order would exceed risk limits
- **Expected**: 400 Bad Request with risk violation
- **Action**: Adjust risk parameters or reduce order size

## Success Criteria

✅ **Authentication**: Successfully connect to Public.com API  
✅ **Risk Management**: Configure and enforce risk limits  
✅ **Order Execution**: Place and execute trades successfully  
✅ **Position Tracking**: Monitor positions and P&L in real-time  
✅ **Emergency Controls**: Emergency stop functionality working  
✅ **Error Handling**: Graceful handling of API failures and edge cases  
✅ **Compliance**: All trades logged for audit and regulatory requirements  

## Next Steps

1. **Strategy Implementation**: Implement Iron Condor, Butterfly Spread, and Calendar Spread strategies
2. **Backtesting**: Validate strategies against historical data
3. **Monitoring**: Set up alerts and monitoring dashboards
4. **Scaling**: Prepare for multiple account support
5. **Integration**: Connect with existing analytics and reporting systems

This quickstart demonstrates a complete live trading workflow with proper risk management, error handling, and compliance features.
