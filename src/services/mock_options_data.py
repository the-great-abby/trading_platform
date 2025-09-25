"""
Mock Options Data Generation Module
==================================
Generates synthetic options data for backtesting when real options data is unavailable.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MockOptionContract:
    """Mock option contract data structure"""
    symbol: str
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: datetime
    price: float
    volume: int
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    bid: float
    ask: float
    open_interest: int

class MockOptionsDataGenerator:
    """Generates synthetic options data for backtesting"""
    
    def __init__(self, base_iv: float = 0.25, volume_range: tuple = (100, 10000)):
        self.base_iv = base_iv
        self.volume_range = volume_range
        
    def generate_options_chain(self, 
                              symbol: str, 
                              current_price: float,
                              expiration_dates: List[datetime],
                              strikes: List[float]) -> List[MockOptionContract]:
        """Generate a complete options chain for a symbol"""
        
        options_chain = []
        
        for expiration in expiration_dates:
            for strike in strikes:
                # Generate both call and put options
                for option_type in ['call', 'put']:
                    option = self._generate_single_option(
                        symbol, option_type, strike, expiration, current_price
                    )
                    options_chain.append(option)
        
        logger.info(f"Generated {len(options_chain)} mock options for {symbol}")
        return options_chain
    
    def _generate_single_option(self, 
                               symbol: str,
                               option_type: str,
                               strike: float,
                               expiration: datetime,
                               current_price: float) -> MockOptionContract:
        """Generate a single mock option contract"""
        
        # Calculate days to expiration
        dte = (expiration - datetime.now()).days
        
        # Generate realistic option price using Black-Scholes approximation
        option_price = self._calculate_option_price(
            current_price, strike, dte, option_type
        )
        
        # Generate Greeks
        delta = self._calculate_delta(current_price, strike, dte, option_type)
        gamma = self._calculate_gamma(current_price, strike, dte)
        theta = self._calculate_theta(current_price, strike, dte, option_type)
        vega = self._calculate_vega(current_price, strike, dte)
        
        # Generate volume and open interest
        volume = np.random.randint(*self.volume_range)
        open_interest = np.random.randint(volume, volume * 3)
        
        # Generate bid/ask spread
        spread = option_price * 0.02  # 2% spread
        bid = option_price - spread / 2
        ask = option_price + spread / 2
        
        return MockOptionContract(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            expiration=expiration,
            price=option_price,
            volume=volume,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            implied_volatility=self.base_iv,
            bid=bid,
            ask=ask,
            open_interest=open_interest
        )
    
    def _calculate_option_price(self, 
                               current_price: float,
                               strike: float,
                               dte: int,
                               option_type: str) -> float:
        """Simple Black-Scholes approximation for option pricing"""
        
        # Avoid division by zero
        if dte <= 0:
            dte = 1
        
        # Time to expiration in years
        t = dte / 365.0
        
        # Risk-free rate (assume 3%)
        r = 0.03
        
        # Calculate moneyness
        moneyness = current_price / strike
        
        # Base price calculation
        if option_type == 'call':
            intrinsic_value = max(0, current_price - strike)
        else:  # put
            intrinsic_value = max(0, strike - current_price)
        
        # Time value (simplified)
        time_value = current_price * 0.05 * np.sqrt(t) * self.base_iv
        
        return max(0.01, intrinsic_value + time_value)
    
    def _calculate_delta(self, 
                        current_price: float,
                        strike: float,
                        dte: int,
                        option_type: str) -> float:
        """Calculate option delta"""
        
        moneyness = current_price / strike
        
        if option_type == 'call':
            # Call delta approximation
            if moneyness > 1.1:
                return 0.8
            elif moneyness < 0.9:
                return 0.2
            else:
                return 0.5
        else:  # put
            # Put delta approximation
            if moneyness > 1.1:
                return -0.2
            elif moneyness < 0.9:
                return -0.8
            else:
                return -0.5
    
    def _calculate_gamma(self, current_price: float, strike: float, dte: int) -> float:
        """Calculate option gamma"""
        # Simplified gamma calculation
        return 0.01
    
    def _calculate_theta(self, 
                        current_price: float,
                        strike: float,
                        dte: int,
                        option_type: str) -> float:
        """Calculate option theta (time decay)"""
        # Theta is typically negative (time decay)
        return -current_price * 0.001 * self.base_iv / np.sqrt(dte / 365.0)
    
    def _calculate_vega(self, current_price: float, strike: float, dte: int) -> float:
        """Calculate option vega (volatility sensitivity)"""
        return current_price * 0.1 * np.sqrt(dte / 365.0)

def get_standard_strikes(current_price: float, num_strikes: int = 10) -> List[float]:
    """Generate standard strike prices around current price"""
    
    # Create strikes in 2.5% increments
    increment = current_price * 0.025
    
    strikes = []
    for i in range(-num_strikes//2, num_strikes//2 + 1):
        strike = current_price + (i * increment)
        strikes.append(round(strike, 2))
    
    return strikes

def get_standard_expirations(num_expirations: int = 4) -> List[datetime]:
    """Generate standard expiration dates"""
    
    expirations = []
    base_date = datetime.now()
    
    # Weekly expirations for next month
    for weeks in [1, 2, 3, 4]:
        expiration = base_date + timedelta(weeks=weeks)
        expirations.append(expiration)
    
    return expirations


