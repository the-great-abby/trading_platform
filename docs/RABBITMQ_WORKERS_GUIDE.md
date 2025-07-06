# RabbitMQ Workers System Guide

## Overview

The RabbitMQ Workers System provides asynchronous background job processing for the algorithmic trading bot. It enables scalable, fault-tolerant processing of news scanning, sentiment analysis, and trading signal generation.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News Scanner  │───▶│  RabbitMQ Queue │───▶│  News Worker    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Trading Signal  │◀───│ Sentiment Queue │◀───│ Sentiment       │
│ Worker          │    │                 │    │ Analysis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Portfolio       │◀───│ Trading Signal  │◀───│ Trading Signal  │
│ Update Worker   │    │ Queue           │    │ Generation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. RabbitMQ Service (`src/services/queue/rabbitmq_service.py`)

Core message queue service that handles:
- Connection management
- Job publishing and consumption
- Queue management
- Retry logic and dead letter queues
- Health monitoring

**Key Features:**
- Persistent message storage
- Priority-based job scheduling
- Automatic retry with exponential backoff
- Dead letter queue for failed jobs
- Queue statistics and monitoring

### 2. News Worker (`src/services/workers/news_worker.py`)

Processes news scanning and sentiment analysis jobs:

**Job Types:**
- `news_scan`: Scans news sources for market-moving events
- `sentiment_analysis`: Analyzes sentiment of news events

**Workflow:**
1. Receives news scan job
2. Scans configured news sources
3. Extracts relevant news events
4. Creates sentiment analysis jobs
5. Schedules next scan

### 3. Trading Signal Worker (`src/services/workers/trading_signal_worker.py`)

Processes trading signal generation jobs:

**Job Types:**
- `trading_signal`: Generates trading signals
- `backtest`: Runs backtesting analysis

**Signal Types:**
- `news_driven`: Based on news sentiment
- `technical`: Based on technical indicators
- `combined`: News + technical analysis

### 4. Worker Manager (`src/services/workers/worker_manager.py`)

Coordinates all background workers:
- Starts/stops workers
- Health monitoring
- Graceful shutdown handling

## Queues

| Queue Name | Purpose | Job Types | Priority |
|------------|---------|-----------|----------|
| `news_scan_queue` | News scanning jobs | `news_scan` | 0-5 |
| `sentiment_analysis_queue` | Sentiment analysis | `sentiment_analysis` | 0-5 |
| `trading_signal_queue` | Trading signals | `trading_signal`, `backtest` | 0-10 |
| `risk_check_queue` | Risk assessment | `risk_check` | 0-8 |
| `portfolio_update_queue` | Portfolio updates | `portfolio_update` | 0-10 |

## Job Message Structure

```python
@dataclass
class JobMessage:
    job_id: str                    # Unique job identifier
    job_type: str                  # Type of job to process
    payload: Dict[str, Any]        # Job-specific data
    priority: int = 0              # Job priority (0-10)
    created_at: datetime = None    # Job creation timestamp
    retry_count: int = 0           # Current retry attempt
    max_retries: int = 3           # Maximum retry attempts
```

## Usage

### 1. Start the System

```bash
# Start Docker environment with RabbitMQ
make docker-up

# Start background workers
make docker-start-workers
```

### 2. Run Demo

```bash
# Run RabbitMQ workers demo
make docker-rabbitmq-demo
```

### 3. Check Status

```bash
# Check queue status
make docker-rabbitmq-status
```

### 4. Manual Job Publishing

```python
from src.services.workers.news_worker import NewsWorker
from src.services.workers.trading_signal_worker import TradingSignalWorker

# Publish manual news scan
news_worker = NewsWorker(config)
await news_worker.publish_manual_scan(
    symbols=['AAPL', 'TSLA'],
    sources=['reuters', 'bloomberg']
)

# Publish manual trading signal
trading_worker = TradingSignalWorker(config)
await trading_worker.publish_manual_signal(
    symbol='AAPL',
    strategy='news_enhanced'
)
```

## Configuration

### Environment Variables

```bash
# RabbitMQ Configuration
RABBITMQ_URL=amqp://trading_user:trading_pass@rabbitmq-dev:5672/trading_vhost

# Worker Configuration
WORKER_PREFETCH_COUNT=10
WORKER_MAX_RETRIES=3
WORKER_RETRY_DELAY=5
```

### Queue Configuration

```python
# Queue settings
queues = {
    'news_scan': 'news_scan_queue',
    'sentiment_analysis': 'sentiment_analysis_queue',
    'trading_signal': 'trading_signal_queue',
    'backtest': 'backtest_queue',
    'risk_check': 'risk_check_queue',
    'portfolio_update': 'portfolio_update_queue'
}

# Queue arguments
queue_args = {
    'x-message-ttl': 24 * 60 * 60 * 1000,  # 24 hours
    'x-max-priority': 10
}
```

## Job Processing Workflow

### 1. News Scanning Workflow

```
News Scan Job → News Worker → Sentiment Analysis Job → Trading Signal Job → Portfolio Update
```

1. **News Scan Job**: Triggers scanning of news sources
2. **News Worker**: Scans sources, extracts events
3. **Sentiment Analysis Job**: Analyzes sentiment of events
4. **Trading Signal Job**: Generates trading signals if thresholds met
5. **Portfolio Update**: Executes trades and updates portfolio

### 2. Trading Signal Workflow

```
Trading Signal Job → Signal Processing → Portfolio Update Job
```

1. **Trading Signal Job**: Contains signal parameters
2. **Signal Processing**: Applies strategy logic
3. **Portfolio Update Job**: Executes the trade

## Error Handling

### Retry Logic

- Jobs are retried up to `max_retries` times
- Exponential backoff between retries
- Failed jobs are moved to dead letter queue

### Dead Letter Queue

- Failed jobs after max retries
- Contains error information and original job data
- Can be manually reprocessed or analyzed

### Health Monitoring

```python
# Check worker health
status = await manager.health_check()

# Check queue health
stats = await rabbitmq.get_queue_stats(queue_name)
```

## Scaling

### Horizontal Scaling

- Multiple worker instances can consume from same queue
- RabbitMQ automatically distributes jobs
- Workers can be added/removed dynamically

### Vertical Scaling

- Increase `prefetch_count` for higher throughput
- Adjust worker concurrency
- Optimize job processing logic

## Monitoring

### Queue Statistics

```python
# Get queue stats
stats = await rabbitmq.get_queue_stats('news_scan_queue')
print(f"Messages: {stats['message_count']}")
print(f"Consumers: {stats['consumer_count']}")
print(f"Status: {stats['status']}")
```

### Worker Status

```python
# Get worker status
status = manager.get_worker_status()
for worker, running in status.items():
    print(f"{worker}: {'Running' if running else 'Stopped'}")
```

### RabbitMQ Management UI

Access the RabbitMQ management interface at:
- URL: http://localhost:15672
- Username: trading_user
- Password: trading_pass

## Best Practices

### 1. Job Design

- Keep jobs small and focused
- Use appropriate priorities
- Include all necessary data in payload
- Handle errors gracefully

### 2. Worker Design

- Implement proper error handling
- Use async/await for I/O operations
- Log important events
- Implement health checks

### 3. Queue Management

- Monitor queue depths
- Set appropriate TTL for messages
- Use dead letter queues
- Implement proper cleanup

### 4. Performance

- Use connection pooling
- Implement proper prefetch counts
- Monitor memory usage
- Use appropriate message sizes

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check RabbitMQ service is running
   - Verify connection URL
   - Check network connectivity

2. **Job Processing Errors**
   - Check job payload format
   - Verify worker handlers
   - Review error logs

3. **Queue Backlog**
   - Increase worker instances
   - Check job processing speed
   - Review job priorities

### Debug Commands

```bash
# Check RabbitMQ status
docker-compose ps rabbitmq-dev

# View RabbitMQ logs
docker-compose logs rabbitmq-dev

# Check queue status
make docker-rabbitmq-status

# Purge queues (if needed)
docker-compose -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def purge(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); await rmq.purge_queue('news_scan_queue'); await rmq.disconnect(); asyncio.run(purge())"
```

## Integration with Trading System

The RabbitMQ workers integrate seamlessly with the existing trading system:

1. **News Events**: Automatically trigger sentiment analysis
2. **Trading Signals**: Generate based on news and technical analysis
3. **Portfolio Updates**: Execute trades and update positions
4. **Risk Management**: Check risk limits before execution
5. **Backtesting**: Run historical analysis in background

This creates a complete, automated trading pipeline that processes news, generates signals, and executes trades asynchronously and reliably. 