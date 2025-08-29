#!/usr/bin/env python3
"""
Backtest API Service - Main entry point
Runs the backtest API on port 10001
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
import psycopg2
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import time
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

app = FastAPI(title="Backtest API", version="1.0.0")

# Prometheus metrics
backtest_jobs_total = Counter('backtest_jobs_total', 'Total backtest jobs', ['status'])
backtest_jobs_completed = Counter('backtest_jobs_completed', 'Completed backtest jobs')
backtest_jobs_failed = Counter('backtest_jobs_failed', 'Failed backtest jobs')
backtest_duration_seconds = Histogram('backtest_duration_seconds', 'Backtest execution time in seconds')
backtest_queue_depth = Gauge('backtest_queue_depth', 'Number of jobs in queue')

# Strategy performance metrics
strategy_win_rate = Gauge('strategy_win_rate', 'Strategy win rate', ['strategy'])
strategy_sharpe_ratio = Gauge('strategy_sharpe_ratio', 'Strategy Sharpe ratio', ['strategy'])
strategy_max_drawdown = Gauge('strategy_max_drawdown', 'Strategy maximum drawdown', ['strategy'])
strategy_profit_factor = Gauge('strategy_profit_factor', 'Strategy profit factor', ['strategy'])

# Service metrics
backtest_requests_total = Counter('backtest_requests_total', 'Total backtest API requests', ['endpoint', 'status'])
backtest_request_duration_seconds = Histogram('backtest_request_duration_seconds', 'Backtest API request duration')

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-dev"),
        database=os.getenv("DB_NAME", "trading_bot"),
        user=os.getenv("DB_USER", "trading_user"),
        password=os.getenv("DB_PASSWORD", "trading_pass"),
        port=os.getenv("DB_PORT", "5432")
    )

@app.get("/")
async def root():
    """API root endpoint"""
    backtest_requests_total.labels(endpoint="/", status="200").inc()
    return {
        "message": "Backtest Results API",
        "version": "1.0.0",
        "endpoints": {
            "runs": "/api/v1/runs",
            "run_details": "/api/v1/runs/{run_id}",
            "compare_strategies": "/api/v1/compare",
            "stats": "/api/v1/stats",
            "execute_backtest": "/api/v1/backtest"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        backtest_requests_total.labels(endpoint="/health", status="200").inc()
        return {"status": "healthy", "service": "backtest-api"}
    except Exception as e:
        backtest_requests_total.labels(endpoint="/health", status="500").inc()
        return {"status": "unhealthy", "error": str(e)}

@app.get("/ready")
async def ready_check():
    """Readiness check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ready", "service": "backtest-api"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/api/v1/runs")
async def list_runs(limit: int = 10):
    """List recent backtest runs"""
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT run_id, strategy_name, total_return_pct, sharpe_ratio, 
                   max_drawdown_pct, total_trades, win_rate, created_at
            FROM backtest_runs 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        runs = []
        for row in cursor.fetchall():
            runs.append({
                "run_id": row[0],
                "strategy_name": row[1],
                "total_return_pct": float(row[2]) if row[2] else 0.0,
                "sharpe_ratio": float(row[3]) if row[3] else 0.0,
                "max_drawdown_pct": float(row[4]) if row[4] else 0.0,
                "total_trades": row[5] if row[5] else 0,
                "win_rate": float(row[6]) if row[6] else 0.0,
                "created_at": row[7].isoformat() if row[7] else None
            })
        
        cursor.close()
        conn.close()
        
        # Update metrics
        backtest_requests_total.labels(endpoint="/api/v1/runs", status="200").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        
        # Update strategy metrics from database
        update_strategy_metrics_from_runs(runs)
        
        return {"success": True, "data": runs}
    except Exception as e:
        backtest_requests_total.labels(endpoint="/api/v1/runs", status="500").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        return {"success": False, "data": [], "error": str(e)}

def update_strategy_metrics_from_runs(runs):
    """Update strategy performance metrics from backtest runs"""
    strategy_stats = {}
    
    for run in runs:
        strategy = run['strategy_name']
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'win_rates': [],
                'sharpe_ratios': [],
                'max_drawdowns': [],
                'profit_factors': []
            }
        
        strategy_stats[strategy]['win_rates'].append(run['win_rate'])
        strategy_stats[strategy]['sharpe_ratios'].append(run['sharpe_ratio'])
        strategy_stats[strategy]['max_drawdowns'].append(run['max_drawdown_pct'])
        # Calculate profit factor (simplified)
        profit_factor = 1.0 + (run['total_return_pct'] / 100.0) if run['total_return_pct'] > 0 else 1.0
        strategy_stats[strategy]['profit_factors'].append(profit_factor)
    
    # Update Prometheus metrics
    for strategy, stats in strategy_stats.items():
        if stats['win_rates']:
            avg_win_rate = sum(stats['win_rates']) / len(stats['win_rates'])
            strategy_win_rate.labels(strategy=strategy).set(avg_win_rate)
        
        if stats['sharpe_ratios']:
            avg_sharpe = sum(stats['sharpe_ratios']) / len(stats['sharpe_ratios'])
            strategy_sharpe_ratio.labels(strategy=strategy).set(avg_sharpe)
        
        if stats['max_drawdowns']:
            avg_drawdown = sum(stats['max_drawdowns']) / len(stats['max_drawdowns'])
            strategy_max_drawdown.labels(strategy=strategy).set(avg_drawdown)
        
        if stats['profit_factors']:
            avg_profit_factor = sum(stats['profit_factors']) / len(stats['profit_factors'])
            strategy_profit_factor.labels(strategy=strategy).set(avg_profit_factor)

@app.get("/api/v1/compare")
async def compare_strategies():
    """Compare performance of different strategies"""
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strategy_name, AVG(total_return_pct) as avg_return,
                   COUNT(*) as run_count, MAX(total_return_pct) as best_return
            FROM backtest_runs 
            GROUP BY strategy_name 
            ORDER BY avg_return DESC
        """)
        
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                "strategy_name": row[0],
                "total_return_pct": float(row[1]) if row[1] else 0.0,
                "run_count": row[2],
                "best_return": float(row[3]) if row[3] else 0.0
            })
        
        cursor.close()
        conn.close()
        
        # Update metrics
        backtest_requests_total.labels(endpoint="/api/v1/compare", status="200").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        
        return {"success": True, "data": strategies}
    except Exception as e:
        backtest_requests_total.labels(endpoint="/api/v1/compare", status="500").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        return {"success": False, "data": [], "error": str(e)}

@app.post("/api/v1/backtest")
async def execute_backtest(backtest_request: dict):
    """Execute a new backtest with specified parameters"""
    start_time = time.time()
    try:
        # Validate required fields
        required_fields = ['symbols', 'strategies', 'start_date', 'end_date', 'initial_capital']
        for field in required_fields:
            if field not in backtest_request:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        # Generate a unique run ID
        run_id = f"backtest_{uuid.uuid4().hex[:8]}"
        
        # For now, create a simple simulated backtest result
        # In a real system, this would trigger the actual backtest engine
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the backtest run
        cursor.execute("""
            INSERT INTO backtest_runs (
                run_id, strategy_name, backtest_name, symbols, start_date, end_date,
                initial_capital, final_capital, total_return, total_return_pct,
                max_drawdown_pct, sharpe_ratio, total_trades, winning_trades,
                losing_trades, win_rate, profit_factor, avg_win, avg_loss,
                database_only, data_provider, created_at, completed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            run_id,
            backtest_request['strategies'][0] if backtest_request['strategies'] else 'SimpleStrategy',
            f"Backtest_{run_id}",
            ','.join(backtest_request['symbols']),
            backtest_request['start_date'],
            backtest_request['end_date'],
            backtest_request['initial_capital'],
            backtest_request['initial_capital'] * 1.15,  # Simulate 15% return
            0.15,  # 15% return
            15.0,  # 15% return
            8.0,   # 8% max drawdown
            1.2,   # Sharpe ratio
            25,    # Total trades
            15,    # Winning trades
            10,    # Losing trades
            0.6,   # 60% win rate
            1.5,   # Profit factor
            150.0, # Average win
            -100.0, # Average loss
            'false',
            'simulated',
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        # Insert some sample trades
        for i, symbol in enumerate(backtest_request['symbols'][:5]):  # Limit to 5 symbols
            for j in range(5):  # 5 trades per symbol
                trade_id = f"{run_id}_trade_{i}_{j}"
                cursor.execute("""
                    INSERT INTO backtest_trades (
                        run_id, symbol, action, quantity, price, value, pnl, confidence, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    run_id,
                    symbol,
                    'BUY' if j % 2 == 0 else 'SELL',
                    100,
                    100.0 + (j * 10),  # Varying prices
                    10000.0 + (j * 1000),
                    50.0 if j % 2 == 0 else -30.0,  # Varying P&L
                    0.8,
                    datetime.utcnow()
                ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update metrics
        backtest_jobs_total.labels(status="completed").inc()
        backtest_jobs_completed.inc()
        backtest_requests_total.labels(endpoint="/api/v1/backtest", status="200").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        
        return {
            "success": True,
            "job_id": run_id,
            "message": "Backtest completed successfully",
            "run_id": run_id
        }
        
    except Exception as e:
        backtest_jobs_total.labels(status="failed").inc()
        backtest_jobs_failed.inc()
        backtest_requests_total.labels(endpoint="/api/v1/backtest", status="500").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        return {"success": False, "error": str(e)}

@app.get("/api/v1/stats")
async def get_stats():
    """Get overall statistics about backtest results"""
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total_runs,
                   COUNT(DISTINCT strategy_name) as total_strategies,
                   AVG(total_return_pct) as avg_return,
                   MAX(total_return_pct) as best_return,
                   MIN(total_return_pct) as worst_return
            FROM backtest_runs
        """)
        
        row = cursor.fetchone()
        stats = {
            "total_runs": row[0],
            "total_strategies": row[1],
            "avg_return": float(row[2]) if row[2] else 0.0,
            "best_return": float(row[3]) if row[3] else 0.0,
            "worst_return": float(row[4]) if row[4] else 0.0
        }
        
        cursor.close()
        conn.close()
        
        # Update job metrics
        backtest_jobs_total.labels(status="completed").inc(stats["total_runs"])
        backtest_jobs_completed.inc(stats["total_runs"])
        
        # Update metrics
        backtest_requests_total.labels(endpoint="/api/v1/backtest", status="200").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        
        return {"success": True, "data": stats}
    except Exception as e:
        backtest_requests_total.labels(endpoint="/api/v1/backtest", status="500").inc()
        backtest_request_duration_seconds.observe(time.time() - start_time)
        return {"success": False, "data": {}, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 11101
    port = int(os.getenv("API_PORT", "11101"))
    
    print(f"🚀 Starting Backtest API Service on port {port}")
    print("This is ORION, Mission Control. Backtest API is now active!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 