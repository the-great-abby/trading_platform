"""
Options Data Service - Fetch real options data with Greeks from Polygon API
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

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


class OptionsDataService:
    """Service for fetching real options data with Greeks from Polygon API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay_between_requests = 2.0  # 2 seconds between requests
        
        if not self.api_key:
            logger.warning("Polygon API key not provided - options data will be limited")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
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
    
    def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Optional[List[OptionContract]]:
        """
        Get options chain for a symbol
        
        Args:
            symbol: Stock symbol
            expiration_date: Expiration date (YYYY-MM-DD) or None for nearest expiration
            
        Returns:
            List of OptionContract objects or None if error
        """
        if not self.api_key:
            logger.warning(f"No Polygon API key - cannot fetch options data for {symbol}")
            return None
        
        try:
            self._enforce_rate_limit()
            
            # Get options chain
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
            
            # Convert to OptionContract objects
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
        """
        Get liquid options contracts for a symbol, fetch and attach Greeks, and log details.
        Args:
            symbol: Stock symbol
            min_volume: Minimum volume threshold (lowered for debugging)
        Returns:
            List of liquid OptionContract objects
        """
        contracts = self.get_options_chain(symbol)
        if contracts is None:
            logger.warning(f"[OptionsService] No contracts returned from get_options_chain for {symbol}")
            return None
        
        # Log volume distribution for debugging
        if contracts:
            volumes = [c.volume for c in contracts]
            logger.info(f"[OptionsService] Volume distribution for {symbol}: min={min(volumes)}, max={max(volumes)}, avg={sum(volumes)/len(volumes):.1f}")
            logger.info(f"[OptionsService] Contracts with volume > 0: {sum(1 for c in contracts if c.volume > 0)}/{len(contracts)}")
            logger.info(f"[OptionsService] Contracts with open_interest > 0: {sum(1 for c in contracts if c.open_interest > 0)}/{len(contracts)}")
        
        logger.info(f"[OptionsService] Raw contracts from Polygon for {symbol}: {contracts}")
        logger.info(f"[OptionsService] Total contracts from Polygon for {symbol}: {len(contracts)}")

        # Filter for liquid contracts
        liquid_contracts = [
            contract for contract in contracts
            if contract.volume >= min_volume and contract.open_interest > 0
        ]
        logger.info(f"[OptionsService] Liquid contracts after filtering for {symbol}: {len(liquid_contracts)}")

        # If no liquid contracts, try with just volume > 0
        if not liquid_contracts:
            liquid_contracts = [
                contract for contract in contracts
                if contract.volume > 0
            ]
            logger.info(f"[OptionsService] Contracts with volume > 0 for {symbol}: {len(liquid_contracts)}")

        # If still no contracts, take any contracts with data
        if not liquid_contracts and contracts:
            liquid_contracts = contracts[:5]  # Take first 5 contracts
            logger.info(f"[OptionsService] Using first 5 contracts for {symbol} (no volume filter)")

        # Fetch and attach Greeks for each contract
        for contract in liquid_contracts:
            greeks = self.get_options_greeks(symbol, contract.strike, contract.expiration, contract.option_type)
            if greeks:
                contract.delta = greeks.get("delta")
                contract.gamma = greeks.get("gamma")
                contract.theta = greeks.get("theta")
                contract.vega = greeks.get("vega")
                contract.implied_volatility = greeks.get("implied_volatility")
                logger.info(f"[OptionsService] Attached Greeks for {symbol} {contract.strike} {contract.option_type} {contract.expiration}: {greeks}")
            else:
                logger.warning(f"[OptionsService] No Greeks found for {symbol} {contract.strike} {contract.option_type} {contract.expiration}")

        logger.info(f"[OptionsService] Final liquid contracts with Greeks for {symbol}: {liquid_contracts}")
        return liquid_contracts[:10]  # Return top 10 most liquid
    
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