"""
Options Data Cache - Historical options data caching system
Fetches and caches options data for improved performance
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import json
from dataclasses import dataclass
import asyncio
import aiohttp
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@dataclass
class OptionsContract:
    """Represents an options contract"""
    symbol: str
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    contract_id: str
    underlying_price: float
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class OptionsDataCache:
    """Historical options data caching system"""
    
    def __init__(self, database_url: str, cache_dir: str = "cache/options"):
        self.database_url = database_url
        self.cache_dir = cache_dir
        self.engine = create_engine(database_url)
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize cache tables
        self._init_cache_tables()
        
        # Cache statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'total_requests': 0
        }
    
    def _init_cache_tables(self):
        """Initialize cache tables in database"""
        try:
            with self.engine.connect() as conn:
                # Options contracts cache table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS options_contracts_cache (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL,
                        strike DECIMAL(10,2) NOT NULL,
                        expiration_date DATE NOT NULL,
                        option_type VARCHAR(4) NOT NULL,
                        contract_id VARCHAR(50) UNIQUE NOT NULL,
                        underlying_price DECIMAL(10,2),
                        last_price DECIMAL(10,4),
                        bid DECIMAL(10,4),
                        ask DECIMAL(10,4),
                        volume INTEGER,
                        open_interest INTEGER,
                        implied_volatility DECIMAL(10,6),
                        delta DECIMAL(10,6),
                        gamma DECIMAL(10,6),
                        theta DECIMAL(10,6),
                        vega DECIMAL(10,6),
                        rho DECIMAL(10,6),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Options chain cache table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS options_chain_cache (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL,
                        date DATE NOT NULL,
                        chain_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, date)
                    )
                """))
                
                # Options historical data cache table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS options_historical_cache (
                        id SERIAL PRIMARY KEY,
                        contract_id VARCHAR(50) NOT NULL,
                        date DATE NOT NULL,
                        open DECIMAL(10,4),
                        high DECIMAL(10,4),
                        low DECIMAL(10,4),
                        close DECIMAL(10,4),
                        volume INTEGER,
                        open_interest INTEGER,
                        implied_volatility DECIMAL(10,6),
                        delta DECIMAL(10,6),
                        gamma DECIMAL(10,6),
                        theta DECIMAL(10,6),
                        vega DECIMAL(10,6),
                        rho DECIMAL(10,6),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(contract_id, date)
                    )
                """))
                
                conn.commit()
                logger.info("✅ Options cache tables initialized successfully")
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error initializing options cache tables: {e}")
    
    async def get_options_chain(self, symbol: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Get options chain for a symbol on a specific date"""
        self.stats['total_requests'] += 1
        
        # Check cache first
        cached_data = self._get_cached_options_chain(symbol, date)
        if cached_data:
            self.stats['cache_hits'] += 1
            logger.info(f"✅ Options chain cache hit for {symbol} on {date.date()}")
            return cached_data
        
        self.stats['cache_misses'] += 1
        logger.info(f"📥 Fetching options chain for {symbol} on {date.date()}")
        
        # Fetch from API (simulated for now)
        options_data = await self._fetch_options_chain(symbol, date)
        
        if options_data:
            # Cache the data
            self._cache_options_chain(symbol, date, options_data)
            self.stats['api_calls'] += 1
            return options_data
        
        return None
    
    async def get_contract_history(self, contract_id: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Get historical data for a specific options contract"""
        self.stats['total_requests'] += 1
        
        # Check cache first
        cached_data = self._get_cached_contract_history(contract_id, start_date, end_date)
        if cached_data is not None:
            self.stats['cache_hits'] += 1
            logger.info(f"✅ Contract history cache hit for {contract_id}")
            return cached_data
        
        self.stats['cache_misses'] += 1
        logger.info(f"📥 Fetching contract history for {contract_id}")
        
        # Fetch from API
        historical_data = await self._fetch_contract_history(contract_id, start_date, end_date)
        
        if historical_data is not None:
            # Cache the data
            self._cache_contract_history(contract_id, historical_data)
            self.stats['api_calls'] += 1
            return historical_data
        
        return None
    
    async def get_atm_options(self, symbol: str, date: datetime, days_to_expiry: int = 30) -> List[OptionsContract]:
        """Get at-the-money options for a symbol"""
        options_chain = await self.get_options_chain(symbol, date)
        if not options_chain:
            return []
        
        # Find ATM options (closest to current stock price)
        current_price = options_chain.get('underlying_price', 0)
        if current_price == 0:
            return []
        
        atm_options = []
        for contract in options_chain.get('contracts', []):
            # Check if expiration is within target range
            expiration = datetime.strptime(contract['expiration'], '%Y-%m-%d')
            days_diff = (expiration - date).days
            
            if days_diff <= days_to_expiry:
                # Find closest strike to current price
                strike_diff = abs(contract['strike'] - current_price)
                if strike_diff <= current_price * 0.05:  # Within 5% of current price
                    atm_options.append(OptionsContract(
                        symbol=contract['symbol'],
                        strike=contract['strike'],
                        expiration=expiration,
                        option_type=contract['option_type'],
                        contract_id=contract['contract_id'],
                        underlying_price=current_price,
                        last_price=contract.get('last_price', 0),
                        bid=contract.get('bid', 0),
                        ask=contract.get('ask', 0),
                        volume=contract.get('volume', 0),
                        open_interest=contract.get('open_interest', 0),
                        implied_volatility=contract.get('implied_volatility', 0),
                        delta=contract.get('delta', 0),
                        gamma=contract.get('gamma', 0),
                        theta=contract.get('theta', 0),
                        vega=contract.get('vega', 0),
                        rho=contract.get('rho', 0)
                    ))
        
        return atm_options
    
    def _get_cached_options_chain(self, symbol: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Get cached options chain data"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT chain_data FROM options_chain_cache 
                    WHERE symbol = :symbol AND date = :date
                """), {'symbol': symbol, 'date': date.date()})
                
                row = result.fetchone()
                if row:
                    chain_data = row[0]
                    # Handle both string and dict return types
                    if isinstance(chain_data, str):
                        return json.loads(chain_data)
                    elif isinstance(chain_data, dict):
                        return chain_data
                    else:
                        logger.warning(f"Unexpected data type for cached options chain: {type(chain_data)}")
                        return None
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting cached options chain: {e}")
            return None
    
    def _cache_options_chain(self, symbol: str, date: datetime, data: Dict[str, Any]):
        """Cache options chain data"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO options_chain_cache (symbol, date, chain_data)
                    VALUES (:symbol, :date, :chain_data)
                    ON CONFLICT (symbol, date) 
                    DO UPDATE SET chain_data = :chain_data, updated_at = CURRENT_TIMESTAMP
                """), {
                    'symbol': symbol,
                    'date': date.date(),
                    'chain_data': json.dumps(data)
                })
                conn.commit()
                logger.info(f"💾 Cached options chain for {symbol} on {date.date()}")
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error caching options chain: {e}")
    
    def _get_cached_contract_history(self, contract_id: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Get cached contract historical data"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT date, open, high, low, close, volume, open_interest,
                           implied_volatility, delta, gamma, theta, vega, rho
                    FROM options_historical_cache 
                    WHERE contract_id = :contract_id 
                    AND date BETWEEN :start_date AND :end_date
                    ORDER BY date
                """), {
                    'contract_id': contract_id,
                    'start_date': start_date.date(),
                    'end_date': end_date.date()
                })
                
                rows = result.fetchall()
                if rows:
                    df = pd.DataFrame(rows, columns=[
                        'date', 'open', 'high', 'low', 'close', 'volume', 'open_interest',
                        'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'
                    ])
                    df['date'] = pd.to_datetime(df['date'])
                    return df
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting cached contract history: {e}")
            return None
    
    def _cache_contract_history(self, contract_id: str, data: pd.DataFrame):
        """Cache contract historical data"""
        try:
            with self.engine.connect() as conn:
                for _, row in data.iterrows():
                    conn.execute(text("""
                        INSERT INTO options_historical_cache 
                        (contract_id, date, open, high, low, close, volume, open_interest,
                         implied_volatility, delta, gamma, theta, vega, rho)
                        VALUES (:contract_id, :date, :open, :high, :low, :close, :volume, :open_interest,
                                :implied_volatility, :delta, :gamma, :theta, :vega, :rho)
                        ON CONFLICT (contract_id, date) DO NOTHING
                    """), {
                        'contract_id': contract_id,
                        'date': row['date'].date(),
                        'open': row.get('open', 0),
                        'high': row.get('high', 0),
                        'low': row.get('low', 0),
                        'close': row.get('close', 0),
                        'volume': row.get('volume', 0),
                        'open_interest': row.get('open_interest', 0),
                        'implied_volatility': row.get('implied_volatility', 0),
                        'delta': row.get('delta', 0),
                        'gamma': row.get('gamma', 0),
                        'theta': row.get('theta', 0),
                        'vega': row.get('vega', 0),
                        'rho': row.get('rho', 0)
                    })
                conn.commit()
                logger.info(f"💾 Cached historical data for contract {contract_id}")
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error caching contract history: {e}")
    
    async def _fetch_options_chain(self, symbol: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Fetch options chain from API (simulated)"""
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Generate mock options chain data
        current_price = 100 + np.random.normal(0, 10)  # Mock stock price
        
        contracts = []
        strikes = np.arange(current_price * 0.8, current_price * 1.2, current_price * 0.05)
        expirations = [date + timedelta(days=30), date + timedelta(days=60), date + timedelta(days=90)]
        
        for strike in strikes:
            for expiration in expirations:
                for option_type in ['call', 'put']:
                    # Generate realistic options data
                    implied_vol = 0.3 + np.random.normal(0, 0.1)
                    delta = 0.5 + np.random.normal(0, 0.2) if option_type == 'call' else -0.5 + np.random.normal(0, 0.2)
                    
                    contracts.append({
                        'symbol': symbol,
                        'strike': round(strike, 2),
                        'expiration': expiration.strftime('%Y-%m-%d'),
                        'option_type': option_type,
                        'contract_id': f"{symbol}{expiration.strftime('%Y%m%d')}{strike}{option_type.upper()}",
                        'last_price': max(0.01, implied_vol * np.sqrt(expiration.day / 365) * current_price / 16),
                        'bid': max(0.01, implied_vol * np.sqrt(expiration.day / 365) * current_price / 16 * 0.95),
                        'ask': max(0.01, implied_vol * np.sqrt(expiration.day / 365) * current_price / 16 * 1.05),
                        'volume': np.random.randint(0, 1000),
                        'open_interest': np.random.randint(0, 5000),
                        'implied_volatility': implied_vol,
                        'delta': delta,
                        'gamma': np.random.normal(0.01, 0.005),
                        'theta': np.random.normal(-0.01, 0.005),
                        'vega': np.random.normal(0.1, 0.05),
                        'rho': np.random.normal(0.01, 0.005)
                    })
        
        return {
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'underlying_price': current_price,
            'contracts': contracts
        }
    
    async def _fetch_contract_history(self, contract_id: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch contract historical data from API (simulated)"""
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Generate mock historical data
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        base_price = 1.0  # Base option price
        
        for date in date_range:
            # Generate realistic price movements
            price_change = np.random.normal(0, 0.02)  # 2% daily volatility
            base_price *= (1 + price_change)
            
            open_price = base_price
            high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
            close_price = open_price * (1 + np.random.normal(0, 0.005))
            
            data.append({
                'date': date,
                'open': max(0.01, open_price),
                'high': max(0.01, high_price),
                'low': max(0.01, low_price),
                'close': max(0.01, close_price),
                'volume': np.random.randint(0, 1000),
                'open_interest': np.random.randint(0, 5000),
                'implied_volatility': 0.3 + np.random.normal(0, 0.05),
                'delta': 0.5 + np.random.normal(0, 0.1),
                'gamma': np.random.normal(0.01, 0.005),
                'theta': np.random.normal(-0.01, 0.005),
                'vega': np.random.normal(0.1, 0.05),
                'rho': np.random.normal(0.01, 0.005)
            })
        
        return pd.DataFrame(data)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            return self.stats
        
        hit_rate = (self.stats['cache_hits'] / total_requests) * 100
        
        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'miss_rate_percent': round(100 - hit_rate, 2)
        }
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for a specific symbol or all data"""
        try:
            with self.engine.connect() as conn:
                if symbol:
                    conn.execute(text("DELETE FROM options_chain_cache WHERE symbol = :symbol"), {'symbol': symbol})
                    conn.execute(text("DELETE FROM options_historical_cache WHERE contract_id LIKE :pattern"), 
                               {'pattern': f"{symbol}%"})
                    logger.info(f"🗑️  Cleared cache for symbol {symbol}")
                else:
                    conn.execute(text("DELETE FROM options_chain_cache"))
                    conn.execute(text("DELETE FROM options_historical_cache"))
                    logger.info("🗑️  Cleared all options cache")
                conn.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error clearing cache: {e}")
    
    def get_cache_size(self) -> Dict[str, int]:
        """Get cache size information"""
        try:
            with self.engine.connect() as conn:
                chain_count = conn.execute(text("SELECT COUNT(*) FROM options_chain_cache")).scalar()
                history_count = conn.execute(text("SELECT COUNT(*) FROM options_historical_cache")).scalar()
                
                return {
                    'options_chains': chain_count,
                    'historical_records': history_count,
                    'total_records': chain_count + history_count
                }
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting cache size: {e}")
            return {'options_chains': 0, 'historical_records': 0, 'total_records': 0}


# Global cache instance
_options_cache = None

def get_options_cache(database_url: Optional[str] = None) -> OptionsDataCache:
    """Get global options cache instance"""
    global _options_cache
    
    if _options_cache is None:
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/trading_db')
        
        _options_cache = OptionsDataCache(database_url)
    
    return _options_cache 