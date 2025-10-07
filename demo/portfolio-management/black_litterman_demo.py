#!/usr/bin/env python3
"""
Black-Litterman Demo
Demonstrates Black-Litterman model with market views and confidence levels
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

class BlackLittermanDemo:
    """Black-Litterman model demonstration"""
    
    def __init__(self, portfolio_api_url: str = "http://localhost:11180"):
        self.portfolio_api_url = portfolio_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Demo configuration
        self.demo_assets = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "SPOT", "SQ"
        ]
        self.demo_user_id = "demo-user-003"
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
    
    async def run_demo(self, confidence_level: float = 0.5, 
                      risk_aversion: float = 3.0) -> Dict[str, Any]:
        """Run the complete Black-Litterman demo"""
        logger.info("🚀 Starting Black-Litterman Demo")
        logger.info("=" * 60)
        
        demo_results = {
            "demo_name": "Black-Litterman Demo",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "confidence_level": confidence_level,
                "risk_aversion": risk_aversion,
                "asset_universe": self.demo_assets,
                "description": "Black-Litterman model with market views and confidence levels"
            },
            "results": {}
        }
        
        try:
            # Step 1: Create demo portfolio
            logger.info("📊 Step 1: Creating demo portfolio...")
            portfolio_id = await self._create_demo_portfolio()
            demo_results["results"]["portfolio_creation"] = {"success": True, "portfolio_id": portfolio_id}
            
            # Step 2: Add demo positions
            logger.info("💰 Step 2: Adding demo positions...")
            await self._add_demo_positions(portfolio_id)
            demo_results["results"]["position_creation"] = {"success": True}
            
            # Step 3: Create market views
            logger.info("🎯 Step 3: Creating market views...")
            market_views = await self._create_market_views()
            demo_results["results"]["market_views"] = market_views
            
            # Step 4: Run Black-Litterman optimization
            logger.info("📈 Step 4: Running Black-Litterman optimization...")
            optimization_result = await self._run_black_litterman_optimization(
                portfolio_id, market_views, confidence_level, risk_aversion
            )
            demo_results["results"]["optimization"] = optimization_result
            
            # Step 5: Compare with market equilibrium
            logger.info("🔄 Step 5: Comparing with market equilibrium...")
            comparison_result = await self._compare_with_market_equilibrium(portfolio_id)
            demo_results["results"]["comparison"] = comparison_result
            
            # Step 6: Analyze view impact
            logger.info("📊 Step 6: Analyzing view impact...")
            impact_analysis = await self._analyze_view_impact(portfolio_id, market_views)
            demo_results["results"]["view_impact"] = impact_analysis
            
            # Step 7: Display results
            self._display_results(demo_results)
            
            # Step 8: Clean up
            logger.info("🧹 Step 8: Cleaning up demo portfolio...")
            await self._cleanup_demo_portfolio(portfolio_id)
            demo_results["results"]["cleanup"] = {"success": True}
            
            logger.info("✅ Black-Litterman Demo completed successfully!")
            return demo_results
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            demo_results["results"]["error"] = {"message": str(e)}
            return demo_results
    
    async def _create_demo_portfolio(self) -> str:
        """Create demo portfolio for Black-Litterman"""
        portfolio_data = {
            "name": "Demo Portfolio - Black-Litterman",
            "owner_id": self.demo_user_id,
            "risk_tolerance": "MODERATE",
            "base_currency": "USD",
            "rebalancing_frequency": "MONTHLY",
            "max_single_asset_weight": 0.25,
            "max_sector_weight": 0.50,
            "long_only": True,
            "description": "Demo portfolio for Black-Litterman optimization demonstration"
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
        # Create tech-focused demo positions
        demo_positions = [
            {"asset_id": "AAPL", "quantity": 100, "average_cost": 150.0, "current_price": 175.0},
            {"asset_id": "GOOGL", "quantity": 50, "average_cost": 2500.0, "current_price": 2800.0},
            {"asset_id": "MSFT", "quantity": 75, "average_cost": 300.0, "current_price": 350.0},
            {"asset_id": "TSLA", "quantity": 25, "average_cost": 200.0, "current_price": 250.0},
            {"asset_id": "AMZN", "quantity": 30, "average_cost": 3000.0, "current_price": 3200.0},
            {"asset_id": "NVDA", "quantity": 40, "average_cost": 400.0, "current_price": 500.0},
            {"asset_id": "META", "quantity": 60, "average_cost": 250.0, "current_price": 300.0},
            {"asset_id": "NFLX", "quantity": 35, "average_cost": 400.0, "current_price": 450.0},
            {"asset_id": "AMD", "quantity": 80, "average_cost": 80.0, "current_price": 100.0},
            {"asset_id": "INTC", "quantity": 120, "average_cost": 50.0, "current_price": 55.0}
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
    
    async def _create_market_views(self) -> Dict[str, Any]:
        """Create realistic market views for Black-Litterman"""
        market_views = {
            "views": [
                {
                    "view_id": "tech_bullish",
                    "type": "absolute",
                    "assets": ["AAPL", "GOOGL", "MSFT"],
                    "expected_return": 0.15,
                    "confidence": 0.7,
                    "description": "Tech giants expected to outperform with 15% annual return"
                },
                {
                    "view_id": "tesla_volatile",
                    "type": "absolute",
                    "assets": ["TSLA"],
                    "expected_return": 0.20,
                    "confidence": 0.4,
                    "description": "Tesla expected to be volatile with 20% annual return but low confidence"
                },
                {
                    "view_id": "relative_tech",
                    "type": "relative",
                    "assets": ["NVDA", "AMD"],
                    "expected_return_diff": 0.05,
                    "confidence": 0.6,
                    "description": "NVDA expected to outperform AMD by 5% annually"
                },
                {
                    "view_id": "meta_recovery",
                    "type": "absolute",
                    "assets": ["META"],
                    "expected_return": 0.12,
                    "confidence": 0.5,
                    "description": "Meta expected to recover with 12% annual return"
                },
                {
                    "view_id": "streaming_competition",
                    "type": "relative",
                    "assets": ["NFLX", "SPOT"],
                    "expected_return_diff": -0.03,
                    "confidence": 0.3,
                    "description": "Netflix expected to underperform Spotify by 3% annually"
                }
            ],
            "total_views": 5,
            "absolute_views": 3,
            "relative_views": 2
        }
        
        logger.info(f"✅ Created {market_views['total_views']} market views")
        return market_views
    
    async def _run_black_litterman_optimization(self, portfolio_id: str, market_views: Dict[str, Any],
                                              confidence_level: float, risk_aversion: float) -> Dict[str, Any]:
        """Run Black-Litterman optimization"""
        optimization_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "BLACK_LITTERMAN",
            "risk_aversion": risk_aversion,
            "confidence_level": confidence_level,
            "tau": 0.05,
            "views": market_views["views"],
            "view_uncertainty": 0.1,
            "max_iterations": 1000,
            "convergence_tolerance": 1e-6
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/black-litterman",
            json=optimization_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Black-Litterman optimization completed: {data.get('optimization_id')}")
                return {
                    "success": True,
                    "optimization_id": data.get("optimization_id"),
                    "expected_return": data.get("expected_return"),
                    "expected_volatility": data.get("expected_volatility"),
                    "sharpe_ratio": data.get("sharpe_ratio"),
                    "convergence_achieved": data.get("convergence_achieved"),
                    "iterations": data.get("iterations"),
                    "risk_aversion": risk_aversion,
                    "confidence_level": confidence_level
                }
            else:
                error_text = await response.text()
                raise Exception(f"Black-Litterman optimization failed: HTTP {response.status} - {error_text}")
    
    async def _compare_with_market_equilibrium(self, portfolio_id: str) -> Dict[str, Any]:
        """Compare Black-Litterman with market equilibrium (MPT)"""
        # Run MPT optimization for comparison
        mpt_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "MPT",
            "risk_free_rate": 0.02,
            "max_iterations": 1000,
            "convergence_tolerance": 1e-6
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/mpt",
            json=mpt_data
        ) as response:
            if response.status == 200:
                mpt_result = await response.json()
                
                # Get Black-Litterman result
                async with self.session.get(
                    f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if len(data.get("results", [])) >= 2:
                            bl_result = data["results"][-2]  # Second to last (Black-Litterman)
                            mpt_optimization = data["results"][-1]  # Last (MPT)
                            
                            comparison = {
                                "success": True,
                                "black_litterman": {
                                    "expected_return": bl_result.get("expected_return", 0),
                                    "expected_volatility": bl_result.get("expected_volatility", 0),
                                    "sharpe_ratio": bl_result.get("sharpe_ratio", 0)
                                },
                                "market_equilibrium": {
                                    "expected_return": mpt_optimization.get("expected_return", 0),
                                    "expected_volatility": mpt_optimization.get("expected_volatility", 0),
                                    "sharpe_ratio": mpt_optimization.get("sharpe_ratio", 0)
                                },
                                "differences": {
                                    "return_diff": (bl_result.get("expected_return", 0) - 
                                                  mpt_optimization.get("expected_return", 0)),
                                    "volatility_diff": (bl_result.get("expected_volatility", 0) - 
                                                      mpt_optimization.get("expected_volatility", 0)),
                                    "sharpe_diff": (bl_result.get("sharpe_ratio", 0) - 
                                                  mpt_optimization.get("sharpe_ratio", 0))
                                }
                            }
                            
                            logger.info("✅ Black-Litterman vs Market Equilibrium comparison completed")
                            return comparison
                        else:
                            return {"success": False, "error": "Insufficient optimization results for comparison"}
                    else:
                        return {"success": False, "error": "Failed to get optimization results for comparison"}
            else:
                error_text = await response.text()
                raise Exception(f"MPT optimization failed: HTTP {response.status} - {error_text}")
    
    async def _analyze_view_impact(self, portfolio_id: str, market_views: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the impact of market views on portfolio weights"""
        # Get optimization results
        async with self.session.get(
            f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                if len(data.get("results", [])) >= 2:
                    bl_result = data["results"][-2]  # Black-Litterman
                    mpt_result = data["results"][-1]  # MPT
                    
                    bl_weights = bl_result.get("optimal_weights", {})
                    mpt_weights = mpt_result.get("optimal_weights", {})
                    
                    # Calculate weight differences
                    weight_differences = {}
                    for asset in bl_weights:
                        if asset in mpt_weights:
                            weight_differences[asset] = bl_weights[asset] - mpt_weights[asset]
                    
                    # Analyze view impact
                    impact_analysis = {
                        "success": True,
                        "total_assets": len(weight_differences),
                        "weight_differences": weight_differences,
                        "largest_increases": self._get_largest_changes(weight_differences, "increase"),
                        "largest_decreases": self._get_largest_changes(weight_differences, "decrease"),
                        "view_summary": {
                            "total_views": market_views["total_views"],
                            "absolute_views": market_views["absolute_views"],
                            "relative_views": market_views["relative_views"]
                        }
                    }
                    
                    logger.info("✅ View impact analysis completed")
                    return impact_analysis
                else:
                    return {"success": False, "error": "Insufficient optimization results for view impact analysis"}
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get optimization results: HTTP {response.status} - {error_text}")
    
    def _get_largest_changes(self, weight_differences: Dict[str, float], change_type: str) -> List[Dict[str, Any]]:
        """Get largest weight changes"""
        if change_type == "increase":
            changes = [(asset, diff) for asset, diff in weight_differences.items() if diff > 0]
        else:  # decrease
            changes = [(asset, diff) for asset, diff in weight_differences.items() if diff < 0]
        
        # Sort by absolute value and return top 5
        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        return [{"asset": asset, "change": diff} for asset, diff in changes[:5]]
    
    def _display_results(self, demo_results: Dict[str, Any]):
        """Display demo results in a formatted way"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 BLACK-LITTERMAN DEMO RESULTS")
        logger.info("=" * 60)
        
        # Configuration
        config = demo_results["configuration"]
        logger.info(f"🎯 Confidence Level: {config['confidence_level']}")
        logger.info(f"📈 Risk Aversion: {config['risk_aversion']}")
        logger.info(f"📊 Asset Universe: {len(config['asset_universe'])} assets")
        logger.info(f"📝 Description: {config['description']}")
        
        # Market Views
        if "market_views" in demo_results["results"]:
            views = demo_results["results"]["market_views"]
            logger.info(f"🎯 Market Views: {views['total_views']} total")
            logger.info(f"   • Absolute Views: {views['absolute_views']}")
            logger.info(f"   • Relative Views: {views['relative_views']}")
        
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
        
        # Comparison Results
        if "comparison" in demo_results["results"]:
            comparison = demo_results["results"]["comparison"]
            if comparison.get("success"):
                bl = comparison["black_litterman"]
                mpt = comparison["market_equilibrium"]
                diff = comparison["differences"]
                
                logger.info(f"🔄 Black-Litterman vs Market Equilibrium:")
                logger.info(f"   • Return: {bl['expected_return']:.2%} vs {mpt['expected_return']:.2%} (diff: {diff['return_diff']:+.2%})")
                logger.info(f"   • Volatility: {bl['expected_volatility']:.2%} vs {mpt['expected_volatility']:.2%} (diff: {diff['volatility_diff']:+.2%})")
                logger.info(f"   • Sharpe Ratio: {bl['sharpe_ratio']:.2f} vs {mpt['sharpe_ratio']:.2f} (diff: {diff['sharpe_diff']:+.2f})")
        
        # View Impact Analysis
        if "view_impact" in demo_results["results"]:
            impact = demo_results["results"]["view_impact"]
            if impact.get("success"):
                logger.info(f"📊 View Impact Analysis:")
                logger.info(f"   • Total Assets: {impact['total_assets']}")
                
                if impact.get("largest_increases"):
                    logger.info(f"   • Largest Weight Increases:")
                    for change in impact["largest_increases"][:3]:
                        logger.info(f"     - {change['asset']}: {change['change']:+.2%}")
                
                if impact.get("largest_decreases"):
                    logger.info(f"   • Largest Weight Decreases:")
                    for change in impact["largest_decreases"][:3]:
                        logger.info(f"     - {change['asset']}: {change['change']:+.2%}")
        
        logger.info("=" * 60)
        logger.info("✅ Black-Litterman Demo completed successfully!")
    
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
    parser = argparse.ArgumentParser(description="Black-Litterman Demo")
    parser.add_argument("--confidence-level", type=float, default=0.5,
                       help="Confidence level for market views (0.0-1.0)")
    parser.add_argument("--risk-aversion", type=float, default=3.0,
                       help="Risk aversion parameter")
    parser.add_argument("--portfolio-api-url", default="http://localhost:11180",
                       help="Portfolio API URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with BlackLittermanDemo(args.portfolio_api_url) as demo:
        results = await demo.run_demo(args.confidence_level, args.risk_aversion)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {args.output}")
        
        # Return success/failure for script exit code
        return 0 if not results.get("results", {}).get("error") else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)






















