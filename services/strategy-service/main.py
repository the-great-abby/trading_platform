from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response
from typing import List, Optional
import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append('/app/src')

# Import pattern scanner and multi-indicator analyzer
from pattern_scanner import PatternScanner
from multi_indicator_analyzer import MultiIndicatorAnalyzer, combine_elliott_wave_and_indicators

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
                    
                    # Get current market price from market-data-service
                    current_price = None
                    try:
                        async with session.get(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/current/{sym}",
                            timeout=aiohttp.ClientTimeout(total=3)
                        ) as response:
                            if response.status == 200:
                                price_data = await response.json()
                                current_price = price_data.get('price')  # Get current price from response
                    except Exception as e:
                        logger.warning(f"Could not get current price for {sym}: {e}")
                    
                    # Fallback: Use last price from Elliott Wave data if available
                    if (current_price is None or current_price == 0.0) and elliott_analysis and 'waves' in elliott_analysis:
                        waves = elliott_analysis.get('waves', [])
                        if waves and isinstance(waves, list) and len(waves) > 0:
                            last_wave = waves[-1]
                            if isinstance(last_wave, dict) and 'price' in last_wave:
                                current_price = last_wave['price']
                                logger.info(f"Using Elliott Wave price for {sym}: ${current_price}")
                    
                    # Final fallback (should rarely happen)
                    if current_price is None or current_price == 0.0:
                        current_price = 150.0  # Conservative fallback
                        logger.warning(f"Using fallback price for {sym}: ${current_price}")
                    
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

@app.get("/api/trading/scan/recent-patterns")
async def scan_for_recent_patterns(
    min_confidence: float = 0.5,
    max_age_days: int = 60,
    limit: int = 10,
    timeframe: str = "1d"
):
    """
    Scan all symbols for RECENT valid Elliott Wave patterns
    
    Returns only symbols with patterns that:
    - Were detected in the last 60 days (not year-old patterns)
    - Meet minimum confidence threshold
    - Have actionable BUY/SELL signals
    """
    strategy_requests_total.inc()
    
    try:
        # All available symbols from database
        all_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'SPY', 'QQQ', 'VOO', 'VTI', 'ADBE', 'CRM', 'ORCL', 'CSCO',
            'QCOM', 'TXN', 'AVGO', 'SMCI', 'DIS', 'AMD', 'INTC', 'JPM',
            'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD'
        ]
        
        # Create scanner
        scanner = PatternScanner()
        scanner.min_confidence = min_confidence
        scanner.max_pattern_age_days = max_age_days
        
        # Scan all symbols
        patterns = await scanner.scan_symbols_for_patterns(all_symbols, timeframe)
        
        # Limit results
        patterns = patterns[:limit]
        
        return {
            "message": f"Found {len(patterns)} symbols with recent Elliott Wave patterns",
            "patterns": patterns,
            "total_scanned": len(all_symbols),
            "criteria": {
                "min_confidence": min_confidence,
                "max_pattern_age_days": max_age_days,
                "timeframe": timeframe
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scanning for patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/recommendations/enhanced")
async def get_enhanced_recommendations(
    symbol: Optional[str] = None,
    symbols: Optional[str] = None,  # NEW: Comma-separated list of symbols
    limit: int = 10,
    timeframe: str = "1d",  # NEW: Support multiple timeframes
    lookback_days: int = 365,  # NEW: Adjustable lookback period
    min_elliott_confidence: float = 0.3,  # Lowered from 0.5 for more flexibility
    elliott_weight: float = 0.5,  # 50/50 blend
    technical_weight: float = 0.5
):
    """
    Enhanced recommendations combining Elliott Wave + Technical Indicators
    
    Features:
    - Lower Elliott Wave confidence threshold (0.3 vs 0.5)
    - Adds RSI, MACD, Moving Averages, Volume, Bollinger Bands, Ichimoku
    - Multi-indicator consensus voting
    - Works even when Elliott Wave patterns are old
    - Supports multiple timeframes: 1d, 1h, 15m, 5m
    - Automatic indicator period adjustment based on timeframe
    """
    strategy_requests_total.inc()
    
    try:
        import aiohttp
        
        from src.utils.trading_config import get_symbols
        
        recommendations = []
        # Priority: explicit symbols list > single symbol > all configured symbols
        if symbols:
            symbols_to_analyze = [s.strip() for s in symbols.split(",")]
        elif symbol:
            symbols_to_analyze = [symbol]
        else:
            symbols_to_analyze = get_symbols()
        
        # Create analyzer instance with timeframe-adjusted parameters
        indicator_analyzer = MultiIndicatorAnalyzer(timeframe=timeframe)
        
        async with aiohttp.ClientSession() as session:
            for sym in symbols_to_analyze:
                try:
                    # Get Elliott Wave analysis (relaxed threshold)
                    elliott_analysis = None
                    try:
                        async with session.get(
                            f"http://elliott-wave-service.trading-system.svc.cluster.local:8000/elliott-wave/analyze/{sym}",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                elliott_analysis = await response.json()
                    except Exception as e:
                        logger.warning(f"Could not get Elliott Wave for {sym}: {e}")
                    
                    # Get historical data for technical analysis
                    market_data = None
                    try:
                        async with session.post(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/historical",
                            json={
                                "symbol": sym,
                                "start_date": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
                                "end_date": datetime.now().strftime("%Y-%m-%d"),
                                "interval": timeframe
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data_response = await response.json()
                                if data_response.get('data'):
                                    # Convert to DataFrame for analysis
                                    import pandas as pd
                                    df = pd.DataFrame(data_response['data'])
                                    df['date'] = pd.to_datetime(df['date'])
                                    df = df.rename(columns={
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    })
                                    market_data = df
                    except Exception as e:
                        logger.warning(f"Could not get market data for {sym}: {e}")
                    
                    if market_data is None or market_data.empty:
                        continue
                    
                    # Run technical indicator analysis
                    technical_analysis = indicator_analyzer.analyze(market_data)
                    
                    # Get current price
                    current_price = float(market_data['Close'].iloc[-1])
                    
                    # Combine Elliott Wave with technical indicators
                    if elliott_analysis and elliott_analysis.get('pattern_found'):
                        # Use combining function
                        combined = combine_elliott_wave_and_indicators(
                            elliott_analysis,
                            technical_analysis,
                            elliott_weight,
                            technical_weight
                        )
                    else:
                        # No Elliott Wave, use pure technical
                        combined = {
                            'signal': technical_analysis['composite_signal'],
                            'confidence': technical_analysis['composite_confidence'],
                            'score': technical_analysis['composite_score'],
                            'reasons': ['No Elliott Wave pattern'] + technical_analysis['reasons']
                        }
                    
                    recommendation = {
                        "symbol": sym,
                        "current_price": round(current_price, 2),
                        "action": combined['signal'],
                        "score": combined['score'],
                        "confidence": combined['confidence'],
                        "reasons": combined['reasons'],
                        "elliott_wave": elliott_analysis,
                        "technical_indicators": technical_analysis,
                        "methodology": "Elliott Wave + Multi-Indicator",
                        "timeframe": timeframe,
                        "lookback_days": lookback_days,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {sym}: {e}")
                    continue
        
        # Sort by composite score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:limit]
        
        return {
            "message": f"Enhanced recommendations for {len(recommendations)} symbols",
            "timeframe": timeframe,
            "lookback_days": lookback_days,
            "recommendations": recommendations,
            "methodology": "Elliott Wave (50%) + Technical Indicators (50%)",
            "indicators_used": ["RSI", "MACD", "Moving Averages", "Volume", "Bollinger Bands"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/recommendations/intraday")
async def get_intraday_recommendations(
    symbol: Optional[str] = None,
    limit: int = 10,
    timeframe: str = "1h",  # Default to hourly for intraday
    aggressive: bool = True  # More aggressive signals for day trading
):
    """
    Intraday-optimized recommendations for day trading
    
    Features:
    - Optimized for 1h and 15m timeframes
    - Faster indicator periods for quick signals
    - More aggressive entry/exit signals
    - No Elliott Wave (too slow for intraday)
    - Pure technical indicators
    - Volume-weighted signals
    
    Best for:
    - Day trading strategies
    - Quick entries/exits
    - Momentum plays
    - Scalping opportunities
    """
    strategy_requests_total.inc()
    
    try:
        import aiohttp
        
        recommendations = []
        symbols_to_analyze = [symbol] if symbol else ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY", "QQQ", "AMZN", "META", "NFLX"]
        
        # Use shorter lookback for intraday
        lookback_days = 30 if timeframe == "1h" else 7 if timeframe == "15m" else 3
        
        # Create analyzer instance optimized for intraday
        indicator_analyzer = MultiIndicatorAnalyzer(timeframe=timeframe)
        
        async with aiohttp.ClientSession() as session:
            for sym in symbols_to_analyze:
                try:
                    # Get historical data for technical analysis (no Elliott Wave for speed)
                    market_data = None
                    try:
                        async with session.post(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/historical",
                            json={
                                "symbol": sym,
                                "start_date": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
                                "end_date": datetime.now().strftime("%Y-%m-%d"),
                                "interval": timeframe
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data_response = await response.json()
                                if data_response.get('data'):
                                    # Convert to DataFrame for analysis
                                    import pandas as pd
                                    df = pd.DataFrame(data_response['data'])
                                    df['date'] = pd.to_datetime(df['date'])
                                    df = df.rename(columns={
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    })
                                    market_data = df
                    except Exception as e:
                        logger.warning(f"Could not get market data for {sym}: {e}")
                    
                    if market_data is None or market_data.empty:
                        continue
                    
                    # Run technical indicator analysis
                    technical_analysis = indicator_analyzer.analyze(market_data)
                    
                    # Get current price
                    current_price = float(market_data['Close'].iloc[-1])
                    
                    # For aggressive intraday, boost signals
                    composite_score = technical_analysis['composite_score']
                    composite_confidence = technical_analysis['composite_confidence']
                    
                    if aggressive:
                        # More aggressive thresholds for intraday
                        if composite_score > 40:
                            signal = 'STRONG_BUY'
                            composite_confidence = min(1.0, composite_confidence * 1.2)
                        elif composite_score > 20:
                            signal = 'BUY'
                            composite_confidence = min(1.0, composite_confidence * 1.1)
                        elif composite_score > -20:
                            signal = 'HOLD'
                        elif composite_score > -40:
                            signal = 'SELL'
                            composite_confidence = min(1.0, composite_confidence * 1.1)
                        else:
                            signal = 'STRONG_SELL'
                            composite_confidence = min(1.0, composite_confidence * 1.2)
                    else:
                        signal = technical_analysis['composite_signal']
                    
                    # Build recommendation
                    recommendation = {
                        "symbol": sym,
                        "current_price": round(current_price, 2),
                        "action": signal,
                        "score": composite_score,
                        "confidence": round(composite_confidence, 2),
                        "reasons": technical_analysis['reasons'],
                        "technical_indicators": technical_analysis,
                        "methodology": "Pure Technical Indicators (Intraday Optimized)",
                        "timeframe": timeframe,
                        "lookback_days": lookback_days,
                        "aggressive_mode": aggressive,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {sym}: {e}")
                    continue
        
        # Sort by composite score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:limit]
        
        return {
            "message": f"Intraday recommendations for {len(recommendations)} symbols",
            "timeframe": timeframe,
            "lookback_days": lookback_days,
            "aggressive_mode": aggressive,
            "recommendations": recommendations,
            "methodology": "Pure Technical Indicators - No Elliott Wave",
            "indicators_used": ["RSI", "MACD", "Moving Averages", "Volume", "Bollinger Bands", "Ichimoku"],
            "optimized_for": "Day Trading / Intraday",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating intraday recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/recommendations/multi-timeframe")
async def get_multi_timeframe_recommendations(
    symbol: Optional[str] = None,
    limit: int = 10,
    daily_weight: float = 0.4,  # 40% weight to daily trend
    hourly_weight: float = 0.4,  # 40% weight to hourly momentum
    minute_weight: float = 0.2   # 20% weight to 15m entry timing
):
    """
    Multi-timeframe analysis combining daily trend + hourly momentum + 15m timing
    
    This is the most sophisticated recommendation system that analyzes:
    - Daily (1d): Overall trend direction and long-term health
    - Hourly (1h): Medium-term momentum and entry opportunities  
    - 15-minute (15m): Short-term entry/exit timing
    
    Weighted scoring system combines all three timeframes to give you:
    - Trend alignment (all timeframes agree = highest confidence)
    - Better entry timing (combine daily trend with intraday signals)
    - Risk management (avoid counter-trend trades)
    
    Best for:
    - Swing trading with precise entries
    - Avoiding false breakouts
    - High-confidence setups
    - Position trading with day-trader entries
    """
    strategy_requests_total.inc()
    
    try:
        import aiohttp
        from src.utils.trading_config import get_symbols
        
        recommendations = []
        symbols_to_analyze = [symbol] if symbol else get_symbols()
        
        # Create analyzers for each timeframe
        daily_analyzer = MultiIndicatorAnalyzer(timeframe="1d")
        hourly_analyzer = MultiIndicatorAnalyzer(timeframe="1h")
        minute_analyzer = MultiIndicatorAnalyzer(timeframe="15m")
        
        async with aiohttp.ClientSession() as session:
            for sym in symbols_to_analyze:
                try:
                    # Fetch data for all three timeframes
                    daily_data = None
                    hourly_data = None
                    minute_data = None
                    
                    # Daily data (1 year)
                    try:
                        async with session.post(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/historical",
                            json={
                                "symbol": sym,
                                "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                                "end_date": datetime.now().strftime("%Y-%m-%d"),
                                "interval": "1d"
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data_response = await response.json()
                                if data_response.get('data'):
                                    import pandas as pd
                                    df = pd.DataFrame(data_response['data'])
                                    df['date'] = pd.to_datetime(df['date'])
                                    df = df.rename(columns={
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    })
                                    daily_data = df
                    except Exception as e:
                        logger.warning(f"Could not get daily data for {sym}: {e}")
                    
                    # Hourly data (30 days)
                    try:
                        async with session.post(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/historical",
                            json={
                                "symbol": sym,
                                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                                "end_date": datetime.now().strftime("%Y-%m-%d"),
                                "interval": "1h"
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data_response = await response.json()
                                if data_response.get('data'):
                                    import pandas as pd
                                    df = pd.DataFrame(data_response['data'])
                                    df['date'] = pd.to_datetime(df['date'])
                                    df = df.rename(columns={
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    })
                                    hourly_data = df
                    except Exception as e:
                        logger.warning(f"Could not get hourly data for {sym}: {e}")
                    
                    # 15-minute data (7 days)
                    try:
                        async with session.post(
                            f"http://market-data-service.trading-system.svc.cluster.local:11084/market-data/historical",
                            json={
                                "symbol": sym,
                                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                                "end_date": datetime.now().strftime("%Y-%m-%d"),
                                "interval": "15m"
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data_response = await response.json()
                                if data_response.get('data'):
                                    import pandas as pd
                                    df = pd.DataFrame(data_response['data'])
                                    df['date'] = pd.to_datetime(df['date'])
                                    df = df.rename(columns={
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    })
                                    minute_data = df
                    except Exception as e:
                        logger.warning(f"Could not get 15m data for {sym}: {e}")
                    
                    # Skip if we don't have at least 2 timeframes
                    available_timeframes = sum([
                        daily_data is not None and not daily_data.empty,
                        hourly_data is not None and not hourly_data.empty,
                        minute_data is not None and not minute_data.empty
                    ])
                    
                    if available_timeframes < 2:
                        logger.warning(f"Insufficient data for multi-timeframe analysis of {sym}")
                        continue
                    
                    # Analyze each timeframe
                    daily_analysis = None
                    hourly_analysis = None
                    minute_analysis = None
                    current_price = None
                    
                    if daily_data is not None and not daily_data.empty:
                        daily_analysis = daily_analyzer.analyze(daily_data)
                        current_price = float(daily_data['Close'].iloc[-1])
                    
                    if hourly_data is not None and not hourly_data.empty:
                        hourly_analysis = hourly_analyzer.analyze(hourly_data)
                        if current_price is None:
                            current_price = float(hourly_data['Close'].iloc[-1])
                    
                    if minute_data is not None and not minute_data.empty:
                        minute_analysis = minute_analyzer.analyze(minute_data)
                        if current_price is None:
                            current_price = float(minute_data['Close'].iloc[-1])
                    
                    # Combine signals with weighted scoring
                    scores = []
                    weights = []
                    reasons = []
                    
                    if daily_analysis:
                        scores.append(daily_analysis['composite_score'])
                        weights.append(daily_weight)
                        trend = daily_analysis['moving_averages']['trend']
                        reasons.append(f"Daily: {daily_analysis['composite_signal']} ({trend})")
                    
                    if hourly_analysis:
                        scores.append(hourly_analysis['composite_score'])
                        weights.append(hourly_weight)
                        reasons.append(f"Hourly: {hourly_analysis['composite_signal']} (Momentum)")
                    
                    if minute_analysis:
                        scores.append(minute_analysis['composite_score'])
                        weights.append(minute_weight)
                        reasons.append(f"15m: {minute_analysis['composite_signal']} (Entry Timing)")
                    
                    # Calculate weighted combined score
                    combined_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                    
                    # Calculate alignment confidence boost
                    # If all timeframes point same direction, boost confidence
                    all_positive = all(s > 0 for s in scores)
                    all_negative = all(s < 0 for s in scores)
                    alignment_boost = 1.3 if (all_positive or all_negative) else 1.0
                    
                    # Base confidence from available analyses
                    confidences = []
                    if daily_analysis:
                        confidences.append(daily_analysis['composite_confidence'])
                    if hourly_analysis:
                        confidences.append(hourly_analysis['composite_confidence'])
                    if minute_analysis:
                        confidences.append(minute_analysis['composite_confidence'])
                    
                    # Avoid division by zero
                    if confidences:
                        combined_confidence = (sum(confidences) / len(confidences)) * alignment_boost
                        combined_confidence = min(1.0, combined_confidence)
                    else:
                        combined_confidence = 0.5  # Default confidence if no analyses available
                    
                    # Determine final signal
                    if combined_score > 60:
                        final_signal = 'STRONG_BUY'
                    elif combined_score > 30:
                        final_signal = 'BUY'
                    elif combined_score > -30:
                        final_signal = 'HOLD'
                    elif combined_score > -60:
                        final_signal = 'SELL'
                    else:
                        final_signal = 'STRONG_SELL'
                    
                    # Add alignment info
                    if all_positive or all_negative:
                        reasons.insert(0, "✅ ALL TIMEFRAMES ALIGNED - High Confidence!")
                    else:
                        reasons.insert(0, "⚠️ Mixed signals across timeframes")
                    
                    # Build recommendation
                    recommendation = {
                        "symbol": sym,
                        "current_price": round(current_price, 2),
                        "action": final_signal,
                        "score": round(combined_score, 2),
                        "confidence": round(combined_confidence, 2),
                        "alignment_boost": round(alignment_boost, 2),
                        "reasons": reasons,
                        "daily_analysis": daily_analysis,
                        "hourly_analysis": hourly_analysis,
                        "minute_analysis": minute_analysis,
                        "methodology": "Multi-Timeframe Analysis (Daily + Hourly + 15m)",
                        "timeframes_analyzed": available_timeframes,
                        "weights": {
                            "daily": daily_weight if daily_analysis else 0,
                            "hourly": hourly_weight if hourly_analysis else 0,
                            "minute": minute_weight if minute_analysis else 0
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {sym} multi-timeframe: {e}")
                    continue
        
        # Sort by composite score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:limit]
        
        return {
            "message": f"Multi-timeframe analysis for {len(recommendations)} symbols",
            "timeframes": ["1d (Daily)", "1h (Hourly)", "15m (Minute)"],
            "weights": {
                "daily": daily_weight,
                "hourly": hourly_weight,
                "minute": minute_weight
            },
            "recommendations": recommendations,
            "methodology": "Weighted Multi-Timeframe Analysis",
            "advantages": [
                "Better trend alignment",
                "Improved entry timing",
                "Higher confidence when aligned",
                "Reduced false signals"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating multi-timeframe recommendations: {e}")
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

@app.get("/api/options/scan")
async def scan_options_opportunities(
    symbols: Optional[str] = None,
    available_cash: float = 4000,
    min_confidence: float = 0.6
):
    """
    Scan for budget-friendly options opportunities.
    
    This endpoint uses the AutomatedOptionsScanner to find opportunities
    and filters them by available cash to ensure affordability.
    
    Args:
        symbols: Comma-separated list of symbols (default: standard options symbols)
        available_cash: Available cash for options trading (default: $4000)
        min_confidence: Minimum confidence score (default: 0.6 = 60%)
    
    Returns:
        List of affordable options opportunities with strategy recommendations
    """
    try:
        from src.services.options.automated_options_scanner import AutomatedOptionsScanner
        
        # Parse symbols
        symbol_list = None
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
        
        # Initialize scanner
        scanner = AutomatedOptionsScanner(symbols=symbol_list)
        scanner.min_confidence = min_confidence
        
        # Scan for opportunities
        opportunities = await scanner.scan_for_opportunities()
        
        # Filter by affordability
        # Strategy costs (from AdaptiveSectorWaveStrategy)
        strategy_costs = {
            'iron_condor': 100,
            'calendar_spread': 150,
            'butterfly_spread': 200,
            'strangle': 400,
            'straddle': 500
        }
        
        max_position_value = available_cash * 0.20  # 20% of capital per trade
        
        affordable_opportunities = []
        for opp in opportunities:
            # Map opportunity type to strategy cost
            estimated_cost = 200  # Default
            
            if 'iv_mean_reversion' in str(opp.opportunity_type).lower():
                estimated_cost = strategy_costs['iron_condor']
            elif 'calendar' in str(opp.opportunity_type).lower():
                estimated_cost = strategy_costs['calendar_spread']
            elif 'diagonal' in str(opp.opportunity_type).lower():
                estimated_cost = strategy_costs['butterfly_spread']
            elif 'volatility' in str(opp.opportunity_type).lower():
                estimated_cost = strategy_costs['strangle']
            
            # Check if affordable
            if estimated_cost <= max_position_value:
                affordable_opportunities.append({
                    'symbol': opp.symbol,
                    'opportunity_type': str(opp.opportunity_type),
                    'confidence': opp.confidence,
                    'estimated_cost': estimated_cost,
                    'suggested_strategy': opp.suggested_strategy,
                    'entry_price': opp.entry_price,
                    'target_price': opp.target_price,
                    'stop_loss': opp.stop_loss,
                    'expires_date': opp.expires_date.isoformat() if opp.expires_date else None,
                    'metadata': opp.metadata,
                    'affordable': True,
                    'max_position_value': max_position_value
                })
        
        return {
            'success': True,
            'opportunities_found': len(affordable_opportunities),
            'total_scanned': len(opportunities),
            'filtered_by_budget': len(opportunities) - len(affordable_opportunities),
            'available_cash': available_cash,
            'max_position_value': max_position_value,
            'opportunities': affordable_opportunities,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Options scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Options scan failed: {str(e)}")

