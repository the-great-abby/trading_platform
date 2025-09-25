#!/usr/bin/env python3
"""
Portfolio Optimization Demo
Demonstrates Modern Portfolio Theory (MPT) optimization with efficient frontier generation
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

class PortfolioOptimizationDemo:
    """Portfolio optimization demonstration"""
    
    def __init__(self, portfolio_api_url: str = "http://localhost:11180"):
        self.portfolio_api_url = portfolio_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Demo configuration
        self.demo_assets = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "SPOT", "SQ",
            "SPY", "QQQ", "IWM", "VTI", "VEA", "VWO", "BND", "TLT"
        ]
        self.demo_user_id = "demo-user-001"
        self.demo_portfolio_id = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_demo(self, risk_tolerance: str = "MODERATE", 
                      optimization_type: str = "MPT") -> Dict[str, Any]:
        """Run the complete portfolio optimization demo"""
        logger.info("🚀 Starting Portfolio Optimization Demo")
        logger.info("=" * 60)
        
        demo_results = {
            "demo_name": "Portfolio Optimization Demo",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "risk_tolerance": risk_tolerance,
                "optimization_type": optimization_type,
                "asset_universe": self.demo_assets
            },
            "results": {}
        }
        
        try:
            # Step 1: Create demo portfolio
            logger.info("📊 Step 1: Creating demo portfolio...")
            portfolio_id = await self._create_demo_portfolio(risk_tolerance)
            demo_results["results"]["portfolio_creation"] = {"success": True, "portfolio_id": portfolio_id}
            
            # Step 2: Add demo positions
            logger.info("💰 Step 2: Adding demo positions...")
            await self._add_demo_positions(portfolio_id)
            demo_results["results"]["position_creation"] = {"success": True}
            
            # Step 3: Run optimization
            logger.info("🎯 Step 3: Running portfolio optimization...")
            optimization_result = await self._run_optimization(portfolio_id, optimization_type)
            demo_results["results"]["optimization"] = optimization_result
            
            # Step 4: Generate efficient frontier
            logger.info("📈 Step 4: Generating efficient frontier...")
            frontier_result = await self._generate_efficient_frontier(portfolio_id)
            demo_results["results"]["efficient_frontier"] = frontier_result
            
            # Step 5: Analyze results
            logger.info("📊 Step 5: Analyzing optimization results...")
            analysis_result = await self._analyze_optimization_results(portfolio_id)
            demo_results["results"]["analysis"] = analysis_result
            
            # Step 6: Display results
            self._display_results(demo_results)
            
            # Step 7: Clean up
            logger.info("🧹 Step 7: Cleaning up demo portfolio...")
            await self._cleanup_demo_portfolio(portfolio_id)
            demo_results["results"]["cleanup"] = {"success": True}
            
            logger.info("✅ Portfolio Optimization Demo completed successfully!")
            return demo_results
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            demo_results["results"]["error"] = {"message": str(e)}
            return demo_results
    
    async def _create_demo_portfolio(self, risk_tolerance: str) -> str:
        """Create demo portfolio"""
        portfolio_data = {
            "name": f"Demo Portfolio - {risk_tolerance} Risk",
            "owner_id": self.demo_user_id,
            "risk_tolerance": risk_tolerance,
            "base_currency": "USD",
            "rebalancing_frequency": "MONTHLY",
            "max_single_asset_weight": 0.20,
            "max_sector_weight": 0.40,
            "long_only": True,
            "description": "Demo portfolio for optimization demonstration"
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
        """Add demo positions to portfolio"""
        # Create realistic demo positions
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
    
    async def _run_optimization(self, portfolio_id: str, optimization_type: str) -> Dict[str, Any]:
        """Run portfolio optimization"""
        optimization_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": optimization_type,
            "risk_free_rate": 0.02,
            "max_iterations": 1000,
            "convergence_tolerance": 1e-6,
            "max_single_asset_weight": 0.20,
            "min_single_asset_weight": 0.0,
            "enable_short_selling": False,
            "transaction_cost_rate": 0.001
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/{optimization_type.lower().replace('_', '-')}",
            json=optimization_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Optimization completed: {data.get('optimization_id')}")
                return {
                    "success": True,
                    "optimization_id": data.get("optimization_id"),
                    "expected_return": data.get("expected_return"),
                    "expected_volatility": data.get("expected_volatility"),
                    "sharpe_ratio": data.get("sharpe_ratio"),
                    "convergence_achieved": data.get("convergence_achieved"),
                    "iterations": data.get("iterations")
                }
            else:
                error_text = await response.text()
                raise Exception(f"Optimization failed: HTTP {response.status} - {error_text}")
    
    async def _generate_efficient_frontier(self, portfolio_id: str) -> Dict[str, Any]:
        """Generate efficient frontier"""
        frontier_data = {
            "portfolio_id": portfolio_id,
            "num_portfolios": 100,
            "risk_free_rate": 0.02,
            "min_return": 0.05,
            "max_return": 0.25
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/efficient-frontier",
            json=frontier_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Efficient frontier generated with {len(data.get('frontier_points', []))} points")
                return {
                    "success": True,
                    "frontier_points": len(data.get("frontier_points", [])),
                    "max_sharpe_portfolio": data.get("max_sharpe_portfolio"),
                    "min_variance_portfolio": data.get("min_variance_portfolio")
                }
            else:
                error_text = await response.text()
                raise Exception(f"Efficient frontier generation failed: HTTP {response.status} - {error_text}")
    
    async def _analyze_optimization_results(self, portfolio_id: str) -> Dict[str, Any]:
        """Analyze optimization results"""
        # Get optimization results
        async with self.session.get(
            f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                # Analyze the results
                analysis = {
                    "success": True,
                    "total_optimizations": len(data.get("results", [])),
                    "latest_optimization": data.get("results", [])[-1] if data.get("results") else None
                }
                
                if analysis["latest_optimization"]:
                    opt = analysis["latest_optimization"]
                    analysis["summary"] = {
                        "expected_return": f"{opt.get('expected_return', 0):.2%}",
                        "expected_volatility": f"{opt.get('expected_volatility', 0):.2%}",
                        "sharpe_ratio": f"{opt.get('sharpe_ratio', 0):.2f}",
                        "convergence_achieved": opt.get('convergence_achieved', False),
                        "iterations": opt.get('iterations', 0)
                    }
                
                logger.info("✅ Optimization results analyzed")
                return analysis
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get optimization results: HTTP {response.status} - {error_text}")
    
    def _display_results(self, demo_results: Dict[str, Any]):
        """Display demo results in a formatted way"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 PORTFOLIO OPTIMIZATION DEMO RESULTS")
        logger.info("=" * 60)
        
        # Configuration
        config = demo_results["configuration"]
        logger.info(f"🎯 Risk Tolerance: {config['risk_tolerance']}")
        logger.info(f"🔧 Optimization Type: {config['optimization_type']}")
        logger.info(f"📈 Asset Universe: {len(config['asset_universe'])} assets")
        
        # Optimization Results
        if "optimization" in demo_results["results"]:
            opt = demo_results["results"]["optimization"]
            if opt.get("success"):
                logger.info(f"✅ Optimization ID: {opt.get('optimization_id')}")
                logger.info(f"📈 Expected Return: {opt.get('expected_return', 0):.2%}")
                logger.info(f"📊 Expected Volatility: {opt.get('expected_volatility', 0):.2%}")
                logger.info(f"🎯 Sharpe Ratio: {opt.get('sharpe_ratio', 0):.2f}")
                logger.info(f"🔄 Convergence: {'✅' if opt.get('convergence_achieved') else '❌'}")
                logger.info(f"🔄 Iterations: {opt.get('iterations', 0)}")
        
        # Efficient Frontier Results
        if "efficient_frontier" in demo_results["results"]:
            frontier = demo_results["results"]["efficient_frontier"]
            if frontier.get("success"):
                logger.info(f"📈 Efficient Frontier Points: {frontier.get('frontier_points', 0)}")
                logger.info(f"🎯 Max Sharpe Portfolio: {frontier.get('max_sharpe_portfolio', 'N/A')}")
                logger.info(f"📊 Min Variance Portfolio: {frontier.get('min_variance_portfolio', 'N/A')}")
        
        # Analysis Results
        if "analysis" in demo_results["results"]:
            analysis = demo_results["results"]["analysis"]
            if analysis.get("success") and "summary" in analysis:
                summary = analysis["summary"]
                logger.info(f"📊 Total Optimizations: {analysis.get('total_optimizations', 0)}")
                logger.info(f"📈 Latest Return: {summary.get('expected_return', 'N/A')}")
                logger.info(f"📊 Latest Volatility: {summary.get('expected_volatility', 'N/A')}")
                logger.info(f"🎯 Latest Sharpe: {summary.get('sharpe_ratio', 'N/A')}")
        
        logger.info("=" * 60)
        logger.info("✅ Demo completed successfully!")
    
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
    parser = argparse.ArgumentParser(description="Portfolio Optimization Demo")
    parser.add_argument("--risk-tolerance", choices=["CONSERVATIVE", "MODERATE", "AGGRESSIVE"], 
                       default="MODERATE", help="Risk tolerance level")
    parser.add_argument("--optimization-type", choices=["MPT", "BLACK_LITTERMAN", "RISK_PARITY"], 
                       default="MPT", help="Optimization type")
    parser.add_argument("--portfolio-api-url", default="http://localhost:11180", 
                       help="Portfolio API URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with PortfolioOptimizationDemo(args.portfolio_api_url) as demo:
        results = await demo.run_demo(args.risk_tolerance, args.optimization_type)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {args.output}")
        
        # Return success/failure for script exit code
        return 0 if not results.get("results", {}).get("error") else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

