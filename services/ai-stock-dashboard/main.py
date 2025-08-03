#!/usr/bin/env python3
"""
AI Stock Analysis Dashboard - Interactive web dashboard for AI-powered stock analysis
Uses real market data, news feed, LLM service, and vector database
Supports asynchronous report processing with browser push notifications
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
import logging
import os
import json
import uuid
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Stock Analysis Dashboard", version="1.0.0")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:11008", "http://localhost:11007", "http://127.0.0.1:11008", "http://127.0.0.1:11007"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates (optional)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Static directory doesn't exist, skip mounting
    pass

templates = Jinja2Templates(directory="templates")

# Configuration - Real service URLs
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:11081")
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:11031")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:11084")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "http://rss-feed-service:11004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:80")

# VAPID Configuration for Web Push Notifications
def generate_vapid_keys():
    """Generate VAPID keys for web push notifications"""
    # Use a known working VAPID key for web push notifications
    # This is a properly formatted key that works with the Push API
    return (
        "BEl62iUYgUivxIkv69yViEuiBIa1FQj8vCN8vx7K_6gf35aSW_NiKdsckgAf7UW1SVbEXkuVxNUaiYrFQHDf1E",
        "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZy96VDV5WitUYmw1MUdXVm0Kb0dWNkpDbG1FRVJ5SkN0NGNkcWx5QmJVdERTaFJBTkNBQVJYRm9Qd29BWDE0Y21QVk11dDY3c0dDZlhPaFZQZApORGV6MU5TNVlDWlFIR0dpNko0T0s0cWhiN0hlL1crNUV2VlpCQWU3Q2RUSXd6OFhTU1Z1SkRRcQotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg"
    )

# Generate VAPID keys
VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY = generate_vapid_keys()

# Validate VAPID key format
def validate_vapid_key(key: str) -> bool:
    """Validate VAPID key format"""
    try:
        # Check if key is base64 URL-safe
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', key):
            return False
        
        # Check length (should be around 87 characters for base64 URL-safe DER format)
        if len(key) < 80 or len(key) > 150:
            return False
            
        return True
    except:
        return False

# Force use of the properly formatted VAPID key for Push API
VAPID_PUBLIC_KEY = "BAxIINiuz1sx6JFpsmL1f4Er_q8h_PWVTLa9husCk6CXXFy9My-d8_SxS7ff66vUIAiL0Bu8qYmTyVpU8-Jd8wY"

# Report status tracking
class ReportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY_WITHOUT_AI = "ready_without_ai"
    READY_WITH_AI = "ready_with_ai"
    FAILED = "failed"

@dataclass
class ReportJob:
    """Report job tracking"""
    job_id: str
    symbol: str
    current_price: float
    status: ReportStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    notification_sent: bool = False

# In-memory storage for report jobs (in production, use Redis or database)
report_jobs: Dict[str, ReportJob] = {}

# Pydantic models
class StockAnalysisRequest(BaseModel):
    symbol: str
    current_price: float
    include_news: bool = True
    include_technical: bool = True
    include_sentiment: bool = True
    async_mode: bool = False  # New: request async processing
    user_email: Optional[str] = None  # For notifications

class StockAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    recommendation: str
    confidence: int
    risk_level: str
    reasoning: str
    target_price: Optional[float]
    stop_loss: Optional[float]
    technical_indicators: Dict[str, Any]
    news_sentiment: Optional[Dict[str, Any]] = None
    market_data: Optional[Dict[str, Any]] = None
    vector_context: Optional[Dict[str, Any]] = None
    analysis_time: float
    timestamp: str

class ReportJobRequest(BaseModel):
    symbol: str
    current_price: float
    include_news: bool = True
    include_technical: bool = True
    include_sentiment: bool = True
    user_email: Optional[str] = None

class WebPushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]

class AIStockAnalyzer:
    """AI Stock Analyzer using real data sources"""
    
    def __init__(self):
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.llm_proxy_url = LLM_PROXY_URL
        self.backtest_api_url = BACKTEST_API_URL
        self.market_data_url = MARKET_DATA_URL
        self.rss_feed_url = RSS_FEED_URL
        self.notification_service_url = NOTIFICATION_SERVICE_URL

    async def analyze_stock(self, symbol: str, current_price: float,
                          include_news: bool = True, include_technical: bool = True,
                          include_sentiment: bool = True) -> Dict[str, Any]:
        """Analyze stock using real data sources"""
        start_time = datetime.now()
        
        # Initialize data structures
        market_data = {}
        technical_analysis = {}
        news_sentiment = {}
        vector_context = {}
        
        # Step 1: Get real market data (don't fail if this doesn't work)
        try:
            market_data = await self._get_real_market_data(symbol, current_price)
        except Exception as e:
            logger.warning(f"Could not fetch market data for {symbol}: {e}")
            market_data = {
                "price": current_price,
                "volume": 0,
                "change_percent": 0.0,
                "market_cap": "N/A",
                "technical_indicators": {}
            }
        
        # Step 2: Get technical analysis (don't fail if this doesn't work)
        if include_technical:
            try:
                technical_analysis = await self._get_real_technical_analysis(symbol, market_data)
            except Exception as e:
                logger.warning(f"Could not fetch technical analysis for {symbol}: {e}")
                technical_analysis = self._calculate_basic_technical_indicators(market_data)
        
        # Step 3: Get real news sentiment (don't fail if this doesn't work)
        if include_news:
            try:
                news_sentiment = await self._get_real_news_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not fetch news sentiment for {symbol}: {e}")
                news_sentiment = {
                    "sentiment": "NEUTRAL",
                    "sentiment_score": 0.0,
                    "news_items": [],
                    "confidence": 50
                }
        
        # Step 4: Get vector database context (don't fail if this doesn't work)
        try:
            vector_context = await self._get_vector_context(symbol)
        except Exception as e:
            logger.warning(f"Could not fetch vector context for {symbol}: {e}")
            vector_context = {
                "market_context": [],
                "news_context": [],
                "decision_context": []
            }
        
        # Step 5: Generate AI recommendation using real LLM
        ai_analysis_successful = False
        try:
            ai_analysis = await self._generate_real_ai_recommendation(
                symbol, current_price, market_data, technical_analysis, news_sentiment, vector_context
            )
            # Check if AI analysis was successful (has meaningful reasoning)
            ai_analysis_successful = (
                ai_analysis.get("reasoning") and 
                len(ai_analysis.get("reasoning", "")) > 50 and
                ai_analysis.get("reasoning") != "Analysis in progress"
            )
        except Exception as e:
            logger.error(f"Could not generate AI recommendation for {symbol}: {e}")
            ai_analysis = self._get_fallback_recommendation({
                "symbol": symbol,
                "current_price": current_price,
                "market_data": market_data,
                "technical_analysis": technical_analysis,
                "news_sentiment": news_sentiment,
                "vector_context": vector_context
            })
            ai_analysis_successful = False
        
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "recommendation": ai_analysis.get("recommendation", "HOLD"),
            "confidence": int(ai_analysis.get("confidence", 5)),
            "risk_level": ai_analysis.get("risk_level", "MEDIUM"),
            "reasoning": ai_analysis.get("reasoning", "Analysis in progress"),
            "target_price": ai_analysis.get("target_price"),
            "stop_loss": ai_analysis.get("stop_loss"),
            "technical_indicators": technical_analysis,
            "news_sentiment": news_sentiment,
            "market_data": market_data,
            "vector_context": vector_context,
            "analysis_time": analysis_time,
            "timestamp": datetime.now().isoformat(),
            "ai_analysis_successful": ai_analysis_successful,
            "ai_analysis": ai_analysis
        }

    async def _get_real_market_data(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Get real market data from market data service"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to get from market data service
                url = f"{self.market_data_url}/market-data/current/{symbol}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "price": data.get("price", current_price),
                            "volume": data.get("volume", 0),
                            "change_percent": data.get("change_percent", 0.0),
                            "market_cap": data.get("market_cap", "N/A"),
                            "technical_indicators": data.get("technical_indicators", {})
                        }
        except Exception as e:
            logger.warning(f"Could not fetch real market data for {symbol}: {e}")
        
        # Fallback to basic data
        return {
            "price": current_price,
            "volume": 0,
            "change_percent": 0.0,
            "market_cap": "N/A",
            "technical_indicators": {}
        }

    async def _get_real_technical_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get real technical analysis"""
        try:
            # Use cached market data manager if available
            async with aiohttp.ClientSession() as session:
                # Get historical data for technical analysis
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)
                
                url = f"{self.market_data_url}/market-data/historical"
                request_data = {
                    "symbol": symbol,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "interval": "1d"
                }
                
                logger.info(f"Requesting historical data for {symbol} from {url}")
                async with session.post(url, json=request_data, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Received historical data for {symbol}: {len(data.get('data', []))} data points")
                        if data.get("data") and len(data["data"]) >= 20:
                            logger.info(f"Calculating technical indicators for {symbol} with {len(data['data'])} data points")
                            result = self._calculate_technical_indicators(data["data"])
                            logger.info(f"Technical indicators for {symbol}: {result}")
                            return result
                        else:
                            logger.warning(f"Insufficient historical data for {symbol}: {len(data.get('data', []))} data points")
                    else:
                        logger.warning(f"Failed to get historical data for {symbol}: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"Could not fetch real technical analysis for {symbol}: {e}")
        
        # Fallback to basic technical analysis
        logger.info(f"Using fallback technical analysis for {symbol}")
        return self._calculate_basic_technical_indicators(market_data)

    def _calculate_technical_indicators(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate technical indicators from historical data"""
        if not historical_data or len(historical_data) < 20:
            return {}
        
        # Extract close prices and volumes from the historical data
        prices = [float(d["close"]) for d in historical_data]
        volumes = [int(d["volume"]) for d in historical_data]
        
        # Calculate RSI
        rsi = self._calculate_rsi(prices, 14)
        
        # Calculate MACD
        macd_data = self._calculate_macd(prices)
        
        # Calculate Moving Averages
        sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
        sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else prices[-1]
        
        # Calculate volume SMA
        volume_sma = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
        
        return {
            "rsi": round(rsi, 1),
            "macd": {
                "value": round(macd_data["macd"], 3),
                "signal": round(macd_data["signal"], 3),
                "histogram": round(macd_data["histogram"], 3)
            },
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "volume_sma": round(volume_sma, 0),
            "price_trend": "bullish" if sma_20 > sma_50 else "bearish"
        }

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD"""
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate EMA12 and EMA26
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        
        macd = ema12 - ema26
        
        # Calculate signal line (EMA of MACD)
        # Instead of using a single MACD value, we'll use a simple approximation
        # In a real implementation, you'd track MACD values over time
        signal = macd * 0.8  # Simple approximation for signal line
        histogram = macd - signal
        
        return {
            "macd": macd,
            "signal": signal,
            "histogram": histogram
        }

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def _calculate_basic_technical_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic technical indicators from current market data"""
        price = market_data.get("price", 0)
        change_percent = market_data.get("change_percent", 0)
        
        # Simple indicators based on price change
        rsi = 50 + (change_percent * 2)  # Simplified RSI
        rsi = max(0, min(100, rsi))
        
        macd_value = change_percent * 0.1  # Simplified MACD
        
        return {
            "rsi": round(rsi, 1),
            "macd": {
                "value": round(macd_value, 3),
                "signal": round(macd_value * 0.8, 3),
                "histogram": round(macd_value * 0.2, 3)
            },
            "sma_20": round(price * 0.98, 2),
            "sma_50": round(price * 0.95, 2),
            "volume_sma": market_data.get("volume", 0),
            "price_trend": "bullish" if change_percent > 0 else "bearish"
        }

    async def _get_real_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get real news sentiment from RSS feed service"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get news from RSS feed service
                url = f"{self.rss_feed_url}/api/news/{symbol}"
                params = {"hours_back": 24}
                
                async with session.get(url, params=params, timeout=60) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._analyze_news_sentiment(data.get("articles", []))
        except Exception as e:
            import traceback
            logger.warning(f"Could not fetch real news for {symbol}: {e}")
            logger.warning(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback to basic sentiment
        return {
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.0,
            "news_items": [],
            "confidence": 50
        }

    def _analyze_news_sentiment(self, articles: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news articles"""
        if not articles:
            return {
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "news_items": [],
                "confidence": 50
            }
        
        # Calculate average sentiment score
        sentiment_scores = [article.get("sentiment_score", 0) for article in articles]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Determine sentiment category
        if avg_sentiment > 0.3:
            sentiment = "POSITIVE"
        elif avg_sentiment < -0.3:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "sentiment_score": round(avg_sentiment, 2),
            "news_items": articles[:5],  # Top 5 articles
            "confidence": min(95, len(articles) * 10)
        }

    async def _get_vector_context(self, symbol: str) -> Dict[str, Any]:
        """Get vector database context for the symbol"""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for similar patterns in vector database
                url = f"{self.vector_storage_url}/api/search/context"
                params = {
                    "query": f"market data for {symbol}",
                    "symbol": symbol,
                    "context_type": "all"
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.warning(f"Could not fetch vector context for {symbol}: {e}")
        
        return {
            "market_context": [],
            "news_context": [],
            "decision_context": []
        }

    async def _generate_real_ai_recommendation(self, symbol: str, current_price: float,
                                             market_data: Dict[str, Any], technical_analysis: Dict[str, Any],
                                             news_sentiment: Dict[str, Any], vector_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI recommendation using real LLM service"""
        logger.info(f"Starting AI recommendation generation for {symbol}")
        try:
            # Prepare context for LLM
            context = {
                "symbol": symbol,
                "current_price": current_price,
                "market_data": market_data,
                "technical_analysis": technical_analysis,
                "news_sentiment": news_sentiment,
                "vector_context": vector_context
            }
            
            # Create comprehensive prompt
            prompt = self._build_ai_prompt(context)
            
            async with aiohttp.ClientSession() as session:
                # Call real LLM service
                llm_request = {
                    "operation": "custom",
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "You are an expert stock analyst."},
                            {"role": "user", "content": prompt}
                        ],
                        "task_type": "stock_analysis",
                        "temperature": 0.3,
                        "max_tokens": 800,
                        "use_cache": True
                    },
                    "model": "gpt-3.5-turbo",
                    "priority": 1,
                    "use_cache": True
                }
                
                logger.info(f"Calling LLM service at: {self.llm_proxy_url}/api/v1/llm")
                logger.info(f"LLM request: {llm_request}")
                
                url = f"{self.llm_proxy_url}/api/v1/llm"
                logger.info(f"Making POST request to: {url}")
                async with session.post(url, json=llm_request, timeout=120) as response:
                    logger.info(f"LLM service response status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"LLM service response: {result}")
                        if result.get("success") and result.get("data"):
                            return self._parse_ai_response(result["data"]["content"], context)
                        else:
                            logger.error(f"LLM service error: {result.get('error', 'Unknown error')}")
                            return self._get_fallback_recommendation(context)
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM service error: {response.status} - {error_text}")
                        return self._get_fallback_recommendation(context)
                        
        except Exception as e:
            import traceback
            logger.error(f"Error generating AI recommendation: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._get_fallback_recommendation({
                "symbol": symbol,
                "current_price": current_price,
                "market_data": market_data,
                "technical_analysis": technical_analysis,
                "news_sentiment": news_sentiment
            })

    def _build_ai_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for AI analysis"""
        symbol = context["symbol"]
        current_price = context["current_price"]
        market_data = context["market_data"]
        technical = context["technical_analysis"]
        news = context["news_sentiment"]
        
        prompt = f"""
You are an expert stock analyst. Analyze the following data for {symbol} and provide a trading recommendation.

Current Market Data:
- Symbol: {symbol}
- Price: ${current_price:.2f}
- Volume: {market_data.get('volume', 0):,}
- Change: {market_data.get('change_percent', 0):.2f}%
- Market Cap: {market_data.get('market_cap', 'N/A')}

Technical Indicators:
- RSI: {technical.get('rsi', 0):.1f}
- MACD: {technical.get('macd', {}).get('value', 0):.3f}
- 20-day SMA: ${technical.get('sma_20', 0):.2f}
- 50-day SMA: ${technical.get('sma_50', 0):.2f}
- Price Trend: {technical.get('price_trend', 'neutral')}

News Sentiment:
- Sentiment: {news.get('sentiment', 'NEUTRAL')}
- Sentiment Score: {news.get('sentiment_score', 0):.2f}
- News Count: {len(news.get('news_items', []))}

Provide your analysis in the following JSON format:
{{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 1-10,
    "reasoning": "Detailed explanation",
    "target_price": 0.0,
    "stop_loss": 0.0,
    "risk_level": "LOW|MEDIUM|HIGH"
}}

Focus on:
1. Technical analysis signals
2. News sentiment impact
3. Risk assessment
4. Market timing
5. Historical patterns
"""

        return prompt

    def _parse_ai_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response and extract recommendation"""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
                return analysis
        except:
            pass
        
        # Fallback parsing
        return self._parse_fallback_response(response_text, context)

    def _parse_fallback_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response when JSON extraction fails"""
        symbol = context["symbol"]
        current_price = context["current_price"]
        technical = context["technical_analysis"]
        
        # Simple keyword-based analysis
        response_lower = response_text.lower()
        
        if "buy" in response_lower:
            recommendation = "BUY"
            confidence = 7
        elif "sell" in response_lower:
            recommendation = "SELL"
            confidence = 7
        else:
            recommendation = "HOLD"
            confidence = 5
        
        # Calculate target prices
        if recommendation == "BUY":
            target_price = current_price * 1.05
            stop_loss = current_price * 0.95
        elif recommendation == "SELL":
            target_price = current_price * 0.95
            stop_loss = current_price * 1.05
        else:
            target_price = current_price * 1.02
            stop_loss = current_price * 0.98
        
        # Determine risk level
        rsi = technical.get('rsi', 50)
        if rsi > 70 or rsi < 30:
            risk_level = "HIGH"
        elif rsi > 60 or rsi < 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_level": risk_level
        }

    def _get_fallback_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback recommendation when LLM is unavailable"""
        symbol = context["symbol"]
        current_price = context["current_price"]
        technical = context["technical_analysis"]
        
        # Simple rule-based analysis
        rsi = technical.get('rsi', 50)
        macd_value = technical.get('macd', {}).get('value', 0)
        
        if rsi < 30 and macd_value > 0:
            recommendation = "BUY"
            confidence = 6
            reasoning = f"{symbol} appears oversold with positive momentum"
        elif rsi > 70 and macd_value < 0:
            recommendation = "SELL"
            confidence = 7
            reasoning = f"{symbol} appears overbought with negative momentum"
        else:
            recommendation = "HOLD"
            confidence = 5
            reasoning = f"{symbol} shows mixed signals, waiting for clearer direction"
        
        # Calculate target prices
        if recommendation == "BUY":
            target_price = current_price * 1.05
            stop_loss = current_price * 0.95
        elif recommendation == "SELL":
            target_price = current_price * 0.95
            stop_loss = current_price * 1.05
        else:
            target_price = current_price * 1.02
            stop_loss = current_price * 0.98
        
        # Determine risk level
        if rsi > 70 or rsi < 30:
            risk_level = "HIGH"
        elif rsi > 60 or rsi < 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_level": risk_level
        }

    async def _fallback_analysis(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Complete fallback analysis when all services fail"""
        return {
            "symbol": symbol,
            "current_price": current_price,
            "recommendation": "HOLD",
            "confidence": 3,
            "risk_level": "MEDIUM",
            "reasoning": "Analysis services temporarily unavailable",
            "target_price": current_price * 1.02,
            "stop_loss": current_price * 0.98,
            "technical_indicators": {},
            "news_sentiment": {},
            "market_data": {"price": current_price},
            "vector_context": {},
            "analysis_time": 0.1,
            "timestamp": datetime.now().isoformat()
        }

    async def send_browser_notification(self, job_id: str, result: Dict[str, Any], user_email: Optional[str] = None):
        """Send browser push notification when report is ready"""
        try:
            symbol = result.get("symbol", "Unknown")
            recommendation = result.get("recommendation", "HOLD")
            confidence = result.get("confidence", 5)
            
            # Send notification via notification service
            notification_data = {
                "title": f"📊 {symbol} Analysis Complete",
                "message": f"{symbol}: {recommendation} recommendation with {confidence}/10 confidence",
                "notification_type": "stock_analysis_complete",
                "priority": "normal",
                "channels": ["email"] if user_email else [],
                "recipients": [user_email] if user_email else [],
                "data": {
                    "job_id": job_id,
                    "symbol": symbol,
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "result": result
                }
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.notification_service_url}/api/notifications/push"
                async with session.post(url, json=notification_data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"✅ Browser notification sent for job {job_id}")
                    else:
                        logger.warning(f"⚠️ Failed to send browser notification for job {job_id}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending browser notification: {e}")

# Initialize analyzer
analyzer = AIStockAnalyzer()

@app.get("/sw.js")
async def service_worker():
    """Serve the Service Worker file"""
    try:
        with open("static/sw.js", "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Service Worker not found")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/analyze")
async def analyze_stock(request: StockAnalysisRequest) -> StockAnalysisResponse:
    """Analyze a stock using real data sources"""
    try:
        result = await analyzer.analyze_stock(
            symbol=request.symbol,
            current_price=request.current_price,
            include_news=request.include_news,
            include_technical=request.include_technical,
            include_sentiment=request.include_sentiment
        )
        
        return StockAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in stock analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/submit")
async def submit_report_job(request: ReportJobRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Submit a report job for asynchronous processing"""
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create report job
        report_job = ReportJob(
            job_id=job_id,
            symbol=request.symbol,
            current_price=request.current_price,
            status=ReportStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Store job
        report_jobs[job_id] = report_job
        
        # Start background processing
        background_tasks.add_task(
            process_report_job,
            job_id,
            request.symbol,
            request.current_price,
            request.include_news,
            request.include_technical,
            request.include_sentiment,
            request.user_email
        )
        
        return {
            "job_id": job_id,
            "status": "submitted",
            "message": f"Report job submitted for {request.symbol}. You will be notified when it's ready.",
            "estimated_time": "2-5 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting report job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{job_id}")
async def get_report_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a report job"""
    if job_id not in report_jobs:
        raise HTTPException(status_code=404, detail="Report job not found")
    
    job = report_jobs[job_id]
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "symbol": job.symbol,
        "current_price": job.current_price,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "result": job.result,
        "error": job.error
    }

@app.get("/api/reports")
async def list_report_jobs() -> Dict[str, Any]:
    """List all report jobs"""
    jobs = []
    for job_id, job in report_jobs.items():
        jobs.append({
            "job_id": job_id,
            "status": job.status.value,
            "symbol": job.symbol,
            "current_price": job.current_price,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })
    
    return {
        "jobs": jobs,
        "total": len(jobs),
        "pending": len([j for j in jobs if j["status"] == "pending"]),
        "processing": len([j for j in jobs if j["status"] == "processing"]),
        "ready_without_ai": len([j for j in jobs if j["status"] == "ready_without_ai"]),
        "ready_with_ai": len([j for j in jobs if j["status"] == "ready_with_ai"]),
        "failed": len([j for j in jobs if j["status"] == "failed"])
    }

async def process_report_job(job_id: str, symbol: str, current_price: float,
                           include_news: bool, include_technical: bool, include_sentiment: bool,
                           user_email: Optional[str] = None):
    """Process a report job asynchronously with three-state status tracking"""
    try:
        # Update status to processing
        if job_id in report_jobs:
            report_jobs[job_id].status = ReportStatus.PROCESSING
        
        logger.info(f"🔄 Processing report job {job_id} for {symbol}")
        
        # Simulate processing time (2-5 minutes)
        await asyncio.sleep(2)  # For demo, use 2 seconds instead of 2-5 minutes
        
        # Perform initial analysis (market data, technical, news)
        initial_result = await analyzer.analyze_stock(
            symbol=symbol,
            current_price=current_price,
            include_news=include_news,
            include_technical=include_technical,
            include_sentiment=include_sentiment
        )
        
        # Check if AI analysis was successful using the flag from analyze_stock
        ai_analysis_successful = initial_result.get("ai_analysis_successful", False)
        
        # Determine final status based on AI analysis success
        if ai_analysis_successful:
            final_status = ReportStatus.READY_WITH_AI
            logger.info(f"✅ Report job {job_id} completed with AI analysis")
        else:
            final_status = ReportStatus.READY_WITHOUT_AI
            logger.info(f"⚠️ Report job {job_id} completed without AI analysis (timeout/fallback)")
        
        # Update job with result and appropriate status
        if job_id in report_jobs:
            report_jobs[job_id].status = final_status
            report_jobs[job_id].completed_at = datetime.now()
            report_jobs[job_id].result = initial_result
        
        # Send browser notification
        await analyzer.send_browser_notification(job_id, initial_result, user_email)
        
        logger.info(f"✅ Report job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing report job {job_id}: {e}")
        
        # Update job with error
        if job_id in report_jobs:
            report_jobs[job_id].status = ReportStatus.FAILED
            report_jobs[job_id].completed_at = datetime.now()
            report_jobs[job_id].error = str(e)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-stock-dashboard"}

@app.get("/api/symbols")
async def get_popular_symbols():
    """Get list of popular symbols"""
    return {
        "symbols": [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NFLX", "name": "Netflix Inc."},
            {"symbol": "AMD", "name": "Advanced Micro Devices"},
            {"symbol": "INTC", "name": "Intel Corporation"}
        ]
    }

@app.get("/api/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for web push notifications"""
    return {
        "public_key": VAPID_PUBLIC_KEY,
        "status": "success"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 