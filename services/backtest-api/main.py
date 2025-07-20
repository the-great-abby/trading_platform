#!/usr/bin/env python3
"""
Backtest API Service - Main entry point
Runs the backtest API on port 10001
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

app = FastAPI(title="Backtest API", version="1.0.0")

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
    return {
        "message": "Backtest Results API",
        "version": "1.0.0",
        "endpoints": {
            "runs": "/api/v1/runs",
            "run_details": "/api/v1/runs/{run_id}",
            "compare_strategies": "/api/v1/compare",
            "stats": "/api/v1/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "service": "backtest-api"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/v1/runs")
async def list_runs(limit: int = 10):
    """List recent backtest runs"""
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
        
        return {"success": True, "data": runs}
    except Exception as e:
        return {"success": False, "data": [], "error": str(e)}

@app.get("/api/v1/compare")
async def compare_strategies():
    """Compare performance of different strategies"""
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
        
        return {"success": True, "data": strategies}
    except Exception as e:
        return {"success": False, "data": [], "error": str(e)}

@app.get("/api/v1/stats")
async def get_stats():
    """Get overall statistics about backtest results"""
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
        
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "data": {}, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 10001
    port = int(os.getenv("API_PORT", "10001"))
    
    print(f"🚀 Starting Backtest API Service on port {port}")
    print("This is ORION, Mission Control. Backtest API is now active!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 