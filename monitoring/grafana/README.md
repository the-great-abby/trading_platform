# 📊 Trading System Grafana Dashboards

This directory contains comprehensive Grafana dashboards for monitoring the trading system. The dashboards are automatically provisioned when Grafana starts.

## 🚀 Quick Start

1. **Access Grafana**: http://localhost:3000
2. **Login**: admin/admin
3. **Navigate to Dashboards**: All dashboards are automatically loaded in the "Trading System" folder

## 📈 Available Dashboards

### 1. Trading System Overview
**File**: `trading-system-overview.json`
**Purpose**: High-level system health and trading performance
**Key Metrics**:
- System health status for all services
- Total trades and P&L
- Win rate and active positions
- Service response times and error rates
- P&L over time visualization

### 2. Strategy Performance Dashboard
**File**: `strategy-performance.json`
**Purpose**: Detailed analysis of individual trading strategies
**Key Metrics**:
- Strategy win rates and P&L
- Sharpe ratios and max drawdown
- Trade counts and profit factors
- Strategy P&L over time
- Signal generation rates

### 3. System Infrastructure
**File**: `system-infrastructure.json`
**Purpose**: Infrastructure monitoring and system health
**Key Metrics**:
- CPU, memory, and disk usage
- Network I/O and system load
- Service health status
- Database connections and Redis usage
- Kafka consumer lag

### 4. AI Performance Dashboard
**File**: `ai-performance.json`
**Purpose**: LLM and AI system monitoring
**Key Metrics**:
- LLM request rates and response times
- AI signal generation and accuracy
- Model confidence and cache hit rates
- AI P&L contribution
- Error rates and processing times

### 5. Risk Management Dashboard
**File**: `risk-management.json`
**Purpose**: Comprehensive risk monitoring
**Key Metrics**:
- Value at Risk (VaR) calculations
- Maximum drawdown tracking
- Position concentration limits
- Portfolio beta and volatility
- Risk alerts and budget utilization

### 6. Market Data Dashboard
**File**: `market-data.json`
**Purpose**: Market data feed monitoring
**Key Metrics**:
- Data latency and feed health
- Data quality scores
- Market volatility and conditions
- Data update rates and errors
- Market depth and impact analysis

## 🔧 Configuration

### Data Sources
- **Prometheus**: Primary metrics source
- **Configuration**: `datasources/prometheus.yaml`

### Dashboard Provisioning
- **Provider**: `dashboards/dashboard-provider.yaml`
- **Auto-loading**: All dashboards are automatically loaded
- **Updates**: Dashboards update every 30 seconds

## 📊 Key Metrics Explained

### Trading Metrics
- **Total P&L**: Cumulative profit/loss across all strategies
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough decline

### System Metrics
- **Service Health**: Up/down status of all microservices
- **Response Time**: API endpoint latency
- **Error Rate**: HTTP 4xx/5xx error frequency
- **Throughput**: Requests per second

### AI Metrics
- **Signal Accuracy**: Percentage of correct AI predictions
- **Model Confidence**: AI model confidence scores
- **Cache Hit Rate**: LLM response caching efficiency
- **Processing Time**: AI signal generation latency

### Risk Metrics
- **VaR**: Value at Risk (95% and 99% confidence)
- **Position Concentration**: Individual position size limits
- **Portfolio Beta**: Market correlation measure
- **Risk Budget**: Risk allocation utilization

### Market Data Metrics
- **Latency**: Data feed update delays
- **Quality Score**: Data accuracy and completeness
- **Market Impact**: Trading impact on prices
- **Feed Health**: Data source availability

## 🎨 Dashboard Features

### Color Coding
- **Green**: Good/healthy status
- **Yellow**: Warning thresholds
- **Red**: Critical issues

### Time Ranges
- **Overview**: 1 hour default
- **Performance**: 24 hours default
- **Infrastructure**: 1 hour default
- **Risk**: 24 hours default

### Refresh Rates
- **Real-time**: 30-second refresh
- **Historical**: 5-minute refresh
- **Alerts**: Immediate updates

## 🚨 Alerting

### Built-in Alerts
- Service down alerts
- High error rate warnings
- Risk limit breaches
- Performance degradation

### Custom Alerts
Create custom alerts in Grafana:
1. Go to Alerting → Alert Rules
2. Create new rule
3. Set thresholds and conditions
4. Configure notifications

## 🔍 Troubleshooting

### No Data Showing
1. Check Prometheus is running: http://localhost:9090
2. Verify metrics endpoints: `/metrics` on services
3. Check data source connection in Grafana

### Dashboard Not Loading
1. Verify dashboard files are in correct location
2. Check Grafana logs for errors
3. Restart Grafana container

### Missing Metrics
1. Ensure services expose `/metrics` endpoint
2. Check Prometheus configuration
3. Verify metric names match dashboard queries

## 📝 Customization

### Adding New Dashboards
1. Create JSON file in `dashboards/` directory
2. Follow existing dashboard structure
3. Restart Grafana or wait for auto-provisioning

### Modifying Existing Dashboards
1. Edit JSON files directly
2. Use Grafana UI for quick changes
3. Export modified dashboards

### Custom Metrics
1. Add metrics to your services
2. Update Prometheus configuration
3. Create new dashboard panels

## 🔗 Related Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Kibana**: http://localhost:5601
- **Trading Dashboard**: http://localhost:11001

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Trading System Architecture](../docs/SPACE_STATION_ARCHITECTURE_DIAGRAMS.md) 