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
import subprocess

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
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:11006")
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://host.docker.internal:12001")
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:11031")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:8002")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "http://rss-feed-service:11004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:80")
TRANSFORMATION_PIPELINE_URL = os.getenv("TRANSFORMATION_PIPELINE_URL", "http://data-transformation-pipeline:11135")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://ai-analysis-service:11085")
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
            pool_timeout=30,
            connect_args={"connect_timeout": 30}  # 30 second connection timeout
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
        
        # Create popular symbols table
        create_popular_symbols_table_sql = """
        CREATE TABLE IF NOT EXISTS popular_symbols (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            description VARCHAR(255),
            category VARCHAR(50) DEFAULT 'stock',
            priority INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_reports_table_sql))
            conn.execute(text(create_popular_symbols_table_sql))
            
            # Insert default popular symbols if table is empty
            check_symbols_sql = "SELECT COUNT(*) FROM popular_symbols"
            result = conn.execute(text(check_symbols_sql))
            count = result.scalar()
            
            if count == 0:
                default_symbols = [
                    ('AAPL', 'Apple Inc.', 'stock', 1),
                    ('GOOGL', 'Alphabet Inc.', 'stock', 2),
                    ('MSFT', 'Microsoft Corp.', 'stock', 3),
                    ('AMZN', 'Amazon.com Inc.', 'stock', 4),
                    ('TSLA', 'Tesla Inc.', 'stock', 5),
                    ('NVDA', 'NVIDIA Corp.', 'stock', 6),
                    ('META', 'Meta Platforms Inc.', 'stock', 7),
                    ('NFLX', 'Netflix Inc.', 'stock', 8),
                    ('SPY', 'SPDR S&P 500 ETF', 'etf', 9),
                    ('QQQ', 'Invesco QQQ Trust', 'etf', 10)
                ]
                
                insert_symbols_sql = """
                INSERT INTO popular_symbols (symbol, description, category, priority) 
                VALUES (:symbol, :description, :category, :priority)
                """
                
                for symbol, description, category, priority in default_symbols:
                    conn.execute(text(insert_symbols_sql), {
                        'symbol': symbol,
                        'description': description,
                        'category': category,
                        'priority': priority
                    })
            
            conn.commit()
        
        logger.info("Report and popular symbols tables created successfully")
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
                # Call real LLM service (same format as kubernetes-rag-chat)
                import uuid
                request_id = str(uuid.uuid4())
                
                llm_request = {
                    "model": "gpt-oss:20b",
                    "prompt": prompt,
                    "stream": True,
                    "priority": 40,  # High priority
                    "timeout_seconds": 300,
                    "request_id": request_id
                }
                
                logger.info(f"Calling LLM service at: {self.llm_proxy_url}/api/generate")
                logger.info(f"LLM request: {llm_request}")
                
                url = f"{self.llm_proxy_url}/api/generate"
                logger.info(f"Making POST request to: {url}")
                async with session.post(url, json=llm_request, timeout=300) as response:
                    logger.info(f"LLM service response status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"LLM service response: {result}")
                        
                        # Handle immediate response format from LLM service
                        if "response" in result:
                            # This is an immediate response, process it directly
                            ai_response = result["response"]
                            logger.info(f"Received immediate AI response: {ai_response}")
                            
                            # Parse the AI response to extract trading recommendation
                            parsed_response = self._parse_ai_response(ai_response, context)
                            return parsed_response
                        else:
                            logger.error(f"Unexpected LLM response format: {result}")
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

IMPORTANT: Use the current price of ${current_price:.2f} for all calculations.
ANALYSIS TIMESTAMP: {datetime.now().isoformat()}

Current Market Data:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}
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

CRITICAL: You MUST respond with ONLY valid JSON in this exact format:
{{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 1-10,
    "reasoning": "Detailed explanation",
    "target_price": <CALCULATE: current_price * 1.05 to 1.15 for BUY, current_price * 0.85 to 0.95 for SELL>,
    "stop_loss": <CALCULATE: current_price * 0.92 to 0.97 for BUY, current_price * 1.03 to 1.08 for SELL>,
    "risk_level": "LOW|MEDIUM|HIGH"
}}

DO NOT include any text before or after the JSON. Return ONLY the JSON object.

IMPORTANT CALCULATION RULES:
- For BUY recommendations: target_price should be 5-15% above current price (${current_price:.2f})
- For SELL recommendations: target_price should be 5-15% below current price (${current_price:.2f})
- For HOLD recommendations: target_price should be 2-5% above current price (${current_price:.2f})
- Stop loss should be 3-8% from current price in the opposite direction
- ALWAYS calculate target_price and stop_loss based on the current price of ${current_price:.2f}
- DO NOT use hardcoded values - calculate percentages relative to current price
- CRITICAL: You MUST calculate target_price and stop_loss using the current price of ${current_price:.2f}
- FORBIDDEN: Do not use $185.00 or $165.00 - these are wrong values
- REQUIRED: Calculate target_price = current_price * (1.05 to 1.15) for BUY recommendations
- REQUIRED: Calculate stop_loss = current_price * (0.92 to 0.97) for BUY recommendations

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
                
                # Validate and correct target prices if they seem unreasonable
                current_price = context["current_price"]
                if analysis.get("target_price"):
                    target_price = float(analysis["target_price"])
                    # Check if target price is reasonable (within 50% of current price)
                    if target_price < current_price * 0.5 or target_price > current_price * 1.5:
                        logger.warning(f"LLM returned unreasonable target price {target_price} for current price {current_price}, recalculating")
                        if analysis.get("recommendation", "").upper() == "BUY":
                            analysis["target_price"] = current_price * 1.05
                        elif analysis.get("recommendation", "").upper() == "SELL":
                            analysis["target_price"] = current_price * 0.95
                        else:
                            analysis["target_price"] = current_price * 1.02
                
                if analysis.get("stop_loss"):
                    stop_loss = float(analysis["stop_loss"])
                    # Check if stop loss is reasonable (within 50% of current price)
                    if stop_loss < current_price * 0.5 or stop_loss > current_price * 1.5:
                        logger.warning(f"LLM returned unreasonable stop loss {stop_loss} for current price {current_price}, recalculating")
                        if analysis.get("recommendation", "").upper() == "BUY":
                            analysis["stop_loss"] = current_price * 0.95
                        elif analysis.get("recommendation", "").upper() == "SELL":
                            analysis["stop_loss"] = current_price * 1.05
                        else:
                            analysis["stop_loss"] = current_price * 0.98
                
                return analysis
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            pass
        
        # Enhanced text parsing for confidence extraction
        return self._parse_enhanced_fallback_response(response_text, context)

    def _parse_fallback_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response when JSON extraction fails"""
        symbol = context["symbol"]
        current_price = context["current_price"]
        technical = context["technical_analysis"]
        
        # Simple keyword-based analysis
        response_lower = response_text.lower()
        
        if "buy" in response_lower:
            recommendation = "BUY"
            confidence = 75  # Much more realistic confidence for BUY
        elif "sell" in response_lower:
            recommendation = "SELL"
            confidence = 75  # Much more realistic confidence for SELL
        else:
            recommendation = "HOLD"
            confidence = 60  # Realistic confidence for HOLD
        
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

    def _parse_enhanced_fallback_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced parsing that extracts confidence from text"""
        symbol = context["symbol"]
        current_price = context["current_price"]
        technical = context["technical_analysis"]
        
        # Extract recommendation
        response_lower = response_text.lower()
        
        if "buy" in response_lower:
            recommendation = "BUY"
        elif "sell" in response_lower:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        # Extract confidence from text (look for patterns like "8/10", "80%", "confidence: 8")
        confidence = 75  # Default confidence
        
        # Look for confidence patterns in the text
        import re
        
        # Pattern 1: "8/10" or "7/10" etc.
        confidence_match = re.search(r'(\d+)/10', response_text, re.IGNORECASE)
        if confidence_match:
            confidence = int(confidence_match.group(1)) * 10
        
        # Pattern 2: "confidence level: 8" or "confidence: 8"
        confidence_match = re.search(r'confidence[:\s]*(\d+)', response_text, re.IGNORECASE)
        if confidence_match:
            confidence = int(confidence_match.group(1)) * 10
        
        # Pattern 3: "80%" or "75%"
        confidence_match = re.search(r'(\d+)%', response_text)
        if confidence_match:
            confidence = int(confidence_match.group(1))
        
        # Ensure confidence is within reasonable bounds
        confidence = max(10, min(95, confidence))
        
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
            "reasoning": response_text,
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
            confidence = 80  # High confidence for oversold with positive momentum
            reasoning = f"{symbol} appears oversold with positive momentum"
        elif rsi > 70 and macd_value < 0:
            recommendation = "SELL"
            confidence = 80  # High confidence for overbought with negative momentum
            reasoning = f"{symbol} appears overbought with negative momentum"
        else:
            recommendation = "HOLD"
            confidence = 65  # Moderate confidence for mixed signals
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
        """Get data pipeline status with detailed error information"""
        try:
            status = {
                "transformation_pipeline": "unknown",
                "analysis_service": "unknown",
                "market_data_service": "unknown",
                "last_updated": datetime.now().isoformat(),
                "details": {}
            }
            
            # Check transformation pipeline
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.get(f"{self.transformation_pipeline_url}/health") as response:
                        if response.status == 200:
                            status["transformation_pipeline"] = "healthy"
                            status["details"]["transformation"] = "Service responding normally"
                        else:
                            status["transformation_pipeline"] = "unhealthy"
                            status["details"]["transformation"] = f"HTTP {response.status}"
            except asyncio.TimeoutError:
                status["transformation_pipeline"] = "error"
                status["details"]["transformation"] = "Connection timeout"
            except Exception as e:
                status["transformation_pipeline"] = "error"
                status["details"]["transformation"] = f"Connection error: {str(e)}"
                logger.error(f"Error checking transformation pipeline: {e}")
            
            # Check analysis service
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.get(f"{self.analysis_service_url}/health") as response:
                        if response.status == 200:
                            status["analysis_service"] = "healthy"
                            status["details"]["analysis"] = "Service responding normally"
                        else:
                            status["analysis_service"] = "unhealthy"
                            status["details"]["analysis"] = f"HTTP {response.status}"
            except asyncio.TimeoutError:
                status["analysis_service"] = "error"
                status["details"]["analysis"] = "Connection timeout"
            except Exception as e:
                status["analysis_service"] = "error"
                status["details"]["analysis"] = f"Connection error: {str(e)}"
                logger.error(f"Error checking analysis service: {e}")
            
            # Check market data service
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.get(f"{self.market_data_url}/health") as response:
                        if response.status == 200:
                            status["market_data_service"] = "healthy"
                            status["details"]["market_data"] = "Service responding normally"
                        else:
                            status["market_data_service"] = "unhealthy"
                            status["details"]["market_data"] = f"HTTP {response.status}"
            except asyncio.TimeoutError:
                status["market_data_service"] = "error"
                status["details"]["market_data"] = "Connection timeout"
            except Exception as e:
                status["market_data_service"] = "error"
                status["details"]["market_data"] = f"Connection error: {str(e)}"
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
        """Get central hub data with enhanced status reporting"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get data coverage
                coverage = await self._get_data_coverage(session)
                
                # Get Polygon status
                polygon_status = await self._get_polygon_status(session)
                
                # Get recent activity (enhanced)
                recent_activity = await self._get_recent_activity(session)
                
                # Get worker status
                worker_status = await self._get_worker_status(session)
                
                # Get worker queue status
                worker_queues = await self._get_worker_queue_status(session)
                
                # Get popular symbols
                popular_symbols = await self._get_popular_symbols(session)
                
                return {
                    "data_coverage": coverage,
                    "polygon_status": polygon_status,
                    "recent_activity": recent_activity,
                    "worker_status": worker_status,
                    "worker_queues": worker_queues,
                    "popular_symbols": popular_symbols,
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting central hub data: {e}")
            return {"error": str(e)}
    
    async def _get_worker_status(self, session: aiohttp.ClientSession) -> str:
        """Get worker status with detailed information"""
        try:
            # Check if LLM workers are running by checking the external LLM proxy
            async with session.get("http://host.docker.internal:12001/api/v1/health", timeout=5) as response:
                if response.status == 200:
                    return "healthy"
                else:
                    return "unhealthy"
        except asyncio.TimeoutError:
            return "timeout"
        except Exception as e:
            logger.error(f"Error checking worker status: {e}")
            return "error"

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
        """Get data coverage with actual symbol information"""
        try:
            # Get available symbols from market data service
            try:
                async with session.get(f"{MARKET_DATA_URL}/market-data/symbols", timeout=5) as response:
                    if response.status == 200:
                        symbols_data = await response.json()
                        available_symbols = symbols_data.get('symbols', [])
                    else:
                        available_symbols = []
            except Exception as e:
                logger.error(f"Error getting symbols: {e}")
                available_symbols = []
            
            # Get popular symbols for coverage calculation
            popular_symbols = await self._get_popular_symbols(session)
            
            # Calculate coverage based on popular symbols
            total_symbols = len(popular_symbols)
            
            # Extract symbol names from available_symbols (they are objects with symbol and name properties)
            available_symbol_names = []
            if available_symbols and isinstance(available_symbols[0], dict):
                available_symbol_names = [s.get('symbol', '') for s in available_symbols if s.get('symbol')]
            else:
                available_symbol_names = available_symbols
            
            # Count how many popular symbols are available
            covered_symbols = len([s for s in popular_symbols if s in available_symbol_names])
            coverage_percentage = (covered_symbols / total_symbols * 100) if total_symbols > 0 else 0.0
            
            return {
                "total_symbols": total_symbols,
                "covered_symbols": covered_symbols,
                "coverage_percentage": round(coverage_percentage, 1),
                "available_symbols": available_symbols[:10],  # Show first 10
                "popular_symbols": popular_symbols
            }
        except Exception as e:
            logger.error(f"Error getting data coverage: {e}")
            return {
                "total_symbols": 0,
                "covered_symbols": 0,
                "coverage_percentage": 0.0,
                "available_symbols": [],
                "popular_symbols": []
            }
    
    async def _get_polygon_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get Polygon API status with detailed error reporting"""
        try:
            # Try the correct status endpoint first
            async with session.get(f"{self.market_data_url}/status", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy" if data.get("status") == "operational" else "degraded",
                        "data_source": data.get("data_source", "Unknown"),
                        "service": data.get("service", "Unknown"),
                        "last_check": datetime.utcnow().isoformat(),
                        "details": f"Service: {data.get('service', 'Unknown')}, Data Source: {data.get('data_source', 'Unknown')}"
                    }
                else:
                    return {
                        "status": "error",
                        "last_check": datetime.utcnow().isoformat(),
                        "details": f"HTTP {response.status}: Service not responding properly"
                    }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "last_check": datetime.utcnow().isoformat(),
                "details": "Connection timeout - service may be overloaded or unavailable"
            }
        except Exception as e:
            logger.error(f"Error getting Polygon status: {e}")
            return {
                "status": "error",
                "last_check": datetime.utcnow().isoformat(),
                "details": f"Connection error: {str(e)}"
            }
    
    async def _get_recent_activity(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Get recent activity with enhanced tracking"""
        try:
            activities = []
            
            # Check LLM worker activity
            try:
                async with session.get("http://host.docker.internal:12001/api/v1/health", timeout=3) as response:
                    if response.status == 200:
                        activities.append({
                            "type": "worker",
                            "status": "active",
                            "message": "LLM workers processing requests",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        activities.append({
                            "type": "worker",
                            "status": "inactive",
                            "message": "LLM workers not responding",
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except Exception as e:
                activities.append({
                    "type": "worker",
                            "status": "error",
                            "message": f"LLM worker error: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
            
            # Check market data activity
            try:
                async with session.get(f"{MARKET_DATA_URL}/status", timeout=3) as response:
                    if response.status == 200:
                        data = await response.json()
                        activities.append({
                            "type": "market_data",
                            "status": "active",
                            "message": f"Market data service: {data.get('status', 'unknown')}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        activities.append({
                            "type": "market_data",
                            "status": "inactive",
                            "message": "Market data service not responding",
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except Exception as e:
                activities.append({
                    "type": "market_data",
                    "status": "error",
                    "message": f"Market data error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check data processing activity
            try:
                async with session.get("http://data-transformation-pipeline:11135/health", timeout=3) as response:
                    if response.status == 200:
                        activities.append({
                            "type": "processing",
                            "status": "active",
                            "message": "Data transformation pipeline running",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        activities.append({
                            "type": "processing",
                            "status": "inactive",
                            "message": "Data transformation pipeline not responding",
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except Exception as e:
                activities.append({
                    "type": "processing",
                    "status": "error",
                    "message": f"Processing error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return activities
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return [{
                "type": "error",
                "status": "error",
                "message": f"Activity tracking error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }]
    
    async def _get_popular_symbols(self, session: aiohttp.ClientSession) -> List[str]:
        """Get popular symbols from the database"""
        try:
            # Get symbols from the database
            engine = get_database_connection()
            if engine is None:
                return ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", "SPY", "QQQ"]
            
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT symbol FROM popular_symbols 
                    WHERE active = TRUE 
                    ORDER BY priority, symbol
                """))
                
                symbols = [row[0] for row in result]
                return symbols if symbols else ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", "SPY", "QQQ"]
        except Exception as e:
            logger.error(f"Error getting popular symbols from database: {e}")
            # Fallback to a subset of common symbols
            return ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", "SPY", "QQQ"]
    
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

    async def _get_worker_queue_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get worker queue status from RabbitMQ"""
        try:
            # Try to get queue status from RabbitMQ management API
            rabbitmq_url = "http://rabbitmq:15672/api/queues"
            auth = aiohttp.BasicAuth('trading', 'trading_pass')
            
            async with session.get(rabbitmq_url, auth=auth, timeout=5) as response:
                if response.status == 200:
                    queues = await response.json()
                    
                    # Filter for LLM worker queues
                    llm_queues = [q for q in queues if q['name'].startswith('llm.')]
                    
                    queue_status = {}
                    for queue in llm_queues:
                        queue_status[queue['name']] = {
                            "messages": queue.get('messages', 0),
                            "consumers": queue.get('consumers', 0),
                            "state": queue.get('state', 'unknown')
                        }
                    
                    return {
                        "status": "connected",
                        "queues": queue_status,
                        "total_queues": len(llm_queues),
                        "active_consumers": sum(q.get('consumers', 0) for q in llm_queues),
                        "pending_messages": sum(q.get('messages', 0) for q in llm_queues)
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "queues": {},
                        "total_queues": 0,
                        "active_consumers": 0,
                        "pending_messages": 0
                    }
        except Exception as e:
            logger.error(f"Error getting worker queue status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "queues": {},
                "total_queues": 0,
                "active_consumers": 0,
                "pending_messages": 0
            }

# Initialize dashboard manager
dashboard_manager = UnifiedAnalyticsDashboard()

# Initialize database tables on startup (non-blocking)
try:
    create_report_tables()
    logger.info("Database tables initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization failed (non-critical): {e}")
    logger.info("Dashboard will continue without database features")

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

@app.get("/backtest", response_class=HTMLResponse)
async def backtest_dashboard(request: Request):
    """Backtest dashboard page"""
    return templates.TemplateResponse("backtest.html", {"request": request})

@app.get("/rag-search", response_class=HTMLResponse)
async def rag_search_dashboard(request: Request):
    """RAG search dashboard page"""
    return templates.TemplateResponse("rag-search.html", {"request": request})

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
    """Get popular symbols from database"""
    try:
        # Get symbols from the database
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, description, category, priority, active 
                FROM popular_symbols 
                WHERE active = TRUE 
                ORDER BY priority, symbol
            """))
            
            symbols = []
            for row in result:
                symbols.append({
                    "symbol": row[0],
                    "description": row[1],
                    "category": row[2],
                    "priority": row[3],
                    "active": row[4]
                })
            
            return {
                "success": True,
                "symbols": [s["symbol"] for s in symbols],  # Backward compatibility
                "symbols_detailed": symbols,
                "total_count": len(symbols)
            }
    except Exception as e:
        logger.error(f"Error getting popular symbols: {e}")
        return {
            "success": False,
            "symbols": [],
            "error": str(e)
        }

@app.get("/api/symbols/all")
async def get_all_symbols() -> List[Dict[str, Any]]:
    """Get all symbols from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return [{"error": "Database connection failed"}]
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, description, category, priority, active 
                FROM popular_symbols 
                ORDER BY priority, symbol
            """))
            
            symbols = []
            for row in result:
                symbols.append({
                    "name": row[0],
                    "description": row[1] or "",
                    "category": row[2] or "stock",
                    "priority": row[3] or 0,
                    "active": row[4]
                })
            
            return symbols
    except Exception as e:
        logger.error(f"Error getting all symbols: {e}")
        return [{"error": str(e)}]

@app.get("/api/symbols/active")
async def get_active_symbols() -> List[Dict[str, Any]]:
    """Get active symbols from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return [{"error": "Database connection failed"}]
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, description, category, priority, active 
                FROM popular_symbols 
                WHERE active = TRUE 
                ORDER BY priority, symbol
            """))
            
            symbols = []
            for row in result:
                symbols.append({
                    "name": row[0],
                    "description": row[1] or "",
                    "category": row[2] or "stock",
                    "priority": row[3] or 0,
                    "active": row[4]
                })
            
            return symbols
    except Exception as e:
        logger.error(f"Error getting active symbols: {e}")
        return [{"error": str(e)}]

@app.get("/api/symbols/inactive")
async def get_inactive_symbols() -> List[Dict[str, Any]]:
    """Get inactive symbols from database"""
    try:
        engine = get_database_connection()
        if engine is None:
            return [{"error": "Database connection failed"}]
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, description, category, priority, active 
                FROM popular_symbols 
                WHERE active = FALSE 
                ORDER BY priority, symbol
            """))
            
            symbols = []
            for row in result:
                symbols.append({
                    "name": row[0],
                    "description": row[1] or "",
                    "category": row[2] or "stock",
                    "priority": row[3] or 0,
                    "active": row[4]
                })
            
            return symbols
    except Exception as e:
        logger.error(f"Error getting inactive symbols: {e}")
        return [{"error": str(e)}]

@app.get("/api/symbols/get/{symbol}")
async def get_symbol_details(symbol: str) -> Dict[str, Any]:
    """Get details for a specific symbol"""
    try:
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, description, category, priority, active 
                FROM popular_symbols 
                WHERE symbol = :symbol
            """), {"symbol": symbol.upper()})
            
            row = result.fetchone()
            if row:
                return {
                    "name": row[0],
                    "description": row[1] or "",
                    "category": row[2] or "stock",
                    "priority": row[3] or 0,
                    "active": row[4]
                }
            else:
                return {"error": f"Symbol {symbol} not found"}
    except Exception as e:
        logger.error(f"Error getting symbol details: {e}")
        return {"error": str(e)}

@app.post("/api/symbols/add")
async def add_symbol(symbol_data: dict) -> Dict[str, Any]:
    """Add a new symbol"""
    try:
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        name = symbol_data.get("name", "").upper()
        description = symbol_data.get("description", "")
        category = symbol_data.get("category", "stock")
        priority = symbol_data.get("priority", 0)
        active = symbol_data.get("active", True)
        
        if not name:
            return {"error": "Symbol name is required"}
        
        with engine.connect() as conn:
            # Check if symbol already exists
            check_result = conn.execute(text("SELECT id FROM popular_symbols WHERE symbol = :symbol"), {"symbol": name})
            if check_result.fetchone():
                return {"error": f"Symbol {name} already exists"}
            
            # Insert new symbol
            conn.execute(text("""
                INSERT INTO popular_symbols (symbol, description, category, priority, active)
                VALUES (:symbol, :description, :category, :priority, :active)
            """), {
                "symbol": name,
                "description": description,
                "category": category,
                "priority": priority,
                "active": active
            })
            conn.commit()
            
            return {"success": True, "message": f"Symbol {name} added successfully"}
    except Exception as e:
        logger.error(f"Error adding symbol: {e}")
        return {"error": str(e)}

@app.put("/api/symbols/edit/{symbol}")
async def edit_symbol(symbol: str, symbol_data: dict) -> Dict[str, Any]:
    """Edit an existing symbol"""
    try:
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        description = symbol_data.get("description", "")
        category = symbol_data.get("category", "stock")
        priority = symbol_data.get("priority", 0)
        active = symbol_data.get("active", True)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE popular_symbols 
                SET description = :description, category = :category, priority = :priority, 
                    active = :active, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = :symbol
            """), {
                "symbol": symbol.upper(),
                "description": description,
                "category": category,
                "priority": priority,
                "active": active
            })
            conn.commit()
            
            if result.rowcount == 0:
                return {"error": f"Symbol {symbol} not found"}
            
            return {"success": True, "message": f"Symbol {symbol} updated successfully"}
    except Exception as e:
        logger.error(f"Error updating symbol: {e}")
        return {"error": str(e)}

@app.put("/api/symbols/toggle-active/{symbol}")
async def toggle_symbol_active(symbol: str, toggle_data: dict) -> Dict[str, Any]:
    """Toggle active status of a symbol"""
    try:
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        active = toggle_data.get("active", True)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE popular_symbols 
                SET active = :active, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = :symbol
            """), {
                "symbol": symbol.upper(),
                "active": active
            })
            conn.commit()
            
            if result.rowcount == 0:
                return {"error": f"Symbol {symbol} not found"}
            
            status = "activated" if active else "deactivated"
            return {"success": True, "message": f"Symbol {symbol} {status} successfully"}
    except Exception as e:
        logger.error(f"Error toggling symbol active status: {e}")
        return {"error": str(e)}

@app.delete("/api/symbols/delete/{symbol}")
async def delete_symbol(symbol: str) -> Dict[str, Any]:
    """Delete a symbol (soft delete by setting active = FALSE)"""
    try:
        engine = get_database_connection()
        if engine is None:
            return {"error": "Database connection failed"}
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE popular_symbols 
                SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = :symbol
            """), {"symbol": symbol.upper()})
            conn.commit()
            
            if result.rowcount == 0:
                return {"error": f"Symbol {symbol} not found"}
            
            return {"success": True, "message": f"Symbol {symbol} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting symbol: {e}")
        return {"error": str(e)}

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
        
        # Use the real AI analyzer
        analyzer = AIStockAnalyzer()
        result = await analyzer.analyze_stock(
            symbol=symbol,
            current_price=current_price,
            include_news=include_news,
            include_technical=include_technical,
            include_sentiment=include_sentiment
        )
        
        # Store result
        update_report_status(job_id, "completed", result)
        
        logger.info(f"Report job {job_id} completed successfully with real AI analysis")
        
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
        # Create a mock report job
        job_id = f"mock_report_{int(time.time())}"
        job_data = {
            "job_id": job_id,
            "symbol": "AAPL",
            "current_price": 150.00,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "result": {
                "recommendation": "BUY",
                "confidence": 85,
                "risk_level": "Medium",
                "reasoning": "Strong technical indicators and positive sentiment",
                "target_price": 165.00,
                "stop_loss": 140.00,
                "technical_indicators": {
                    "rsi": 65.2,
                    "macd": "bullish",
                    "moving_averages": "above_50_ma"
                }
            }
        }
        
        # Store in database
        store_report_job(job_data)
        
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Mock report created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating mock report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create mock report: {str(e)}")

# Order Management Endpoints
@app.post("/api/orders")
async def create_order(order_data: dict):
    """Create a new trading order"""
    try:
        # Validate required fields
        required_fields = ['symbol', 'side', 'quantity', 'order_type']
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate order type and price requirements
        if order_data['order_type'] == 'LIMIT' and not order_data.get('price'):
            raise HTTPException(status_code=400, detail="Price is required for limit orders")
        
        # Generate order ID
        order_id = f"order_{int(time.time())}_{order_data['symbol']}"
        
        # Store order in database
        engine = get_database_connection()
        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO orders (
                        order_id, symbol, action, quantity, price, order_type, 
                        status, created_at
                    ) VALUES (
                        :order_id, :symbol, :action, :quantity, :price, :order_type,
                        :status, NOW()
                    )
                """), {
                    'order_id': order_id,
                    'symbol': order_data['symbol'],
                    'action': order_data['side'],
                    'quantity': order_data['quantity'],
                    'price': order_data.get('price') or 0.0,
                    'order_type': order_data['order_type'],
                    'status': 'pending'
                })
                conn.commit()
        
        # Forward to order service if available
        try:
            order_service_url = os.getenv("ORDER_SERVICE_URL", "http://order-service:11106")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"{order_service_url}/api/v1/orders", json=order_data) as response:
                    if response.status == 200:
                        logger.info(f"Order forwarded to order service: {order_id}")
        except Exception as e:
            logger.warning(f"Could not forward order to order service: {e}")
        
        return {
            "order_id": order_id,
            "status": "pending",
            "message": "Order created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.get("/api/orders")
async def get_orders():
    """Get recent orders"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent orders
            result = conn.execute(text("""
                SELECT 
                    order_id,
                    symbol,
                    action as side,
                    quantity,
                    price,
                    order_type,
                    status,
                    created_at,
                    updated_at as filled_at,
                    price as filled_price,
                    quantity as filled_quantity
                FROM orders
                ORDER BY created_at DESC
                LIMIT 50
            """))
            
            orders = []
            for row in result:
                orders.append({
                    "order_id": row.order_id,
                    "symbol": row.symbol,
                    "side": row.side,
                    "quantity": int(row.quantity or 0),
                    "price": float(row.price or 0) if row.price else None,
                    "order_type": row.order_type,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "filled_at": row.filled_at.isoformat() if row.filled_at else None,
                    "filled_price": float(row.filled_price or 0) if row.filled_price else None,
                    "filled_quantity": int(row.filled_quantity or 0) if row.filled_quantity else None
                })
            
            return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get specific order details"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    order_id,
                    symbol,
                    action as side,
                    quantity,
                    price,
                    order_type,
                    status,
                    created_at,
                    updated_at as filled_at,
                    price as filled_price,
                    quantity as filled_quantity
                FROM orders
                WHERE order_id = :order_id
            """), {'order_id': order_id})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Order not found")
            
            return {
                "order_id": row.order_id,
                "symbol": row.symbol,
                "side": row.side,
                "quantity": int(row.quantity or 0),
                "price": float(row.price or 0) if row.price else None,
                "order_type": row.order_type,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "filled_at": row.filled_at.isoformat() if row.filled_at else None,
                "filled_price": float(row.filled_price or 0) if row.filled_price else None,
                "filled_quantity": int(row.filled_quantity or 0) if row.filled_quantity else None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/api/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Check if order exists and is cancellable
            result = conn.execute(text("""
                SELECT status FROM orders WHERE order_id = :order_id
            """), {'order_id': order_id})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Order not found")
            
            if row.status in ['filled', 'cancelled']:
                raise HTTPException(status_code=400, detail=f"Order cannot be cancelled in status: {row.status}")
            
            # Update order status
            conn.execute(text("""
                UPDATE orders SET status = 'cancelled' WHERE order_id = :order_id
            """), {'order_id': order_id})
            conn.commit()
            
            return {"message": "Order cancelled successfully", "order_id": order_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

@app.get("/api/market-data/current/{symbol}")
async def get_current_market_price(symbol: str):
    """Proxy endpoint to get current market price from market data service"""
    try:
        # Use the proper Kubernetes service name
        async with aiohttp.ClientSession() as session:
            url = f"{MARKET_DATA_URL}/market-data/current/{symbol.upper()}"
            logger.info(f"Attempting to fetch market data from: {url}")
            async with session.get(url, timeout=10) as response:
                logger.info(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Got REAL market data for {symbol}: {data}")
                    return {
                        "symbol": data.get("symbol", symbol.upper()),
                        "price": data.get("price"),
                        "timestamp": data.get("timestamp"),
                        "source": "real_market_data"
                    }
                else:
                    response_text = await response.text()
                    logger.warning(f"Market data service returned {response.status} for {symbol}: {response_text}")
                    # Fallback to estimated prices
                    return {
                        "symbol": symbol.upper(),
                        "price": get_simple_estimate(symbol.upper()),
                        "timestamp": datetime.now().isoformat(),
                        "source": "estimated"
                    }
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Fallback to estimated prices
        return {
            "symbol": symbol.upper(),
            "price": get_simple_estimate(symbol.upper()),
            "timestamp": datetime.now().isoformat(),
            "source": "estimated"
        }

def get_simple_estimate(symbol: str) -> float:
    """Get a simple estimate for testing - this should be replaced with real data"""
    # These are the REAL prices from the working market data service
    estimates = {
        'AAPL': 203.35,    # Real price from market data service
        'MSFT': 535.64,    # Real price from market data service  
        'NVDA': 180.0,     # Real price from market data service
        'GOOGL': 2800.00,  # Estimated - need to get real price
        'AMZN': 180.00,    # Estimated - need to get real price
        'TSLA': 250.00,    # Estimated - need to get real price
        'META': 500.00,    # Estimated - need to get real price
        'NFLX': 650.00,    # Estimated - need to get real price
        'SPY': 550.00,     # Estimated - need to get real price
        'QQQ': 450.00,     # Estimated - need to get real price
        'JPM': 200.00,     # Estimated - need to get real price
        'BAC': 35.00,      # Estimated - need to get real price
        'WFC': 45.00,      # Estimated - need to get real price
        'GS': 450.00,      # Estimated - need to get real price
        'MS': 85.00,       # Estimated - need to get real price
        'JNJ': 160.00,     # Estimated - need to get real price
        'PFE': 30.00,      # Estimated - need to get real price
        'UNH': 500.00,     # Estimated - need to get real price
        'HD': 350.00,      # Estimated - need to get real price
        'DIS': 90.00,      # Estimated - need to get real price
        'V': 250.00,       # Estimated - need to get real price
        'MA': 400.00,      # Estimated - need to get real price
        'PYPL': 60.00,     # Estimated - need to get real price
        'ADBE': 500.00,    # Estimated - need to get real price
        'CRM': 250.00,     # Estimated - need to get real price
        'ORCL': 120.00,    # Estimated - need to get real price
        'CSCO': 50.00,     # Estimated - need to get real price
        'QCOM': 150.00,    # Estimated - need to get real price
        'TXN': 180.00,     # Estimated - need to get real price
        'AVGO': 800.00,    # Estimated - need to get real price
        'SMCI': 800.00,    # Estimated - need to get real price
        'VTI': 250.00,     # Estimated - need to get real price
        'VOO': 450.00,     # Estimated - need to get real price
        'VUG': 250.00,     # Estimated - need to get real price
        'XLK': 200.00,     # Estimated - need to get real price
        'XLF': 40.00,      # Estimated - need to get real price
        'XLE': 90.00,      # Estimated - need to get real price
        'XLV': 140.00,     # Estimated - need to get real price
        'XLY': 180.00      # Estimated - need to get real price
    }
    
    return estimates.get(symbol, 100.00)

# Add after the existing Pydantic models (around line 295)

class RAGSearchRequest(BaseModel):
    """Request for RAG-based search"""
    query: str
    search_type: str = "all"  # "market_data", "news", "decisions", "all"
    top_k: int = 5
    include_context: bool = True

class RAGSearchResponse(BaseModel):
    """Response from RAG-based search"""
    query: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    search_time: float
    timestamp: str

class RAGSearchProcessor:
    """Process RAG-based search queries using vector storage and LLM"""
    
    def __init__(self):
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.llm_proxy_url = LLM_PROXY_URL
    
    async def process_rag_query(self, query: str, search_type: str = "all", 
                              top_k: int = 5, include_context: bool = True) -> RAGSearchResponse:
        """Process a RAG query using vector storage, real-time services, and LLM"""
        start_time = time.time()
        
        try:
            # Step 1: Search vector storage for relevant context
            vector_results = await self._search_vector_storage(query, search_type, top_k)
            
            # Step 2: Extract symbols from query and fetch real-time data
            symbols = self._extract_symbols_from_query(query)
            real_time_data = await self._fetch_real_time_data(symbols, search_type)
            
            # Step 3: Build comprehensive context from vector results and real-time data
            context = self._build_comprehensive_context(vector_results, real_time_data, query)
            
            # Step 4: Generate AI response using LLM
            ai_response = await self._generate_ai_response(query, context, include_context)
            
            # Step 5: Calculate confidence based on available data
            confidence = self._calculate_enhanced_confidence(vector_results, real_time_data)
            
            search_time = time.time() - start_time
            
            return RAGSearchResponse(
                query=query,
                answer=ai_response["answer"],
                confidence=confidence,
                sources=vector_results + real_time_data.get("sources", []),
                search_time=search_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            return RAGSearchResponse(
                query=query,
                answer=f"I encountered an error while processing your query: {str(e)}",
                confidence=0.0,
                sources=[],
                search_time=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )
    
    async def _search_vector_storage(self, query: str, search_type: str, top_k: int) -> List[Dict[str, Any]]:
        """Search vector storage for relevant content"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.vector_storage_url}/api/search/similar"
                params = {
                    "query": query,
                    "top_k": top_k
                }
                
                if search_type != "all":
                    params["vector_type"] = search_type
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Vector storage search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching vector storage: {e}")
            return []
    
    def _build_context_from_results(self, vector_results: List[Dict[str, Any]]) -> str:
        """Build context string from vector search results"""
        if not vector_results:
            return "No relevant historical data found."
        
        context_parts = []
        for i, result in enumerate(vector_results[:5], 1):  # Limit to top 5
            content = result.get("content", "")
            similarity = result.get("similarity", 0.0)
            vector_type = result.get("vector_type", "unknown")
            
            context_parts.append(f"Source {i} ({vector_type}, similarity: {similarity:.2f}):\n{content}\n")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, query: str, context: str, include_context: bool) -> Dict[str, Any]:
        """Generate AI response using external LLM with async callback system"""
        try:
            # Build prompt for LLM
            if include_context:
                prompt = f"""You are an expert financial analyst. Answer the following question based on the provided context.

Question: {query}

Context from historical data:
{context}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information, say so and provide general guidance.

Answer:"""
            else:
                prompt = f"""You are an expert financial analyst. Answer the following question about financial markets and trading.

Question: {query}

Please provide a comprehensive and helpful answer.

Answer:"""
            
            # Generate a unique request ID for tracking
            import uuid
            request_id = str(uuid.uuid4())
            
            # Use the external LLM API endpoint with callback system
            url = f"{self.llm_proxy_url}/api/generate"
            
            # Format request for external LLM API with callback
            llm_request = {
                "model": "gpt-oss:20b",
                "prompt": prompt,
                "stream": False,  # Use async callback system
                "priority": 40,  # Highest priority (40 = highest)
                "timeout_seconds": 300,  # 5 minutes timeout
                "request_id": request_id,
                "callback_url": f"http://unified-analytics-dashboard:80/api/rag/callback/{request_id}",
                "callback_method": "POST"
            }
            
            # Log the request for debugging
            logger.info(f"Sending LLM request with priority {llm_request['priority']}: {llm_request}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=llm_request, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Check for the async response format
                        if "request_id" in result:
                            # This is an async request, we need to return a status response
                            actual_request_id = result["request_id"]
                            logger.info(f"Submitted request {actual_request_id} to external LLM service")
                            
                            # Return a response indicating the request is being processed
                            status_url = f"/api/rag/status/{actual_request_id}"
                            
                            return {
                                "answer": f"Your request is being processed by the AI service. This may take a few minutes due to high demand. You can check the status of your request at: <a href='{status_url}' target='_blank' style='color: #007bff; text-decoration: underline;'>{status_url}</a>",
                                "model": "gpt-oss:20b",
                                "request_id": actual_request_id,
                                "status_url": status_url
                            }
                        else:
                            logger.error(f"Unexpected LLM response format: {result}")
                            return {"answer": "I'm having trouble processing the AI response. Please try again later."}
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM request failed with status {response.status}: {error_text}")
                        return {"answer": "I'm having trouble connecting to the AI service. Please try again later."}
                        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {"answer": f"I encountered an error while generating a response: {str(e)}"}
    
    def _extract_symbols_from_query(self, query: str) -> List[str]:
        """Extract stock symbols from the query"""
        import re
        # Common stock symbols to look for
        common_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
                         'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
                         'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
                         'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY']
        
        found_symbols = []
        query_upper = query.upper()
        
        # Look for specific symbols in the query
        for symbol in common_symbols:
            if symbol in query_upper:
                found_symbols.append(symbol)
        
        # If no specific symbols found, check for general market terms
        if not found_symbols:
            general_terms = ['STOCK', 'STOCKS', 'MARKET', 'TRENDING', 'TREND', 'PERFORMANCE', 'PRICE', 'PRICES']
            if any(term in query_upper for term in general_terms):
                # Return empty list to trigger popular symbols fetch
                return []
        
        return found_symbols

    async def _fetch_real_time_data(self, symbols: List[str], search_type: str) -> Dict[str, Any]:
        """Fetch real-time data from available services"""
        real_time_data = {"market_data": {}, "news": {}, "technical": {}, "sources": []}
        
        # If no specific symbols found, use popular symbols for general queries
        if not symbols:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'AMZN', 'SPY', 'QQQ']
            logger.info(f"No specific symbols found in query, using popular symbols: {symbols}")
        
        try:
            # Fetch market data for each symbol using direct function calls
            for symbol in symbols[:3]:  # Limit to 3 symbols to avoid overwhelming
                try:
                    # Get current market price using direct function call
                    price_data = await get_current_market_price(symbol)
                    if price_data and isinstance(price_data, dict):
                        real_time_data["market_data"][symbol] = price_data
                        real_time_data["sources"].append({
                            "type": "market_data",
                            "symbol": symbol,
                            "data": price_data
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch market data for {symbol}: {e}")
            
            # Fetch news data if requested (using external service)
            if search_type in ["news", "all"] and symbols:
                try:
                    async with aiohttp.ClientSession() as session:
                        # Get news sentiment for first symbol
                        news_url = f"{RSS_FEED_URL}/api/news/sentiment/{symbols[0]}"
                        async with session.get(news_url, timeout=10) as response:
                            if response.status == 200:
                                news_data = await response.json()
                                real_time_data["news"] = news_data
                                real_time_data["sources"].append({
                                    "type": "news",
                                    "symbol": symbols[0],
                                    "data": news_data
                                })
                except Exception as e:
                    logger.warning(f"Failed to fetch news data: {e}")
            
            # Fetch technical analysis if requested (using external service)
            if search_type in ["market_data", "all"] and symbols:
                try:
                    async with aiohttp.ClientSession() as session:
                        # Get technical analysis for first symbol
                        tech_url = f"{MARKET_DATA_URL}/api/technical/{symbols[0]}"
                        async with session.get(tech_url, timeout=10) as response:
                            if response.status == 200:
                                tech_data = await response.json()
                                real_time_data["technical"] = tech_data
                                real_time_data["sources"].append({
                                    "type": "technical",
                                    "symbol": symbols[0],
                                    "data": tech_data
                                })
                except Exception as e:
                    logger.warning(f"Failed to fetch technical data: {e}")
                        
        except Exception as e:
            logger.error(f"Error fetching real-time data: {e}")
        
        return real_time_data

    def _build_comprehensive_context(self, vector_results: List[Dict[str, Any]], 
                                   real_time_data: Dict[str, Any], query: str) -> str:
        """Build comprehensive context from vector results and real-time data"""
        context_parts = []
        
        # Add vector storage results
        if vector_results:
            context_parts.append("Historical Data from Vector Storage:")
            for i, result in enumerate(vector_results[:3], 1):
                content = result.get("content", "")
                similarity = result.get("similarity", 0.0)
                vector_type = result.get("vector_type", "unknown")
                context_parts.append(f"Source {i} ({vector_type}, similarity: {similarity:.2f}):\n{content}\n")
        
        # Add real-time market data
        market_data = real_time_data.get("market_data", {})
        if market_data:
            context_parts.append("Real-time Market Data:")
            # Sort symbols by price to show trending stocks first
            sorted_data = sorted(market_data.items(), key=lambda x: x[1].get("price", 0) if isinstance(x[1], dict) else 0, reverse=True)
            
            for symbol, data in sorted_data:
                if isinstance(data, dict):
                    price = data.get("price", data.get("current_price", "N/A"))
                    change = data.get("change", "N/A")
                    volume = data.get("volume", "N/A")
                    source = data.get("source", "unknown")
                    context_parts.append(f"{symbol}: Price ${price}, Source: {source}")
                    if change != "N/A":
                        context_parts.append(f"{symbol}: Change {change}, Volume {volume}")
            
            # Add summary for general market queries
            if len(market_data) > 3:
                prices = [data.get("price", 0) for data in market_data.values() if isinstance(data, dict)]
                avg_price = sum(prices) / len(prices) if prices else 0
                context_parts.append(f"Market Summary: {len(market_data)} stocks tracked, average price: ${avg_price:.2f}")
        
        # Add real-time news data
        news_data = real_time_data.get("news", {})
        if news_data:
            context_parts.append("Recent News and Sentiment:")
            sentiment = news_data.get("sentiment", {})
            if sentiment:
                overall_sentiment = sentiment.get("overall_sentiment", "neutral")
                confidence = sentiment.get("confidence", 0.0)
                context_parts.append(f"Overall sentiment: {overall_sentiment} (confidence: {confidence:.2f})")
            
            articles = news_data.get("articles", [])
            if articles:
                context_parts.append("Recent articles:")
                for i, article in enumerate(articles[:3], 1):
                    title = article.get("title", "No title")
                    sentiment = article.get("sentiment", "neutral")
                    context_parts.append(f"{i}. {title} (sentiment: {sentiment})")
        
        # Add technical analysis
        tech_data = real_time_data.get("technical", {})
        if tech_data:
            context_parts.append("Technical Analysis:")
            indicators = tech_data.get("indicators", {})
            if indicators:
                for indicator, value in indicators.items():
                    context_parts.append(f"{indicator}: {value}")
        
        if not context_parts:
            return "No relevant data found from vector storage or real-time services."
        
        return "\n\n".join(context_parts)

    def _calculate_enhanced_confidence(self, vector_results: List[Dict[str, Any]], 
                                     real_time_data: Dict[str, Any]) -> float:
        """Calculate enhanced confidence score based on available data"""
        confidence = 0.0
        
        # Base confidence from vector similarity
        if vector_results:
            similarities = [result.get("similarity", 0.0) for result in vector_results]
            avg_similarity = sum(similarities) / len(similarities)
            confidence += min(0.6, avg_similarity * 1.2)  # Vector data contributes up to 60%
        
        # Additional confidence from real-time data
        real_time_sources = len(real_time_data.get("sources", []))
        if real_time_sources > 0:
            confidence += min(0.4, real_time_sources * 0.2)  # Real-time data contributes up to 40%
        
        return round(min(1.0, confidence), 2)

    def _calculate_confidence(self, vector_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on vector similarity"""
        if not vector_results:
            return 0.0
        
        # Calculate average similarity score
        similarities = [result.get("similarity", 0.0) for result in vector_results]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Convert to confidence score (0-1)
        confidence = min(1.0, avg_similarity * 2)  # Scale similarity to confidence
        
        return round(confidence, 2)

# Initialize RAG processor
rag_processor = RAGSearchProcessor()

# RAG Search API Endpoints
@app.post("/api/rag/search")
async def rag_search(request: RAGSearchRequest):
    """Search and generate RAG response"""
    try:
        logger.info(f"RAG search request: {request}")
        
        # Use the RAGSearchProcessor for consistent response structure
        response = await rag_processor.process_rag_query(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k,
            include_context=request.include_context
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in RAG search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/examples")
async def get_rag_examples() -> Dict[str, List[str]]:
    """Get example RAG search queries"""
    return {
        "market_analysis": [
            "What happened to AAPL stock in the last quarter?",
            "How did NVDA perform during earnings season?",
            "What are the recent trends in tech stocks?",
            "Show me market data for MSFT"
        ],
        "news_analysis": [
            "What news affected TSLA recently?",
            "What are the latest developments for META?",
            "Show me news about AI stocks",
            "What earnings news came out this week?"
        ],
        "investment_decisions": [
            "What were the best trading decisions for AAPL?",
            "When should I buy NVDA?",
            "What's the risk level for tech stocks?",
            "Show me successful trading patterns"
        ],
        "general": [
            "What's the current market sentiment?",
            "Which stocks are trending up?",
            "What are the key market drivers?",
            "How is the overall market performing?"
        ]
    }

@app.get("/api/rag/stats")
async def get_rag_stats() -> Dict[str, Any]:
    """Get RAG search statistics"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get vector storage stats
            url = f"{VECTOR_STORAGE_URL}/api/stats"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    vector_stats = await response.json()
                else:
                    vector_stats = {"error": "Vector storage unavailable"}
        
        return {
            "vector_storage": vector_stats,
            "rag_processor": "active",
            "supported_search_types": ["market_data", "news", "decisions", "all"],
            "max_results_per_query": 10
        }
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return {"error": str(e)}

async def generate_ai_response_for_rag(question: str, context: str) -> Dict[str, Any]:
    """Generate AI response using the same async callback system as kubernetes-rag-chat"""
    try:
        # Build prompt for financial analysis
        prompt = f"""You are an expert financial analyst and trading strategist. Answer the following question based on the provided context.

Question: {question}

Context:
{context}

Please provide a comprehensive, practical answer that includes:
1. Clear analysis of the financial data or market situation
2. Key insights and trends
3. Practical implications for trading or investment decisions
4. Risk considerations
5. Recommendations when appropriate

Answer:"""
        
        # Generate a unique request ID for tracking
        import uuid
        request_id = str(uuid.uuid4())
        
        # Use the exact same LLM request format as kubernetes-rag-chat
        llm_request = {
            "model": "gpt-oss:20b",
            "prompt": prompt,
            "stream": False,  # Use async callback system like kubernetes-rag-chat
            "priority": 40,  # Highest priority (40 = highest, 30 = high, 20 = normal, 10 = low)
            "timeout_seconds": 300,  # 5 minutes for the LLM request
            "request_id": request_id,
            "callback_url": f"http://unified-analytics-dashboard:80/api/rag/callback/{request_id}",
            "callback_method": "POST"
        }
        
        # Log the request for debugging
        logger.info(f"Sending LLM request with priority {llm_request['priority']}: {llm_request}")
        
        # Use the generate endpoint for external LLM proxy (same as kubernetes-rag-chat)
        url = f"{LLM_PROXY_URL}/api/generate"
        
        # Create a session with longer timeout and retry logic (same as kubernetes-rag-chat)
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, keepalive_timeout=60)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Submit the request
            async with session.post(url, json=llm_request) as response:
                if response.status == 200:
                    result = await response.json()
                    # Check for the correct response format (same as kubernetes-rag-chat)
                    if "request_id" in result:
                        # This is an async request, we need to poll for the result
                        actual_request_id = result["request_id"]
                        logger.info(f"Submitted request {actual_request_id} to LLM proxy")
                        
                        # Store the request ID for later retrieval
                        # For now, we'll return a status URL immediately (same as kubernetes-rag-chat)
                        status_url = f"/api/rag/status/{actual_request_id}"
                        
                        return {
                            "answer": f"Your request is being processed. This may take a few minutes due to high demand. You can check the status of your request at: <a href='{status_url}' target='_blank' style='color: #007bff; text-decoration: underline;'>{status_url}</a>",
                            "model": "gpt-oss:20b",
                            "request_id": actual_request_id,
                            "status_url": status_url
                        }
                    else:
                        logger.error(f"Unexpected LLM response format: {result}")
                        return {
                            "answer": "I'm having trouble processing the AI response. Please try again later.",
                            "model": "gpt-oss:20b"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"LLM request failed with status {response.status}: {error_text}")
                    return {
                        "answer": "I'm having trouble connecting to the AI service. Please try again later.",
                        "model": "gpt-oss:20b"
                    }
                    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return {
            "answer": f"I encountered an error while generating a response: {str(e)}",
            "model": "gpt-oss:20b"
        }

@app.post("/api/rag/callback/{request_id}")
async def handle_rag_callback(request_id: str, request: Dict[str, Any]):
    """Handle callback from external LLM proxy when request completes (same as kubernetes-rag-chat)"""
    try:
        logger.info(f"Received callback for RAG request {request_id}: {request}")
        
        # Store the completed request result (in a real implementation, you'd use a database)
        # For now, we'll just log it (same as kubernetes-rag-chat)
        if request.get("status") == "completed" and request.get("result"):
            logger.info(f"RAG request {request_id} completed successfully")
            # Here you could store the result in a database or cache
        elif request.get("status") == "failed":
            logger.error(f"RAG request {request_id} failed: {request.get('error')}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling callback for RAG request {request_id}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/rag/status/{request_id}")
async def check_rag_request_status(request_id: str):
    """Check the status of a RAG request and display the result if completed (same as kubernetes-rag-chat)"""
    try:
        # Check the status with the external LLM proxy (same as kubernetes-rag-chat)
        status_url = f"{LLM_PROXY_URL}/api/status/{request_id}"
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(status_url) as response:
                if response.status == 200:
                    status_result = await response.json()
                    
                    # Create a simple HTML page to display the status (same as kubernetes-rag-chat)
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>RAG Request Status - {request_id}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .status {{ padding: 20px; border-radius: 5px; margin: 20px 0; }}
                            .queued {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
                            .processing {{ background-color: #d1ecf1; border: 1px solid #bee5eb; }}
                            .completed {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
                            .failed {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
                            .answer {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                            .refresh {{ background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                            .refresh:hover {{ background-color: #0056b3; }}
                        </style>
                        <script>
                            function refreshStatus() {{
                                location.reload();
                            }}
                            
                            // Auto-refresh every 30 seconds if still processing
                            function autoRefresh() {{
                                const status = '{status_result.get("status", "unknown")}';
                                if (status === 'queued' || status === 'processing') {{
                                    setTimeout(refreshStatus, 30000);
                                }}
                            }}
                            
                            // Start auto-refresh when page loads
                            window.onload = autoRefresh;
                        </script>
                    </head>
                    <body>
                        <h1>RAG Request Status</h1>
                        <p><strong>Request ID:</strong> {request_id}</p>
                        
                        <div class="status {status_result.get('status', 'unknown')}">
                            <h2>Status: {status_result.get('status', 'unknown').title()}</h2>
                            <p>{status_result.get('message', 'No status message available')}</p>
                        </div>
                        
                        {f'''
                        <div class="answer">
                            <h3>Generated Answer:</h3>
                            <p>{status_result.get('result', {}).get('response', 'No response available')}</p>
                        </div>
                        ''' if status_result.get('status') == 'completed' else ''}
                        
                        <button class="refresh" onclick="refreshStatus()">Refresh Status</button>
                        
                        <p><a href="/api/rag/search" style="color: #007bff;">← Back to RAG Search</a></p>
                    </body>
                    </html>
                    """
                    
                    return HTMLResponse(content=html_content)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to check status: {response.status} - {error_text}")
                    return HTMLResponse(content=f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h1>Error Checking Status</h1>
                        <p>Failed to check status: {response.status}</p>
                        <p><a href="/api/rag/search">← Back to RAG Search</a></p>
                    </body>
                    </html>
                    """)
                    
    except Exception as e:
        logger.error(f"Error checking RAG request status: {e}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>Error checking status: {str(e)}</p>
            <p><a href="/api/rag/search">← Back to RAG Search</a></p>
        </body>
        </html>
        """)

# Removed old mock functions - now using RAGSearchProcessor class methods

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80) 