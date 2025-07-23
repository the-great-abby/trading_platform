"""
Enhanced Options Data Service with Historical Snapshots Support
"""

import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import time
from collections import defaultdict

from .options_data_service import OptionsDataService, OptionContract, CacheStats
from ..database.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


@dataclass
class HistoricalOptionsData:
    """Historical options data for backtesting"""
    symbol: str
    snapshot_date: date
    contracts: List[Dict]
    underlying_price: float
    data_source: str


class EnhancedOptionsDataService:
    """Enhanced options data service with historical snapshots support"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.options_service = OptionsDataService(api_key)
        self.market_data_service = MarketDataService()
        
        # Historical data configuration
        self.auto_snapshot_enabled = True
        self.snapshot_retention_days = 730  # 2 years
        self.snapshot_cleanup_interval = timedelta(days=30)
        self.last_cleanup = datetime.now()
        
        logger.info("Enhanced Options Data Service initialized")
    
    def get_current_options_data(self, symbol: str, expiration_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """Get current options data with automatic snapshot storage"""
        try:
            # Get current options data
            contracts = self.options_service.get_options_chain(symbol, expiration_date)
            
            if contracts and self.auto_snapshot_enabled:
                # Store snapshot for historical data
                self._store_current_snapshot(symbol, contracts)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting current options data for {symbol}: {e}")
            return None
    
    def _store_current_snapshot(self, symbol: str, contracts: List[OptionContract]) -> bool:
        """Store current options data as historical snapshot"""
        try:
            # Get current stock price for underlying
            from ..market_data.cached_market_data_manager import CachedMarketDataManager
            market_data_manager = CachedMarketDataManager()
            
            # Get today's stock price
            today = datetime.now().strftime("%Y-%m-%d")
            stock_data = market_data_manager.get_historical_data(symbol, today, today)
            
            underlying_price = 0.0
            if stock_data is not None and not stock_data.empty:
                underlying_price = float(stock_data.iloc[-1]['Close'])
            
            # Convert contracts to dictionaries
            contracts_dict = []
            for contract in contracts:
                contracts_dict.append({
                    'symbol': contract.symbol,
                    'expiration': contract.expiration,
                    'strike': contract.strike,
                    'option_type': contract.option_type,
                    'price': contract.price,
                    'volume': contract.volume,
                    'open_interest': contract.open_interest,
                    'delta': contract.delta,
                    'gamma': contract.gamma,
                    'theta': contract.theta,
                    'vega': contract.vega,
                    'implied_volatility': contract.implied_volatility
                })
            
            # Store snapshot
            snapshot_date = datetime.now().date()
            success = self.market_data_service.store_historical_options_snapshot(
                symbol=symbol,
                contracts=contracts_dict,
                snapshot_date=snapshot_date,
                underlying_price=underlying_price,
                data_source="polygon"
            )
            
            if success:
                logger.info(f"✅ Stored historical snapshot for {symbol} on {snapshot_date} with {len(contracts)} contracts")
            else:
                logger.warning(f"⚠️ Failed to store historical snapshot for {symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing historical snapshot for {symbol}: {e}")
            return False
    
    def get_historical_options_data(self, symbol: str, snapshot_date: date, 
                                  expiration_date: Optional[str] = None) -> Optional['HistoricalOptionsData']:
        """Get historical options data for a specific date"""
        try:
            # Ensure snapshot_date is a date object, not datetime, and not None
            if snapshot_date is None:
                logger.error(f"snapshot_date cannot be None for {symbol}")
                return None
            elif isinstance(snapshot_date, datetime):
                snapshot_date = snapshot_date.date()
            elif isinstance(snapshot_date, str):
                snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
            if not isinstance(snapshot_date, date):
                snapshot_date = pd.to_datetime(snapshot_date).date()
            if snapshot_date is None:
                logger.error(f"snapshot_date is still None after conversion for {symbol}")
                return None
            contracts = self.market_data_service.get_historical_options_data(symbol, snapshot_date, expiration_date)
            if not contracts:
                logger.info(f"No historical options data found for {symbol} on {snapshot_date}")
                return None
            # Get underlying price from first contract
            underlying_price = contracts[0].get('underlying_price', 0.0) if contracts else 0.0
            data_source = contracts[0].get('data_source', 'unknown') if contracts else 'unknown'
            # Final check: snapshot_date must be a date
            assert isinstance(snapshot_date, date) and snapshot_date is not None, f"snapshot_date is not a valid date for {symbol}: {snapshot_date}"
            historical_data = HistoricalOptionsData(
                symbol=symbol,
                snapshot_date=snapshot_date,
                contracts=contracts,
                underlying_price=underlying_price,
                data_source=data_source
            )
            logger.info(f"✅ Retrieved historical options data for {symbol} on {snapshot_date}: {len(contracts)} contracts")
            return historical_data
        except Exception as e:
            logger.error(f"Error getting historical options data for {symbol} on {snapshot_date}: {e}")
            return None

    def get_historical_options_as_contracts(self, symbol: str, snapshot_date: date, 
                                          expiration_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """Get historical options data as OptionContract objects for strategy compatibility"""
        try:
            # Ensure snapshot_date is a date object
            if snapshot_date is None:
                logger.error(f"snapshot_date cannot be None for {symbol}")
                return None
            elif isinstance(snapshot_date, datetime):
                snapshot_date = snapshot_date.date()
            elif isinstance(snapshot_date, str):
                snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
            if not isinstance(snapshot_date, date):
                snapshot_date = pd.to_datetime(snapshot_date).date()
            
            historical_data = self.get_historical_options_data(symbol, snapshot_date, expiration_date)
            if not historical_data:
                return None
            
            # Convert dictionary contracts to OptionContract objects
            contracts = []
            for contract_dict in historical_data.contracts:
                try:
                    contract = OptionContract(
                        symbol=contract_dict.get('symbol', symbol),
                        strike=contract_dict.get('strike', 0.0),
                        expiration=contract_dict.get('expiration', ''),
                        option_type=contract_dict.get('option_type', 'call'),
                        price=contract_dict.get('price', 0.0),
                        volume=contract_dict.get('volume', 0),
                        open_interest=contract_dict.get('open_interest', 0),
                        delta=contract_dict.get('delta'),
                        gamma=contract_dict.get('gamma'),
                        theta=contract_dict.get('theta'),
                        vega=contract_dict.get('vega'),
                        implied_volatility=contract_dict.get('implied_volatility')
                    )
                    contracts.append(contract)
                except Exception as e:
                    logger.warning(f"Error converting contract dict to OptionContract for {symbol}: {e}")
                    continue
            
            logger.info(f"✅ Converted {len(contracts)} historical contracts to OptionContract objects for {symbol}")
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting historical options as contracts for {symbol} on {snapshot_date}: {e}")
            return None
    
    def get_historical_options_date_range(self, symbol: str, start_date: date, end_date: date,
                                        expiration_date: Optional[str] = None) -> List[HistoricalOptionsData]:
        """Get historical options data for a date range"""
        try:
            contracts_list = self.market_data_service.get_historical_options_date_range(
                symbol, start_date, end_date, expiration_date
            )
            
            if not contracts_list:
                logger.info(f"No historical options data found for {symbol} from {start_date} to {end_date}")
                return []
            
            # Group contracts by snapshot date
            historical_data_list = []
            current_date = None
            current_contracts = []
            current_underlying_price = 0.0
            current_data_source = 'unknown'
            
            for contract in contracts_list:
                contract_date = datetime.strptime(contract['snapshot_date'], "%Y-%m-%d").date()
                
                if current_date is None:
                    current_date = contract_date
                    current_underlying_price = contract.get('underlying_price', 0.0)
                    current_data_source = contract.get('data_source', 'unknown')
                
                if contract_date != current_date:
                    # Create historical data object for previous date
                    if current_contracts:
                        historical_data = HistoricalOptionsData(
                            symbol=symbol,
                            snapshot_date=current_date,
                            contracts=current_contracts,
                            underlying_price=current_underlying_price,
                            data_source=current_data_source
                        )
                        historical_data_list.append(historical_data)
                    
                    # Start new date
                    current_date = contract_date
                    current_contracts = [contract]
                    current_underlying_price = contract.get('underlying_price', 0.0)
                    current_data_source = contract.get('data_source', 'unknown')
                else:
                    current_contracts.append(contract)
            
            # Add the last group
            if current_contracts:
                historical_data = HistoricalOptionsData(
                    symbol=symbol,
                    snapshot_date=current_date,
                    contracts=current_contracts,
                    underlying_price=current_underlying_price,
                    data_source=current_data_source
                )
                historical_data_list.append(historical_data)
            
            logger.info(f"✅ Retrieved {len(historical_data_list)} historical snapshots for {symbol} from {start_date} to {end_date}")
            return historical_data_list
            
        except Exception as e:
            logger.error(f"Error getting historical options date range for {symbol}: {e}")
            return []
    
    def get_available_historical_dates(self, symbol: str) -> List[date]:
        """Get list of available historical snapshot dates for a symbol"""
        try:
            dates = self.market_data_service.get_available_historical_dates(symbol)
            logger.info(f"Found {len(dates)} available historical dates for {symbol}")
            return dates
        except Exception as e:
            logger.error(f"Error getting available historical dates for {symbol}: {e}")
            return []
    
    def get_historical_greeks_data(self, symbol: str, snapshot_date: date, 
                                 current_price: float, expiration_date: Optional[str] = None) -> Optional[Dict[str, float]]:
        """Get historical Greeks data for backtesting"""
        try:
            # Ensure snapshot_date is a date object, not datetime
            if snapshot_date is None:
                logger.error(f"snapshot_date cannot be None for {symbol}")
                return None
            elif isinstance(snapshot_date, datetime):
                snapshot_date = snapshot_date.date()
            elif isinstance(snapshot_date, str):
                snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
            # Defensive: if still not a date, try to coerce
            if not isinstance(snapshot_date, date):
                snapshot_date = pd.to_datetime(snapshot_date).date()
            
            historical_data = self.get_historical_options_data(symbol, snapshot_date, expiration_date)
            
            if not historical_data or not historical_data.contracts:
                logger.warning(f"No historical options data available for {symbol} on {snapshot_date}")
                return None
            
            # Find the most liquid contract (highest volume)
            liquid_contracts = [c for c in historical_data.contracts if c.get('volume', 0) > 0]
            
            if not liquid_contracts:
                logger.warning(f"No liquid contracts found for {symbol} on {snapshot_date}")
                return None
            
            # Get the most liquid contract
            most_liquid = max(liquid_contracts, key=lambda x: x.get('volume', 0))
            
            # Calculate average Greeks across liquid contracts
            total_delta = 0.0
            total_gamma = 0.0
            total_theta = 0.0
            total_vega = 0.0
            valid_contracts = 0
            
            for contract in liquid_contracts:
                if (contract.get('delta') is not None and 
                    contract.get('gamma') is not None and 
                    contract.get('theta') is not None and 
                    contract.get('vega') is not None):
                    total_delta += contract['delta']
                    total_gamma += contract['gamma']
                    total_theta += contract['theta']
                    total_vega += contract['vega']
                    valid_contracts += 1
            
            if valid_contracts == 0:
                logger.warning(f"No valid Greeks data found for {symbol} on {snapshot_date}")
                return None
            
            avg_delta = total_delta / valid_contracts
            avg_gamma = total_gamma / valid_contracts
            avg_theta = total_theta / valid_contracts
            avg_vega = total_vega / valid_contracts
            
            greeks_data = {
                'delta': avg_delta,
                'gamma': avg_gamma,
                'theta': avg_theta,
                'vega': avg_vega,
                'strike': most_liquid.get('strike'),
                'expiration': most_liquid.get('expiration'),
                'option_type': most_liquid.get('option_type'),
                'underlying_price': historical_data.underlying_price,
                'snapshot_date': snapshot_date.isoformat()
            }
            
            logger.info(f"✅ Retrieved historical Greeks for {symbol} on {snapshot_date}: delta={avg_delta:.3f}, gamma={avg_gamma:.3f}, theta={avg_theta:.3f}, vega={avg_vega:.3f}")
            return greeks_data
            
        except Exception as e:
            logger.error(f"Error getting historical Greeks data for {symbol} on {snapshot_date}: {e}")
            return None
    
    def cleanup_old_historical_data(self) -> int:
        """Cleanup old historical options data"""
        try:
            if datetime.now() - self.last_cleanup < self.snapshot_cleanup_interval:
                return 0
            
            deleted_count = self.market_data_service.cleanup_old_historical_options(self.snapshot_retention_days)
            self.last_cleanup = datetime.now()
            
            logger.info(f"🧹 Cleaned up {deleted_count} old historical options records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old historical data: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.options_service.get_cache_stats()
    
    def batch_store_historical_snapshots(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, int]:
        """Batch store historical snapshots for multiple symbols and date range"""
        results = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Processing historical snapshots for {symbol} from {start_date} to {end_date}")
                
                # Get historical stock data
                from ..market_data.cached_market_data_manager import CachedMarketDataManager
                market_data_manager = CachedMarketDataManager()
                
                stock_data = market_data_manager.get_historical_data(
                    symbol, 
                    start_date.strftime("%Y-%m-%d"), 
                    end_date.strftime("%Y-%m-%d")
                )
                
                if stock_data is None or stock_data.empty:
                    logger.warning(f"No stock data available for {symbol}")
                    results[symbol] = 0
                    continue
                
                # For each trading day, try to get options data
                snapshot_count = 0
                current_date = start_date
                
                while current_date <= end_date:
                    try:
                        # Skip weekends
                        if current_date.weekday() >= 5:
                            current_date += timedelta(days=1)
                            continue
                        
                        # Get stock price for this date
                        date_str = current_date.strftime("%Y-%m-%d")
                        if date_str in stock_data.index:
                            stock_price = float(stock_data.loc[date_str]['Close'])
                            
                            # Try to get options data for this date
                            # Note: This would require historical options data provider
                            # For now, we'll simulate with current data
                            contracts = self.options_service.get_options_chain(symbol)
                            
                            if contracts:
                                # Convert to dictionaries
                                contracts_dict = []
                                for contract in contracts:
                                    contracts_dict.append({
                                        'symbol': contract.symbol,
                                        'expiration': contract.expiration,
                                        'strike': contract.strike,
                                        'option_type': contract.option_type,
                                        'price': contract.price,
                                        'volume': contract.volume,
                                        'open_interest': contract.open_interest,
                                        'delta': contract.delta,
                                        'gamma': contract.gamma,
                                        'theta': contract.theta,
                                        'vega': contract.vega,
                                        'implied_volatility': contract.implied_volatility
                                    })
                                
                                # Store snapshot
                                success = self.market_data_service.store_historical_options_snapshot(
                                    symbol=symbol,
                                    contracts=contracts_dict,
                                    snapshot_date=current_date,
                                    underlying_price=stock_price,
                                    data_source="polygon"
                                )
                                
                                if success:
                                    snapshot_count += 1
                                    logger.info(f"✅ Stored snapshot for {symbol} on {date_str}")
                        
                    except Exception as e:
                        logger.warning(f"Error processing {symbol} on {current_date}: {e}")
                    
                    current_date += timedelta(days=1)
                
                results[symbol] = snapshot_count
                logger.info(f"✅ Completed {symbol}: {snapshot_count} snapshots stored")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results[symbol] = 0
        
        return results


def get_enhanced_options_service() -> EnhancedOptionsDataService:
    """Get enhanced options data service instance"""
    return EnhancedOptionsDataService() 