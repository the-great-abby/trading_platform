"""
Mock Options Data Service
========================
Provides mock options data for backtesting when real options data is unavailable.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.core.types import MockOptionContract

# Mock data generation functions
def get_standard_strikes(current_price: float, num_strikes: int = 5) -> List[float]:
    """Generate standard strike prices around current price."""
    strikes = []
    step = current_price * 0.05  # 5% steps
    for i in range(-num_strikes//2, num_strikes//2 + 1):
        strikes.append(round(current_price + i * step, 2))
    return strikes

def get_standard_expirations(current_date: datetime, num_expirations: int = 3) -> List[datetime]:
    """Generate standard expiration dates."""
    expirations = []
    for i in range(1, num_expirations + 1):
        expirations.append(current_date + timedelta(days=30 * i))
    return expirations

class MockOptionsDataGenerator:
    """Generates mock options data for backtesting."""
    
    def __init__(self, base_iv: float = 0.25, volume_range: tuple = (100, 10000)):
        self.logger = logging.getLogger(__name__)
        self.base_iv = base_iv
        self.volume_range = volume_range
    
    def generate_options_chain(self, symbol: str, current_price: float, 
                              expirations: List[datetime], strikes: List[float]) -> List[MockOptionContract]:
        """Generate a complete options chain."""
        options = []
        # Use the passed parameters instead of generating them
        
        for strike in strikes:
            for expiration in expirations:
                # Generate call option
                call_option = self._generate_option_contract(
                    symbol, 'call', strike, expiration, current_price, datetime.now()
                )
                options.append(call_option)
                
                # Generate put option
                put_option = self._generate_option_contract(
                    symbol, 'put', strike, expiration, current_price, datetime.now()
                )
                options.append(put_option)
        
        return options
    
    def _generate_option_contract(self, symbol: str, option_type: str, strike: float,
                                 expiration: datetime, current_price: float, 
                                 current_date: datetime) -> MockOptionContract:
        """Generate a single mock option contract."""
        import random
        
        # Simple mock pricing
        time_to_exp = (expiration - current_date).days / 365.0
        intrinsic_value = max(0, current_price - strike) if option_type == 'call' else max(0, strike - current_price)
        time_value = random.uniform(0.5, 5.0) * time_to_exp
        
        price = intrinsic_value + time_value
        volume = random.randint(100, 5000)
        open_interest = random.randint(1000, 20000)
        
        # Mock Greeks
        delta = random.uniform(0.1, 0.9) if option_type == 'call' else random.uniform(-0.9, -0.1)
        gamma = random.uniform(0.01, 0.1)
        theta = random.uniform(-0.1, -0.01)
        vega = random.uniform(0.05, 0.2)
        implied_volatility = random.uniform(0.2, 0.4)
        
        return MockOptionContract(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            expiration=expiration,
            price=price,
            volume=volume,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            implied_volatility=implied_volatility,
            bid=price * 0.95,
            ask=price * 1.05,
            open_interest=open_interest
        )
# Import error handler if available, otherwise use basic logging
try:
    from src.utils.error_handler import ErrorHandler
    OPTIONS_DATA_ERROR_AVAILABLE = True
except ImportError:
    OPTIONS_DATA_ERROR_AVAILABLE = False
    class ErrorHandler:
        def __init__(self):
            pass
        def handle_error(self, error, context):
            logging.error(f"Error in {context}: {error}")

class OptionsDataError(Exception):
    """Custom exception for options data errors."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context if context is not None else {}

logger = logging.getLogger(__name__)

class MockOptionsDataService:
    """Service that provides mock options data for backtesting"""
    
    def __init__(self, base_iv: float = 0.25, volume_range: tuple = (100, 10000)):
        self.generator = MockOptionsDataGenerator(base_iv, volume_range)
        self.error_handler = ErrorHandler()
        self.cache = {}  # Simple cache for generated data
        
    def get_liquid_options(self, symbol: str, min_volume: int = 100) -> List[Dict[str, Any]]:
        """
        Get liquid options for a symbol with minimum volume requirement.
        
        Args:
            symbol: Stock symbol
            min_volume: Minimum volume requirement
            
        Returns:
            List of option contracts meeting volume requirements
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{min_volume}"
            if cache_key in self.cache:
                logger.info(f"Using cached options data for {symbol}")
                return self.cache[cache_key]
            
            # Generate mock options chain
            options_chain = self._generate_mock_chain(symbol)
            
            # Filter by volume and convert to dict format
            liquid_options = []
            for option in options_chain:
                if option.volume >= min_volume:
                    option_dict = {
                        'symbol': option.symbol,
                        'option_type': option.option_type,
                        'strike': option.strike,
                        'expiration': option.expiration,
                        'price': option.price,
                        'volume': option.volume,
                        'delta': option.delta,
                        'gamma': option.gamma,
                        'theta': option.theta,
                        'vega': option.vega,
                        'implied_volatility': option.implied_volatility,
                        'bid': option.bid,
                        'ask': option.ask,
                        'open_interest': option.open_interest
                    }
                    liquid_options.append(option_dict)
            
            # Cache the result
            self.cache[cache_key] = liquid_options
            
            logger.info(f"Generated {len(liquid_options)} liquid options for {symbol}")
            return liquid_options
            
        except Exception as e:
            error_context = {
                "symbol": symbol,
                "min_volume": min_volume,
                "service": "mock_options_data"
            }
            self.error_handler.handle_error(e, error_context)
            raise OptionsDataError(f"Failed to get liquid options for {symbol}: {e}", error_context)
    
    def get_liquid_options_with_historical_support(self, 
                                                   symbol: str, 
                                                   min_volume: int = 100,
                                                   historical_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get liquid options with historical data support.
        
        Args:
            symbol: Stock symbol
            min_volume: Minimum volume requirement
            historical_date: Historical date for backtesting (YYYY-MM-DD format)
            
        Returns:
            List of option contracts for the specified date
        """
        try:
            # For mock data, we can generate historical options
            # In a real implementation, this would fetch historical options data
            
            if historical_date:
                # Parse historical date
                hist_date = datetime.strptime(historical_date, "%Y-%m-%d")
                
                # Adjust expiration dates relative to historical date
                current_date = datetime.now()
                days_diff = (current_date - hist_date).days
                
                # Generate options chain with adjusted dates
                options_chain = self._generate_mock_chain(symbol, date_offset=days_diff)
                
                # Filter and convert to dict format
                liquid_options = []
                for option in options_chain:
                    if option.volume >= min_volume:
                        option_dict = {
                            'symbol': option.symbol,
                            'option_type': option.option_type,
                            'strike': option.strike,
                            'expiration': option.expiration,
                            'price': option.price,
                            'volume': option.volume,
                            'delta': option.delta,
                            'gamma': option.gamma,
                            'theta': option.theta,
                            'vega': option.vega,
                            'implied_volatility': option.implied_volatility,
                            'bid': option.bid,
                            'ask': option.ask,
                            'open_interest': option.open_interest,
                            'historical_date': historical_date
                        }
                        liquid_options.append(option_dict)
                
                logger.info(f"Generated {len(liquid_options)} historical options for {symbol} on {historical_date}")
                return liquid_options
            else:
                # Use regular method for current data
                return self.get_liquid_options(symbol, min_volume)
                
        except Exception as e:
            error_context = {
                "symbol": symbol,
                "min_volume": min_volume,
                "historical_date": historical_date,
                "service": "mock_options_data"
            }
            self.error_handler.handle_error(e, error_context)
            raise OptionsDataError(f"Failed to get historical options for {symbol}: {e}", error_context)
    
    def generate_mock_options_chain(self, symbol: str, current_price: float = None) -> List[MockOptionContract]:
        """
        Generate a complete mock options chain for a symbol.
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price (if None, uses default)
            
        Returns:
            List of MockOptionContract objects
        """
        try:
            # Use default price if not provided
            if current_price is None:
                current_price = self._get_default_price(symbol)
            
            # Generate standard strikes and expirations
            strikes = get_standard_strikes(current_price)
            expirations = get_standard_expirations(datetime.now())
            
            # Generate options chain
            options_chain = self.generator.generate_options_chain(
                symbol, current_price, expirations, strikes
            )
            
            logger.info(f"Generated {len(options_chain)} mock options for {symbol}")
            return options_chain
            
        except Exception as e:
            error_context = {
                "symbol": symbol,
                "current_price": current_price,
                "service": "mock_options_data"
            }
            self.error_handler.handle_error(e, error_context)
            raise OptionsDataError(f"Failed to generate mock options chain for {symbol}: {e}", error_context)
    
    def _generate_mock_chain(self, symbol: str, date_offset: int = 0) -> List[MockOptionContract]:
        """Generate mock options chain with optional date offset"""
        current_price = self._get_default_price(symbol)
        
        # Adjust strikes and expirations
        strikes = get_standard_strikes(current_price)
        expirations = get_standard_expirations(datetime.now())
        
        # Apply date offset for historical data
        if date_offset != 0:
            expirations = [exp + timedelta(days=date_offset) for exp in expirations]
        
        return self.generator.generate_options_chain(
            symbol, current_price, expirations, strikes
        )
    
    def _get_default_price(self, symbol: str) -> float:
        """Get default price for a symbol"""
        # Default prices for common symbols
        default_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'GOOGL': 2500.0,
            'AMZN': 3000.0,
            'TSLA': 200.0,
            'AMD': 100.0,
            'INTC': 30.0,
            'PYPL': 60.0,
            'NVDA': 400.0,
            'META': 300.0
        }
        
        return default_prices.get(symbol.upper(), 100.0)  # Default to $100
    
    def can_execute_with_options_data(self) -> bool:
        """Check if service can provide options data"""
        return True  # Mock service always can provide data
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "service_type": "mock_options_data",
            "status": "active",
            "cache_size": len(self.cache),
            "generator_config": {
                "base_iv": self.generator.base_iv,
                "volume_range": self.generator.volume_range
            },
            "supported_symbols": list(self._get_default_price("").keys()) if hasattr(self, '_get_default_price') else []
        }

# Global instance for easy access
mock_options_data_service = MockOptionsDataService()
