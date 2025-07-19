"""
Database Service for Market Data Storage and Retrieval
"""

import os
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple, Any
from sqlalchemy import create_engine, text, Column, String, Float, Integer, Date, DateTime, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from ...models.market_data import Base, HistoricalPrice, MarketDataCache
from ...utils.database_optimizer import DatabaseOptimizer

logger = logging.getLogger(__name__)

Base = declarative_base()

class OptionContractCache(Base):
    __tablename__ = 'options_contracts_cache'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    expiration = Column(String, index=True)
    strike = Column(Float)
    option_type = Column(String)
    price = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    implied_volatility = Column(Float)
    cache_date = Column(Date, default=lambda: datetime.date.today(), index=True)
    last_updated = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


class HistoricalOptionsSnapshot(Base):
    __tablename__ = 'historical_options_snapshots'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    snapshot_date = Column(Date, index=True)  # Date when snapshot was taken
    expiration = Column(String, index=True)
    strike = Column(Float)
    option_type = Column(String)
    price = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    implied_volatility = Column(Float)
    underlying_price = Column(Float)  # Stock price when snapshot was taken
    data_source = Column(String)  # Source of the data (polygon, etc.)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


class MarketDataService:
    """Service for managing market data - wrapper around MarketDataDatabaseService"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.db_service = MarketDataDatabaseService(database_url)
    
    def store_historical_data(self, symbol: str, data: pd.DataFrame, provider: str, interval: str = '1d') -> bool:
        """Store historical market data"""
        return self.db_service.store_historical_data(symbol, data, provider, interval)
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          provider: Optional[str] = None, interval: str = '1d') -> Optional[pd.DataFrame]:
        """Retrieve historical data"""
        return self.db_service.get_historical_data(symbol, start_date, end_date, provider, interval)
    
    def get_missing_dates(self, symbol: str, start_date: date, end_date: date, 
                         provider: Optional[str] = None, interval: str = '1d') -> List[date]:
        """Find missing dates"""
        return self.db_service.get_missing_dates(symbol, start_date, end_date, provider, interval)
    
    def get_cache_status(self, symbol: str, provider: Optional[str] = None) -> Dict:
        """Get cache status"""
        return self.db_service.get_cache_status(symbol, provider)
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Cleanup old data"""
        return self.db_service.cleanup_old_data(days_to_keep)
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols"""
        return self.db_service.get_all_symbols()
    
    def get_all_data_for_symbol(self, symbol: str, provider: Optional[str] = None, interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get all data for a symbol"""
        return self.db_service.get_all_data_for_symbol(symbol, provider, interval)
    
    # Historical options methods
    def store_historical_options_snapshot(self, symbol: str, contracts: List[Dict], snapshot_date: date, 
                                       underlying_price: float, data_source: str = "polygon") -> bool:
        """Store historical options snapshot"""
        return self.db_service.store_historical_options_snapshot(symbol, contracts, snapshot_date, underlying_price, data_source)
    
    def get_historical_options_data(self, symbol: str, snapshot_date: date, 
                                  expiration_date: Optional[str] = None) -> Optional[List[Dict]]:
        """Get historical options data for a specific date"""
        return self.db_service.get_historical_options_data(symbol, snapshot_date, expiration_date)
    
    def get_historical_options_date_range(self, symbol: str, start_date: date, end_date: date,
                                        expiration_date: Optional[str] = None) -> Optional[List[Dict]]:
        """Get historical options data for a date range"""
        return self.db_service.get_historical_options_date_range(symbol, start_date, end_date, expiration_date)
    
    def get_available_historical_dates(self, symbol: str) -> List[date]:
        """Get list of available historical snapshot dates for a symbol"""
        return self.db_service.get_available_historical_dates(symbol)
    
    def cleanup_old_historical_options(self, days_to_keep: int = 730) -> int:
        """Cleanup old historical options data (keep 2 years by default)"""
        return self.db_service.cleanup_old_historical_options(days_to_keep)


class MarketDataDatabaseService:
    """Database service for market data storage and retrieval"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
        # Initialize database optimizer
        self.optimizer = DatabaseOptimizer(self.database_url)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close database session"""
        session.close()
    
    def store_historical_data(self, symbol: str, data: pd.DataFrame, provider: str, interval: str = '1d') -> bool:
        """
        Store historical market data in database
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            provider: Data provider name
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if data.empty:
            logger.warning(f"No data to store for {symbol}")
            return False
        
        session = self.get_session()
        try:
            # Convert DataFrame to database records
            records = []
            for index, row in data.iterrows():
                # Handle different date formats
                if hasattr(index, 'date'):
                    record_date = index.date()
                elif isinstance(index, str):
                    record_date = datetime.strptime(index, '%Y-%m-%d').date()
                else:
                    record_date = index
                
                # Create record
                record = HistoricalPrice(
                    symbol=symbol,
                    date=record_date,
                    open_price=float(row.get('Open', row.get('open', 0))),
                    high_price=float(row.get('High', row.get('high', 0))),
                    low_price=float(row.get('Low', row.get('low', 0))),
                    close_price=float(row.get('Close', row.get('close', 0))),
                    volume=int(row.get('Volume', row.get('volume', 0))),
                    provider=provider,
                    interval=interval
                )
                records.append(record)
            
            # Use upsert to handle duplicates
            for record in records:
                session.merge(record)
            
            session.commit()
            
            # Update cache metadata
            self._update_cache_metadata(symbol, provider, interval, data)
            
            logger.info(f"Stored {len(records)} records for {symbol} from {provider}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error storing data for {symbol}: {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing data for {symbol}: {e}")
            return False
        finally:
            session.close()
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          provider: Optional[str] = None, interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        Retrieve historical data from database
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            provider: Optional provider filter
            interval: Data interval
            
        Returns:
            DataFrame with historical data or None if not found
        """
        session = self.get_session()
        try:
            query = session.query(HistoricalPrice).filter(
                HistoricalPrice.symbol == symbol,
                HistoricalPrice.date >= start_date,
                HistoricalPrice.date <= end_date,
                HistoricalPrice.interval == interval
            )
            
            if provider:
                query = query.filter(HistoricalPrice.provider == provider)
            
            records = query.order_by(HistoricalPrice.date).all()
            
            if not records:
                logger.info(f"No historical data found for {symbol} from {start_date} to {end_date}")
                return None
            
            # Convert to DataFrame
            data = []
            for record in records:
                data.append({
                    'Open': record.open_price,
                    'High': record.high_price,
                    'Low': record.low_price,
                    'Close': record.close_price,
                    'Volume': record.volume,
                    'Symbol': record.symbol,
                    'Provider': record.provider
                })
            
            df = pd.DataFrame(data)
            df['Date'] = [record.date for record in records]
            df.set_index('Date', inplace=True)
            
            logger.info(f"Retrieved {len(records)} records for {symbol} from database")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving data for {symbol}: {e}")
            return None
        finally:
            session.close()
    
    def get_missing_dates(self, symbol: str, start_date: date, end_date: date, 
                         provider: Optional[str] = None, interval: str = '1d') -> List[date]:
        """
        Find missing dates in the database for a given range
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            provider: Optional provider filter
            interval: Data interval
            
        Returns:
            List of missing dates
        """
        session = self.get_session()
        try:
            # Get existing dates
            query = session.query(HistoricalPrice.date).filter(
                HistoricalPrice.symbol == symbol,
                HistoricalPrice.date >= start_date,
                HistoricalPrice.date <= end_date,
                HistoricalPrice.interval == interval
            )
            
            if provider:
                query = query.filter(HistoricalPrice.provider == provider)
            
            existing_dates = {record.date for record in query.all()}
            
            # Generate all dates in range
            all_dates = []
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends (optional - you can remove this for crypto or 24/7 markets)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    all_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # Find missing dates
            missing_dates = [d for d in all_dates if d not in existing_dates]
            
            logger.info(f"Found {len(missing_dates)} missing dates for {symbol}")
            return missing_dates
            
        except SQLAlchemyError as e:
            logger.error(f"Database error finding missing dates for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error finding missing dates for {symbol}: {e}")
            return []
        finally:
            session.close()
    
    def _update_cache_metadata(self, symbol: str, provider: str, interval: str, data: pd.DataFrame):
        """Update cache metadata table"""
        session = self.get_session()
        try:
            # Get date range from data
            dates = [d.date() if hasattr(d, 'date') else d for d in data.index]
            earliest_date = min(dates)
            latest_date = max(dates)
            
            # Update or create cache record
            cache_record = session.query(MarketDataCache).filter(
                MarketDataCache.symbol == symbol,
                MarketDataCache.provider == provider,
                MarketDataCache.interval == interval
            ).first()
            
            if cache_record:
                # Update existing record
                cache_record.earliest_date = min(cache_record.earliest_date or earliest_date, earliest_date)
                cache_record.latest_date = max(cache_record.latest_date or latest_date, latest_date)
                cache_record.total_records = session.query(HistoricalPrice).filter(
                    HistoricalPrice.symbol == symbol,
                    HistoricalPrice.provider == provider,
                    HistoricalPrice.interval == interval
                ).count()
                cache_record.last_updated = datetime.now()
            else:
                # Create new record
                cache_record = MarketDataCache(
                    symbol=symbol,
                    provider=provider,
                    interval=interval,
                    earliest_date=earliest_date,
                    latest_date=latest_date,
                    total_records=len(data),
                    last_updated=datetime.now()
                )
                session.add(cache_record)
            
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating cache metadata: {e}")
        finally:
            session.close()
    
    def get_cache_status(self, symbol: str, provider: Optional[str] = None) -> Dict:
        """Get cache status for a symbol"""
        session = self.get_session()
        try:
            query = session.query(MarketDataCache).filter(MarketDataCache.symbol == symbol)
            if provider:
                query = query.filter(MarketDataCache.provider == provider)
            
            cache_records = query.all()
            
            status = {
                'symbol': symbol,
                'providers': {}
            }
            
            for record in cache_records:
                status['providers'][record.provider] = {
                    'interval': record.interval,
                    'earliest_date': record.earliest_date.isoformat() if record.earliest_date else None,
                    'latest_date': record.latest_date.isoformat() if record.latest_date else None,
                    'total_records': record.total_records,
                    'last_updated': record.last_updated.isoformat() if record.last_updated else None
                }
            
            return status
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting cache status: {e}")
            return {'symbol': symbol, 'error': str(e)}
        finally:
            session.close()
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Clean up old data (keep last N days)"""
        session = self.get_session()
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            # Delete old records
            deleted_count = session.query(HistoricalPrice).filter(
                HistoricalPrice.date < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error cleaning up old data: {e}")
            return 0
        finally:
            session.close()
    
    def get_all_symbols(self) -> List[str]:
        """Get all unique symbols in the database"""
        session = self.get_session()
        try:
            symbols = session.query(HistoricalPrice.symbol).distinct().all()
            return [symbol[0] for symbol in symbols]
        except SQLAlchemyError as e:
            logger.error(f"Error getting all symbols: {e}")
            return []
        finally:
            session.close()
    
    def get_all_data_for_symbol(self, symbol: str, provider: Optional[str] = None, interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get all historical data for a symbol"""
        session = self.get_session()
        try:
            query = session.query(HistoricalPrice).filter(HistoricalPrice.symbol == symbol)
            
            if provider:
                query = query.filter(HistoricalPrice.provider == provider)
            
            query = query.filter(HistoricalPrice.interval == interval)
            records = query.order_by(HistoricalPrice.date).all()
            
            if not records:
                return None
            
            # Convert to DataFrame
            data = []
            for record in records:
                data.append({
                    'Open': record.open_price,
                    'High': record.high_price,
                    'Low': record.low_price,
                    'Close': record.close_price,
                    'Volume': record.volume,
                    'Symbol': record.symbol,
                    'Provider': record.provider
                })
            
            df = pd.DataFrame(data)
            df['Date'] = [record.date for record in records]
            df.set_index('Date', inplace=True)
            
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all data for {symbol}: {e}")
            return None
        finally:
            session.close()
    
    # Historical options methods
    def store_historical_options_snapshot(self, symbol: str, contracts: List[Dict], snapshot_date: date, 
                                       underlying_price: float, data_source: str = "polygon") -> bool:
        """
        Store historical options snapshot
        
        Args:
            symbol: Stock symbol
            contracts: List of option contracts as dictionaries
            snapshot_date: Date when snapshot was taken
            underlying_price: Stock price when snapshot was taken
            data_source: Source of the data
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            # Delete existing snapshots for this symbol and date to avoid duplicates
            session.query(HistoricalOptionsSnapshot).filter(
                HistoricalOptionsSnapshot.symbol == symbol,
                HistoricalOptionsSnapshot.snapshot_date == snapshot_date
            ).delete()
            
            # Insert new snapshots
            for contract in contracts:
                snapshot = HistoricalOptionsSnapshot(
                    symbol=symbol,
                    snapshot_date=snapshot_date,
                    expiration=str(contract.get('expiration', '')),
                    strike=float(contract.get('strike', 0.0)),
                    option_type=str(contract.get('option_type', '')),
                    price=float(contract.get('price', 0.0)),
                    volume=int(contract.get('volume', 0)),
                    open_interest=int(contract.get('open_interest', 0)),
                    delta=float(contract.get('delta', 0.0)) if contract.get('delta') is not None else None,
                    gamma=float(contract.get('gamma', 0.0)) if contract.get('gamma') is not None else None,
                    theta=float(contract.get('theta', 0.0)) if contract.get('theta') is not None else None,
                    vega=float(contract.get('vega', 0.0)) if contract.get('vega') is not None else None,
                    implied_volatility=float(contract.get('implied_volatility', 0.0)) if contract.get('implied_volatility') is not None else None,
                    underlying_price=underlying_price,
                    data_source=data_source
                )
                session.add(snapshot)
            
            session.commit()
            logger.info(f"Stored {len(contracts)} historical options contracts for {symbol} on {snapshot_date}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error storing historical options for {symbol}: {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing historical options for {symbol}: {e}")
            return False
        finally:
            session.close()
    
    def get_historical_options_data(self, symbol: str, snapshot_date: date, 
                                  expiration_date: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get historical options data for a specific date
        
        Args:
            symbol: Stock symbol
            snapshot_date: Date of the snapshot
            expiration_date: Optional expiration date filter
            
        Returns:
            List of option contracts or None if not found
        """
        session = self.get_session()
        try:
            query = session.query(HistoricalOptionsSnapshot).filter(
                HistoricalOptionsSnapshot.symbol == symbol,
                HistoricalOptionsSnapshot.snapshot_date == snapshot_date
            )
            
            if expiration_date:
                query = query.filter(HistoricalOptionsSnapshot.expiration == expiration_date)
            
            snapshots = query.all()
            
            if not snapshots:
                logger.info(f"No historical options data found for {symbol} on {snapshot_date}")
                return None
            
            # Convert to list of dictionaries
            contracts = []
            for snapshot in snapshots:
                contracts.append({
                    'symbol': snapshot.symbol,
                    'expiration': snapshot.expiration,
                    'strike': snapshot.strike,
                    'option_type': snapshot.option_type,
                    'price': snapshot.price,
                    'volume': snapshot.volume,
                    'open_interest': snapshot.open_interest,
                    'delta': snapshot.delta,
                    'gamma': snapshot.gamma,
                    'theta': snapshot.theta,
                    'vega': snapshot.vega,
                    'implied_volatility': snapshot.implied_volatility,
                    'underlying_price': snapshot.underlying_price,
                    'data_source': snapshot.data_source,
                    'snapshot_date': snapshot.snapshot_date.isoformat()
                })
            
            logger.info(f"Retrieved {len(contracts)} historical options contracts for {symbol} on {snapshot_date}")
            return contracts
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving historical options for {symbol}: {e}")
            return None
        finally:
            session.close()
    
    def get_historical_options_date_range(self, symbol: str, start_date: date, end_date: date,
                                        expiration_date: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get historical options data for a date range
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            expiration_date: Optional expiration date filter
            
        Returns:
            List of option contracts or None if not found
        """
        session = self.get_session()
        try:
            query = session.query(HistoricalOptionsSnapshot).filter(
                HistoricalOptionsSnapshot.symbol == symbol,
                HistoricalOptionsSnapshot.snapshot_date >= start_date,
                HistoricalOptionsSnapshot.snapshot_date <= end_date
            )
            
            if expiration_date:
                query = query.filter(HistoricalOptionsSnapshot.expiration == expiration_date)
            
            snapshots = query.order_by(HistoricalOptionsSnapshot.snapshot_date).all()
            
            if not snapshots:
                logger.info(f"No historical options data found for {symbol} from {start_date} to {end_date}")
                return None
            
            # Convert to list of dictionaries
            contracts = []
            for snapshot in snapshots:
                contracts.append({
                    'symbol': snapshot.symbol,
                    'expiration': snapshot.expiration,
                    'strike': snapshot.strike,
                    'option_type': snapshot.option_type,
                    'price': snapshot.price,
                    'volume': snapshot.volume,
                    'open_interest': snapshot.open_interest,
                    'delta': snapshot.delta,
                    'gamma': snapshot.gamma,
                    'theta': snapshot.theta,
                    'vega': snapshot.vega,
                    'implied_volatility': snapshot.implied_volatility,
                    'underlying_price': snapshot.underlying_price,
                    'data_source': snapshot.data_source,
                    'snapshot_date': snapshot.snapshot_date.isoformat()
                })
            
            logger.info(f"Retrieved {len(contracts)} historical options contracts for {symbol} from {start_date} to {end_date}")
            return contracts
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving historical options range for {symbol}: {e}")
            return None
        finally:
            session.close()
    
    def get_available_historical_dates(self, symbol: str) -> List[date]:
        """
        Get list of available historical snapshot dates for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of available dates
        """
        session = self.get_session()
        try:
            dates = session.query(HistoricalOptionsSnapshot.snapshot_date).filter(
                HistoricalOptionsSnapshot.symbol == symbol
            ).distinct().order_by(HistoricalOptionsSnapshot.snapshot_date).all()
            
            return [d.snapshot_date for d in dates]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting available dates for {symbol}: {e}")
            return []
        finally:
            session.close()
    
    def cleanup_old_historical_options(self, days_to_keep: int = 730) -> int:
        """
        Cleanup old historical options data
        
        Args:
            days_to_keep: Number of days to keep (default 2 years)
            
        Returns:
            Number of records deleted
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            deleted_count = session.query(HistoricalOptionsSnapshot).filter(
                HistoricalOptionsSnapshot.snapshot_date < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_count} old historical options records")
            return deleted_count
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error cleaning up historical options: {e}")
            return 0
        finally:
            session.close() 