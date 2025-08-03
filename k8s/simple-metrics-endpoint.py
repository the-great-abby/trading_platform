#!/usr/bin/env python3
"""
Simple Prometheus metrics endpoint for trading services
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import time
import random
import psutil
from datetime import datetime

app = FastAPI(title="Trading Service Metrics")

# Mock trading metrics
trading_metrics = {
    'total_trades': 0,
    'total_pnl': 0.0,
    'win_count': 0,
    'loss_count': 0,
    'active_positions': 0,
    'daily_pnl': 0.0,
    'sharpe_ratio': 0.0,
    'max_drawdown': 0.0,
    'profit_factor': 0.0
}

@app.get("/metrics")
async def get_metrics():
    """Return Prometheus metrics"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Update mock trading metrics
        trading_metrics['total_trades'] += random.randint(0, 5)
        trading_metrics['total_pnl'] += random.uniform(-100, 200)
        trading_metrics['daily_pnl'] = random.uniform(-50, 100)
        trading_metrics['active_positions'] = random.randint(0, 10)
        trading_metrics['win_count'] += random.randint(0, 2)
        trading_metrics['loss_count'] += random.randint(0, 1)
        
        if trading_metrics['total_trades'] > 0:
            trading_metrics['win_rate'] = (trading_metrics['win_count'] / trading_metrics['total_trades']) * 100
        else:
            trading_metrics['win_rate'] = 0.0
            
        trading_metrics['sharpe_ratio'] = random.uniform(0.5, 2.0)
        trading_metrics['max_drawdown'] = random.uniform(-0.1, 0)
        trading_metrics['profit_factor'] = random.uniform(1.0, 3.0)
        
        # Build Prometheus metrics
        metrics = f"""# HELP trading_trades_total Total number of trades
# TYPE trading_trades_total counter
trading_trades_total {trading_metrics['total_trades']}

# HELP trading_pnl_total Total P&L
# TYPE trading_pnl_total gauge
trading_pnl_total {trading_metrics['total_pnl']:.2f}

# HELP trading_daily_pnl Daily P&L
# TYPE trading_daily_pnl gauge
trading_daily_pnl {trading_metrics['daily_pnl']:.2f}

# HELP trading_win_count Total wins
# TYPE trading_win_count counter
trading_win_count {trading_metrics['win_count']}

# HELP trading_loss_count Total losses
# TYPE trading_loss_count counter
trading_loss_count {trading_metrics['loss_count']}

# HELP trading_active_positions Active positions
# TYPE trading_active_positions gauge
trading_active_positions {trading_metrics['active_positions']}

# HELP trading_win_rate Win rate percentage
# TYPE trading_win_rate gauge
trading_win_rate {trading_metrics['win_rate']:.2f}

# HELP trading_sharpe_ratio Sharpe ratio
# TYPE trading_sharpe_ratio gauge
trading_sharpe_ratio {trading_metrics['sharpe_ratio']:.2f}

# HELP trading_max_drawdown Maximum drawdown
# TYPE trading_max_drawdown gauge
trading_max_drawdown {trading_metrics['max_drawdown']:.4f}

# HELP trading_profit_factor Profit factor
# TYPE trading_profit_factor gauge
trading_profit_factor {trading_metrics['profit_factor']:.2f}

# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {disk.percent}

# HELP service_uptime_seconds Service uptime in seconds
# TYPE service_uptime_seconds gauge
service_uptime_seconds {time.time()}

# HELP service_requests_total Total requests
# TYPE service_requests_total counter
service_requests_total {random.randint(100, 1000)}

# HELP service_request_duration_seconds Request duration
# TYPE service_request_duration_seconds histogram
service_request_duration_seconds_bucket{{le="0.1"}} {random.randint(50, 100)}
service_request_duration_seconds_bucket{{le="0.5"}} {random.randint(100, 200)}
service_request_duration_seconds_bucket{{le="1.0"}} {random.randint(150, 250)}
service_request_duration_seconds_bucket{{le="+Inf"}} {random.randint(200, 300)}
service_request_duration_seconds_sum {random.uniform(50, 100):.2f}
service_request_duration_seconds_count {random.randint(200, 300)}
"""
        
        return PlainTextResponse(metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

@app.get("/health")
async def get_health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "trading-metrics"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 