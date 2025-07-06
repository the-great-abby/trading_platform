from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import redis
import os
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Health Dashboard", version="1.0.0")

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

try:
    redis_client = redis.from_url(redis_url)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": "connected" if redis_client else "disconnected"
    }
    
    if not redis_client:
        status["status"] = "degraded"
    
    return status

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Health dashboard HTML page"""
    # Get system metrics from Redis if available
    metrics = {}
    if redis_client:
        try:
            # Get cache statistics
            cache_stats = redis_client.info("memory")
            metrics["cache_memory"] = cache_stats.get("used_memory_human", "N/A")
            metrics["cache_keys"] = redis_client.dbsize()
            
            # Get recent logs (if stored in Redis)
            recent_logs = redis_client.lrange("system_logs", 0, 9)
            metrics["recent_logs"] = [log.decode() for log in recent_logs]
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            metrics["error"] = str(e)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading System Health Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .status-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .status-healthy {{ border-left: 4px solid #4CAF50; }}
            .status-degraded {{ border-left: 4px solid #FF9800; }}
            .status-error {{ border-left: 4px solid #f44336; }}
            .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
            .metric-label {{ font-weight: bold; }}
            .refresh-btn {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
            .refresh-btn:hover {{ background: #5a6fd8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Trading System Health Dashboard</h1>
                <p>Real-time system monitoring and health status</p>
            </div>
            
            <div class="status-card status-healthy">
                <h2>System Status</h2>
                <div class="metric">
                    <span class="metric-label">Overall Status:</span>
                    <span>✅ Healthy</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Updated:</span>
                    <span>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Redis Connection:</span>
                    <span>{'✅ Connected' if redis_client else '❌ Disconnected'}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h2>Cache Metrics</h2>
                <div class="metric">
                    <span class="metric-label">Memory Usage:</span>
                    <span>{metrics.get('cache_memory', 'N/A')}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Keys:</span>
                    <span>{metrics.get('cache_keys', 'N/A')}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h2>Recent System Logs</h2>
                <div style="max-height: 200px; overflow-y: auto; background: #f9f9f9; padding: 10px; border-radius: 5px;">
                    {''.join([f'<div style="margin: 5px 0; font-family: monospace; font-size: 12px;">{log}</div>' for log in metrics.get('recent_logs', ['No recent logs available'])])}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Dashboard</button>
            </div>
        </div>
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/api/metrics")
async def get_metrics():
    """API endpoint for system metrics"""
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": redis_client is not None,
        "cache_stats": {}
    }
    
    if redis_client:
        try:
            cache_stats = redis_client.info("memory")
            metrics["cache_stats"] = {
                "memory_usage": cache_stats.get("used_memory_human", "N/A"),
                "keys_count": redis_client.dbsize(),
                "connected_clients": cache_stats.get("connected_clients", 0)
            }
        except Exception as e:
            metrics["error"] = str(e)
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 