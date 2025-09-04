#!/usr/bin/env python3
"""
Direct Test of Historical Greeks Functionality
Tests the historical date functionality directly without the backtest engine
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.enhanced_logging import get_trading_logger
from src.strategies.greeks_enhanced_strategy import GreeksEnhancedStrategy
from src.services.database.market_data_service import MarketDataService
from src.utils.config import get_config

logger = get_trading_logger()

async def test_historical_greeks_direct():
    """Test historical Greeks functionality directly"""
    
    print("🧪 DIRECT TEST OF HISTORICAL GREEKS FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize services
    market_data_service = MarketDataService()
    strategy = GreeksEnhancedStrategy()
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Test historical dates
    test_dates = [
        "2023-07-10",
        "2023-07-15", 
        "2023-07-20",
        "2023-08-01",
        "2023-08-10"
    ]
    
    print(f"📊 Testing {len(symbols)} symbols on {len(test_dates)} historical dates")
    print()
    
    for symbol in symbols:
        print(f"🎯 Testing {symbol}:")
        
        # Get historical data for the symbol
        # Use the actual historical period we want to test
        start_date = datetime.strptime("2023-07-06", "%Y-%m-%d").date()
        end_date = datetime.strptime("2023-08-15", "%Y-%m-%d").date()
        data = market_data_service.get_historical_data(symbol, start_date, end_date)
        
        if data is None or data.empty:
            print(f"   ❌ No data available for {symbol}")
            continue
        
        print(f"   ✅ Found {len(data)} data points for {symbol}")
        print(f"   📅 Data range: {data.index.min()} to {data.index.max()}")
        print(f"   💰 Latest price: ${data['Close'].iloc[-1]:.2f}")
        
        # Test each historical date
        for test_date in test_dates:
            print(f"   📅 Testing historical date: {test_date}")
            
            try:
                # Call the strategy directly with historical date
                signal = await strategy.generate_signal(symbol, data, historical_date=test_date)
                
                if signal:
                    action = signal.get('action', 'HOLD')
                    confidence = signal.get('confidence', 0.0)
                    metadata = signal.get('metadata', {})
                    historical_date_in_metadata = metadata.get('historical_date', 'Not found')
                    
                    print(f"      ✅ Signal generated: {action} (confidence: {confidence:.2f})")
                    print(f"      📅 Historical date in metadata: {historical_date_in_metadata}")
                    
                    # Check if Greeks data was used
                    greeks_data = metadata.get('greeks_data', {})
                    if greeks_data:
                        print(f"      📊 Greeks data: delta={greeks_data.get('delta', 'N/A')}, gamma={greeks_data.get('gamma', 'N/A')}")
                else:
                    print(f"      ⚠️ No signal generated for {test_date}")
                    
            except Exception as e:
                print(f"      ❌ Error testing {test_date}: {e}")
        
        print()

async def main():
    """Main function"""
    try:
        await test_historical_greeks_direct()
        print("✅ Direct test completed!")
    except Exception as e:
        logger.error(f"❌ Error in direct test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 