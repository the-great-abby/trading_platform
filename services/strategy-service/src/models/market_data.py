"""
Market Data Models for PostgreSQL Storage
"""

from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Index, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional

Base = declarative_base()


class HistoricalPrice(Base):
    """Historical market data storage model"""
    
    __tablename__ = 'historical_prices'
    
    # Primary key: symbol + date ensures no duplicates
    symbol = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    
    # OHLCV data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Metadata
    provider = Column(String(50), nullable=False)  # 'yahoo', 'polygon', 'alpha_vantage'
    interval = Column(String(10), nullable=False, default='1d')  # '1d', '1h', '5m'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'date'),
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_provider_symbol', 'provider', 'symbol'),
        Index('idx_date_range', 'date'),
    )
    
    def __repr__(self):
        return f"<HistoricalPrice(symbol='{self.symbol}', date='{self.date}', close={self.close_price})>"
    
    @classmethod
    def from_dataframe_row(cls, symbol: str, row, provider: str = 'unknown', interval: str = '1d'):
        """Create instance from pandas DataFrame row"""
        return cls(
            symbol=symbol,
            date=row.name.date() if hasattr(row.name, 'date') else row.name,
            open_price=float(row.get('Open', row.get('open', 0))),
            high_price=float(row.get('High', row.get('high', 0))),
            low_price=float(row.get('Low', row.get('low', 0))),
            close_price=float(row.get('Close', row.get('close', 0))),
            volume=int(row.get('Volume', row.get('volume', 0))),
            provider=provider,
            interval=interval
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'provider': self.provider,
            'interval': self.interval
        }


class MarketDataCache(Base):
    """Cache metadata for tracking data freshness"""
    
    __tablename__ = 'market_data_cache'
    
    symbol = Column(String(10), nullable=False)
    provider = Column(String(50), nullable=False)
    interval = Column(String(10), nullable=False, default='1d')
    
    # Cache metadata
    earliest_date = Column(Date, nullable=True)
    latest_date = Column(Date, nullable=True)
    total_records = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'provider', 'interval'),
        Index('idx_cache_symbol', 'symbol'),
        Index('idx_cache_provider', 'provider'),
    )
    
    def __repr__(self):
        return f"<MarketDataCache(symbol='{self.symbol}', provider='{self.provider}', records={self.total_records})>" 