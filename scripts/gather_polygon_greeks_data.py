#!/usr/bin/env python3
"""
Polygon Greeks Data Gatherer

This script explores all available Polygon API endpoints to gather historical Greeks data
for options contracts. It tests different methods and stores the results in the database.
"""

import os
import sys
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, Tuple
import time
import json
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PolygonEndpointTest:
    """Container for Polygon API endpoint test results"""
    endpoint: str
    method: str
    params: Dict[str, Any]
    status_code: int
    response_time: float
    data_found: bool
    greeks_found: bool
    error_message: Optional[str] = None
    sample_data: Optional[Dict] = None


class PolygonGreeksDataGatherer:
    """Comprehensive Greeks data gatherer for Polygon API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        # Test results
        self.endpoint_tests: List[PolygonEndpointTest] = []
        
        if not self.api_key:
            logger.error("❌ No Polygon API key found")
            raise ValueError("Polygon API key required")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        time.sleep(1.0)  # 1 second between requests
    
    def test_polygon_endpoints(self, symbols: Optional[List[str]] = None) -> List[PolygonEndpointTest]:
        """Test all available Polygon endpoints for options and Greeks data"""
        if symbols is None:
            symbols = ['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA']
        
        logger.info(f"🔍 Testing Polygon endpoints for {len(symbols)} symbols")
        
        for symbol in symbols:
            logger.info(f"\n📊 Testing endpoints for {symbol}:")
            
            # Test 1: Snapshot endpoint (current options)
            self._test_snapshot_endpoint(symbol)
            
            # Test 2: Options contracts endpoint
            self._test_contracts_endpoint(symbol)
            
            # Test 3: Options chain endpoint
            self._test_options_chain_endpoint(symbol)
            
            # Test 4: Historical options data endpoint
            self._test_historical_options_endpoint(symbol)
            
            # Test 5: Previous close endpoint (for underlying price)
            self._test_previous_close_endpoint(symbol)
            
            # Test 6: Aggregates endpoint (for historical price data)
            self._test_aggregates_endpoint(symbol)
        
        return self.endpoint_tests
    
    def _test_snapshot_endpoint(self, symbol: str):
        """Test the snapshot endpoint for current options data"""
        endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}/options"
        params = {"apiKey": self.api_key}
        
        logger.info("  1. Testing snapshot endpoint...")
        
        try:
            self._enforce_rate_limit()
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response_time = time.time() - start_time
            
            data_found = False
            greeks_found = False
            sample_data = None
            error_message = None
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})
                options = results.get("options", [])
                
                if options:
                    data_found = True
                    sample_data = options[0] if options else None
                    
                    # Check for Greeks data
                    for option in options[:5]:  # Check first 5
                        if any([option.get("delta"), option.get("gamma"), option.get("theta"), option.get("vega")]):
                            greeks_found = True
                            break
                    
                    logger.info(f"    ✅ Found {len(options)} options, Greeks: {greeks_found}")
                else:
                    logger.warning(f"    ⚠️ No options found")
            elif response.status_code == 404:
                error_message = "Endpoint not found"
                logger.warning(f"    ⚠️ 404 - Endpoint not available")
            else:
                error_message = f"HTTP {response.status_code}"
                logger.error(f"    ❌ Error: {response.status_code}")
            
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=response.status_code,
                response_time=response_time,
                data_found=data_found,
                greeks_found=greeks_found,
                error_message=error_message,
                sample_data=sample_data
            )
            
            self.endpoint_tests.append(test_result)
            
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=0,
                response_time=0,
                data_found=False,
                greeks_found=False,
                error_message=str(e)
            )
            self.endpoint_tests.append(test_result)
    
    def _test_contracts_endpoint(self, symbol: str):
        """Test the options contracts endpoint"""
        endpoint = "/v3/reference/options/contracts"
        params = {"underlying_ticker": symbol, "apiKey": self.api_key}
        
        logger.info("  2. Testing contracts endpoint...")
        
        try:
            self._enforce_rate_limit()
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response_time = time.time() - start_time
            
            data_found = False
            greeks_found = False
            sample_data = None
            error_message = None
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    data_found = True
                    sample_data = results[0] if results else None
                    
                    # Check for Greeks data
                    for contract in results[:5]:  # Check first 5
                        if any([contract.get("delta"), contract.get("gamma"), contract.get("theta"), contract.get("vega")]):
                            greeks_found = True
                            break
                    
                    logger.info(f"    ✅ Found {len(results)} contracts, Greeks: {greeks_found}")
                else:
                    logger.warning(f"    ⚠️ No contracts found")
            else:
                error_message = f"HTTP {response.status_code}"
                logger.error(f"    ❌ Error: {response.status_code}")
            
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=response.status_code,
                response_time=response_time,
                data_found=data_found,
                greeks_found=greeks_found,
                error_message=error_message,
                sample_data=sample_data
            )
            
            self.endpoint_tests.append(test_result)
            
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=0,
                response_time=0,
                data_found=False,
                greeks_found=False,
                error_message=str(e)
            )
            self.endpoint_tests.append(test_result)
    
    def _test_options_chain_endpoint(self, symbol: str):
        """Test the options chain endpoint"""
        # Try different expiration dates
        expiration_dates = [
            (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        ]
        
        for exp_date in expiration_dates:
            endpoint = f"/v3/reference/options/contracts"
            params = {
                "underlying_ticker": symbol,
                "expiration_date": exp_date,
                "apiKey": self.api_key
            }
            
            logger.info(f"  3. Testing options chain for {exp_date}...")
            
            try:
                self._enforce_rate_limit()
                start_time = time.time()
                
                response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
                response_time = time.time() - start_time
                
                data_found = False
                greeks_found = False
                sample_data = None
                error_message = None
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        data_found = True
                        sample_data = results[0] if results else None
                        
                        # Check for Greeks data
                        for contract in results[:5]:  # Check first 5
                            if any([contract.get("delta"), contract.get("gamma"), contract.get("theta"), contract.get("vega")]):
                                greeks_found = True
                                break
                        
                        logger.info(f"    ✅ Found {len(results)} contracts for {exp_date}, Greeks: {greeks_found}")
                        break  # Found data, no need to try other dates
                    else:
                        logger.warning(f"    ⚠️ No contracts found for {exp_date}")
                else:
                    error_message = f"HTTP {response.status_code}"
                    logger.error(f"    ❌ Error: {response.status_code}")
                
                test_result = PolygonEndpointTest(
                    endpoint=endpoint,
                    method="GET",
                    params=params,
                    status_code=response.status_code,
                    response_time=response_time,
                    data_found=data_found,
                    greeks_found=greeks_found,
                    error_message=error_message,
                    sample_data=sample_data
                )
                
                self.endpoint_tests.append(test_result)
                
            except Exception as e:
                logger.error(f"    ❌ Exception: {e}")
                test_result = PolygonEndpointTest(
                    endpoint=endpoint,
                    method="GET",
                    params=params,
                    status_code=0,
                    response_time=0,
                    data_found=False,
                    greeks_found=False,
                    error_message=str(e)
                )
                self.endpoint_tests.append(test_result)
    
    def _test_historical_options_endpoint(self, symbol: str):
        """Test historical options data endpoints"""
        # Test historical aggregates for options (if available)
        test_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/O:{symbol}230815C00150000/range/1/day/{test_date}/{test_date}"
        params = {"apiKey": self.api_key}
        
        logger.info("  4. Testing historical options endpoint...")
        
        try:
            self._enforce_rate_limit()
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response_time = time.time() - start_time
            
            data_found = False
            greeks_found = False
            sample_data = None
            error_message = None
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    data_found = True
                    sample_data = results[0] if results else None
                    logger.info(f"    ✅ Found {len(results)} historical records")
                else:
                    logger.warning(f"    ⚠️ No historical data found")
            elif response.status_code == 404:
                error_message = "Historical options endpoint not available"
                logger.warning(f"    ⚠️ 404 - Historical options endpoint not available")
            else:
                error_message = f"HTTP {response.status_code}"
                logger.error(f"    ❌ Error: {response.status_code}")
            
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=response.status_code,
                response_time=response_time,
                data_found=data_found,
                greeks_found=greeks_found,
                error_message=error_message,
                sample_data=sample_data
            )
            
            self.endpoint_tests.append(test_result)
            
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=0,
                response_time=0,
                data_found=False,
                greeks_found=False,
                error_message=str(e)
            )
            self.endpoint_tests.append(test_result)
    
    def _test_previous_close_endpoint(self, symbol: str):
        """Test previous close endpoint for underlying price"""
        endpoint = f"/v2/aggs/ticker/{symbol}/prev"
        params = {"apiKey": self.api_key}
        
        logger.info("  5. Testing previous close endpoint...")
        
        try:
            self._enforce_rate_limit()
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response_time = time.time() - start_time
            
            data_found = False
            greeks_found = False
            sample_data = None
            error_message = None
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    data_found = True
                    sample_data = results[0] if results else None
                    logger.info(f"    ✅ Found previous close data")
                else:
                    logger.warning(f"    ⚠️ No previous close data found")
            else:
                error_message = f"HTTP {response.status_code}"
                logger.error(f"    ❌ Error: {response.status_code}")
            
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=response.status_code,
                response_time=response_time,
                data_found=data_found,
                greeks_found=greeks_found,
                error_message=error_message,
                sample_data=sample_data
            )
            
            self.endpoint_tests.append(test_result)
            
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=0,
                response_time=0,
                data_found=False,
                greeks_found=False,
                error_message=str(e)
            )
            self.endpoint_tests.append(test_result)
    
    def _test_aggregates_endpoint(self, symbol: str):
        """Test aggregates endpoint for historical price data"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
        params = {"apiKey": self.api_key}
        
        logger.info("  6. Testing aggregates endpoint...")
        
        try:
            self._enforce_rate_limit()
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response_time = time.time() - start_time
            
            data_found = False
            greeks_found = False
            sample_data = None
            error_message = None
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    data_found = True
                    sample_data = results[0] if results else None
                    logger.info(f"    ✅ Found {len(results)} historical price records")
                else:
                    logger.warning(f"    ⚠️ No historical price data found")
            else:
                error_message = f"HTTP {response.status_code}"
                logger.error(f"    ❌ Error: {response.status_code}")
            
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=response.status_code,
                response_time=response_time,
                data_found=data_found,
                greeks_found=greeks_found,
                error_message=error_message,
                sample_data=sample_data
            )
            
            self.endpoint_tests.append(test_result)
            
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            test_result = PolygonEndpointTest(
                endpoint=endpoint,
                method="GET",
                params=params,
                status_code=0,
                response_time=0,
                data_found=False,
                greeks_found=False,
                error_message=str(e)
            )
            self.endpoint_tests.append(test_result)
    
    def generate_report(self) -> str:
        """Generate a comprehensive report of the findings"""
        logger.info(f"\n📋 Generating comprehensive report...")
        
        report = []
        report.append("# Polygon Greeks Data Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_tests = len(self.endpoint_tests)
        successful_tests = len([t for t in self.endpoint_tests if t.status_code == 200])
        data_found_tests = len([t for t in self.endpoint_tests if t.data_found])
        greeks_found_tests = len([t for t in self.endpoint_tests if t.greeks_found])
        
        report.append("## Summary Statistics")
        report.append(f"- Total endpoint tests: {total_tests}")
        report.append(f"- Successful responses (200): {successful_tests}")
        report.append(f"- Tests with data found: {data_found_tests}")
        report.append(f"- Tests with Greeks data: {greeks_found_tests}")
        report.append("")
        
        # Endpoint analysis
        report.append("## Endpoint Analysis")
        
        # Group by endpoint type
        endpoint_groups = {}
        for test in self.endpoint_tests:
            endpoint_type = test.endpoint.split('/')[2] if len(test.endpoint.split('/')) > 2 else 'unknown'
            if endpoint_type not in endpoint_groups:
                endpoint_groups[endpoint_type] = []
            endpoint_groups[endpoint_type].append(test)
        
        for endpoint_type, tests in endpoint_groups.items():
            report.append(f"### {endpoint_type.upper()} Endpoints")
            
            success_count = len([t for t in tests if t.status_code == 200])
            greeks_count = len([t for t in tests if t.greeks_found])
            
            report.append(f"- Total tests: {len(tests)}")
            report.append(f"- Successful: {success_count}")
            report.append(f"- With Greeks: {greeks_count}")
            report.append("")
            
            # Show sample data if available
            for test in tests:
                if test.sample_data:
                    report.append(f"**Sample data from {test.endpoint}:**")
                    report.append(f"```json")
                    report.append(json.dumps(test.sample_data, indent=2)[:500] + "...")
                    report.append(f"```")
                    report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        
        if greeks_found_tests > 0:
            report.append("✅ **Greeks data is available** from Polygon API")
            report.append("- Use snapshot endpoints for current Greeks data")
            report.append("- Implement caching to reduce API calls")
            report.append("- Consider storing historical snapshots in database")
        else:
            report.append("❌ **No Greeks data found** in current tests")
            report.append("- Check API subscription tier for options data access")
            report.append("- Verify API key permissions")
            report.append("- Consider alternative data providers")
        
        report.append("")
        report.append("## Next Steps")
        report.append("1. Implement daily Greeks data collection")
        report.append("2. Store historical snapshots in database")
        report.append("3. Integrate with backtesting system")
        report.append("4. Monitor API rate limits and costs")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "polygon_greeks_analysis_report.md"):
        """Save the analysis report to a file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Report saved to {filename}")


def main():
    """Main function to run the Greeks data gathering analysis"""
    logger.info("🚀 Starting Polygon Greeks Data Analysis")
    logger.info("=" * 60)
    
    try:
        # Initialize gatherer
        gatherer = PolygonGreeksDataGatherer()
        
        # Test symbols
        test_symbols = ['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA']
        
        # Test all endpoints
        logger.info("🔍 Phase 1: Testing Polygon API endpoints")
        endpoint_tests = gatherer.test_polygon_endpoints(test_symbols)
        
        # Generate and save report
        logger.info("\n📋 Phase 2: Generating analysis report")
        gatherer.save_report()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ Analysis complete!")
        
        successful_tests = len([t for t in endpoint_tests if t.status_code == 200])
        greeks_found = len([t for t in endpoint_tests if t.greeks_found])
        
        logger.info(f"📊 Results:")
        logger.info(f"  - Endpoint tests: {len(endpoint_tests)}")
        logger.info(f"  - Successful responses: {successful_tests}")
        logger.info(f"  - Tests with Greeks data: {greeks_found}")
        
        if greeks_found > 0:
            logger.info("🎉 Greeks data is available from Polygon!")
        else:
            logger.warning("⚠️ No Greeks data found - check API subscription")
        
        logger.info(f"\n📄 Full report saved to: polygon_greeks_analysis_report.md")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 