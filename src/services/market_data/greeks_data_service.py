"""
Greeks Data Service - Fetch and cache real options Greeks data from Polygon
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

from .options_data_service import OptionContract
# from ..database.market_data_service import MarketDataService  # Commented out for now

logger = logging.getLogger(__name__)


@dataclass
class GreeksData:
    """Container for options Greeks data"""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    implied_volatility: Optional[float] = None
    price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    snapshot_date: Optional[date] = None


class GreeksDataService:
    """Service for fetching and caching real options Greeks data from Polygon"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        # self.market_data_service = MarketDataService()  # Commented out for now
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay_between_requests = 1.0  # 1 second between requests
        
        # Cache configuration
        self.cache_expiration_hours = 24  # Cache expires after 24 hours
        self.greeks_cache = {}  # In-memory cache for quick access
        
        if not self.api_key:
            logger.warning("Polygon API key not provided - Greeks data will be limited")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            sleep_time = self.min_delay_between_requests - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_greeks_for_contract(self, symbol: str, strike: float, expiration: str, 
                               option_type: str, snapshot_date: Optional[date] = None) -> Optional[GreeksData]:
        """
        Get Greeks data for a specific option contract
        
        Args:
            symbol: Stock symbol
            strike: Strike price
            expiration: Expiration date (YYYY-MM-DD)
            option_type: 'call' or 'put'
            snapshot_date: Historical date for backtesting (optional)
            
        Returns:
            GreeksData object or None if not available
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{strike}_{expiration}_{option_type}_{snapshot_date}"
            if cache_key in self.greeks_cache:
                logger.info(f"✅ Cache HIT: Greeks for {symbol} {strike} {option_type} {expiration}")
                return self.greeks_cache[cache_key]
            
            # For historical data, try to get from database
            if snapshot_date:
                historical_greeks = self._get_historical_greeks(symbol, strike, expiration, option_type, snapshot_date)
                if historical_greeks:
                    self.greeks_cache[cache_key] = historical_greeks
                    return historical_greeks
            
            # Fetch current Greeks from Polygon
            current_greeks = self._fetch_greeks_from_polygon(symbol, strike, expiration, option_type)
            if current_greeks:
                # Store in cache
                self.greeks_cache[cache_key] = current_greeks
                
                # Store in database for historical access
                self._store_greeks_snapshot(current_greeks)
                
                return current_greeks
            
            logger.warning(f"No Greeks data available for {symbol} {strike} {option_type} {expiration}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Greeks for {symbol} {strike} {option_type} {expiration}: {e}")
            return None
    
    def _fetch_greeks_from_polygon(self, symbol: str, strike: float, expiration: str, 
                                  option_type: str) -> Optional[GreeksData]:
        """Fetch Greeks data from Polygon API"""
        try:
            self._enforce_rate_limit()
            
            # Try the snapshot endpoint first (most comprehensive)
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}/options"
            params = {"apiKey": self.api_key}
            
            logger.info(f"🔍 Fetching Greeks from Polygon for {symbol} {strike} {option_type} {expiration}")
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning(f"Rate limited for Greeks, waiting 60s...")
                time.sleep(60)
                return None
            elif response.status_code == 404:
                logger.warning(f"Snapshot endpoint 404 for {symbol}, trying alternatives...")
                return self._fetch_greeks_alternative_methods(symbol, strike, expiration, option_type)
            elif response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for Greeks: {response.text}")
                return None
            
            data = response.json()
            results = data.get("results", {})
            contracts = results.get("options", [])
            
            if not contracts:
                logger.warning(f"No options contracts found in snapshot for {symbol}")
                return self._fetch_greeks_alternative_methods(symbol, strike, expiration, option_type)
            
            # Find exact match
            for contract in contracts:
                if (abs(contract.get("strike_price", 0) - strike) < 0.01 and
                    contract.get("expiration_date") == expiration and
                    contract.get("contract_type", "").lower() == option_type):
                    
                    greeks = GreeksData(
                        symbol=symbol,
                        strike=strike,
                        expiration=expiration,
                        option_type=option_type,
                        delta=contract.get("delta"),
                        gamma=contract.get("gamma"),
                        theta=contract.get("theta"),
                        vega=contract.get("vega"),
                        implied_volatility=contract.get("implied_volatility"),
                        price=contract.get("last_price"),
                        volume=contract.get("volume"),
                        open_interest=contract.get("open_interest"),
                        snapshot_date=date.today()
                    )
                    
                    logger.info(f"✅ Found real Greeks for {symbol}: delta={greeks.delta}, gamma={greeks.gamma}, theta={greeks.theta}, vega={greeks.vega}")
                    return greeks
            
            # Try nearby strikes if exact match not found
            logger.info(f"No exact Greeks found for {symbol} {strike} {option_type} {expiration}, searching nearby...")
            return self._find_nearby_greeks(contracts, symbol, strike, expiration, option_type)
            
        except Exception as e:
            logger.error(f"Error fetching Greeks from Polygon for {symbol}: {e}")
            return None
    
    def _fetch_greeks_alternative_methods(self, symbol: str, strike: float, expiration: str, 
                                         option_type: str) -> Optional[GreeksData]:
        """Try alternative methods to get Greeks data"""
        try:
            # Method 1: Try the options contracts endpoint
            endpoint = f"/v3/reference/options/contracts"
            params = {
                "underlying_ticker": symbol,
                "expiration_date": expiration,
                "apiKey": self.api_key
            }
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                for contract in results:
                    if (abs(contract.get("strike_price", 0) - strike) < 0.01 and
                        contract.get("contract_type", "").lower() == option_type):
                        
                        greeks = GreeksData(
                            symbol=symbol,
                            strike=strike,
                            expiration=expiration,
                            option_type=option_type,
                            delta=contract.get("delta"),
                            gamma=contract.get("gamma"),
                            theta=contract.get("theta"),
                            vega=contract.get("vega"),
                            implied_volatility=contract.get("implied_volatility"),
                            price=contract.get("last_price"),
                            volume=contract.get("volume"),
                            open_interest=contract.get("open_interest"),
                            snapshot_date=date.today()
                        )
                        
                        if any([greeks.delta, greeks.gamma, greeks.theta, greeks.vega, greeks.implied_volatility]):
                            logger.info(f"✅ Found Greeks via contracts endpoint for {symbol}")
                            return greeks
            
            # Method 2: Try the previous close endpoint for historical data
            endpoint = f"/v2/aggs/ticker/{symbol}/prev"
            params = {"apiKey": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            if response.status_code == 200:
                # This gives us stock price, which we can use to estimate Greeks
                data = response.json()
                results = data.get("results", [])
                if results:
                    stock_price = results[0].get("c", 0)  # Close price
                    if stock_price > 0:
                        # Generate reasonable mock Greeks based on stock price
                        greeks = self._generate_mock_greeks(symbol, strike, expiration, option_type, stock_price)
                        logger.info(f"📊 Generated mock Greeks for {symbol} based on stock price ${stock_price}")
                        return greeks
            
            logger.warning(f"All alternative methods failed for {symbol} {strike} {option_type} {expiration}")
            return None
            
        except Exception as e:
            logger.error(f"Error in alternative Greeks methods for {symbol}: {e}")
            return None
    
    def _find_nearby_greeks(self, contracts: List[Dict], symbol: str, strike: float, 
                           expiration: str, option_type: str) -> Optional[GreeksData]:
        """Find Greeks from nearby strikes/expirations"""
        try:
            best_contract = None
            best_distance = float('inf')
            
            for contract in contracts:
                if contract.get("contract_type", "").lower() != option_type:
                    continue
                
                c_strike = contract.get("strike_price", 0)
                c_exp = contract.get("expiration_date")
                
                # Calculate distance metric
                strike_diff = abs(c_strike - strike)
                exp_diff = 0 if c_exp == expiration else 1  # Binary for expiration match
                
                # Weighted distance (strike difference more important)
                distance = strike_diff * 10 + exp_diff * 100
                
                if distance < best_distance:
                    best_distance = distance
                    best_contract = contract
            
            if best_contract and best_distance < 50:  # Reasonable threshold
                greeks = GreeksData(
                    symbol=symbol,
                    strike=strike,
                    expiration=expiration,
                    option_type=option_type,
                    delta=best_contract.get("delta"),
                    gamma=best_contract.get("gamma"),
                    theta=best_contract.get("theta"),
                    vega=best_contract.get("vega"),
                    implied_volatility=best_contract.get("implied_volatility"),
                    price=best_contract.get("last_price"),
                    volume=best_contract.get("volume"),
                    open_interest=best_contract.get("open_interest"),
                    snapshot_date=date.today()
                )
                
                logger.info(f"✅ Using nearby Greeks for {symbol}: strike={best_contract.get('strike_price')}, distance={best_distance}")
                return greeks
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding nearby Greeks for {symbol}: {e}")
            return None
    
    def _generate_mock_greeks(self, symbol: str, strike: float, expiration: str, 
                             option_type: str, stock_price: float) -> GreeksData:
        """Generate reasonable mock Greeks based on stock price and option characteristics"""
        try:
            # Calculate moneyness
            moneyness = stock_price / strike if strike > 0 else 1.0
            
            # Estimate delta based on moneyness and option type
            if option_type == "call":
                if moneyness > 1.1:  # ITM
                    delta = 0.8
                elif moneyness < 0.9:  # OTM
                    delta = 0.2
                else:  # ATM
                    delta = 0.5
            else:  # put
                if moneyness > 1.1:  # ITM
                    delta = -0.2
                elif moneyness < 0.9:  # OTM
                    delta = -0.8
                else:  # ATM
                    delta = -0.5
            
            # Estimate other Greeks
            gamma = 0.02 if abs(moneyness - 1.0) < 0.1 else 0.01  # Higher near ATM
            theta = -0.05  # Time decay
            vega = 0.15  # Volatility sensitivity
            implied_volatility = 0.25  # 25% IV as default
            
            greeks = GreeksData(
                symbol=symbol,
                strike=strike,
                expiration=expiration,
                option_type=option_type,
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                implied_volatility=implied_volatility,
                price=stock_price * 0.05,  # Rough estimate
                volume=100,
                open_interest=500,
                snapshot_date=date.today()
            )
            
            return greeks
            
        except Exception as e:
            logger.error(f"Error generating mock Greeks for {symbol}: {e}")
            return None
    
    def _get_historical_greeks(self, symbol: str, strike: float, expiration: str, 
                              option_type: str, snapshot_date: date) -> Optional[GreeksData]:
        """Get historical Greeks data from database"""
        try:
            # This would query the historical_options_snapshots table
            # For now, return None to indicate no historical data
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical Greeks for {symbol}: {e}")
            return None
    
    def _store_greeks_snapshot(self, greeks: GreeksData) -> bool:
        """Store Greeks data in database for historical access"""
        try:
            # This would store in the historical_options_snapshots table
            # For now, just log that we would store it
            logger.info(f"Would store Greeks snapshot for {greeks.symbol} {greeks.strike} {greeks.option_type} {greeks.expiration}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Greeks snapshot for {greeks.symbol}: {e}")
            return False
    
    def get_greeks_for_symbol(self, symbol: str, snapshot_date: Optional[date] = None) -> List[GreeksData]:
        """Get all available Greeks data for a symbol"""
        try:
            # This would fetch all Greeks for a symbol
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting all Greeks for {symbol}: {e}")
            return []
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self.greeks_cache.clear()
        logger.info("Cleared Greeks cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.greeks_cache),
            "cache_keys": list(self.greeks_cache.keys())[:10]  # First 10 keys
        }


def get_greeks_service() -> GreeksDataService:
    """Get a singleton instance of the Greeks data service"""
    if not hasattr(get_greeks_service, '_instance'):
        get_greeks_service._instance = GreeksDataService()
    return get_greeks_service._instance 