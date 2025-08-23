"""
Polygon.io Earnings Service

Fetches quarterly earnings reports from Polygon.io API including:
- EPS and revenue data
- Earnings estimates and surprises
- Forward guidance
- Conference call dates
"""

import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class PolygonEarningsService:
    """Service for fetching earnings data from Polygon.io"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "TradingSystem/1.0",
                    "Accept": "application/json"
                }
            )
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_earnings(self, symbol: str, start_date: str, end_date: str, 
                           include_estimates: bool = True, include_guidance: bool = True) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch earnings data for a symbol
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            include_estimates: Whether to include earnings estimates
            include_guidance: Whether to include forward guidance
            
        Returns:
            List of earnings data dictionaries
        """
        try:
            logger.info(f"📊 Fetching earnings for {symbol} from {start_date} to {end_date}")
            
            session = await self._get_session()
            
            # Fetch earnings data
            earnings_data = await self._fetch_earnings_data(session, symbol, start_date, end_date)
            if not earnings_data:
                logger.warning(f"No earnings data returned for {symbol}")
                return None
            
            # Fetch estimates if requested
            estimates_data = None
            if include_estimates:
                estimates_data = await self._fetch_earnings_estimates(session, symbol, start_date, end_date)
            
            # Fetch guidance if requested
            guidance_data = None
            if include_guidance:
                guidance_data = await self._fetch_guidance(session, symbol, start_date, end_date)
            
            # Combine and process data
            processed_earnings = self._process_earnings_data(
                earnings_data, estimates_data, guidance_data, symbol
            )
            
            logger.info(f"✅ Successfully processed {len(processed_earnings)} earnings records for {symbol}")
            return processed_earnings
            
        except Exception as e:
            logger.error(f"❌ Error fetching earnings for {symbol}: {e}")
            return None
    
    async def _fetch_earnings_data(self, session: aiohttp.ClientSession, symbol: str, 
                                 start_date: str, end_date: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch actual earnings data from Polygon"""
        try:
            url = f"{self.base_url}/v2/reference/financials/{symbol}"
            
            params = {
                "apiKey": self.api_key,
                "limit": 1000,  # Maximum limit
                "type": "Q",  # Quarterly
                "sort": "period_of_report_date",
                "order": "desc"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Polygon API error for {symbol}: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("results"):
                    logger.warning(f"No earnings results for {symbol}")
                    return None
                
                # Filter by date range
                filtered_results = []
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                for result in data["results"]:
                    report_date = datetime.strptime(result.get("period_of_report_date", ""), "%Y-%m-%d")
                    if start_dt <= report_date <= end_dt:
                        filtered_results.append(result)
                
                logger.info(f"📈 Found {len(filtered_results)} earnings records for {symbol} in date range")
                return filtered_results
                
        except Exception as e:
            logger.error(f"Error fetching earnings data for {symbol}: {e}")
            return None
    
    async def _fetch_earnings_estimates(self, session: aiohttp.ClientSession, symbol: str,
                                      start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Fetch earnings estimates from Polygon"""
        try:
            url = f"{self.base_url}/v2/reference/financials/{symbol}"
            
            params = {
                "apiKey": self.api_key,
                "limit": 1000,
                "type": "Q",
                "sort": "period_of_report_date",
                "order": "desc"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Extract estimates data
                estimates = {}
                for result in data.get("results", []):
                    period_key = result.get("period_of_report_date", "")
                    if period_key:
                        estimates[period_key] = {
                            "eps_estimate": result.get("eps_estimate"),
                            "revenue_estimate": result.get("revenue_estimate")
                        }
                
                return estimates
                
        except Exception as e:
            logger.warning(f"Could not fetch estimates for {symbol}: {e}")
            return None
    
    async def _fetch_guidance(self, session: aiohttp.ClientSession, symbol: str,
                            start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Fetch forward guidance from Polygon"""
        try:
            # Polygon doesn't have a dedicated guidance endpoint, so we'll use news/search
            # to find guidance-related news articles
            url = f"{self.base_url}/v2/reference/news"
            
            params = {
                "apiKey": self.api_key,
                "ticker": symbol,
                "limit": 100,
                "order": "desc",
                "sort": "published_utc"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Filter for guidance-related articles
                guidance_articles = []
                guidance_keywords = ["guidance", "outlook", "forecast", "expectations", "projections"]
                
                for article in data.get("results", []):
                    title = article.get("title", "").lower()
                    description = article.get("description", "").lower()
                    
                    if any(keyword in title or keyword in description for keyword in guidance_keywords):
                        guidance_articles.append({
                            "date": article.get("published_utc", ""),
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("article_url", "")
                        })
                
                return {"articles": guidance_articles}
                
        except Exception as e:
            logger.warning(f"Could not fetch guidance for {symbol}: {e}")
            return None
    
    def _process_earnings_data(self, earnings_data: List[Dict[str, Any]], 
                              estimates_data: Optional[Dict[str, Any]],
                              guidance_data: Optional[Dict[str, Any]],
                              symbol: str) -> List[Dict[str, Any]]:
        """Process and combine earnings data"""
        processed_earnings = []
        
        for earnings in earnings_data:
            try:
                # Extract basic earnings info
                report_date = earnings.get("period_of_report_date", "")
                quarter = self._extract_quarter(report_date)
                year = self._extract_year(report_date)
                
                # Get estimates if available
                eps_estimate = None
                revenue_estimate = None
                if estimates_data and report_date in estimates_data:
                    eps_estimate = estimates_data[report_date].get("eps_estimate")
                    revenue_estimate = estimates_data[report_date].get("revenue_estimate")
                
                # Calculate surprises
                eps_surprise = None
                revenue_surprise = None
                actual_eps = earnings.get("eps_basic", earnings.get("eps_diluted"))
                actual_revenue = earnings.get("revenue")
                
                if eps_estimate and actual_eps:
                    eps_surprise = float(actual_eps) - float(eps_estimate)
                
                if revenue_estimate and actual_revenue:
                    revenue_surprise = float(actual_revenue) - float(revenue_estimate)
                
                # Process guidance
                guidance = None
                conference_call_date = None
                if guidance_data and guidance_data.get("articles"):
                    # Find guidance articles around this earnings date
                    guidance_articles = self._find_relevant_guidance(
                        guidance_data["articles"], report_date
                    )
                    if guidance_articles:
                        guidance = "; ".join([article["title"] for article in guidance_articles])
                
                processed_earnings.append({
                    "symbol": symbol,
                    "quarter": quarter,
                    "year": year,
                    "report_date": report_date,
                    "eps": actual_eps,
                    "revenue": actual_revenue,
                    "eps_estimate": eps_estimate,
                    "revenue_estimate": revenue_estimate,
                    "eps_surprise": eps_surprise,
                    "revenue_surprise": revenue_surprise,
                    "guidance": guidance,
                    "conference_call_date": conference_call_date,
                    "notes": f"Data from Polygon.io - {earnings.get('filing_date', 'N/A')}",
                    "source": "polygon",
                    "raw_data": earnings
                })
                
            except Exception as e:
                logger.error(f"Error processing earnings record for {symbol}: {e}")
                continue
        
        return processed_earnings
    
    def _extract_quarter(self, date_str: str) -> str:
        """Extract quarter from date string"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except:
            return "Q4"  # Default fallback
    
    def _extract_year(self, date_str: str) -> int:
        """Extract year from date string"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.year
        except:
            return datetime.now().year
    
    def _find_relevant_guidance(self, guidance_articles: List[Dict[str, Any]], 
                               earnings_date: str) -> List[Dict[str, Any]]:
        """Find guidance articles relevant to a specific earnings date"""
        try:
            earnings_dt = datetime.strptime(earnings_date, "%Y-%m-%d")
            relevant_articles = []
            
            for article in guidance_articles:
                try:
                    article_date = datetime.strptime(article["date"][:10], "%Y-%m-%d")
                    # Look for guidance within 30 days of earnings
                    if abs((earnings_dt - article_date).days) <= 30:
                        relevant_articles.append(article)
                except:
                    continue
            
            return relevant_articles
            
        except Exception as e:
            logger.warning(f"Error finding relevant guidance: {e}")
            return []


