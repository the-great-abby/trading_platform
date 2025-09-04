#!/usr/bin/env python3
"""
Theoretical Greeks Calculator

This script calculates theoretical Greeks (delta, gamma, theta, vega) using the Black-Scholes model
based on available Polygon data (options contracts and historical price data).
"""

import os
import sys
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, Tuple
import time
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
from scipy.stats import norm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TheoreticalGreeks:
    """Container for theoretical Greeks data"""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    current_price: float
    option_price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    time_to_expiry: float  # in years
    risk_free_rate: float
    calculated_at: datetime


class BlackScholesCalculator:
    """Black-Scholes model calculator for options Greeks"""
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize calculator
        
        Args:
            risk_free_rate: Risk-free interest rate (default: 5%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_implied_volatility(self, option_price: float, S: float, K: float, 
                                   T: float, r: float, option_type: str, 
                                   tolerance: float = 1e-5, max_iterations: int = 100) -> float:
        """
        Calculate implied volatility using Newton-Raphson method
        
        Args:
            option_price: Current option price
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            option_type: 'call' or 'put'
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations
            
        Returns:
            Implied volatility
        """
        if T <= 0:
            return 0.0
        
        # Initial guess for volatility (30% is a reasonable starting point)
        sigma = 0.3
        
        for i in range(max_iterations):
            # Calculate option price with current volatility
            if option_type.lower() == 'call':
                theoretical_price = self.black_scholes_call(S, K, T, r, sigma)
                vega = self.vega(S, K, T, r, sigma)
            else:
                theoretical_price = self.black_scholes_put(S, K, T, r, sigma)
                vega = self.vega(S, K, T, r, sigma)
            
            # Calculate difference
            diff = option_price - theoretical_price
            
            # Check convergence
            if abs(diff) < tolerance:
                break
            
            # Update volatility using Newton-Raphson
            if abs(vega) < 1e-10:  # Avoid division by zero
                break
            
            sigma = sigma + diff / vega
            
            # Ensure volatility is positive
            sigma = max(0.001, sigma)
        
        return sigma
    
    def black_scholes_call(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price"""
        if T <= 0:
            return max(0, S - K)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    
    def black_scholes_put(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price"""
        if T <= 0:
            return max(0, K - S)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    def delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate delta"""
        if T <= 0:
            if option_type.lower() == 'call':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        
        if option_type.lower() == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    
    def gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate gamma (same for calls and puts)"""
        if T <= 0:
            return 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        return norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    def theta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate theta (time decay)"""
        if T <= 0:
            return 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        theta_term1 = -(S * sigma * norm.pdf(d1)) / (2 * math.sqrt(T))
        
        if option_type.lower() == 'call':
            theta_term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
        else:
            theta_term2 = -r * K * math.exp(-r * T) * norm.cdf(-d2)
        
        return theta_term1 + theta_term2
    
    def vega(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate vega (same for calls and puts)"""
        if T <= 0:
            return 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        return S * math.sqrt(T) * norm.pdf(d1) / 100  # Divide by 100 for percentage change


class PolygonDataFetcher:
    """Fetcher for Polygon data needed for Greeks calculations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        if not self.api_key:
            logger.error("❌ No Polygon API key found")
            raise ValueError("Polygon API key required")
    
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
        time.sleep(1.0)  # 1 second between requests
    
    def get_current_stock_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        try:
            self._enforce_rate_limit()
            
            # Try snapshot endpoint first
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {"apiKey": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})
                
                if "lastTrade" in results and "p" in results["lastTrade"]:
                    return float(results["lastTrade"]["p"])
                elif "prevDay" in results and "c" in results["prevDay"]:
                    return float(results["prevDay"]["c"])
            
            # Fallback to previous close endpoint
            logger.info(f"  🔄 Snapshot endpoint failed, trying previous close for {symbol}")
            return self._get_previous_close_price(symbol)
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            # Try previous close as fallback
            return self._get_previous_close_price(symbol)
    
    def _get_previous_close_price(self, symbol: str) -> Optional[float]:
        """Get previous close price as fallback"""
        try:
            self._enforce_rate_limit()
            
            endpoint = f"/v2/aggs/ticker/{symbol}/prev"
            params = {"apiKey": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results and "c" in results[0]:
                    return float(results[0]["c"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting previous close for {symbol}: {e}")
            return None
    
    def get_options_contracts(self, symbol: str, expiration_date: Optional[str] = None) -> List[Dict]:
        """Get options contracts for a symbol"""
        try:
            self._enforce_rate_limit()
            
            endpoint = "/v3/reference/options/contracts"
            params = {"underlying_ticker": symbol, "apiKey": self.api_key}
            
            if expiration_date:
                params["expiration_date"] = expiration_date
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting options contracts for {symbol}: {e}")
            return []
    
    def get_historical_volatility(self, symbol: str, days: int = 30) -> Optional[float]:
        """Calculate historical volatility from price data"""
        try:
            self._enforce_rate_limit()
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
            params = {"apiKey": self.api_key}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) < 2:
                    return None
                
                # Calculate daily returns
                prices = [result["c"] for result in results]
                returns = []
                
                for i in range(1, len(prices)):
                    if prices[i-1] > 0:
                        returns.append(math.log(prices[i] / prices[i-1]))
                
                if len(returns) == 0:
                    return None
                
                # Calculate volatility (annualized)
                mean_return = np.mean(returns)
                variance = np.mean([(r - mean_return) ** 2 for r in returns])
                daily_volatility = math.sqrt(variance)
                annual_volatility = daily_volatility * math.sqrt(252)  # 252 trading days
                
                return annual_volatility
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating historical volatility for {symbol}: {e}")
            return None


class TheoreticalGreeksCalculator:
    """Main calculator for theoretical Greeks"""
    
    def __init__(self, api_key: Optional[str] = None, risk_free_rate: float = 0.05):
        self.data_fetcher = PolygonDataFetcher(api_key)
        self.bs_calculator = BlackScholesCalculator(risk_free_rate)
        self.risk_free_rate = risk_free_rate
    
    def calculate_greeks_for_symbol(self, symbol: str, expiration_date: Optional[str] = None) -> List[TheoreticalGreeks]:
        """Calculate theoretical Greeks for all available options of a symbol"""
        logger.info(f"🔍 Calculating theoretical Greeks for {symbol}")
        
        # Get current stock price
        current_price = self.data_fetcher.get_current_stock_price(symbol)
        if not current_price:
            logger.error(f"❌ Could not get current price for {symbol}")
            return []
        
        logger.info(f"  📊 Current price: ${current_price:.2f}")
        
        # Get historical volatility
        historical_vol = self.data_fetcher.get_historical_volatility(symbol)
        if not historical_vol:
            logger.warning(f"  ⚠️ Could not calculate historical volatility for {symbol}, using 30%")
            historical_vol = 0.30
        
        logger.info(f"  📈 Historical volatility: {historical_vol:.1%}")
        
        # Get options contracts
        contracts = self.data_fetcher.get_options_contracts(symbol, expiration_date)
        if not contracts:
            logger.warning(f"  ⚠️ No options contracts found for {symbol}")
            return []
        
        logger.info(f"  📋 Found {len(contracts)} options contracts")
        
        # Calculate Greeks for each contract
        greeks_list = []
        
        for contract in contracts[:20]:  # Limit to first 20 contracts
            try:
                greeks = self._calculate_greeks_for_contract(
                    symbol, contract, current_price, historical_vol
                )
                if greeks:
                    greeks_list.append(greeks)
            except Exception as e:
                logger.warning(f"  ⚠️ Error calculating Greeks for contract {contract.get('ticker', 'unknown')}: {e}")
                continue
        
        logger.info(f"  ✅ Calculated Greeks for {len(greeks_list)} contracts")
        return greeks_list
    
    def _calculate_greeks_for_contract(self, symbol: str, contract: Dict, 
                                     current_price: float, historical_vol: float) -> Optional[TheoreticalGreeks]:
        """Calculate Greeks for a specific contract"""
        try:
            # Extract contract details
            ticker = contract.get("ticker", "")
            strike_price = float(contract.get("strike_price", 0))
            expiration_date = contract.get("expiration_date", "")
            contract_type = contract.get("contract_type", "").lower()
            
            if not all([ticker, strike_price, expiration_date, contract_type]):
                return None
            
            # Calculate time to expiration
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            current_date = datetime.now()
            time_to_expiry = (exp_date - current_date).days / 365.0
            
            if time_to_expiry <= 0:
                return None
            
            # Estimate option price (this is a simplified approach)
            # In a real scenario, you'd get this from market data
            option_price = self._estimate_option_price(
                current_price, strike_price, time_to_expiry, 
                self.risk_free_rate, historical_vol, contract_type
            )
            
            # Calculate implied volatility
            implied_vol = self.bs_calculator.calculate_implied_volatility(
                option_price, current_price, strike_price, time_to_expiry,
                self.risk_free_rate, contract_type
            )
            
            # Calculate Greeks
            delta = self.bs_calculator.delta(
                current_price, strike_price, time_to_expiry,
                self.risk_free_rate, implied_vol, contract_type
            )
            
            gamma = self.bs_calculator.gamma(
                current_price, strike_price, time_to_expiry,
                self.risk_free_rate, implied_vol
            )
            
            theta = self.bs_calculator.theta(
                current_price, strike_price, time_to_expiry,
                self.risk_free_rate, implied_vol, contract_type
            )
            
            vega = self.bs_calculator.vega(
                current_price, strike_price, time_to_expiry,
                self.risk_free_rate, implied_vol
            )
            
            return TheoreticalGreeks(
                symbol=symbol,
                strike=strike_price,
                expiration=expiration_date,
                option_type=contract_type,
                current_price=current_price,
                option_price=option_price,
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                implied_volatility=implied_vol,
                time_to_expiry=time_to_expiry,
                risk_free_rate=self.risk_free_rate,
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating Greeks for contract: {e}")
            return None
    
    def _estimate_option_price(self, S: float, K: float, T: float, r: float, 
                              sigma: float, option_type: str) -> float:
        """Estimate option price using Black-Scholes"""
        if option_type == 'call':
            return self.bs_calculator.black_scholes_call(S, K, T, r, sigma)
        else:
            return self.bs_calculator.black_scholes_put(S, K, T, r, sigma)
    
    def print_greeks_summary(self, greeks_list: List[TheoreticalGreeks]):
        """Print a summary of calculated Greeks"""
        if not greeks_list:
            logger.info("No Greeks data to display")
            return
        
        logger.info(f"\n📊 Greeks Summary for {greeks_list[0].symbol}")
        logger.info("=" * 80)
        logger.info(f"{'Type':<6} {'Strike':<8} {'Expiry':<12} {'Delta':<8} {'Gamma':<8} {'Theta':<8} {'Vega':<8} {'IV':<8}")
        logger.info("-" * 80)
        
        for greeks in greeks_list[:10]:  # Show first 10
            logger.info(
                f"{greeks.option_type.upper():<6} "
                f"${greeks.strike:<7.0f} "
                f"{greeks.expiration:<12} "
                f"{greeks.delta:<8.3f} "
                f"{greeks.gamma:<8.4f} "
                f"{greeks.theta:<8.3f} "
                f"{greeks.vega:<8.3f} "
                f"{greeks.implied_volatility:<8.1%}"
            )
        
        if len(greeks_list) > 10:
            logger.info(f"... and {len(greeks_list) - 10} more contracts")


def main():
    """Main function to demonstrate theoretical Greeks calculation"""
    logger.info("🚀 Starting Theoretical Greeks Calculator")
    logger.info("=" * 60)
    
    try:
        # Initialize calculator
        calculator = TheoreticalGreeksCalculator()
        
        # Test symbols
        test_symbols = ['AAPL', 'TSLA', 'SPY']
        
        all_greeks = {}
        
        for symbol in test_symbols:
            logger.info(f"\n🔍 Processing {symbol}...")
            
            # Calculate Greeks for the symbol
            greeks_list = calculator.calculate_greeks_for_symbol(symbol)
            
            if greeks_list:
                all_greeks[symbol] = greeks_list
                calculator.print_greeks_summary(greeks_list)
            else:
                logger.warning(f"❌ No Greeks calculated for {symbol}")
        
        # Summary
        logger.info(f"\n" + "=" * 60)
        logger.info("✅ Theoretical Greeks calculation complete!")
        
        total_contracts = sum(len(greeks) for greeks in all_greeks.values())
        logger.info(f"📊 Results:")
        logger.info(f"  - Symbols processed: {len(all_greeks)}")
        logger.info(f"  - Total contracts: {total_contracts}")
        
        if total_contracts > 0:
            logger.info("🎉 Successfully calculated theoretical Greeks!")
            logger.info("💡 Note: These are theoretical values based on Black-Scholes model")
            logger.info("💡 For real trading, consider using actual market prices when available")
        else:
            logger.warning("⚠️ No Greeks calculated - check data availability")
        
    except Exception as e:
        logger.error(f"❌ Calculation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 