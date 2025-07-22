#!/usr/bin/env python3
"""
AI Analysis Service - Generates buy/sell recommendations using LLM analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Analysis Service", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://localhost:12001")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://localhost:8002")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trading")

# Default stock list - can be configured via environment
DEFAULT_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", 
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "NKE", "DIS",
    "JPM", "BAC", "WFC", "GS", "JNJ", "PFE", "UNH", "HD", "PG"
]

class StockAnalysis(BaseModel):
    symbol: str
    current_price: float
    recommendation: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: str
    target_price: Optional[float]
    stop_loss: Optional[float]
    position_size: Optional[str]
    risk_level: str  # LOW, MEDIUM, HIGH
    technical_signals: Dict[str, Any]
    sentiment_score: Optional[float]
    market_context: Dict[str, Any]
    analysis_timestamp: datetime

class AnalysisRequest(BaseModel):
    symbols: Optional[List[str]] = None
    include_news: bool = True
    include_technical: bool = True
    include_sentiment: bool = True
    force_refresh: bool = False

class AnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: datetime
    total_symbols: int
    recommendations: List[StockAnalysis]
    summary: Dict[str, Any]

# In-memory storage for analysis results
analysis_cache: Dict[str, Dict] = {}

async def get_market_data(symbol: str) -> Dict[str, Any]:
    """Fetch current market data for a symbol"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get from market data service
            url = f"{MARKET_DATA_URL}/api/market-data/{symbol}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                
        # Fallback: return basic structure
        return {
            "symbol": symbol,
            "price": 0.0,
            "volume": 0,
            "change": 0.0,
            "change_percent": 0.0
        }
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        return {"symbol": symbol, "price": 0.0}

async def get_technical_indicators(symbol: str) -> Dict[str, Any]:
    """Get technical indicators for a symbol"""
    try:
        # This would integrate with your existing technical analysis
        # For now, return mock data
        return {
            "rsi": 50.0,
            "macd": {"value": 0.0, "signal": 0.0, "histogram": 0.0},
            "bollinger_bands": {"upper": 0.0, "middle": 0.0, "lower": 0.0},
            "sma_20": 0.0,
            "sma_50": 0.0,
            "volume_sma": 0.0
        }
    except Exception as e:
        logger.error(f"Error fetching technical indicators for {symbol}: {e}")
        return {}

async def get_sentiment_data(symbol: str) -> Dict[str, Any]:
    """Get sentiment analysis for a symbol"""
    try:
        # This would integrate with your existing news/sentiment analysis
        return {
            "sentiment_score": 0.0,
            "news_count": 0,
            "positive_news": 0,
            "negative_news": 0,
            "neutral_news": 0
        }
    except Exception as e:
        logger.error(f"Error fetching sentiment data for {symbol}: {e}")
        return {"sentiment_score": 0.0}

async def analyze_with_llm(symbol: str, market_data: Dict, technical_data: Dict, sentiment_data: Dict) -> Dict[str, Any]:
    """Use LLM to analyze stock and generate recommendation"""
    
    # Prepare context for LLM
    context = {
        "symbol": symbol,
        "current_price": market_data.get("price", 0),
        "volume": market_data.get("volume", 0),
        "change_percent": market_data.get("change_percent", 0),
        "technical_indicators": technical_data,
        "sentiment": sentiment_data
    }
    
    # Create prompt for LLM
    prompt = f"""
You are an expert stock analyst. Analyze the following data for {symbol} and provide a trading recommendation.

Current Market Data:
- Price: ${context['current_price']:.2f}
- Volume: {context['volume']:,}
- Change: {context['change_percent']:.2f}%

Technical Indicators:
- RSI: {technical_data.get('rsi', 0):.1f}
- MACD: {technical_data.get('macd', {}).get('value', 0):.3f}
- 20-day SMA: ${technical_data.get('sma_20', 0):.2f}
- 50-day SMA: ${technical_data.get('sma_50', 0):.2f}

Sentiment Analysis:
- Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f}
- News Count: {sentiment_data.get('news_count', 0)}

Provide your analysis in the following JSON format:
{{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 0-100,
    "reasoning": "Detailed explanation",
    "target_price": 0.0,
    "stop_loss": 0.0,
    "position_size": "SMALL|MEDIUM|LARGE",
    "risk_level": "LOW|MEDIUM|HIGH",
    "key_factors": ["factor1", "factor2", "factor3"]
}}

Focus on:
1. Technical analysis signals
2. Sentiment impact
3. Risk assessment
4. Market timing
"""

    try:
        async with aiohttp.ClientSession() as session:
            # Call LLM proxy service
            llm_request = {
                "prompt": prompt,
                "max_tokens": 500,
                "temperature": 0.3,
                "task_type": "stock_analysis"
            }
            
            url = f"{LLM_PROXY_URL}/api/chat"
            async with session.post(url, json=llm_request) as response:
                if response.status == 200:
                    result = await response.json()
                    # Parse LLM response
                    try:
                        # Extract JSON from LLM response
                        response_text = result.get("response", "")
                        # Find JSON in the response
                        start_idx = response_text.find('{')
                        end_idx = response_text.rfind('}') + 1
                        if start_idx != -1 and end_idx != 0:
                            json_str = response_text[start_idx:end_idx]
                            analysis = json.loads(json_str)
                            return analysis
                        else:
                            # Fallback parsing
                            return parse_llm_response(response_text)
                    except json.JSONDecodeError:
                        return parse_llm_response(response_text)
                else:
                    logger.error(f"LLM service error: {response.status}")
                    return get_fallback_analysis(symbol, context)
                    
    except Exception as e:
        logger.error(f"Error calling LLM for {symbol}: {e}")
        return get_fallback_analysis(symbol, context)

def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response when JSON parsing fails"""
    # Simple keyword-based parsing
    response_text = response_text.upper()
    
    recommendation = "HOLD"
    if "BUY" in response_text:
        recommendation = "BUY"
    elif "SELL" in response_text:
        recommendation = "SELL"
    
    confidence = 50.0
    if "HIGH" in response_text or "STRONG" in response_text:
        confidence = 80.0
    elif "MEDIUM" in response_text:
        confidence = 60.0
    elif "LOW" in response_text or "WEAK" in response_text:
        confidence = 30.0
    
    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasoning": "AI analysis based on technical and sentiment factors",
        "target_price": 0.0,
        "stop_loss": 0.0,
        "position_size": "MEDIUM",
        "risk_level": "MEDIUM",
        "key_factors": ["Technical analysis", "Market sentiment"]
    }

def get_fallback_analysis(symbol: str, context: Dict) -> Dict[str, Any]:
    """Generate fallback analysis when LLM fails"""
    return {
        "recommendation": "HOLD",
        "confidence": 50.0,
        "reasoning": f"Limited data available for {symbol}. Recommend monitoring for better signals.",
        "target_price": context.get("current_price", 0),
        "stop_loss": context.get("current_price", 0) * 0.95,
        "position_size": "SMALL",
        "risk_level": "MEDIUM",
        "key_factors": ["Limited data", "Conservative approach"]
    }

async def analyze_stock(symbol: str, include_news: bool = True, include_technical: bool = True) -> StockAnalysis:
    """Analyze a single stock and return recommendation"""
    
    # Get market data
    market_data = await get_market_data(symbol)
    
    # Get technical indicators
    technical_data = {}
    if include_technical:
        technical_data = await get_technical_indicators(symbol)
    
    # Get sentiment data
    sentiment_data = {}
    if include_news:
        sentiment_data = await get_sentiment_data(symbol)
    
    # Analyze with LLM
    llm_analysis = await analyze_with_llm(symbol, market_data, technical_data, sentiment_data)
    
    # Create analysis result
    analysis = StockAnalysis(
        symbol=symbol,
        current_price=market_data.get("price", 0),
        recommendation=llm_analysis.get("recommendation", "HOLD"),
        confidence=llm_analysis.get("confidence", 50.0),
        reasoning=llm_analysis.get("reasoning", "Analysis completed"),
        target_price=llm_analysis.get("target_price"),
        stop_loss=llm_analysis.get("stop_loss"),
        position_size=llm_analysis.get("position_size", "MEDIUM"),
        risk_level=llm_analysis.get("risk_level", "MEDIUM"),
        technical_signals=technical_data,
        sentiment_score=sentiment_data.get("sentiment_score"),
        market_context={
            "volume": market_data.get("volume", 0),
            "change_percent": market_data.get("change_percent", 0)
        },
        analysis_timestamp=datetime.utcnow()
    )
    
    return analysis

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-analysis-service", "timestamp": datetime.utcnow()}

@app.post("/api/analyze/symbol/{symbol}")
async def analyze_single_symbol(symbol: str, request: AnalysisRequest = AnalysisRequest()):
    """Analyze a single stock symbol"""
    try:
        analysis = await analyze_stock(
            symbol.upper(), 
            include_news=request.include_news,
            include_technical=request.include_technical
        )
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed for {symbol}")

@app.post("/api/analyze/batch")
async def analyze_batch(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze multiple stock symbols"""
    
    symbols = request.symbols or DEFAULT_STOCKS
    analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Start background analysis
    background_tasks.add_task(
        run_batch_analysis, 
        analysis_id, 
        symbols, 
        request.include_news, 
        request.include_technical,
        request.include_sentiment
    )
    
    return {
        "analysis_id": analysis_id,
        "status": "started",
        "symbols": symbols,
        "estimated_completion": datetime.utcnow() + timedelta(minutes=len(symbols) * 0.5)
    }

async def run_batch_analysis(analysis_id: str, symbols: List[str], include_news: bool, include_technical: bool, include_sentiment: bool):
    """Run batch analysis in background"""
    logger.info(f"Starting batch analysis {analysis_id} for {len(symbols)} symbols")
    
    results = []
    for i, symbol in enumerate(symbols):
        try:
            analysis = await analyze_stock(symbol, include_news, include_technical)
            results.append(analysis)
            logger.info(f"Completed {symbol} ({i+1}/{len(symbols)})")
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            # Add error result
            error_analysis = StockAnalysis(
                symbol=symbol,
                current_price=0,
                recommendation="ERROR",
                confidence=0,
                reasoning=f"Analysis failed: {str(e)}",
                analysis_timestamp=datetime.utcnow()
            )
            results.append(error_analysis)
    
    # Store results
    analysis_cache[analysis_id] = {
        "timestamp": datetime.utcnow(),
        "total_symbols": len(symbols),
        "recommendations": [r.dict() for r in results],
        "summary": generate_summary(results)
    }
    
    logger.info(f"Completed batch analysis {analysis_id}")

def generate_summary(results: List[StockAnalysis]) -> Dict[str, Any]:
    """Generate summary statistics for batch analysis"""
    buy_count = sum(1 for r in results if r.recommendation == "BUY")
    sell_count = sum(1 for r in results if r.recommendation == "SELL")
    hold_count = sum(1 for r in results if r.recommendation == "HOLD")
    
    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
    
    return {
        "total_analyzed": len(results),
        "buy_recommendations": buy_count,
        "sell_recommendations": sell_count,
        "hold_recommendations": hold_count,
        "average_confidence": round(avg_confidence, 2),
        "high_confidence_signals": sum(1 for r in results if r.confidence >= 80),
        "medium_confidence_signals": sum(1 for r in results if 60 <= r.confidence < 80),
        "low_confidence_signals": sum(1 for r in results if r.confidence < 60)
    }

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get results of a batch analysis"""
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_cache[analysis_id]

@app.get("/api/analysis/recent")
async def get_recent_analyses(limit: int = 10):
    """Get recent analysis results"""
    recent = sorted(analysis_cache.items(), key=lambda x: x[1]["timestamp"], reverse=True)[:limit]
    return {
        "analyses": [
            {"analysis_id": k, **v} for k, v in recent
        ]
    }

@app.get("/api/recommendations/daily")
async def get_daily_recommendations():
    """Get daily stock recommendations"""
    # Find today's analysis or run new one
    today = datetime.utcnow().date()
    today_key = f"daily_{today.strftime('%Y%m%d')}"
    
    if today_key not in analysis_cache:
        # Run daily analysis
        await run_batch_analysis(today_key, DEFAULT_STOCKS, True, True, True)
    
    return analysis_cache.get(today_key, {"status": "not_available"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11085) 