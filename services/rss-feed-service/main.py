"""
RSS Feed Service - Generates and serves RSS feeds for daily trade recommendations
Enhanced with news event caching and LLM analysis
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

# Import news data service
from news_data_service import NewsDataService, NewsEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RSS Feed Service", version="2.0.0")

# Configuration
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:80")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost")

# Initialize news data service
news_data_service = NewsDataService()

class RSSFeedConfig(BaseModel):
    """RSS feed configuration"""
    title: str = "Daily Trading Recommendations"
    description: str = "AI-powered daily trading recommendations from Space Trading Station"
    language: str = "en-us"
    ttl: int = 60  # minutes
    max_items: int = 50
    feed_url: str = "http://localhost:11004/rss/daily-recommendations"
    site_url: str = "http://localhost:11001/"

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
    """Service for generating daily trading recommendations with news analysis"""
    
    def __init__(self):
        self.strategy_service_url = STRATEGY_SERVICE_URL
        self.rss_generator = RSSFeedGenerator(RSSFeedConfig())
        self.news_data_service = news_data_service
        
    async def get_daily_recommendations(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Get daily trading recommendations with news analysis"""
        if symbols is None:
            # Use centralized symbol list (same as trading_config.py)
            symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
                'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
                'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
            ]
            logger.info(f"✅ Using centralized symbol list with {len(symbols)} symbols")
        
        recommendations = []
        
        # Check if we have API key for real data
        polygon_api_key = os.getenv("POLYGON_API_KEY")
        
        if not polygon_api_key:
            logger.warning("⚠️ POLYGON_API_KEY not set - generating mock recommendations")
            # Generate mock recommendations when API key is not available
            mock_prices = {
                "AAPL": 185.50, "MSFT": 420.30, "GOOGL": 175.80, "AMZN": 155.20,
                "TSLA": 245.90, "NVDA": 850.75, "META": 485.60, "NFLX": 625.40,
                "AMD": 145.30, "INTC": 42.80, "SPY": 485.20
            }
            
            for symbol in symbols:
                if symbol in mock_prices:
                    current_price = mock_prices[symbol]
                    recommendation = generate_recommendation(symbol, current_price)
                    recommendations.append(recommendation)
            
            if recommendations:
                logger.info(f"✅ Generated {len(recommendations)} mock recommendations")
                return recommendations
        
        # Process each symbol with news analysis
        for symbol in symbols:
            try:
                # Get current price
                current_price = await get_real_market_price(symbol)
                if not current_price:
                    logger.warning(f"⚠️ Could not get price for {symbol}")
                    continue
                
                # Get news analysis for the symbol
                news_analysis = await self._get_news_analysis(symbol)
                
                # Generate recommendation with news context
                recommendation = generate_recommendation_with_news(symbol, current_price, news_analysis)
                recommendations.append(recommendation)
                
                logger.info(f"✅ Generated recommendation for {symbol}: ${current_price:.2f} with news analysis")
                
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {e}")
        
        if not recommendations:
            logger.warning("⚠️ No recommendations available")
        
        return recommendations
    
    async def _get_news_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get news analysis for a symbol"""
        try:
            # Get recent news from database
            recent_news = self.news_data_service.get_recent_news_for_symbol(symbol, hours_back=24)
            
            if not recent_news:
                # Try to fetch fresh news from Polygon
                logger.info(f"📰 No recent news in database for {symbol}, fetching from Polygon...")
                news_events = await self.news_data_service.fetch_news_from_polygon(symbol, days_back=7)
                
                if news_events:
                    # Analyze news with LLM
                    analyzed_news = await self.news_data_service.analyze_news_with_llm(news_events)
                    
                    # Store in database
                    store_result = self.news_data_service.store_news_batch(analyzed_news)
                    logger.info(f"💾 Stored {store_result['stored']} news articles for {symbol}")
                    
                    # Get updated recent news
                    recent_news = self.news_data_service.get_recent_news_for_symbol(symbol, hours_back=24)
            
            # Calculate news metrics
            if recent_news:
                sentiments = [n.get('sentiment_score', 0) for n in recent_news if n.get('sentiment_score') is not None]
                impacts = [n.get('impact_score', 0) for n in recent_news if n.get('impact_score') is not None]
                
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
                avg_impact = sum(impacts) / len(impacts) if impacts else 0.0
                
                return {
                    "has_news": True,
                    "article_count": len(recent_news),
                    "avg_sentiment": avg_sentiment,
                    "avg_impact": avg_impact,
                    "recent_articles": recent_news[:3],  # Top 3 most recent
                    "event_types": list(set(n.get('event_type', 'general') for n in recent_news))
                }
            else:
                return {
                    "has_news": False,
                    "article_count": 0,
                    "avg_sentiment": 0.0,
                    "avg_impact": 0.0,
                    "recent_articles": [],
                    "event_types": []
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting news analysis for {symbol}: {e}")
            return {
                "has_news": False,
                "article_count": 0,
                "avg_sentiment": 0.0,
                "avg_impact": 0.0,
                "recent_articles": [],
                "event_types": []
            }
    
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
            news_context = rec.get('news_context', {})
            
            # Create title
            title = f"{action} {symbol} - {confidence:.1%} Confidence"
            
            # Create description with news context
            description = f"""
            <h3>{action} {symbol}</h3>
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Target Price:</strong> ${target_price:.2f}</p>
            <p><strong>Confidence:</strong> {confidence:.1%}</p>
            <p><strong>Reasoning:</strong> {reasoning}</p>
            """
            
            # Add news context if available
            if news_context.get('has_news'):
                description += f"""
                <h4>📰 News Analysis</h4>
                <p><strong>Recent Articles:</strong> {news_context.get('article_count', 0)}</p>
                <p><strong>Sentiment:</strong> {news_context.get('avg_sentiment', 0.0):.2f}</p>
                <p><strong>Impact:</strong> {news_context.get('avg_impact', 0.0):.2f}</p>
                """
                
                if news_context.get('recent_articles'):
                    description += "<p><strong>Latest News:</strong></p><ul>"
                    for article in news_context['recent_articles'][:2]:  # Show top 2
                        description += f"<li>{article.get('title', 'No title')}</li>"
                    description += "</ul>"
            
            # Create link to trading dashboard RSS feeds
            link = f"http://localhost:11001/dashboard/rss/positions"
            
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

# Helper functions for real market data
async def get_real_market_price(symbol: str) -> Optional[float]:
    """Get real current price from Polygon API"""
    try:
        # Use Polygon API to get current price
        polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not polygon_api_key:
            logger.warning("⚠️ POLYGON_API_KEY not set")
            return None
            
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={polygon_api_key}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    return data['results'][0]['c']  # Close price
            else:
                logger.warning(f"⚠️ Polygon API error for {symbol}: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ Error getting price for {symbol}: {e}")
    
    return None

def generate_recommendation(symbol: str, current_price: float) -> Dict[str, Any]:
    """Generate a recommendation based on current price"""
    # Simple recommendation logic based on price ranges
    if symbol == "AAPL":
        if current_price < 180:
            action = "BUY"
            confidence = 0.85
            target_price = current_price * 1.05
            reasoning = "Strong technical indicators show upward momentum. RSI indicates oversold conditions."
        elif current_price > 200:
            action = "SELL"
            confidence = 0.75
            target_price = current_price * 0.95
            reasoning = "Price approaching resistance levels. Consider taking profits."
        else:
            action = "HOLD"
            confidence = 0.70
            target_price = current_price * 1.02
            reasoning = "Stock trading within normal range. Technical indicators suggest consolidation."
    
    elif symbol == "NVDA":
        if current_price < 800:
            action = "BUY"
            confidence = 0.90
            target_price = current_price * 1.08
            reasoning = "Exceptional AI market position. Strong earnings growth and technical momentum."
        elif current_price > 1000:
            action = "SELL"
            confidence = 0.80
            target_price = current_price * 0.92
            reasoning = "High valuation levels reached. Consider profit taking."
        else:
            action = "HOLD"
            confidence = 0.75
            target_price = current_price * 1.03
            reasoning = "Strong fundamentals but price at fair value."
    
    elif symbol == "TSLA":
        if current_price < 200:
            action = "BUY"
            confidence = 0.75
            target_price = current_price * 1.10
            reasoning = "Oversold conditions. Potential for recovery."
        elif current_price > 300:
            action = "SELL"
            confidence = 0.80
            target_price = current_price * 0.90
            reasoning = "Overbought conditions. MACD divergence suggests potential reversal."
        else:
            action = "HOLD"
            confidence = 0.65
            target_price = current_price * 1.02
            reasoning = "Volatile trading pattern. Monitor for clear direction."
    
    else:  # MSFT, GOOGL
        action = "HOLD"
        confidence = 0.70
        target_price = current_price * 1.02
        reasoning = "Stable large-cap stock. Technical indicators suggest steady performance."
    
    return {
        "symbol": symbol,
        "overall_recommendation": action,
        "confidence": confidence,
        "current_price": current_price,
        "target_price": target_price,
        "reasoning": reasoning,
        "risk_level": "Medium",
        "news_context": {}
    }

def generate_recommendation_with_news(symbol: str, current_price: float, news_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a recommendation with news analysis context"""
    # Get base recommendation
    base_rec = generate_recommendation(symbol, current_price)
    
    # Enhance with news analysis
    if news_analysis.get('has_news'):
        avg_sentiment = news_analysis.get('avg_sentiment', 0.0)
        avg_impact = news_analysis.get('avg_impact', 0.0)
        article_count = news_analysis.get('article_count', 0)
        
        # Adjust recommendation based on news sentiment
        if avg_sentiment > 0.3 and base_rec['overall_recommendation'] == 'HOLD':
            base_rec['overall_recommendation'] = 'BUY'
            base_rec['confidence'] = min(0.95, base_rec['confidence'] + 0.1)
            base_rec['reasoning'] += f" Positive news sentiment ({avg_sentiment:.2f}) supports bullish outlook."
        elif avg_sentiment < -0.3 and base_rec['overall_recommendation'] == 'HOLD':
            base_rec['overall_recommendation'] = 'SELL'
            base_rec['confidence'] = min(0.95, base_rec['confidence'] + 0.1)
            base_rec['reasoning'] += f" Negative news sentiment ({avg_sentiment:.2f}) suggests caution."
        
        # Adjust target price based on sentiment
        if avg_sentiment > 0.2:
            base_rec['target_price'] *= (1 + avg_sentiment * 0.05)
        elif avg_sentiment < -0.2:
            base_rec['target_price'] *= (1 + avg_sentiment * 0.05)
        
        # Add news context to reasoning
        if article_count > 0:
            base_rec['reasoning'] += f" Recent news activity ({article_count} articles) with {avg_impact:.2f} average impact."
    
    # Add news context to recommendation
    base_rec['news_context'] = news_analysis
    
    return base_rec

# Global service instance
recommendations_service = DailyRecommendationsService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rss-feed-service", "version": "2.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/rss/daily-recommendations", response_class=PlainTextResponse)
async def get_daily_recommendations_rss():
    """Get RSS feed for daily recommendations with news analysis"""
    try:
        logger.info("📊 Generating daily recommendations RSS feed with news analysis...")
        
        # Get recommendations with news analysis
        recommendations = await recommendations_service.get_daily_recommendations()
        
        if not recommendations:
            logger.warning("⚠️ No recommendations available")
            return "<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'><channel><title>No Recommendations Available</title></channel></rss>"
        
        # Convert to RSS items
        rss_items = recommendations_service.recommendations_to_rss_items(recommendations)
        
        # Generate RSS feed
        rss_xml = recommendations_service.rss_generator.generate_rss_feed(rss_items)
        
        logger.info(f"✅ Generated RSS feed with {len(rss_items)} items including news analysis")
        
        return PlainTextResponse(content=rss_xml, media_type="application/rss+xml")
        
    except Exception as e:
        logger.error(f"❌ Error generating RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/rss/symbol/{symbol}", response_class=PlainTextResponse)
async def get_symbol_recommendation_rss(symbol: str):
    """Get RSS feed for a specific symbol with news analysis"""
    try:
        logger.info(f"📊 Generating RSS feed for {symbol} with news analysis...")
        
        # Get recommendation for specific symbol
        recommendations = await recommendations_service.get_daily_recommendations([symbol])
        
        if not recommendations:
            logger.warning(f"⚠️ No recommendation available for {symbol}")
            return "<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'><channel><title>No Recommendation Available</title></channel></rss>"
        
        # Convert to RSS items
        rss_items = recommendations_service.recommendations_to_rss_items(recommendations)
        
        # Generate RSS feed
        rss_xml = recommendations_service.rss_generator.generate_rss_feed(rss_items)
        
        logger.info(f"✅ Generated RSS feed for {symbol} with news analysis")
        
        return PlainTextResponse(content=rss_xml, media_type="application/rss+xml")
        
    except Exception as e:
        logger.error(f"❌ Error generating RSS feed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/api/feed")
async def get_feed_data(feed_type: str = "daily", symbol: str = None):
    """Get feed data for the RSS dashboard"""
    try:
        logger.info(f"📊 Getting feed data for type: {feed_type}, symbol: {symbol}")
        
        if feed_type == "symbol" and symbol:
            # Get recommendation for specific symbol
            recommendations = await recommendations_service.get_daily_recommendations([symbol])
        elif feed_type == "api":
            # Return API format
            recommendations = await recommendations_service.get_daily_recommendations()
            return {
                "status": "success",
                "count": len(recommendations),
                "timestamp": datetime.now().isoformat(),
                "recommendations": recommendations
            }
        else:
            # Get daily recommendations
            recommendations = await recommendations_service.get_daily_recommendations()
        
        if not recommendations:
            return {
                "status": "success",
                "count": 0,
                "recommendations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert to format expected by dashboard
        feed_data = []
        for rec in recommendations:
            feed_item = {
                "symbol": rec.get("symbol"),
                "overall_recommendation": rec.get("overall_recommendation", "HOLD"),
                "confidence": rec.get("confidence", 0.0),
                "current_price": rec.get("current_price", 0.0),
                "target_price": rec.get("target_price", 0.0),
                "reasoning": rec.get("reasoning", ""),
                "risk_level": rec.get("risk_level", "Medium"),
                "news_context": rec.get("news_context", {})
            }
            feed_data.append(feed_item)
        
        return {
            "status": "success",
            "count": len(feed_data),
            "recommendations": feed_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting feed data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "count": 0,
            "recommendations": []
        }

@app.get("/api/recommendations")
async def get_recommendations_api():
    """Get recommendations as JSON API with news analysis"""
    try:
        logger.info("📊 Getting daily recommendations via API with news analysis...")
        
        # Get real recommendations with news analysis
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

@app.get("/api/news/{symbol}")
async def get_symbol_news(symbol: str, hours_back: int = 24):
    """Get recent news for a specific symbol"""
    try:
        logger.info(f"📰 Getting recent news for {symbol}...")
        
        recent_news = news_data_service.get_recent_news_for_symbol(symbol, hours_back)
        news_stats = news_data_service.get_news_statistics(symbol, days_back=7)
        
        return {
            "symbol": symbol,
            "hours_back": hours_back,
            "articles": recent_news,
            "statistics": news_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get news: {str(e)}")

@app.post("/api/news/fetch/{symbol}")
async def fetch_symbol_news(symbol: str, days_back: int = 7):
    """Fetch fresh news for a symbol from Polygon API"""
    try:
        logger.info(f"📰 Fetching fresh news for {symbol} from Polygon...")
        
        # Fetch news from Polygon
        news_events = await news_data_service.fetch_news_from_polygon(symbol, days_back)
        
        if news_events:
            # Analyze with LLM
            analyzed_news = await news_data_service.analyze_news_with_llm(news_events)
            
            # Store in database
            store_result = news_data_service.store_news_batch(analyzed_news)
            
            return {
                "symbol": symbol,
                "days_back": days_back,
                "fetched": len(news_events),
                "stored": store_result['stored'],
                "errors": store_result['errors']
            }
        else:
            return {
                "symbol": symbol,
                "days_back": days_back,
                "fetched": 0,
                "stored": 0,
                "errors": 0,
                "message": "No news found"
            }
        
    except Exception as e:
        logger.error(f"❌ Error fetching news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "RSS Feed Service",
        "version": "2.0.0",
        "features": [
            "News event caching",
            "LLM analysis integration", 
            "Polygon API integration",
            "Database storage"
        ],
        "endpoints": {
            "rss_feed": "/rss/daily-recommendations",
            "symbol_feed": "/rss/symbol/{symbol}",
            "api": "/api/recommendations",
            "news": "/api/news/{symbol}",
            "fetch_news": "/api/news/fetch/{symbol}",
            "health": "/health"
        },
        "description": "Generates RSS feeds for daily trading recommendations with news analysis"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11004) 