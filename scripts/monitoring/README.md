# Monitoring Scripts

This directory contains scripts for monitoring live trading systems, system health, and performance.

## Monitoring Categories

### Live Trading Monitors
- `live_trading_monitor.py` - Monitor live trading activity and performance
- `live_system_comparison.py` - Compare live vs expected performance
- `public_com_monitor.py` - Monitor Public.com account
- `standalone_public_com_monitor.py` - Standalone Public.com monitoring

### System Monitors
- `optimized_system_monitor.py` - Monitor optimized trading system
- `simplified_system_monitor.py` - Simplified system monitoring

### Strategy Monitors
- `monitor_hybrid_ichimoku.py` - Monitor hybrid Ichimoku strategy

## Usage

### Live Trading Monitor

```bash
# Monitor live trading
python scripts/monitoring/live_trading_monitor.py

# Monitor with custom interval
python scripts/monitoring/live_trading_monitor.py --interval 60
```

### System Health Monitor

```bash
# Check system health
python scripts/monitoring/optimized_system_monitor.py
```

## Integration with Kubernetes

Many monitoring scripts are designed to run in Kubernetes:

```bash
# Port forward to access services
kubectl port-forward svc/grafana 11003:3000

# Run monitoring in cluster
kubectl apply -f k8s/monitoring/
```

## Alerting

For alert configuration, see:
- `monitoring/` - Prometheus/Grafana configurations
- `docs/OBSERVABILITY_GUIDE.md` - Comprehensive observability documentation

## Logs

Monitoring script logs are stored in:
- `logs/` - Local log files
- `port_monitor_logs/` - Port forwarding monitor logs
- `port_watcher_logs/` - Port watcher logs

## See Also

- `docs/LIVE_TRADING_MONITORING_SYSTEM_GUIDE.md` - Live trading monitoring guide
- `docs/OBSERVABILITY_GUIDE.md` - Observability and monitoring guide
- `monitoring/` - Grafana dashboards and Prometheus configs

