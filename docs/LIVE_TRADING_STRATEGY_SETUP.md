# Live Trading Strategy Setup Guide

This guide walks you through setting up trading strategies for the live trading service, similar to the paper trading configuration but with real money and enhanced risk controls.

## 🎯 Overview

The live trading service supports the same strategies as paper trading but with additional safety measures:

- **Iron Condor**: Range-bound market strategy
- **Butterfly Spread**: Directional play strategy  
- **Calendar Spread**: Time decay strategy
- **Elliott Wave Integration**: Advanced pattern-based strategies

## 🚀 Quick Start

### 1. Prerequisites

- Live trading service running on port 11120
- Public.com account with API access
- Valid access token from Public.com

### 2. Basic Setup

```bash
# Make the setup script executable
chmod +x scripts/setup_live_trading_strategies.py

# Run the setup script
python scripts/setup_live_trading_strategies.py
```

### 3. Interactive Setup

The script will guide you through:

1. **Health Check**: Verify live trading service is running
2. **Authentication**: Connect to Public.com API
3. **Account Selection**: Choose trading account
4. **Strategy Configuration**: Set up trading strategies
5. **Risk Management**: Configure risk limits and controls
6. **Testing**: Optional test order submission

## 📊 Strategy Configuration

### Iron Condor Strategy

```yaml
iron_condor:
  name: "IRON_CONDOR"
  enabled: true
  max_position_size: 0.05      # 5% of portfolio
  max_risk_per_trade: 0.01     # 1% risk per trade
  max_daily_trades: 5
  max_daily_loss: 500.0
  symbols: ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"]
```

**Risk Profile:**
- Conservative approach for range-bound markets
- Limited profit potential but high probability of success
- Suitable for stable market conditions

### Butterfly Spread Strategy

```yaml
butterfly_spread:
  name: "BUTTERFLY_SPREAD"
  enabled: true
  max_position_size: 0.03      # 3% of portfolio
  max_risk_per_trade: 0.008    # 0.8% risk per trade
  max_daily_trades: 3
  max_daily_loss: 300.0
  symbols: ["SPY", "QQQ", "AAPL"]
```

**Risk Profile:**
- Directional strategy with limited risk
- Higher profit potential than Iron Condor
- Requires more precise market timing

### Calendar Spread Strategy

```yaml
calendar_spread:
  name: "CALENDAR_SPREAD"
  enabled: true
  max_position_size: 0.04      # 4% of portfolio
  max_risk_per_trade: 0.009    # 0.9% risk per trade
  max_daily_trades: 4
  max_daily_loss: 400.0
  symbols: ["SPY", "QQQ", "AAPL", "MSFT"]
```

**Risk Profile:**
- Time decay focused strategy
- Profits from time value erosion
- Moderate risk with steady income potential

## 🛡️ Risk Management

### Portfolio Limits

```yaml
portfolio_limits:
  max_total_exposure: 0.20     # 20% total portfolio exposure
  max_single_symbol: 0.10      # 10% max per symbol
  min_cash_reserve: 0.20       # 20% cash reserve
  max_daily_loss: 1000.0       # $1000 max daily loss
  max_daily_trades: 15         # 15 trades per day max
```

### Trailing Stops

```yaml
trailing_stops:
  iron_condor:
    profit_threshold: 0.5      # 50% profit
    trail_percentage: 0.05     # 5% below current
    min_profit: 0.3            # Minimum profit to activate
```

### Emergency Controls

```yaml
emergency_controls:
  stop_loss_percentage: 0.15   # 15% stop loss
  max_drawdown: 0.20           # 20% max drawdown
  emergency_stop_enabled: true
```

## 🌊 Elliott Wave Integration

### Configuration

```yaml
elliott_wave:
  enabled: true
  service_url: "http://elliott-wave-service.trading-system.svc.cluster.local:8000"
  confidence_threshold: 0.6
  min_pattern_strength: 0.7
  fibonacci_levels: [0.236, 0.382, 0.5, 0.618, 0.786]
```

### Elliott Wave Strategies

#### Impulse Pattern Strategy

```yaml
elliott_wave_impulse:
  name: "ELLIOTT_WAVE_IMPULSE"
  enabled: true
  pattern_type: "impulse"
  confidence_threshold: 0.8
  options_strategy: "StraddleStrategy"
  risk_level: "high"
  max_position_size: 0.02
  max_risk_per_trade: 0.005
```

#### Corrective Pattern Strategy

```yaml
elliott_wave_corrective:
  name: "ELLIOTT_WAVE_CORRECTIVE"
  enabled: true
  pattern_type: "corrective"
  confidence_threshold: 0.7
  options_strategy: "IronCondorStrategy"
  risk_level: "medium"
  max_position_size: 0.03
  max_risk_per_trade: 0.008
```

## 🔧 API Endpoints

### Strategy Management

```bash
# Get current strategies
curl -s http://localhost:11120/api/v1/risk/profile/{account_id}

# Update risk profile
curl -X PUT http://localhost:11120/api/v1/risk/profile/{account_id} \
  -H "Content-Type: application/json" \
  -d '{
    "max_position_size": 0.05,
    "max_portfolio_risk": 0.20,
    "max_daily_loss": 1000.0,
    "max_daily_trades": 15,
    "allowed_strategies": ["IRON_CONDOR", "BUTTERFLY_SPREAD", "CALENDAR_SPREAD"]
  }'
```

### Order Submission

```bash
# Submit Iron Condor order
curl -X POST http://localhost:11120/api/v1/trading/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SPY",
    "strategy": "IRON_CONDOR",
    "legs": [
      {"action": "SELL", "option_type": "CALL", "strike_price": 450, "quantity": 1, "premium": 2.50},
      {"action": "BUY", "option_type": "CALL", "strike_price": 455, "quantity": 1, "premium": 1.00},
      {"action": "SELL", "option_type": "PUT", "strike_price": 440, "quantity": 1, "premium": 2.00},
      {"action": "BUY", "option_type": "PUT", "strike_price": 435, "quantity": 1, "premium": 0.50}
    ],
    "order_type": "LIMIT",
    "limit_price": 3.00,
    "time_in_force": "DAY",
    "estimated_premium": 3.00,
    "estimated_risk": 1000.0
  }' \
  --data-urlencode "account_id=your-account-id"
```

### Position Monitoring

```bash
# Get current positions
curl -s http://localhost:11120/api/v1/trading/positions

# Get account balance
curl -s http://localhost:11120/api/v1/accounts/{account_id}/balance

# Get risk profile
curl -s http://localhost:11120/api/v1/risk/profile/{account_id}
```

## 📈 Monitoring and Alerts

### Real-time Monitoring

```bash
# Check service health
curl -s http://localhost:11120/health

# Check system status
curl -s http://localhost:11120/api/v1/status

# Check market hours
curl -s http://localhost:11120/api/v1/status/market-hours
```

### Performance Tracking

The system automatically tracks:

- **Trade Performance**: P&L, win rate, drawdown
- **Strategy Performance**: Individual strategy metrics
- **Risk Metrics**: VaR, exposure, Greeks
- **Portfolio Health**: Overall portfolio status

### Alert Configuration

```yaml
monitoring:
  enable_alerts: true
  alert_channels: ["email", "webhook"]
  
  alerts:
    position_risk_breach: true
    daily_loss_limit: true
    trade_execution_failure: true
    market_hours_change: true
    elliott_wave_signal: true
```

## 🧪 Testing and Validation

### 1. Paper Trading First

Before going live, test your strategies with paper trading:

```bash
# Start paper trading with same strategies
python scripts/setup_paper_trading.py config/paper_trading_strategies.yaml
```

### 2. Small Position Testing

Start with small position sizes:

```yaml
# Conservative initial setup
portfolio:
  initial_capital: 1000.0      # Start small
  max_position_size: 0.01      # 1% max position
  max_risk_per_trade: 0.005    # 0.5% risk per trade
```

### 3. Gradual Scaling

Increase position sizes as you gain confidence:

```yaml
# After successful testing
portfolio:
  initial_capital: 10000.0     # Increase capital
  max_position_size: 0.05      # 5% max position
  max_risk_per_trade: 0.01     # 1% risk per trade
```

## 🚨 Safety Guidelines

### 1. Start Conservative

- Begin with small position sizes
- Use conservative risk limits
- Test thoroughly before scaling up

### 2. Monitor Closely

- Check positions regularly
- Monitor risk metrics
- Set up alerts for important events

### 3. Emergency Controls

- Know how to stop trading quickly
- Have emergency stop procedures
- Keep contact information for support

### 4. Risk Management

- Never risk more than you can afford to lose
- Diversify across strategies and symbols
- Maintain adequate cash reserves

## 🔄 Maintenance and Updates

### Regular Tasks

1. **Daily**: Check positions and P&L
2. **Weekly**: Review strategy performance
3. **Monthly**: Adjust risk parameters if needed
4. **Quarterly**: Full strategy review and optimization

### Configuration Updates

```bash
# Update strategy configuration
python scripts/setup_live_trading_strategies.py --update-config

# Reload risk parameters
curl -X PUT http://localhost:11120/api/v1/risk/profile/{account_id} \
  -H "Content-Type: application/json" \
  -d @config/updated_risk_profile.json
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:11120/docs
- **Paper Trading Guide**: `docs/ENHANCED_PAPER_TRADING_GUIDE.md`
- **Risk Management**: `docs/RISK_MANAGEMENT_GUIDE.md`
- **Elliott Wave Analysis**: `docs/ELLIOTT_WAVE_GUIDE.md`

## 🆘 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check Public.com access token
   - Verify account is active
   - Ensure sufficient permissions

2. **Order Rejected**
   - Check market hours
   - Verify account balance
   - Review risk limits

3. **Service Unavailable**
   - Check live trading service health
   - Verify port forwarding
   - Review service logs

### Getting Help

- Check service logs: `kubectl logs -f deployment/live-trading-service`
- Review API documentation: http://localhost:11120/docs
- Monitor system status: http://localhost:11120/api/v1/status

---

**⚠️ Important**: Live trading involves real money and real risk. Always test thoroughly with paper trading first and start with small position sizes. Never risk more than you can afford to lose.


