#!/usr/bin/env python3
"""
Demo: Historical Options Snapshots for Backtesting

This script demonstrates how to use the enhanced options data service
with historical snapshots for more effective backtesting.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.market_data.enhanced_options_data_service import get_enhanced_options_service
from src.services.market_data.cached_market_data_manager import CachedMarketDataManager
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.utils.backtest_utils import get_backtest_name_from_script

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_historical_options_data(symbols: List[str], start_date: date, end_date: date) -> Dict[str, int]:
    """
    Set up historical options data for backtesting
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for historical data
        end_date: End date for historical data
        
    Returns:
        Dictionary with symbol -> snapshot count
    """
    logger.info(f"Setting up historical options data for {len(symbols)} symbols from {start_date} to {end_date}")
    
    enhanced_service = get_enhanced_options_service()
    
    # Batch store historical snapshots
    results = enhanced_service.batch_store_historical_snapshots(symbols, start_date, end_date)
    
    total_snapshots = sum(results.values())
    logger.info(f"✅ Stored {total_snapshots} historical snapshots across {len(symbols)} symbols")
    
    for symbol, count in results.items():
        logger.info(f"  {symbol}: {count} snapshots")
    
    return results


def run_historical_greeks_backtest(symbol: str, start_date: date, end_date: date, backtest_name: str) -> List[Dict]:
    """
    Run a backtest using historical Greeks data
    
    Args:
        symbol: Stock symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        backtest_name: Name of the backtest file
        
    Returns:
        List of backtest results
    """
    logger.info(f"Running historical Greeks backtest for {symbol} from {start_date} to {end_date}")
    logger.info(f"Backtest name: {backtest_name}")
    
    enhanced_service = get_enhanced_options_service()
    market_data_manager = CachedMarketDataManager()
    strategy = GreeksEnhancedStrategy()
    
    # Get available historical dates
    available_dates = enhanced_service.get_available_historical_dates(symbol)
    logger.info(f"Found {len(available_dates)} available historical dates for {symbol}")
    
    if not available_dates:
        logger.warning(f"No historical data available for {symbol}")
        return []
    
    # Filter dates within backtest range
    backtest_dates = [d for d in available_dates if start_date <= d <= end_date]
    logger.info(f"Using {len(backtest_dates)} dates for backtest")
    
    results = []
    
    for snapshot_date in backtest_dates:
        try:
            # Get stock price for this date
            date_str = snapshot_date.strftime("%Y-%m-%d")
            stock_data = market_data_manager.get_historical_data(symbol, date_str, date_str)
            
            if stock_data is None or stock_data.empty:
                logger.warning(f"No stock data for {symbol} on {date_str}")
                continue
            
            current_price = float(stock_data.iloc[-1]['Close'])
            
            # Get historical Greeks data
            greeks_data = strategy.get_greeks_data(
                symbol=symbol,
                current_price=current_price,
                historical_date=date_str
            )
            
            if greeks_data:
                result = {
                    'date': date_str,
                    'symbol': symbol,
                    'backtest_name': backtest_name,
                    'stock_price': current_price,
                    'delta': greeks_data.delta,
                    'gamma': greeks_data.gamma,
                    'theta': greeks_data.theta,
                    'vega': greeks_data.vega,
                    'strike': greeks_data.strike,
                    'expiration': greeks_data.expiration,
                    'option_type': greeks_data.option_type
                }
                results.append(result)
                
                logger.info(f"✅ {date_str}: Price=${current_price:.2f}, Delta={greeks_data.delta:.3f}, Gamma={greeks_data.gamma:.3f}")
            else:
                logger.warning(f"⚠️ No Greeks data for {symbol} on {date_str}")
                
        except Exception as e:
            logger.error(f"Error processing {symbol} on {snapshot_date}: {e}")
    
    logger.info(f"✅ Completed backtest for {symbol}: {len(results)} data points")
    return results


def analyze_backtest_results(results: List[Dict]) -> Dict:
    """
    Analyze backtest results
    
    Args:
        results: List of backtest results
        
    Returns:
        Analysis summary
    """
    if not results:
        return {}
    
    # Calculate statistics
    deltas = [r['delta'] for r in results if r['delta'] is not None]
    gammas = [r['gamma'] for r in results if r['gamma'] is not None]
    thetas = [r['theta'] for r in results if r['theta'] is not None]
    vegas = [r['vega'] for r in results if r['vega'] is not None]
    prices = [r['stock_price'] for r in results]
    
    analysis = {
        'total_days': len(results),
        'backtest_name': results[0].get('backtest_name', 'Unknown') if results else 'Unknown',
        'avg_stock_price': sum(prices) / len(prices) if prices else 0,
        'avg_delta': sum(deltas) / len(deltas) if deltas else 0,
        'avg_gamma': sum(gammas) / len(gammas) if gammas else 0,
        'avg_theta': sum(thetas) / len(thetas) if thetas else 0,
        'avg_vega': sum(vegas) / len(vegas) if vegas else 0,
        'min_delta': min(deltas) if deltas else 0,
        'max_delta': max(deltas) if deltas else 0,
        'min_gamma': min(gammas) if gammas else 0,
        'max_gamma': max(gammas) if gammas else 0,
        'date_range': {
            'start': min(r['date'] for r in results),
            'end': max(r['date'] for r in results)
        }
    }
    
    return analysis


def main():
    """Main demo function"""
    logger.info("🚀 Starting Historical Options Backtest Demo")
    
    # Get backtest name from the script
    backtest_name = get_backtest_name_from_script()
    logger.info(f"Backtest name: {backtest_name}")
    
    # Configuration
    symbols = ['AAPL', 'MSFT', 'TSLA']  # Example symbols
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    
    logger.info(f"Configuration:")
    logger.info(f"  Backtest Name: {backtest_name}")
    logger.info(f"  Symbols: {symbols}")
    logger.info(f"  Date Range: {start_date} to {end_date}")
    
    # Step 1: Set up historical options data
    logger.info("\n📊 Step 1: Setting up historical options data")
    snapshot_results = setup_historical_options_data(symbols, start_date, end_date)
    
    # Step 2: Run backtests for each symbol
    logger.info("\n📈 Step 2: Running historical Greeks backtests")
    all_results = {}
    
    for symbol in symbols:
        if snapshot_results.get(symbol, 0) > 0:
            results = run_historical_greeks_backtest(symbol, start_date, end_date, backtest_name)
            all_results[symbol] = results
        else:
            logger.warning(f"Skipping {symbol} - no historical snapshots available")
    
    # Step 3: Analyze results
    logger.info("\n📋 Step 3: Analyzing backtest results")
    
    for symbol, results in all_results.items():
        if results:
            analysis = analyze_backtest_results(results)
            
            logger.info(f"\n📊 Analysis for {symbol}:")
            logger.info(f"  Backtest: {analysis['backtest_name']}")
            logger.info(f"  Total Days: {analysis['total_days']}")
            logger.info(f"  Date Range: {analysis['date_range']['start']} to {analysis['date_range']['end']}")
            logger.info(f"  Avg Stock Price: ${analysis['avg_stock_price']:.2f}")
            logger.info(f"  Avg Delta: {analysis['avg_delta']:.3f}")
            logger.info(f"  Avg Gamma: {analysis['avg_gamma']:.3f}")
            logger.info(f"  Avg Theta: {analysis['avg_theta']:.3f}")
            logger.info(f"  Avg Vega: {analysis['avg_vega']:.3f}")
            logger.info(f"  Delta Range: {analysis['min_delta']:.3f} to {analysis['max_delta']:.3f}")
            logger.info(f"  Gamma Range: {analysis['min_gamma']:.3f} to {analysis['max_gamma']:.3f}")
    
    # Step 4: Cleanup old data
    logger.info("\n🧹 Step 4: Cleaning up old historical data")
    enhanced_service = get_enhanced_options_service()
    deleted_count = enhanced_service.cleanup_old_historical_data()
    logger.info(f"Cleaned up {deleted_count} old records")
    
    logger.info("\n✅ Historical Options Backtest Demo completed!")


if __name__ == "__main__":
    main() 