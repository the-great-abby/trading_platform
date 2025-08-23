"""
Earnings Data Service

Main service for managing earnings data operations including:
- Fetching from multiple providers (Polygon, Alpha Vantage, Yahoo Finance)
- Database storage and retrieval
- Data aggregation and deduplication
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
import json

from .polygon_earnings_service import PolygonEarningsService
from .alpha_vantage_earnings_service import AlphaVantageEarningsService
from .yahoo_finance_earnings_service import YahooFinanceEarningsService

logger = logging.getLogger(__name__)

class EarningsDataService:
    """Main service for earnings data operations"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
        # Initialize provider services
        self.polygon_service = None
        self.alpha_vantage_service = None
        self.yahoo_service = None

    async def initialize(self, polygon_api_key: str = None, alpha_vantage_api_key: str = None):
        """Initialize the service and database connection"""
        try:
            # Initialize database connection pool
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("✅ Database connection pool created")

            # Initialize provider services
            if polygon_api_key:
                self.polygon_service = PolygonEarningsService(polygon_api_key)
                logger.info("✅ Polygon service initialized")

            if alpha_vantage_api_key:
                self.alpha_vantage_service = AlphaVantageEarningsService(alpha_vantage_api_key)
                logger.info("✅ Alpha Vantage service initialized")

            # Yahoo Finance doesn't require API key
            self.yahoo_service = YahooFinanceEarningsService()
            logger.info("✅ Yahoo Finance service initialized")

            # Ensure tables exist
            await self._ensure_tables_exist()
            logger.info("✅ Database tables verified")

        except Exception as e:
            logger.error(f"❌ Error initializing earnings data service: {e}")
            raise

    async def close(self):
        """Close database connections and provider services"""
        try:
            if self.pool:
                await self.pool.close()
                logger.info("✅ Database connection pool closed")

            if self.polygon_service:
                await self.polygon_service.close()

            if self.alpha_vantage_service:
                await self.alpha_vantage_service.close()

            if self.yahoo_service:
                await self.yahoo_service.close()

        except Exception as e:
            logger.error(f"❌ Error closing earnings data service: {e}")

    async def _ensure_tables_exist(self):
        """Ensure required database tables exist"""
        async with self.pool.acquire() as conn:
            # Create earnings_reports table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS earnings_reports (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    quarter VARCHAR(3) NOT NULL,
                    year INTEGER NOT NULL,
                    report_date DATE NOT NULL,
                    eps DECIMAL(10,4),
                    revenue DECIMAL(20,2),
                    eps_estimate DECIMAL(10,4),
                    revenue_estimate DECIMAL(20,2),
                    eps_surprise DECIMAL(10,4),
                    revenue_surprise DECIMAL(20,2),
                    surprise_percentage DECIMAL(10,4),
                    surprise DECIMAL(10,4),
                    guidance TEXT,
                    conference_call_date DATE,
                    notes TEXT,
                    source VARCHAR(50) NOT NULL,
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vectorized_at TIMESTAMP,
                    UNIQUE(symbol, quarter, year, source)
                )
            """)

            # Create index for efficient queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_earnings_reports_symbol_date 
                ON earnings_reports(symbol, report_date)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_earnings_reports_source 
                ON earnings_reports(source)
            """)

            logger.info("✅ Database tables and indexes verified")

    async def store_earnings_batch(self, symbol: str, earnings_data: List[Dict[str, Any]]) -> int:
        """Store a batch of earnings data for a symbol"""
        if not earnings_data:
            return 0

        stored_count = 0
        async with self.pool.acquire() as conn:
            for earnings in earnings_data:
                try:
                    # Check if record already exists
                    existing = await conn.fetchrow("""
                        SELECT id FROM earnings_reports 
                        WHERE symbol = $1 AND quarter = $2 AND year = $3 AND source = $4
                    """, symbol, earnings.get('quarter'), earnings.get('year'), earnings.get('source'))

                    if existing:
                        # Update existing record
                        await conn.execute("""
                            UPDATE earnings_reports SET
                                eps = $1, revenue = $2, eps_estimate = $3, revenue_estimate = $4,
                                eps_surprise = $5, revenue_surprise = $6, surprise_percentage = $7,
                                surprise = $8, guidance = $9, conference_call_date = $10,
                                notes = $11, raw_data = $12, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $13
                        """, earnings.get('eps'), earnings.get('revenue'), earnings.get('eps_estimate'),
                              earnings.get('revenue_estimate'), earnings.get('eps_surprise'),
                              earnings.get('revenue_surprise'), earnings.get('surprise_percentage'),
                              earnings.get('surprise'), earnings.get('guidance'),
                              earnings.get('conference_call_date'), earnings.get('notes'),
                              json.dumps(earnings.get('raw_data', {})), existing['id'])
                    else:
                        # Insert new record
                        await conn.execute("""
                            INSERT INTO earnings_reports (
                                symbol, quarter, year, report_date, eps, revenue, eps_estimate,
                                revenue_estimate, eps_surprise, revenue_surprise, surprise_percentage,
                                surprise, guidance, conference_call_date, notes, source, raw_data
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                        """, symbol, earnings.get('quarter'), earnings.get('year'),
                              earnings.get('report_date'), earnings.get('eps'), earnings.get('revenue'),
                              earnings.get('eps_estimate'), earnings.get('revenue_estimate'),
                              earnings.get('eps_surprise'), earnings.get('revenue_surprise'),
                              earnings.get('surprise_percentage'), earnings.get('surprise'),
                              earnings.get('guidance'), earnings.get('conference_call_date'),
                              earnings.get('notes'), earnings.get('source'),
                              json.dumps(earnings.get('raw_data', {})))

                    stored_count += 1

                except Exception as e:
                    logger.error(f"❌ Error storing earnings record for {symbol}: {e}")
                    continue

        logger.info(f"💾 Stored {stored_count}/{len(earnings_data)} earnings records for {symbol}")
        return stored_count

    async def get_earnings_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get earnings data for a specific symbol"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM earnings_reports 
                    WHERE symbol = $1 
                    ORDER BY report_date DESC 
                    LIMIT $2
                """, symbol.upper(), limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Error getting earnings for {symbol}: {e}")
            return []

    async def get_symbols_with_earnings(self) -> List[str]:
        """Get list of symbols that have earnings data"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT symbol FROM earnings_reports 
                    ORDER BY symbol
                """)

                return [row['symbol'] for row in rows]

        except Exception as e:
            logger.error(f"❌ Error getting symbols with earnings: {e}")
            return []

    async def get_upcoming_earnings(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming earnings in the next N days"""
        try:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM earnings_reports 
                    WHERE report_date BETWEEN CURRENT_DATE AND $1
                    ORDER BY report_date ASC
                """, end_date.date())

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Error getting upcoming earnings: {e}")
            return []

    async def get_earnings_summary(self, symbol: str = None) -> Dict[str, Any]:
        """Get summary statistics for earnings data"""
        try:
            async with self.pool.acquire() as conn:
                if symbol:
                    # Summary for specific symbol
                    total_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM earnings_reports WHERE symbol = $1
                    """, symbol.upper())
                    
                    latest_date = await conn.fetchval("""
                        SELECT MAX(report_date) FROM earnings_reports WHERE symbol = $1
                    """, symbol.upper())
                    
                    earliest_date = await conn.fetchval("""
                        SELECT MIN(report_date) FROM earnings_reports WHERE symbol = $1
                    """, symbol.upper())
                else:
                    # Overall summary
                    total_count = await conn.fetchval("SELECT COUNT(*) FROM earnings_reports")
                    
                    latest_date = await conn.fetchval("SELECT MAX(report_date) FROM earnings_reports")
                    
                    earliest_date = await conn.fetchval("SELECT MIN(report_date) FROM earnings_reports")

                return {
                    "total_count": total_count or 0,
                    "latest_date": latest_date.isoformat() if latest_date else None,
                    "earliest_date": earliest_date.isoformat() if earliest_date else None,
                    "symbol": symbol
                }

        except Exception as e:
            logger.error(f"❌ Error getting earnings summary: {e}")
            return {}

    async def get_earnings_by_date_range(self, start_date: str, end_date: str, 
                                       symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Get earnings data within a date range"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM earnings_reports 
                    WHERE report_date BETWEEN $1 AND $2
                """
                params = [start_date, end_date]

                if symbols:
                    query += " AND symbol = ANY($3)"
                    params.append(symbols)

                query += " ORDER BY report_date DESC, symbol"

                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Error getting earnings by date range: {e}")
            return []

    async def get_earnings_surprises(self, min_surprise_percent: float = 5.0, 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """Get earnings surprises above a threshold"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM earnings_reports 
                    WHERE ABS(surprise_percentage) >= $1 
                    AND surprise_percentage IS NOT NULL
                    ORDER BY ABS(surprise_percentage) DESC 
                    LIMIT $2
                """, min_surprise_percent, limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Error getting earnings surprises: {e}")
            return []

    async def cleanup_old_data(self, days_to_keep: int = 1095) -> int:
        """Clean up earnings data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM earnings_reports 
                    WHERE report_date < $1
                """, cutoff_date.date())

                deleted_count = int(result.split()[-1])
                logger.info(f"🧹 Cleaned up {deleted_count} old earnings records")
                return deleted_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up old earnings data: {e}")
            return 0


