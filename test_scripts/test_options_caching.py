#!/usr/bin/env python3
"""
Test script for enhanced options data caching functionality
"""

import asyncio
import logging
import time
from src.services.market_data.options_data_service import get_options_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_options_caching():
    """Test the enhanced options data caching functionality"""
    logger.info("🧪 Testing enhanced options data caching...")
    
    # Get options service
    options_service = get_options_service()
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    # 1. Test initial cache stats
    logger.info("📊 Initial cache statistics:")
    stats = options_service.get_cache_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    # 2. Test cache size
    cache_size = options_service.get_cache_size()
    logger.info(f"📦 Current cache size: {cache_size} contracts")
    
    # 3. Test fetching options data (this will populate cache)
    for symbol in test_symbols:
        logger.info(f"🔄 Fetching options data for {symbol}...")
        start_time = time.time()
        
        contracts = options_service.get_options_chain(symbol)
        
        if contracts:
            logger.info(f"✅ Found {len(contracts)} contracts for {symbol}")
            
            # Show some contract details
            for i, contract in enumerate(contracts[:3]):  # Show first 3
                logger.info(f"   Contract {i+1}: {contract.symbol} {contract.strike} {contract.option_type} {contract.expiration}")
                logger.info(f"     Price: ${contract.price}, Volume: {contract.volume}, OI: {contract.open_interest}")
                if contract.delta:
                    logger.info(f"     Greeks: Δ={contract.delta:.3f}, Γ={contract.gamma:.3f}, Θ={contract.theta:.3f}")
        else:
            logger.warning(f"⚠️ No contracts found for {symbol}")
        
        fetch_time = time.time() - start_time
        logger.info(f"⏱️ Fetch time for {symbol}: {fetch_time:.3f}s")
    
    # 4. Test cache hit (second fetch should be faster)
    logger.info("\n🔄 Testing cache hit performance...")
    for symbol in test_symbols:
        start_time = time.time()
        contracts = options_service.get_options_chain(symbol)
        fetch_time = time.time() - start_time
        
        if contracts:
            logger.info(f"⚡ Cache HIT for {symbol}: {len(contracts)} contracts in {fetch_time:.3f}s")
        else:
            logger.warning(f"⚠️ Cache miss for {symbol}")
    
    # 5. Test cache statistics after operations
    logger.info("\n📊 Updated cache statistics:")
    stats = options_service.get_cache_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    # 6. Test cache invalidation
    logger.info("\n🗑️ Testing cache invalidation...")
    symbol_to_invalidate = test_symbols[0]
    deleted_count = options_service.invalidate_cache_for_symbol(symbol_to_invalidate)
    logger.info(f"🗑️ Invalidated {deleted_count} cache entries for {symbol_to_invalidate}")
    
    # 7. Test cache cleanup
    logger.info("\n🧹 Testing cache cleanup...")
    cleaned_count = options_service.cleanup_expired_cache()
    logger.info(f"🧹 Cleaned {cleaned_count} expired cache entries")
    
    # 8. Test batch caching
    logger.info("\n📦 Testing batch caching...")
    # Create some mock contracts for batch caching test
    from src.services.market_data.options_data_service import OptionContract
    from datetime import datetime
    
    mock_contracts = {
        "TEST1": [
            OptionContract(
                symbol="TEST1",
                strike=100.0,
                expiration="2024-01-19",
                option_type="call",
                price=5.0,
                volume=100,
                open_interest=500,
                delta=0.6,
                gamma=0.02,
                theta=-0.05,
                vega=0.1,
                implied_volatility=0.25
            )
        ],
        "TEST2": [
            OptionContract(
                symbol="TEST2",
                strike=150.0,
                expiration="2024-01-19",
                option_type="put",
                price=3.0,
                volume=50,
                open_interest=200,
                delta=-0.4,
                gamma=0.015,
                theta=-0.03,
                vega=0.08,
                implied_volatility=0.22
            )
        ]
    }
    
    cached_count = options_service.batch_cache_contracts(mock_contracts)
    logger.info(f"📦 Batch cached {cached_count} contracts for {len(mock_contracts)} symbols")
    
    # 9. Final cache statistics
    logger.info("\n📊 Final cache statistics:")
    stats = options_service.get_cache_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    logger.info("🎉 Options caching tests completed!")

if __name__ == "__main__":
    test_options_caching() 