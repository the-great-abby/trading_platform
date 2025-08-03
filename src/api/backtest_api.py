"""
Backtest Results API - REST API for viewing and managing backtest results
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import logging

from ..services.database.backtest_results_service import BacktestResultsService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Backtest Results API",
    description="API for viewing and managing backtest results from the database",
    version="1.0.0"
)

# Dependency to get the service
def get_backtest_service():
    return BacktestResultsService()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Backtest Results API",
        "version": "1.0.0",
        "endpoints": {
            "runs": "/api/v1/runs",
            "run_details": "/api/v1/runs/{run_id}",
            "trades": "/api/v1/runs/{run_id}/trades",
            "equity_curve": "/api/v1/runs/{run_id}/equity",
            "compare_strategies": "/api/v1/compare",
            "delete_run": "/api/v1/runs/{run_id} (DELETE)"
        }
    }

@app.get("/api/v1/runs")
async def list_runs(
    strategy_name: Optional[str] = Query(None, description="Filter by strategy name"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=1000, description="Maximum number of runs to return"),
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """List backtest runs with optional filtering"""
    try:
        runs = service.get_backtest_runs(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "data": runs,
            "count": len(runs),
            "filters": {
                "strategy_name": strategy_name,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error listing runs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/runs/{run_id}")
async def get_run_details(
    run_id: str,
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Get detailed information about a specific backtest run"""
    try:
        # Get all runs to find the specific one
        runs = service.get_backtest_runs(limit=1000)
        target_run = None
        
        for run in runs:
            if run['run_id'] == run_id:
                target_run = run
                break
        
        if not target_run:
            raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found")
        
        return {
            "success": True,
            "data": target_run
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/runs/{run_id}/trades")
async def get_run_trades(
    run_id: str,
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of trades to return"),
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Get trades for a specific backtest run"""
    try:
        trades = service.get_backtest_trades(run_id)
        
        # Apply limit
        if limit and len(trades) > limit:
            trades = trades[:limit]
        
        return {
            "success": True,
            "data": trades,
            "count": len(trades),
            "run_id": run_id,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/runs/{run_id}/equity")
async def get_run_equity_curve(
    run_id: str,
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of equity points to return"),
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Get equity curve data for a specific backtest run"""
    try:
        equity_data = service.get_equity_curve(run_id)
        
        # Apply limit
        if limit and len(equity_data) > limit:
            equity_data = equity_data[:limit]
        
        return {
            "success": True,
            "data": equity_data,
            "count": len(equity_data),
            "run_id": run_id,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting equity curve: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/compare")
async def compare_strategies(
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Compare performance of different strategies"""
    try:
        # Get recent runs for each strategy
        all_runs = service.get_backtest_runs(limit=1000)
        
        # Group by strategy and get the most recent run for each
        strategy_runs = {}
        for run in all_runs:
            strategy = run['strategy_name']
            if strategy not in strategy_runs or run['created_at'] > strategy_runs[strategy]['created_at']:
                strategy_runs[strategy] = run
        
        if not strategy_runs:
            return {
                "success": True,
                "data": [],
                "message": "No backtest runs found for comparison"
            }
        
        # Sort by return percentage
        sorted_runs = sorted(strategy_runs.values(), key=lambda x: x['total_return_pct'], reverse=True)
        
        # Calculate summary statistics
        total_strategies = len(sorted_runs)
        avg_return = sum(r['total_return_pct'] for r in sorted_runs) / total_strategies
        best_strategy = sorted_runs[0] if sorted_runs else None
        worst_strategy = sorted_runs[-1] if sorted_runs else None
        
        return {
            "success": True,
            "data": sorted_runs,
            "summary": {
                "total_strategies": total_strategies,
                "average_return": avg_return,
                "best_strategy": {
                    "name": best_strategy['strategy_name'],
                    "return": best_strategy['total_return_pct']
                } if best_strategy else None,
                "worst_strategy": {
                    "name": worst_strategy['strategy_name'],
                    "return": worst_strategy['total_return_pct']
                } if worst_strategy else None
            }
        }
    except Exception as e:
        logger.error(f"Error comparing strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/v1/runs/{run_id}")
async def delete_run(
    run_id: str,
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Delete a backtest run and all associated data"""
    try:
        success = service.delete_backtest_run(run_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully deleted backtest run '{run_id}'"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete backtest run '{run_id}'")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/strategies")
async def list_strategies(
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Get list of all strategies that have been tested"""
    try:
        all_runs = service.get_backtest_runs(limit=1000)
        
        # Get unique strategy names
        strategies = list(set(run['strategy_name'] for run in all_runs))
        strategies.sort()
        
        # Get performance summary for each strategy
        strategy_summary = []
        for strategy in strategies:
            strategy_runs = [r for r in all_runs if r['strategy_name'] == strategy]
            
            if strategy_runs:
                # Get the most recent run
                latest_run = max(strategy_runs, key=lambda x: x['created_at'])
                
                strategy_summary.append({
                    "name": strategy,
                    "total_runs": len(strategy_runs),
                    "latest_run": {
                        "run_id": latest_run['run_id'],
                        "return": latest_run['total_return_pct'],
                        "sharpe": latest_run['sharpe_ratio'],
                        "trades": latest_run['total_trades'],
                        "win_rate": latest_run['win_rate'],
                        "date_range": f"{latest_run['start_date']} to {latest_run['end_date']}"
                    }
                })
        
        return {
            "success": True,
            "data": strategy_summary,
            "count": len(strategy_summary)
        }
    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/stats")
async def get_stats(
    service: BacktestResultsService = Depends(get_backtest_service)
):
    """Get overall statistics about backtest results"""
    try:
        all_runs = service.get_backtest_runs(limit=1000)
        
        if not all_runs:
            return {
                "success": True,
                "data": {
                    "total_runs": 0,
                    "total_strategies": 0,
                    "date_range": None,
                    "performance_summary": None
                }
            }
        
        # Calculate statistics
        total_runs = len(all_runs)
        total_strategies = len(set(r['strategy_name'] for r in all_runs))
        
        # Date range
        all_dates = []
        for run in all_runs:
            all_dates.extend([run['start_date'], run['end_date']])
        
        date_range = {
            "earliest": min(all_dates),
            "latest": max(all_dates)
        }
        
        # Performance summary
        returns = [r['total_return_pct'] for r in all_runs]
        performance_summary = {
            "average_return": sum(returns) / len(returns),
            "best_return": max(returns),
            "worst_return": min(returns),
            "total_trades": sum(r['total_trades'] for r in all_runs),
            "average_win_rate": sum(r['win_rate'] for r in all_runs) / len(all_runs)
        }
        
        return {
            "success": True,
            "data": {
                "total_runs": total_runs,
                "total_strategies": total_strategies,
                "date_range": date_range,
                "performance_summary": performance_summary
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    ) 