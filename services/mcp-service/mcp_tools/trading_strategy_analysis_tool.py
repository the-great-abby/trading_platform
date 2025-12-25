"""
Trading Strategy Analysis Tool for MCP Service
Analyzes trading strategies by integrating with existing service APIs
"""

import asyncio
import aiohttp
import logging
import os
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class TradingStrategyAnalysisTool:
    """Analyzes trading strategies using existing service APIs"""
    
    def __init__(self):
        # Service URLs from environment or defaults
        self.backtest_api_url = os.getenv(
            'BACKTEST_API_URL', 
            'http://backtest-api.trading-system.svc.cluster.local:10001'
        )
        self.portfolio_api_url = os.getenv(
            'PORTFOLIO_API_URL',
            'http://portfolio-service.trading-system.svc.cluster.local:8000'
        )
        self.analytics_api_url = os.getenv(
            'ANALYTICS_API_URL',
            'http://analytics-service.trading-system.svc.cluster.local:8000'
        )
        self.live_trading_api_url = os.getenv(
            'LIVE_TRADING_API_URL',
            'http://live-trading-service.trading-system.svc.cluster.local:8000'
        )
        
        # Database configuration - postgres-infra namespace
        self.db_host = os.getenv('DB_HOST', 'postgres-timescale-external.postgres-infra.svc.cluster.local')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'trading_bot')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'postgres')
        
        # Configuration file paths - try multiple locations
        self.config_search_paths = [
            '/app/config/live_trading_strategies.yaml',
            '/config/live_trading_strategies.yaml',
            '../config/live_trading_strategies.yaml',
            '/Users/abby/code/trading/config/live_trading_strategies.yaml'  # Fallback for local dev
        ]
        
    def _get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                cursor_factory=RealDictCursor
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    async def _call_api(self, url: str, method: str = 'GET', data: Dict = None, timeout: int = 30) -> Dict:
        """Helper to call external APIs"""
        try:
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.warning(f"API call to {url} failed with status {response.status}")
                            return {"error": f"HTTP {response.status}", "url": url}
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.warning(f"API call to {url} failed with status {response.status}")
                            return {"error": f"HTTP {response.status}", "url": url}
        except asyncio.TimeoutError:
            logger.error(f"API call to {url} timed out")
            return {"error": "timeout", "url": url}
        except Exception as e:
            logger.error(f"API call to {url} failed: {e}")
            return {"error": str(e), "url": url}
    
    async def get_active_strategies(self) -> Dict[str, Any]:
        """Get currently active trading strategies from configuration"""
        try:
            # Try multiple config file locations
            config_path = None
            for path in self.config_search_paths:
                if os.path.exists(path):
                    config_path = path
                    logger.info(f"Found config file at: {path}")
                    break
            
            if not config_path:
                return {
                    "success": False,
                    "error": f"Config file not found. Searched: {', '.join(self.config_search_paths)}",
                    "active_strategies": {},
                    "total_active": 0
                }
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            active_strategies = {}
            if 'strategies' in config:
                for strategy_name, strategy_config in config['strategies'].items():
                    if strategy_config.get('enabled', False):
                        active_strategies[strategy_name] = {
                            'name': strategy_name,
                            'enabled': True,
                            'config': strategy_config
                        }
            
            return {
                "success": True,
                "active_strategies": active_strategies,
                "total_active": len(active_strategies),
                "portfolio_config": {
                    "initial_capital": config.get('portfolio', {}).get('initial_capital', 0),
                    "max_daily_loss": config.get('portfolio', {}).get('max_daily_loss', 0),
                    "max_daily_trades": config.get('portfolio', {}).get('max_daily_trades', 0)
                }
            }
        except Exception as e:
            logger.error(f"Error getting active strategies: {e}")
            return {
                "success": False,
                "error": str(e),
                "active_strategies": {},
                "total_active": 0
            }
    
    async def get_strategy_backtest_performance(self, limit: int = 50) -> Dict[str, Any]:
        """Get strategy performance from backtest API"""
        try:
            url = f"{self.backtest_api_url}/api/v1/runs?limit={limit}"
            data = await self._call_api(url)
            
            if "error" in data:
                return {"success": False, "error": data["error"], "strategies": {}}
            
            # Aggregate by strategy
            strategy_performance = {}
            
            if data.get("success") and data.get("data"):
                for run in data["data"]:
                    strategy = run.get("strategy_name", "Unknown")
                    
                    if strategy not in strategy_performance:
                        strategy_performance[strategy] = {
                            "runs": 0,
                            "total_return": 0,
                            "avg_return": 0,
                            "avg_sharpe": 0,
                            "avg_max_drawdown": 0,
                            "total_trades": 0,
                            "avg_win_rate": 0,
                            "best_run": None,
                            "worst_run": None
                        }
                    
                    perf = strategy_performance[strategy]
                    perf["runs"] += 1
                    
                    ret = run.get("total_return_pct", 0)
                    perf["total_return"] += ret
                    
                    if perf["best_run"] is None or ret > perf["best_run"]["return"]:
                        perf["best_run"] = {"return": ret, "run_id": run.get("run_id")}
                    
                    if perf["worst_run"] is None or ret < perf["worst_run"]["return"]:
                        perf["worst_run"] = {"return": ret, "run_id": run.get("run_id")}
                    
                    perf["avg_sharpe"] += run.get("sharpe_ratio", 0)
                    perf["avg_max_drawdown"] += run.get("max_drawdown_pct", 0)
                    perf["total_trades"] += run.get("total_trades", 0)
                    perf["avg_win_rate"] += run.get("win_rate", 0)
                
                # Calculate averages
                for strategy, perf in strategy_performance.items():
                    if perf["runs"] > 0:
                        perf["avg_return"] = perf["total_return"] / perf["runs"]
                        perf["avg_sharpe"] = perf["avg_sharpe"] / perf["runs"]
                        perf["avg_max_drawdown"] = perf["avg_max_drawdown"] / perf["runs"]
                        perf["avg_win_rate"] = perf["avg_win_rate"] / perf["runs"]
            
            return {
                "success": True,
                "strategies": strategy_performance,
                "total_strategies": len(strategy_performance),
                "source": "backtest-api"
            }
        except Exception as e:
            logger.error(f"Error getting backtest performance: {e}")
            return {"success": False, "error": str(e), "strategies": {}}
    
    async def get_live_trading_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get live trading performance from database"""
        conn = self._get_db_connection()
        if not conn:
            return {"success": False, "error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            
            # First check if there are ANY trades in the specified period
            check_query = """
                SELECT COUNT(*) as count, MAX(timestamp) as latest
                FROM trades
                WHERE timestamp >= NOW() - INTERVAL '%s days' AND strategy IS NOT NULL
            """
            cursor.execute(check_query, (days,))
            check_result = cursor.fetchone()
            
            # If no trades in period, get all available trades
            if check_result['count'] == 0:
                logger.info(f"No trades found in last {days} days. Querying all available trades.")
                query = """
                    SELECT 
                        strategy,
                        COUNT(*) as trade_count,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        AVG(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as avg_win,
                        AVG(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as avg_loss,
                        MIN(timestamp) as first_trade,
                        MAX(timestamp) as last_trade
                    FROM trades
                    WHERE strategy IS NOT NULL
                    GROUP BY strategy
                    ORDER BY total_pnl DESC
                """
                cursor.execute(query)
                actual_period = "all_time"
            else:
                # Get trades from last N days
                query = """
                    SELECT 
                        strategy,
                        COUNT(*) as trade_count,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        AVG(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as avg_win,
                        AVG(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as avg_loss,
                        MIN(timestamp) as first_trade,
                        MAX(timestamp) as last_trade
                    FROM trades
                    WHERE 
                        timestamp >= NOW() - INTERVAL '%s days'
                        AND strategy IS NOT NULL
                    GROUP BY strategy
                    ORDER BY total_pnl DESC
                """
                cursor.execute(query, (days,))
                actual_period = f"{days}_days"
            
            results = cursor.fetchall()
            
            strategy_performance = {}
            for row in results:
                strategy = row['strategy']
                trade_count = row['trade_count']
                winning_trades = row['winning_trades']
                
                win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
                profit_factor = abs(row['avg_win'] / row['avg_loss']) if row['avg_loss'] != 0 else 0
                
                strategy_performance[strategy] = {
                    "trade_count": trade_count,
                    "winning_trades": winning_trades,
                    "losing_trades": trade_count - winning_trades,
                    "win_rate": round(win_rate, 2),
                    "total_pnl": float(row['total_pnl']) if row['total_pnl'] else 0,
                    "avg_pnl": float(row['avg_pnl']) if row['avg_pnl'] else 0,
                    "best_trade": float(row['best_trade']) if row['best_trade'] else 0,
                    "worst_trade": float(row['worst_trade']) if row['worst_trade'] else 0,
                    "profit_factor": round(profit_factor, 2),
                    "avg_win": float(row['avg_win']) if row['avg_win'] else 0,
                    "avg_loss": float(row['avg_loss']) if row['avg_loss'] else 0,
                    "first_trade": row['first_trade'].isoformat() if row.get('first_trade') else None,
                    "last_trade": row['last_trade'].isoformat() if row.get('last_trade') else None
                }
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "strategies": strategy_performance,
                "total_strategies": len(strategy_performance),
                "period_requested_days": days,
                "period_actual": actual_period,
                "note": f"No trades in last {days} days. Showing all available trades." if actual_period == "all_time" else f"Showing trades from last {days} days",
                "source": "database-trades"
            }
        except Exception as e:
            logger.error(f"Error getting live trading performance: {e}")
            if conn:
                conn.close()
            return {"success": False, "error": str(e), "strategies": {}}
    
    async def get_portfolio_analytics(self) -> Dict[str, Any]:
        """Get portfolio-level analytics"""
        try:
            # Get risk analytics from analytics service
            risk_url = f"{self.analytics_api_url}/analytics/risk?period=1m"
            risk_data = await self._call_api(risk_url)
            
            # Get returns analytics
            returns_url = f"{self.analytics_api_url}/analytics/returns?period=1m"
            returns_data = await self._call_api(returns_url)
            
            # Get trade analytics
            trades_url = f"{self.analytics_api_url}/analytics/trades?period=1m"
            trades_data = await self._call_api(trades_url)
            
            return {
                "success": True,
                "risk_metrics": risk_data if "error" not in risk_data else None,
                "returns_metrics": returns_data if "error" not in returns_data else None,
                "trade_metrics": trades_data if "error" not in trades_data else None,
                "source": "analytics-api"
            }
        except Exception as e:
            logger.error(f"Error getting portfolio analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_positions(self) -> Dict[str, Any]:
        """Get current open positions from database"""
        conn = self._get_db_connection()
        if not conn:
            return {"success": False, "error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            
            # Query live_positions table for active positions
            query = """
                SELECT 
                    strategy,
                    symbol,
                    quantity,
                    average_price,
                    current_price,
                    unrealized_pnl,
                    opened_at
                FROM live_positions
                WHERE status = 'OPEN'
                ORDER BY strategy, opened_at DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Group by strategy
            positions_by_strategy = {}
            total_unrealized_pnl = 0
            
            for row in results:
                strategy = row['strategy'] or 'Unknown'
                
                if strategy not in positions_by_strategy:
                    positions_by_strategy[strategy] = {
                        "positions": [],
                        "position_count": 0,
                        "total_unrealized_pnl": 0
                    }
                
                unrealized_pnl = float(row['unrealized_pnl']) if row['unrealized_pnl'] else 0
                
                position = {
                    "symbol": row['symbol'],
                    "quantity": int(row['quantity']),
                    "average_price": float(row['average_price']),
                    "current_price": float(row['current_price']) if row['current_price'] else float(row['average_price']),
                    "unrealized_pnl": unrealized_pnl,
                    "opened_at": row['opened_at'].isoformat() if row['opened_at'] else None
                }
                
                positions_by_strategy[strategy]["positions"].append(position)
                positions_by_strategy[strategy]["position_count"] += 1
                positions_by_strategy[strategy]["total_unrealized_pnl"] += unrealized_pnl
                total_unrealized_pnl += unrealized_pnl
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "positions_by_strategy": positions_by_strategy,
                "total_open_positions": sum(s["position_count"] for s in positions_by_strategy.values()),
                "total_unrealized_pnl": total_unrealized_pnl,
                "strategies_with_positions": len(positions_by_strategy),
                "source": "database-live_positions"
            }
        except Exception as e:
            logger.error(f"Error getting current positions: {e}")
            if conn:
                conn.close()
            return {"success": False, "error": str(e)}
    
    async def get_comprehensive_strategy_analysis(self) -> Dict[str, Any]:
        """Get comprehensive analysis of all strategies"""
        try:
            # Run all queries in parallel
            results = await asyncio.gather(
                self.get_active_strategies(),
                self.get_strategy_backtest_performance(),
                self.get_live_trading_performance(),
                self.get_portfolio_analytics(),
                self.get_current_positions(),
                return_exceptions=True
            )
            
            active_strategies = results[0] if not isinstance(results[0], Exception) else {}
            backtest_performance = results[1] if not isinstance(results[1], Exception) else {}
            live_performance = results[2] if not isinstance(results[2], Exception) else {}
            portfolio_analytics = results[3] if not isinstance(results[3], Exception) else {}
            current_positions = results[4] if not isinstance(results[4], Exception) else {}
            
            # Combine all data for comprehensive view
            combined_strategies = {}
            
            # Start with active strategies
            if active_strategies.get("success"):
                for strategy_name in active_strategies.get("active_strategies", {}):
                    combined_strategies[strategy_name] = {
                        "status": "active",
                        "config": active_strategies["active_strategies"][strategy_name].get("config", {}),
                        "backtest_performance": None,
                        "live_performance": None,
                        "current_positions": None
                    }
            
            # Add backtest performance
            if backtest_performance.get("success"):
                for strategy_name, perf in backtest_performance.get("strategies", {}).items():
                    if strategy_name not in combined_strategies:
                        combined_strategies[strategy_name] = {
                            "status": "inactive",
                            "config": {},
                            "backtest_performance": perf,
                            "live_performance": None,
                            "current_positions": None
                        }
                    else:
                        combined_strategies[strategy_name]["backtest_performance"] = perf
            
            # Add live performance
            if live_performance.get("success"):
                for strategy_name, perf in live_performance.get("strategies", {}).items():
                    if strategy_name not in combined_strategies:
                        combined_strategies[strategy_name] = {
                            "status": "unknown",
                            "config": {},
                            "backtest_performance": None,
                            "live_performance": perf,
                            "current_positions": None
                        }
                    else:
                        combined_strategies[strategy_name]["live_performance"] = perf
            
            # Add current positions
            if current_positions.get("success"):
                for strategy_name, positions in current_positions.get("positions_by_strategy", {}).items():
                    if strategy_name in combined_strategies:
                        combined_strategies[strategy_name]["current_positions"] = positions
            
            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_strategies": len(combined_strategies),
                    "active_strategies": len([s for s in combined_strategies.values() if s["status"] == "active"]),
                    "total_open_positions": current_positions.get("total_open_positions", 0) if current_positions else 0,
                    "total_unrealized_pnl": current_positions.get("total_unrealized_pnl", 0) if current_positions else 0,
                    "portfolio_capital": active_strategies.get("portfolio_config", {}).get("initial_capital", 0) if active_strategies else 0
                },
                "strategies": combined_strategies,
                "portfolio_analytics": portfolio_analytics,
                "data_sources": {
                    "active_strategies": active_strategies.get("success", False),
                    "backtest_performance": backtest_performance.get("success", False),
                    "live_performance": live_performance.get("success", False),
                    "portfolio_analytics": portfolio_analytics.get("success", False),
                    "current_positions": current_positions.get("success", False)
                }
            }
        except Exception as e:
            logger.error(f"Error in comprehensive strategy analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_strategy_comparison(self, strategies: List[str] = None) -> Dict[str, Any]:
        """Compare multiple strategies side-by-side"""
        try:
            # Get comprehensive data first
            comprehensive = await self.get_comprehensive_strategy_analysis()
            
            if not comprehensive.get("success"):
                return comprehensive
            
            all_strategies = comprehensive.get("strategies", {})
            
            # Filter to requested strategies if specified
            if strategies:
                all_strategies = {k: v for k, v in all_strategies.items() if k in strategies}
            
            # Build comparison table
            comparison = []
            for strategy_name, strategy_data in all_strategies.items():
                backtest = strategy_data.get("backtest_performance", {})
                live = strategy_data.get("live_performance", {})
                positions = strategy_data.get("current_positions", {})
                
                comparison.append({
                    "strategy": strategy_name,
                    "status": strategy_data.get("status"),
                    "backtest": {
                        "avg_return": backtest.get("avg_return", 0),
                        "avg_sharpe": backtest.get("avg_sharpe", 0),
                        "avg_win_rate": backtest.get("avg_win_rate", 0),
                        "total_runs": backtest.get("runs", 0)
                    },
                    "live": {
                        "total_pnl": live.get("total_pnl", 0),
                        "win_rate": live.get("win_rate", 0),
                        "profit_factor": live.get("profit_factor", 0),
                        "trade_count": live.get("trade_count", 0)
                    },
                    "positions": {
                        "open_count": positions.get("position_count", 0) if positions else 0,
                        "unrealized_pnl": positions.get("total_unrealized_pnl", 0) if positions else 0
                    }
                })
            
            # Sort by live performance (total PnL)
            comparison.sort(key=lambda x: x["live"]["total_pnl"], reverse=True)
            
            return {
                "success": True,
                "comparison": comparison,
                "total_strategies": len(comparison),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in strategy comparison: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_top_performing_strategies(self, metric: str = "pnl", limit: int = 5) -> Dict[str, Any]:
        """Get top performing strategies based on specified metric"""
        try:
            comparison = await self.get_strategy_comparison()
            
            if not comparison.get("success"):
                return comparison
            
            strategies = comparison.get("comparison", [])
            
            # Sort by requested metric
            if metric == "pnl":
                strategies.sort(key=lambda x: x["live"]["total_pnl"], reverse=True)
            elif metric == "win_rate":
                strategies.sort(key=lambda x: x["live"]["win_rate"], reverse=True)
            elif metric == "sharpe":
                strategies.sort(key=lambda x: x["backtest"]["avg_sharpe"], reverse=True)
            elif metric == "return":
                strategies.sort(key=lambda x: x["backtest"]["avg_return"], reverse=True)
            else:
                return {
                    "success": False,
                    "error": f"Unknown metric: {metric}. Use: pnl, win_rate, sharpe, return"
                }
            
            top_strategies = strategies[:limit]
            
            return {
                "success": True,
                "metric": metric,
                "top_strategies": top_strategies,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting top performing strategies: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

