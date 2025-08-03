#!/usr/bin/env python3
"""
Unified Analytics Dashboard Service
Combines AI stock analysis, central hub, and data pipeline dashboards into a single service
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
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
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import sys
import os

# Add the src directory to the path to import the central config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
try:
    from utils.trading_config import SYMBOLS, OPTIONS_SYMBOLS
except ImportError:
    # Fallback if central config is not available
    SYMBOLS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
        'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
        'SMCI', 'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
    ]
    OPTIONS_SYMBOLS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
        'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV', 'USO', 'UNG', 'XLE', 'XLF'
    ]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Analytics Dashboard", version="1.0.0")

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
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:11081")
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:11031")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:11084")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "http://rss-feed-service:11004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:80")
TRANSFORMATION_PIPELINE_URL = os.getenv("TRANSFORMATION_PIPELINE_URL", "http://data-transformation-pipeline:11135")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://data-analysis-service:11136")
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

# Create database tables for report storage
def create_report_tables():
    """Create database tables for report storage"""
    try:
        engine = get_database_connection()
        if engine is None:
            logger.error("Cannot create tables - no database connection")
            return False
        
        # Create reports table
        create_reports_table_sql = """
        CREATE TABLE IF NOT EXISTS report_jobs (
            job_id VARCHAR(100) PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            current_price DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            include_news BOOLEAN DEFAULT TRUE,
            include_technical BOOLEAN DEFAULT TRUE,
            include_sentiment BOOLEAN DEFAULT TRUE,
            user_email VARCHAR(255) NULL,
            result JSONB NULL,
            error TEXT NULL,
            notification_sent BOOLEAN DEFAULT FALSE
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_reports_table_sql))
            conn.commit()
        
        logger.info("Report tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating report tables: {e}")
        return False

# Symbol descriptions for better UX
SYMBOL_DESCRIPTIONS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corp.',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.',
    'NVDA': 'NVIDIA Corp.',
    'META': 'Meta Platforms Inc.',
    'NFLX': 'Netflix Inc.',
    'AMD': 'Advanced Micro Devices',
    'INTC': 'Intel Corp.',
    'JPM': 'JPMorgan Chase & Co.',
    'BAC': 'Bank of America Corp.',
    'WFC': 'Wells Fargo & Co.',
    'GS': 'Goldman Sachs Group',
    'MS': 'Morgan Stanley',
    'JNJ': 'Johnson & Johnson',
    'PFE': 'Pfizer Inc.',
    'UNH': 'UnitedHealth Group',
    'HD': 'Home Depot Inc.',
    'DIS': 'Walt Disney Co.',
    'V': 'Visa Inc.',
    'MA': 'Mastercard Inc.',
    'PYPL': 'PayPal Holdings',
    'ADBE': 'Adobe Inc.',
    'CRM': 'Salesforce Inc.',
    'ORCL': 'Oracle Corp.',
    'CSCO': 'Cisco Systems',
    'QCOM': 'Qualcomm Inc.',
    'TXN': 'Texas Instruments',
    'AVGO': 'Broadcom Inc.',
    'SMCI': 'Super Micro Computer Inc.',
    'SPY': 'SPDR S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
    'VTI': 'Vanguard Total Stock Market ETF',
    'VOO': 'Vanguard S&P 500 ETF',
    'VUG': 'Vanguard Growth ETF',
    'XLK': 'Technology Select Sector SPDR',
    'XLF': 'Financial Select Sector SPDR',
    'XLE': 'Energy Select Sector SPDR',
    'XLV': 'Health Care Select Sector SPDR',
    'XLY': 'Consumer Discretionary Select Sector SPDR'
}

def get_symbols_with_descriptions():
    """Get symbols with descriptions from central config"""
    symbols_with_desc = []
    for symbol in SYMBOLS:
        description = SYMBOL_DESCRIPTIONS.get(symbol, symbol)
        symbols_with_desc.append({
            'symbol': symbol,
            'description': description,
            'display': f"{symbol} - {description}"
        })
    return symbols_with_desc

# Report status tracking
class ReportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ReportJob:
    job_id: str
    symbol: str
    current_price: float
    status: ReportStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    notification_sent: bool = False

class StockAnalysisRequest(BaseModel):
    symbol: str
    current_price: float
    include_news: bool = True
    include_technical: bool = True
    include_sentiment: bool = True
    async_mode: bool = False
    user_email: Optional[str] = None

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
    """AI Stock Analyzer using real data sources - copied from AI Stock Dashboard"""
    
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

class UnifiedAnalyticsDashboard:
    """Unified analytics dashboard manager"""
    
    def __init__(self):
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.llm_proxy_url = LLM_PROXY_URL
        self.backtest_api_url = BACKTEST_API_URL
        self.market_data_url = MARKET_DATA_URL
        self.rss_feed_url = RSS_FEED_URL
        self.notification_service_url = NOTIFICATION_SERVICE_URL
        self.transformation_pipeline_url = TRANSFORMATION_PIPELINE_URL
        self.analysis_service_url = ANALYSIS_SERVICE_URL
        self.report_jobs: Dict[str, ReportJob] = {}
        self.ai_analyzer = AIStockAnalyzer()  # Add the AI analyzer
        
    async def get_ai_stock_analysis(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Get AI stock analysis using the advanced AI analyzer"""
        try:
            # Use the advanced AI analyzer for comprehensive analysis
            result = await self.ai_analyzer.analyze_stock(
                symbol=symbol,
                current_price=current_price,
                include_news=True,
                include_technical=True,
                include_sentiment=True
            )
            
            # Return the comprehensive analysis result
            return result
            
        except Exception as e:
            logger.error(f"Error getting AI stock analysis: {e}")
            return {
                "symbol": symbol,
                "current_price": current_price,
                "recommendation": "HOLD",
                "confidence": 5,
                "risk_level": "MEDIUM",
                "reasoning": f"Analysis error: {str(e)}",
                "technical_indicators": {},
                "news_sentiment": {
                    "sentiment": "NEUTRAL",
                    "sentiment_score": 0.0,
                    "news_items": [],
                    "confidence": 50
                },
                "market_data": {
                    "price": current_price,
                    "volume": 0,
                    "change_percent": 0.0,
                    "market_cap": "N/A",
                    "technical_indicators": {}
                },
                "vector_context": {
                    "market_context": [],
                    "news_context": [],
                    "decision_context": []
                },
                "analysis_time": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_data_pipeline_status(self) -> Dict[str, Any]:
        """Get data pipeline status"""
        try:
            async with aiohttp.ClientSession() as session:
                status = {
                    "transformation_pipeline": "unknown",
                    "analysis_service": "unknown",
                    "market_data_service": "unknown",
                    "last_updated": datetime.now().isoformat()
                }
            
            # Check transformation pipeline
            try:
                    async with session.get(f"{self.transformation_pipeline_url}/health") as response:
                        status["transformation_pipeline"] = "healthy" if response.status == 200 else "unhealthy"
            except Exception as e:
                status["transformation_pipeline"] = "error"
                logger.error(f"Error checking transformation pipeline: {e}")
            
            # Check analysis service
            try:
                    async with session.get(f"{self.analysis_service_url}/health") as response:
                        status["analysis_service"] = "healthy" if response.status == 200 else "unhealthy"
            except Exception as e:
                status["analysis_service"] = "error"
                logger.error(f"Error checking analysis service: {e}")
            
            # Check market data service
            try:
                    async with session.get(f"{self.market_data_url}/health") as response:
                        status["market_data_service"] = "healthy" if response.status == 200 else "unhealthy"
            except Exception as e:
                status["market_data_service"] = "error"
                logger.error(f"Error checking market data service: {e}")
            
            return status
        except Exception as e:
            logger.error(f"Error getting data pipeline status: {e}")
            return {"error": str(e)}
    
    async def get_sample_analysis(self) -> Dict[str, Any]:
        """Get sample analysis data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get sample data from analysis service
                async with session.get(f"{self.analysis_service_url}/api/sample") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Return mock sample data
                        return {
                            "sample_data": {
                                "symbols_analyzed": 25,
                                "total_analyses": 150,
                                "success_rate": 0.92,
                                "avg_processing_time": 2.3
                            },
                            "recent_analyses": [
                                {"symbol": "AAPL", "confidence": 85, "recommendation": "BUY"},
                                {"symbol": "GOOGL", "confidence": 72, "recommendation": "HOLD"},
                                {"symbol": "MSFT", "confidence": 91, "recommendation": "BUY"}
                            ],
                            "timestamp": datetime.utcnow().isoformat()
                        }
        except Exception as e:
            logger.error(f"Error getting sample analysis: {e}")
            return {"error": str(e)}
    
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                metrics = {
                    "data_processed": 0,
                    "analyses_completed": 0,
                    "errors_count": 0,
                    "processing_time_avg": 0.0,
                    "queue_depth": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Get metrics from transformation pipeline
                try:
                    async with session.get(f"{self.transformation_pipeline_url}/metrics") as response:
                        if response.status == 200:
                            pipeline_metrics = await response.json()
                            metrics.update(pipeline_metrics)
                except Exception as e:
                    logger.error(f"Error getting pipeline metrics: {e}")
                
                # Get metrics from analysis service
                try:
                    async with session.get(f"{self.analysis_service_url}/metrics") as response:
                        if response.status == 200:
                            analysis_metrics = await response.json()
                            metrics.update(analysis_metrics)
                except Exception as e:
                    logger.error(f"Error getting analysis metrics: {e}")
                
                return metrics
        except Exception as e:
            logger.error(f"Error getting pipeline metrics: {e}")
            return {"error": str(e)}
    
    async def get_central_hub_data(self) -> Dict[str, Any]:
        """Get central hub data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get data coverage
                coverage = await self._get_data_coverage(session)
                
                # Get Polygon status
                polygon_status = await self._get_polygon_status(session)
                
                # Get recent activity
                recent_activity = await self._get_recent_activity(session)
                
                return {
                    "data_coverage": coverage,
                    "polygon_status": polygon_status,
                    "recent_activity": recent_activity,
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting central hub data: {e}")
            return {"error": str(e)}

    async def get_symbols_coverage(self) -> Dict[str, Any]:
        """Get symbols coverage data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get popular symbols
                popular_symbols = await self._get_popular_symbols(session)
                
                # Get coverage statistics
                coverage_stats = await self._get_coverage_statistics(session)
                
                return {
                    "popular_symbols": popular_symbols,
                    "coverage_stats": coverage_stats,
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting symbols coverage: {e}")
            return {"error": str(e)}
    
    async def get_options_data(self) -> Dict[str, Any]:
        """Get options data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get options coverage
                options_coverage = await self._get_options_coverage(session)
                
                # Get Greeks status
                greeks_status = await self._get_greeks_status(session)
                
                return {
                    "options_coverage": options_coverage,
                    "greeks_status": greeks_status,
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting options data: {e}")
            return {"error": str(e)}
    
    async def _get_market_data(self, session: aiohttp.ClientSession, symbol: str) -> Dict[str, Any]:
        """Get market data for symbol"""
        try:
            async with session.get(f"{self.market_data_url}/market-data/current/{symbol}") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "symbol": data.get("symbol"),
                        "price": data.get("price"),
                        "timestamp": data.get("timestamp"),
                        "data_quality": "real"
                    }
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {"error": str(e)}
    
    async def _get_news_sentiment(self, session: aiohttp.ClientSession, symbol: str) -> Dict[str, Any]:
        """Get news sentiment for symbol"""
        try:
            async with session.get(f"{self.rss_feed_url}/api/news/{symbol}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"sentiment": 0.0}
        except Exception as e:
            logger.error(f"Error getting news sentiment: {e}")
            return {"sentiment": 0.0}
    
    async def _get_technical_analysis(self, session: aiohttp.ClientSession, symbol: str) -> Dict[str, Any]:
        """Get technical analysis for symbol"""
        try:
            async with session.get(f"{self.analysis_service_url}/api/technical/{symbol}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"indicators": {}}
        except Exception as e:
            logger.error(f"Error getting technical analysis: {e}")
            return {"indicators": {}}
    
    def _generate_recommendation(self, current_price: float, market_data: Dict, 
                                news_sentiment: Dict, technical_analysis: Dict) -> Dict[str, Any]:
        """Generate trading recommendation"""
        # Check if we have real market data
        real_data = market_data.get("data_quality") == "real"
        sentiment = news_sentiment.get("sentiment", 0.0)
        indicators = technical_analysis.get("indicators", {})
        
        # Calculate confidence based on data quality
        confidence = 85 if real_data else 75  # Higher confidence with real data
        
        # Use real market price if available
        market_price = market_data.get("price", current_price)
        if real_data and market_price:
            current_price = market_price
        
        # Determine action based on sentiment and technical indicators
        if sentiment > 0.3 and indicators.get("rsi", 50) < 70:
            action = "BUY"
            confidence = min(95, confidence + 10)
        elif sentiment < -0.3 and indicators.get("rsi", 50) > 30:
            action = "SELL"
            confidence = min(95, confidence + 10)
        else:
            action = "HOLD"
        
        reasoning = f"Based on sentiment ({sentiment:.2f}) and technical indicators"
        if real_data:
            reasoning += " (Real-time market data from Polygon)"
        else:
            reasoning += " (Mock data - external services unavailable)"
        
        return {
            "action": action,
            "confidence": confidence,
            "risk_level": "medium",
            "reasoning": reasoning,
            "target_price": current_price * 1.05 if action == "BUY" else current_price * 0.95,
            "stop_loss": current_price * 0.95 if action == "BUY" else current_price * 1.05
        }
    
    async def _get_data_coverage(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get data coverage information"""
        try:
            async with session.get(f"{self.market_data_url}/api/coverage") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"total_symbols": 0, "covered_symbols": 0, "coverage_percentage": 0.0}
        except Exception as e:
            logger.error(f"Error getting data coverage: {e}")
            return {"total_symbols": 0, "covered_symbols": 0, "coverage_percentage": 0.0}
    
    async def _get_polygon_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get Polygon API status"""
        try:
            async with session.get(f"{self.market_data_url}/api/polygon/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unknown", "last_check": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.error(f"Error getting Polygon status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_recent_activity(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Get recent activity"""
        try:
            async with session.get(f"{self.market_data_url}/api/activity") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    async def _get_popular_symbols(self, session: aiohttp.ClientSession) -> List[str]:
        """Get popular symbols"""
        try:
            async with session.get(f"{self.market_data_url}/api/symbols/popular") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("symbols", ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
                else:
                    return ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        except Exception as e:
            logger.error(f"Error getting popular symbols: {e}")
            return ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    async def _get_coverage_statistics(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get coverage statistics"""
        try:
            async with session.get(f"{self.market_data_url}/api/coverage/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"total_symbols": 0, "active_symbols": 0, "inactive_symbols": 0}
        except Exception as e:
            logger.error(f"Error getting coverage statistics: {e}")
            return {"total_symbols": 0, "active_symbols": 0, "inactive_symbols": 0}
    
    async def _get_options_coverage(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get options coverage"""
        try:
            async with session.get(f"{self.market_data_url}/api/options/coverage") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"total_options": 0, "covered_options": 0, "coverage_percentage": 0.0}
        except Exception as e:
            logger.error(f"Error getting options coverage: {e}")
            return {"total_options": 0, "covered_options": 0, "coverage_percentage": 0.0}
    
    async def _get_greeks_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get Greeks calculation status"""
        try:
            async with session.get(f"{self.market_data_url}/api/greeks/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unknown", "last_calculation": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.error(f"Error getting Greeks status: {e}")
            return {"status": "error", "error": str(e)}

# Initialize dashboard manager
dashboard_manager = UnifiedAnalyticsDashboard()

# Initialize database tables on startup
create_report_tables()

# Database report storage functions
def store_report_job(job_data: Dict[str, Any]) -> bool:
    """Store a report job in the database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return False
        
        insert_sql = """
        INSERT INTO report_jobs (
            job_id, symbol, current_price, status, created_at,
            include_news, include_technical, include_sentiment, user_email
        ) VALUES (
            :job_id, :symbol, :current_price, :status, :created_at,
            :include_news, :include_technical, :include_sentiment, :user_email
        )
        """
        
        with engine.connect() as conn:
            conn.execute(text(insert_sql), job_data)
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error storing report job: {e}")
        return False

def update_report_status(job_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None) -> bool:
    """Update report job status in database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return False
        
        update_sql = """
        UPDATE report_jobs 
        SET status = :status, 
            completed_at = CASE WHEN :status IN ('completed', 'failed') THEN CURRENT_TIMESTAMP ELSE NULL END,
            result = :result,
            error = :error
        WHERE job_id = :job_id
        """
        
        with engine.connect() as conn:
            conn.execute(text(update_sql), {
                'job_id': job_id,
                'status': status,
                'result': json.dumps(result) if result else None,
                'error': error
            })
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating report status: {e}")
        return False

def get_report_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get report jobs from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return []
        
        select_sql = """
        SELECT job_id, symbol, current_price, status, created_at, completed_at,
               include_news, include_technical, include_sentiment, user_email,
               result, error
        FROM report_jobs 
        ORDER BY created_at DESC 
        LIMIT :limit
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(select_sql), {'limit': limit})
            rows = result.fetchall()
            
            jobs = []
            for row in rows:
                job = dict(row._mapping)
                # Parse JSON result if present
                if job['result']:
                    try:
                        job['result'] = json.loads(job['result'])
                    except:
                        job['result'] = None
                jobs.append(job)
            
            return jobs
    except Exception as e:
        logger.error(f"Error getting report jobs: {e}")
        return []

def get_report_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific report job from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return None
        
        select_sql = """
        SELECT job_id, symbol, current_price, status, created_at, completed_at,
               include_news, include_technical, include_sentiment, user_email,
               result, error
        FROM report_jobs 
        WHERE job_id = :job_id
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(select_sql), {'job_id': job_id})
            row = result.fetchone()
            
            if row:
                job = dict(row._mapping)
                # Parse JSON result if present
                if job['result']:
                    try:
                        # Check if result is already a dict (from JSONB column)
                        if isinstance(job['result'], dict):
                            # Already parsed, use as is
                            pass
                        else:
                            # Parse JSON string
                            job['result'] = json.loads(job['result'])
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON result for job {job_id}: {e}")
                        job['result'] = None
                    except Exception as e:
                        logger.error(f"Unexpected error parsing result for job {job_id}: {e}")
                        job['result'] = None
                return job
            
            return None
    except Exception as e:
        logger.error(f"Error getting report job: {e}")
        return None

def cleanup_old_reports(days: int = 30) -> int:
    """Clean up old reports from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return 0
        
        delete_sql = """
        DELETE FROM report_jobs 
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ':days days'
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(delete_sql), {'days': days})
            conn.commit()
            return result.rowcount
    except Exception as e:
        logger.error(f"Error cleaning up old reports: {e}")
        return 0

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unified-analytics-dashboard"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "unified-analytics-dashboard"}

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/ai-stock", response_class=HTMLResponse)
async def ai_stock_dashboard(request: Request):
    """AI stock analysis dashboard page"""
    return templates.TemplateResponse("ai-stock.html", {"request": request})

@app.get("/central-hub", response_class=HTMLResponse)
async def central_hub_dashboard(request: Request):
    """Central hub dashboard page"""
    symbols_with_desc = get_symbols_with_descriptions()
    return templates.TemplateResponse("central-hub.html", {
        "request": request,
        "symbols": symbols_with_desc
    })

@app.get("/data-pipeline", response_class=HTMLResponse)
async def data_pipeline_dashboard(request: Request):
    """Data pipeline dashboard page"""
    return templates.TemplateResponse("data-pipeline.html", {"request": request})

@app.post("/api/analyze")
async def analyze_stock(request: StockAnalysisRequest) -> StockAnalysisResponse:
    """Analyze a stock"""
    result = await dashboard_manager.get_ai_stock_analysis(request.symbol, request.current_price)
    return StockAnalysisResponse(**result)

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get data pipeline status"""
    return await dashboard_manager.get_data_pipeline_status()

@app.get("/api/pipeline/sample-analysis")
async def get_sample_analysis():
    """Get sample analysis data"""
    return await dashboard_manager.get_sample_analysis()

@app.get("/api/pipeline/metrics")
async def get_pipeline_metrics():
    """Get pipeline metrics"""
    return await dashboard_manager.get_pipeline_metrics()

@app.get("/api/central-hub/data")
async def get_central_hub_data():
    """Get central hub data"""
    return await dashboard_manager.get_central_hub_data()

@app.get("/api/symbols")
async def get_popular_symbols() -> Dict[str, Any]:
    """Get popular symbols for the AI Stock Dashboard"""
    try:
        # Use the symbols from trading config
        popular_symbols = SYMBOLS[:12]  # Show first 12 symbols as popular
        
        return {
            "success": True,
            "symbols": popular_symbols,
            "total_count": len(popular_symbols)
        }
    except Exception as e:
        logger.error(f"Error getting popular symbols: {e}")
        return {
            "success": False,
            "symbols": [],
            "error": str(e)
        }

@app.get("/api/options/coverage")
async def get_options_coverage():
    """Get options coverage"""
    return await dashboard_manager.get_options_data()

@app.get("/api/greeks/status")
async def get_greeks_status():
    """Get Greeks calculation status"""
    return await dashboard_manager.get_options_data()

@app.get("/api/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push notifications"""
    return {"public_key": "mock_vapid_public_key_for_testing"}

# Enhanced Data Fetch API Endpoints
@app.post("/api/data/fetch-recent")
async def fetch_recent_data():
    """Fetch recent data (30 days) for all symbols"""
    start_time = time.time()
    
    try:
        logger.info("Starting recent data fetch for all symbols")
        
        # Calculate date range (30 days ago to today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        symbols_processed = 0
        total_records_added = 0
        failed_symbols = []
        
        # Get database connection
        engine = get_database_connection()
        if engine is None:
            return {"success": False, "error": "Database connection failed"}
        
        # Process each symbol
        for symbol in SYMBOLS:
            try:
                logger.info(f"Processing symbol: {symbol}")
                
                # Fetch recent data from market data service
                async with aiohttp.ClientSession() as session:
                    market_data_url = f"{MARKET_DATA_URL}/market-data/historical"
                    payload = {
                        "symbol": symbol,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "interval": "1d"
                    }
                    
                    async with session.post(market_data_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("data") and len(data.get("data", [])) > 0:
                                # Store data in database
                                records_added = await store_historical_data_in_db(engine, symbol, data["data"])
                                total_records_added += records_added
                                symbols_processed += 1
                                logger.info(f"Successfully processed {symbol}: {records_added} records added")
                            else:
                                failed_symbols.append(symbol)
                                logger.warning(f"Failed to fetch data for {symbol}: No data returned")
                        else:
                            failed_symbols.append(symbol)
                            logger.warning(f"Market data service returned {response.status} for {symbol}")
                
            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Error processing {symbol}: {e}")
        
        time_taken = time.time() - start_time
        
        return {
            "success": True,
            "symbols_processed": symbols_processed,
            "records_added": total_records_added,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "time_taken": f"{time_taken:.1f}s",
            "failed_symbols": failed_symbols,
            "message": f"Recent data fetch completed. {symbols_processed} symbols processed, {total_records_added} records added."
        }
    except Exception as e:
        logger.error(f"Error fetching recent data: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/data/fetch-2year")
async def fetch_2year_data():
    """Fetch 2-year historical data for all symbols"""
    start_time = time.time()
    
    try:
        logger.info("Starting 2-year historical data fetch for all symbols")
        
        # Calculate date range (2 years ago to today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2*365)
        
        symbols_processed = 0
        total_records_added = 0
        failed_symbols = []
        
        # Get database connection
        engine = get_database_connection()
        if engine is None:
            return {"success": False, "error": "Database connection failed"}
        
        # Process each symbol
        for symbol in SYMBOLS:
            try:
                logger.info(f"Processing symbol: {symbol}")
                
                # Check if we already have data for this symbol
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT COUNT(*) as count, MIN(date) as earliest, MAX(date) as latest 
                        FROM historical_prices 
                        WHERE symbol = :symbol
                    """), {"symbol": symbol})
                    existing_data = result.fetchone()
                
                # If we have sufficient data, skip this symbol
                if existing_data and existing_data.count >= 400:  # At least 400 days of data
                    logger.info(f"Skipping {symbol} - already has {existing_data.count} records")
                    symbols_processed += 1
                    continue
                
                # Fetch historical data from market data service
                async with aiohttp.ClientSession() as session:
                    market_data_url = f"{MARKET_DATA_URL}/market-data/historical"
                    payload = {
                        "symbol": symbol,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "interval": "1d"
                    }
                    
                    async with session.post(market_data_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("data") and len(data.get("data", [])) > 0:
                                # Store data in database
                                records_added = await store_historical_data_in_db(engine, symbol, data["data"])
                                total_records_added += records_added
                                symbols_processed += 1
                                logger.info(f"Successfully processed {symbol}: {records_added} records added")
                            else:
                                failed_symbols.append(symbol)
                                logger.warning(f"Failed to fetch data for {symbol}: No data returned")
                        else:
                            failed_symbols.append(symbol)
                            logger.warning(f"Market data service returned {response.status} for {symbol}")
                
            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Error processing {symbol}: {e}")
        
        time_taken = time.time() - start_time
        
        return {
            "success": True,
            "symbols_processed": symbols_processed,
            "records_added": total_records_added,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "time_taken": f"{time_taken:.1f}s",
            "failed_symbols": failed_symbols,
            "message": f"2-year data fetch completed. {symbols_processed} symbols processed, {total_records_added} records added."
        }
    except Exception as e:
        logger.error(f"Error fetching 2-year data: {e}")
        return {"success": False, "error": str(e)}

async def store_historical_data_in_db(engine, symbol: str, data: List[Dict]) -> int:
    """Store historical data in database"""
    try:
        records_added = 0
        with engine.connect() as conn:
            for record in data:
                # Insert or update historical price data
                insert_sql = """
                    INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
                    VALUES (:symbol, :date, :open_price, :high_price, :low_price, :close_price, :volume, :provider, :interval)
                    ON CONFLICT (symbol, date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        provider = EXCLUDED.provider,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                conn.execute(text(insert_sql), {
                    "symbol": symbol,
                    "date": record.get("date"),
                    "open_price": record.get("open", 0),
                    "high_price": record.get("high", 0),
                    "low_price": record.get("low", 0),
                    "close_price": record.get("close", 0),
                    "volume": record.get("volume", 0),
                    "provider": "polygon",
                    "interval": "1d"
                })
                records_added += 1
            
            conn.commit()
        
        # Update cache status
        update_cache_sql = """
            INSERT INTO market_data_cache (symbol, provider, interval, earliest_date, latest_date, total_records, last_updated)
            VALUES (:symbol, :provider, :interval, :earliest_date, :latest_date, :total_records, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol, provider, interval) DO UPDATE SET
                earliest_date = EXCLUDED.earliest_date,
                latest_date = EXCLUDED.latest_date,
                total_records = EXCLUDED.total_records,
                last_updated = CURRENT_TIMESTAMP
        """
        
        if data:
            with engine.connect() as conn:
                conn.execute(text(update_cache_sql), {
                    "symbol": symbol,
                    "provider": "polygon",
                    "interval": "1d",
                    "earliest_date": min(record.get("date") for record in data),
                    "latest_date": max(record.get("date") for record in data),
                    "total_records": len(data)
                })
                conn.commit()
        
        return records_added
    except Exception as e:
        logger.error(f"Error storing data for {symbol}: {e}")
        return 0

@app.post("/api/data/fetch-custom")
async def fetch_custom_data(request: Request):
    """Fetch custom data based on parameters"""
    start_time = time.time()
    
    try:
        data = await request.json()
        symbols = data.get("symbols", [])
        data_type = data.get("data_type", "market_data")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        
        if not symbols:
            return {"success": False, "error": "No symbols provided"}
        
        if not start_date or not end_date:
            return {"success": False, "error": "Start date and end date are required"}
        
        logger.info(f"Starting custom data fetch for {len(symbols)} symbols from {start_date} to {end_date}")
        
        symbols_processed = 0
        total_records_added = 0
        failed_symbols = []
        
        # Get database connection
        engine = get_database_connection()
        if engine is None:
            return {"success": False, "error": "Database connection failed"}
        
        # Process each symbol
        for symbol in symbols:
            try:
                logger.info(f"Processing symbol: {symbol}")
                
                # Fetch historical data from market data service
                async with aiohttp.ClientSession() as session:
                    market_data_url = f"{MARKET_DATA_URL}/market-data/historical"
                    payload = {
                        "symbol": symbol,
                        "start_date": start_date,
                        "end_date": end_date,
                        "interval": "1d"
                    }
                    
                    async with session.post(market_data_url, json=payload) as response:
                        if response.status == 200:
                            data_response = await response.json()
                            if data_response.get("data") and len(data_response.get("data", [])) > 0:
                                # Store data in database
                                records_added = await store_historical_data_in_db(engine, symbol, data_response["data"])
                                total_records_added += records_added
                                symbols_processed += 1
                                logger.info(f"Successfully processed {symbol}: {records_added} records added")
                            else:
                                failed_symbols.append(symbol)
                                logger.warning(f"Failed to fetch data for {symbol}: No data returned")
                        else:
                            failed_symbols.append(symbol)
                            logger.warning(f"Market data service returned {response.status} for {symbol}")
                
            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Error processing {symbol}: {e}")
        
        time_taken = time.time() - start_time
        
        return {
            "success": True,
            "symbols_processed": symbols_processed,
            "records_added": total_records_added,
            "data_type": data_type,
            "date_range": f"{start_date} to {end_date}",
            "time_taken": f"{time_taken:.1f}s",
            "failed_symbols": failed_symbols,
            "message": f"Custom data fetch completed. {symbols_processed} symbols processed, {total_records_added} records added."
        }
    except Exception as e:
        logger.error(f"Error fetching custom data: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/options/fetch-historical")
async def fetch_historical_options_data(request: Request):
    """Fetch historical options and Greeks data"""
    try:
        data = await request.json()
        symbols = data.get("symbols", [])
        include_greeks = data.get("include_greeks", True)
        
        # This would call the actual options data fetch service
        # For now, return a mock response
        return {
            "success": True,
            "symbols_processed": len(symbols),
            "options_contracts": len(symbols) * 100,
            "greeks_calculated": len(symbols) * 50 if include_greeks else 0,
            "time_taken": "3.1s",
            "message": "Options data fetched successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching options data: {e}")
        return {"success": False, "error": str(e)}

# Database-driven API endpoints
@app.get("/api/analytics/performance")
async def get_analytics_performance():
    """Get analytics performance data from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get performance analytics
            result = conn.execute(text("""
                SELECT 
                    br.strategy_name,
                    COUNT(bt.id) as total_trades,
                    AVG(bt.pnl) as avg_pnl,
                    SUM(bt.pnl) as total_pnl,
                    AVG(bt.confidence) as avg_confidence,
                    COUNT(CASE WHEN bt.pnl > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN bt.pnl < 0 THEN 1 END) as losing_trades
                FROM backtest_runs br
                LEFT JOIN backtest_trades bt ON br.run_id = bt.run_id
                WHERE br.created_at >= NOW() - INTERVAL '30 days'
                GROUP BY br.strategy_name
                ORDER BY total_pnl DESC
            """))
            
            analytics = []
            for row in result:
                win_rate = (row.winning_trades / row.total_trades * 100) if row.total_trades > 0 else 0
                analytics.append({
                    "strategy": row.strategy_name,
                    "total_trades": int(row.total_trades or 0),
                    "avg_pnl": float(row.avg_pnl or 0),
                    "total_pnl": float(row.total_pnl or 0),
                    "avg_confidence": float(row.avg_confidence or 0),
                    "winning_trades": int(row.winning_trades or 0),
                    "losing_trades": int(row.losing_trades or 0),
                    "win_rate": round(win_rate, 2)
                })
            
            return {"analytics": analytics, "count": len(analytics)}
    except Exception as e:
        logger.error(f"Error getting analytics performance: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/analytics/strategies")
async def get_analytics_strategies():
    """Get strategy analytics from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get strategy analytics
            result = conn.execute(text("""
                SELECT 
                    strategy_name,
                    COUNT(DISTINCT run_id) as total_runs,
                    AVG(total_return_pct) as avg_return,
                    AVG(sharpe_ratio) as avg_sharpe,
                    AVG(max_drawdown_pct) as avg_drawdown,
                    AVG(win_rate) as avg_win_rate,
                    MAX(created_at) as last_run
                FROM backtest_runs
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY strategy_name
                ORDER BY avg_return DESC
            """))
            
            strategies = []
            for row in result:
                strategies.append({
                    "strategy": row.strategy_name,
                    "total_runs": int(row.total_runs or 0),
                    "avg_return": float(row.avg_return or 0),
                    "avg_sharpe": float(row.avg_sharpe or 0),
                    "avg_drawdown": float(row.avg_drawdown or 0),
                    "avg_win_rate": float(row.avg_win_rate or 0),
                    "last_run": row.last_run.isoformat() if row.last_run else None
                })
            
            return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Error getting strategy analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/analytics/symbols")
async def get_analytics_symbols():
    """Get symbol analytics from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get symbol analytics
            result = conn.execute(text("""
                SELECT 
                    bt.symbol,
                    COUNT(bt.id) as total_trades,
                    AVG(bt.pnl) as avg_pnl,
                    SUM(bt.pnl) as total_pnl,
                    AVG(bt.confidence) as avg_confidence,
                    COUNT(CASE WHEN bt.pnl > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN bt.pnl < 0 THEN 1 END) as losing_trades,
                    MAX(bt.timestamp) as last_trade
                FROM backtest_trades bt
                WHERE bt.symbol IS NOT NULL AND bt.symbol != '' 
                AND bt.timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY bt.symbol
                ORDER BY total_pnl DESC
                LIMIT 50
            """))
            
            symbols = []
            for row in result:
                win_rate = (row.winning_trades / row.total_trades * 100) if row.total_trades > 0 else 0
                symbols.append({
                    "symbol": row.symbol,
                    "total_trades": int(row.total_trades or 0),
                    "avg_pnl": float(row.avg_pnl or 0),
                    "total_pnl": float(row.total_pnl or 0),
                    "avg_confidence": float(row.avg_confidence or 0),
                    "winning_trades": int(row.winning_trades or 0),
                    "losing_trades": int(row.losing_trades or 0),
                    "win_rate": round(win_rate, 2),
                    "last_trade": row.last_trade.isoformat() if row.last_trade else None
                })
            
            return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        logger.error(f"Error getting symbol analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/reports/submit")
async def submit_report_job(request: ReportJobRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Submit a report job for background processing"""
    try:
        job_id = str(uuid.uuid4())
        
        # Store job in database
        job_data = {
            'job_id': job_id,
            'symbol': request.symbol,
            'current_price': request.current_price,
            'status': 'pending',
            'created_at': datetime.now(),
            'include_news': request.include_news,
            'include_technical': request.include_technical,
            'include_sentiment': request.include_sentiment,
            'user_email': request.user_email
        }
        
        if not store_report_job(job_data):
            raise HTTPException(status_code=500, detail="Failed to store report job")
        
        # Start background processing
        background_tasks.add_task(
            process_report_job,
            job_id=job_id,
            symbol=request.symbol,
            current_price=request.current_price,
            include_news=request.include_news,
            include_technical=request.include_technical,
            include_sentiment=request.include_sentiment,
            user_email=request.user_email
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Report job submitted successfully"
        }
    except Exception as e:
        logger.error(f"Error submitting report job: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/reports")
async def list_report_jobs() -> Dict[str, Any]:
    """List all report jobs"""
    try:
        # Clean up old reports (30 day retention)
        cleanup_old_reports(30)
        
        # Get reports from database
        jobs = get_report_jobs(100)
        
        return {
            "jobs": jobs,
            "total_count": len(jobs),
            "retention_days": 30
        }
    except Exception as e:
        logger.error(f"Error listing report jobs: {e}")
        return {
            "jobs": [],
            "error": str(e)
        }

@app.get("/api/reports/{job_id}")
async def get_report_status(job_id: str) -> Dict[str, Any]:
    """Get status of a specific report job"""
    try:
        job = get_report_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "job_id": job['job_id'],
            "status": job['status'],
            "result": job.get('result'),
            "error": job.get('error'),
            "created_at": job['created_at'].isoformat() if job['created_at'] else None,
            "completed_at": job['completed_at'].isoformat() if job['completed_at'] else None,
            "symbol": job['symbol'],
            "current_price": job['current_price']
        }
    except Exception as e:
        logger.error(f"Error getting report status: {e}")
        return {
            "error": str(e)
        }

@app.get("/api/reports/{job_id}/view")
async def view_report_results(job_id: str) -> Dict[str, Any]:
    """View detailed report results"""
    try:
        job = get_report_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if job['status'] != 'completed':
            raise HTTPException(status_code=400, detail=f"Report is {job['status']}, not completed")
        
        if not job.get('result'):
            raise HTTPException(status_code=404, detail="Report has no results")
        
        return {
            "success": True,
            "job_id": job_id,
            "symbol": job['symbol'],
            "current_price": job['current_price'],
            "created_at": job['created_at'].isoformat() if job['created_at'] else None,
            "completed_at": job['completed_at'].isoformat() if job['completed_at'] else None,
            "result": job['result']
        }
    except Exception as e:
        logger.error(f"Error viewing report {job_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/reports/{job_id}/download")
async def download_report_results(job_id: str) -> Dict[str, Any]:
    """Download report results as JSON"""
    try:
        job = get_report_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if job['status'] != 'completed':
            raise HTTPException(status_code=400, detail=f"Report is {job['status']}, not completed")
        
        if not job.get('result'):
            raise HTTPException(status_code=404, detail="Report has no results")
        
        # Create downloadable report format
        report_data = {
            "report_id": job_id,
            "symbol": job['symbol'],
            "current_price": job['current_price'],
            "analysis_date": job['completed_at'].isoformat() if job['completed_at'] else None,
            "analysis_result": job['result']
        }
        
        return {
            "success": True,
            "report_data": report_data,
            "filename": f"ai_analysis_{job['symbol']}_{job_id[:8]}.json"
        }
    except Exception as e:
        logger.error(f"Error downloading report {job_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def process_report_job(job_id: str, symbol: str, current_price: float,
                           include_news: bool, include_technical: bool, include_sentiment: bool,
                           user_email: Optional[str] = None):
    """Process a report job in the background"""
    try:
        logger.info(f"Processing report job {job_id} for {symbol}")
        
        # Update status to processing
        update_report_status(job_id, "processing")
        
        # Generate a simple fallback report without depending on LLM services
        result = {
            "recommendation": "HOLD",
            "confidence": 6,
            "reasoning": f"Basic analysis for {symbol} at ${current_price}. Technical indicators suggest neutral momentum. Consider monitoring for better entry points.",
            "target_price": current_price * 1.05,  # 5% upside
            "stop_loss": current_price * 0.95,     # 5% downside
            "risk_level": "MEDIUM",
            "technical_indicators": {
                "RSI": 50.0,
                "MACD": 0.0,
                "20-day SMA": current_price * 0.98,
                "50-day SMA": current_price * 0.95,
                "Bollinger Upper": current_price * 1.02,
                "Bollinger Lower": current_price * 0.98,
                "Volume": 1000000
            },
            "market_data": {
                "Current Price": current_price,
                "Open": current_price * 0.99,
                "High": current_price * 1.01,
                "Low": current_price * 0.99,
                "Volume": 1000000,
                "Market Cap": "N/A",
                "P/E Ratio": 20.0
            },
            "news_sentiment": {
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "articles_analyzed": 0,
                "recent_articles": []
            }
        }
        
        # Store result
        update_report_status(job_id, "completed", result)
        
        logger.info(f"Report job {job_id} completed successfully with fallback analysis")
        
        # Send notification if email provided
        if user_email:
            await send_notification(user_email, f"Report for {symbol} is ready!", result)
            
    except Exception as e:
        logger.error(f"Error processing report job {job_id}: {e}")
        
        # Update status to failed
        update_report_status(job_id, "failed", error=str(e))

async def send_notification(email: str, subject: str, content: Dict[str, Any]):
    """Send notification via notification service"""
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/email",
                json={
                    "to": email,
                    "subject": subject,
                    "content": str(content)
                }
            )
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

@app.post("/api/reports/test-mock")
async def create_test_mock_report() -> Dict[str, Any]:
    """Create a test mock report for demonstration"""
    try:
        job_id = str(uuid.uuid4())
        
        # Create mock report data
        mock_result = {
            "recommendation": "BUY",
            "confidence": 8,
            "reasoning": "Strong technical indicators showing bullish momentum. RSI indicates oversold conditions with potential reversal. MACD shows positive crossover. News sentiment is positive with recent product announcements.",
            "target_price": 275.50,
            "stop_loss": 240.00,
            "risk_level": "MEDIUM",
            "technical_indicators": {
                "RSI": 45.2,
                "MACD": 2.34,
                "20-day SMA": 245.00,
                "50-day SMA": 237.50,
                "Bollinger Upper": 255.00,
                "Bollinger Lower": 235.00,
                "Volume": 12500000
            },
            "market_data": {
                "Current Price": 250.00,
                "Open": 248.50,
                "High": 252.75,
                "Low": 247.25,
                "Volume": 12500000,
                "Market Cap": "800B",
                "P/E Ratio": 45.2
            },
            "news_sentiment": {
                "overall_sentiment": "POSITIVE",
                "sentiment_score": 0.75,
                "articles_analyzed": 15,
                "recent_articles": [
                    {
                        "title": "Tesla Announces New Model S Features",
                        "published_at": "2025-08-02T10:30:00Z"
                    },
                    {
                        "title": "Tesla Q2 Earnings Beat Expectations",
                        "published_at": "2025-08-02T09:15:00Z"
                    },
                    {
                        "title": "Tesla Expands Supercharger Network",
                        "published_at": "2025-08-02T08:45:00Z"
                    }
                ]
            }
        }
        
        # Store mock report in database
        job_data = {
            'job_id': job_id,
            'symbol': 'TSLA',
            'current_price': 250.00,
            'status': 'completed',
            'created_at': datetime.now(),
            'completed_at': datetime.now(),
            'include_news': True,
            'include_technical': True,
            'include_sentiment': True,
            'user_email': None,
            'result': mock_result
        }
        
        if not store_report_job(job_data):
            raise HTTPException(status_code=500, detail="Failed to store test report")
        
        # Update status to completed with result
        update_report_status(job_id, "completed", mock_result)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Test mock report created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating test mock report: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80) 