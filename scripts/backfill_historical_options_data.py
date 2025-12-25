#!/usr/bin/env python3
"""
Backfill Historical Options Data from Polygon

This script fetches historical options data for the past 2 years from Polygon API
and stores it in the database so backtests can use cached data instead of hitting the API.

Usage:
    # Backfill all default symbols for past year
    python scripts/backfill_historical_options_data.py

    # Backfill specific symbols
    python scripts/backfill_historical_options_data.py --symbols AAPL MSFT TSLA
    
    # Backfill custom date range
    python scripts/backfill_historical_options_data.py --days 730  # 2 years

    # Dry run (don't save to database)
    python scripts/backfill_historical_options_data.py --dry-run
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta, date
from typing import List, Optional
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.market_data.options_data_service import OptionsDataService, OptionContract
from src.services.database.market_data_service import MarketDataService
from src.utils.trading_config import get_symbols
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backfill_options_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OptionsDataBackfill:
    """Backfill historical options data from Polygon"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # Initialize services
        polygon_api_key = os.getenv('POLYGON_API_KEY')
        if not polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set!")
        
        self.options_service = OptionsDataService(api_key=polygon_api_key)
        
        if not dry_run:
            # For local development, override DATABASE_URL to use localhost with psycopg2
            # (the env var might be set to K8s service with asyncpg for other services)
            database_url = 'postgresql+psycopg2://postgres:postgres@localhost:5432/trading_bot'
            
            logger.info(f"📊 Database: {database_url}")
            logger.info(f"   (using localhost port-forward, not K8s service)")
            
            self.db_service = MarketDataService(database_url)
        else:
            self.db_service = None
            logger.info("🔍 DRY RUN MODE - No data will be saved to database")
        
        # Statistics
        self.stats = {
            'symbols_processed': 0,
            'snapshots_fetched': 0,
            'snapshots_saved': 0,
            'errors': 0,
            'api_calls': 0,
            'skipped': 0
        }
    
    async def backfill_symbol(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        check_existing: bool = True
    ) -> int:
        """
        Backfill options data for a single symbol
        
        Returns number of snapshots saved
        """
        logger.info(f"📊 Backfilling {symbol} from {start_date} to {end_date}")
        
        snapshots_saved = 0
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # Check if data already exists (unless dry-run)
                if check_existing and not self.dry_run:
                    existing = self.db_service.get_historical_options_data(
                        symbol, 
                        current_date, 
                        None  # No specific expiration
                    )
                    if existing and len(existing) > 0:
                        logger.debug(f"⏭️  Skipping {symbol} on {current_date} - data exists")
                        self.stats['skipped'] += 1
                        current_date += timedelta(days=1)
                        continue
                
                # Fetch options chain for this date using Polygon API directly
                logger.info(f"🔄 Fetching options data for {symbol} on {current_date}")
                options_chain = await self._fetch_historical_options_from_polygon(
                    symbol,
                    current_date
                )
                
                if options_chain is not None:
                    self.stats['api_calls'] += 1
                
                if options_chain and len(options_chain) > 0:
                    logger.info(f"✅ Found {len(options_chain)} contracts for {symbol} on {current_date}")
                    
                    if not self.dry_run:
                        # Get stock price for this date
                        underlying_price = await self._get_stock_price(symbol, current_date)
                        
                        if underlying_price is None:
                            logger.warning(f"⚠️ Could not get stock price for {symbol} on {current_date}, skipping")
                            self.stats['errors'] += 1
                            current_date += timedelta(days=1)
                            continue
                        
                        # Convert OptionContract objects to dicts
                        contracts_dicts = [
                            {
                                'symbol': c.symbol,
                                'strike': c.strike,
                                'expiration': c.expiration,
                                'option_type': c.option_type,
                                'price': c.price,
                                'volume': c.volume,
                                'open_interest': c.open_interest,
                                'delta': c.delta,
                                'gamma': c.gamma,
                                'theta': c.theta,
                                'vega': c.vega,
                                'implied_volatility': c.implied_volatility
                            }
                            for c in options_chain
                        ]
                        
                        # Store in database
                        success = self.db_service.store_historical_options_snapshot(
                            symbol=symbol,
                            snapshot_date=current_date,
                            contracts=contracts_dicts,
                            underlying_price=underlying_price
                        )
                        
                        if success:
                            snapshots_saved += 1
                            self.stats['snapshots_saved'] += 1
                            logger.info(f"💾 Saved snapshot for {symbol} on {current_date} (underlying @ ${underlying_price:.2f}, {len(contracts_dicts)} contracts)")
                        else:
                            logger.warning(f"⚠️  Failed to save snapshot for {symbol} on {current_date}")
                            self.stats['errors'] += 1
                    else:
                        # Dry run - still get stock price to show what would be saved
                        underlying_price = await self._get_stock_price(symbol, current_date)
                        price_info = f" (underlying @ ${underlying_price:.2f})" if underlying_price else ""
                        logger.info(f"🔍 [DRY RUN] Would save {len(options_chain)} contracts{price_info}")
                        snapshots_saved += 1
                    
                    self.stats['snapshots_fetched'] += 1
                else:
                    logger.debug(f"📭 No options data for {symbol} on {current_date}")
                
                # Rate limiting - Polygon allows 5 requests/minute on free tier
                await asyncio.sleep(0.5)  # 2 requests per second = safe
                
            except Exception as e:
                logger.error(f"❌ Error fetching {symbol} on {current_date}: {e}")
                self.stats['errors'] += 1
            
            # Move to next day
            current_date += timedelta(days=1)
        
        self.stats['symbols_processed'] += 1
        return snapshots_saved
    
    async def _fetch_historical_options_from_polygon(
        self,
        symbol: str,
        snapshot_date: date
    ) -> Optional[List[OptionContract]]:
        """
        Fetch historical options data from Polygon API for a specific date
        
        Uses Polygon's options chain snapshot endpoint:
        https://api.polygon.io/v3/snapshot/options/{underlying_asset}
        """
        if not self.options_service.api_key:
            logger.error("No Polygon API key available")
            return None
        
        try:
            # Format date for API
            date_str = snapshot_date.strftime('%Y-%m-%d')
            
            # Polygon API endpoint for options snapshots
            # Note: Polygon may not support historical snapshots on free tier
            # We'll use the contracts endpoint instead
            url = f"{self.options_service.base_url}/v3/reference/options/contracts"
            
            params = {
                'underlying_ticker': symbol,
                'as_of': date_str,
                'limit': 1000,  # Max per request
                'apiKey': self.options_service.api_key
            }
            
            # Rate limiting
            self.options_service._enforce_rate_limit()
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.debug(f"No options contracts found for {symbol} on {date_str}")
                    return []
                
                # Convert to OptionContract objects
                contracts = []
                for contract_data in results:
                    try:
                        contract = OptionContract(
                            symbol=symbol,
                            strike=contract_data.get('strike_price', 0),
                            expiration=contract_data.get('expiration_date', ''),
                            option_type='call' if contract_data.get('contract_type') == 'call' else 'put',
                            price=0.0,  # Need separate API call for prices
                            volume=0,
                            open_interest=0,
                            delta=None,
                            gamma=None,
                            theta=None,
                            vega=None,
                            implied_volatility=None
                        )
                        contracts.append(contract)
                    except Exception as e:
                        logger.debug(f"Error parsing contract: {e}")
                        continue
                
                logger.debug(f"Fetched {len(contracts)} contracts for {symbol} on {date_str}")
                return contracts
                
            elif response.status_code == 404:
                logger.debug(f"No data available for {symbol} on {date_str}")
                return []
            else:
                logger.warning(f"Polygon API returned status {response.status_code} for {symbol} on {date_str}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from Polygon for {symbol} on {snapshot_date}: {e}")
            return None
    
    async def _get_stock_price(self, symbol: str, price_date: date) -> Optional[float]:
        """
        Get historical stock price for a specific date from Polygon
        
        Uses Polygon's aggregates (bars) endpoint:
        https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{date}/{date}
        """
        if not self.options_service.api_key:
            logger.error("No Polygon API key available")
            return None
        
        try:
            date_str = price_date.strftime('%Y-%m-%d')
            
            url = f"{self.options_service.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{date_str}/{date_str}"
            
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'apiKey': self.options_service.api_key
            }
            
            # Rate limiting
            self.options_service._enforce_rate_limit()
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results and len(results) > 0:
                    # Use closing price
                    close_price = results[0].get('c', 0)
                    logger.debug(f"Stock price for {symbol} on {date_str}: ${close_price:.2f}")
                    return float(close_price)
                else:
                    logger.debug(f"No stock price data for {symbol} on {date_str}")
                    return None
            else:
                logger.warning(f"Failed to get stock price for {symbol} on {date_str}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol} on {price_date}: {e}")
            return None
    
    async def backfill_multiple_symbols(
        self,
        symbols: List[str],
        days: int = 365,
        check_existing: bool = True
    ):
        """Backfill multiple symbols"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        logger.info("=" * 80)
        logger.info("🚀 HISTORICAL OPTIONS DATA BACKFILL")
        logger.info("=" * 80)
        logger.info(f"📅 Date Range: {start_date} to {end_date} ({days} days)")
        logger.info(f"📊 Symbols: {', '.join(symbols)} ({len(symbols)} total)")
        logger.info(f"🔍 Check Existing: {check_existing}")
        logger.info(f"🏃 Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        logger.info("=" * 80)
        logger.info("")
        
        start_time = time.time()
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"📊 Processing {symbol} ({i}/{len(symbols)})")
            logger.info(f"{'='*80}")
            
            try:
                saved = await self.backfill_symbol(
                    symbol,
                    start_date,
                    end_date,
                    check_existing
                )
                logger.info(f"✅ Completed {symbol}: {saved} snapshots saved")
                
            except Exception as e:
                logger.error(f"❌ Failed to process {symbol}: {e}")
                self.stats['errors'] += 1
        
        # Print final statistics
        duration = time.time() - start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"📊 Symbols Processed: {self.stats['symbols_processed']}/{len(symbols)}")
        logger.info(f"📦 Snapshots Fetched: {self.stats['snapshots_fetched']}")
        logger.info(f"💾 Snapshots Saved: {self.stats['snapshots_saved']}")
        logger.info(f"⏭️  Snapshots Skipped: {self.stats['skipped']}")
        logger.info(f"🔄 API Calls Made: {self.stats['api_calls']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 80)
        
        if self.dry_run:
            logger.info("")
            logger.info("🔍 This was a DRY RUN - no data was saved to the database")
            logger.info("💡 Run without --dry-run to actually save data")
        else:
            logger.info("")
            logger.info("✅ Data successfully backfilled to database!")
            logger.info("🎯 Your backtests can now use cached historical options data")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Backfill historical options data from Polygon')
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Symbols to backfill (default: uses trading_config.py symbols)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days to backfill (default: 365 = 1 year, max: 730 = 2 years)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - fetch but don\'t save to database'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip dates that already have data (faster)'
    )
    
    args = parser.parse_args()
    
    # Get symbols
    if args.symbols:
        symbols = args.symbols
    else:
        # Use default symbols from trading config
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'SPY', 'QQQ']
    
    # Limit to 2 years max
    days = min(args.days, 730)
    
    # Create backfill instance
    backfill = OptionsDataBackfill(dry_run=args.dry_run)
    
    # Run backfill
    await backfill.backfill_multiple_symbols(
        symbols=symbols,
        days=days,
        check_existing=args.skip_existing
    )


if __name__ == "__main__":
    asyncio.run(main())

