#!/usr/bin/env python3
"""
Test script to check Polygon Greeks data availability and demonstrate the Greeks data service
"""

import os
import sys
import logging
from datetime import date, datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.greeks_data_service import GreeksDataService, GreeksData
from services.market_data.options_data_service import OptionsDataService
# from utils.logging_config import setup_logging  # Commented out for now

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_polygon_greeks_availability():
    """Test what Greeks data is available from Polygon"""
    logger.info("🔍 Testing Polygon Greeks Data Availability")
    logger.info("=" * 60)
    
    # Initialize services
    greeks_service = GreeksDataService()
    options_service = OptionsDataService()
    
    # Test symbols (highly liquid options)
    test_symbols = ['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA']
    
    for symbol in test_symbols:
        logger.info(f"\n📊 Testing {symbol} Greeks Data:")
        logger.info("-" * 40)
        
        try:
            # First, get options chain to see what contracts are available
            contracts = options_service.get_options_chain(symbol)
            if not contracts:
                logger.warning(f"❌ No options contracts found for {symbol}")
                continue
            
            logger.info(f"✅ Found {len(contracts)} options contracts for {symbol}")
            
            # Get liquid contracts
            liquid_contracts = options_service.get_liquid_options(symbol, min_volume=10)
            if not liquid_contracts:
                logger.warning(f"⚠️ No liquid contracts found for {symbol}, using first 3 contracts")
                liquid_contracts = contracts[:3]
            else:
                logger.info(f"✅ Found {len(liquid_contracts)} liquid contracts for {symbol}")
            
            # Test Greeks for each liquid contract
            greeks_found = 0
            for i, contract in enumerate(liquid_contracts[:3]):  # Test first 3
                logger.info(f"\n  Contract {i+1}: {contract.strike} {contract.option_type} exp {contract.expiration}")
                
                greeks = greeks_service.get_greeks_for_contract(
                    symbol=contract.symbol,
                    strike=contract.strike,
                    expiration=contract.expiration,
                    option_type=contract.option_type
                )
                
                if greeks:
                    greeks_found += 1
                    logger.info(f"    ✅ Greeks found:")
                    logger.info(f"      Delta: {greeks.delta}")
                    logger.info(f"      Gamma: {greeks.gamma}")
                    logger.info(f"      Theta: {greeks.theta}")
                    logger.info(f"      Vega: {greeks.vega}")
                    logger.info(f"      IV: {greeks.implied_volatility}")
                    logger.info(f"      Price: ${greeks.price}")
                    logger.info(f"      Volume: {greeks.volume}")
                    logger.info(f"      OI: {greeks.open_interest}")
                else:
                    logger.warning(f"    ❌ No Greeks data available")
            
            logger.info(f"\n📈 Summary for {symbol}: {greeks_found}/{min(3, len(liquid_contracts))} contracts have Greeks data")
            
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {e}")
    
    # Test cache performance
    logger.info(f"\n📊 Cache Performance:")
    logger.info("-" * 40)
    cache_stats = greeks_service.get_cache_stats()
    logger.info(f"Cache size: {cache_stats['cache_size']}")
    logger.info(f"Cache keys: {cache_stats['cache_keys']}")


def test_historical_greeks():
    """Test historical Greeks data retrieval"""
    logger.info(f"\n🕰️ Testing Historical Greeks Data")
    logger.info("=" * 60)
    
    greeks_service = GreeksDataService()
    
    # Test with a recent date
    test_date = date(2025, 7, 15)  # Recent date
    
    test_contracts = [
        ('AAPL', 200.0, '2025-08-15', 'call'),
        ('TSLA', 250.0, '2025-08-15', 'put'),
        ('SPY', 500.0, '2025-08-15', 'call')
    ]
    
    for symbol, strike, expiration, option_type in test_contracts:
        logger.info(f"\n📅 Testing historical Greeks for {symbol} {strike} {option_type} {expiration}")
        
        greeks = greeks_service.get_greeks_for_contract(
            symbol=symbol,
            strike=strike,
            expiration=expiration,
            option_type=option_type,
            snapshot_date=test_date
        )
        
        if greeks:
            logger.info(f"✅ Historical Greeks found:")
            logger.info(f"  Delta: {greeks.delta}")
            logger.info(f"  Gamma: {greeks.gamma}")
            logger.info(f"  Theta: {greeks.theta}")
            logger.info(f"  Vega: {greeks.vega}")
            logger.info(f"  IV: {greeks.implied_volatility}")
        else:
            logger.warning(f"❌ No historical Greeks data available")


def test_polygon_api_endpoints():
    """Test different Polygon API endpoints for Greeks data"""
    logger.info(f"\n🔌 Testing Polygon API Endpoints")
    logger.info("=" * 60)
    
    import requests
    
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        logger.error("❌ No Polygon API key found")
        return
    
    base_url = "https://api.polygon.io"
    session = requests.Session()
    
    # Test symbols
    test_symbols = ['AAPL', 'TSLA']
    
    for symbol in test_symbols:
        logger.info(f"\n🔍 Testing endpoints for {symbol}:")
        
        # Test 1: Snapshot endpoint
        logger.info("  1. Testing snapshot endpoint...")
        try:
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}/options"
            response = session.get(f"{base_url}{endpoint}", params={"apiKey": api_key}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})
                options = results.get("options", [])
                logger.info(f"    ✅ Snapshot endpoint works: {len(options)} options found")
                
                # Check if any have Greeks
                greeks_count = 0
                for option in options[:5]:  # Check first 5
                    if any([option.get("delta"), option.get("gamma"), option.get("theta"), option.get("vega")]):
                        greeks_count += 1
                
                logger.info(f"    📊 {greeks_count}/5 options have Greeks data")
                
            elif response.status_code == 404:
                logger.warning(f"    ⚠️ Snapshot endpoint 404 for {symbol}")
            else:
                logger.error(f"    ❌ Snapshot endpoint error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"    ❌ Snapshot endpoint error: {e}")
        
        # Test 2: Options contracts endpoint
        logger.info("  2. Testing contracts endpoint...")
        try:
            endpoint = f"/v3/reference/options/contracts"
            response = session.get(f"{base_url}{endpoint}", 
                                 params={"underlying_ticker": symbol, "apiKey": api_key}, 
                                 timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.info(f"    ✅ Contracts endpoint works: {len(results)} contracts found")
                
                # Check if any have Greeks
                greeks_count = 0
                for contract in results[:5]:  # Check first 5
                    if any([contract.get("delta"), contract.get("gamma"), contract.get("theta"), contract.get("vega")]):
                        greeks_count += 1
                
                logger.info(f"    📊 {greeks_count}/5 contracts have Greeks data")
                
            else:
                logger.error(f"    ❌ Contracts endpoint error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"    ❌ Contracts endpoint error: {e}")
        
        # Test 3: Previous close endpoint (for stock price)
        logger.info("  3. Testing previous close endpoint...")
        try:
            endpoint = f"/v2/aggs/ticker/{symbol}/prev"
            response = session.get(f"{base_url}{endpoint}", params={"apiKey": api_key}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    close_price = results[0].get("c", 0)
                    logger.info(f"    ✅ Previous close endpoint works: ${close_price}")
                else:
                    logger.warning(f"    ⚠️ No previous close data for {symbol}")
            else:
                logger.error(f"    ❌ Previous close endpoint error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"    ❌ Previous close endpoint error: {e}")


def main():
    """Main test function"""
    logger.info("🚀 Starting Polygon Greeks Data Test")
    logger.info("=" * 60)
    
    # Check API key
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        logger.error("❌ POLYGON_API_KEY environment variable not set")
        logger.info("Please set your Polygon API key:")
        logger.info("export POLYGON_API_KEY='your_api_key_here'")
        return
    
    logger.info(f"✅ Polygon API key found: {api_key[:8]}...")
    
    # Run tests
    test_polygon_api_endpoints()
    test_polygon_greeks_availability()
    test_historical_greeks()
    
    logger.info(f"\n🎉 Polygon Greeks Data Test Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main() 