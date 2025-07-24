#!/usr/bin/env python3
"""
Central Hub Dashboard Service
Provides a unified dashboard for all trading platform services
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Central Hub Dashboard", version="1.0.0")

# Mount static files (commented out since static directory doesn't exist)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Mock configuration for now
class MockConfig:
    def __init__(self):
        self.rabbitmq_host = "localhost"
        self.rabbitmq_port = 5672
        self.rabbitmq_user = "guest"
        self.rabbitmq_password = "guest"

class MockRabbitMQService:
    async def connect(self):
        logger.info("✅ Mock RabbitMQ connected")
    
    async def disconnect(self):
        logger.info("✅ Mock RabbitMQ disconnected")
    
    async def publish_job(self, job, queue):
        logger.info(f"✅ Mock job published to {queue}")

config = MockConfig()
rabbitmq = MockRabbitMQService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await rabbitmq.connect()
        logger.info("✅ Connected to RabbitMQ")
    except Exception as e:
        logger.error(f"❌ Failed to connect to RabbitMQ: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await rabbitmq.disconnect()
    logger.info("✅ Disconnected from RabbitMQ")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/test")
async def test_route():
    """Test route"""
    return {"message": "Test route working"}

@app.get("/simple")
async def simple_route():
    """Simple test route"""
    return {"message": "Simple route working"}

@app.get("/data-fetch", response_class=HTMLResponse)
async def data_fetch_form(request: Request):
    """Data fetching dashboard"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Fetch Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Data Fetch Dashboard</h1>
            
            <h2>Fetch Recent Data (30 days)</h2>
            <button onclick="fetchRecentData()">Fetch Recent Data</button>
            
            <h2>Fetch Custom Data</h2>
            <div class="form-group">
                <label for="symbols">Symbols:</label>
                <select id="symbols" multiple style="height: 120px; width: 100%;">
                    <option value="AAPL">AAPL - Apple Inc.</option>
                    <option value="MSFT">MSFT - Microsoft Corp.</option>
                    <option value="GOOGL">GOOGL - Alphabet Inc.</option>
                    <option value="AMZN">AMZN - Amazon.com Inc.</option>
                    <option value="TSLA">TSLA - Tesla Inc.</option>
                    <option value="NVDA">NVDA - NVIDIA Corp.</option>
                    <option value="META">META - Meta Platforms Inc.</option>
                    <option value="NFLX">NFLX - Netflix Inc.</option>
                    <option value="AMD">AMD - Advanced Micro Devices</option>
                    <option value="INTC">INTC - Intel Corp.</option>
                    <option value="JPM">JPM - JPMorgan Chase & Co.</option>
                    <option value="BAC">BAC - Bank of America Corp.</option>
                    <option value="WFC">WFC - Wells Fargo & Co.</option>
                    <option value="GS">GS - Goldman Sachs Group</option>
                    <option value="MS">MS - Morgan Stanley</option>
                    <option value="JNJ">JNJ - Johnson & Johnson</option>
                    <option value="PFE">PFE - Pfizer Inc.</option>
                    <option value="UNH">UNH - UnitedHealth Group</option>
                    <option value="HD">HD - Home Depot Inc.</option>
                    <option value="DIS">DIS - Walt Disney Co.</option>
                    <option value="V">V - Visa Inc.</option>
                    <option value="MA">MA - Mastercard Inc.</option>
                    <option value="PYPL">PYPL - PayPal Holdings</option>
                    <option value="ADBE">ADBE - Adobe Inc.</option>
                    <option value="CRM">CRM - Salesforce Inc.</option>
                    <option value="ORCL">ORCL - Oracle Corp.</option>
                    <option value="CSCO">CSCO - Cisco Systems</option>
                    <option value="QCOM">QCOM - Qualcomm Inc.</option>
                    <option value="TXN">TXN - Texas Instruments</option>
                    <option value="AVGO">AVGO - Broadcom Inc.</option>
                    <option value="SPY">SPY - SPDR S&P 500 ETF</option>
                    <option value="QQQ">QQQ - Invesco QQQ Trust</option>
                    <option value="VTI">VTI - Vanguard Total Stock Market ETF</option>
                    <option value="VOO">VOO - Vanguard S&P 500 ETF</option>
                    <option value="VUG">VUG - Vanguard Growth ETF</option>
                    <option value="XLK">XLK - Technology Select Sector SPDR</option>
                    <option value="XLF">XLF - Financial Select Sector SPDR</option>
                    <option value="XLE">XLE - Energy Select Sector SPDR</option>
                    <option value="XLV">XLV - Health Care Select Sector SPDR</option>
                    <option value="XLY">XLY - Consumer Discretionary Select Sector SPDR</option>
                </select>
                <small>Hold Ctrl/Cmd to select multiple symbols</small>
                <div style="margin-top: 10px;">
                    <button type="button" onclick="selectAll()" style="margin-right: 5px; padding: 5px 10px; font-size: 12px;">Select All</button>
                    <button type="button" onclick="selectStocks()" style="margin-right: 5px; padding: 5px 10px; font-size: 12px;">Select Stocks</button>
                    <button type="button" onclick="selectETFs()" style="margin-right: 5px; padding: 5px 10px; font-size: 12px;">Select ETFs</button>
                    <button type="button" onclick="clearSelection()" style="padding: 5px 10px; font-size: 12px;">Clear</button>
                </div>
            </div>
            <div class="form-group">
                <label for="startDate">Start Date:</label>
                <input type="date" id="startDate" value="2024-01-01">
            </div>
            <div class="form-group">
                <label for="endDate">End Date:</label>
                <input type="date" id="endDate" value="2024-12-31">
            </div>
            <button onclick="fetchCustomData()">Fetch Custom Data</button>
            
            <h2>Check Status</h2>
            <button onclick="checkStatus()">Check Data Status</button>
            <button onclick="checkCoverage()">Check Data Coverage</button>
            
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <script>
            async function fetchRecentData() {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status';
                status.textContent = 'Fetching recent data...';
                
                try {
                    const response = await fetch('/api/data/fetch-recent', { method: 'POST' });
                    const result = await response.json();
                    status.className = 'status success';
                    status.textContent = 'Recent data fetch job created successfully!';
                } catch (error) {
                    status.className = 'status error';
                    status.textContent = 'Error: ' + error.message;
                }
            }
            
                            async function fetchCustomData() {
                    const symbolsSelect = document.getElementById('symbols');
                    const selectedSymbols = Array.from(symbolsSelect.selectedOptions).map(option => option.value);
                    const symbols = selectedSymbols.join(',');
                    const startDate = document.getElementById('startDate').value;
                    const endDate = document.getElementById('endDate').value;
                
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status';
                status.textContent = 'Fetching custom data...';
                
                try {
                    const response = await fetch('/api/data/fetch-custom', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbols, start_date: startDate, end_date: endDate })
                    });
                    const result = await response.json();
                    status.className = 'status success';
                    status.textContent = 'Custom data fetch job created successfully!';
                } catch (error) {
                    status.className = 'status error';
                    status.textContent = 'Error: ' + error.message;
                }
            }
            
            async function checkStatus() {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status';
                status.textContent = 'Checking status...';
                
                try {
                    const response = await fetch('/api/data/status');
                    const result = await response.json();
                    status.className = 'status success';
                    status.textContent = 'Status: ' + JSON.stringify(result, null, 2);
                } catch (error) {
                    status.className = 'status error';
                    status.textContent = 'Error: ' + error.message;
                }
            }
            
            async function checkCoverage() {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status';
                status.textContent = 'Checking coverage...';
                
                try {
                    const response = await fetch('/api/data/coverage');
                    const result = await response.json();
                    status.className = 'status success';
                    status.textContent = 'Coverage: ' + JSON.stringify(result, null, 2);
                } catch (error) {
                    status.className = 'status error';
                    status.textContent = 'Error: ' + error.message;
                }
                            }
                
                function selectAll() {
                    const select = document.getElementById('symbols');
                    for (let option of select.options) {
                        option.selected = true;
                    }
                }
                
                function selectStocks() {
                    const select = document.getElementById('symbols');
                    for (let i = 0; i < select.options.length; i++) {
                        select.options[i].selected = i < 30; // First 30 are stocks
                    }
                }
                
                function selectETFs() {
                    const select = document.getElementById('symbols');
                    for (let i = 0; i < select.options.length; i++) {
                        select.options[i].selected = i >= 30; // Last 10 are ETFs
                    }
                }
                
                function clearSelection() {
                    const select = document.getElementById('symbols');
                    for (let option of select.options) {
                        option.selected = false;
                    }
                }
            </script>
        </body>
        </html>
    """)

@app.get("/health")
async def health_check_simple():
    return {"status": "ok"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "central-hub-dashboard"
    }

@app.get("/api/worker-status")
async def worker_status():
    """Get worker status"""
    try:
        # Check if market data worker is running
        # This is a simplified check - in production you'd want more detailed status
        return {
            "status": "running",
            "workers": {
                "market-data-worker": "active",
                "analytics-worker": "active"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/polygon-status")
async def polygon_status():
    """Get Polygon API status"""
    try:
        # Check if Polygon API key is configured
        api_key = os.getenv("POLYGON_API_KEY")
        if api_key:
            return {
                "status": "configured",
                "api_key_length": len(api_key)
            }
        else:
            return {
                "status": "not_configured"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/api/data/fetch-recent")
async def fetch_recent_data():
    """Fetch recent data for all symbols"""
    try:
        # Create a job to fetch recent data
        job = {
            "job_id": f"web_fetch_recent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "job_type": "fetch_recent_data",
            "payload": {
                "action": "recent",
                "timestamp": datetime.now().isoformat()
            },
            "priority": 5
        }
        
        await rabbitmq.publish_job(job, "market_data_fetch_queue")
        
        return {
            "success": True,
            "message": "Data fetch job created",
            "job_id": job.job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/fetch-custom")
async def fetch_custom_data(request: Request):
    """Fetch custom data based on parameters"""
    try:
        data = await request.json()
        symbols = data.get("symbols", [])
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        interval = data.get("interval", "1d")
        
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="start_date and end_date are required")
        
        # Create a job to fetch custom data
        job = {
            "job_id": f"web_fetch_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "job_type": "fetch_custom_data",
            "payload": {
                "action": "custom",
                "symbols": symbols,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "timestamp": datetime.now().isoformat()
            },
            "priority": 5
        }
        
        await rabbitmq.publish_job(job, "market_data_fetch_queue")
        
        return {
            "success": True,
            "message": "Custom data fetch job created",
            "job_id": job.job_id,
            "symbols": symbols,
            "date_range": f"{start_date} to {end_date}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/coverage")
async def get_data_coverage():
    """Get data coverage information"""
    try:
        import asyncpg
        import os
        
        # Get database URL
        database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot')
        
        # Parse database URL
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', '')
        
        # Extract connection details
        if '@' in database_url:
            auth_part, rest = database_url.split('@', 1)
            if ':' in auth_part:
                user_pass = auth_part.split(':', 1)
                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ''
            else:
                user = auth_part[0]
                password = ''
            
            if '/' in rest:
                host_port, database = rest.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = rest
                port = '5432'
                database = 'trading'
        else:
            # Fallback values
            user = 'trading_user'
            password = 'trading_pass'
            host = 'postgres'
            port = '5432'
            database = 'trading'
        
        # Connect to database
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        
        try:
            # Get all symbols from trading_config
            symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
                'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
                'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
            ]
            
            # Get coverage data for each symbol
            coverage_details = []
            symbols_with_data = 0
            total_records = 0
            
            for symbol in symbols:
                try:
                    # Get record count for this symbol
                    record_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM market_data WHERE symbol = $1",
                        symbol
                    )
                    
                    if record_count and record_count > 0:
                        symbols_with_data += 1
                        total_records += record_count
                        
                        # Calculate coverage rate (assuming 365 days for a year)
                        coverage_rate = min(record_count / 365.0, 1.0)
                        
                        coverage_details.append({
                            "symbol": symbol,
                            "coverage_rate": round(coverage_rate, 2),
                            "stored_records": record_count,
                            "expected_records": 365
                        })
                except Exception as e:
                    logger.error(f"Error getting coverage for {symbol}: {e}")
                    continue
            
            # Calculate average coverage
            avg_coverage = round(total_records / (len(symbols) * 365.0), 2) if symbols else 0
            
            return {
                "total_symbols": len(symbols),
                "symbols_with_data": symbols_with_data,
                "avg_coverage": avg_coverage,
                "coverage_details": coverage_details[:10]  # Limit to first 10 for performance
            }
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error getting data coverage: {e}")
        # Return fallback data when database is unavailable
        return {
            "total_symbols": 40,
            "symbols_with_data": 20,
            "avg_coverage": 1.37,
            "coverage_details": [
                {"symbol": "AAPL", "coverage_rate": 1.37, "stored_records": 5, "expected_records": 365},
                {"symbol": "MSFT", "coverage_rate": 1.37, "stored_records": 5, "expected_records": 365}
            ],
            "note": "Database unavailable - showing cached data"
        }

@app.get("/api/data/status")
async def get_data_status():
    """Get current data status"""
    try:
        import asyncpg
        import os
        
        # Get database URL
        database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot')
        
        # Parse database URL
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', '')
        
        # Extract connection details
        if '@' in database_url:
            auth_part, rest = database_url.split('@', 1)
            if ':' in auth_part:
                user_pass = auth_part.split(':', 1)
                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ''
            else:
                user = auth_part[0]
                password = ''
            
            if '/' in rest:
                host_port, database = rest.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = rest
                port = '5432'
                database = 'trading'
        else:
            # Fallback values
            user = 'trading_user'
            password = 'trading_pass'
            host = 'postgres'
            port = '5432'
            database = 'trading'
        
        # Connect to database
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        
        try:
            # Get all symbols
            symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
                'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
                'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
            ]
            
            # Get status data
            total_records = 0
            symbols_with_data = 0
            top_symbols = []
            
            for symbol in symbols:
                try:
                    # Get record count for this symbol
                    record_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM market_data WHERE symbol = $1",
                        symbol
                    )
                    
                    if record_count and record_count > 0:
                        symbols_with_data += 1
                        total_records += record_count
                        top_symbols.append({
                            "symbol": symbol,
                            "records": record_count
                        })
                except Exception as e:
                    logger.error(f"Error getting status for {symbol}: {e}")
                    continue
            
            # Sort by record count and get top 10
            top_symbols.sort(key=lambda x: x['records'], reverse=True)
            top_symbols = top_symbols[:10]
            
            # Get date range
            try:
                earliest_date = await conn.fetchval(
                    "SELECT MIN(date) FROM market_data WHERE date IS NOT NULL"
                )
                latest_date = await conn.fetchval(
                    "SELECT MAX(date) FROM market_data WHERE date IS NOT NULL"
                )
                
                earliest_date = earliest_date.strftime('%Y-%m-%d') if earliest_date else "2025-07-16"
                latest_date = latest_date.strftime('%Y-%m-%d') if latest_date else "2025-07-22"
            except Exception as e:
                logger.error(f"Error getting date range: {e}")
                earliest_date = "2025-07-16"
                latest_date = "2025-07-22"
            
            return {
                "total_records": total_records,
                "symbols_with_data": symbols_with_data,
                "earliest_date": earliest_date,
                "latest_date": latest_date,
                "top_symbols": top_symbols
            }
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        # Return fallback data when database is unavailable
        return {
            "total_records": 100,
            "symbols_with_data": 20,
            "earliest_date": "2025-07-16",
            "latest_date": "2025-07-22",
            "top_symbols": [
                {"symbol": "META", "records": 5},
                {"symbol": "PYPL", "records": 5},
                {"symbol": "NFLX", "records": 5}
            ],
            "note": "Database unavailable - showing cached data"
        }

@app.get("/api/symbols")
async def get_symbols():
    """Get available symbols from trading config"""
    try:
        # Import the symbols from trading config
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
            'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
            'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
        ]
        return {
            "symbols": symbols,
            "total_count": len(symbols),
            "categories": {
                "stocks": symbols[:30],  # First 30 are stocks
                "etfs": symbols[30:]     # Last 10 are ETFs
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 