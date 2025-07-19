"""
Backtest API Client for Space Trading Station
Fetches backtest data from the Backtest Results API
"""

import httpx
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class BacktestAPIClient:
    """Client for fetching backtest data from the API"""
    
    def __init__(self, base_url: str = None):
        # Default to Kubernetes ingress if no URL provided
        if base_url is None:
            # Try to detect if we're in Kubernetes or local development
            if os.getenv('KUBERNETES_SERVICE_HOST'):
                # Running in Kubernetes
                self.base_url = "http://trading-ingress.trading-system.svc.cluster.local/api/v1/backtest"
            else:
                # Local development - use port forwarding or localhost
                self.base_url = "http://localhost:10001"
        else:
            self.base_url = base_url
            
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def list_backtest_runs(
        self, 
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List backtest runs with optional filtering"""
        try:
            params = {"limit": limit}
            if strategy_name:
                params["strategy_name"] = strategy_name
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            
            response = await self.client.get(f"{self.base_url}/api/v1/runs", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
            else:
                logger.error(f"API returned error: {data}")
                return []
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    async def get_run_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific backtest run"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/runs/{run_id}")
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data")
            else:
                logger.error(f"API returned error: {data}")
                return None
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def get_run_trades(
        self, 
        run_id: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get trades for a specific backtest run"""
        try:
            params = {"limit": limit}
            response = await self.client.get(
                f"{self.base_url}/api/v1/runs/{run_id}/trades", 
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
            else:
                logger.error(f"API returned error: {data}")
                return []
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    async def get_run_equity_curve(
        self, 
        run_id: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get equity curve data for a specific backtest run"""
        try:
            params = {"limit": limit}
            response = await self.client.get(
                f"{self.base_url}/api/v1/runs/{run_id}/equity", 
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
            else:
                logger.error(f"API returned error: {data}")
                return []
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    async def compare_strategies(self) -> Dict[str, Any]:
        """Compare performance of different strategies"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/compare")
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data
            else:
                logger.error(f"API returned error: {data}")
                return {"success": False, "data": [], "summary": {}}
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return {"success": False, "data": [], "summary": {}}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return {"success": False, "data": [], "summary": {}}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "data": [], "summary": {}}
    
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Get list of all strategies that have been tested"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/strategies")
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
            else:
                logger.error(f"API returned error: {data}")
                return []
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics about backtest results"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/stats")
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data.get("data", {})
            else:
                logger.error(f"API returned error: {data}")
                return {}
                
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return {}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}


# Global client instance
backtest_client = BacktestAPIClient()


async def demo_backtest_api():
    """Demo function to show how to use the backtest API client"""
    async with BacktestAPIClient() as client:
        print("🚀 Space Trading Station - Backtest API Demo")
        print("=" * 50)
        
        # 1. List backtest runs
        print("\n📊 Listing recent backtest runs...")
        runs = await client.list_backtest_runs(limit=5)
        
        if runs:
            print(f"Found {len(runs)} backtest runs:")
            for run in runs:
                print(f"  • {run.get('strategy_name', 'Unknown')} - "
                      f"Return: {run.get('total_return_pct', 0):.2f}% - "
                      f"Trades: {run.get('total_trades', 0)}")
            
            # 2. Get details for the first run
            first_run = runs[0]
            run_id = first_run.get('run_id')
            
            print(f"\n📈 Getting details for run: {run_id}")
            run_details = await client.get_run_details(run_id)
            
            if run_details:
                print(f"  Strategy: {run_details.get('strategy_name')}")
                print(f"  Date Range: {run_details.get('start_date')} to {run_details.get('end_date')}")
                print(f"  Total Return: {run_details.get('total_return_pct', 0):.2f}%")
                print(f"  Sharpe Ratio: {run_details.get('sharpe_ratio', 0):.2f}")
                print(f"  Win Rate: {run_details.get('win_rate', 0)*100:.1f}%")
            
            # 3. Get trades for the first run
            print(f"\n💹 Getting trades for run: {run_id}")
            trades = await client.get_run_trades(run_id, limit=10)
            
            if trades:
                print(f"Found {len(trades)} trades (showing first 10):")
                for trade in trades[:10]:
                    print(f"  • {trade.get('symbol', 'Unknown')} - "
                          f"{trade.get('action', 'Unknown')} - "
                          f"P&L: ${trade.get('pnl', 0):.2f}")
        
        # 4. Compare strategies
        print("\n🏆 Strategy Comparison:")
        comparison = await client.compare_strategies()
        
        if comparison.get("success") and comparison.get("data"):
            strategies = comparison["data"]
            for i, strategy in enumerate(strategies[:5], 1):
                print(f"  {i}. {strategy.get('strategy_name', 'Unknown')} - "
                      f"Return: {strategy.get('total_return_pct', 0):.2f}%")
        
        # 5. Get overall stats
        print("\n📊 Overall Statistics:")
        stats = await client.get_stats()
        
        if stats:
            print(f"  Total Runs: {stats.get('total_runs', 0)}")
            print(f"  Total Strategies: {stats.get('total_strategies', 0)}")
            if stats.get('performance_summary'):
                perf = stats['performance_summary']
                print(f"  Average Return: {perf.get('average_return', 0):.2f}%")
                print(f"  Best Return: {perf.get('best_return', 0):.2f}%")
                print(f"  Total Trades: {perf.get('total_trades', 0)}")


if __name__ == "__main__":
    """Run the demo"""
    asyncio.run(demo_backtest_api()) 