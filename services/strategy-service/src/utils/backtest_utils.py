"""
Backtest Utilities - Helper functions for backtest operations
"""

import os
import inspect
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def get_backtest_name(caller_depth: int = 2) -> Optional[str]:
    """
    Extract the backtest name from the calling script
    
    Args:
        caller_depth: How many levels up the call stack to look (default: 2)
        
    Returns:
        The name of the backtest file, or None if not found
    """
    try:
        # Get the call stack
        frame = inspect.currentframe()
        for _ in range(caller_depth):
            if frame is None:
                break
            frame = frame.f_back
        
        if frame is None:
            logger.warning("Could not determine backtest name - frame is None")
            return None
        
        # Get the filename from the frame
        filename = frame.f_code.co_filename
        
        # Extract just the filename without path
        backtest_name = os.path.basename(filename)
        
        # Remove .py extension if present
        if backtest_name.endswith('.py'):
            backtest_name = backtest_name[:-3]
        
        logger.info(f"Detected backtest name: {backtest_name}")
        return backtest_name
        
    except Exception as e:
        logger.warning(f"Could not determine backtest name: {e}")
        return None


def get_backtest_name_from_path(file_path: str) -> str:
    """
    Extract backtest name from a file path
    
    Args:
        file_path: Path to the backtest file
        
    Returns:
        The name of the backtest file
    """
    # Get just the filename
    filename = os.path.basename(file_path)
    
    # Remove .py extension if present
    if filename.endswith('.py'):
        filename = filename[:-3]
    
    return filename


def get_backtest_name_from_script() -> Optional[str]:
    """
    Get backtest name from the current script being executed
    
    Returns:
        The name of the current script, or None if not found
    """
    try:
        # Get the main module's file path
        import sys
        if hasattr(sys, '_getframe'):
            frame = sys._getframe(1)
            while frame:
                if frame.f_globals.get('__name__') == '__main__':
                    filename = frame.f_code.co_filename
                    return get_backtest_name_from_path(filename)
                frame = frame.f_back
        
        # Fallback: try to get from sys.argv[0]
        if len(sys.argv) > 0:
            return get_backtest_name_from_path(sys.argv[0])
        
        return None
        
    except Exception as e:
        logger.warning(f"Could not determine script name: {e}")
        return None


def format_backtest_name(name: str) -> str:
    """
    Format a backtest name for display
    
    Args:
        name: Raw backtest name
        
    Returns:
        Formatted backtest name
    """
    # Replace underscores with spaces
    formatted = name.replace('_', ' ')
    
    # Capitalize first letter of each word
    formatted = ' '.join(word.capitalize() for word in formatted.split())
    
    return formatted


def get_backtest_summary(backtest_name: str, strategy_name: str, symbols: list, start_date: str, end_date: str) -> str:
    """
    Generate a summary string for a backtest run
    
    Args:
        backtest_name: Name of the backtest file
        strategy_name: Name of the strategy
        symbols: List of symbols tested
        start_date: Start date
        end_date: End date
        
    Returns:
        Formatted summary string
    """
    formatted_name = format_backtest_name(backtest_name)
    symbols_str = ', '.join(symbols)
    
    summary = f"{formatted_name} - {strategy_name} on {symbols_str} ({start_date} to {end_date})"
    
    return summary 