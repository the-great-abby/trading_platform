"""
RSS Feed Service - Generates and serves RSS feeds for daily trade recommendations
"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
import httpx
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RSS Feed Service", version="1.0.0")

# Configuration
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost")

class RSSFeedConfig(BaseModel):
    """RSS feed configuration"""
    title: str = "Daily Trading Recommendations"
    description: str = "AI-powered daily trading recommendations from Space Trading Station"
    language: str = "en-us"
    ttl: int = 60  # minutes
    max_items: int = 50
    feed_url: str = "http://localhost:8084/rss/daily-recommendations"
    site_url: str = "http://localhost:8081"

class RSSItem(BaseModel):
    """RSS item structure"""
    title: str
    description: str
    link: str
    guid: str
    pub_date: datetime
    category: Optional[str] = None
    author: str = "Space Trading Station AI"

class RSSFeedGenerator:
    """RSS feed generator"""
    
    def __init__(self, config: RSSFeedConfig):
        self.config = config
        
    def generate_rss_feed(self, items: List[RSSItem]) -> str:
        """Generate RSS XML feed"""
        
        # Create RSS root element
        rss = ET.Element("rss", version="2.0")
        rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
        
        # Create channel element
        channel = ET.SubElement(rss, "channel")
        
        # Channel metadata
        title_elem = ET.SubElement(channel, "title")
        title_elem.text = self.config.title
        
        description_elem = ET.SubElement(channel, "description")
        description_elem.text = self.config.description
        
        link_elem = ET.SubElement(channel, "link")
        link_elem.text = self.config.site_url
        
        language_elem = ET.SubElement(channel, "language")
        language_elem.text = self.config.language
        
        ttl_elem = ET.SubElement(channel, "ttl")
        ttl_elem.text = str(self.config.ttl)
        
        # Atom link for RSS readers
        atom_link = ET.SubElement(channel, "atom:link")
        atom_link.set("href", self.config.feed_url)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")
        
        # Add items
        for item in items[:self.config.max_items]:
            item_elem = ET.SubElement(channel, "item")
            
            title = ET.SubElement(item_elem, "title")
            title.text = item.title
            
            description = ET.SubElement(item_elem, "description")
            description.text = item.description
            
            link = ET.SubElement(item_elem, "link")
            link.text = item.link
            
            guid = ET.SubElement(item_elem, "guid")
            guid.text = item.guid
            
            pub_date = ET.SubElement(item_elem, "pubDate")
            pub_date.text = item.pub_date.strftime("%a, %d %b %Y %H:%M:%S %z")
            
            if item.category:
                category = ET.SubElement(item_elem, "category")
                category.text = item.category
        
        # Pretty print XML
        rough_string = ET.tostring(rss, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

class DailyRecommendationsService:
    """Service for generating daily trading recommendations"""
    
    def __init__(self):
        self.strategy_service_url = STRATEGY_SERVICE_URL
        self.rss_generator = RSSFeedGenerator(RSSFeedConfig())
        
    async def get_daily_recommendations(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Get daily recommendations for symbols"""
        try:
            if not symbols:
                # Use default symbols from trading config
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC"]
            
            recommendations = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for symbol in symbols:
                    try:
                        # Get recommendation from strategy service
                        response = await client.post(
                            f"{self.strategy_service_url}/recommendations/stock",
                            json={
                                "symbol": symbol,
                                "include_ai_analysis": True,
                                "include_news_sentiment": True,
                                "include_risk_assessment": True,
                                "strategies": ["rsi_strategy", "macd_strategy", "bollinger_bands_strategy", "news_enhanced_strategy"]
                            }
                        )
                        
                        if response.status_code == 200:
                            recommendation = response.json()
                            recommendations.append(recommendation)
                            logger.info(f"✅ Got recommendation for {symbol}: {recommendation['overall_recommendation']}")
                        else:
                            logger.warning(f"⚠️ Failed to get recommendation for {symbol}: {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error getting recommendation for {symbol}: {e}")
                        continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting daily recommendations: {e}")
            return []
    
    def recommendations_to_rss_items(self, recommendations: List[Dict[str, Any]]) -> List[RSSItem]:
        """Convert recommendations to RSS items"""
        items = []
        
        for rec in recommendations:
            symbol = rec.get('symbol', 'UNKNOWN')
            action = rec.get('overall_recommendation', 'HOLD')
            confidence = rec.get('confidence', 0.0)
            current_price = rec.get('current_price', 0.0)
            target_price = rec.get('target_price', 0.0)
            reasoning = rec.get('reasoning', 'No reasoning provided')
            
            # Create title
            title = f"{action} {symbol} - {confidence:.1%} Confidence"
            
            # Create description
            description = f"""
            <h3>{action} {symbol}</h3>
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Target Price:</strong> ${target_price:.2f}</p>
            <p><strong>Confidence:</strong> {confidence:.1%}</p>
            <p><strong>Reasoning:</strong> {reasoning}</p>
            """
            
            # Create link
            link = f"http://localhost:8081/dashboard/recommendations/{symbol}"
            
            # Create GUID
            guid = f"recommendation-{symbol}-{datetime.now().strftime('%Y%m%d')}"
            
            # Create RSS item
            item = RSSItem(
                title=title,
                description=description,
                link=link,
                guid=guid,
                pub_date=datetime.now(),
                category=action.lower()
            )
            
            items.append(item)
        
        return items

# Global service instance
recommendations_service = DailyRecommendationsService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rss-feed-service", "timestamp": datetime.now().isoformat()}

@app.get("/rss/daily-recommendations", response_class=PlainTextResponse)
async def get_daily_recommendations_rss():
    """Get RSS feed for daily recommendations"""
    try:
        logger.info("📊 Generating daily recommendations RSS feed...")
        
        # Get daily recommendations
        recommendations = await recommendations_service.get_daily_recommendations()
        
        if not recommendations:
            logger.warning("⚠️ No recommendations available")
            return "<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'><channel><title>No Recommendations Available</title></channel></rss>"
        
        # Convert to RSS items
        rss_items = recommendations_service.recommendations_to_rss_items(recommendations)
        
        # Generate RSS feed
        rss_xml = recommendations_service.rss_generator.generate_rss_feed(rss_items)
        
        logger.info(f"✅ Generated RSS feed with {len(rss_items)} items")
        
        return PlainTextResponse(content=rss_xml, media_type="application/rss+xml")
        
    except Exception as e:
        logger.error(f"❌ Error generating RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/rss/symbol/{symbol}", response_class=PlainTextResponse)
async def get_symbol_recommendation_rss(symbol: str):
    """Get RSS feed for a specific symbol"""
    try:
        logger.info(f"📊 Generating RSS feed for {symbol}...")
        
        # Get recommendation for specific symbol
        recommendations = await recommendations_service.get_daily_recommendations([symbol])
        
        if not recommendations:
            logger.warning(f"⚠️ No recommendation available for {symbol}")
            return "<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'><channel><title>No Recommendation Available</title></channel></rss>"
        
        # Convert to RSS items
        rss_items = recommendations_service.recommendations_to_rss_items(recommendations)
        
        # Generate RSS feed
        rss_xml = recommendations_service.rss_generator.generate_rss_feed(rss_items)
        
        logger.info(f"✅ Generated RSS feed for {symbol}")
        
        return PlainTextResponse(content=rss_xml, media_type="application/rss+xml")
        
    except Exception as e:
        logger.error(f"❌ Error generating RSS feed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/api/recommendations")
async def get_recommendations_api():
    """Get recommendations as JSON API"""
    try:
        logger.info("📊 Getting daily recommendations via API...")
        
        # Get daily recommendations
        recommendations = await recommendations_service.get_daily_recommendations()
        
        return {
            "status": "success",
            "count": len(recommendations),
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "RSS Feed Service",
        "version": "1.0.0",
        "endpoints": {
            "rss_feed": "/rss/daily-recommendations",
            "symbol_feed": "/rss/symbol/{symbol}",
            "api": "/api/recommendations",
            "health": "/health"
        },
        "description": "Generates RSS feeds for daily trading recommendations"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8084) 