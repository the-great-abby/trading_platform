#!/usr/bin/env python3
"""
15-Minute Market Data Manager
Handles fetching, storing, and retrieving 15-minute interval data from Polygon API
Stores data in TimescaleDB for efficient time series queries
"""

import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import logging
import psycopg2
from sqlalchemy import create_engine, text
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class FifteenMinuteDataManager:
    """
    Manages 15-minute interval market data
    
    Features:
    - Fetches data from Polygon API
    - Stores in TimescaleDB hypertable
    - Smart caching and incremental updates
    - Efficient time series queries
    """
    
    def __init__(self, 
                 timescale_url: str = None,
                 polygon_api_key: str = None,
                 cache_duration_hours: int = 24):
        
        load_dotenv()
        
        # TimescaleDB connection
        if timescale_url:
            self.timescale_url = timescale_url
        else:
            # Default to port-forwarded TimescaleDB
            self.timescale_url = "postgresql://postgres:postgres@localhost:13001/trading_bot"
        
        # Polygon API
        self.polygon_api_key = polygon_api_key or os.getenv('POLYGON_API_KEY')
        if not self.polygon_api_key:
            raise ValueError("Polygon API key not found. Set POLYGON_API_KEY environment variable.")
        
        self.cache_duration_hours = cache_duration_hours
        self.polygon_base_url = "https://api.polygon.io"
        
        # Create database engine
        self.engine = create_engine(self.timescale_url)
        
        logger.info(f"🎯 15-Minute Data Manager initialized")
        logger.info(f"   TimescaleDB: {self.timescale_url.split('@')[1] if '@' in self.timescale_url else 'configured'}")
        logger.info(f"   Polygon API: {'✅ Key loaded' if self.polygon_api_key else '❌ No key'}")
    
    async def fetch_15min_data(self, 
                              symbol: str, 
                              start_date: datetime, 
                              end_date: datetime,
                              force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch 15-minute data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            start_date: Start date (datetime)
            end_date: End date (datetime)
            force_refresh: Force API fetch even if data exists
            
        Returns:
            DataFrame with 15-minute OHLCV data
        """
        
        logger.info(f"📊 Fetching 15-minute data for {symbol} from {start_date.date()} to {end_date.date()}")
        
        # Check if we have recent data in database
        if not force_refresh:
            cached_data = await self._get_cached_15min_data(symbol, start_date, end_date)
            if cached_data is not None and len(cached_data) > 0:
                logger.info(f"✅ Using cached 15-minute data for {symbol} ({len(cached_data)} records)")
                return cached_data
        
        # Fetch from Polygon API
        api_data = await self._fetch_from_polygon_15min(symbol, start_date, end_date)
        
        if api_data is not None and len(api_data) > 0:
            # Store in TimescaleDB
            await self._store_15min_data(symbol, api_data)
            logger.info(f"💾 Stored {len(api_data)} 15-minute records for {symbol}")
            return api_data
        else:
            logger.warning(f"⚠️ No 15-minute data available for {symbol}")
            return None
    
    async def _fetch_from_polygon_15min(self, 
                                       symbol: str, 
                                       start_date: datetime, 
                                       end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch 15-minute data from Polygon API"""
        
        # Convert to timestamps (Polygon uses milliseconds)
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        url = f"{self.polygon_base_url}/v2/aggs/ticker/{symbol}/range/15/minute/{start_ts}/{end_ts}"
        
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000,  # Maximum limit
            'apikey': self.polygon_api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    logger.info(f"📈 Fetched {len(results)} 15-minute bars for {symbol}")
                    
                    # Convert to DataFrame
                    df_data = []
                    for bar in results:
                        df_data.append({
                            'timestamp': pd.to_datetime(bar['t'], unit='ms'),
                            'open': bar['o'],
                            'high': bar['h'],
                            'low': bar['l'],
                            'close': bar['c'],
                            'volume': bar['v']
                        })
                    
                    df = pd.DataFrame(df_data)
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    
                    return df
                else:
                    logger.warning(f"⚠️ No 15-minute data returned for {symbol}: {data.get('status')}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching 15-minute data for {symbol}: {e}")
            return None
    
    async def _store_15min_data(self, symbol: str, data: pd.DataFrame):
        """Store 15-minute data in TimescaleDB"""
        
        if data is None or len(data) == 0:
            return
        
        # Prepare data for database
        records = []
        for timestamp, row in data.iterrows():
            records.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        # Insert with conflict resolution (upsert)
        insert_sql = text("""
            INSERT INTO historical_prices_15m (symbol, timestamp, open, high, low, close, volume)
            VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
            ON CONFLICT (symbol, timestamp) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                created_at = NOW()
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(insert_sql, records)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Error storing 15-minute data for {symbol}: {e}")
    
    async def _get_cached_15min_data(self, 
                                    symbol: str, 
                                    start_date: datetime, 
                                    end_date: datetime) -> Optional[pd.DataFrame]:
        """Get cached 15-minute data from TimescaleDB"""
        
        query_sql = text("""
            SELECT timestamp, open, high, low, close, volume
            FROM historical_prices_15m
            WHERE symbol = :symbol
            AND timestamp >= :start_date
            AND timestamp <= :end_date
            ORDER BY timestamp ASC
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query_sql, {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                rows = result.fetchall()
                
                if rows:
                    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df.set_index('timestamp', inplace=True)
                    return df
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving cached 15-minute data for {symbol}: {e}")
            return None
    
    async def get_latest_15min_data(self, symbol: str, periods: int = 100) -> Optional[pd.DataFrame]:
        """Get the latest N periods of 15-minute data"""
        
        query_sql = text("""
            SELECT timestamp, open, high, low, close, volume
            FROM historical_prices_15m
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT :periods
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query_sql, {
                    'symbol': symbol,
                    'periods': periods
                })
                
                rows = result.fetchall()
                
                if rows:
                    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)  # Sort ascending for proper time series
                    return df
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving latest 15-minute data for {symbol}: {e}")
            return None
    
    async def get_data_coverage(self, symbol: str) -> Dict[str, Any]:
        """Get information about data coverage for a symbol"""
        
        query_sql = text("""
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date,
                MAX(created_at) as last_updated
            FROM historical_prices_15m
            WHERE symbol = :symbol
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query_sql, {'symbol': symbol})
                row = result.fetchone()
                
                if row:
                    return {
                        'symbol': symbol,
                        'total_records': row[0],
                        'earliest_date': row[1],
                        'latest_date': row[2],
                        'last_updated': row[3]
                    }
                else:
                    return {
                        'symbol': symbol,
                        'total_records': 0,
                        'earliest_date': None,
                        'latest_date': None,
                        'last_updated': None
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error getting data coverage for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old 15-minute data (keep last N days)"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        delete_sql = text("""
            DELETE FROM historical_prices_15m
            WHERE timestamp < :cutoff_date
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(delete_sql, {'cutoff_date': cutoff_date})
                deleted_count = result.rowcount
                conn.commit()
                
                logger.info(f"🗑️ Cleaned up {deleted_count} old 15-minute records")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up old 15-minute data: {e}")
            return 0


# Global instance
_fifteen_min_manager = None

def get_15min_data_manager() -> FifteenMinuteDataManager:
    """Get global 15-minute data manager instance"""
    global _fifteen_min_manager
    
    if _fifteen_min_manager is None:
        _fifteen_min_manager = FifteenMinuteDataManager()
    
    return _fifteen_min_manager
