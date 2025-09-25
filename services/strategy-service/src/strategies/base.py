"""
Base strategy class for all trading strategies
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
import logging

from ..core.types import TradeSignal
# Import error handler if available, otherwise use basic logging
try:
    from ..utils.error_handler import StrategyError, ErrorHandler
except ImportError:
    import logging
    class StrategyError(Exception):
        def __init__(self, message: str, context: dict = None):
            super().__init__(message)
            self.context = context if context is not None else {}
    
    class ErrorHandler:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        def handle_error(self, error, context):
            self.logger.error(f"Error in {context}: {error}")

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.is_active = True
        self.error_handler = ErrorHandler()
        self.options_service = None  # Will be set by strategy service
        
    @abstractmethod
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """
        Generate trading signal based on market data
        
        Args:
            symbol: Trading symbol
            data: Market data dataframe with technical indicators
            historical_date: Historical date (YYYY-MM-DD) for backtesting, or None for current date
            
        Returns:
            TradeSignal or None if no signal
        """
        pass
    
    def can_execute_with_options_data(self) -> bool:
        """
        Check if strategy can execute with available options data.
        
        Returns:
            True if strategy can execute, False otherwise
        """
        try:
            # Check if strategy requires options data
            if hasattr(self, 'requires_options_data') and self.requires_options_data:
                # Check if options service is available
                if self.options_service is None:
                    logger.warning(f"Strategy {self.name} requires options data but no service available")
                    return False
                
                # Try to get options data for a test symbol
                test_symbol = "AAPL"  # Default test symbol
                try:
                    options = self.options_service.get_liquid_options(test_symbol, min_volume=10)
                    return len(options) > 0
                except Exception as e:
                    logger.warning(f"Failed to get options data for {test_symbol}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            error_context = {"strategy": self.name, "method": "can_execute_with_options_data"}
            self.error_handler.handle_error(e, error_context)
            return False
    
    def fallback_to_stock_strategy(self) -> Optional['BaseStrategy']:
        """
        Fall back to a stock-based strategy when options data is unavailable.
        
        Returns:
            Stock-based strategy instance or None if no fallback available
        """
        try:
            # Check if strategy has a stock-based fallback
            if hasattr(self, 'stock_fallback_strategy'):
                fallback_class = self.stock_fallback_strategy
                fallback_config = self.config.copy()
                fallback_config['is_fallback'] = True
                
                logger.info(f"Falling back to stock strategy: {fallback_class.__name__}")
                return fallback_class(config=fallback_config)
            
            # Generic fallback to RSI strategy
            from .momentum.rsi_strategy import RSIStrategy
            fallback_config = self.config.copy()
            fallback_config['is_fallback'] = True
            fallback_config['fallback_from'] = self.name
            
            logger.info(f"Using generic RSI fallback for {self.name}")
            return RSIStrategy(config=fallback_config)
            
        except Exception as e:
            error_context = {"strategy": self.name, "method": "fallback_to_stock_strategy"}
            self.error_handler.handle_error(e, error_context)
            return None
    
    async def handle_options_data_unavailable(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """
        Handle the case when options data is unavailable.
        
        Args:
            symbol: Trading symbol
            data: Market data dataframe
            historical_date: Historical date for backtesting
            
        Returns:
            TradeSignal from fallback strategy or None
        """
        try:
            # Try to get fallback strategy
            fallback_strategy = self.fallback_to_stock_strategy()
            
            if fallback_strategy:
                logger.info(f"Using fallback strategy for {self.name} on {symbol}")
                return await fallback_strategy.generate_signal(symbol, data, historical_date)
            else:
                logger.warning(f"No fallback strategy available for {self.name}")
                return None
                
        except Exception as e:
            error_context = {
                "strategy": self.name,
                "symbol": symbol,
                "method": "handle_options_data_unavailable"
            }
            self.error_handler.handle_error(e, error_context)
            return None
    
    def set_options_service(self, options_service):
        """Set the options data service"""
        self.options_service = options_service
    
    def calculate_position_size(self, capital: float, price: float, risk_percentage: float = 0.02) -> float:
        """Calculate position size based on risk management"""
        risk_amount = capital * risk_percentage
        position_size = risk_amount / price
        return position_size
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "is_active": self.is_active,
            "config": self.config,
            "can_execute_with_options": self.can_execute_with_options_data(),
            "has_fallback": hasattr(self, 'stock_fallback_strategy')
        }
    
    def activate(self):
        """Activate the strategy"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate the strategy"""
        self.is_active = False 