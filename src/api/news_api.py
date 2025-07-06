"""
News API endpoints for the trading bot
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.news.news_scanner import NewsScanner, NewsEvent
from ..utils.config import Config

# Pydantic models
class NewsEventResponse(BaseModel):
    title: str
    source: str
    url: str
    published_at: str
    sentiment_score: float
    impact_score: float
    affected_symbols: List[str]
    event_type: str
    confidence: float
    metadata: Dict[str, Any]


class NewsScannerConfig(BaseModel):
    is_active: bool
    scan_interval: int = 300  # seconds
    sources: List[str]
    event_types: List[str]
    min_impact_score: float = 0.5
    min_confidence: float = 0.6


# Global news scanner instance
news_scanner: Optional[NewsScanner] = None

# Create router
router = APIRouter(prefix="/news", tags=["news"])


@router.on_event("startup")
async def startup_event():
    """Initialize news scanner on startup"""
    global news_scanner
    config = Config()
    news_scanner = NewsScanner(config)


@router.get("/scanner/status")
async def get_scanner_status():
    """Get news scanner status"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    return {
        "is_running": news_scanner.is_running,
        "sources": list(news_scanner.news_sources.keys()),
        "event_types": list(news_scanner.event_keywords.keys()),
        "processed_news_count": len(news_scanner.processed_news)
    }


@router.post("/scanner/start")
async def start_scanner():
    """Start the news scanner"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    if news_scanner.is_running:
        raise HTTPException(status_code=400, detail="News scanner is already running")
    
    # Start scanner in background
    import asyncio
    asyncio.create_task(news_scanner.start())
    
    return {"message": "News scanner started"}


@router.post("/scanner/stop")
async def stop_scanner():
    """Stop the news scanner"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    if not news_scanner.is_running:
        raise HTTPException(status_code=400, detail="News scanner is not running")
    
    await news_scanner.stop()
    return {"message": "News scanner stopped"}


@router.get("/events", response_model=List[NewsEventResponse])
async def get_recent_events(limit: int = 50):
    """Get recent news events"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    # In a real implementation, you'd store events in a database
    # For now, return a sample response
    sample_events = [
        NewsEventResponse(
            title="Apple Reports Strong Q4 Earnings, Beats Estimates",
            source="reuters",
            url="https://www.reuters.com/example",
            published_at=datetime.now().isoformat(),
            sentiment_score=0.8,
            impact_score=0.9,
            affected_symbols=["AAPL"],
            event_type="earnings",
            confidence=0.85,
            metadata={"headline_length": 45, "source": "reuters"}
        ),
        NewsEventResponse(
            title="Tesla Faces Regulatory Investigation Over Safety Concerns",
            source="bloomberg",
            url="https://www.bloomberg.com/example",
            published_at=datetime.now().isoformat(),
            sentiment_score=-0.6,
            impact_score=0.7,
            affected_symbols=["TSLA"],
            event_type="regulatory",
            confidence=0.75,
            metadata={"headline_length": 52, "source": "bloomberg"}
        )
    ]
    
    return sample_events[:limit]


@router.get("/events/{symbol}")
async def get_events_by_symbol(symbol: str, limit: int = 20):
    """Get news events for a specific symbol"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    # In a real implementation, you'd query events by symbol
    # For now, return a sample response
    sample_events = [
        NewsEventResponse(
            title=f"Latest news about {symbol}",
            source="reuters",
            url="https://www.reuters.com/example",
            published_at=datetime.now().isoformat(),
            sentiment_score=0.5,
            impact_score=0.6,
            affected_symbols=[symbol],
            event_type="general",
            confidence=0.7,
            metadata={"headline_length": 30, "source": "reuters"}
        )
    ]
    
    return sample_events[:limit]


@router.get("/sentiment/{symbol}")
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a symbol"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    # In a real implementation, you'd calculate sentiment from recent news
    return {
        "symbol": symbol,
        "sentiment_score": 0.65,
        "sentiment_label": "positive",
        "confidence": 0.8,
        "recent_events_count": 5,
        "last_updated": datetime.now().isoformat()
    }


@router.post("/scan/trigger")
async def trigger_manual_scan():
    """Trigger a manual news scan"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    try:
        # Trigger a manual scan
        events = await news_scanner._scan_news_sources()
        
        return {
            "message": "Manual scan completed",
            "events_found": len(events),
            "scan_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/sources")
async def get_news_sources():
    """Get configured news sources"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    return {
        "sources": news_scanner.news_sources,
        "total_sources": len(news_scanner.news_sources)
    }


@router.get("/keywords")
async def get_event_keywords():
    """Get event keywords by category"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    return {
        "event_keywords": news_scanner.event_keywords,
        "positive_keywords": news_scanner.positive_keywords,
        "negative_keywords": news_scanner.negative_keywords
    }


@router.get("/companies")
async def get_company_mappings():
    """Get company name to symbol mappings"""
    if not news_scanner:
        raise HTTPException(status_code=503, detail="News scanner not initialized")
    
    return {
        "company_symbols": news_scanner.company_symbols,
        "total_companies": len(news_scanner.company_symbols)
    } 