#!/usr/bin/env python3
"""
Portfolio System Integration Testing
Comprehensive integration testing for the Advanced Portfolio Management System
"""
import asyncio
import aiohttp
import json
import logging
import sys
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PortfolioSystemIntegrationTester:
    """Comprehensive integration testing for portfolio system"""
    
    def __init__(self):
        self.portfolio_api_url = "http://localhost:11180"
        self.risk_api_url = "http://localhost:11181"
        self.analytics_api_url = "http://localhost:11114"
        self.mcp_api_url = "http://localhost:11117"
        
        self.test_results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Test data
        self.test_portfolio_id = "test-portfolio-001"
        self.test_assets = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        self.test_user_id = "test-user-001"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("🚀 Starting Portfolio System Integration Tests")
        logger.info("=" * 60)
        
        try:
            # Test 1: Service Health Checks
            await self.test_service_health_checks()
            
            # Test 2: Portfolio CRUD Operations
            await self.test_portfolio_crud_operations()
            
            # Test 3: Portfolio Optimization
            await self.test_portfolio_optimization()
            
            # Test 4: Risk Management
            await self.test_risk_management()
            
            # Test 5: Market Data Integration
            await self.test_market_data_integration()
            
            # Test 6: Tax Optimization
            await self.test_tax_optimization()
            
            # Test 7: Backtesting
            await self.test_backtesting()
            
            # Test 8: Analytics Integration
            await self.test_analytics_integration()
            
            # Test 9: MCP Integration
            await self.test_mcp_integration()
            
            # Test 10: End-to-End Workflow
            await self.test_end_to_end_workflow()
            
            # Generate test report
            self.generate_test_report()
            
            # Check overall success
            failed_tests = [r for r in self.test_results if not r.success]
            success_rate = (len(self.test_results) - len(failed_tests)) / len(self.test_results)
            
            logger.info(f"📊 Test Results: {len(self.test_results)} tests, {len(failed_tests)} failed")
            logger.info(f"✅ Success Rate: {success_rate:.1%}")
            
            return len(failed_tests) == 0
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            return False
    
    async def test_service_health_checks(self):
        """Test service health endpoints"""
        logger.info("🔍 Testing Service Health Checks...")
        
        services = [
            ("Portfolio Service", f"{self.portfolio_api_url}/health"),
            ("Risk Management Service", f"{self.risk_api_url}/health"),
            ("Analytics Dashboard", f"{self.analytics_api_url}/health"),
            ("MCP Service", f"{self.mcp_api_url}/health")
        ]
        
        for service_name, url in services:
            start_time = time.time()
            try:
                async with self.session.get(url) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.test_results.append(TestResult(
                            test_name=f"Health Check - {service_name}",
                            success=True,
                            duration=duration,
                            details={"status": data.get("status"), "url": url}
                        ))
                        logger.info(f"✅ {service_name}: Healthy ({duration:.2f}s)")
                    else:
                        self.test_results.append(TestResult(
                            test_name=f"Health Check - {service_name}",
                            success=False,
                            duration=duration,
                            error_message=f"HTTP {response.status}",
                            details={"url": url}
                        ))
                        logger.error(f"❌ {service_name}: HTTP {response.status}")
                        
            except Exception as e:
                duration = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=f"Health Check - {service_name}",
                    success=False,
                    duration=duration,
                    error_message=str(e),
                    details={"url": url}
                ))
                logger.error(f"❌ {service_name}: {e}")
    
    async def test_portfolio_crud_operations(self):
        """Test portfolio CRUD operations"""
        logger.info("📊 Testing Portfolio CRUD Operations...")
        
        # Create portfolio
        start_time = time.time()
        try:
            portfolio_data = {
                "name": "Test Portfolio",
                "owner_id": self.test_user_id,
                "risk_tolerance": "MODERATE",
                "base_currency": "USD",
                "rebalancing_frequency": "MONTHLY",
                "max_single_asset_weight": 0.20,
                "max_sector_weight": 0.40,
                "long_only": True
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/portfolios",
                json=portfolio_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    portfolio_id = data.get("portfolio_id")
                    self.test_results.append(TestResult(
                        test_name="Create Portfolio",
                        success=True,
                        duration=duration,
                        details={"portfolio_id": portfolio_id}
                    ))
                    logger.info(f"✅ Portfolio created: {portfolio_id}")
                else:
                    self.test_results.append(TestResult(
                        test_name="Create Portfolio",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Portfolio creation failed: HTTP {response.status}")
                    return
            
            # Read portfolio
            start_time = time.time()
            async with self.session.get(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}"
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Read Portfolio",
                        success=True,
                        duration=duration,
                        details={"portfolio_id": portfolio_id}
                    ))
                    logger.info(f"✅ Portfolio retrieved: {portfolio_id}")
                else:
                    self.test_results.append(TestResult(
                        test_name="Read Portfolio",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}"
                    ))
                    logger.error(f"❌ Portfolio retrieval failed: HTTP {response.status}")
            
            # Update portfolio
            start_time = time.time()
            update_data = {"name": "Updated Test Portfolio"}
            async with self.session.put(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}",
                json=update_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    self.test_results.append(TestResult(
                        test_name="Update Portfolio",
                        success=True,
                        duration=duration,
                        details={"portfolio_id": portfolio_id}
                    ))
                    logger.info(f"✅ Portfolio updated: {portfolio_id}")
                else:
                    self.test_results.append(TestResult(
                        test_name="Update Portfolio",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}"
                    ))
                    logger.error(f"❌ Portfolio update failed: HTTP {response.status}")
            
            # Delete portfolio
            start_time = time.time()
            async with self.session.delete(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}"
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    self.test_results.append(TestResult(
                        test_name="Delete Portfolio",
                        success=True,
                        duration=duration,
                        details={"portfolio_id": portfolio_id}
                    ))
                    logger.info(f"✅ Portfolio deleted: {portfolio_id}")
                else:
                    self.test_results.append(TestResult(
                        test_name="Delete Portfolio",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}"
                    ))
                    logger.error(f"❌ Portfolio deletion failed: HTTP {response.status}")
                    
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Portfolio CRUD Operations",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Portfolio CRUD test failed: {e}")
    
    async def test_portfolio_optimization(self):
        """Test portfolio optimization functionality"""
        logger.info("🎯 Testing Portfolio Optimization...")
        
        # Create test portfolio first
        portfolio_id = await self._create_test_portfolio()
        if not portfolio_id:
            return
        
        try:
            # Test MPT Optimization
            start_time = time.time()
            optimization_data = {
                "portfolio_id": portfolio_id,
                "optimization_type": "MPT",
                "risk_free_rate": 0.02,
                "max_iterations": 1000
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/optimization/mpt",
                json=optimization_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="MPT Optimization",
                        success=True,
                        duration=duration,
                        details={"optimization_id": data.get("optimization_id")}
                    ))
                    logger.info(f"✅ MPT Optimization completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="MPT Optimization",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ MPT Optimization failed: HTTP {response.status}")
            
            # Test Black-Litterman Optimization
            start_time = time.time()
            bl_data = {
                "portfolio_id": portfolio_id,
                "optimization_type": "BLACK_LITTERMAN",
                "views": [
                    {
                        "asset_id": "AAPL",
                        "expected_return": 0.12,
                        "confidence": 0.5
                    }
                ]
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/optimization/black-litterman",
                json=bl_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Black-Litterman Optimization",
                        success=True,
                        duration=duration,
                        details={"optimization_id": data.get("optimization_id")}
                    ))
                    logger.info(f"✅ Black-Litterman Optimization completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Black-Litterman Optimization",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Black-Litterman Optimization failed: HTTP {response.status}")
            
            # Test Risk Parity Optimization
            start_time = time.time()
            rp_data = {
                "portfolio_id": portfolio_id,
                "optimization_type": "RISK_PARITY"
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/optimization/risk-parity",
                json=rp_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Risk Parity Optimization",
                        success=True,
                        duration=duration,
                        details={"optimization_id": data.get("optimization_id")}
                    ))
                    logger.info(f"✅ Risk Parity Optimization completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Risk Parity Optimization",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Risk Parity Optimization failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Portfolio Optimization",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Portfolio optimization test failed: {e}")
        finally:
            # Clean up test portfolio
            await self._delete_test_portfolio(portfolio_id)
    
    async def test_risk_management(self):
        """Test risk management functionality"""
        logger.info("⚠️ Testing Risk Management...")
        
        # Create test portfolio first
        portfolio_id = await self._create_test_portfolio()
        if not portfolio_id:
            return
        
        try:
            # Test Risk Assessment
            start_time = time.time()
            risk_data = {
                "portfolio_id": portfolio_id,
                "confidence_levels": [0.95, 0.99],
                "lookback_period": 252
            }
            
            async with self.session.post(
                f"{self.risk_api_url}/api/v1/risk/assess",
                json=risk_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Risk Assessment",
                        success=True,
                        duration=duration,
                        details={"risk_metrics_id": data.get("risk_metrics_id")}
                    ))
                    logger.info(f"✅ Risk Assessment completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Risk Assessment",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Risk Assessment failed: HTTP {response.status}")
            
            # Test Stress Testing
            start_time = time.time()
            stress_data = {
                "portfolio_id": portfolio_id,
                "scenarios": [
                    {"name": "Market Crash", "shock_return": -0.20},
                    {"name": "Interest Rate Shock", "shock_return": 0.02}
                ]
            }
            
            async with self.session.post(
                f"{self.risk_api_url}/api/v1/risk/stress-test",
                json=stress_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Stress Testing",
                        success=True,
                        duration=duration,
                        details={"scenarios_tested": len(stress_data["scenarios"])}
                    ))
                    logger.info(f"✅ Stress Testing completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Stress Testing",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Stress Testing failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Risk Management",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Risk management test failed: {e}")
        finally:
            # Clean up test portfolio
            await self._delete_test_portfolio(portfolio_id)
    
    async def test_market_data_integration(self):
        """Test market data integration"""
        logger.info("📈 Testing Market Data Integration...")
        
        try:
            # Test asset data retrieval
            start_time = time.time()
            async with self.session.get(
                f"{self.portfolio_api_url}/api/v1/assets/AAPL"
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Asset Data Retrieval",
                        success=True,
                        duration=duration,
                        details={"symbol": data.get("symbol")}
                    ))
                    logger.info(f"✅ Asset data retrieved for AAPL ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Asset Data Retrieval",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Asset data retrieval failed: HTTP {response.status}")
            
            # Test correlation matrix
            start_time = time.time()
            correlation_data = {
                "symbols": self.test_assets,
                "days": 252
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/market-data/correlation",
                json=correlation_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Correlation Matrix",
                        success=True,
                        duration=duration,
                        details={"symbols": len(correlation_data["symbols"])}
                    ))
                    logger.info(f"✅ Correlation matrix generated ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Correlation Matrix",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Correlation matrix failed: HTTP {response.status}")
                    
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Market Data Integration",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Market data integration test failed: {e}")
    
    async def test_tax_optimization(self):
        """Test tax optimization functionality"""
        logger.info("💰 Testing Tax Optimization...")
        
        # Create test portfolio first
        portfolio_id = await self._create_test_portfolio()
        if not portfolio_id:
            return
        
        try:
            # Test Tax Loss Harvesting
            start_time = time.time()
            tax_data = {
                "portfolio_id": portfolio_id,
                "optimization_type": "tax_loss_harvesting",
                "min_harvest_amount": 1000.0
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/tax/optimize",
                json=tax_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Tax Loss Harvesting",
                        success=True,
                        duration=duration,
                        details={"optimization_id": data.get("optimization_id")}
                    ))
                    logger.info(f"✅ Tax Loss Harvesting completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Tax Loss Harvesting",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Tax Loss Harvesting failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Tax Optimization",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Tax optimization test failed: {e}")
        finally:
            # Clean up test portfolio
            await self._delete_test_portfolio(portfolio_id)
    
    async def test_backtesting(self):
        """Test backtesting functionality"""
        logger.info("📊 Testing Backtesting...")
        
        # Create test portfolio first
        portfolio_id = await self._create_test_portfolio()
        if not portfolio_id:
            return
        
        try:
            # Test Portfolio Backtesting
            start_time = time.time()
            backtest_data = {
                "portfolio_id": portfolio_id,
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "benchmark_symbol": "SPY",
                "transaction_cost": 0.001
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/backtesting/portfolio",
                json=backtest_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="Portfolio Backtesting",
                        success=True,
                        duration=duration,
                        details={"backtest_id": data.get("backtest_id")}
                    ))
                    logger.info(f"✅ Portfolio Backtesting completed ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Portfolio Backtesting",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"response": await response.text()}
                    ))
                    logger.error(f"❌ Portfolio Backtesting failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Backtesting",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Backtesting test failed: {e}")
        finally:
            # Clean up test portfolio
            await self._delete_test_portfolio(portfolio_id)
    
    async def test_analytics_integration(self):
        """Test analytics dashboard integration"""
        logger.info("📊 Testing Analytics Integration...")
        
        try:
            # Test analytics dashboard health
            start_time = time.time()
            async with self.session.get(
                f"{self.analytics_api_url}/health"
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    self.test_results.append(TestResult(
                        test_name="Analytics Dashboard Health",
                        success=True,
                        duration=duration,
                        details={"url": self.analytics_api_url}
                    ))
                    logger.info(f"✅ Analytics Dashboard is healthy ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="Analytics Dashboard Health",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"url": self.analytics_api_url}
                    ))
                    logger.error(f"❌ Analytics Dashboard health check failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="Analytics Integration",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ Analytics integration test failed: {e}")
    
    async def test_mcp_integration(self):
        """Test MCP service integration"""
        logger.info("🤖 Testing MCP Integration...")
        
        try:
            # Test MCP service health
            start_time = time.time()
            async with self.session.get(
                f"{self.mcp_api_url}/health"
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(TestResult(
                        test_name="MCP Service Health",
                        success=True,
                        duration=duration,
                        details={"status": data.get("status")}
                    ))
                    logger.info(f"✅ MCP Service is healthy ({duration:.2f}s)")
                else:
                    self.test_results.append(TestResult(
                        test_name="MCP Service Health",
                        success=False,
                        duration=duration,
                        error_message=f"HTTP {response.status}",
                        details={"url": self.mcp_api_url}
                    ))
                    logger.error(f"❌ MCP Service health check failed: HTTP {response.status}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="MCP Integration",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ MCP integration test failed: {e}")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("🔄 Testing End-to-End Workflow...")
        
        start_time = time.time()
        try:
            # Step 1: Create portfolio
            portfolio_id = await self._create_test_portfolio()
            if not portfolio_id:
                raise Exception("Failed to create test portfolio")
            
            # Step 2: Add positions
            await self._add_test_positions(portfolio_id)
            
            # Step 3: Run optimization
            await self._run_portfolio_optimization(portfolio_id)
            
            # Step 4: Run risk assessment
            await self._run_risk_assessment(portfolio_id)
            
            # Step 5: Run tax optimization
            await self._run_tax_optimization(portfolio_id)
            
            # Step 6: Run backtesting
            await self._run_backtesting(portfolio_id)
            
            # Step 7: Generate insights
            await self._generate_insights(portfolio_id)
            
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="End-to-End Workflow",
                success=True,
                duration=duration,
                details={"portfolio_id": portfolio_id}
            ))
            logger.info(f"✅ End-to-End Workflow completed successfully ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="End-to-End Workflow",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
            logger.error(f"❌ End-to-End Workflow failed: {e}")
        finally:
            # Clean up test portfolio
            if 'portfolio_id' in locals():
                await self._delete_test_portfolio(portfolio_id)
    
    async def _create_test_portfolio(self) -> Optional[str]:
        """Create test portfolio"""
        try:
            portfolio_data = {
                "name": "Integration Test Portfolio",
                "owner_id": self.test_user_id,
                "risk_tolerance": "MODERATE",
                "base_currency": "USD",
                "rebalancing_frequency": "MONTHLY",
                "max_single_asset_weight": 0.20,
                "max_sector_weight": 0.40,
                "long_only": True
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/portfolios",
                json=portfolio_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    return data.get("portfolio_id")
                else:
                    logger.error(f"Failed to create test portfolio: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating test portfolio: {e}")
            return None
    
    async def _add_test_positions(self, portfolio_id: str):
        """Add test positions to portfolio"""
        for asset in self.test_assets:
            position_data = {
                "asset_id": asset,
                "quantity": 100.0,
                "average_cost": 100.0,
                "current_price": 105.0
            }
            
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}/positions",
                json=position_data
            ) as response:
                if response.status != 201:
                    logger.warning(f"Failed to add position for {asset}: HTTP {response.status}")
    
    async def _run_portfolio_optimization(self, portfolio_id: str):
        """Run portfolio optimization"""
        optimization_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "MPT",
            "risk_free_rate": 0.02
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/mpt",
            json=optimization_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Optimization failed: HTTP {response.status}")
    
    async def _run_risk_assessment(self, portfolio_id: str):
        """Run risk assessment"""
        risk_data = {
            "portfolio_id": portfolio_id,
            "confidence_levels": [0.95, 0.99]
        }
        
        async with self.session.post(
            f"{self.risk_api_url}/api/v1/risk/assess",
            json=risk_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Risk assessment failed: HTTP {response.status}")
    
    async def _run_tax_optimization(self, portfolio_id: str):
        """Run tax optimization"""
        tax_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "tax_loss_harvesting"
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/tax/optimize",
            json=tax_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Tax optimization failed: HTTP {response.status}")
    
    async def _run_backtesting(self, portfolio_id: str):
        """Run backtesting"""
        backtest_data = {
            "portfolio_id": portfolio_id,
            "start_date": "2020-01-01",
            "end_date": "2023-12-31",
            "benchmark_symbol": "SPY"
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/backtesting/portfolio",
            json=backtest_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Backtesting failed: HTTP {response.status}")
    
    async def _generate_insights(self, portfolio_id: str):
        """Generate portfolio insights"""
        insights_data = {
            "portfolio_id": portfolio_id
        }
        
        async with self.session.post(
            f"{self.mcp_api_url}/api/v1/insights/generate",
            json=insights_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Insights generation failed: HTTP {response.status}")
    
    async def _delete_test_portfolio(self, portfolio_id: str):
        """Delete test portfolio"""
        try:
            async with self.session.delete(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"✅ Test portfolio {portfolio_id} deleted")
                else:
                    logger.warning(f"Failed to delete test portfolio: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"Error deleting test portfolio: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📋 Generating Test Report...")
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.success])
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Calculate timing statistics
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        # Generate report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "average_duration": avg_duration
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in self.test_results
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save report to file
        report_filename = f"portfolio_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Test report saved to: {report_filename}")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1%}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Average Duration: {avg_duration:.2f}s")
        
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result.success:
                    logger.info(f"  - {result.test_name}: {result.error_message}")
        
        logger.info("=" * 60)

async def main():
    """Main function"""
    async with PortfolioSystemIntegrationTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())



