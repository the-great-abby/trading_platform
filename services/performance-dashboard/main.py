"""
Trade Performance Dashboard - Web-based dashboard for viewing trading performance
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime, timedelta
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trade Performance Dashboard", version="1.0.0")

# Configuration
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:8000")
ANALYTICS_API_URL = os.getenv("ANALYTICS_API_URL", "http://analytics-service:8000")

class DashboardConfig:
    """Dashboard configuration"""
    REFRESH_INTERVAL = 30  # seconds
    MAX_RECENT_RUNS = 10
    DEFAULT_PERIOD = "1m"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "performance-dashboard"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main performance dashboard HTML page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Trade Performance Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #666;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #6c757d; }
        
        .chart-container {
            height: 300px;
            background: #f8f9fa;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 15px;
            border: 2px dashed #dee2e6;
        }
        
        .refresh-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 20px 0;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background: #28a745; }
        .status-warning { background: #ffc107; }
        .status-error { background: #dc3545; }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        .error {
            color: #dc3545;
            text-align: center;
            padding: 20px;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Trade Performance Dashboard</h1>
            <p>Real-time trading performance metrics and analytics</p>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>
        </div>
        
        <div class="dashboard-grid">
            <!-- Recent Backtest Runs -->
            <div class="card">
                <h2>📊 Recent Backtest Runs</h2>
                <div id="recent-runs">
                    <div class="loading">Loading recent runs...</div>
                </div>
            </div>
            
            <!-- Performance Metrics -->
            <div class="card">
                <h2>📈 Performance Metrics</h2>
                <div id="performance-metrics">
                    <div class="loading">Loading performance metrics...</div>
                </div>
            </div>
            
            <!-- Risk Analysis -->
            <div class="card">
                <h2>⚠️ Risk Analysis</h2>
                <div id="risk-analysis">
                    <div class="loading">Loading risk analysis...</div>
                </div>
            </div>
            
            <!-- Trade Analysis -->
            <div class="card">
                <h2>🎯 Trade Analysis</h2>
                <div id="trade-analysis">
                    <div class="loading">Loading trade analysis...</div>
                </div>
            </div>
            
            <!-- Strategy Comparison -->
            <div class="card">
                <h2>🏆 Strategy Comparison</h2>
                <div id="strategy-comparison">
                    <div class="loading">Loading strategy comparison...</div>
                </div>
            </div>
            
            <!-- System Status -->
            <div class="card">
                <h2>🔧 System Status</h2>
                <div id="system-status">
                    <div class="loading">Loading system status...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Dashboard refresh interval (30 seconds)
        const REFRESH_INTERVAL = 30000;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
            setInterval(loadDashboard, REFRESH_INTERVAL);
        });
        
        function refreshDashboard() {
            loadDashboard();
        }
        
        async function loadDashboard() {
            try {
                await Promise.all([
                    loadRecentRuns(),
                    loadPerformanceMetrics(),
                    loadRiskAnalysis(),
                    loadTradeAnalysis(),
                    loadStrategyComparison(),
                    loadSystemStatus()
                ]);
            } catch (error) {
                console.error('Dashboard loading error:', error);
            }
        }
        
        async function loadRecentRuns() {
            try {
                const response = await fetch('/api/recent-runs');
                const data = await response.json();
                
                const container = document.getElementById('recent-runs');
                if (data.success && data.data.length > 0) {
                    let html = '';
                    data.data.slice(0, 5).forEach(run => {
                        const returnClass = run.total_return_pct >= 0 ? 'positive' : 'negative';
                        html += `
                            <div class="metric">
                                <div class="metric-label">${run.strategy_name}</div>
                                <div class="metric-value ${returnClass}">${run.total_return_pct.toFixed(2)}%</div>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<div class="error">No recent runs found</div>';
                }
            } catch (error) {
                document.getElementById('recent-runs').innerHTML = '<div class="error">Failed to load recent runs</div>';
            }
        }
        
        async function loadPerformanceMetrics() {
            try {
                const response = await fetch('/api/performance-metrics');
                const data = await response.json();
                
                const container = document.getElementById('performance-metrics');
                if (data.success) {
                    const metrics = data.data;
                    container.innerHTML = `
                        <div class="metric">
                            <div class="metric-label">Total Return</div>
                            <div class="metric-value ${metrics.total_return >= 0 ? 'positive' : 'negative'}">${(metrics.total_return * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Sharpe Ratio</div>
                            <div class="metric-value neutral">${metrics.sharpe_ratio.toFixed(2)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Max Drawdown</div>
                            <div class="metric-value negative">${(metrics.max_drawdown * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Win Rate</div>
                            <div class="metric-value neutral">${(metrics.win_rate * 100).toFixed(1)}%</div>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="error">Failed to load performance metrics</div>';
                }
            } catch (error) {
                document.getElementById('performance-metrics').innerHTML = '<div class="error">Failed to load performance metrics</div>';
            }
        }
        
        async function loadRiskAnalysis() {
            try {
                const response = await fetch('/api/risk-analysis');
                const data = await response.json();
                
                const container = document.getElementById('risk-analysis');
                if (data.success) {
                    const risk = data.data;
                    container.innerHTML = `
                        <div class="metric">
                            <div class="metric-label">Volatility</div>
                            <div class="metric-value neutral">${(risk.volatility * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">VaR (95%)</div>
                            <div class="metric-value negative">${(risk.var_95 * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Current Drawdown</div>
                            <div class="metric-value negative">${(risk.current_drawdown * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Sortino Ratio</div>
                            <div class="metric-value neutral">${risk.sortino_ratio.toFixed(2)}</div>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="error">Failed to load risk analysis</div>';
                }
            } catch (error) {
                document.getElementById('risk-analysis').innerHTML = '<div class="error">Failed to load risk analysis</div>';
            }
        }
        
        async function loadTradeAnalysis() {
            try {
                const response = await fetch('/api/trade-analysis');
                const data = await response.json();
                
                const container = document.getElementById('trade-analysis');
                if (data.success) {
                    const trades = data.data;
                    container.innerHTML = `
                        <div class="metric">
                            <div class="metric-label">Total Trades</div>
                            <div class="metric-value neutral">${trades.total_trades}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Win Rate</div>
                            <div class="metric-value neutral">${(trades.win_rate * 100).toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Avg Win</div>
                            <div class="metric-value positive">${(trades.avg_win * 100).toFixed(2)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Avg Loss</div>
                            <div class="metric-value negative">${(trades.avg_loss * 100).toFixed(2)}%</div>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="error">Failed to load trade analysis</div>';
                }
            } catch (error) {
                document.getElementById('trade-analysis').innerHTML = '<div class="error">Failed to load trade analysis</div>';
            }
        }
        
        async function loadStrategyComparison() {
            try {
                const response = await fetch('/api/strategy-comparison');
                const data = await response.json();
                
                const container = document.getElementById('strategy-comparison');
                if (data.success && data.data.length > 0) {
                    let html = '';
                    data.data.slice(0, 5).forEach(strategy => {
                        const returnClass = strategy.total_return_pct >= 0 ? 'positive' : 'negative';
                        html += `
                            <div class="metric">
                                <div class="metric-label">${strategy.strategy_name}</div>
                                <div class="metric-value ${returnClass}">${strategy.total_return_pct.toFixed(2)}%</div>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<div class="error">No strategy data available</div>';
                }
            } catch (error) {
                document.getElementById('strategy-comparison').innerHTML = '<div class="error">Failed to load strategy comparison</div>';
            }
        }
        
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/system-status');
                const data = await response.json();
                
                const container = document.getElementById('system-status');
                if (data.success) {
                    const status = data.data;
                    container.innerHTML = `
                        <div class="metric">
                            <div class="metric-label">Backtest API</div>
                            <div class="metric-value">
                                <span class="status-indicator status-${status.backtest_api.status}"></span>
                                ${status.backtest_api.status}
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Analytics API</div>
                            <div class="metric-value">
                                <span class="status-indicator status-${status.analytics_api.status}"></span>
                                ${status.analytics_api.status}
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Database</div>
                            <div class="metric-value">
                                <span class="status-indicator status-${status.database.status}"></span>
                                ${status.database.status}
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Last Updated</div>
                            <div class="metric-value neutral">${new Date().toLocaleTimeString()}</div>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="error">Failed to load system status</div>';
                }
            } catch (error) {
                document.getElementById('system-status').innerHTML = '<div class="error">Failed to load system status</div>';
            }
        }
    </script>
</body>
</html>
    """

@app.get("/api/recent-runs")
async def get_recent_runs():
    """Get recent backtest runs"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKTEST_API_URL}/api/v1/runs?limit=10")
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "data": [], "error": "Failed to fetch recent runs"}
    except Exception as e:
        logger.error(f"Error fetching recent runs: {e}")
        return {"success": False, "data": [], "error": str(e)}

@app.get("/api/performance-metrics")
async def get_performance_metrics():
    """Get performance metrics from analytics service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ANALYTICS_API_URL}/analytics/performance")
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "data": {}, "error": "Failed to fetch performance metrics"}
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        return {"success": False, "data": {}, "error": str(e)}

@app.get("/api/risk-analysis")
async def get_risk_analysis():
    """Get risk analysis from analytics service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ANALYTICS_API_URL}/analytics/risk")
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "data": {}, "error": "Failed to fetch risk analysis"}
    except Exception as e:
        logger.error(f"Error fetching risk analysis: {e}")
        return {"success": False, "data": {}, "error": str(e)}

@app.get("/api/trade-analysis")
async def get_trade_analysis():
    """Get trade analysis from analytics service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ANALYTICS_API_URL}/analytics/trades")
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "data": {}, "error": "Failed to fetch trade analysis"}
    except Exception as e:
        logger.error(f"Error fetching trade analysis: {e}")
        return {"success": False, "data": {}, "error": str(e)}

@app.get("/api/strategy-comparison")
async def get_strategy_comparison():
    """Get strategy comparison from backtest API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKTEST_API_URL}/api/v1/compare")
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data.get("data", [])}
            else:
                return {"success": False, "data": [], "error": "Failed to fetch strategy comparison"}
    except Exception as e:
        logger.error(f"Error fetching strategy comparison: {e}")
        return {"success": False, "data": [], "error": str(e)}

@app.get("/api/system-status")
async def get_system_status():
    """Get system status for all services"""
    try:
        status = {
            "backtest_api": {"status": "unknown"},
            "analytics_api": {"status": "unknown"},
            "database": {"status": "unknown"}
        }
        
        # Check Backtest API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BACKTEST_API_URL}/health")
                status["backtest_api"]["status"] = "healthy" if response.status_code == 200 else "error"
        except:
            status["backtest_api"]["status"] = "error"
        
        # Check Analytics API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ANALYTICS_API_URL}/health")
                status["analytics_api"]["status"] = "healthy" if response.status_code == 200 else "error"
        except:
            status["analytics_api"]["status"] = "error"
        
        # Check Database (via backtest API)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BACKTEST_API_URL}/api/v1/stats")
                status["database"]["status"] = "healthy" if response.status_code == 200 else "error"
        except:
            status["database"]["status"] = "error"
        
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        return {"success": False, "data": {}, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 