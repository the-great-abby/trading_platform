#!/usr/bin/env python3
"""
Risk Parity Demo
Demonstrates Risk Parity optimization with equal risk contribution across assets
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

class RiskParityDemo:
    """Risk Parity optimization demonstration"""
    
    def __init__(self, portfolio_api_url: str = "http://localhost:11180"):
        self.portfolio_api_url = portfolio_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Demo configuration
        self.demo_assets = [
            "SPY", "QQQ", "IWM", "EFA", "VWO", "TLT", "IEF", "LQD",
            "GLD", "SLV", "VNQ", "IYR", "DJP", "USO", "UNG"
        ]
        self.demo_user_id = "demo-user-002"
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
    
    async def run_demo(self, risk_budget_method: str = "equal") -> Dict[str, Any]:
        """Run the complete risk parity demo"""
        logger.info("🚀 Starting Risk Parity Demo")
        logger.info("=" * 60)
        
        demo_results = {
            "demo_name": "Risk Parity Demo",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "risk_budget_method": risk_budget_method,
                "asset_universe": self.demo_assets,
                "description": "Risk Parity optimization with equal risk contribution"
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
            
            # Step 3: Run risk parity optimization
            logger.info("🎯 Step 3: Running risk parity optimization...")
            optimization_result = await self._run_risk_parity_optimization(portfolio_id, risk_budget_method)
            demo_results["results"]["optimization"] = optimization_result
            
            # Step 4: Analyze risk contributions
            logger.info("📊 Step 4: Analyzing risk contributions...")
            risk_analysis = await self._analyze_risk_contributions(portfolio_id)
            demo_results["results"]["risk_analysis"] = risk_analysis
            
            # Step 5: Compare with traditional optimization
            logger.info("🔄 Step 5: Comparing with traditional MPT optimization...")
            comparison_result = await self._compare_with_mpt(portfolio_id)
            demo_results["results"]["comparison"] = comparison_result
            
            # Step 6: Display results
            self._display_results(demo_results)
            
            # Step 7: Clean up
            logger.info("🧹 Step 7: Cleaning up demo portfolio...")
            await self._cleanup_demo_portfolio(portfolio_id)
            demo_results["results"]["cleanup"] = {"success": True}
            
            logger.info("✅ Risk Parity Demo completed successfully!")
            return demo_results
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            demo_results["results"]["error"] = {"message": str(e)}
            return demo_results
    
    async def _create_demo_portfolio(self) -> str:
        """Create demo portfolio for risk parity"""
        portfolio_data = {
            "name": "Demo Portfolio - Risk Parity",
            "owner_id": self.demo_user_id,
            "risk_tolerance": "MODERATE",
            "base_currency": "USD",
            "rebalancing_frequency": "QUARTERLY",
            "max_single_asset_weight": 0.15,  # Lower for diversification
            "max_sector_weight": 0.30,
            "long_only": True,
            "description": "Demo portfolio for risk parity optimization demonstration"
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
        # Create diversified demo positions across asset classes
        demo_positions = [
            # Equities
            {"asset_id": "SPY", "quantity": 100, "average_cost": 400.0, "current_price": 420.0},
            {"asset_id": "QQQ", "quantity": 50, "average_cost": 350.0, "current_price": 380.0},
            {"asset_id": "IWM", "quantity": 75, "average_cost": 200.0, "current_price": 210.0},
            {"asset_id": "EFA", "quantity": 80, "average_cost": 70.0, "current_price": 75.0},
            {"asset_id": "VWO", "quantity": 60, "average_cost": 40.0, "current_price": 42.0},
            
            # Bonds
            {"asset_id": "TLT", "quantity": 40, "average_cost": 140.0, "current_price": 145.0},
            {"asset_id": "IEF", "quantity": 60, "average_cost": 110.0, "current_price": 112.0},
            {"asset_id": "LQD", "quantity": 50, "average_cost": 120.0, "current_price": 125.0},
            
            # Commodities
            {"asset_id": "GLD", "quantity": 30, "average_cost": 170.0, "current_price": 175.0},
            {"asset_id": "SLV", "quantity": 100, "average_cost": 20.0, "current_price": 22.0},
            
            # Real Estate
            {"asset_id": "VNQ", "quantity": 40, "average_cost": 80.0, "current_price": 85.0},
            {"asset_id": "IYR", "quantity": 35, "average_cost": 90.0, "current_price": 95.0},
            
            # Alternative Assets
            {"asset_id": "DJP", "quantity": 25, "average_cost": 35.0, "current_price": 37.0},
            {"asset_id": "USO", "quantity": 50, "average_cost": 60.0, "current_price": 65.0},
            {"asset_id": "UNG", "quantity": 40, "average_cost": 15.0, "current_price": 16.0}
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
    
    async def _run_risk_parity_optimization(self, portfolio_id: str, risk_budget_method: str) -> Dict[str, Any]:
        """Run risk parity optimization"""
        optimization_data = {
            "portfolio_id": portfolio_id,
            "optimization_type": "RISK_PARITY",
            "risk_budget_method": risk_budget_method,
            "convergence_tolerance": 1e-6,
            "max_iterations": 1000,
            "enable_short_selling": False,
            "transaction_cost_rate": 0.001
        }
        
        async with self.session.post(
            f"{self.portfolio_api_url}/api/v1/optimization/risk-parity",
            json=optimization_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Risk Parity optimization completed: {data.get('optimization_id')}")
                return {
                    "success": True,
                    "optimization_id": data.get("optimization_id"),
                    "expected_return": data.get("expected_return"),
                    "expected_volatility": data.get("expected_volatility"),
                    "sharpe_ratio": data.get("sharpe_ratio"),
                    "convergence_achieved": data.get("convergence_achieved"),
                    "iterations": data.get("iterations"),
                    "risk_budget_method": risk_budget_method
                }
            else:
                error_text = await response.text()
                raise Exception(f"Risk Parity optimization failed: HTTP {response.status} - {error_text}")
    
    async def _analyze_risk_contributions(self, portfolio_id: str) -> Dict[str, Any]:
        """Analyze risk contributions"""
        # Get optimization results
        async with self.session.get(
            f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get("results"):
                    latest_opt = data["results"][-1]
                    risk_contributions = latest_opt.get("risk_contributions", {})
                    
                    # Analyze risk contributions
                    analysis = {
                        "success": True,
                        "total_assets": len(risk_contributions),
                        "risk_contributions": risk_contributions,
                        "risk_contribution_stats": self._calculate_risk_stats(risk_contributions)
                    }
                    
                    logger.info("✅ Risk contributions analyzed")
                    return analysis
                else:
                    return {"success": False, "error": "No optimization results found"}
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get optimization results: HTTP {response.status} - {error_text}")
    
    def _calculate_risk_stats(self, risk_contributions: Dict[str, float]) -> Dict[str, Any]:
        """Calculate risk contribution statistics"""
        if not risk_contributions:
            return {}
        
        values = list(risk_contributions.values())
        
        return {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "range": np.max(values) - np.min(values),
            "coefficient_of_variation": np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
        }
    
    async def _compare_with_mpt(self, portfolio_id: str) -> Dict[str, Any]:
        """Compare risk parity with traditional MPT optimization"""
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
                
                # Get risk parity result
                async with self.session.get(
                    f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if len(data.get("results", [])) >= 2:
                            risk_parity_result = data["results"][-2]  # Second to last (risk parity)
                            mpt_optimization = data["results"][-1]    # Last (MPT)
                            
                            comparison = {
                                "success": True,
                                "risk_parity": {
                                    "expected_return": risk_parity_result.get("expected_return", 0),
                                    "expected_volatility": risk_parity_result.get("expected_volatility", 0),
                                    "sharpe_ratio": risk_parity_result.get("sharpe_ratio", 0)
                                },
                                "mpt": {
                                    "expected_return": mpt_optimization.get("expected_return", 0),
                                    "expected_volatility": mpt_optimization.get("expected_volatility", 0),
                                    "sharpe_ratio": mpt_optimization.get("sharpe_ratio", 0)
                                },
                                "differences": {
                                    "return_diff": (risk_parity_result.get("expected_return", 0) - 
                                                  mpt_optimization.get("expected_return", 0)),
                                    "volatility_diff": (risk_parity_result.get("expected_volatility", 0) - 
                                                      mpt_optimization.get("expected_volatility", 0)),
                                    "sharpe_diff": (risk_parity_result.get("sharpe_ratio", 0) - 
                                                  mpt_optimization.get("sharpe_ratio", 0))
                                }
                            }
                            
                            logger.info("✅ Risk Parity vs MPT comparison completed")
                            return comparison
                        else:
                            return {"success": False, "error": "Insufficient optimization results for comparison"}
                    else:
                        return {"success": False, "error": "Failed to get optimization results for comparison"}
            else:
                error_text = await response.text()
                raise Exception(f"MPT optimization failed: HTTP {response.status} - {error_text}")
    
    def _display_results(self, demo_results: Dict[str, Any]):
        """Display demo results in a formatted way"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 RISK PARITY DEMO RESULTS")
        logger.info("=" * 60)
        
        # Configuration
        config = demo_results["configuration"]
        logger.info(f"🎯 Risk Budget Method: {config['risk_budget_method']}")
        logger.info(f"📈 Asset Universe: {len(config['asset_universe'])} assets")
        logger.info(f"📝 Description: {config['description']}")
        
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
        
        # Risk Analysis
        if "risk_analysis" in demo_results["results"]:
            risk_analysis = demo_results["results"]["risk_analysis"]
            if risk_analysis.get("success"):
                stats = risk_analysis.get("risk_contribution_stats", {})
                logger.info(f"📊 Risk Contribution Analysis:")
                logger.info(f"   • Mean Risk Contribution: {stats.get('mean', 0):.2%}")
                logger.info(f"   • Standard Deviation: {stats.get('std', 0):.2%}")
                logger.info(f"   • Range: {stats.get('range', 0):.2%}")
                logger.info(f"   • Coefficient of Variation: {stats.get('coefficient_of_variation', 0):.2f}")
        
        # Comparison Results
        if "comparison" in demo_results["results"]:
            comparison = demo_results["results"]["comparison"]
            if comparison.get("success"):
                rp = comparison["risk_parity"]
                mpt = comparison["mpt"]
                diff = comparison["differences"]
                
                logger.info(f"🔄 Risk Parity vs MPT Comparison:")
                logger.info(f"   • Return: {rp['expected_return']:.2%} vs {mpt['expected_return']:.2%} (diff: {diff['return_diff']:+.2%})")
                logger.info(f"   • Volatility: {rp['expected_volatility']:.2%} vs {mpt['expected_volatility']:.2%} (diff: {diff['volatility_diff']:+.2%})")
                logger.info(f"   • Sharpe Ratio: {rp['sharpe_ratio']:.2f} vs {mpt['sharpe_ratio']:.2f} (diff: {diff['sharpe_diff']:+.2f})")
        
        logger.info("=" * 60)
        logger.info("✅ Risk Parity Demo completed successfully!")
    
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
    parser = argparse.ArgumentParser(description="Risk Parity Demo")
    parser.add_argument("--risk-budget-method", choices=["equal", "custom"], 
                       default="equal", help="Risk budget method")
    parser.add_argument("--portfolio-api-url", default="http://localhost:11180", 
                       help="Portfolio API URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with RiskParityDemo(args.portfolio_api_url) as demo:
        results = await demo.run_demo(args.risk_budget_method)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {args.output}")
        
        # Return success/failure for script exit code
        return 0 if not results.get("results", {}).get("error") else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
























