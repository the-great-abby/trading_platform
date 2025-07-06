# 🔄 Event Replay Guide

## Overview

Event replay is a crucial feature of event sourcing systems that allows you to:
- **Test scenarios** by replaying historical events
- **Debug issues** by replaying events up to a specific point
- **Restore system state** to a previous point in time
- **Validate system behavior** by comparing replay results with expectations
- **Audit and compliance** by providing complete audit trails

## 🏗️ Architecture

### Event Replay Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event Replay System                          │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  EventReplay    │ │ SnapshotReplay  │ │ EventReplayCLI  │   │
│  │    Engine       │ │    Engine       │ │                 │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              EventReplayManager                             │ │
│  │  - High-level replay operations                            │ │
│  │  - Test scenario management                                │ │
│  │  - System restore functionality                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    Event Store                                  │
│  - EventStoreDB / PostgreSQL                                    │
│  - Event persistence and retrieval                              │
│  - Event filtering and querying                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Basic Event Replay

```bash
# List events without replaying (dry run)
make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02

# Replay events for a specific date range (dry run)
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02

# Execute event replay
make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02
```

### 2. Test Scenarios

```bash
# Replay trading day scenario
make replay-scenario SCENARIO=trading_day

# Replay market crash scenario
make replay-scenario SCENARIO=market_crash

# Execute scenario replay
make replay-scenario-execute SCENARIO=strategy_backtest
```

### 3. System Restoration

```bash
# Restore to start of day (dry run)
make replay-restore RESTORE_POINT=start_of_day

# Execute system restore
make replay-restore-execute RESTORE_POINT=before_crash
```

## 📋 Available Commands

### Event Replay Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `replay-events` | Replay events with filters (dry run) | `make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02` |
| `replay-events-execute` | Execute event replay | `make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02` |
| `replay-scenario` | Replay predefined test scenarios | `make replay-scenario SCENARIO=trading_day` |
| `replay-scenario-execute` | Execute scenario replay | `make replay-scenario-execute SCENARIO=market_crash` |
| `replay-aggregate` | Replay specific aggregate | `make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10` |
| `replay-restore` | Restore system state (dry run) | `make replay-restore RESTORE_POINT=start_of_day` |
| `replay-restore-execute` | Execute system restore | `make replay-restore-execute RESTORE_POINT=before_crash` |
| `replay-list` | List events without replaying | `make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02` |

### Direct CLI Usage

```bash
# Basic replay
python scripts/replay_events.py replay --from-date 2023-12-01 --to-date 2023-12-02 --dry-run

# Replay specific event types
python scripts/replay_events.py replay --event-types OrderPlacedEvent OrderFilledEvent --dry-run

# Replay specific aggregates
python scripts/replay_events.py replay --aggregate-ids order-123 order-456 --dry-run

# Aggregate replay from snapshot
python scripts/replay_events.py aggregate order-123 10 --to-version 15

# Test scenarios
python scripts/replay_events.py scenario trading_day --from-date 2023-12-01

# System restore
python scripts/replay_events.py restore start_of_day --execute
```

## 🧪 Test Scenarios

### Predefined Scenarios

#### 1. Trading Day Scenario
```bash
make replay-scenario SCENARIO=trading_day
```
**Events**: `OrderPlacedEvent`, `OrderFilledEvent`, `TradeExecutedEvent`
**Time Range**: 9:30 AM - 4:00 PM
**Purpose**: Test normal trading day operations

#### 2. Market Crash Scenario
```bash
make replay-scenario SCENARIO=market_crash
```
**Events**: `OrderCancelledEvent`, `RiskLimitExceededEvent`
**Purpose**: Test system behavior during market stress

#### 3. Strategy Backtest Scenario
```bash
make replay-scenario SCENARIO=strategy_backtest
```
**Events**: `SignalGeneratedEvent`, `StrategyExecutedEvent`
**Purpose**: Test strategy performance and execution

### Custom Scenarios

You can create custom scenarios by modifying the `EventReplayManager.replay_for_testing()` method:

```python
# Add custom scenario
scenarios = {
    "custom_scenario": {
        "from_timestamp": datetime.utcnow() - timedelta(days=7),
        "to_timestamp": datetime.utcnow(),
        "event_types": ["CustomEvent1", "CustomEvent2"],
        "batch_size": 500
    }
}
```

## 🔧 Configuration

### Event Replay Settings

```python
# Event replay configuration
REPLAY_CONFIG = {
    "default_batch_size": 1000,
    "max_events_per_replay": 100000,
    "timeout_seconds": 3600,
    "enable_parallel_processing": True,
    "max_workers": 4
}
```

### Replay Handlers Registration

```python
# Register replay handlers for different event types
handlers = {
    "OrderPlacedEvent": [OrderReplayHandler()],
    "OrderFilledEvent": [TradeReplayHandler(), PortfolioReplayHandler()],
    "StrategyExecutedEvent": [StrategyReplayHandler()],
    "RiskLimitExceededEvent": [RiskReplayHandler()]
}

replay_manager.register_replay_handlers(handlers)
```

## 📊 Monitoring and Results

### Replay Statistics

Each replay operation returns detailed statistics:

```json
{
    "total_events": 15000,
    "processed_events": 14995,
    "errors": 5,
    "duration": 45.2,
    "dry_run": false,
    "success_rate": 99.97,
    "error_details": [
        {
            "event_id": "event-123",
            "aggregate_id": "order-456",
            "event_type": "OrderPlacedEvent",
            "timestamp": "2023-12-01T10:30:00",
            "error": "Handler failed: Database connection error"
        }
    ],
    "event_type_counts": {
        "OrderPlacedEvent": 5000,
        "OrderFilledEvent": 4500,
        "TradeExecutedEvent": 4500,
        "OrderCancelledEvent": 1000
    }
}
```

### Performance Monitoring

```bash
# Monitor replay performance
make docker-logs-service SERVICE=trading-service | grep "REPLAY"

# Check replay progress
tail -f logs/replay.log
```

## 🔍 Debugging and Troubleshooting

### Common Issues

#### 1. Event Handler Failures
```bash
# Check handler errors
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02
# Look for error details in output
```

#### 2. Memory Issues
```bash
# Reduce batch size for large replays
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02 BATCH_SIZE=100
```

#### 3. Timeout Issues
```bash
# Increase timeout for long replays
export REPLAY_TIMEOUT=7200  # 2 hours
make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02
```

### Debugging Commands

```bash
# Check event store health
make docker-shell SERVICE=eventstore
# Inside container: eventstore-cli status

# Verify event data
make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02 --limit 10

# Test specific event types
make replay-events --event-types OrderPlacedEvent --dry-run
```

## 🛡️ Safety Features

### Dry Run Mode
Always use dry run mode first to understand what will be replayed:

```bash
# Safe exploration
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02 --dry-run

# Check results before executing
make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02
```

### Batch Processing
Events are processed in batches to prevent memory issues:

```bash
# Adjust batch size for your system
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02 BATCH_SIZE=500
```

### Error Handling
Failed events are logged and don't stop the replay:

```bash
# Check error details
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02
# Review error_details in output
```

## 📈 Advanced Usage

### Parallel Processing

```python
# Enable parallel processing for large replays
replay_config = {
    "enable_parallel_processing": True,
    "max_workers": 4,
    "chunk_size": 1000
}
```

### Incremental Replay

```bash
# Replay only new events since last replay
make replay-events FROM_DATE=2023-12-02T00:00:00 TO_DATE=2023-12-02T23:59:59
```

### Selective Replay

```bash
# Replay only specific event types
make replay-events --event-types OrderPlacedEvent OrderFilledEvent --dry-run

# Replay only specific aggregates
make replay-events --aggregate-ids order-123 order-456 --dry-run
```

## 🔄 Integration with CI/CD

### Automated Testing

```yaml
# .github/workflows/event-replay-test.yml
name: Event Replay Tests
on: [push, pull_request]

jobs:
  replay-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Run replay tests
        run: |
          make replay-scenario SCENARIO=trading_day
          make replay-scenario SCENARIO=market_crash
```

### Performance Regression Testing

```bash
# Run performance benchmarks
make benchmark

# Compare with baseline
python scripts/compare_replay_performance.py baseline.json current.json
```

## 📚 Best Practices

### 1. Always Use Dry Run First
```bash
# Explore before executing
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02 --dry-run
```

### 2. Monitor Resource Usage
```bash
# Check system resources during replay
docker stats
```

### 3. Use Appropriate Batch Sizes
```bash
# Start with small batches for testing
make replay-events BATCH_SIZE=100 --dry-run

# Increase for production
make replay-events BATCH_SIZE=1000 --dry-run
```

### 4. Regular Testing
```bash
# Run regular replay tests
make replay-scenario SCENARIO=trading_day
make replay-scenario SCENARIO=market_crash
```

### 5. Backup Before Major Replays
```bash
# Backup current state
make db-backup

# Execute replay
make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02

# Restore if needed
make db-restore WRITE_BACKUP=backup_write_20231201_120000.sql READ_BACKUP=backup_read_20231201_120000.sql
```

## 🚨 Emergency Procedures

### Stop Replay in Progress
```bash
# Stop all services
make docker-down

# Restart services
make docker-up
```

### Rollback Failed Replay
```bash
# Restore from backup
make db-restore WRITE_BACKUP=backup_write_20231201_120000.sql READ_BACKUP=backup_read_20231201_120000.sql

# Verify system state
make status
```

### Emergency System Restore
```bash
# Restore to known good state
make replay-restore-execute RESTORE_POINT=before_crash

# Verify system health
make test
```

## 📞 Support

For issues with event replay:

1. **Check logs**: `make docker-logs-service SERVICE=trading-service`
2. **Verify configuration**: `make env-check`
3. **Test connectivity**: `make test-api`
4. **Review documentation**: Check this guide and architecture.md

## 🔗 Related Documentation

- [Architecture Guide](architecture.md) - System architecture overview
- [Deployment Guide](DEPLOYMENT.md) - Deployment instructions
- [Makefile Reference](MAKEFILE_REFERENCE.md) - Available commands
- [API Documentation](README.md#api-documentation) - API endpoints 