"""
RSS Dashboard Service - Real-time RSS feed viewer with auto-refresh
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from loguru import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RSS Dashboard", version="1.0.0")

# Configuration
RSS_SERVICE_URL = os.getenv("RSS_SERVICE_URL", "http://rss-feed-service:11004")
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:8000")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))  # seconds

class RSSDashboard:
    """RSS Dashboard manager"""
    
    def __init__(self):
        self.rss_service_url = RSS_SERVICE_URL
        self.strategy_service_url = STRATEGY_SERVICE_URL
        self.cache = {}
        self.last_update = {}
        
    async def get_rss_feed(self, feed_type: str = "daily", symbol: str = None) -> Dict[str, Any]:
        """Get RSS feed data"""
        try:
            if feed_type == "daily":
                url = f"{self.rss_service_url}/api/feed"
            elif feed_type == "symbol" and symbol:
                url = f"{self.rss_service_url}/api/feed?type=symbol&symbol={symbol}"
            else:
                url = f"{self.rss_service_url}/api/recommendations"
            
            logger.info(f"🔗 Calling RSS service at: {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.get(url)
                    logger.info(f"📡 RSS service response: {response.status_code}")
                    logger.info(f"📄 Response headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Got data with {len(data.get('recommendations', []))} recommendations")
                        return data
                    else:
                        logger.error(f"❌ RSS service returned {response.status_code}: {response.text}")
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
                except httpx.ConnectError as e:
                    logger.error(f"❌ Connection error to RSS service: {e}")
                    return {"error": f"Connection error: {str(e)}"}
                except httpx.TimeoutException as e:
                    logger.error(f"❌ Timeout error to RSS service: {e}")
                    return {"error": f"Timeout error: {str(e)}"}
                except Exception as e:
                    logger.error(f"❌ HTTP client error: {e}")
                    return {"error": f"HTTP client error: {str(e)}"}
                    
        except Exception as e:
            logger.error(f"❌ Error getting RSS feed: {e}")
            return {"error": str(e)}
    
    async def _parse_rss_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse RSS XML content"""
        try:
            root = ET.fromstring(xml_content)
            channel = root.find('channel')
            
            if channel is None:
                return {"error": "Invalid RSS format"}
            
            # Extract channel information
            channel_info = {
                "title": self._get_text(channel, "title"),
                "description": self._get_text(channel, "description"),
                "link": self._get_text(channel, "link"),
                "language": self._get_text(channel, "language"),
                "ttl": self._get_text(channel, "ttl"),
                "last_build_date": self._get_text(channel, "lastBuildDate"),
                "items": []
            }
            
            # Extract items
            for item in channel.findall('item'):
                item_data = {
                    "title": self._get_text(item, "title"),
                    "description": self._get_text(item, "description"),
                    "link": self._get_text(item, "link"),
                    "guid": self._get_text(item, "guid"),
                    "pub_date": self._get_text(item, "pubDate"),
                    "category": self._get_text(item, "category")
                }
                channel_info["items"].append(item_data)
            
            return channel_info
            
        except Exception as e:
            logger.error(f"Error parsing RSS XML: {e}")
            return {"error": f"XML parsing error: {str(e)}"}
    
    def _get_text(self, element, tag: str) -> str:
        """Safely get text from XML element"""
        child = element.find(tag)
        return child.text if child is not None else ""

# Global dashboard instance
dashboard = RSSDashboard()

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Main dashboard page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Trading Dashboard</title>
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
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .controls {
            background: rgba(255, 255, 255, 0.95);
            margin: 20px;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .control-group {
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .control-group label {
            font-weight: bold;
            min-width: 120px;
        }
        
        select, input, button {
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }
        
        button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .status {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .feed-container {
            background: rgba(255, 255, 255, 0.95);
            margin: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .feed-header {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .feed-content {
            max-height: 600px;
            overflow-y: auto;
            padding: 20px;
        }
        
        .feed-item {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: white;
            transition: all 0.3s ease;
        }
        
        .feed-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .feed-item.buy {
            border-left: 4px solid #28a745;
        }
        
        .feed-item.sell {
            border-left: 4px solid #dc3545;
        }
        
        .feed-item.hold {
            border-left: 4px solid #ffc107;
        }
        
        .item-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        
        .item-meta {
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }
        
        .item-description {
            line-height: 1.6;
            color: #555;
        }
        
        .item-link {
            display: inline-block;
            margin-top: 10px;
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
        }
        
        .item-link:hover {
            text-decoration: underline;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 20px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .control-group {
                flex-direction: column;
                align-items: stretch;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .feed-content {
                max-height: 400px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 RSS Trading Dashboard</h1>
        <p>Real-time trading recommendations from Space Trading Station</p>
    </div>
    
    <div class="controls">
        <div class="control-group">
            <label for="feedType">Feed Type:</label>
            <select id="feedType" onchange="updateFeed()">
                <option value="api" selected>JSON API</option>
                <option value="daily">Daily Recommendations</option>
                <option value="symbol">Symbol Specific</option>
            </select>
            
            <label for="symbol" id="symbolLabel" style="display: none;">Symbol:</label>
            <input type="text" id="symbol" placeholder="AAPL" style="display: none;" onchange="updateFeed()">
            
            <label for="refreshInterval">Refresh (seconds):</label>
            <select id="refreshInterval" onchange="updateRefreshInterval()">
                <option value="10">10s</option>
                <option value="30" selected>30s</option>
                <option value="60">1m</option>
                <option value="300">5m</option>
                <option value="0">Manual</option>
            </select>
            
            <button onclick="refreshFeed()">🔄 Refresh Now</button>
        </div>
        
        <div class="status">
            <div class="status-indicator" id="statusIndicator"></div>
            <span id="lastUpdate">Last update: Never</span>
            <span id="itemCount">Items: 0</span>
        </div>
    </div>
    
    <div class="stats" id="stats" style="display: none;">
        <div class="stat-card">
            <div class="stat-number" id="buyCount">0</div>
            <div class="stat-label">Buy Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="sellCount">0</div>
            <div class="stat-label">Sell Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="holdCount">0</div>
            <div class="stat-label">Hold Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="totalCount">0</div>
            <div class="stat-label">Total Items</div>
        </div>
    </div>
    
    <div class="feed-container">
        <div class="feed-header">
            <h2 id="feedTitle">Daily Trading Recommendations</h2>
            <span id="feedInfo">Loading...</span>
        </div>
        <div class="feed-content" id="feedContent">
            <div class="loading">Loading RSS feed...</div>
        </div>
    </div>
    
    <script>
        let refreshInterval = 30;
        let refreshTimer = null;
        let currentFeedType = 'api';
        let currentSymbol = '';
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            updateFeed();
            updateRefreshInterval();
        });
        
        function updateFeed() {
            currentFeedType = document.getElementById('feedType').value;
            currentSymbol = document.getElementById('symbol').value;
            
            // Show/hide symbol input
            const symbolLabel = document.getElementById('symbolLabel');
            const symbolInput = document.getElementById('symbol');
            
            if (currentFeedType === 'symbol') {
                symbolLabel.style.display = 'inline';
                symbolInput.style.display = 'inline';
                if (!currentSymbol) {
                    currentSymbol = 'AAPL';
                    symbolInput.value = currentSymbol;
                }
            } else {
                symbolLabel.style.display = 'none';
                symbolInput.style.display = 'none';
            }
            
            refreshFeed();
        }
        
        function updateRefreshInterval() {
            refreshInterval = parseInt(document.getElementById('refreshInterval').value);
            
            if (refreshTimer) {
                clearInterval(refreshTimer);
            }
            
            if (refreshInterval > 0) {
                refreshTimer = setInterval(refreshFeed, refreshInterval * 1000);
            }
        }
        
        async function refreshFeed() {
            const statusIndicator = document.getElementById('statusIndicator');
            const lastUpdate = document.getElementById('lastUpdate');
            const feedContent = document.getElementById('feedContent');
            const feedTitle = document.getElementById('feedTitle');
            const feedInfo = document.getElementById('feedInfo');
            
            // Show loading state
            statusIndicator.style.background = '#ffc107';
            feedContent.innerHTML = '<div class="loading">Loading RSS feed...</div>';
            
            try {
                let url = '/api/feed';
                if (currentFeedType === 'symbol') {
                    url += `?type=symbol&symbol=${currentSymbol}`;
                } else if (currentFeedType === 'api') {
                    url += '?type=api';
                } else {
                    url += '?type=daily';
                }
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update feed content - all feed types use JSON API format
                displayApiData(data);
                
                // Update status
                statusIndicator.style.background = '#28a745';
                lastUpdate.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
                
            } catch (error) {
                console.error('Error refreshing feed:', error);
                statusIndicator.style.background = '#dc3545';
                feedContent.innerHTML = `<div class="error">Error loading feed: ${error.message}</div>`;
            }
        }
        
        function displayRssData(data) {
            const feedContent = document.getElementById('feedContent');
            const feedTitle = document.getElementById('feedTitle');
            const feedInfo = document.getElementById('feedInfo');
            const stats = document.getElementById('stats');
            
            // Update header
            feedTitle.textContent = data.title || 'RSS Feed';
            feedInfo.textContent = `${data.items ? data.items.length : 0} items`;
            
            if (!data.items || data.items.length === 0) {
                feedContent.innerHTML = '<div class="loading">No items available</div>';
                stats.style.display = 'none';
                return;
            }
            
            // Calculate stats
            let buyCount = 0, sellCount = 0, holdCount = 0;
            
            // Generate HTML
            let html = '';
            data.items.forEach(item => {
                const category = item.category ? item.category.toLowerCase() : 'hold';
                if (category === 'buy') buyCount++;
                else if (category === 'sell') sellCount++;
                else holdCount++;
                
                html += `
                    <div class="feed-item ${category}">
                        <div class="item-title">${item.title || 'No title'}</div>
                        <div class="item-meta">
                            <span>📅 ${item.pub_date || 'No date'}</span>
                            <span>🏷️ ${item.category || 'No category'}</span>
                        </div>
                        <div class="item-description">${item.description || 'No description'}</div>
                        ${item.link ? `<a href="${item.link}" class="item-link" target="_blank">View Details →</a>` : ''}
                    </div>
                `;
            });
            
            feedContent.innerHTML = html;
            
            // Update stats
            document.getElementById('buyCount').textContent = buyCount;
            document.getElementById('sellCount').textContent = sellCount;
            document.getElementById('holdCount').textContent = holdCount;
            document.getElementById('totalCount').textContent = data.items.length;
            stats.style.display = 'grid';
        }
        
        function displayApiData(data) {
            const feedContent = document.getElementById('feedContent');
            const feedTitle = document.getElementById('feedTitle');
            const feedInfo = document.getElementById('feedInfo');
            const stats = document.getElementById('stats');
            
            // Update header based on feed type
            if (currentFeedType === 'symbol') {
                feedTitle.textContent = `Symbol Specific: ${currentSymbol}`;
            } else if (currentFeedType === 'daily') {
                feedTitle.textContent = 'Daily Trading Recommendations';
            } else {
                feedTitle.textContent = 'JSON API Data';
            }
            feedInfo.textContent = `${data.recommendations ? data.recommendations.length : 0} recommendations`;
            
            if (!data.recommendations || data.recommendations.length === 0) {
                feedContent.innerHTML = '<div class="loading">No recommendations available</div>';
                stats.style.display = 'none';
                return;
            }
            
            // Calculate stats
            let buyCount = 0, sellCount = 0, holdCount = 0;
            
            // Generate HTML
            let html = '';
            data.recommendations.forEach(rec => {
                // Handle both RSS item format and raw recommendation format
                if (rec.title) {
                    // RSS item format
                    const category = rec.category ? rec.category.toLowerCase() : 'hold';
                    if (category === 'buy') buyCount++;
                    else if (category === 'sell') sellCount++;
                    else holdCount++;
                    
                    html += `
                        <div class="feed-item ${category}">
                            <div class="item-title">${rec.title || 'No title'}</div>
                            <div class="item-meta">
                                <span>📅 ${rec.pub_date || 'No date'}</span>
                                <span>🏷️ ${rec.category || 'No category'}</span>
                            </div>
                            <div class="item-description">${rec.description || 'No description'}</div>
                            ${rec.link ? `<a href="${rec.link}" class="item-link" target="_blank">View Details →</a>` : ''}
                        </div>
                    `;
                } else {
                    // Raw recommendation format
                    const action = rec.overall_recommendation ? rec.overall_recommendation.toLowerCase() : 'hold';
                    if (action === 'buy') buyCount++;
                    else if (action === 'sell') sellCount++;
                    else holdCount++;
                    
                    html += `
                        <div class="feed-item ${action}">
                            <div class="item-title">${rec.symbol} - ${rec.overall_recommendation} (${(rec.confidence * 100).toFixed(1)}% confidence)</div>
                            <div class="item-meta">
                                <span>💰 $${rec.current_price || 0}</span>
                                <span>🎯 $${rec.target_price || 0}</span>
                                <span>⚠️ ${rec.risk_level || 'Unknown'}</span>
                            </div>
                            <div class="item-description">${rec.reasoning || 'No reasoning provided'}</div>
                        </div>
                    `;
                }
            });
            
            feedContent.innerHTML = html;
            
            // Update stats
            document.getElementById('buyCount').textContent = buyCount;
            document.getElementById('sellCount').textContent = sellCount;
            document.getElementById('holdCount').textContent = holdCount;
            document.getElementById('totalCount').textContent = data.recommendations.length;
            stats.style.display = 'grid';
        }
    </script>
</body>
</html>
"""

@app.get("/api/feed")
async def get_feed_data(feed_type: str = "daily", symbol: str = None):
    """Get RSS feed data for dashboard"""
    try:
        if feed_type == "symbol" and symbol:
            data = await dashboard.get_rss_feed("symbol", symbol)
        elif feed_type == "api":
            data = await dashboard.get_rss_feed("api")
        else:
            data = await dashboard.get_rss_feed("daily")
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting feed data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rss-dashboard",
        "timestamp": datetime.now().isoformat(),
        "refresh_interval": REFRESH_INTERVAL
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085) 