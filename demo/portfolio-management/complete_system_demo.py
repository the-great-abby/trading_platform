#!/usr/bin/env python3
"""
Complete System Demo
Demonstrates the full Advanced Portfolio Management System workflow
"""
import asyncio
import aiohttp
import json
import argparse
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteSystemDemo:
    """Complete system demonstration"""
    
    def __init__(self, portfolio_api_url: str = "http://localhost:11180",
                 risk_api_url: str = "http://localhost:11181"):
        self.portfolio_api_url = portfolio_api_url
        self.risk_api_url = risk_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Demo configuration
        self.demo_assets = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "SPOT", "SQ",
            "SPY", "QQQ", "IWM", "VTI", "VEA", "VWO", "BND", "TLT"
        ]
        self.demo_user_id = "demo-user-complete"
        self.demo_portfolio_id = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_demo(self) -> Dict[str, Any]:
        """Run the complete system demonstration"""
        logger.info("🚀 Starting Complete System Demo")
        logger.info("=" * 60)
        
        demo_results = {
            "demo_name": "Complete System Demo",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "asset_universe": self.demo_assets,
                "description": "Complete Advanced Portfolio Management System workflow demonstration"
            },
            "results": {}
        }
        
        try:
            # Step 1: Health Check
            logger.info("🏥 Step 1: System health check...")
            health_result = await self._check_system_health()
            demo_results["results"]["health_check"] = health_result
            
            # Step 2: Create Portfolio
            logger.info("📊 Step 2: Creating portfolio...")
            portfolio_id = await self._create_demo_portfolio()
            demo_results["results"]["portfolio_creation"] = {"success": True, "portfolio_id": portfolio_id}
            
            # Step 3: Add Positions
            logger.info("💰 Step 3: Adding positions...")
            await self._add_demo_positions(portfolio_id)
            demo_results["results"]["position_creation"] = {"success": True}
            
            # Step 4: Market Data Integration
            logger.info("📈 Step 4: Market data integration...")
            market_data_result = await self._test_market_data_integration()
            demo_results["results"]["market_data"] = market_data_result
            
            # Step 5: Portfolio Optimization
            logger.info("🎯 Step 5: Portfolio optimization...")
            optimization_result = await self._run_portfolio_optimization(portfolio_id)
            demo_results["results"]["optimization"] = optimization_result
            
            # Step 6: Risk Management
            logger.info("⚠️ Step 6: Risk management...")
            risk_result = await self._run_risk_management(portfolio_id)
            demo_results["results"]["risk_management"] = risk_result
            
            # Step 7: Tax Optimization
            logger.info("💰 Step 7: Tax optimization...")
            tax_result = await self._run_tax_optimization(portfolio_id)
            demo_results["results"]["tax_optimization"] = tax_result
            
            # Step 8: Rebalancing
            logger.info("⚖️ Step 8: Portfolio rebalancing...")
            rebalancing_result = await self._run_rebalancing(portfolio_id)
            demo_results["results"]["rebalancing"] = rebalancing_result
            
            # Step 9: Backtesting
            logger.info("📊 Step 9: Portfolio backtesting...")
            backtesting_result = await self._run_backtesting(portfolio_id)
            demo_results["results"]["backtesting"] = backtesting_result
            
            # Step 10: Performance Analytics
            logger.info("📈 Step 10: Performance analytics...")
            analytics_result = await self._run_performance_analytics(portfolio_id)
            demo_results["results"]["analytics"] = analytics_result
            
            # Step 11: Display Results
            self._display_results(demo_results)
            
            # Step 12: Cleanup
            logger.info("🧹 Step 12: Cleaning up...")
            await self._cleanup_demo_portfolio(portfolio_id)
            demo_results["results"]["cleanup"] = {"success": True}
            
            logger.info("✅ Complete System Demo completed successfully!")
            return demo_results
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            demo_results["results"]["error"] = {"message": str(e)}
            return demo_results
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system health"""
        health_checks = {}
        
        # Check Portfolio Service
        try:
            async with self.session.get(f"{self.portfolio_api_url}/health") as response:
                health_checks["portfolio_service"] = {
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "http_status": response.status
                }
        except Exception as e:
            health_checks["portfolio_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Risk Management Service
        try:
            async with self.session.get(f"{self.risk_api_url}/health") as response:
                health_checks["risk_service"] = {
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "http_status": response.status
                }
        except Exception as e:
            health_checks["risk_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        all_healthy = all(check.get("status") == "healthy" for check in health_checks.values())
        
        logger.info(f"✅ System health check: {'All healthy' if all_healthy else 'Some services unhealthy'}")
        return {
            "success": all_healthy,
            "services": health_checks,
            "overall_status": "healthy" if all_healthy else "unhealthy"
        }
    
    async def _create_demo_portfolio(self) -> str:
        """Create demo portfolio"""
        portfolio_data = {
            "name": "Complete System Demo Portfolio",
            "owner_id": self.demo_user_id,
            "risk_tolerance": "MODERATE",
            "base_currency": "USD",
            "rebalancing_frequency": "MONTHLY",
            "max_single_asset_weight": 0.20,
            "max_sector_weight": 0.40,
            "long_only": True,
            "description": "Demo portfolio for complete system demonstration"
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/portfolios",
            json=portfolio_data
        ) as response:
            if response.status == 201:
                data = await response.json()
                portfolio_id = data.get("portfolio_id")
                logger.info(f"✅ Created demo portfolio: {portfolio_id}")
                return portfolio_id
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create portfolio: HTTP {response.status} - {error_text}")
    
    async def _add_demo_positions(self, portfolio_id: str):
        """Add demo positions"""
        demo_positions = [
            {"asset_id": "AAPL", "quantity": 100, "average_cost": 150.0, "current_price": 175.0},
            {"asset_id": "GOOGL", "quantity": 50, "average_cost": 2500.0, "current_price": 2800.0},
            {"asset_id": "MSFT", "quantity": 75, "average_cost": 300.0, "current_price": 350.0},
            {"asset_id": "TSLA", "quantity": 25, "average_cost": 200.0, "current_price": 250.0},
            {"asset_id": "AMZN", "quantity": 30, "average_cost": 3000.0, "current_price": 3200.0},
            {"asset_id": "SPY", "quantity": 200, "average_cost": 400.0, "current_price": 420.0},
            {"asset_id": "QQQ", "quantity": 100, "average_cost": 350.0, "current_price": 380.0},
            {"asset_id": "BND", "quantity": 150, "average_cost": 80.0, "current_price": 85.0}
        ]
        
        for position in demo_positions:
            async with self.session.post(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}/positions",
                json=position
            ) as response:
                if response.status == 201:
                    logger.info(f"✅ Added position: {position['asset_id']}")
                else:
                    logger.warning(f"⚠️ Failed to add position {position['asset_id']}: HTTP {response.status}")
    
    async def _test_market_data_integration(self) -> Dict[str, Any]:
        """Test market data integration"""
        try:
            # Test asset data retrieval
            async with self.session.get(
                f"{self.portfolio_api_url}/api/v1/assets/AAPL"
            ) as response:
                if response.status == 200:
                    asset_data = await response.json()
                    logger.info("✅ Market data integration successful")
                    return {
                        "success": True,
                        "asset_data_retrieved": True,
                        "sample_asset": asset_data.get("symbol", "AAPL")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "asset_data_retrieved": False
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "asset_data_retrieved": False
            }
    
    async def _run_portfolio_optimization(self, portfolio_id: str) -> Dict[str, Any]:
        """Run portfolio optimization"""
        optimization_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "MPT",
            "risk_free_rate": 0.02,
            "max_iterations": 1000,
            "convergence_tolerance": 1e-6
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/mpt",
            json=optimization_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Portfolio optimization completed: {data.get('optimization_id')}")
                return {
                    "success": True,
                    "optimization_id": data.get("optimization_id"),
                    "expected_return": data.get("expected_return"),
                    "expected_volatility": data.get("expected_volatility"),
                    "sharpe_ratio": data.get("sharpe_ratio")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    async def _run_risk_management(self, portfolio_id: str) -> Dict[str, Any]:
        """Run risk management"""
        risk_data = {
            "portfolio_id": portfolio_id,
            "confidence_levels": [0.95, 0.99],
            "lookback_period": 252
        }
        
        async with self.session.post(
            f"{self.risk_api_url}/api/v1/risk/assess",
            json=risk_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Risk assessment completed: {data.get('risk_metrics_id')}")
                return {
                    "success": True,
                    "risk_metrics_id": data.get("risk_metrics_id"),
                    "var_95": data.get("var_95"),
                    "var_99": data.get("var_99"),
                    "portfolio_volatility": data.get("portfolio_volatility")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    async def _run_tax_optimization(self, portfolio_id: str) -> Dict[str, Any]:
        """Run tax optimization"""
        tax_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "tax_loss_harvesting",
            "min_harvest_amount": 1000.0
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/tax/optimize",
            json=tax_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Tax optimization completed: {data.get('optimization_id')}")
                return {
                    "success": True,
                    "optimization_id": data.get("optimization_id"),
                    "tax_benefit": data.get("tax_benefit"),
                    "harvested_losses": data.get("harvested_losses")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    async def _run_rebalancing(self, portfolio_id: str) -> Dict[str, Any]:
        """Run portfolio rebalancing"""
        rebalancing_data = {
            "portfolio_id": portfolio_id,
            "strategy": "intelligent",
            "drift_threshold": 0.05
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/rebalancing/recommend",
            json=rebalancing_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Rebalancing recommendations generated: {data.get('recommendation_id')}")
                return {
                    "success": True,
                    "recommendation_id": data.get("recommendation_id"),
                    "total_drift": data.get("total_drift"),
                    "number_of_trades": data.get("number_of_trades")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    async def _run_backtesting(self, portfolio_id: str) -> Dict[str, Any]:
        """Run portfolio backtesting"""
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
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Portfolio backtesting completed: {data.get('backtest_id')}")
                return {
                    "success": True,
                    "backtest_id": data.get("backtest_id"),
                    "total_return": data.get("total_return"),
                    "annualized_return": data.get("annualized_return"),
                    "sharpe_ratio": data.get("sharpe_ratio"),
                    "max_drawdown": data.get("max_drawdown")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    async def _run_performance_analytics(self, portfolio_id: str) -> Dict[str, Any]:
        """Run performance analytics"""
        analytics_data = {
            "portfolio_id": portfolio_id,
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        }
        
        async with self.session.get(
            f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}/performance",
            params=analytics_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("✅ Performance analytics completed")
                return {
                    "success": True,
                    "total_return": data.get("total_return"),
                    "annualized_return": data.get("annualized_return"),
                    "volatility": data.get("volatility"),
                    "sharpe_ratio": data.get("sharpe_ratio"),
                    "max_drawdown": data.get("max_drawdown")
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status} - {error_text}"
                }
    
    def _display_results(self, demo_results: Dict[str, Any]):
        """Display comprehensive demo results"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPLETE SYSTEM DEMO RESULTS")
        logger.info("=" * 60)
        
        # Configuration
        config = demo_results["configuration"]
        logger.info(f"📈 Asset Universe: {len(config['asset_universe'])} assets")
        logger.info(f"📝 Description: {config['description']}")
        
        # Health Check
        if "health_check" in demo_results["results"]:
            health = demo_results["results"]["health_check"]
            logger.info(f"🏥 System Health: {health['overall_status'].upper()}")
            for service, status in health["services"].items():
                logger.info(f"   • {service}: {status['status']}")
        
        # Portfolio Creation
        if "portfolio_creation" in demo_results["results"]:
            portfolio = demo_results["results"]["portfolio_creation"]
            logger.info(f"📊 Portfolio Created: {portfolio['portfolio_id']}")
        
        # Market Data
        if "market_data" in demo_results["results"]:
            market_data = demo_results["results"]["market_data"]
            logger.info(f"📈 Market Data: {'✅ Success' if market_data['success'] else '❌ Failed'}")
        
        # Optimization
        if "optimization" in demo_results["results"]:
            opt = demo_results["results"]["optimization"]
            if opt.get("success"):
                logger.info(f"🎯 Optimization: ✅ Success")
                logger.info(f"   • Expected Return: {opt.get('expected_return', 0):.2%}")
                logger.info(f"   • Expected Volatility: {opt.get('expected_volatility', 0):.2%}")
                logger.info(f"   • Sharpe Ratio: {opt.get('sharpe_ratio', 0):.2f}")
            else:
                logger.info(f"🎯 Optimization: ❌ Failed - {opt.get('error', 'Unknown error')}")
        
        # Risk Management
        if "risk_management" in demo_results["results"]:
            risk = demo_results["results"]["risk_management"]
            if risk.get("success"):
                logger.info(f"⚠️ Risk Management: ✅ Success")
                logger.info(f"   • VaR 95%: {risk.get('var_95', 0):.2%}")
                logger.info(f"   • VaR 99%: {risk.get('var_99', 0):.2%}")
                logger.info(f"   • Volatility: {risk.get('portfolio_volatility', 0):.2%}")
            else:
                logger.info(f"⚠️ Risk Management: ❌ Failed - {risk.get('error', 'Unknown error')}")
        
        # Tax Optimization
        if "tax_optimization" in demo_results["results"]:
            tax = demo_results["results"]["tax_optimization"]
            if tax.get("success"):
                logger.info(f"💰 Tax Optimization: ✅ Success")
                logger.info(f"   • Tax Benefit: ${tax.get('tax_benefit', 0):,.2f}")
                logger.info(f"   • Harvested Losses: ${tax.get('harvested_losses', 0):,.2f}")
            else:
                logger.info(f"💰 Tax Optimization: ❌ Failed - {tax.get('error', 'Unknown error')}")
        
        # Rebalancing
        if "rebalancing" in demo_results["results"]:
            reb = demo_results["results"]["rebalancing"]
            if reb.get("success"):
                logger.info(f"⚖️ Rebalancing: ✅ Success")
                logger.info(f"   • Total Drift: {reb.get('total_drift', 0):.2%}")
                logger.info(f"   • Number of Trades: {reb.get('number_of_trades', 0)}")
            else:
                logger.info(f"⚖️ Rebalancing: ❌ Failed - {reb.get('error', 'Unknown error')}")
        
        # Backtesting
        if "backtesting" in demo_results["results"]:
            backtest = demo_results["results"]["backtesting"]
            if backtest.get("success"):
                logger.info(f"📊 Backtesting: ✅ Success")
                logger.info(f"   • Total Return: {backtest.get('total_return', 0):.2%}")
                logger.info(f"   • Annualized Return: {backtest.get('annualized_return', 0):.2%}")
                logger.info(f"   • Sharpe Ratio: {backtest.get('sharpe_ratio', 0):.2f}")
                logger.info(f"   • Max Drawdown: {backtest.get('max_drawdown', 0):.2%}")
            else:
                logger.info(f"📊 Backtesting: ❌ Failed - {backtest.get('error', 'Unknown error')}")
        
        # Analytics
        if "analytics" in demo_results["results"]:
            analytics = demo_results["results"]["analytics"]
            if analytics.get("success"):
                logger.info(f"📈 Analytics: ✅ Success")
                logger.info(f"   • Total Return: {analytics.get('total_return', 0):.2%}")
                logger.info(f"   • Volatility: {analytics.get('volatility', 0):.2%}")
                logger.info(f"   • Sharpe Ratio: {analytics.get('sharpe_ratio', 0):.2f}")
            else:
                logger.info(f"📈 Analytics: ❌ Failed - {analytics.get('error', 'Unknown error')}")
        
        # Summary
        successful_steps = sum(1 for result in demo_results["results"].values() 
                             if isinstance(result, dict) and result.get("success"))
        total_steps = len([r for r in demo_results["results"].values() 
                          if isinstance(r, dict) and "success" in r])
        
        logger.info("=" * 60)
        logger.info(f"📊 SUMMARY: {successful_steps}/{total_steps} steps completed successfully")
        logger.info("✅ Complete System Demo finished!")
    
    async def _cleanup_demo_portfolio(self, portfolio_id: str):
        """Clean up demo portfolio"""
        try:
            async with self.session.delete(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"✅ Demo portfolio {portfolio_id} deleted")
                else:
                    logger.warning(f"⚠️ Failed to delete demo portfolio: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up demo portfolio: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Complete System Demo")
    parser.add_argument("--portfolio-api-url", default="http://localhost:11180",
                       help="Portfolio API URL")
    parser.add_argument("--risk-api-url", default="http://localhost:11181",
                       help="Risk API URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with CompleteSystemDemo(args.portfolio_api_url, args.risk_api_url) as demo:
        results = await demo.run_demo()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {args.output}")
        
        # Return success/failure for script exit code
        return 0 if not results.get("results", {}).get("error") else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
























