"""
News Scanner Service - Monitors headlines for market-moving events
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import json
from loguru import logger

from ...core.trading_engine import TradeSignal
from ...utils.config import Config


@dataclass
class NewsEvent:
    """News event data structure"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float
    impact_score: float
    affected_symbols: List[str]
    event_type: str
    confidence: float
    metadata: Dict[str, Any]


class NewsScanner:
    """News scanner that monitors headlines for trading opportunities"""
    
    def __init__(self, config: Config):
        self.config = config
        self.is_running = False
        self.session = None
        
        # News sources configuration
        self.news_sources = {
            "reuters": "https://www.reuters.com/markets/",
            "bloomberg": "https://www.bloomberg.com/markets",
            "cnbc": "https://www.cnbc.com/markets/",
            "yahoo_finance": "https://finance.yahoo.com/news/",
            "marketwatch": "https://www.marketwatch.com/newsview"
        }
        
        # Keywords for different event types
        self.event_keywords = {
            "earnings": [
                "earnings", "quarterly results", "profit", "revenue", "beat", "miss",
                "guidance", "outlook", "analyst estimates", "EPS", "EBITDA"
            ],
            "mergers_acquisitions": [
                "merger", "acquisition", "buyout", "takeover", "deal", "purchase",
                "consolidation", "spin-off", "divestiture", "IPO", "SPAC"
            ],
            "regulatory": [
                "regulation", "regulatory", "FDA", "SEC", "DOJ", "antitrust",
                "investigation", "lawsuit", "settlement", "approval", "rejection"
            ],
            "macro_economic": [
                "Fed", "Federal Reserve", "interest rates", "inflation", "GDP",
                "unemployment", "jobs report", "CPI", "PPI", "economic data"
            ],
            "sector_specific": [
                "oil", "energy", "tech", "healthcare", "finance", "retail",
                "automotive", "real estate", "biotech", "pharmaceutical"
            ],
            "geopolitical": [
                "trade war", "tariffs", "sanctions", "election", "political",
                "conflict", "diplomatic", "international relations"
            ]
        }
        
        # Company name to symbol mapping
        self.company_symbols = {
            "apple": "AAPL",
            "microsoft": "MSFT", 
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "salesforce": "CRM",
            "oracle": "ORCL",
            "intel": "INTC",
            "amd": "AMD",
            "coca-cola": "KO",
            "coca cola": "KO",
            "pepsi": "PEP",
            "pepsico": "PEP",
            "walmart": "WMT",
            "target": "TGT",
            "home depot": "HD",
            "lowes": "LOW",
            "disney": "DIS",
            "comcast": "CMCSA",
            "verizon": "VZ",
            "at&t": "T",
            "att": "T",
            "jpmorgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "goldman sachs": "GS",
            "morgan stanley": "MS",
            "berkshire hathaway": "BRK.A",
            "berkshire": "BRK.A",
            "johnson & johnson": "JNJ",
            "johnson and johnson": "JNJ",
            "pfizer": "PFE",
            "moderna": "MRNA",
            "biontech": "BNTX",
            "exxon": "XOM",
            "chevron": "CVX",
            "conocophillips": "COP",
            "unitedhealth": "UNH",
            "anthem": "ANTM",
            "cigna": "CI",
            "humana": "HUM",
            # Additional major companies
            "palantir": "PLTR",
            "shopify": "SHOP",
            "zoom": "ZM",
            "uber": "UBER",
            "lyft": "LYFT",
            "airbnb": "ABNB",
            "doordash": "DASH",
            "snap": "SNAP",
            "pinterest": "PINS",
            "twitter": "TWTR",
            "x": "TWTR",
            "spotify": "SPOT",
            "roblox": "RBLX",
            "coinbase": "COIN",
            "paypal": "PYPL",
            "square": "SQ",
            "block": "SQ",
            "visa": "V",
            "mastercard": "MA",
            "american express": "AXP",
            "amex": "AXP",
            "boeing": "BA",
            "airbus": "EADSY",
            "general electric": "GE",
            "3m": "MMM",
            "caterpillar": "CAT",
            "deere": "DE",
            "john deere": "DE",
            "mcdonalds": "MCD",
            "starbucks": "SBUX",
            "costco": "COST",
            "home depot": "HD",
            "lowes": "LOW",
            "nike": "NKE",
            "adidas": "ADS.DE",
            "adobe": "ADBE",
            "autodesk": "ADSK",
            "intuit": "INTU",
            "workday": "WDAY",
            "servicenow": "NOW",
            "snowflake": "SNOW",
            "datadog": "DDOG",
            "mongodb": "MDB",
            "okta": "OKTA",
            "crowdstrike": "CRWD",
            "zscaler": "ZS",
            "fortinet": "FTNT",
            "palo alto networks": "PANW",
            "cisco": "CSCO",
            "qualcomm": "QCOM",
            "broadcom": "AVGO",
            "marvell": "MRVL",
            "micron": "MU",
            "western digital": "WDC",
            "seagate": "STX",
            "amd": "AMD",
            "intel": "INTC",
            "nvidia": "NVDA",
            "meta": "META",
            "facebook": "META",
            "alphabet": "GOOGL",
            "google": "GOOGL",
            "microsoft": "MSFT",
            "apple": "AAPL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "netflix": "NFLX",
            "salesforce": "CRM",
            "oracle": "ORCL"
        }
        
        # Sentiment analysis keywords
        self.positive_keywords = [
            "beat", "surge", "jump", "rise", "gain", "positive", "strong", "growth",
            "profit", "revenue", "success", "approval", "breakthrough", "innovation",
            "partnership", "expansion", "acquisition", "merger", "deal", "win"
        ]
        
        self.negative_keywords = [
            "miss", "fall", "drop", "decline", "loss", "negative", "weak", "rejection",
            "failure", "delay", "investigation", "lawsuit", "recall", "bankruptcy",
            "layoff", "restructuring", "downgrade", "cut", "reduction"
        ]
        
        # Track processed news to avoid duplicates
        self.processed_news: Set[str] = set()
        
    async def start(self):
        """Start the news scanner"""
        self.is_running = True
        self.session = aiohttp.ClientSession()
        logger.info("News scanner started")
        
        # Start monitoring loop
        await self._monitoring_loop()
    
    async def stop(self):
        """Stop the news scanner"""
        self.is_running = False
        if self.session:
            await self.session.close()
        logger.info("News scanner stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Scan all news sources
                news_events = await self._scan_news_sources()
                
                # Process and analyze news events
                for event in news_events:
                    if await self._should_generate_signal(event):
                        signal = await self._generate_trading_signal(event)
                        if signal:
                            # Send signal to trading engine
                            await self._send_signal(signal)
                
                # Wait before next scan
                await asyncio.sleep(self.config.news_scan_interval or 300)  # 5 minutes default
                
            except Exception as e:
                logger.error(f"Error in news monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _scan_news_sources(self) -> List[NewsEvent]:
        """Scan all configured news sources"""
        events = []
        
        for source_name, source_url in self.news_sources.items():
            try:
                source_events = await self._scan_source(source_name, source_url)
                events.extend(source_events)
            except Exception as e:
                logger.error(f"Error scanning {source_name}: {e}")
        
        return events
    
    async def _scan_source(self, source_name: str, source_url: str) -> List[NewsEvent]:
        """Scan a specific news source"""
        events = []
        
        try:
            async with self.session.get(source_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract headlines and content (simplified - in production you'd use proper parsing)
                    headlines = self._extract_headlines(content, source_name)
                    
                    for headline in headlines:
                        if self._is_market_relevant(headline):
                            event = await self._analyze_news_event(headline, source_name, source_url)
                            if event:
                                events.append(event)
                                
        except Exception as e:
            logger.error(f"Error scanning {source_name}: {e}")
        
        return events
    
    def _extract_headlines(self, content: str, source: str) -> List[str]:
        """Extract headlines from HTML content"""
        headlines = []
        
        # Simple regex patterns for different sources
        patterns = {
            "reuters": r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            "bloomberg": r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            "cnbc": r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            "yahoo_finance": r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            "marketwatch": r'<h[1-6][^>]*>([^<]+)</h[1-6]>'
        }
        
        pattern = patterns.get(source, r'<h[1-6][^>]*>([^<]+)</h[1-6]>')
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for match in matches[:10]:  # Limit to first 10 headlines
            if len(match.strip()) > 20:  # Filter out short headlines
                headlines.append(match.strip())
        
        return headlines
    
    def _is_market_relevant(self, headline: str) -> bool:
        """Check if headline is market-relevant"""
        headline_lower = headline.lower()
        
        # Check for any event keywords
        for event_type, keywords in self.event_keywords.items():
            for keyword in keywords:
                if keyword.lower() in headline_lower:
                    return True
        
        # Check for company names
        for company_name in self.company_symbols.keys():
            if company_name.lower() in headline_lower:
                return True
        
        return False
    
    async def _analyze_news_event(self, headline: str, source: str, url: str) -> Optional[NewsEvent]:
        """Analyze a news headline and create a news event"""
        try:
            # Skip if already processed
            headline_hash = hash(headline)
            if headline_hash in self.processed_news:
                return None
            
            self.processed_news.add(headline_hash)
            
            # Determine event type
            event_type = self._classify_event_type(headline)
            
            # Extract affected symbols
            affected_symbols = self._extract_symbols(headline)
            
            # Calculate sentiment score
            sentiment_score = self._calculate_sentiment(headline)
            
            # Calculate impact score
            impact_score = self._calculate_impact(headline, event_type, affected_symbols)
            
            # Calculate confidence
            confidence = self._calculate_confidence(headline, event_type, sentiment_score, impact_score)
            
            return NewsEvent(
                title=headline,
                content=headline,  # In production, you'd fetch full article content
                source=source,
                url=url,
                published_at=datetime.now(),
                sentiment_score=sentiment_score,
                impact_score=impact_score,
                affected_symbols=affected_symbols,
                event_type=event_type,
                confidence=confidence,
                metadata={
                    "headline_length": len(headline),
                    "source": source,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing news event: {e}")
            return None
    
    def _classify_event_type(self, headline: str) -> str:
        """Classify the type of news event"""
        headline_lower = headline.lower()
        
        for event_type, keywords in self.event_keywords.items():
            for keyword in keywords:
                if keyword.lower() in headline_lower:
                    return event_type
        
        return "general"
    
    def _extract_symbols(self, headline: str) -> List[str]:
        """Extract affected stock symbols from headline"""
        symbols = []
        headline_lower = headline.lower()
        
        for company_name, symbol in self.company_symbols.items():
            if company_name.lower() in headline_lower:
                symbols.append(symbol)
        
        return list(set(symbols))  # Remove duplicates
    
    def _calculate_sentiment(self, headline: str) -> float:
        """Calculate sentiment score (-1 to 1)"""
        headline_lower = headline.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in headline_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in headline_lower)
        
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_keywords
    
    def _calculate_impact(self, headline: str, event_type: str, symbols: List[str]) -> float:
        """Calculate impact score (0 to 1)"""
        impact = 0.0
        
        # Base impact by event type
        event_impact = {
            "earnings": 0.8,
            "mergers_acquisitions": 0.9,
            "regulatory": 0.7,
            "macro_economic": 0.6,
            "sector_specific": 0.5,
            "geopolitical": 0.8,
            "general": 0.3
        }
        
        impact += event_impact.get(event_type, 0.3)
        
        # Boost impact for major companies
        major_companies = {"AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"}
        if any(symbol in major_companies for symbol in symbols):
            impact += 0.2
        
        # Boost for urgent keywords
        urgent_keywords = ["breaking", "urgent", "alert", "just in", "live"]
        if any(keyword in headline.lower() for keyword in urgent_keywords):
            impact += 0.1
        
        return min(impact, 1.0)
    
    def _calculate_confidence(self, headline: str, event_type: str, sentiment: float, impact: float) -> float:
        """Calculate confidence score (0 to 1)"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for specific event types
        if event_type in ["earnings", "mergers_acquisitions"]:
            confidence += 0.2
        
        # Boost confidence for strong sentiment
        if abs(sentiment) > 0.5:
            confidence += 0.1
        
        # Boost confidence for high impact
        if impact > 0.7:
            confidence += 0.1
        
        # Boost confidence for longer headlines (more detail)
        if len(headline) > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _should_generate_signal(self, event: NewsEvent) -> bool:
        """Determine if a news event should generate a trading signal"""
        # Only generate signals for high-impact events
        if event.impact_score < 0.5:
            return False
        
        # Only generate signals for events with affected symbols
        if not event.affected_symbols:
            return False
        
        # Only generate signals for events with sufficient confidence
        if event.confidence < 0.6:
            return False
        
        return True
    
    async def _generate_trading_signal(self, event: NewsEvent) -> Optional[TradeSignal]:
        """Generate a trading signal from a news event"""
        try:
            # Determine action based on sentiment
            if event.sentiment_score > 0.3:
                action = "BUY"
            elif event.sentiment_score < -0.3:
                action = "SELL"
            else:
                return None  # Neutral sentiment, no signal
            
            # Use the first affected symbol (in production, you might want to handle multiple)
            symbol = event.affected_symbols[0]
            
            # Calculate position size based on impact and confidence
            base_quantity = 1000  # Base $1000 position
            quantity = base_quantity * event.impact_score * event.confidence
            
            # Estimate price (in production, you'd get real-time price)
            estimated_price = 100.0  # Placeholder
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=quantity / estimated_price,
                price=estimated_price,
                timestamp=datetime.now(),
                strategy="news_scanner",
                confidence=event.confidence,
                metadata={
                    "news_event": {
                        "title": event.title,
                        "source": event.source,
                        "event_type": event.event_type,
                        "sentiment_score": event.sentiment_score,
                        "impact_score": event.impact_score,
                        "url": event.url
                    },
                    "signal_type": "news_driven",
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating trading signal from news event: {e}")
            return None
    
    async def _send_signal(self, signal: TradeSignal):
        """Send trading signal to the trading engine"""
        try:
            # In production, you'd send this to your trading engine
            logger.info(f"News-driven signal generated: {signal.action} {signal.symbol}")
            logger.info(f"News: {signal.metadata['news_event']['title']}")
            
            # You can also send via API
            # await self._send_signal_via_api(signal)
            
        except Exception as e:
            logger.error(f"Error sending news signal: {e}")
    
    async def _send_signal_via_api(self, signal: TradeSignal):
        """Send signal via REST API"""
        try:
            async with self.session.post(
                f"{self.config.api_base_url}/signals",
                json={
                    "symbol": signal.symbol,
                    "action": signal.action,
                    "quantity": signal.quantity,
                    "price": signal.price,
                    "strategy": signal.strategy,
                    "confidence": signal.confidence,
                    "metadata": signal.metadata
                }
            ) as response:
                if response.status == 200:
                    logger.info("News signal sent successfully via API")
                else:
                    logger.error(f"Failed to send news signal: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending signal via API: {e}") 