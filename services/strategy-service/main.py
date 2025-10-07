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

# Include config router
from src.api.config import router as config_router
app.include_router(config_router)

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
    initial_capital: float = 100000.0

class BacktestResult(BaseModel):
    name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    final_capital: float  # Add the missing final_capital field
    trades: List[dict] = []  # Add trades field

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
        logger.info(f"🔧 DEBUG: Initial capital from request: {request.initial_capital}")
        engine = BacktestEngine(use_real_data=use_real_data, use_cache=use_cache, initial_capital=request.initial_capital)
        logger.info(f"🔧 DEBUG: Engine initial capital: {engine.initial_capital}")
        
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
                profit_factor=result.profit_factor,
                final_capital=result.final_capital,  # Add the missing final_capital field
                trades=[trade.__dict__ for trade in result.trades] if hasattr(result, 'trades') and result.trades else []
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

@app.post("/api/trading/generate-trade")
async def generate_trade():
    """Generate a test trade and send it to trading services"""
    strategy_requests_total.inc()
    
    try:
        import aiohttp
        import random
        from datetime import datetime, timedelta
        
        # Generate a simple test trade
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        symbol = random.choice(symbols)
        action = "BUY"
        quantity = random.randint(1, 10)
        price = random.uniform(100, 500)
        
        trade_data = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "strategy": "SimpleStrategy",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to paper trading service
        paper_trade_sent = False
        live_trade_sent = False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Send to paper trading service
                paper_order = {
                    "symbol": symbol,
                    "strategy": "SimpleStrategy",
                    "legs": [{
                        "action": action,
                        "option_type": "CALL",
                        "strike_price": price * 1.02,
                        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                        "quantity": quantity,
                        "premium": price * 0.1
                    }],
                    "order_type": "MARKET",
                    "time_in_force": "DAY",
                    "estimated_premium": price * 0.1,
                    "estimated_risk": price * quantity,
                    "greeks": {}
                }
                
                async with session.post(
                    "http://paper-trading-k8s-service.trading-system.svc.cluster.local:8080/api/v1/trading/orders",
                    json=paper_order,
                    params={"account_id": "19c25392-8b61-4b71-a344-0eb04d275528"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        paper_trade_sent = True
                        logger.info(f"✅ Paper trade sent: {symbol} {action} {quantity} @ ${price:.2f}")
                
                # Send to live trading service
                async with session.post(
                    "http://live-trading-service.default.svc.cluster.local:8080/api/v1/trading/orders",
                    json=paper_order,
                    params={"account_id": "19c25392-8b61-4b71-a344-0eb04d275528"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        live_trade_sent = True
                        logger.info(f"✅ Live trade sent: {symbol} {action} {quantity} @ ${price:.2f}")
                        
        except Exception as e:
            logger.error(f"Error sending trades: {e}")
        
        return {
            "message": "Trade generated and sent",
            "trade": trade_data,
            "paper_trade_sent": paper_trade_sent,
            "live_trade_sent": live_trade_sent
        }
        
    except Exception as e:
        logger.error(f"Error generating trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/recommendations")
async def get_trade_recommendations(symbol: Optional[str] = None, limit: int = 5):
    """Get trade recommendations combining Elliott Wave analysis with strategy signals"""
    strategy_requests_total.inc()
    
    try:
        import aiohttp
        import random
        from datetime import datetime, timedelta
        
        recommendations = []
        
        # Define symbols to analyze
        symbols_to_analyze = [symbol] if symbol else ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY", "QQQ"]
        
        async with aiohttp.ClientSession() as session:
            for sym in symbols_to_analyze:
                try:
                    # Get Elliott Wave analysis
                    elliott_analysis = None
                    try:
                        async with session.get(
                            f"http://elliott-wave-service.trading-system.svc.cluster.local:8000/elliott-wave/analyze/{sym}",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                elliott_data = await response.json()
                                elliott_analysis = elliott_data  # Elliott Wave service returns analysis directly
                    except Exception as e:
                        logger.warning(f"Could not get Elliott Wave analysis for {sym}: {e}")
                    
                    # Get current market data
                    current_price = random.uniform(100, 500)  # Mock price for now
                    
                    # Calculate recommendation score
                    recommendation_score = 0
                    recommendation_reasons = []
                    
                    # Elliott Wave scoring
                    if elliott_analysis:
                        pattern_type = elliott_analysis.get('pattern_type', '')
                        confidence = elliott_analysis.get('confidence', 0)
                        pattern_found = elliott_analysis.get('pattern_found', False)
                        target_price = elliott_analysis.get('target_price', 0)
                        
                        # Determine signal based on pattern and target price
                        signal = 'HOLD'
                        if pattern_found and confidence > 0.5:
                            if target_price > current_price:
                                signal = 'BUY'
                            elif target_price < current_price:
                                signal = 'SELL'
                        
                        if signal == 'BUY' and confidence > 0.5:
                            recommendation_score += confidence * 60  # Up to 60 points (increased for swing trades)
                            recommendation_reasons.append(f"Elliott Wave BUY signal (confidence: {confidence:.2f})")
                        elif signal == 'SELL' and confidence > 0.5:
                            recommendation_score -= confidence * 50  # Up to -50 points
                            recommendation_reasons.append(f"Elliott Wave SELL signal (confidence: {confidence:.2f})")
                        
                        if pattern_type:
                            recommendation_reasons.append(f"Pattern: {pattern_type}")
                        
                        # Store the signal for the response
                        elliott_analysis['signal'] = signal
                    
                    # Strategy scoring - Use Elliott Wave confidence as primary signal
                    # For daily swing trades, Elliott Wave is the main indicator
                    strategy_score = confidence if confidence else 0.5
                    recommendation_score += strategy_score * 25  # Up to 25 points
                    recommendation_reasons.append(f"Daily swing signal strength: {strategy_score:.2f}")
                    
                    # Market conditions - Stable scoring based on pattern strength
                    # Higher confidence patterns = better market conditions
                    market_score = 0.7 if confidence > 0.6 else (0.5 if confidence > 0.4 else 0.3)
                    recommendation_score += market_score * 15  # Up to 15 points
                    recommendation_reasons.append(f"Market regime: {market_score:.2f}")
                    
                    # Risk assessment - Minimal deduction (we have risk mgmt layer)
                    risk_score = 0.1 if pattern_found else 0.2  # Lower is better
                    recommendation_score -= risk_score * 5  # Up to -5 points (reduced impact)
                    recommendation_reasons.append(f"Pattern risk: {risk_score:.2f}")
                    
                    # Calculate final recommendation
                    if recommendation_score > 60:
                        action = "STRONG BUY"
                        color = "🟢"
                    elif recommendation_score > 40:
                        action = "BUY"
                        color = "🟡"
                    elif recommendation_score > 20:
                        action = "HOLD"
                        color = "🟠"
                    elif recommendation_score > 0:
                        action = "WEAK SELL"
                        color = "🔴"
                    else:
                        action = "SELL"
                        color = "🔴"
                    
                    recommendation = {
                        "symbol": sym,
                        "current_price": round(current_price, 2),
                        "action": action,
                        "color": color,
                        "score": round(recommendation_score, 2),
                        "confidence": min(1.0, max(0.0, abs(recommendation_score) / 100)),
                        "reasons": recommendation_reasons,
                        "elliott_wave": elliott_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {sym}: {e}")
                    continue
        
        # Sort by recommendation score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit results
        recommendations = recommendations[:limit]
        
        return {
            "message": f"Trade recommendations for {len(recommendations)} symbols",
            "recommendations": recommendations,
            "total_analyzed": len(symbols_to_analyze),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/recommendations/{symbol}")
async def get_symbol_recommendation(symbol: str):
    """Get detailed trade recommendation for a specific symbol"""
    recommendations = await get_trade_recommendations(symbol=symbol, limit=1)
    if recommendations['recommendations']:
        return recommendations['recommendations'][0]
    else:
        raise HTTPException(status_code=404, detail=f"No recommendation found for {symbol}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
