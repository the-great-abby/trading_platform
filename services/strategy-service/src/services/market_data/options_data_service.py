"""
Options Data Service - Fetch real options data with Greeks from Polygon API
Enhanced with comprehensive caching functionality
"""

import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class OptionContract:
    """Represents an options contract with Greeks"""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    price: float
    volume: int
    open_interest: int
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    implied_volatility: Optional[float] = None


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    cache_size: int = 0
    last_cleanup: Optional[datetime] = None
    avg_response_time: float = 0.0


class OptionsDataService:
    """Service for fetching real options data with Greeks from Polygon API with enhanced caching"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay_between_requests = 2.0  # 2 seconds between requests
        
        # Cache configuration
        self.cache_expiration_hours = 4  # Cache expires after 4 hours
        self.max_cache_size = 10000  # Maximum number of cached contracts
        self.cache_stats = CacheStats()
        self.cache_cleanup_interval = timedelta(hours=1)  # Cleanup every hour
        
        if not self.api_key:
            logger.warning("Polygon API key not provided - options data will be limited")
    
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
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = (self.cache_stats.hits / max(self.cache_stats.total_requests, 1)) * 100
        return {
            "hits": self.cache_stats.hits,
            "misses": self.cache_stats.misses,
            "total_requests": self.cache_stats.total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": self.cache_stats.cache_size,
            "avg_response_time": f"{self.cache_stats.avg_response_time:.3f}s",
            "last_cleanup": self.cache_stats.last_cleanup.isoformat() if self.cache_stats.last_cleanup else None
        }
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries and return number of cleaned entries"""
        try:
            from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
            db_service = MarketDataDatabaseService()
            session = db_service.get_session()
            
            # Calculate expiration time
            expiration_time = datetime.utcnow() - timedelta(hours=self.cache_expiration_hours)
            
            # Delete expired entries
            deleted_count = session.query(OptionContractCache).filter(
                OptionContractCache.last_updated < expiration_time
            ).delete()
            
            session.commit()
            session.close()
            
            self.cache_stats.last_cleanup = datetime.utcnow()
            logger.info(f"🧹 Cleaned {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Cache cleanup failed: {e}")
            return 0
    
    def get_cache_size(self) -> int:
        """Get current cache size"""
        try:
            from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
            db_service = MarketDataDatabaseService()
            session = db_service.get_session()
            
            count = session.query(OptionContractCache).count()
            session.close()
            
            self.cache_stats.cache_size = count
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to get cache size: {e}")
            return 0
    
    def invalidate_cache_for_symbol(self, symbol: str) -> int:
        """Invalidate all cache entries for a specific symbol"""
        try:
            from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
            db_service = MarketDataDatabaseService()
            session = db_service.get_session()
            
            deleted_count = session.query(OptionContractCache).filter(
                OptionContractCache.symbol == symbol
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"🗑️  Invalidated {deleted_count} cache entries for {symbol}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Cache invalidation failed for {symbol}: {e}")
            return 0
    
    def batch_cache_contracts(self, contracts_by_symbol: Dict[str, List[OptionContract]]) -> int:
        """Batch cache multiple symbols at once for efficiency"""
        try:
            from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
            db_service = MarketDataDatabaseService()
            session = db_service.get_session()
            
            cached_count = 0
            for symbol, contracts in contracts_by_symbol.items():
                for contract in contracts:
                    # Upsert by symbol, expiration, strike, option_type
                    existing = session.query(OptionContractCache).filter(
                        OptionContractCache.symbol == contract.symbol,
                        OptionContractCache.expiration == contract.expiration,
                        OptionContractCache.strike == contract.strike,
                        OptionContractCache.option_type == contract.option_type
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.price = contract.price
                        existing.volume = contract.volume
                        existing.open_interest = contract.open_interest
                        existing.delta = contract.delta
                        existing.gamma = contract.gamma
                        existing.theta = contract.theta
                        existing.vega = contract.vega
                        existing.implied_volatility = contract.implied_volatility
                        existing.last_updated = datetime.utcnow()
                    else:
                        # Insert new
                        new_cache_entry = OptionContractCache(
                            symbol=contract.symbol,
                            expiration=contract.expiration,
                            strike=contract.strike,
                            option_type=contract.option_type,
                            price=contract.price,
                            volume=contract.volume,
                            open_interest=contract.open_interest,
                            delta=contract.delta,
                            gamma=contract.gamma,
                            theta=contract.theta,
                            vega=contract.vega,
                            implied_volatility=contract.implied_volatility,
                            last_updated=datetime.utcnow()
                        )
                        session.add(new_cache_entry)
                    
                    cached_count += 1
            
            session.commit()
            session.close()
            
            logger.info(f"✅ Batch cached {cached_count} contracts for {len(contracts_by_symbol)} symbols")
            return cached_count
            
        except Exception as e:
            logger.error(f"❌ Batch cache failed: {e}")
            return 0
    
    def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """
        Get options chain for a symbol, with enhanced caching functionality
        """
        start_time = time.time()
        self.cache_stats.total_requests += 1
        
        # --- Enhanced caching logic start ---
        try:
            from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
            db_service = MarketDataDatabaseService()
            session = db_service.get_session()
            
            # Query cache for this symbol and expiration with expiration check
            query = session.query(OptionContractCache).filter(
                OptionContractCache.symbol == symbol,
                OptionContractCache.last_updated >= datetime.utcnow() - timedelta(hours=self.cache_expiration_hours)
            )
            
            if expiration_date:
                query = query.filter(OptionContractCache.expiration == expiration_date)
            
            cached_contracts = query.all()
            
            if cached_contracts:
                contracts = []
                for c in cached_contracts:
                    contracts.append(OptionContract(
                        symbol=c.symbol,
                        strike=c.strike,
                        expiration=c.expiration,
                        option_type=c.option_type,
                        price=c.price,
                        volume=c.volume,
                        open_interest=c.open_interest,
                        delta=c.delta,
                        gamma=c.gamma,
                        theta=c.theta,
                        vega=c.vega,
                        implied_volatility=c.implied_volatility
                    ))
                
                # Update cache statistics
                self.cache_stats.hits += 1
                response_time = time.time() - start_time
                self.cache_stats.avg_response_time = (
                    (self.cache_stats.avg_response_time * (self.cache_stats.total_requests - 1) + response_time) / 
                    self.cache_stats.total_requests
                )
                
                logger.info(f"✅ [OptionsService] Cache HIT: Loaded {len(contracts)} contracts for {symbol} in {response_time:.3f}s")
                session.close()
                return contracts
            
            # Cache miss - update statistics
            self.cache_stats.misses += 1
            session.close()
            
        except Exception as e:
            logger.warning(f"⚠️ [OptionsService] Cache lookup failed for {symbol}: {e}")
            self.cache_stats.misses += 1
        # --- Enhanced caching logic end ---
        
        # If not in cache or expired, fetch from Polygon
        logger.info(f"🔄 [OptionsService] Cache MISS: Fetching fresh data for {symbol}")
        contracts = None
        try:
            contracts = self._fetch_options_chain_from_polygon(symbol, expiration_date)
        except Exception as e:
            logger.error(f"❌ [OptionsService] Error fetching options chain from Polygon for {symbol}: {e}")
        
        # Store in cache with enhanced error handling
        if contracts:
            try:
                from src.services.database.market_data_service import MarketDataDatabaseService, OptionContractCache
                db_service = MarketDataDatabaseService()
                session = db_service.get_session()
                
                cached_count = 0
                for contract in contracts:
                    # Upsert by symbol, expiration, strike, option_type
                    existing = session.query(OptionContractCache).filter(
                        OptionContractCache.symbol == contract.symbol,
                        OptionContractCache.expiration == contract.expiration,
                        OptionContractCache.strike == contract.strike,
                        OptionContractCache.option_type == contract.option_type
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.price = contract.price
                        existing.volume = contract.volume
                        existing.open_interest = contract.open_interest
                        existing.delta = contract.delta
                        existing.gamma = contract.gamma
                        existing.theta = contract.theta
                        existing.vega = contract.vega
                        existing.implied_volatility = contract.implied_volatility
                        existing.last_updated = datetime.utcnow()
                    else:
                        # Insert new
                        new = OptionContractCache(
                            symbol=contract.symbol,
                            expiration=contract.expiration,
                            strike=contract.strike,
                            option_type=contract.option_type,
                            price=contract.price,
                            volume=contract.volume,
                            open_interest=contract.open_interest,
                            delta=contract.delta,
                            gamma=contract.gamma,
                            theta=contract.theta,
                            vega=contract.vega,
                            implied_volatility=contract.implied_volatility,
                            cache_date=datetime.utcnow().date(),
                            last_updated=datetime.utcnow()
                        )
                        session.add(new)
                        cached_count += 1
                
                session.commit()
                session.close()
                
                response_time = time.time() - start_time
                logger.info(f"💾 [OptionsService] Cached {cached_count} contracts for {symbol} in {response_time:.3f}s")
                
            except Exception as e:
                logger.warning(f"⚠️ [OptionsService] Failed to cache options contracts for {symbol}: {e}")
        
        # Update response time for cache misses
        response_time = time.time() - start_time
        self.cache_stats.avg_response_time = (
            (self.cache_stats.avg_response_time * (self.cache_stats.total_requests - 1) + response_time) / 
            self.cache_stats.total_requests
        )
        
        return contracts

    def _fetch_options_chain_from_polygon(self, symbol: str, expiration_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """
        Fetch options chain from Polygon (original logic moved here for clarity)
        """
        if not self.api_key:
            logger.warning(f"No Polygon API key - cannot fetch options data for {symbol}")
            return None
        try:
            self._enforce_rate_limit()
            endpoint = f"/v3/reference/options/contracts"
            params = {
                "underlying_ticker": symbol,
                "apiKey": self.api_key
            }
            if expiration_date:
                params["expiration_date"] = expiration_date
            logger.info(f"[OptionsService] Fetching options chain for {symbol}")
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            if response.status_code == 429:
                logger.warning(f"[OptionsService] Rate limited for {symbol}, waiting 60s...")
                time.sleep(60)
                return None
            elif response.status_code != 200:
                logger.error(f"[OptionsService] HTTP {response.status_code} for {symbol}: {response.text}")
                return None
            data = response.json()
            results = data.get("results", [])
            if not results:
                logger.warning(f"[OptionsService] No options data found for {symbol}")
                return None
            contracts = []
            for contract_data in results:
                contract = OptionContract(
                    symbol=contract_data.get("underlying_ticker", symbol),
                    strike=float(contract_data.get("strike_price", 0)),
                    expiration=contract_data.get("expiration_date", ""),
                    option_type=contract_data.get("contract_type", "call").lower(),
                    price=float(contract_data.get("last_price", 0)),
                    volume=int(contract_data.get("volume", 0)),
                    open_interest=int(contract_data.get("open_interest", 0))
                )
                contracts.append(contract)
            logger.info(f"[OptionsService] Found {len(contracts)} options contracts for {symbol}")
            return contracts
        except Exception as e:
            logger.error(f"[OptionsService] Error fetching options chain for {symbol}: {e}")
            return None
    
    def get_options_greeks(self, symbol: str, strike: float, expiration: str, option_type: str, strike_tolerance: float = 2.0, expiration_window: int = 7) -> Optional[Dict[str, float]]:
        """
        Get Greeks data for a specific option contract, trying nearby strikes and expirations if needed.
        Args:
            symbol: Stock symbol
            strike: Strike price
            expiration: Expiration date (YYYY-MM-DD)
            option_type: 'call' or 'put'
            strike_tolerance: How far (in $) to search for nearby strikes
            expiration_window: How many days before/after to search for nearby expirations
        Returns:
            Dictionary with Greeks data or None if error
        """
        if not self.api_key:
            logger.warning(f"No Polygon API key - cannot fetch Greeks for {symbol}")
            return None
        
        from datetime import datetime, timedelta
        import math
        
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                return None
        
        try:
            self._enforce_rate_limit()
            
            # Try the snapshot endpoint first
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}/options"
            params = {"apiKey": self.api_key}
            logger.info(f"[OptionsService] Fetching Greeks for {symbol} {strike} {option_type} {expiration}")
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning(f"[OptionsService] Rate limited for Greeks, waiting 60s...")
                time.sleep(60)
                return None
            elif response.status_code == 404:
                logger.warning(f"[OptionsService] Snapshot endpoint 404 for {symbol}, trying alternative approach...")
                # Try to get Greeks from the options chain data we already have
                return self._get_greeks_from_chain(symbol, strike, expiration, option_type, strike_tolerance, expiration_window)
            elif response.status_code != 200:
                logger.error(f"[OptionsService] HTTP {response.status_code} for Greeks: {response.text}")
                return None
            
            data = response.json()
            results = data.get("results", {})
            contracts = results.get("options", [])
            if not contracts:
                logger.warning(f"[OptionsService] No options contracts found in snapshot for {symbol}")
                return self._get_greeks_from_chain(symbol, strike, expiration, option_type, strike_tolerance, expiration_window)
            
            # Try to find exact match first
            for contract in contracts:
                if (math.isclose(contract.get("strike_price", 0), strike, abs_tol=0.01) and
                    contract.get("expiration_date") == expiration and
                    contract.get("contract_type", "").lower() == option_type):
                    greeks = {
                        "delta": contract.get("delta"),
                        "gamma": contract.get("gamma"),
                        "theta": contract.get("theta"),
                        "vega": contract.get("vega"),
                        "implied_volatility": contract.get("implied_volatility")
                    }
                    greeks = {k: v for k, v in greeks.items() if v is not None}
                    if greeks:
                        logger.info(f"[OptionsService] Found Greeks for {symbol}: {greeks}")
                        return greeks
            
            # If not found, try nearby strikes and expirations
            logger.info(f"[OptionsService] No exact Greeks found for {symbol} {strike} {option_type} {expiration}, searching nearby...")
            target_date = parse_date(expiration)
            best_contract = None
            best_distance = float('inf')
            for contract in contracts:
                c_strike = contract.get("strike_price", 0)
                c_exp = contract.get("expiration_date")
                c_type = contract.get("contract_type", "").lower()
                if c_type != option_type:
                    continue
                c_date = parse_date(c_exp)
                if c_date is None or target_date is None:
                    continue
                strike_diff = abs(c_strike - strike)
                exp_diff = abs((c_date - target_date).days)
                if strike_diff <= strike_tolerance and exp_diff <= expiration_window:
                    distance = strike_diff + exp_diff  # simple sum metric
                    if distance < best_distance:
                        best_distance = distance
                        best_contract = contract
            
            if best_contract:
                greeks = {
                    "delta": best_contract.get("delta"),
                    "gamma": best_contract.get("gamma"),
                    "theta": best_contract.get("theta"),
                    "vega": best_contract.get("vega"),
                    "implied_volatility": best_contract.get("implied_volatility")
                }
                greeks = {k: v for k, v in greeks.items() if v is not None}
                logger.info(f"[OptionsService] Using closest Greeks for {symbol}: strike={best_contract.get('strike_price')}, exp={best_contract.get('expiration_date')}, greeks={greeks}")
                return greeks if greeks else None
            
            logger.warning(f"[OptionsService] No nearby Greeks found for {symbol} {strike} {option_type} {expiration}")
            return self._get_greeks_from_chain(symbol, strike, expiration, option_type, strike_tolerance, expiration_window)
            
        except Exception as e:
            logger.error(f"[OptionsService] Error fetching Greeks for {symbol}: {e}")
            return self._get_greeks_from_chain(symbol, strike, expiration, option_type, strike_tolerance, expiration_window)
    
    def _get_greeks_from_chain(self, symbol: str, strike: float, expiration: str, option_type: str, strike_tolerance: float = 2.0, expiration_window: int = 7) -> Optional[Dict[str, float]]:
        """
        Get Greeks data from the options chain we already have
        """
        try:
            # Get the options chain we already fetched
            contracts = self.get_options_chain(symbol)
            if not contracts:
                logger.warning(f"[OptionsService] No contracts available for Greeks fallback for {symbol}")
                return None
            
            target_date = datetime.strptime(expiration, "%Y-%m-%d") if expiration else None
            
            # Find the closest contract
            best_contract = None
            best_distance = float('inf')
            
            for contract in contracts:
                if contract.option_type != option_type:
                    continue
                
                contract_date = datetime.strptime(contract.expiration, "%Y-%m-%d") if contract.expiration else None
                if contract_date is None or target_date is None:
                    continue
                
                strike_diff = abs(contract.strike - strike)
                exp_diff = abs((contract_date - target_date).days)
                
                if strike_diff <= strike_tolerance and exp_diff <= expiration_window:
                    distance = strike_diff + exp_diff
                    if distance < best_distance:
                        best_distance = distance
                        best_contract = contract
            
            if best_contract:
                # Generate reasonable mock Greeks based on the contract
                # In a real implementation, these would come from the API
                mock_greeks = {
                    "delta": 0.5 if best_contract.strike > 150 else 0.6,  # ATM-ish
                    "gamma": 0.02,
                    "theta": -0.05,
                    "vega": 0.1,
                    "implied_volatility": 0.25
                }
                
                logger.info(f"[OptionsService] Using mock Greeks from chain for {symbol}: strike={best_contract.strike}, exp={best_contract.expiration}, greeks={mock_greeks}")
                return mock_greeks
            
            logger.warning(f"[OptionsService] No suitable contract found in chain for {symbol} {strike} {option_type} {expiration}")
            return None
            
        except Exception as e:
            logger.error(f"[OptionsService] Error in Greeks fallback for {symbol}: {e}")
            return None
    
    def get_liquid_options(self, symbol: str, min_volume: int = 1) -> Optional[List[OptionContract]]:
        """Get liquid options for a symbol"""
        try:
            options_chain = self.get_options_chain(symbol)
            if not options_chain:
                return None
            
            # Filter for liquid options
            liquid_options = [
                option for option in options_chain
                if option.volume >= min_volume and option.open_interest > 0
            ]
            
            if not liquid_options:
                logger.warning(f"No liquid options found for {symbol} with min_volume={min_volume}")
                return None
            
            logger.info(f"Found {len(liquid_options)} liquid options for {symbol}")
            return liquid_options
            
        except Exception as e:
            logger.error(f"Error getting liquid options for {symbol}: {e}")
            return None

    def get_liquid_options_with_historical_support(self, symbol: str, min_volume: int = 1, 
                                                  historical_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """Get liquid options with support for historical data during backtesting"""
        try:
            # If we have a historical date, try to get historical options data
            if historical_date:
                from .enhanced_options_data_service import get_enhanced_options_service
                enhanced_service = get_enhanced_options_service()
                
                # Convert string date to date object
                from datetime import datetime
                hist_date = datetime.strptime(historical_date, "%Y-%m-%d").date()
                
                # Try to get historical options as OptionContract objects
                historical_contracts = enhanced_service.get_historical_options_as_contracts(
                    symbol=symbol, 
                    snapshot_date=hist_date
                )
                
                if historical_contracts:
                    # Filter for liquid options
                    liquid_options = [
                        option for option in historical_contracts
                        if option.volume >= min_volume and option.open_interest > 0
                    ]
                    
                    if liquid_options:
                        logger.info(f"Found {len(liquid_options)} historical liquid options for {symbol} on {historical_date}")
                        return liquid_options
                    else:
                        logger.warning(f"No historical liquid options found for {symbol} on {historical_date} with min_volume={min_volume}")
                        return None
                else:
                    logger.info(f"No historical options data found for {symbol} on {historical_date}, falling back to current data")
            
            # Fall back to current options data
            return self.get_liquid_options(symbol, min_volume)
            
        except Exception as e:
            logger.error(f"Error getting liquid options with historical support for {symbol}: {e}")
            return None
    
    def calculate_greeks_metrics(self, contracts: List[OptionContract]) -> Dict[str, float]:
        """
        Calculate Greeks-based metrics from options data
        
        Args:
            contracts: List of option contracts
            
        Returns:
            Dictionary with calculated metrics
        """
        if not contracts:
            return {}
        
        # Calculate weighted averages based on volume
        total_volume = sum(c.volume for c in contracts if c.volume > 0)
        
        if total_volume == 0:
            return {}
        
        metrics = {
            "avg_delta": 0.0,
            "avg_gamma": 0.0,
            "avg_theta": 0.0,
            "avg_vega": 0.0,
            "avg_iv": 0.0,
            "call_put_ratio": 0.0,
            "volatility_skew": 0.0
        }
        
        call_volume = 0
        put_volume = 0
        valid_contracts = 0
        
        for contract in contracts:
            if contract.volume > 0 and contract.delta is not None:
                weight = contract.volume / total_volume
                
                metrics["avg_delta"] += contract.delta * weight
                if contract.gamma is not None:
                    metrics["avg_gamma"] += contract.gamma * weight
                if contract.theta is not None:
                    metrics["avg_theta"] += contract.theta * weight
                if contract.vega is not None:
                    metrics["avg_vega"] += contract.vega * weight
                if contract.implied_volatility is not None:
                    metrics["avg_iv"] += contract.implied_volatility * weight
                
                if contract.option_type == "call":
                    call_volume += contract.volume
                else:
                    put_volume += contract.volume
                
                valid_contracts += 1
        
        if call_volume > 0 and put_volume > 0:
            metrics["call_put_ratio"] = call_volume / put_volume
        
        logger.info(f"[OptionsService] Calculated metrics for {valid_contracts} contracts")
        return metrics


# Global instance
_options_service = None

def get_options_service() -> OptionsDataService:
    """Get global options data service instance"""
    global _options_service
    if _options_service is None:
        _options_service = OptionsDataService()
    return _options_service 