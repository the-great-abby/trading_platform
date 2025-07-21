# Market Data Worker Service

## Overview

The Market Data Worker is a RabbitMQ-based service that periodically fetches fresh market data from Polygon and fills missing data gaps. It's designed to keep your trading system's database up-to-date with real-time market data without overwhelming the Polygon API.

## 🚀 Features

### **Periodic Data Fetching**
- **Configurable intervals**: Default 15 minutes, customizable via environment variables
- **Smart rate limiting**: Respects Polygon API limits with configurable delays
- **Multiple data types**: OHLCV data, options chains, and Greeks data
- **Gap detection**: Automatically identifies and fills missing data points

### **RabbitMQ Integration**
- **Reliable message processing**: Uses RabbitMQ for durable job queues
- **Priority-based processing**: Different job types have different priorities
- **Retry logic**: Failed jobs are retried with exponential backoff
- **Dead letter queues**: Failed jobs are moved to DLQ for manual review

### **Data Management**
- **Database-first approach**: Checks cache before making API calls
- **Efficient storage**: Uses PostgreSQL for persistent storage
- **Cache cleanup**: Automatic cleanup of old data and expired cache entries
- **Statistics tracking**: Comprehensive metrics on data fetching performance

## 📊 Architecture

```mermaid
graph TD
    A[Market Data Worker] --> B[RabbitMQ]
    B --> C[OHLCV Fetch Queue]
    B --> D[Options Fetch Queue]
    B --> E[Gap Fill Queue]
    B --> F[Cache Cleanup Queue]
    
    C --> G[Polygon API]
    D --> G
    E --> G
    
    G --> H[PostgreSQL Database]
    H --> I[Cache Manager]
    I --> J[Market Data Service]
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MARKET_DATA_UPDATE_INTERVAL` | `15` | Update interval in minutes |
| `MARKET_DATA_GAP_FILL_DAYS` | `7` | Days to look back for gaps |
| `MAX_CONCURRENT_JOBS` | `5` | Maximum concurrent job processing |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | RabbitMQ connection URL |
| `POLYGON_API_KEY` | - | Polygon API key (required) |
| `DATABASE_URL` | - | PostgreSQL connection URL |
| `RATE_LIMIT_DELAY` | `1.0` | Seconds between API requests |
| `LOG_LEVEL` | `INFO` | Logging level |

### Job Priorities

| Job Type | Priority | Description |
|----------|----------|-------------|
| `cleanup_cache` | 1 | Cache cleanup (lowest priority) |
| `fetch_options` | 3 | Options data fetching |
| `fetch_ohlcv` | 5 | OHLCV data fetching |
| `fill_gaps` | 7 | Gap filling (highest priority) |

## 🚀 Deployment

### Docker Build
```bash
# Build the image
docker build -t localhost:32000/market-data-worker:latest services/market-data-worker/

# Push to registry
docker push localhost:32000/market-data-worker:latest
```

### Kubernetes Deployment
```bash
# Deploy to Kubernetes
make k8s-deploy-market-data-worker

# Check status
make k8s-status-market-data-worker

# View logs
make k8s-logs-market-data-worker
```

### Local Development
```bash
# Run locally
cd services/market-data-worker
python main.py
```

## 📈 Job Types

### 1. OHLCV Data Fetching
- **Purpose**: Fetch daily OHLCV data for all symbols
- **Frequency**: Every 15 minutes (configurable)
- **Data**: Open, High, Low, Close, Volume
- **Storage**: PostgreSQL with caching

### 2. Options Data Fetching
- **Purpose**: Fetch options chains for major symbols
- **Frequency**: Every 15 minutes
- **Symbols**: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA
- **Data**: Strike, expiration, Greeks, volume, OI

### 3. Gap Filling
- **Purpose**: Fill missing data points
- **Frequency**: Every 15 minutes
- **Lookback**: 7 days (configurable)
- **Logic**: Identifies missing dates and fetches only those

### 4. Cache Cleanup
- **Purpose**: Remove old data and expired cache entries
- **Frequency**: Every hour
- **Retention**: 365 days of historical data
- **Cleanup**: Expired cache entries, old options data

## 🔍 Monitoring

### Statistics
The worker tracks comprehensive statistics:

```python
{
    'jobs_processed': 0,
    'jobs_failed': 0,
    'data_points_fetched': 0,
    'gaps_filled': 0,
    'last_update': None,
    'symbols_count': len(symbols),
    'update_interval_minutes': 15,
    'gap_fill_days': 7
}
```

### Health Checks
- **Liveness probe**: HTTP GET `/health`
- **Readiness probe**: HTTP GET `/ready`
- **Metrics**: Prometheus metrics available

### Logging
- **Structured logging**: JSON format for easy parsing
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Log rotation**: Automatic log rotation and cleanup

## 🛠️ Usage Examples

### Manual Job Creation
```python
from services.market_data_worker.main import MarketDataWorker

# Create worker instance
worker = MarketDataWorker()

# Create manual job
job = MarketDataJob(
    job_id="manual_fetch_20241201",
    job_type="fetch_ohlcv",
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2024-12-01",
    end_date="2024-12-01",
    priority=5
)

# Publish job
await worker.rabbitmq.publish_job(job, "market_data_fetch")
```

### Custom Configuration
```python
# Environment variables for custom configuration
export MARKET_DATA_UPDATE_INTERVAL=30  # 30 minutes
export MARKET_DATA_GAP_FILL_DAYS=14   # 14 days lookback
export MAX_CONCURRENT_JOBS=10         # 10 concurrent jobs
export RATE_LIMIT_DELAY=2.0          # 2 seconds between requests
```

## 🔧 Troubleshooting

### Common Issues

1. **Rate Limiting**
   ```
   ❌ Error: Rate limited! Waiting 120s...
   ```
   **Solution**: Increase `RATE_LIMIT_DELAY` or reduce `MAX_CONCURRENT_JOBS`

2. **Database Connection Issues**
   ```
   ❌ Error: Database connection failed
   ```
   **Solution**: Check `DATABASE_URL` and database availability

3. **RabbitMQ Connection Issues**
   ```
   ❌ Error: RabbitMQ connection failed
   ```
   **Solution**: Check `RABBITMQ_URL` and RabbitMQ service status

4. **API Key Issues**
   ```
   ❌ Error: Polygon API key required
   ```
   **Solution**: Set `POLYGON_API_KEY` environment variable

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --debug
```

## 📊 Performance Optimization

### Rate Limiting
- **Polygon API**: 5 requests per minute (free tier)
- **Paid tiers**: Higher limits available
- **Smart delays**: Configurable delays between requests

### Caching Strategy
- **Database cache**: PostgreSQL for persistent storage
- **Memory cache**: Redis for fast access
- **Cache expiration**: Configurable TTL for different data types

### Batch Processing
- **Symbol batching**: Process symbols in batches
- **Date batching**: Fetch data in date ranges
- **Concurrent jobs**: Multiple jobs can run simultaneously

## 🔄 Integration

### With Other Services
- **Strategy Service**: Provides fresh data for backtesting
- **Trading Service**: Real-time data for live trading
- **Analytics Service**: Historical data for analysis
- **Notification Service**: Alerts for data issues

### Data Flow
1. **Worker** creates periodic jobs
2. **RabbitMQ** distributes jobs to queues
3. **Polygon API** provides market data
4. **Database** stores data persistently
5. **Cache** provides fast access
6. **Other services** consume fresh data

## 🚀 Future Enhancements

### Planned Features
- **Real-time streaming**: WebSocket connections for live data
- **Multiple providers**: Fallback to other data providers
- **Advanced analytics**: Data quality metrics and alerts
- **Machine learning**: Predictive data fetching
- **Distributed processing**: Multiple worker instances

### Scalability
- **Horizontal scaling**: Multiple worker pods
- **Load balancing**: RabbitMQ cluster
- **Data partitioning**: Symbol-based partitioning
- **Geographic distribution**: Multi-region deployment

---

## 📝 Quick Start

1. **Deploy the worker**:
   ```bash
   make k8s-deploy-market-data-worker
   ```

2. **Check status**:
   ```bash
   make k8s-status-market-data-worker
   ```

3. **Monitor logs**:
   ```bash
   make k8s-logs-market-data-worker
   ```

4. **Verify data**:
   ```bash
   # Check database for fresh data
   make db-shell
   SELECT COUNT(*) FROM historical_prices WHERE date >= CURRENT_DATE - INTERVAL '1 day';
   ```

The Market Data Worker will automatically start fetching fresh data every 15 minutes and keep your trading system's database up-to-date! 🚀 