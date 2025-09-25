"""
Error Handling and Logging Improvements
=======================================
Centralized error handling and logging for the trading system.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Union
from datetime import datetime
import json

# Configure structured logging
def setup_trading_logger(name: str = "trading_system", level: int = logging.INFO) -> logging.Logger:
    """Setup structured logging for trading system"""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        logger.setLevel(level)
    
    return logger

class TradingError(Exception):
    """Base exception for trading system errors"""
    
    def __init__(self, message: str, error_code: str = "TRADING_ERROR", context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()

class BacktestError(TradingError):
    """Exception for backtest-related errors"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BACKTEST_ERROR", context)

class OptionsDataError(TradingError):
    """Exception for options data-related errors"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OPTIONS_DATA_ERROR", context)

class StrategyError(TradingError):
    """Exception for strategy-related errors"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "STRATEGY_ERROR", context)

class ErrorHandler:
    """Centralized error handling for trading system"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_trading_logger()
    
    def handle_error(self, 
                    error: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    raise_error: bool = True) -> Optional[Dict[str, Any]]:
        """Handle errors with logging and optional recovery"""
        
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Add traceback for debugging
        if isinstance(error, TradingError):
            error_context["error_code"] = error.error_code
            error_context["original_context"] = error.context
        
        # Log the error
        self.logger.error(f"Error occurred: {error_context}")
        
        # Log traceback for debugging
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Handle specific error types
        if isinstance(error, OptionsDataError):
            return self._handle_options_data_error(error, error_context)
        elif isinstance(error, BacktestError):
            return self._handle_backtest_error(error, error_context)
        elif isinstance(error, StrategyError):
            return self._handle_strategy_error(error, error_context)
        else:
            return self._handle_generic_error(error, error_context)
    
    def _handle_options_data_error(self, error: OptionsDataError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle options data errors with fallback suggestions"""
        
        recovery_suggestions = [
            "Use mock options data for backtesting",
            "Check options data service availability",
            "Verify symbol has options contracts available"
        ]
        
        context["recovery_suggestions"] = recovery_suggestions
        context["fallback_available"] = True
        
        self.logger.warning(f"Options data error - fallback options available: {recovery_suggestions}")
        
        return context
    
    def _handle_backtest_error(self, error: BacktestError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle backtest errors with debugging information"""
        
        context["debug_info"] = {
            "check_data_availability": "Verify historical data exists",
            "check_strategy_configuration": "Verify strategy parameters",
            "check_risk_parameters": "Verify position sizing and risk limits"
        }
        
        self.logger.error(f"Backtest error - check configuration: {context['debug_info']}")
        
        return context
    
    def _handle_strategy_error(self, error: StrategyError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategy errors with fallback suggestions"""
        
        context["fallback_strategies"] = [
            "Switch to stock-based strategies",
            "Use simpler technical indicators",
            "Reduce position size or risk parameters"
        ]
        
        self.logger.warning(f"Strategy error - fallback strategies available: {context['fallback_strategies']}")
        
        return context
    
    def _handle_generic_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic errors"""
        
        context["generic_recovery"] = [
            "Check system logs for more details",
            "Verify all dependencies are available",
            "Restart the service if necessary"
        ]
        
        self.logger.error(f"Generic error - recovery suggestions: {context['generic_recovery']}")
        
        return context

def log_backtest_progress(stage: str, details: Dict[str, Any], logger: Optional[logging.Logger] = None):
    """Log backtest progress with structured information"""
    
    if logger is None:
        logger = setup_trading_logger()
    
    progress_info = {
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    
    logger.info(f"Backtest Progress - {stage}: {json.dumps(details, default=str)}")

def log_strategy_execution(strategy_name: str, 
                          symbol: str, 
                          action: str, 
                          details: Dict[str, Any],
                          logger: Optional[logging.Logger] = None):
    """Log strategy execution with structured information"""
    
    if logger is None:
        logger = setup_trading_logger()
    
    execution_info = {
        "strategy": strategy_name,
        "symbol": symbol,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    
    logger.info(f"Strategy Execution: {json.dumps(execution_info, default=str)}")

# Global error handler instance
error_handler = ErrorHandler()


