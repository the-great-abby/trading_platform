"""
Alpha Vantage Earnings Service

Fetches quarterly earnings reports from Alpha Vantage API including:
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

logger = logging.getLogger(__name__)

class AlphaVantageEarningsService:
    """Service for fetching earnings data from Alpha Vantage"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
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
            logger.info(f"📊 Fetching earnings for {symbol} from Alpha Vantage")

            session = await self._get_session()

            # Fetch earnings data
            earnings_data = await self._fetch_earnings_data(session, symbol)
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

    async def _fetch_earnings_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch earnings data from Alpha Vantage"""
        try:
            params = {
                "function": "EARNINGS",
                "symbol": symbol,
                "apikey": self.api_key
            }

            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Alpha Vantage API error for {symbol}: {response.status}")
                    return None

                data = await response.json()

                if "Error Message" in data:
                    logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                    return None

                if "Note" in data:
                    logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                    return None

                # Extract quarterly earnings
                quarterly_earnings = data.get("quarterlyEarnings", [])
                if not quarterly_earnings:
                    logger.warning(f"No quarterly earnings found for {symbol}")
                    return None

                logger.info(f"📈 Found {len(quarterly_earnings)} quarterly earnings for {symbol}")
                return quarterly_earnings

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
                    # Alpha Vantage uses "fiscalDateEnding" format like "2023-12-31"
                    report_date = datetime.strptime(earnings.get("fiscalDateEnding", ""), "%Y-%m-%d")
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
                report_date = earnings.get("fiscalDateEnding", "")
                quarter = self._extract_quarter(report_date)
                year = self._extract_year(report_date)

                # Extract financial data
                actual_eps = earnings.get("reportedEPS")
                actual_revenue = earnings.get("reportedRevenue")
                estimated_eps = earnings.get("estimatedEPS")
                estimated_revenue = earnings.get("estimatedRevenue")

                # Calculate surprises
                eps_surprise = None
                revenue_surprise = None

                if estimated_eps and actual_eps:
                    try:
                        eps_surprise = float(actual_eps) - float(estimated_eps)
                    except:
                        pass

                if estimated_revenue and actual_revenue:
                    try:
                        revenue_surprise = float(actual_revenue) - float(estimated_revenue)
                    except:
                        pass

                # Extract additional info
                surprise_percentage = earnings.get("surprisePercentage")
                surprise = earnings.get("surprise")

                processed_earnings.append({
                    "symbol": symbol,
                    "quarter": quarter,
                    "year": year,
                    "report_date": report_date,
                    "eps": actual_eps,
                    "revenue": actual_revenue,
                    "eps_estimate": estimated_eps,
                    "revenue_estimate": estimated_revenue,
                    "eps_surprise": eps_surprise,
                    "revenue_surprise": revenue_surprise,
                    "surprise_percentage": surprise_percentage,
                    "surprise": surprise,
                    "guidance": None,  # Alpha Vantage doesn't provide guidance
                    "conference_call_date": None,
                    "notes": f"Data from Alpha Vantage - {earnings.get('fiscalDateEnding', 'N/A')}",
                    "source": "alpha_vantage",
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

