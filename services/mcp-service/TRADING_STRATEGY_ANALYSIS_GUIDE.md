# Trading Strategy Analysis Tool - MCP Integration Guide

## Overview

The Trading Strategy Analysis Tool is a comprehensive MCP (Model Context Protocol) service that allows you to analyze and monitor your trading strategies using natural language queries. It integrates with your existing service APIs to provide real-time insights into strategy performance, positions, and analytics.

## What It Does

The tool provides a unified interface to:

1. **Analyze Active Strategies** - See which strategies are currently enabled and their configurations
2. **Monitor Performance** - Track both backtest and live trading performance
3. **Compare Strategies** - Side-by-side comparison of multiple strategies
4. **Track Positions** - View current open positions by strategy
5. **Portfolio Analytics** - Access risk metrics and portfolio-level analytics

## Architecture

The tool integrates with the following existing services:

```
┌─────────────────────────────────────────────────────────┐
│           Trading Strategy Analysis Tool (MCP)          │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Backtest API │    │Portfolio API │    │Analytics API │
│  (Port 10001)│    │  (Port 8000) │    │  (Port 8000) │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                  ┌──────────────────┐
                  │   TimescaleDB    │
                  │  (Trading Data)  │
                  └──────────────────┘
```

## API Endpoints

### 1. Comprehensive Strategy Analysis
**GET** `/api/mcp/trading/strategies`

Returns complete analysis combining active strategies, backtest performance, live performance, and current positions.

**Example Response:**
```json
{
  "success": true,
  "timestamp": "2025-10-23T12:00:00Z",
  "summary": {
    "total_strategies": 5,
    "active_strategies": 3,
    "total_open_positions": 12,
    "total_unrealized_pnl": 1234.56,
    "portfolio_capital": 4000.0
  },
  "strategies": {
    "MultiStrategyEnsemble": {
      "status": "active",
      "config": {...},
      "backtest_performance": {...},
      "live_performance": {...},
      "current_positions": {...}
    }
  }
}
```

### 2. Active Strategies
**GET** `/api/mcp/trading/strategies/active`

Returns currently enabled strategies from configuration.

**Example Response:**
```json
{
  "success": true,
  "active_strategies": {
    "MultiStrategyEnsemble": {
      "name": "MultiStrategyEnsemble",
      "enabled": true,
      "config": {
        "strategy_weights": {
          "adaptive_wave": 0.30,
          "regime_switching": 0.20
        }
      }
    }
  },
  "total_active": 1
}
```

### 3. Backtest Performance
**GET** `/api/mcp/trading/strategies/performance/backtest?limit=50`

Returns strategy performance from historical backtests.

**Query Parameters:**
- `limit` (optional, default: 50) - Number of recent backtest runs to analyze

**Example Response:**
```json
{
  "success": true,
  "strategies": {
    "RSI_Strategy": {
      "runs": 10,
      "avg_return": 15.5,
      "avg_sharpe": 1.2,
      "avg_max_drawdown": 8.3,
      "total_trades": 450,
      "avg_win_rate": 68.5,
      "best_run": {"return": 25.3, "run_id": "abc123"},
      "worst_run": {"return": 8.2, "run_id": "def456"}
    }
  }
}
```

### 4. Live Trading Performance
**GET** `/api/mcp/trading/strategies/performance/live?days=30`

Returns live trading performance from the database.

**Query Parameters:**
- `days` (optional, default: 30) - Number of days to analyze

**Example Response:**
```json
{
  "success": true,
  "period_days": 30,
  "strategies": {
    "RSI_Strategy": {
      "trade_count": 45,
      "winning_trades": 31,
      "losing_trades": 14,
      "win_rate": 68.89,
      "total_pnl": 1234.56,
      "avg_pnl": 27.43,
      "best_trade": 150.25,
      "worst_trade": -45.30,
      "profit_factor": 2.15,
      "avg_win": 65.32,
      "avg_loss": -30.21
    }
  }
}
```

### 5. Strategy Comparison
**GET** `/api/mcp/trading/strategies/comparison?strategies=RSI,MACD,Ichimoku`

Compare multiple strategies side-by-side.

**Query Parameters:**
- `strategies` (optional) - Comma-separated list of strategy names. If omitted, compares all strategies.

**Example Response:**
```json
{
  "success": true,
  "comparison": [
    {
      "strategy": "RSI_Strategy",
      "status": "active",
      "backtest": {
        "avg_return": 15.5,
        "avg_sharpe": 1.2,
        "avg_win_rate": 68.5,
        "total_runs": 10
      },
      "live": {
        "total_pnl": 1234.56,
        "win_rate": 68.89,
        "profit_factor": 2.15,
        "trade_count": 45
      },
      "positions": {
        "open_count": 3,
        "unrealized_pnl": 123.45
      }
    }
  ]
}
```

### 6. Top Performing Strategies
**GET** `/api/mcp/trading/strategies/top?metric=pnl&limit=5`

Get top performing strategies by specified metric.

**Query Parameters:**
- `metric` (optional, default: "pnl") - Metric to sort by: `pnl`, `win_rate`, `sharpe`, `return`
- `limit` (optional, default: 5) - Number of top strategies to return

**Example Response:**
```json
{
  "success": true,
  "metric": "pnl",
  "top_strategies": [
    {
      "strategy": "RSI_Strategy",
      "live": {"total_pnl": 1234.56},
      ...
    }
  ]
}
```

### 7. Current Positions
**GET** `/api/mcp/trading/positions`

View all current open positions grouped by strategy.

**Example Response:**
```json
{
  "success": true,
  "positions_by_strategy": {
    "RSI_Strategy": {
      "positions": [
        {
          "symbol": "AAPL",
          "side": "long",
          "quantity": 100,
          "entry_price": 150.25,
          "current_price": 152.80,
          "unrealized_pnl": 255.00,
          "entry_time": "2025-10-20T10:30:00Z"
        }
      ],
      "position_count": 1,
      "total_unrealized_pnl": 255.00
    }
  },
  "total_open_positions": 12,
  "total_unrealized_pnl": 1234.56
}
```

### 8. Portfolio Analytics
**GET** `/api/mcp/trading/analytics`

Get portfolio-level risk and performance analytics.

**Example Response:**
```json
{
  "success": true,
  "risk_metrics": {
    "var_95": 0.015,
    "var_99": 0.025,
    "sharpe_ratio": 1.2,
    "max_drawdown": 0.08,
    "volatility": 0.18
  },
  "returns_metrics": {
    "total_return": 0.125,
    "annualized_return": 0.15
  },
  "trade_metrics": {
    "total_trades": 45,
    "winning_trades": 31
  }
}
```

## Usage Examples

### Using cURL

```bash
# Get comprehensive strategy analysis
curl http://localhost:8000/api/mcp/trading/strategies | jq

# Get active strategies
curl http://localhost:8000/api/mcp/trading/strategies/active | jq

# Compare specific strategies
curl "http://localhost:8000/api/mcp/trading/strategies/comparison?strategies=RSI,MACD" | jq

# Get top 3 strategies by win rate
curl "http://localhost:8000/api/mcp/trading/strategies/top?metric=win_rate&limit=3" | jq

# Get current positions
curl http://localhost:8000/api/mcp/trading/positions | jq

# Get live performance for last 60 days
curl "http://localhost:8000/api/mcp/trading/strategies/performance/live?days=60" | jq
```

### Using Python

```python
import aiohttp
import asyncio

async def get_strategy_analysis():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/mcp/trading/strategies') as response:
            data = await response.json()
            print(f"Total strategies: {data['summary']['total_strategies']}")
            print(f"Active strategies: {data['summary']['active_strategies']}")
            print(f"Total P&L: ${data['summary']['total_unrealized_pnl']:.2f}")

asyncio.run(get_strategy_analysis())
```

### Using Kubernetes Port Forward

If running in Kubernetes:

```bash
# Forward MCP service port
kubectl port-forward -n trading-system svc/mcp-service 8000:8000

# Then use the endpoints as above
curl http://localhost:8000/api/mcp/trading/strategies | jq
```

## Natural Language Queries (Future Enhancement)

With the MCP service running, you'll be able to ask questions like:

- "How are my current strategies performing?"
- "Which strategy has the best Sharpe ratio this month?"
- "Show me the P&L breakdown by strategy"
- "What's the current risk exposure across all strategies?"
- "Which strategies have open positions right now?"
- "Compare RSI and MACD strategies"
- "What are the top 3 performing strategies?"

## Integration with Existing Services

The tool seamlessly integrates with your existing APIs:

### Service Dependencies

| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| Backtest API | Strategy backtest data | 10001 | ✅ Available |
| Portfolio Service | Portfolio management | 8000 | ✅ Available |
| Analytics Service | Risk & performance metrics | 8000 | ✅ Available |
| Live Trading Service | Live trading data | 8000 | ✅ Available |
| TimescaleDB | Trade history & positions | 5432 | ✅ Available |

### Data Sources

1. **Configuration Files**
   - `/config/live_trading_strategies.yaml` - Active strategy configuration
   - `/src/utils/trading_config.py` - Trading system configuration

2. **Database Tables**
   - `backtest_runs` - Historical backtest results
   - `trades` - Live trading history and open positions

3. **Service APIs**
   - Backtest API: `/api/v1/runs` - Recent backtest runs
   - Analytics API: `/analytics/risk` - Risk metrics
   - Analytics API: `/analytics/returns` - Return metrics
   - Analytics API: `/analytics/trades` - Trade analytics

## Configuration

Environment variables (with defaults):

```bash
# Service URLs
BACKTEST_API_URL=http://backtest-api.trading-system.svc.cluster.local:10001
PORTFOLIO_API_URL=http://portfolio-service.trading-system.svc.cluster.local:8000
ANALYTICS_API_URL=http://analytics-service.trading-system.svc.cluster.local:8000
LIVE_TRADING_API_URL=http://live-trading-service.trading-system.svc.cluster.local:8000

# Database
DB_HOST=timescaledb-service.trading-system.svc.cluster.local
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=password
```

## Error Handling

The tool gracefully handles service failures:

- If a service is unavailable, it returns partial data with error indicators
- Database connection failures are logged but don't crash the service
- Timeouts are set to 30 seconds for all external API calls
- Each data source failure is tracked in the response

**Example error response:**
```json
{
  "success": true,
  "summary": {...},
  "data_sources": {
    "active_strategies": true,
    "backtest_performance": false,  // Service unavailable
    "live_performance": true,
    "portfolio_analytics": true,
    "current_positions": true
  }
}
```

## Performance Considerations

- All API calls are made asynchronously using `asyncio.gather()`
- Database queries use connection pooling
- Results are cached where appropriate
- Typical response time: 500-1500ms depending on data volume

## Troubleshooting

### Common Issues

1. **"Database connection failed"**
   - Check database credentials in environment variables
   - Verify TimescaleDB service is running
   - Check network connectivity from MCP service to database

2. **"API timeout"**
   - Increase timeout in configuration (default: 30s)
   - Check service health: `curl http://service-url/health`
   - Verify Kubernetes service networking

3. **"No strategies found"**
   - Verify `live_trading_strategies.yaml` exists and is readable
   - Check file permissions
   - Ensure at least one strategy has `enabled: true`

4. **"No backtest data"**
   - Run backtests first to populate data
   - Check `backtest_runs` table in database
   - Verify Backtest API is accessible

### Debug Endpoints

```bash
# Check MCP service health
curl http://localhost:8000/health

# List all available MCP tools
curl http://localhost:8000/api/mcp/tools

# Check service connectivity
curl http://localhost:8000/api/mcp/services/status
```

## Future Enhancements

- [ ] Real-time strategy performance streaming
- [ ] Strategy recommendations based on AI analysis
- [ ] Automated strategy optimization
- [ ] Risk alerts and notifications
- [ ] Strategy correlation analysis
- [ ] Historical performance charts
- [ ] Export to CSV/Excel
- [ ] Strategy backtesting on-demand via MCP
- [ ] Integration with fundamental analysis tool

## Contributing

To add new analysis capabilities:

1. Add methods to `TradingStrategyAnalysisTool` class
2. Add corresponding endpoints to `main.py`
3. Update this documentation
4. Add tests for new functionality

## Support

For issues or questions:
- Check the logs: `kubectl logs -n trading-system deployment/mcp-service`
- Review the MCP service documentation
- Contact the development team

---

**Last Updated:** October 23, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

