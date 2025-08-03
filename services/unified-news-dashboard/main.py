#!/usr/bin/env python3
"""
Unified News Dashboard Service
Combines RSS dashboard and RSS feed service into a single service
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified News Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory="templates")

# Configuration
RSS_SERVICE_URL = os.getenv("RSS_SERVICE_URL", "http://rss-feed-service:11004")
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:11103")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))  # seconds
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")

# Database connection
def get_database_connection():
    """Get database connection"""
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

class UnifiedNewsDashboard:
    """Unified news dashboard manager"""
    
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
    
    async def get_news_recommendations(self) -> Dict[str, Any]:
        """Get news recommendations"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.rss_service_url}/api/recommendations")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting news recommendations: {e}")
            return {"error": str(e)}
    
    async def get_symbol_news(self, symbol: str) -> Dict[str, Any]:
        """Get news for specific symbol"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.rss_service_url}/api/feed?type=symbol&symbol={symbol}")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting symbol news: {e}")
            return {"error": str(e)}
    
    def _parse_rss_xml(self, xml_content: str) -> Dict[str, Any]:
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
                    "pub_date": self._get_text(item, "pubDate"),
                    "guid": self._get_text(item, "guid")
                }
                channel_info["items"].append(item_data)
            
            return channel_info
            
        except Exception as e:
            logger.error(f"Error parsing RSS XML: {e}")
            return {"error": f"XML parsing error: {str(e)}"}
    
    def _get_text(self, element, tag: str) -> str:
        """Get text content from XML element"""
        found = element.find(tag)
        return found.text if found is not None else ""

dashboard = UnifiedNewsDashboard()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unified-news-dashboard"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main unified news dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/rss", response_class=HTMLResponse)
async def rss_dashboard(request: Request):
    """RSS dashboard section"""
    return templates.TemplateResponse("rss.html", {"request": request})

@app.get("/feed", response_class=HTMLResponse)
async def feed_dashboard(request: Request):
    """Feed dashboard section"""
    return templates.TemplateResponse("feed.html", {"request": request})

@app.get("/api/feed")
async def get_feed_data(feed_type: str = "daily", symbol: str = None):
    """Get RSS feed data API"""
    return await dashboard.get_rss_feed(feed_type, symbol)

@app.get("/api/recommendations")
async def get_recommendations():
    """Get news recommendations API"""
    return await dashboard.get_news_recommendations()

@app.get("/api/symbol/{symbol}/news")
async def get_symbol_news(symbol: str):
    """Get news for specific symbol API"""
    return await dashboard.get_symbol_news(symbol)

@app.get("/api/feed/stream")
async def stream_feed():
    """Stream RSS feed updates"""
    async def generate():
        while True:
            try:
                feed_data = await dashboard.get_rss_feed("daily")
                yield f"data: {json.dumps(feed_data)}\n\n"
                await asyncio.sleep(REFRESH_INTERVAL)
            except Exception as e:
                logger.error(f"Error streaming feed: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                await asyncio.sleep(REFRESH_INTERVAL)
    
    return StreamingResponse(generate(), media_type="text/plain")

# Database-driven RSS feed endpoints
@app.get("/api/rss/trades", response_class=PlainTextResponse)
async def get_trades_rss_feed():
    """Generate RSS feed for recent trades from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent trades
            result = conn.execute(text("""
                SELECT 
                    bt.timestamp,
                    bt.symbol,
                    bt.action,
                    bt.quantity,
                    bt.price,
                    bt.value,
                    bt.pnl,
                    bt.confidence,
                    br.strategy_name,
                    br.backtest_name
                FROM backtest_trades bt
                JOIN backtest_runs br ON bt.run_id = br.run_id
                WHERE bt.symbol IS NOT NULL AND bt.symbol != '' AND LENGTH(TRIM(bt.symbol)) > 0
                ORDER BY bt.timestamp DESC
                LIMIT 50
            """))
            
            # Generate RSS XML
            rss = ET.Element('rss', version='2.0')
            channel = ET.SubElement(rss, 'channel')
            
            title = ET.SubElement(channel, 'title')
            title.text = 'Trading System - Recent Trades'
            
            link = ET.SubElement(channel, 'link')
            link.text = 'http://localhost:11116/api/rss/trades'
            
            description = ET.SubElement(channel, 'description')
            description.text = 'Recent trading activity and transactions from the trading system'
            
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
            last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            for row in result:
                item = ET.SubElement(channel, 'item')
                
                # Create trade title with emojis
                if row.action == "BUY":
                    action_emoji = "🟢"
                    action_desc = "BUY"
                else:
                    action_emoji = "🔴"
                    action_desc = "SELL"
                
                # Determine P&L status
                if row.pnl > 0:
                    pnl_emoji = "📈"
                    pnl_status = "Profit"
                elif row.pnl < 0:
                    pnl_emoji = "📉"
                    pnl_status = "Loss"
                else:
                    pnl_emoji = "➖"
                    pnl_status = "Neutral"
                
                item_title = ET.SubElement(item, 'title')
                item_title.text = f"{action_emoji} {action_desc} {row.quantity:,} {row.symbol} @ ${row.price:.2f} = ${row.value:,.2f}"
                
                item_link = ET.SubElement(item, 'link')
                item_link.text = f"http://localhost:11116/trade/{row.symbol}"
                
                item_description = ET.SubElement(item, 'description')
                item_description.text = f"""
                <strong>Trade Details:</strong><br/>
                <strong>Security:</strong> {row.symbol}<br/>
                <strong>Action:</strong> {action_emoji} {action_desc}<br/>
                <strong>Quantity:</strong> {row.quantity:,} shares<br/>
                <strong>Price:</strong> ${row.price:.2f}<br/>
                <strong>Value:</strong> ${row.value:,.2f}<br/>
                <strong>P&L:</strong> {pnl_emoji} ${row.pnl:,.2f} ({pnl_status})<br/>
                <strong>Strategy:</strong> {row.strategy_name}<br/>
                <strong>Backtest:</strong> {row.backtest_name}<br/>
                <strong>Confidence:</strong> {row.confidence:.1%}<br/>
                <strong>Timestamp:</strong> {row.timestamp.strftime('%Y-%m-%d %H:%M:%S') if row.timestamp else 'N/A'}
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = row.timestamp.strftime('%a, %d %b %Y %H:%M:%S %z') if row.timestamp else datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            return minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    except Exception as e:
        logger.error(f"Error generating trades RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/rss/positions", response_class=PlainTextResponse)
async def get_positions_rss_feed():
    """Generate RSS feed for active positions from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get active positions
            result = conn.execute(text("""
                SELECT 
                    symbol,
                    quantity,
                    avg_price,
                    current_price,
                    market_value,
                    unrealized_pnl,
                    unrealized_pnl_percent,
                    entry_date,
                    strategy,
                    holding_days
                FROM portfolio_positions
                WHERE active = true
                ORDER BY unrealized_pnl DESC
            """))
            
            # Generate RSS XML
            rss = ET.Element('rss', version='2.0')
            channel = ET.SubElement(rss, 'channel')
            
            title = ET.SubElement(channel, 'title')
            title.text = 'Trading System - Active Positions'
            
            link = ET.SubElement(channel, 'link')
            link.text = 'http://localhost:11116/api/rss/positions'
            
            description = ET.SubElement(channel, 'description')
            description.text = 'Current portfolio positions and their performance'
            
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
            last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            for row in result:
                item = ET.SubElement(channel, 'item')
                
                # Determine P&L status
                if row.unrealized_pnl > 0:
                    pnl_emoji = "📈"
                    pnl_status = "Profitable"
                elif row.unrealized_pnl < 0:
                    pnl_emoji = "📉"
                    pnl_status = "Losing"
                else:
                    pnl_emoji = "➖"
                    pnl_status = "Neutral"
                
                item_title = ET.SubElement(item, 'title')
                item_title.text = f"{pnl_emoji} {row.symbol}: {row.quantity:,} shares @ ${row.avg_price:.2f} (Current: ${row.current_price:.2f})"
                
                item_link = ET.SubElement(item, 'link')
                item_link.text = f"http://localhost:11116/position/{row.symbol}"
                
                item_description = ET.SubElement(item, 'description')
                item_description.text = f"""
                <strong>Position Details:</strong><br/>
                <strong>Symbol:</strong> {row.symbol}<br/>
                <strong>Quantity:</strong> {row.quantity:,} shares<br/>
                <strong>Average Price:</strong> ${row.avg_price:.2f}<br/>
                <strong>Current Price:</strong> ${row.current_price:.2f}<br/>
                <strong>Market Value:</strong> ${row.market_value:,.2f}<br/>
                <strong>Unrealized P&L:</strong> {pnl_emoji} ${row.unrealized_pnl:,.2f} ({row.unrealized_pnl_percent:.2%})<br/>
                <strong>Status:</strong> {pnl_status}<br/>
                <strong>Strategy:</strong> {row.strategy}<br/>
                <strong>Entry Date:</strong> {row.entry_date.strftime('%Y-%m-%d') if row.entry_date else 'N/A'}<br/>
                <strong>Holding Days:</strong> {row.holding_days} days
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            return minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    except Exception as e:
        logger.error(f"Error generating positions RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 