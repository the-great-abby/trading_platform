"""
Yahoo Finance Earnings Service

Fetches quarterly earnings reports from Yahoo Finance including:
- EPS and revenue data
- Earnings estimates and surprises
- Forward guidance
"""

import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import re

logger = logging.getLogger(__name__)

class YahooFinanceEarningsService:
    """Service for fetching earnings data from Yahoo Finance"""

    def __init__(self, api_key: str = None):
        # Yahoo Finance doesn't require an API key for basic data
        self.api_key = api_key
        self.base_url = "https://query2.finance.yahoo.com/v10/finance"
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
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
            logger.info(f"📊 Fetching earnings for {symbol} from Yahoo Finance")

            session = await self._get_session()

            # First, get the quote to find the ticker ID
            ticker_id = await self._get_ticker_id(session, symbol)
            if not ticker_id:
                logger.error(f"Could not find ticker ID for {symbol}")
                return None

            # Fetch earnings data
            earnings_data = await self._fetch_earnings_data(session, ticker_id, symbol)
            if not earnings_data:
                logger.warning(f"No earnings data returned for {symbol}")
                return None

            # Filter by date range
            filtered_earnings = self._filter_by_date_range(earnings_data, start_date, end_date)

            # Process the data
            processed_earnings = self._process_earnings_data(filtered_earnings, symbol)

            logger.info(f"✅ Successfully processed {len(processed_earnings)} earnings records for {symbol}")
            return processed_earnings

        except Exception as e:
            logger.error(f"❌ Error fetching earnings for {symbol}: {e}")
            return None

    async def _get_ticker_id(self, session: aiohttp.ClientSession, symbol: str) -> Optional[str]:
        """Get the internal ticker ID for a symbol"""
        try:
            # Use the quote endpoint to get ticker info
            url = f"{self.base_url}/quoteSummary/{symbol}"
            params = {
                "modules": "assetProfile",
                "formatted": "true"
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Could not get ticker info for {symbol}: {response.status}")
                    return symbol  # Fallback to using symbol directly

                data = await response.json()
                # For now, just return the symbol as the ticker ID
                # Yahoo Finance API can work with symbols directly
                return symbol

        except Exception as e:
            logger.warning(f"Error getting ticker ID for {symbol}: {e}")
            return symbol

    async def _fetch_earnings_data(self, session: aiohttp.ClientSession, ticker_id: str, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch earnings data from Yahoo Finance"""
        try:
            # Use the earnings endpoint
            url = f"{self.base_url}/quoteSummary/{ticker_id}"
            params = {
                "modules": "earningsHistory,earningsTrend,earnings",
                "formatted": "true"
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Yahoo Finance API error for {symbol}: {response.status}")
                    return None

                data = await response.json()

                if "error" in data:
                    logger.error(f"Yahoo Finance error for {symbol}: {data['error']}")
                    return None

                # Extract earnings data from different modules
                earnings_data = []

                # Get earnings history
                earnings_history = data.get("earningsHistory", {}).get("history", [])
                if earnings_history:
                    earnings_data.extend(earnings_history)

                # Get earnings trends
                earnings_trend = data.get("earningsTrend", {}).get("trend", [])
                if earnings_trend:
                    # Convert trends to history-like format
                    for trend in earnings_trend:
                        if trend.get("endDate"):
                            earnings_data.append({
                                "endDate": trend.get("endDate"),
                                "estimate": trend.get("estimate"),
                                "actual": trend.get("actual"),
                                "surprise": trend.get("surprise"),
                                "surprisePercent": trend.get("surprisePercent")
                            })

                if not earnings_data:
                    logger.warning(f"No earnings data found for {symbol}")
                    return None

                logger.info(f"📈 Found {len(earnings_data)} earnings records for {symbol}")
                return earnings_data

        except Exception as e:
            logger.error(f"Error fetching earnings data for {symbol}: {e}")
            return None

    def _filter_by_date_range(self, earnings_data: List[Dict[str, Any]], 
                             start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Filter earnings data by date range"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            filtered_results = []

            for earnings in earnings_data:
                try:
                    # Yahoo Finance uses "endDate" format like "2023-12-31"
                    report_date = datetime.strptime(earnings.get("endDate", ""), "%Y-%m-%d")
                    if start_dt <= report_date <= end_dt:
                        filtered_results.append(earnings)
                except:
                    continue

            logger.info(f"📅 Filtered to {len(filtered_results)} earnings in date range")
            return filtered_results

        except Exception as e:
            logger.warning(f"Error filtering by date range: {e}")
            return earnings_data

    def _process_earnings_data(self, earnings_data: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """Process and format earnings data"""
        processed_earnings = []

        for earnings in earnings_data:
            try:
                # Extract basic earnings info
                report_date = earnings.get("endDate", "")
                quarter = self._extract_quarter(report_date)
                year = self._extract_year(report_date)

                # Extract financial data
                actual_eps = earnings.get("actual")
                estimated_eps = earnings.get("estimate")
                surprise = earnings.get("surprise")
                surprise_percent = earnings.get("surprisePercent")

                # Calculate surprises if not provided
                eps_surprise = surprise
                if not eps_surprise and estimated_eps and actual_eps:
                    try:
                        eps_surprise = float(actual_eps) - float(estimated_eps)
                    except:
                        pass

                processed_earnings.append({
                    "symbol": symbol,
                    "quarter": quarter,
                    "year": year,
                    "report_date": report_date,
                    "eps": actual_eps,
                    "revenue": None,  # Yahoo Finance doesn't always provide revenue
                    "eps_estimate": estimated_eps,
                    "revenue_estimate": None,
                    "eps_surprise": eps_surprise,
                    "revenue_surprise": None,
                    "surprise_percentage": surprise_percent,
                    "surprise": surprise,
                    "guidance": None,  # Yahoo Finance doesn't provide guidance
                    "conference_call_date": None,
                    "notes": f"Data from Yahoo Finance - {earnings.get('endDate', 'N/A')}",
                    "source": "yahoo_finance",
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

