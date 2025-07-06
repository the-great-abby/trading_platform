#!/usr/bin/env python3
"""
Simple test for cached market data system
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cached_market_data():
    """Test the cached market data system"""
    
    print("🧪 Testing Cached Market Data System")
    print("=" * 40)
    
    try:
        # Import the cached manager
        from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
        
        # Initialize manager
        print("📦 Initializing cached market data manager...")
        cached_manager = get_cached_market_data_manager()
        print("✅ Manager initialized successfully")
        
        # Test parameters
        symbol = 'AAPL'
        start_date = '2024-01-01'
        end_date = '2024-01-31'  # Short period for testing
        
        print(f"\n📊 Testing with {symbol} from {start_date} to {end_date}")
        
        # First request (should hit API)
        print("\n🔄 First request (should hit API)...")
        data1 = cached_manager.get_historical_data(symbol, start_date, end_date)
        
        if data1 is not None and len(data1) > 0:
            print(f"✅ Retrieved {len(data1)} records")
            print(f"📅 Date range: {data1.index.min()} to {data1.index.max()}")
            print(f"💰 Price range: ${data1['Close'].min():.2f} - ${data1['Close'].max():.2f}")
        else:
            print("❌ No data retrieved")
            return
        
        # Second request (should hit cache)
        print("\n⚡ Second request (should hit cache)...")
        data2 = cached_manager.get_historical_data(symbol, start_date, end_date)
        
        if data2 is not None and len(data2) > 0:
            print(f"✅ Retrieved {len(data2)} records from cache")
            print(f"📅 Date range: {data2.index.min()} to {data2.index.max()}")
        else:
            print("❌ No data retrieved from cache")
        
        # Check stats
        stats = cached_manager.get_stats()
        print(f"\n📊 Cache Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   API calls: {stats['api_calls']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.1f}%")
        
        # Check cache status
        cache_status = cached_manager.get_cache_status(symbol)
        print(f"\n📈 Cache Status for {symbol}:")
        print(f"   {cache_status}")
        
        print("\n🎉 Test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_database_models():
    """Test database models"""
    
    print("\n" + "=" * 40)
    print("🗄️ Testing Database Models")
    print("=" * 40)
    
    try:
        from src.models.market_data import HistoricalPrice, MarketDataCache
        
        # Test model creation
        print("📝 Testing HistoricalPrice model...")
        
        # Create a sample record
        sample_record = HistoricalPrice(
            symbol='TEST',
            date=datetime.now().date(),
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000000,
            provider='test_provider',
            interval='1d'
        )
        
        print(f"✅ Created sample record: {sample_record}")
        
        # Test to_dict method
        record_dict = sample_record.to_dict()
        print(f"📋 Record as dict: {record_dict}")
        
        # Test cache model
        print("\n📝 Testing MarketDataCache model...")
        
        cache_record = MarketDataCache(
            symbol='TEST',
            provider='test_provider',
            interval='1d',
            earliest_date=datetime.now().date(),
            latest_date=datetime.now().date(),
            total_records=100
        )
        
        print(f"✅ Created cache record: {cache_record}")
        
        print("🎉 Database models test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Database models test failed: {e}")


if __name__ == "__main__":
    # Test database models first
    test_database_models()
    
    # Test cached market data
    test_cached_market_data() 