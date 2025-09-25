"""
Mock Options Data Service
Provides synthetic options data for backtesting when real options data is unavailable
"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MockOptionsContract:
    """Mock options contract with realistic data"""
    symbol: str
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class MockOptionsDataService:
    """Mock options data service for backtesting"""
    
    def __init__(self):
        self.logger = logger
        self.contracts_cache = {}
        
    def get_liquid_options(self, symbol: str, expiration_days: int = 30) -> List[MockOptionsContract]:
        """
        Get liquid options contracts for a symbol
        
        Args:
            symbol: Stock symbol
            expiration_days: Days to expiration (default 30)
            
        Returns:
            List of liquid options contracts
        """
        try:
            # Get current stock price (mock)
            current_price = self._get_mock_stock_price(symbol)
            
            # Generate options chain around current price
            contracts = []
            
            # Generate strikes around current price (±20%)
            strikes = self._generate_strikes(current_price, num_strikes=10)
            
            # Generate expiration dates
            expirations = self._generate_expirations(expiration_days)
            
            for strike in strikes:
                for expiration in expirations:
                    # Generate call option
                    call_contract = self._create_mock_contract(
                        symbol, strike, expiration, 'call', current_price
                    )
                    contracts.append(call_contract)
                    
                    # Generate put option
                    put_contract = self._create_mock_contract(
                        symbol, strike, expiration, 'put', current_price
                    )
                    contracts.append(put_contract)
            
            # Filter for liquid contracts (volume > 10, bid-ask spread < 20%)
            liquid_contracts = [
                contract for contract in contracts
                if contract.volume >= 10 and self._calculate_bid_ask_spread(contract) < 0.20
            ]
            
            self.logger.info(f"Generated {len(liquid_contracts)} liquid options contracts for {symbol}")
            return liquid_contracts
            
        except Exception as e:
            self.logger.error(f"Error generating mock options data for {symbol}: {e}")
            return []
    
    def _get_mock_stock_price(self, symbol: str) -> float:
        """Get mock stock price for a symbol"""
        # Mock prices for common symbols
        mock_prices = {
            'AAPL': 175.0,
            'MSFT': 380.0,
            'GOOGL': 140.0,
            'TSLA': 250.0,
            'NVDA': 450.0,
            'AMD': 120.0,
            'PYPL': 60.0,
            'INTC': 35.0,
        }
        
        # Add some random variation
        base_price = mock_prices.get(symbol, 100.0)
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        return base_price * (1 + variation)
    
    def _generate_strikes(self, current_price: float, num_strikes: int = 10) -> List[float]:
        """Generate strike prices around current price"""
        # Generate strikes from 80% to 120% of current price
        min_strike = current_price * 0.8
        max_strike = current_price * 1.2
        
        # Round to nearest $5 for stocks under $100, $10 for stocks over $100
        strike_increment = 5.0 if current_price < 100 else 10.0
        
        strikes = []
        strike = min_strike
        while strike <= max_strike and len(strikes) < num_strikes:
            # Round to nearest increment
            rounded_strike = round(strike / strike_increment) * strike_increment
            if rounded_strike not in strikes:
                strikes.append(rounded_strike)
            strike += strike_increment
        
        return sorted(strikes)
    
    def _generate_expirations(self, expiration_days: int = 30) -> List[datetime]:
        """Generate expiration dates"""
        expirations = []
        current_date = datetime.now()
        
        # Generate 3 expiration dates
        for i in range(3):
            days_ahead = expiration_days + (i * 30)  # 30, 60, 90 days
            expiration = current_date + timedelta(days=days_ahead)
            expirations.append(expiration)
        
        return expirations
    
    def _create_mock_contract(self, symbol: str, strike: float, expiration: datetime, 
                            option_type: str, current_price: float) -> MockOptionsContract:
        """Create a mock options contract with realistic Greeks"""
        
        # Calculate time to expiration
        time_to_exp = (expiration - datetime.now()).days / 365.0
        
        # Mock implied volatility (higher for out-of-the-money options)
        moneyness = strike / current_price
        if option_type == 'call':
            itm = moneyness < 0.95  # In the money if strike < 95% of current price
        else:
            itm = moneyness > 1.05  # In the money if strike > 105% of current price
        
        implied_vol = 0.25 + random.uniform(-0.05, 0.05)  # 20-30% IV
        if not itm:
            implied_vol += 0.05  # Higher IV for OTM options
        
        # Mock Greeks using Black-Scholes approximation
        delta = self._calculate_mock_delta(current_price, strike, time_to_exp, implied_vol, option_type)
        gamma = self._calculate_mock_gamma(current_price, strike, time_to_exp, implied_vol)
        theta = self._calculate_mock_theta(current_price, strike, time_to_exp, implied_vol, option_type)
        vega = self._calculate_mock_vega(current_price, strike, time_to_exp, implied_vol)
        rho = self._calculate_mock_rho(current_price, strike, time_to_exp, implied_vol, option_type)
        
        # Mock option price
        option_price = self._calculate_mock_option_price(current_price, strike, time_to_exp, implied_vol, option_type)
        
        # Mock bid-ask spread (1-5% of option price)
        spread_pct = random.uniform(0.01, 0.05)
        spread = option_price * spread_pct
        
        bid = max(0.01, option_price - spread/2)
        ask = option_price + spread/2
        last_price = random.uniform(bid, ask)
        
        # Mock volume and open interest
        volume = random.randint(10, 1000)
        open_interest = random.randint(100, 10000)
        
        return MockOptionsContract(
            symbol=symbol,
            strike=strike,
            expiration=expiration,
            option_type=option_type,
            bid=round(bid, 2),
            ask=round(ask, 2),
            last_price=round(last_price, 2),
            volume=volume,
            open_interest=open_interest,
            implied_volatility=round(implied_vol, 4),
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )
    
    def _calculate_mock_delta(self, S: float, K: float, T: float, sigma: float, option_type: str) -> float:
        """Calculate mock delta using simplified Black-Scholes"""
        if option_type == 'call':
            # Simplified call delta
            return min(1.0, max(0.0, (S - K) / S * 0.8 + 0.5))
        else:
            # Simplified put delta
            return max(-1.0, min(0.0, (K - S) / S * 0.8 - 0.5))
    
    def _calculate_mock_gamma(self, S: float, K: float, T: float, sigma: float) -> float:
        """Calculate mock gamma"""
        return random.uniform(0.001, 0.01)
    
    def _calculate_mock_theta(self, S: float, K: float, T: float, sigma: float, option_type: str) -> float:
        """Calculate mock theta (time decay)"""
        # Options lose value over time
        base_theta = -random.uniform(0.01, 0.05)
        return base_theta
    
    def _calculate_mock_vega(self, S: float, K: float, T: float, sigma: float) -> float:
        """Calculate mock vega (volatility sensitivity)"""
        return random.uniform(0.1, 0.3)
    
    def _calculate_mock_rho(self, S: float, K: float, T: float, sigma: float, option_type: str) -> float:
        """Calculate mock rho (interest rate sensitivity)"""
        return random.uniform(0.01, 0.05)
    
    def _calculate_mock_option_price(self, S: float, K: float, T: float, sigma: float, option_type: str) -> float:
        """Calculate mock option price using simplified Black-Scholes"""
        # Simplified intrinsic value calculation
        if option_type == 'call':
            intrinsic = max(0, S - K)
        else:
            intrinsic = max(0, K - S)
        
        # Add time value (simplified)
        time_value = S * sigma * np.sqrt(T) * random.uniform(0.1, 0.3)
        
        return max(0.01, intrinsic + time_value)
    
    def _calculate_bid_ask_spread(self, contract: MockOptionsContract) -> float:
        """Calculate bid-ask spread as percentage"""
        if contract.ask <= 0:
            return 1.0  # 100% spread for invalid prices
        return (contract.ask - contract.bid) / contract.ask
    
    def get_options_chain(self, symbol: str, expiration: Optional[datetime] = None) -> Dict[str, List[MockOptionsContract]]:
        """Get options chain for a symbol"""
        contracts = self.get_liquid_options(symbol)
        
        if expiration:
            contracts = [c for c in contracts if c.expiration.date() == expiration.date()]
        
        # Group by expiration
        chain = {}
        for contract in contracts:
            exp_key = contract.expiration.strftime('%Y-%m-%d')
            if exp_key not in chain:
                chain[exp_key] = []
            chain[exp_key].append(contract)
        
        return chain
    
    def get_contract_by_strike_and_type(self, symbol: str, strike: float, option_type: str, 
                                      expiration: Optional[datetime] = None) -> Optional[MockOptionsContract]:
        """Get specific options contract"""
        contracts = self.get_liquid_options(symbol)
        
        for contract in contracts:
            if (contract.strike == strike and 
                contract.option_type == option_type and
                (expiration is None or contract.expiration.date() == expiration.date())):
                return contract
        
        return None


# Global instance for easy access
_mock_options_service = None

def get_mock_options_service() -> MockOptionsDataService:
    """Get global mock options service instance"""
    global _mock_options_service
    if _mock_options_service is None:
        _mock_options_service = MockOptionsDataService()
    return _mock_options_service

