#!/usr/bin/env python3
"""
Live Trading Monitoring Dashboard
Provides real-time monitoring interface for live trading positions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

from .position_monitor import position_monitor
from .exit_strategy_service import exit_strategy_service

logger = logging.getLogger(__name__)

app = FastAPI(title="Live Trading Monitoring Dashboard")

class MonitoringDashboard:
    """Real-time monitoring dashboard for live trading"""
    
    def __init__(self):
        self.connected_clients = []
        self.monitoring_data = {}
        
    async def connect(self, websocket: WebSocket):
        """Connect a client to the dashboard"""
        await websocket.accept()
        self.connected_clients.append(websocket)
        logger.info(f"📱 Client connected to monitoring dashboard")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a client from the dashboard"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"📱 Client disconnected from monitoring dashboard")
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        if self.connected_clients:
            message = json.dumps(data)
            for client in self.connected_clients.copy():
                try:
                    await client.send_text(message)
                except:
                    self.connected_clients.remove(client)
    
    async def start_monitoring_broadcast(self):
        """Start broadcasting monitoring data"""
        while True:
            try:
                # Get monitoring summary
                summary = await position_monitor.get_monitoring_summary()
                
                # Add exit strategy information
                summary['exit_strategies'] = {
                    'total_strategies': len(exit_strategy_service.exit_strategies),
                    'active_strategies': sum(1 for strategies in exit_strategy_service.exit_strategies.values() 
                                           for s in strategies if s.is_active)
                }
                
                # Broadcast to clients
                await self.broadcast_update({
                    'type': 'monitoring_update',
                    'data': summary,
                    'timestamp': datetime.now().isoformat()
                })
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring broadcast: {e}")
                await asyncio.sleep(60)

# Global dashboard instance
dashboard = MonitoringDashboard()

@app.get("/")
async def get_dashboard():
    """Get the monitoring dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Trading Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .position { border-left: 4px solid #3498db; padding: 10px; margin: 5px 0; }
            .high-risk { border-left-color: #e74c3c; }
            .medium-risk { border-left-color: #f39c12; }
            .low-risk { border-left-color: #27ae60; }
            .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status.active { background: #27ae60; color: white; }
            .status.inactive { background: #95a5a6; color: white; }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .metric-label { font-size: 12px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Live Trading Monitoring Dashboard</h1>
                <p>Real-time position monitoring and exit strategy management</p>
            </div>
            
            <div class="card">
                <h2>📊 System Overview</h2>
                <div class="metric">
                    <div class="metric-value" id="total-positions">0</div>
                    <div class="metric-label">Total Positions</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="high-risk-positions">0</div>
                    <div class="metric-label">High Risk</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="monitoring-status">Inactive</div>
                    <div class="metric-label">Monitoring Status</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="last-update">Never</div>
                    <div class="metric-label">Last Update</div>
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Active Positions</h2>
                <div id="positions-list">
                    <p>No active positions</p>
                </div>
            </div>
            
            <div class="card">
                <h2>🎯 Exit Strategies</h2>
                <div id="exit-strategies">
                    <p>Loading exit strategy information...</p>
                </div>
            </div>
            
            <div class="card">
                <h2>🛡️ Position Protection Details</h2>
                <div id="protection-details">
                    <p>No active positions to show protection details</p>
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket("ws://localhost:11180/ws");
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'monitoring_update') {
                    updateDashboard(data.data);
                }
            };
            
            function updateDashboard(data) {
                // Update system overview
                document.getElementById('total-positions').textContent = data.total_positions;
                document.getElementById('high-risk-positions').textContent = data.high_risk_positions;
                document.getElementById('monitoring-status').textContent = data.monitoring_active ? 'Active' : 'Inactive';
                document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleTimeString();
                
                // Update positions list with enhanced information
                const positionsList = document.getElementById('positions-list');
                if (data.positions && data.positions.length > 0) {
                    positionsList.innerHTML = data.positions.map(pos => `
                        <div class="position ${pos.risk_level.toLowerCase()}-risk">
                            <strong>${pos.symbol}</strong> (${pos.strategy})<br>
                            P&L: ${(pos.pnl_pct * 100).toFixed(1)}% | 
                            Holding: ${pos.holding_days} days | 
                            Risk: ${pos.risk_level}<br>
                            <small>Entry: $${pos.entry_price.toFixed(2)} | Current: $${pos.current_price.toFixed(2)} | Qty: ${pos.quantity}</small>
                        </div>
                    `).join('');
                } else {
                    positionsList.innerHTML = '<p>No active positions</p>';
                }
                
                // Update exit strategies with detailed information
                const exitStrategies = document.getElementById('exit-strategies');
                if (data.exit_strategy_config) {
                    const config = data.exit_strategy_config;
                    exitStrategies.innerHTML = `
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <h3 style="margin-top: 0; color: #2c3e50;">🎯 Default Exit Strategy Configuration</h3>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div><strong>Max Holding:</strong> ${config.max_holding_days} days</div>
                                <div><strong>Profit Target:</strong> ${(config.profit_target_pct * 100).toFixed(1)}%</div>
                                <div><strong>Stop Loss:</strong> ${(config.stop_loss_pct * 100).toFixed(1)}%</div>
                                <div><strong>Min Holding:</strong> ${config.min_holding_hours} hours</div>
                            </div>
                        </div>
                        <p><strong>Total Strategies:</strong> ${data.exit_strategies.total_strategies}</p>
                        <p><strong>Active Strategies:</strong> ${data.exit_strategies.active_strategies}</p>
                    `;
                } else {
                    exitStrategies.innerHTML = `
                        <p>Total Strategies: ${data.exit_strategies.total_strategies}</p>
                        <p>Active Strategies: ${data.exit_strategies.active_strategies}</p>
                    `;
                }
                
                // Update position protection details
                const protectionDetails = document.getElementById('protection-details');
                if (data.positions && data.positions.length > 0) {
                    protectionDetails.innerHTML = data.positions.map(pos => `
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #27ae60;">
                            <h3 style="margin-top: 0; color: #27ae60;">🛡️ ${pos.symbol} Protection Details</h3>
                            <div style="white-space: pre-line; font-family: monospace; font-size: 14px;">
                                ${pos.exit_strategy.anxiety_reduction_message}
                            </div>
                            <div style="margin-top: 10px;">
                                <strong>Closest Exit:</strong> ${pos.exit_strategy.closest_exit.description}<br>
                                <strong>Days until max hold:</strong> ${pos.exit_strategy.days_until_max_hold.toFixed(1)} days<br>
                                <strong>Profit target distance:</strong> ${(pos.exit_strategy.profit_distance_pct * 100).toFixed(1)}%<br>
                                <strong>Stop loss distance:</strong> ${(pos.exit_strategy.stop_distance_pct * 100).toFixed(1)}%
                            </div>
                        </div>
                    `).join('');
                } else {
                    protectionDetails.innerHTML = '<p>No active positions to show protection details</p>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await dashboard.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await dashboard.disconnect(websocket)

@app.get("/api/monitoring/summary")
async def get_monitoring_summary():
    """Get monitoring summary API"""
    return await position_monitor.get_monitoring_summary()

@app.get("/api/exit-strategies")
async def get_exit_strategies():
    """Get exit strategies API"""
    return {
        'strategies': exit_strategy_service.exit_strategies,
        'default_strategies': exit_strategy_service.default_strategies
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11180)
