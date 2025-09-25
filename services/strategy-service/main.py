from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response
from typing import List, Optional
import sys
import asyncio
import logging

# Add the src directory to the path
sys.path.append('/app/src')

# Configure logging for containerized environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output for container logs
    ]
)

logger = logging.getLogger(__name__)

# Containerized environment configuration
DATABASE_ONLY = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() in ('true', '1', 'yes')
ENABLE_OPTIONS_STRATEGIES = os.getenv('ENABLE_OPTIONS_STRATEGIES', 'true').lower() in ('true', '1', 'yes')

logger.info(f"🔧 Strategy Service Configuration:")
logger.info(f"   DATABASE_ONLY: {DATABASE_ONLY}")
logger.info(f"   USE_MOCK_DATA: {USE_MOCK_DATA}")
logger.info(f"   ENABLE_OPTIONS_STRATEGIES: {ENABLE_OPTIONS_STRATEGIES}")

app = FastAPI(title="Strategy Service", version="1.0.0")

# Prometheus metrics
strategy_requests_total = Counter("strategy_requests_total", "Total number of strategy requests")
strategy_request_duration = Histogram("strategy_request_duration_seconds", "Time spent on strategy requests")

class Strategy(BaseModel):
    name: str
    type: str
    parameters: dict

class BacktestRequest(BaseModel):
    symbols: List[str]
    start_date: str
    end_date: str
    strategies: List[str]

class BacktestResult(BaseModel):
    name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float

@app.get("/")
async def root():
    strategy_requests_total.inc()
    return {"message": "Strategy Service is running"}

@app.get("/health")
async def health():
    strategy_requests_total.inc()
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    strategy_requests_total.inc()
    return {"status": "ready"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/api/v1/strategies")
async def create_strategy(strategy: Strategy):
    strategy_requests_total.inc()
    return {"message": "Strategy created", "strategy": strategy}

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run a backtest with the specified parameters"""
    strategy_requests_total.inc()
    
    try:
        # Import the backtest engine
        from src.backtesting.engine.backtest_engine import BacktestEngine
        
        # Configure backtest engine based on containerized environment
        use_real_data = not USE_MOCK_DATA
        use_cache = not DATABASE_ONLY
        
        logger.info(f"🔧 Backtest Configuration:")
        logger.info(f"   use_real_data: {use_real_data}")
        logger.info(f"   use_cache: {use_cache}")
        logger.info(f"   enable_options_strategies: {ENABLE_OPTIONS_STRATEGIES}")
        
        # Initialize backtest engine with containerized configuration
        engine = BacktestEngine(use_real_data=use_real_data, use_cache=use_cache)
        
        # Run backtest
        print(f"🚀 Starting backtest for {request.strategies} on {request.symbols}")
        results = await engine.run_backtest(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            strategies=request.strategies
        )
        
        # Convert results to the expected format
        formatted_results = []
        for strategy_name, result in results.items():
            formatted_results.append(BacktestResult(
                name=strategy_name,
                total_return=result.total_return,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                win_rate=result.win_rate,
                total_trades=result.total_trades,
                profit_factor=result.profit_factor
            ))
        
        return {
            "success": True,
            "results": formatted_results,
            "message": "Backtest completed successfully"
        }
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.post("/api/strategies/compare")
async def compare_strategies():
    """Run comprehensive strategy comparison with progress tracking"""
    try:
        # Import the comparison function
        from compare_strategies import compare_strategies
        
        print("🚀 Starting strategy comparison via API...")
        
        # Run the comparison
        await compare_strategies()
        
        return {
            "success": True,
            "message": "Strategy comparison completed successfully. Check logs for detailed results."
        }
        
    except Exception as e:
        print(f"❌ Error running strategy comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy comparison failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
