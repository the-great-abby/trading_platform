#!/usr/bin/env python3
"""
Elliott Wave Analysis Service - Main Application
"""

import logging
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add the src directory to path to import trading config
sys.path.append('/Users/abby/code/trading/src')
try:
    from utils.trading_config import SYMBOLS
except ImportError:
    # Fallback to a comprehensive list if import fails
    SYMBOLS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
        'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
        'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'SMCI'
    ]

from models import ElliottWavePattern, WaveType, HealthCheckResponse
from advanced_pattern_detection import AdvancedElliottWaveDetector
from options_integration import ElliottWaveOptionsIntegrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Elliott Wave Analysis Service",
    description="Advanced Elliott Wave pattern detection with options trading integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
elliott_detector: Optional[AdvancedElliottWaveDetector] = None
options_integrator: Optional[ElliottWaveOptionsIntegrator] = None
TRACKED_SYMBOLS = SYMBOLS  # Track all 43 symbols available in the database

def get_market_data_for_backtest(symbol: str, timeframe: str = "1d", historical_date: str = None, limit: int = 2000) -> pd.DataFrame:
    """Get historical market data for backtesting up to a specific date"""
    try:
        # Call market-data-service API for historical data
        market_data_service_url = os.getenv('MARKET_DATA_SERVICE_URL', 'http://market-data-service:11084')
        
        # Convert timeframe to API format
        if timeframe in ["1d", "daily"]:
            interval = "1d"
        elif timeframe in ["1h", "hourly"]:
            interval = "1h"
        elif timeframe in ["15m", "15min"]:
            interval = "15m"
        else:
            interval = "1d"  # Default to daily
        
        # Call market-data-service API using POST with request body
        url = f"{market_data_service_url}/market-data/historical"
        
        # Calculate date range for backtesting - Use 5 years of data for better Elliott Wave analysis
        from datetime import datetime, timedelta
        if historical_date:
            end_date = historical_date
            start_date = (datetime.strptime(historical_date, "%Y-%m-%d") - timedelta(days=1825)).strftime("%Y-%m-%d")  # 5 years
        else:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=1825)).strftime("%Y-%m-%d")  # 5 years
        
        request_data = {
            "symbol": symbol.upper(),
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval
        }
        
        import requests
        response = requests.post(url, json=request_data, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'data' not in data:
            logger.warning(f"No historical data returned from market-data-service for {symbol} up to {historical_date}")
            return pd.DataFrame()
        
        # Convert API response to DataFrame
        df = pd.DataFrame(data['data'])
        
        # Ensure required columns exist
        required_columns = ['date', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns in historical market data for {symbol}")
            return pd.DataFrame()
        
        # Convert date string to datetime first
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter data to only include data up to historical_date
        if historical_date:
            historical_dt = pd.to_datetime(historical_date)
            df = df[df['date'] <= historical_dt]
        
        # Sort by date and limit results
        df = df.sort_values('date').tail(limit)
        
        # Set date as index BEFORE renaming columns
        df = df.set_index('date')
        
        # Rename columns to match expected format
        df = df.rename(columns={
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        logger.info(f"Retrieved {len(df)} historical data points for {symbol} up to {historical_date}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching historical market data for {symbol}: {str(e)}")
        return pd.DataFrame()

def get_market_data(symbol: str, timeframe: str = "1d", limit: int = 1000) -> pd.DataFrame:
    try:
        # Call market-data-service API instead of direct database access
        market_data_service_url = os.getenv('MARKET_DATA_SERVICE_URL', 'http://market-data-service:11084')
        
        # Convert timeframe to API format
        if timeframe in ["1d", "daily"]:
            interval = "1d"
        elif timeframe in ["1h", "hourly"]:
            interval = "1h"
        elif timeframe in ["15m", "15min"]:
            interval = "15m"
        else:
            interval = "1d"  # Default to daily
        
        # Call market-data-service API using POST with request body
        url = f"{market_data_service_url}/market-data/historical"
        
        # Calculate date range for the request
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # Get 1 year of data
        
        request_data = {
            "symbol": symbol.upper(),
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval
        }
        
        import requests
        response = requests.post(url, json=request_data, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'data' not in data:
            logger.warning(f"No data returned from market-data-service for {symbol}")
            return pd.DataFrame()
        
        # Convert API response to DataFrame
        df = pd.DataFrame(data['data'])
        
        # Ensure required columns exist
        required_columns = ['date', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns in market data for {symbol}")
            return pd.DataFrame()
        
        # Convert date string to datetime first
        df['date'] = pd.to_datetime(df['date'])
        logger.info(f"After date conversion - DataFrame shape: {df.shape}")
        logger.info(f"Date column type: {df['date'].dtype}")
        logger.info(f"First few dates: {df['date'].head().tolist()}")

        # Set date as index BEFORE renaming columns
        df = df.set_index('date')
        logger.info(f"After setting index - DataFrame index type: {type(df.index)}")
        logger.info(f"DataFrame index dtype: {df.index.dtype}")
        logger.info(f"First few index values: {df.index[:5].tolist()}")

        # Rename columns to match expected format
        df = df.rename(columns={
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        # Sort by timestamp
        df = df.sort_index()
        logger.info(f"Final DataFrame - Index type: {type(df.index)}, dtype: {df.index.dtype}")
        logger.info(f"Final DataFrame shape: {df.shape}")
        logger.info(f"Final index sample: {df.index[:3].tolist()}")

        logger.info(f"Retrieved {len(df)} data points for {symbol} from market-data-service")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling market-data-service for {symbol}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error processing market data for {symbol}: {e}")
        return pd.DataFrame()


@app.on_event("startup")
async def startup_event():
    """Initialize service components on startup"""
    global elliott_detector, options_integrator
    
    logger.info("Starting Elliott Wave Analysis Service...")
    
    elliott_detector = AdvancedElliottWaveDetector()
    options_integrator = ElliottWaveOptionsIntegrator()
    
    logger.info("Elliott Wave Analysis Service started successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Elliott Wave Analysis Service",
        "service": "Elliott Wave Analysis",
        "version": "1.0.0",
        "symbols_tracked": len(TRACKED_SYMBOLS)
    }


@app.get("/elliott-wave/symbols")
async def get_symbols():
    """Get list of tracked symbols"""
    return {
        "symbols": TRACKED_SYMBOLS,
        "count": len(TRACKED_SYMBOLS)
    }


@app.get("/elliott-wave/analyze/{symbol}")
async def analyze_single_symbol(symbol: str, timeframe: str = "15m", historical_date: Optional[str] = None):
    """Analyze a single symbol for Elliott Wave patterns"""
    if symbol.upper() not in TRACKED_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not tracked")
    
    start_time = time.time()
    
    # Get market data - either current or historical for backtesting
    if historical_date:
        # For backtesting - get data up to historical_date
        data = get_market_data_for_backtest(symbol, timeframe, historical_date, limit=2000)
    else:
        # For live trading - get current data
        data = get_market_data(symbol, timeframe, limit=1000)
    
    if data.empty:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": f"No market data available for {symbol}",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date
        }
    
    logger.info(f"Analyzing {symbol} with {len(data)} data points (historical_date: {historical_date})")
    
    # Detect swing points
    swing_points = elliott_detector.detect_swing_points(data)
    
    if len(swing_points) < 5:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": f"Insufficient swing points for pattern detection (found {len(swing_points)})",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date
        }
    
    # Identify wave pattern
    pattern = elliott_detector.identify_wave_pattern(swing_points)
    
    if pattern:
        pattern.symbol = symbol.upper()
        pattern.timeframe = timeframe
        
        return {
            "symbol": symbol.upper(),
            "pattern_found": True,
            "pattern_type": pattern.pattern_type.value,
            "confidence": pattern.confidence,
            "waves": [wave.dict() for wave in pattern.waves],
            "fibonacci_levels": pattern.fibonacci_levels,
            "target_price": pattern.target_price,
            "invalidation_level": pattern.invalidation_level,
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date
        }
    else:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": "No Elliott Wave pattern detected",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date
        }


@app.get("/elliott-wave/backtest/{symbol}")
async def analyze_for_backtest(symbol: str, historical_date: str, timeframe: str = "1d"):
    """Analyze a symbol for Elliott Wave patterns at a specific historical date (for backtesting)"""
    if symbol.upper() not in TRACKED_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not tracked")
    
    start_time = time.time()
    
    # Validate historical_date format
    try:
        from datetime import datetime
        datetime.strptime(historical_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="historical_date must be in YYYY-MM-DD format")
    
    # Get historical market data for backtesting
    data = get_market_data_for_backtest(symbol, timeframe, historical_date, limit=2000)
    
    if data.empty:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": f"No historical market data available for {symbol} up to {historical_date}",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date,
            "backtest_mode": True
        }
    
    logger.info(f"Backtesting analysis for {symbol} with {len(data)} data points up to {historical_date}")
    
    # Detect swing points
    swing_points = elliott_detector.detect_swing_points(data)
    
    if len(swing_points) < 5:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": f"Insufficient swing points for pattern detection (found {len(swing_points)})",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date,
            "backtest_mode": True
        }
    
    # Identify wave pattern
    pattern = elliott_detector.identify_wave_pattern(swing_points)
    
    if pattern:
        pattern.symbol = symbol.upper()
        pattern.timeframe = timeframe
        
        return {
            "symbol": symbol.upper(),
            "pattern_found": True,
            "pattern_type": pattern.pattern_type.value,
            "confidence": pattern.confidence,
            "waves": [wave.dict() for wave in pattern.waves],
            "fibonacci_levels": pattern.fibonacci_levels,
            "target_price": pattern.target_price,
            "invalidation_level": pattern.invalidation_level,
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date,
            "backtest_mode": True,
            "data_points": len(data),
            "swing_points": len(swing_points)
        }
    else:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": "No Elliott Wave pattern detected",
            "analysis_time": time.time() - start_time,
            "historical_date": historical_date,
            "backtest_mode": True,
            "data_points": len(data),
            "swing_points": len(swing_points)
        }


@app.get("/elliott-wave/analyze-all")
async def analyze_all_symbols():
    """Analyze all tracked symbols for Elliott Wave patterns"""
    results = []
    patterns_found = 0
    
    for symbol in TRACKED_SYMBOLS:
        result = await analyze_single_symbol(symbol)
        results.append(result)
        
        if result["pattern_found"]:
            patterns_found += 1
    
    return {
        "total_symbols": len(TRACKED_SYMBOLS),
        "patterns_found": patterns_found,
        "patterns": [r for r in results if r["pattern_found"]],
        "summary": f"Found {patterns_found} Elliott Wave patterns across {len(TRACKED_SYMBOLS)} symbols"
    }


@app.get("/elliott-wave/options-analysis/{symbol}")
async def analyze_options_single_symbol(symbol: str):
    """Analyze a single symbol for options trading opportunities"""
    if symbol.upper() not in TRACKED_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not tracked")
    
    start_time = time.time()
    
    # Get Elliott Wave analysis
    wave_result = await analyze_single_symbol(symbol)
    
    if not wave_result["pattern_found"]:
        return {
            "symbol": symbol.upper(),
            "options_signals": [],
            "trading_plan": {
                "symbol": symbol.upper(),
                "primary_signal": None,
                "recommended_strategy": "No pattern detected",
                "strategy_config": {},
                "strike_selection": {},
                "risk_management": {"risk_level": "low", "max_position_size": 0.01}
            },
            "analysis_time": time.time() - start_time
        }
    
    # Generate options analysis
    current_price = 100.0
    pattern = wave_result.get("pattern")  # Get the actual pattern from the analysis
    trading_plan = options_integrator.generate_options_trading_plan(symbol.upper(), pattern, current_price)
    
    return {
        "symbol": symbol.upper(),
        "options_signals": [],
        "trading_plan": trading_plan,
        "analysis_time": time.time() - start_time
    }


@app.get("/elliott-wave/options-analysis-all")
async def analyze_options_all_symbols():
    """Analyze all tracked symbols for options trading opportunities"""
    results = []
    symbols_with_signals = 0
    
    for symbol in TRACKED_SYMBOLS:
        result = await analyze_options_single_symbol(symbol)
        results.append(result)
        
        if result["options_signals"]:
            symbols_with_signals += 1
    
    return {
        "total_symbols_analyzed": len(TRACKED_SYMBOLS),
        "symbols_with_options_signals": symbols_with_signals,
        "options_opportunities": results,
        "summary": f"Found options opportunities for {symbols_with_signals} out of {len(TRACKED_SYMBOLS)} symbols"
    }


@app.get("/elliott-wave/health")
async def health_check():
    """Health check endpoint"""
    try:
        return HealthCheckResponse(
            status="healthy",
            service="Elliott Wave Analysis",
            timestamp=datetime.now(),
            market_data_available=True,
            options_integration=True
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            service="Elliott Wave Analysis",
            timestamp=datetime.now(),
            market_data_available=False,
            options_integration=False
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )