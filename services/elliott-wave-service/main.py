#!/usr/bin/env python3
"""
Elliott Wave Analysis Service - Main Application
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import ElliottWavePattern, WaveType, HealthCheckResponse
from .advanced_pattern_detection import AdvancedElliottWaveDetector
from .options_integration import ElliottWaveOptionsIntegrator

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
TRACKED_SYMBOLS = ["SPY", "QQQ", "AAPL"]


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
async def analyze_single_symbol(symbol: str, timeframe: str = "15m"):
    """Analyze a single symbol for Elliott Wave patterns"""
    if symbol.upper() not in TRACKED_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not tracked")
    
    start_time = time.time()
    
    # Mock data for testing
    dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
    prices = [100 + i * 0.5 for i in range(100)]
    
    data = pd.DataFrame({
        'timestamp': dates,
        'High': prices,
        'Low': [p - 1 for p in prices],
        'Close': [p - 0.5 for p in prices],
        'Volume': [1000 + i * 10 for i in range(len(prices))]
    })
    
    # Detect swing points
    swing_points = elliott_detector.detect_swing_points(data)
    
    if len(swing_points) < 5:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": "Insufficient swing points for pattern detection",
            "analysis_time": time.time() - start_time
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
            "analysis_time": time.time() - start_time
        }
    else:
        return {
            "symbol": symbol.upper(),
            "pattern_found": False,
            "message": "No Elliott Wave pattern detected",
            "analysis_time": time.time() - start_time
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
    trading_plan = options_integrator.generate_options_trading_plan(symbol.upper(), None, current_price)
    
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