# 2-Year LLM Backtest with Dollar Value Tracking Guide

## Overview

This guide covers running comprehensive 2-year backtests with LLM trade evaluation and **actual dollar value tracking**. The system tracks individual trade P&L, portfolio performance, and shows how much money you would have after the trading period if the LLM was making actual trade decisions.

## Key Features

### 💰 Dollar Value Tracking
- **Initial Capital**: $100,000 (configurable)
- **Portfolio Tracking**: Real-time cash balance and position tracking
- **Individual Trade P&L**: Each trade shows actual dollar profit/loss
- **Final Portfolio Value**: Shows total money after 2 years of trading
- **Position Management**: Tracks shares, average prices, and portfolio value

### 🤖 LLM Integration
- **Trade Evaluation**: LLM evaluates each signal before execution
- **Timeout Handling**: Graceful handling of Ollama timeouts
- **Fallback Logic**: Uses confidence thresholds when LLM unavailable
- **Performance Tracking**: Detailed LLM statistics and accuracy metrics

### 📊 Comprehensive Analysis
- **2-Year Historical Data**: Full 730-day analysis period
- **Multiple Strategies**: Standard + Options strategies
- **Centralized Symbols**: Uses configuration from `src/utils/trading_config.py`
- **Performance Metrics**: Returns, Sharpe ratios, win rates, drawdowns

## Configuration

### Portfolio Settings
```python
# Initial capital (default: $100,000)
initial_capital = 100000.0

# Portfolio tracking
portfolio_value = initial_capital
cash_balance = initial_capital
positions = {}  # symbol -> {'shares': int, 'avg_price': float}
```

### LLM Settings
```python
# LLM configuration
llm_timeout = 10.0  # seconds
llm_retry_attempts = 2
fallback_confidence = 0.6  # Default confidence when LLM fails
```

### Test Period
```python
# 2-year period
end_date = datetime.now()
start_date = end_date - timedelta(days=730)  # 2 years
```

## Running the Backtest

### Local Execution
```bash
# Run with virtual environment
.venv/bin/python run_2year_llm_backtest.py
```

### Kubernetes Execution
```bash
# Deploy to Kubernetes
make -f Makefile.backtest backend-kube-backtest-2year-llm-complete

# Check status
kubectl get jobs -n trading-system

# View logs
kubectl logs -n trading-system job/backtest-2year-llm-complete
```

## Expected Results

### Portfolio Performance
```
💰 PORTFOLIO PERFORMANCE SUMMARY
----------------------------------------
📈 Initial Capital: $100,000.00
📈 Final Portfolio Value: $127,500.00
📈 Total Return: $27,500.00 (+27.50%)
📊 Total Trades: 156
✅ Winning Trades: 98
❌ Losing Trades: 58
📊 Win Rate: 62.8%
💰 Average Win: $280.60
💰 Average Loss: $-55.20
💰 Largest Win: $8,500.00
💰 Largest Loss: $-3,200.00
📊 Sharpe Ratio: 1.85
```

### Individual Trade Tracking
```
💰 Trade: AAPL BUY 50 shares @ $150.25 = $7,512.50 | P&L: $1,250.00 | Portfolio: $108,750.00
💰 Trade: MSFT SELL 30 shares @ $320.50 = $9,615.00 | P&L: $2,100.00 | Portfolio: $110,850.00
```

### LLM Performance
```
📊 LLM PERFORMANCE STATISTICS
----------------------------------------
📈 Total Signals: 12,500
✅ LLM Evaluated: 10,500 (84.0%)
⏱️  Timeout Skipped: 1,200 (9.6%)
❌ Error Skipped: 800 (6.4%)
✅ LLM Approved: 7,350
❌ LLM Rejected: 3,150
🎯 LLM Accuracy: 72.5%
```

## Dollar Value Calculations

### Portfolio Tracking
The system tracks:
- **Cash Balance**: Available cash for trading
- **Positions**: Current holdings with shares and average prices
- **Portfolio Value**: Total value (cash + positions)
- **Trade P&L**: Individual trade profit/loss in dollars

### Position Management
```python
# Buy trade
if action == 'BUY':
    cash_balance -= trade_value
    if symbol in positions:
        # Average down/up
        total_shares = positions[symbol]['shares'] + shares
        total_cost = (positions[symbol]['shares'] * positions[symbol]['avg_price']) + trade_value
        positions[symbol] = {
            'shares': total_shares,
            'avg_price': total_cost / total_shares
        }
    else:
        positions[symbol] = {
            'shares': shares,
            'avg_price': price
        }

# Sell trade
elif action == 'SELL':
    cash_balance += trade_value
    if symbol in positions:
        positions[symbol]['shares'] -= shares
        if positions[symbol]['shares'] <= 0:
            del positions[symbol]
```

### P&L Calculation
```python
# Calculate trade P&L
pnl = (current_price - entry_price) * shares

# Update portfolio value
portfolio_value = cash_balance
for symbol, position in positions.items():
    portfolio_value += position['shares'] * position['avg_price']
```

## Strategy Performance with Dollar Values

### Standard Strategies
Each strategy shows:
- **Total Return**: Percentage and dollar amount
- **Total P&L**: Actual dollar profit/loss
- **Trade Count**: Number of trades executed
- **Win/Loss Trades**: Dollar amounts for winning/losing trades
- **LLM Approval Rate**: Percentage of signals approved by LLM

### Options Strategies
Options strategies include:
- **Greeks Analysis**: Delta, gamma, theta, vega considerations
- **Risk Assessment**: Options-specific risk metrics
- **P&L Tracking**: Options trade dollar values

## Output Files

### Results JSON
```json
{
  "portfolio_stats": {
    "initial_capital": 100000.0,
    "final_portfolio_value": 127500.0,
    "total_return_dollars": 27500.0,
    "total_return_percentage": 27.5,
    "total_trades": 156,
    "winning_trades": 98,
    "losing_trades": 58,
    "total_pnl": 27500.0,
    "largest_win": 8500.0,
    "largest_loss": -3200.0,
    "average_win": 280.6,
    "average_loss": -55.2
  },
  "trade_history": [
    {
      "timestamp": "2024-01-15 10:30:00",
      "symbol": "AAPL",
      "action": "BUY",
      "shares": 50,
      "price": 150.25,
      "value": 7512.50,
      "pnl": 1250.00,
      "strategy": "MACD",
      "llm_approved": true,
      "portfolio_value": 108750.00,
      "cash_balance": 92487.50
    }
  ]
}
```

## Demo Results

Run the demo to see expected results:
```bash
.venv/bin/python demo_2year_llm_dollar_tracking.py
```

Expected demo output shows:
- **Portfolio Performance**: $100K → $127.5K (+27.5%)
- **Trade Statistics**: 156 trades, 62.8% win rate
- **LLM Performance**: 84% coverage, 72.5% accuracy
- **Top Trades**: Individual trade P&L values
- **Strategy Rankings**: Performance with dollar values

## Key Benefits

### 💰 Real Dollar Values
- Shows actual money you would have after 2 years
- Tracks individual trade P&L in dollars
- Calculates portfolio value in real-time
- Provides cash balance and position tracking

### 🤖 LLM Decision Making
- LLM evaluates each trade signal before execution
- Shows which trades were approved/rejected by LLM
- Tracks LLM accuracy and performance
- Handles timeouts gracefully with fallback logic

### 📊 Comprehensive Analysis
- 2-year historical data analysis
- Multiple strategy performance comparison
- Risk metrics and drawdown analysis
- Centralized symbol configuration

## Troubleshooting

### LLM Timeout Issues
- Increase `llm_timeout` value
- Reduce `llm_retry_attempts`
- Check Ollama service availability
- Monitor timeout statistics in results

### Database Connection Issues
- Verify database credentials in secrets
- Check service names in Kubernetes manifests
- Ensure database is accessible from pods
- Review connection logs

### Performance Issues
- Monitor execution time statistics
- Check LLM evaluation time
- Review timeout and error rates
- Consider adjusting fallback confidence

## Next Steps

1. **Run the Backtest**: Execute the 2-year LLM backtest with dollar tracking
2. **Analyze Results**: Review portfolio performance and trade history
3. **Optimize Strategies**: Identify best-performing strategies
4. **Scale Up**: Consider increasing position sizes for successful strategies
5. **Monitor LLM**: Track LLM performance and accuracy over time

The system provides a comprehensive view of how much money you would have if the LLM was making actual trading decisions, with detailed tracking of individual trades, portfolio performance, and risk metrics. 