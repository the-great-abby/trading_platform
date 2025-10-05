# 🚀 Port Mapping Guide - Trading System

## 📊 Current Status

**Last Updated**: 2025-01-15 12:45:00 EST
**Active Port Forwards**: 4  
**Total Services**: 50+  
**Paper Trading**: ✅ **ACTIVE** (Running since 16:54:38)  
**RSS Feed Service**: ✅ **ACTIVE** (Running since 11:01:00)  
**RSS Dashboard**: ✅ **ACTIVE** (Running since 11:01:00)  
**Strategy Service**: ✅ **ACTIVE** (Updated with Public.com config)  
**Secrets Management**: ✅ **ACTIVE** (Kubernetes secrets via Makefile)  

## 🎯 Currently Active Port Forwards

| Service | External Port | Internal Port | Status | URL | Last Checked |
|---------|---------------|---------------|--------|-----|--------------|
| Strategy Service | 11001 | 80 | ✅ Active | http://localhost:11001/ | 2025-09-29 08:10 |
| **Strategy Testing Framework** | **11003** | **8000** | ✅ **New** | **http://localhost:11003/** | **2025-01-15 12:45** |
| Live Trading Service | 11120 | 8080 | ✅ Active | http://localhost:11120/ | 2025-09-29 08:10 |
| Unified Trading Dashboard | 11115 | 80 | ✅ Active | http://localhost:11115/ | 2025-09-29 08:10 |

## 🚀 Live Trading System Status

**Configuration**: ✅ **ACTIVE** (Optimized Strategies Running)  
**Expected Annual Return**: +7.53% (vs previous -1.23%)  
**Sharpe Ratio**: +2.177 (vs previous +0.384)  
**Status**: All optimized strategies active and trading  
**Monitoring**: Live trading monitor available  

### 🎯 Active Strategies
- **Calendar Spread**: ✅ 12% max position, 4 daily trades
- **Iron Condor**: ✅ 12% max position, 4 daily trades  
- **Butterfly Spread**: ✅ 12% max position, 4 daily trades
- **Risk Management**: ✅ Enhanced (11% drawdown limit, 15% cash reserve)

### 🔧 Quick Commands
```bash
# Monitor live trading
python3 live_trading_monitor.py single

# Continuous monitoring (every 5 minutes)
python3 live_trading_monitor.py continuous 5

# Check strategy service
python3 simplified_system_monitor.py single
```

## 📈 Paper Trading Status

| Metric | Value | Details |
|--------|-------|---------|
| **Status** | ✅ **RUNNING** | Active since 2025-09-28 17:41:28 |
| **Portfolio Value** | **$4,000.00** | Initial capital |
| **Total Trades** | **0** | No completed trades yet |
| **Total P&L** | **$0.00** | No realized gains/losses |
| **Active Strategies** | **5** | ElliottWaveCorrective, ButterflySpread, SectorRotation, VolatilityTrading, CollarStrategy |
| **Trading Symbols** | **3** | AMD, PYPL, INTC |
| **Trading Interval** | **5 minutes** | 300 seconds between cycles |
| **Max Risk Per Trade** | **5%** | $100 max risk per trade |
| **Max Position Size** | **10%** | $200 max position size |
| **Last Trade** | **None** | No trades yet |

### 🎯 Strategy Configuration
- **Primary**: Iron Condor (Options strategy for range-bound markets)
- **Secondary**: Regime Switching (Adaptive strategy based on market conditions)  
- **Backup**: Bollinger Bands (Mean reversion strategy)## 📋 Service Categories & Port Assignments

### **🔧 Core Infrastructure (11000-11099)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| TimescaleDB | 11140 | 5432 | ⚠️ **DEPRECATED** | localhost:11140 | **DEPRECATED** - Moved to external database |
| Redis | 11379 | 6379 | ⚠️ **DEPRECATED** | localhost:11379 | **DEPRECATED** - Moved to external Redis service |
| RabbitMQ | 11144 | 5672 | ⚠️ **DEPRECATED** | localhost:11144 | **DEPRECATED** - Moved to external RabbitMQ service |
| PostgreSQL Vector | 11180 | 5432 | ⚠️ **DEPRECATED** | localhost:11180 | **DEPRECATED** - Moved to external vector storage |
| Ollama Controller DB | - | 5432 | ⚠️ **DEPRECATED** | - | **DEPRECATED** - Use external postgres service |

### **📊 Unified Dashboards (11110-11119)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Unified Analytics | 11114 | 80 | ✅ Active | http://localhost:11114/ | Main analytics dashboard |
| Unified Trading | 11115 | 80 | ✅ Active | http://localhost:11115/ | Trading interface (includes performance metrics) |
| Unified News | 11116 | 80 | ✅ Active | http://localhost:11116/ | News dashboard |
| MCP Service | 11117 | 8000 | ✅ Active | http://localhost:11117/ | Model Context Protocol service |
| Performance Dashboard | 11116 | 80 | ⚠️ **DEPRECATED** | http://localhost:11116/ | **DEPRECATED** - Functionality moved to unified-trading-dashboard |

### **🧪 Strategy Testing Framework (11000-11009)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| **Strategy Testing Framework** | **11003** | **8000** | ✅ **New** | **http://localhost:11003/** | **Comprehensive strategy validation and testing API** |
| Strategy Testing Database | 11004 | 5432 | ❌ Not Forwarded | localhost:11004 | Testing framework database |

### **🔍 Backtest Validation Framework (11080-11089)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| **Validation Framework API** | **11080** | **8000** | ❌ **Not Forwarded** | **http://localhost:11080/** | **Backtest script validation and testing framework** |
| Validation Framework Database | 11081 | 5432 | ❌ Not Forwarded | localhost:11081 | External validation database connection |

### **💼 Trading Services (11080-11099)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Market Data Service | 11084 | 11084 | ❌ Not Forwarded | http://localhost:11084/ | Market data API |
| Backtest API | 11101 | 10001 | ❌ Not Forwarded | http://localhost:11101/ | Backtesting service |
| Trading Engine | 11080 | 8080 | ❌ Not Forwarded | http://localhost:11080/ | Core trading engine |
| **Live Trading Service** | **11120** | **8080** | ✅ **Active** | **http://localhost:11120/** | **Live trading with Public.com API integration** |
| **Elliott Wave Analysis Service** | **11085** | **8000** | ❌ **Not Forwarded** | **http://localhost:11085/** | **Elliott Wave pattern detection with options integration** |
| **Trade Recovery Service** | **11086** | **10001** | ❌ **Not Forwarded** | **http://localhost:11086/** | **~~Active trade recovery and management service~~** **CONSOLIDATED INTO LIVE TRADING SERVICE** |

### **📊 Advanced Portfolio Management Services (11180-11189)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Enhanced Portfolio Service | 11180 | 80 | ❌ Not Forwarded | http://localhost:11180/ | Advanced portfolio management with MPT, Black-Litterman, Risk Parity |
| Enhanced Risk Management Service | 11081 | 80 | ✅ Active | http://localhost:11081/ | Advanced risk management with VaR, CVaR, stress testing, factor analysis |

### **⚠️ Comprehensive Risk Management Framework (11182-11189)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Risk Management Service | 11182 | 80 | ❌ Not Forwarded | http://localhost:11182/ | **RESOURCE-CONSTRAINED**: 1 replica, VaR, stress testing, compliance |
| Risk Management Database | 11183 | 5432 | ❌ Not Forwarded | localhost:11183 | **RESOURCE-CONSTRAINED**: 1 replica, 5GB storage |
| Risk Management Redis | 11184 | 6379 | ❌ Not Forwarded | localhost:11184 | **RESOURCE-CONSTRAINED**: 1 replica, 256MB memory |

### **🤖 AI/ML Services (11120-11139)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| LLM Proxy | 11081 | 11081 | ❌ Not Forwarded | http://localhost:11081/ | LLM proxy service |
| AI Analysis Service | 11085 | 11085 | ❌ Not Forwarded | http://localhost:11085/ | AI analysis API |
| LLM Service | 11109 | 11109 | ❌ Not Forwarded | http://localhost:11109/ | LLM service |
| RAG Chat Service | 11116 | 8000 | ✅ Active | http://localhost:11116/ | Kubernetes RAG chat interface |

### **📈 Monitoring Services (11190-11199)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Prometheus | 11190 | 9090 | ❌ Not Forwarded | http://localhost:11190/ | Metrics collection |
| Grafana | 11102 | 3000 | ⚠️ **DEPRECATED** | http://localhost:11102/ |  **DEPRECATED** Monitoring dashboards |
| Postgres Exporter | 11191 | 9187 | ❌ Not Forwarded | localhost:11191 | Database metrics |
| RabbitMQ Exporter | 11192 | 9419 | ❌ Not Forwarded | localhost:11192 | Message queue metrics |
| Node Exporter | 11193 | 9100 | ❌ Not Forwarded | localhost:11193 | System metrics |

### **🔄 Data Processing Services (11100-11119)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Data Processing | 11095 | 11095 | ❌ Not Forwarded | localhost:11095 | Data processing pipeline |
| Data Transformation | 11135 | 11135 | ❌ Not Forwarded | localhost:11135 | Data transformation |
| Data Analysis | 11136 | 11136 | ❌ Not Forwarded | localhost:11136 | Data analysis service |

### **📰 RSS & News Services (11150-11169)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| RSS Feed Service | 11004 | 11004 | ✅ **Active** | http://localhost:11004/ | RSS feed processing with news integration |
| RSS Dashboard | 8080 | 80 | ✅ **Active** | http://localhost:8080/ | RSS feed viewer and management |
| News Scanning | 11151 | 11151 | ❌ Not Forwarded | localhost:11151 | News scanning service |

### **🔑 Authentication & Security (11170-11179)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| VAPID Service | 11170 | 11170 | ❌ Not Forwarded | localhost:11170 | VAPID key management |

## 🚀 Quick Commands

### **Check Current Status**
```bash
# Check active port forwards
ps aux | grep "kubectl port-forward" | grep -v grep

# Check paper trading status
curl -s http://localhost:11115/api/paper-trading/status

# Run health check
make simple-status
```

### **Paper Trading Commands**
```bash
# Check paper trading status
curl -s http://localhost:11115/api/paper-trading/status | jq

# Check paper trading configuration
curl -s http://localhost:11115/api/paper-trading/config | jq

# View trading dashboard
open http://localhost:11115/paper-trading

# Stop paper trading
curl -X POST http://localhost:11115/api/paper-trading/stop

# Update PORT_MAP.md with current paper trading status
python scripts/update_paper_trading_status.py
```

### **RSS & News Services Commands**
```bash
# Check RSS feed service health
curl -s http://localhost:11004/health | jq

# View RSS feed (trading recommendations)
curl -s http://localhost:11004/rss/daily-recommendations

# Check RSS dashboard health
curl -s http://localhost:8080/health | jq

# Open RSS dashboard in browser
open http://localhost:8080/

# Get latest trading recommendations
curl -s http://localhost:11004/rss/daily-recommendations | head -50

# Check news integration status
curl -s http://localhost:11004/api/news/status | jq
```

### **Advanced Portfolio Management Commands**
```bash
# Check portfolio service status
curl -s http://localhost:11180/api/v1/status | jq

# Check risk management service status
curl -s http://localhost:11181/api/v1/status | jq

# Create a new portfolio
curl -X POST http://localhost:11180/api/v1/portfolios \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Portfolio", "owner_id": "user123", "risk_tolerance": "MODERATE"}'

# Get portfolio optimization results
curl -s http://localhost:11180/api/v1/portfolios/portfolio-123/optimization/mpt | jq

# Perform risk assessment
curl -X POST http://localhost:11181/api/v1/risk/assess \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": "portfolio-123", "portfolio_value": 100000, "positions": []}'

# Run stress test
curl -X POST http://localhost:11181/api/v1/risk/stress-test \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": "portfolio-123", "scenarios": [{"name": "Market Crash", "shock_return": -0.20}]}'
```

### **Strategy Testing Framework Commands**
```bash
# Check testing framework health
curl -s http://localhost:11003/api/v1/testing/health | jq

# List available strategies
curl -s http://localhost:11003/api/v1/testing/strategies | jq

# Validate Elliott Wave strategy
curl -X POST http://localhost:11003/api/v1/testing/strategies/validate \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ElliottWaveStrategy",
    "config": {
      "symbols": ["AAPL"],
      "timeframe": "1d",
      "lookback_periods": 50
    }
  }'

# Test signal generation
curl -X POST http://localhost:11003/api/v1/testing/signals/test \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ElliottWaveStrategy",
    "symbol": "AAPL",
    "test_config": {
      "confidence_threshold": 0.8
    },
    "mock_data": {
      "price_data": []
    }
  }'

# Test performance metrics
curl -X POST http://localhost:11003/api/v1/testing/performance/test \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ElliottWaveStrategy",
    "test_config": {
      "symbols": ["AAPL"]
    },
    "signal_count": 100
  }'

# Generate mock market data
curl -X POST http://localhost:11003/api/v1/testing/mock-data/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "timeframe": "1d",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "market_regime": "bull",
    "initial_price": 150.0,
    "volatility": 0.2
  }'

# Create comprehensive test suite
curl -X POST http://localhost:11003/api/v1/testing/test-suites/create \
  -H "Content-Type: application/json" \
  -d '{
    "suite_name": "Elliott Wave Comprehensive Test",
    "strategy_name": "ElliottWaveStrategy",
    "test_cases": [
      {
        "name": "Bull Market Test",
        "type": "signal",
        "config": {"market_regime": "bull"},
        "expected_outcomes": {"min_signals": 10}
      }
    ]
  }'

# Open API documentation
open http://localhost:11003/docs
```

### **Backtest Validation Framework Commands**
```bash
# Check validation framework health
curl -s http://localhost:11080/health | jq

# Discover backtest scripts
curl -s http://localhost:11080/api/v1/scripts/discover | jq

# List all scripts
curl -s http://localhost:11080/api/v1/scripts/ | jq

# Get script information
curl -s http://localhost:11080/api/v1/scripts/script-123 | jq

# Execute single script validation
curl -X POST http://localhost:11080/api/v1/validation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "my_backtest_script",
    "test_config_id": "basic_config",
    "timeout_seconds": 300
  }'

# Check validation status
curl -s http://localhost:11080/api/v1/validation/status/script-123 | jq

# Get validation results
curl -s http://localhost:11080/api/v1/validation/results/script-123 | jq

# Execute batch validation
curl -X POST http://localhost:11080/api/v1/batch/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script_ids": ["script1", "script2", "script3"],
    "parallel_execution": true,
    "max_concurrent": 5
  }'

# Check batch status
curl -s http://localhost:11080/api/v1/batch/status/batch-123 | jq

# Get batch results
curl -s http://localhost:11080/api/v1/batch/results/batch-123 | jq

# Generate validation report
curl -X POST http://localhost:11080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "script_ids": ["script1", "script2"],
    "report_type": "summary",
    "format": "json",
    "include_metrics": true
  }'

# List validation configurations
curl -s http://localhost:11080/api/v1/config/ | jq

# Create validation configuration
curl -X POST http://localhost:11080/api/v1/config/ \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "strict_validation",
    "config_data": {
      "timeout_seconds": 600,
      "tolerance_levels": {
        "total_return_pct": 0.001,
        "sharpe_ratio": 0.01
      }
    },
    "description": "Strict validation configuration"
  }'

# Query validation results
curl -s "http://localhost:11080/api/v1/results/?status=PASSED&limit=10" | jq

# Compare script results
curl -s http://localhost:11080/api/v1/results/comparison/script1/script2 | jq

# Get validation metrics
curl -s http://localhost:11080/metrics | jq

# Open API documentation
open http://localhost:11080/docs

# Open ReDoc documentation
open http://localhost:11080/redoc
```

### **Live Trading Service Commands**
```bash
# Check live trading service status
curl -s http://localhost:11120/health | jq

# Check system status
curl -s http://localhost:11120/api/v1/status | jq

# Check market hours
curl -s http://localhost:11120/api/v1/status/market-hours | jq

# Connect to Public.com
curl -X POST http://localhost:11120/api/v1/auth/public-connect \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "account_name": "My Trading Account",
    "account_type": "CASH"
  }'

# Get account balance
curl -s http://localhost:11120/api/v1/accounts/account-123/balance | jq

# Submit a trade order
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
    "estimated_premium": 3.00,
    "estimated_risk": 1000.00
  }'

# Check order status
curl -s http://localhost:11120/api/v1/trading/orders/order-123 | jq

# Get positions
curl -s http://localhost:11120/api/v1/trading/positions | jq

# Get risk profile
curl -s http://localhost:11120/api/v1/risk/profile/account-123 | jq

# Activate emergency stop
curl -X POST http://localhost:11120/api/v1/risk/emergency-stop/account-123 \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Market volatility spike",
    "severity": "HIGH",
    "cancel_orders": true,
    "close_positions": false
  }'
```

### **Start Essential Services**
```bash
# Start core infrastructure
kubectl port-forward -n trading-system service/timescaledb 11140:5432 &
kubectl port-forward -n trading-system service/redis 11379:6379 &
kubectl port-forward -n trading-system service/rabbitmq 11144:5672 &

# Start unified dashboards
kubectl port-forward -n trading-system service/unified-analytics-dashboard 11114:80 &
kubectl port-forward -n trading-system service/unified-trading-dashboard 11115:80 &
kubectl port-forward -n trading-system service/unified-news-dashboard 11113:80 &

# Start advanced portfolio management services
kubectl port-forward -n trading-system service/enhanced-portfolio-service 11180:80 &
kubectl port-forward -n trading-system service/enhanced-risk-management-service 11181:80 &

# Start live trading service
kubectl port-forward -n trading-system service/live-trading-service 11120:8080 &

# Start AI services
kubectl port-forward -n trading-system service/llm-proxy 11081:11081 &
kubectl port-forward -n trading-system service/ai-analysis-service 11085:11085 &
```

### **Stop All Port Forwards**
```bash
pkill -f "kubectl port-forward"
```

### **Test Port Forwards**
```bash
# Test specific service
curl -s http://localhost:11114/health

# Test portfolio management services
curl -s http://localhost:11180/health
curl -s http://localhost:11181/health

# Test live trading service
curl -s http://localhost:11120/health
curl -s http://localhost:11120/api/v1/status/market-hours

# Risk Management Framework Services (Resource-Constrained)
curl -s http://localhost:11182/health
curl -s http://localhost:11183/health  # Database
curl -s http://localhost:11184/health  # Redis

# Test multiple services
for port in 11114 11115 11113 11120 11180 11181 11182 11183 11184; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/health || echo "Port $port not responding"
done
```

## 📝 Status Indicators

- **✅ Active**: Currently port-forwarded and accessible
- **⏸️ LoadBalancer**: Using LoadBalancer instead of port-forward
- **❌ Not Forwarded**: Available but not currently port-forwarded
- **⚠️ DEPRECATED**: Service has been moved to external sources
- **🔧 Maintenance**: Service is down for maintenance
- **🚨 Issues**: Service has known issues

## 🔄 Update Process

Following the **Port Mapping Management Rule** (`.cursor/rules/port-mapping.mdc`):

1. **Before making changes**: Check current active port forwards
   ```bash
   ps aux | grep "kubectl port-forward" | grep -v grep
   ```

2. **After making changes**: Update this document with:
   - Current active port forwards
   - Service status (✅ Active, ❌ Not Forwarded, ⏸️ LoadBalancer)
   - Last updated timestamp

3. **Test changes**: Verify port forwards are working
   ```bash
   curl -s http://localhost:<port>/health
   ```

4. **Document changes**: Update relevant documentation

## 🎯 Port Range Standards

- **External Ports**: 11000-11999 (project standard)
- **Internal Ports**: Service-specific ports
- **Avoid Conflicts**: No default ports (3000, 5432, 6379, 8080, 9090)
- **Consistent Mapping**: Same external port for same service

## 🗄️ External Database Configuration

**Important**: Internal databases have been **DEPRECATED** and moved to external sources.

### **External Database Services:**
- **TimescaleDB**: Moved to external managed database service
- **Redis**: Moved to external managed cache service (redis://redis.redis.svc.cluster.local:6379)
- **RabbitMQ**: Moved to external managed message queue service
- **PostgreSQL Vector**: Moved to external managed vector database service
- **Ollama Controller DB**: Should use external postgres service (postgres-timescale-external.postgres-infra.svc.cluster.local:5432)

### **Configuration:**
- Database connections are configured via environment variables
- Services connect directly to external databases (no port forwarding needed)
- Internal database services should be scaled down or removed
- See `docs/EXTERNAL_DATABASE_CONFIGURATION.md` for detailed setup

### **Migration Status:**
- ✅ **Completed**: All services migrated to external databases
- ⚠️ **Deprecated**: Internal database services (TimescaleDB, Redis, RabbitMQ, PostgreSQL Vector)
- 🔄 **In Progress**: Cleanup of internal database deployments

## 🔗 Related Documentation

- **Port Forwarding Guide**: `docs/PORT_FORWARDING_GUIDE.md`
- **Port Mapping Rule**: `.cursor/rules/port-mapping.mdc`
- **Service Architecture**: `docs/ARCHITECTURE_DIAGRAM.md`
- **Makefile Commands**: `make port-*` (see main Makefile)
- **Ollama Controller Port Map**: `k8s/ollama-controller/PORT_MAP.md` - Detailed port mapping for Ollama services

## 🚀 Risk Management Framework Commands

### **Resource-Constrained Deployment Commands**

```bash
# Deploy Risk Management Framework (1 replica each)
./scripts/deploy-risk-management.sh deploy

# Check health of all services
./scripts/check-risk-management-health.sh health

# Test VaR calculation
curl -X POST http://localhost:11182/api/risk/var-calculation \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "test-portfolio-123",
    "confidence_levels": [0.95, 0.99],
    "calculation_method": "historical_simulation",
    "data_period_days": 252,
    "include_expected_shortfall": true,
    "include_risk_contributions": true
  }'

# Test stress testing
curl -X POST http://localhost:11182/api/risk/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "test-portfolio-123",
    "scenarios": ["market_crash", "volatility_spike"],
    "include_position_impacts": true,
    "include_sector_impacts": true
  }'

# Test correlation analysis
curl -X POST http://localhost:11182/api/risk/correlation-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "test-portfolio-123",
    "rolling_period_days": 30,
    "include_sector_analysis": true,
    "include_diversification_recommendations": true
  }'

# Generate compliance report
curl -X GET "http://localhost:11182/api/risk/compliance-report?portfolio_id=test-portfolio-123&report_type=daily&format=JSON"

# Get risk monitoring status
curl -X GET "http://localhost:11182/api/risk/monitoring?portfolio_id=test-portfolio-123"

# Configure risk limits
curl -X PUT http://localhost:11182/api/risk/limits \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "test-portfolio-123",
    "limits": [
      {
        "limit_type": "position_size",
        "limit_value": 0.15,
        "limit_unit": "percentage",
        "enforcement_action": "alert"
      }
    ]
  }'

# Get risk alerts
curl -X GET "http://localhost:11182/api/risk/alerts?portfolio_id=test-portfolio-123&status=active&limit=100"
```

### **Resource Monitoring Commands**

```bash
# Check resource usage (single replica)
kubectl top pods -n trading -l app=risk-management-service

# Check database resource usage
kubectl top pods -n trading -l app=postgresql-service

# Check Redis resource usage  
kubectl top pods -n trading -l app=redis-service

# View logs for troubleshooting
kubectl logs -f deployment/risk-management-service -n trading
kubectl logs -f statefulset/risk-management-postgresql -n trading
kubectl logs -f deployment/risk-management-redis -n trading
```

## 🆕 Recent Changes

- **2025-01-15**: Added **Live Trading Service** (11120) with Public.com API integration, comprehensive trading endpoints, and risk management
- **2025-01-15**: Added Comprehensive Risk Management Framework (11182-11189) with **RESOURCE-CONSTRAINED** deployment (1 replica each)
- **2025-01-15**: Added Advanced Portfolio Management Services (11180-11189) with Enhanced Portfolio Service and Enhanced Risk Management Service
- **2025-01-15**: Added portfolio management commands section with API examples
- **2025-09-03**: Created standardized PORT_MAP.md following new rules format
- **2025-09-03**: Moved from `md/PORT_MAP.md` to root directory
- **2025-09-03**: Added comprehensive service categories and port assignments
- **2025-09-03**: Integrated with new rules system and update process
- **2025-09-03**: **IMPORTANT**: Marked internal databases as DEPRECATED - moved to external sources
- **2025-09-03**: Added external database configuration section and migration status

---

## 🔐 Secrets Management

**Status**: ✅ **ACTIVE** (Kubernetes secrets via Makefile)  
**Last Updated**: 2025-01-15 12:45:00 EST

### Available Commands
- `make secrets-help` - Show all secrets management commands
- `make secrets-validate` - Validate .env file and secret configurations
- `make secrets-update` - Update Kubernetes secrets from .env file
- `make secrets-list` - List current Kubernetes secrets
- `make secrets-update-api-keys` - Update only API key secrets
- `make secrets-update-database` - Update only database credentials
- `make secrets-check-cluster` - Check cluster connectivity and permissions

### Configuration
- **Environment File**: `.env` (based on `config.env.example`)
- **Namespace**: `default` (configurable via NAMESPACE variable)
- **Secret Types**: API keys (individual secrets), Database credentials (combined secret)

### Secret Mappings
| Environment Variable | Kubernetes Secret | Type |
|---------------------|-------------------|------|
| `POLYGON_API_KEY` | `polygon-api-key` | api-key |
| `ALPHA_VANTAGE_API_KEY` | `alpha-vantage-api-key` | api-key |
| `DB_HOST` | `db-credentials` | database |
| `DB_USERNAME` | `db-credentials` | database |
| `DB_PASSWORD` | `db-credentials` | database |
| `DB_NAME` | `db-credentials` | database |

### Usage Examples
```bash
# Validate environment file
make secrets-validate

# Update all secrets
make secrets-update

# Update secrets in specific namespace
NAMESPACE=trading make secrets-update

# Dry run (show what would be updated)
make secrets-update DRY_RUN=true

# List current secrets
make secrets-list
```

### Security Features
- ✅ Automatic .env file validation
- ✅ File permission checking (must be 600 or less)
- ✅ Kubernetes naming convention enforcement
- ✅ Base64 encoding of secret values
- ✅ No secret values logged in output
- ✅ Comprehensive error handling with next steps

---

*This document follows the Port Mapping Management Rule and is automatically updated when port forwarding changes are made.*
