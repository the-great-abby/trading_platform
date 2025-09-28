#!/usr/bin/env python3
"""
Portfolio Management Demo Runner
Convenient script to run all portfolio management demos
"""
import asyncio
import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoRunner:
    """Portfolio management demo runner"""
    
    def __init__(self, demo_dir: Path):
        self.demo_dir = demo_dir
        self.available_demos = {
            "portfolio-optimization": "portfolio_optimization_demo.py",
            "risk-parity": "risk_parity_demo.py", 
            "black-litterman": "black_litterman_demo.py",
            "complete-system": "complete_system_demo.py"
        }
    
    def list_demos(self):
        """List available demos"""
        logger.info("📋 Available Portfolio Management Demos:")
        logger.info("=" * 50)
        
        for demo_name, script_name in self.available_demos.items():
            script_path = self.demo_dir / script_name
            if script_path.exists():
                logger.info(f"✅ {demo_name}: {script_name}")
            else:
                logger.info(f"❌ {demo_name}: {script_name} (not found)")
        
        logger.info("=" * 50)
        logger.info("Usage: python run_demos.py <demo-name> [options]")
        logger.info("Example: python run_demos.py portfolio-optimization --risk-tolerance AGGRESSIVE")
    
    def run_demo(self, demo_name: str, args: List[str] = None) -> bool:
        """Run a specific demo"""
        if demo_name not in self.available_demos:
            logger.error(f"❌ Unknown demo: {demo_name}")
            logger.info(f"Available demos: {', '.join(self.available_demos.keys())}")
            return False
        
        script_name = self.available_demos[demo_name]
        script_path = self.demo_dir / script_name
        
        if not script_path.exists():
            logger.error(f"❌ Demo script not found: {script_path}")
            return False
        
        # Build command
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        logger.info(f"🚀 Running {demo_name} demo...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            # Run the demo
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.demo_dir)
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            # Return success status
            success = result.returncode == 0
            if success:
                logger.info(f"✅ {demo_name} demo completed successfully")
            else:
                logger.error(f"❌ {demo_name} demo failed with exit code {result.returncode}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error running {demo_name} demo: {e}")
            return False
    
    def run_all_demos(self, args: List[str] = None) -> Dict[str, bool]:
        """Run all available demos"""
        logger.info("🚀 Running all portfolio management demos...")
        logger.info("=" * 60)
        
        results = {}
        total_demos = len(self.available_demos)
        completed_demos = 0
        
        for demo_name in self.available_demos.keys():
            logger.info(f"\n📊 Running {demo_name} demo ({completed_demos + 1}/{total_demos})...")
            
            success = self.run_demo(demo_name, args)
            results[demo_name] = success
            
            if success:
                completed_demos += 1
                logger.info(f"✅ {demo_name} demo completed successfully")
            else:
                logger.error(f"❌ {demo_name} demo failed")
            
            # Add a small delay between demos
            if completed_demos < total_demos:
                logger.info("⏳ Waiting 2 seconds before next demo...")
                import time
                time.sleep(2)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 DEMO RUNNER SUMMARY")
        logger.info("=" * 60)
        
        successful_demos = sum(1 for success in results.values() if success)
        logger.info(f"Total Demos: {total_demos}")
        logger.info(f"Successful: {successful_demos}")
        logger.info(f"Failed: {total_demos - successful_demos}")
        logger.info(f"Success Rate: {successful_demos/total_demos:.1%}")
        
        logger.info("\nDetailed Results:")
        for demo_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"  • {demo_name}: {status}")
        
        return results
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if portfolio services are running
        try:
            import aiohttp
            import asyncio
            
            async def check_services():
                services = [
                    ("Portfolio Service", "http://localhost:11180/health"),
                    ("Risk Management Service", "http://localhost:11181/health")
                ]
                
                async with aiohttp.ClientSession() as session:
                    for service_name, url in services:
                        try:
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                                if response.status == 200:
                                    logger.info(f"✅ {service_name}: Running")
                                else:
                                    logger.warning(f"⚠️ {service_name}: HTTP {response.status}")
                                    return False
                        except Exception as e:
                            logger.error(f"❌ {service_name}: {e}")
                            return False
                
                return True
            
            # Run the async check
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(check_services())
            loop.close()
            
            if result:
                logger.info("✅ All prerequisites met!")
                return True
            else:
                logger.error("❌ Prerequisites not met. Please ensure portfolio services are running.")
                logger.info("💡 To start services:")
                logger.info("   kubectl port-forward -n trading-system service/enhanced-portfolio-service 11180:80 &")
                logger.info("   kubectl port-forward -n trading-system service/enhanced-risk-management-service 11181:80 &")
                return False
                
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            logger.info("💡 Install dependencies: pip install -r requirements.txt")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking prerequisites: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Portfolio Management Demo Runner")
    parser.add_argument("demo", nargs="?", help="Demo name to run (or 'list' to list demos)")
    parser.add_argument("--all", action="store_true", help="Run all demos")
    parser.add_argument("--check", action="store_true", help="Check prerequisites only")
    parser.add_argument("--output-dir", help="Directory to save demo outputs")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    # Demo-specific arguments
    parser.add_argument("--risk-tolerance", choices=["CONSERVATIVE", "MODERATE", "AGGRESSIVE"],
                       help="Risk tolerance for optimization demos")
    parser.add_argument("--optimization-type", choices=["MPT", "BLACK_LITTERMAN", "RISK_PARITY"],
                       help="Optimization type")
    parser.add_argument("--confidence-level", type=float, help="Confidence level for Black-Litterman")
    parser.add_argument("--risk-aversion", type=float, help="Risk aversion parameter")
    parser.add_argument("--risk-budget-method", choices=["equal", "custom"],
                       help="Risk budget method for risk parity")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get demo directory
    demo_dir = Path(__file__).parent
    runner = DemoRunner(demo_dir)
    
    # Check prerequisites
    if not runner.check_prerequisites():
        sys.exit(1)
    
    if args.check:
        logger.info("✅ Prerequisites check completed")
        sys.exit(0)
    
    # List demos
    if args.demo == "list" or (not args.demo and not args.all):
        runner.list_demos()
        sys.exit(0)
    
    # Prepare demo arguments
    demo_args = []
    if args.output_dir:
        demo_args.extend(["--output", str(Path(args.output_dir) / f"{args.demo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")])
    if args.verbose:
        demo_args.append("--verbose")
    if args.risk_tolerance:
        demo_args.extend(["--risk-tolerance", args.risk_tolerance])
    if args.optimization_type:
        demo_args.extend(["--optimization-type", args.optimization_type])
    if args.confidence_level:
        demo_args.extend(["--confidence-level", str(args.confidence_level)])
    if args.risk_aversion:
        demo_args.extend(["--risk-aversion", str(args.risk_aversion)])
    if args.risk_budget_method:
        demo_args.extend(["--risk-budget-method", args.risk_budget_method])
    
    # Run demos
    if args.all:
        results = runner.run_all_demos(demo_args)
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        sys.exit(0 if success_count == total_count else 1)
    else:
        success = runner.run_demo(args.demo, demo_args)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()



