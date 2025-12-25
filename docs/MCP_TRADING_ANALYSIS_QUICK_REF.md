# MCP Trading Strategy Analysis - Quick Reference Card

## 🚀 Quick Start

```bash
# Port forward MCP service (if in Kubernetes)
kubectl port-forward -n trading-system svc/mcp-service 8000:8000

# Test connection
curl http://localhost:8000/health
```

## 📊 Common Queries

### Get Everything
```bash
curl http://localhost:8000/api/mcp/trading/strategies | jq
```

### Active Strategies Only
```bash
curl http://localhost:8000/api/mcp/trading/strategies/active | jq '.active_strategies | keys'
```

### Current Positions
```bash
curl http://localhost:8000/api/mcp/trading/positions | jq
```

### Performance (Last 30 Days)
```bash
curl http://localhost:8000/api/mcp/trading/strategies/performance/live | jq
```

### Top 5 by P&L
```bash
curl "http://localhost:8000/api/mcp/trading/strategies/top?metric=pnl&limit=5" | jq
```

### Top 5 by Win Rate
```bash
curl "http://localhost:8000/api/mcp/trading/strategies/top?metric=win_rate&limit=5" | jq
```

### Compare Specific Strategies
```bash
curl "http://localhost:8000/api/mcp/trading/strategies/comparison?strategies=RSI,MACD,Ichimoku" | jq
```

### Portfolio Analytics
```bash
curl http://localhost:8000/api/mcp/trading/analytics | jq
```

## 🎯 Key Endpoints

| Endpoint | Purpose | Common Use |
|----------|---------|------------|
| `/api/mcp/trading/strategies` | Complete analysis | Daily review |
| `/api/mcp/trading/strategies/active` | Active strategies | Config check |
| `/api/mcp/trading/strategies/performance/live` | Live P&L | Performance tracking |
| `/api/mcp/trading/strategies/top` | Best performers | Quick wins |
| `/api/mcp/trading/positions` | Open positions | Risk management |
| `/api/mcp/trading/analytics` | Risk metrics | Risk assessment |

## 💡 Pro Tips

### Daily Morning Routine
```bash
# 1. Check overall status
curl http://localhost:8000/api/mcp/trading/strategies | jq '.summary'

# 2. Review open positions
curl http://localhost:8000/api/mcp/trading/positions | jq '.total_open_positions, .total_unrealized_pnl'

# 3. Check top performers
curl http://localhost:8000/api/mcp/trading/strategies/top | jq
```

### Weekly Performance Review
```bash
# Last 7 days performance
curl "http://localhost:8000/api/mcp/trading/strategies/performance/live?days=7" | jq

# Compare all strategies
curl http://localhost:8000/api/mcp/trading/strategies/comparison | jq
```

### Find Underperformers
```bash
# Strategies with negative P&L
curl http://localhost:8000/api/mcp/trading/strategies/performance/live | \
  jq '.strategies | to_entries | map(select(.value.total_pnl < 0)) | from_entries'
```

### Check Risk Metrics
```bash
# Quick risk snapshot
curl http://localhost:8000/api/mcp/trading/analytics | \
  jq '{sharpe: .risk_metrics.sharpe_ratio, max_dd: .risk_metrics.max_drawdown, var_95: .risk_metrics.var_95}'
```

## 📈 Metrics Reference

### Backtest Metrics
- `avg_return` - Average return percentage across all backtest runs
- `avg_sharpe` - Average Sharpe ratio (risk-adjusted return)
- `avg_max_drawdown` - Average maximum drawdown
- `avg_win_rate` - Average percentage of winning trades
- `total_trades` - Total number of trades across all runs

### Live Trading Metrics
- `total_pnl` - Total profit/loss in dollars
- `win_rate` - Percentage of winning trades
- `profit_factor` - Ratio of average win to average loss
- `trade_count` - Total number of trades
- `avg_pnl` - Average profit/loss per trade

### Risk Metrics
- `var_95` - Value at Risk (95% confidence)
- `sharpe_ratio` - Risk-adjusted return
- `max_drawdown` - Maximum peak-to-trough decline
- `volatility` - Standard deviation of returns
- `beta` - Correlation with market

## 🔧 Troubleshooting

### No Data Returned
```bash
# Check service health
curl http://localhost:8000/health

# Check if database is accessible
curl http://localhost:8000/api/mcp/services/status
```

### Partial Data
```json
// Check data_sources in response
{
  "data_sources": {
    "backtest_performance": false  // This service is down
  }
}
```

### Slow Responses
```bash
# Reduce scope
curl "http://localhost:8000/api/mcp/trading/strategies/performance/backtest?limit=10"
curl "http://localhost:8000/api/mcp/trading/strategies/performance/live?days=7"
```

## 🎨 Formatting Output

### Pretty Print with jq
```bash
curl http://localhost:8000/api/mcp/trading/strategies | jq '.'
```

### Extract Specific Fields
```bash
# Just the summary
curl http://localhost:8000/api/mcp/trading/strategies | jq '.summary'

# Just strategy names
curl http://localhost:8000/api/mcp/trading/strategies | jq '.strategies | keys'

# P&L by strategy
curl http://localhost:8000/api/mcp/trading/strategies | jq '.strategies | to_entries | map({strategy: .key, pnl: .value.live_performance.total_pnl})'
```

### Save to File
```bash
# Save full report
curl http://localhost:8000/api/mcp/trading/strategies > strategy_report_$(date +%Y%m%d).json

# Save and view
curl http://localhost:8000/api/mcp/trading/strategies | tee report.json | jq '.summary'
```

## 🔗 Integration Examples

### Python
```python
import aiohttp
import asyncio

async def check_strategies():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/mcp/trading/strategies') as r:
            data = await r.json()
            return data['summary']

print(asyncio.run(check_strategies()))
```

### JavaScript
```javascript
fetch('http://localhost:8000/api/mcp/trading/strategies')
  .then(r => r.json())
  .then(data => console.log(data.summary));
```

### Shell Script
```bash
#!/bin/bash
RESPONSE=$(curl -s http://localhost:8000/api/mcp/trading/strategies)
TOTAL_PNL=$(echo $RESPONSE | jq -r '.summary.total_unrealized_pnl')
echo "Total Unrealized P&L: $TOTAL_PNL"
```

## 📱 Mobile/Remote Access

### Via SSH Tunnel
```bash
# From your laptop
ssh -L 8000:localhost:8000 user@trading-server

# Then access locally
curl http://localhost:8000/api/mcp/trading/strategies
```

### Via kubectl from Remote
```bash
# Port forward over SSH
kubectl port-forward -n trading-system svc/mcp-service 8000:8000

# Access from remote machine
curl http://localhost:8000/api/mcp/trading/strategies
```

## ⚡ Performance Tips

1. **Use limits** - Reduce data volume with `?limit=10`
2. **Narrow time ranges** - `?days=7` instead of default 30
3. **Specific strategies** - Compare only what you need
4. **Cache results** - Save to file for repeated analysis
5. **Parallel requests** - Use async for multiple endpoints

## 🔐 Security Notes

- MCP service runs in Kubernetes cluster
- No authentication required for internal access
- Use kubectl port-forward for external access
- Never expose directly to internet
- Use service mesh for production security

## 📞 Support

**Health Check:** `curl http://localhost:8000/health`  
**Service Status:** `curl http://localhost:8000/api/mcp/services/status`  
**Available Tools:** `curl http://localhost:8000/api/mcp/tools`

---

**Tip:** Bookmark this page and add these commands to your shell aliases for quick access!

```bash
# Add to ~/.bashrc or ~/.zshrc
alias mcp-status='curl -s http://localhost:8000/api/mcp/trading/strategies | jq .summary'
alias mcp-positions='curl -s http://localhost:8000/api/mcp/trading/positions | jq'
alias mcp-top='curl -s "http://localhost:8000/api/mcp/trading/strategies/top?limit=5" | jq'
```

