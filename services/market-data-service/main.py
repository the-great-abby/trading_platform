"""
Market Data Service - Internal microservice for market data operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import sys
import asyncio

# Add the src directory to the path to import our services
sys.path.append('/app')

from src.services.market_data.yahoo_finance_service import YahooFinanceService
from src.services.database.market_data_service import MarketDataService
from src.utils.config import get_config
from src.utils.trading_config import get_symbols

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Data Service", version="1.0.0")

# Initialize the Yahoo Finance service
yahoo_service = YahooFinanceService(rate_limit_delay=0.1)

class MarketDataRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    interval: Optional[str] = "1d"

class MarketDataResponse(BaseModel):
    symbol: str
    data: List[Dict[str, Any]]
    count: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "market-data-service"}

@app.get("/status")
async def get_status():
    """Get market data service status"""
    return {
        "service": "market-data-service",
        "version": "1.0.0",
        "status": "operational",
        "data_source": "Yahoo Finance"
    }

@app.post("/market-data/historical", response_model=MarketDataResponse)
async def get_historical_data(request: MarketDataRequest):
    """Get historical market data from Yahoo Finance"""
    try:
        # Set default dates if not provided
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = request.start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        interval = request.interval or "1d"
        
        logger.info(f"Fetching historical data for {request.symbol} from {start_date} to {end_date}")
        
        # Get real data from Yahoo Finance
        data = yahoo_service.get_historical_data(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        if data is None or data.empty:
            logger.warning(f"No data returned for {request.symbol}")
            raise HTTPException(status_code=404, detail=f"No data available for {request.symbol}")
        
        # Convert DataFrame to list of dictionaries
        data_list = []
        for index, row in data.iterrows():
            # Handle the index properly
            if hasattr(index, 'strftime'):
                date_str = index.strftime("%Y-%m-%d")
            else:
                date_str = str(index)
            
            data_dict = {
                "date": date_str,
                "open": float(row.get('OPEN', 0) or 0),
                "high": float(row.get('HIGH', 0) or 0),
                "low": float(row.get('LOW', 0) or 0),
                "close": float(row.get('CLOSE', 0) or 0),
                "volume": int(row.get('VOLUME', 0) or 0),
                "symbol": request.symbol
            }
            data_list.append(data_dict)
        
        logger.info(f"Successfully retrieved {len(data_list)} records for {request.symbol}")
        
        return MarketDataResponse(
            symbol=request.symbol,
            data=data_list,
            count=len(data_list)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get historical data for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")

@app.get("/market-data/current/{symbol}")
async def get_current_price(symbol: str):
    """Get current market price from Yahoo Finance"""
    try:
        logger.info(f"Fetching current price for {symbol}")
        
        # Get real current price
        current_price = yahoo_service.get_live_price(symbol)
        
        if current_price is None:
            logger.warning(f"No current price available for {symbol}")
            raise HTTPException(status_code=404, detail=f"No current price available for {symbol}")
        
        # Get symbol info for additional data
        symbol_info = yahoo_service.get_symbol_info(symbol)
        
        # Calculate change (mock for now since we don't have previous close)
        price_change = 0.0
        change_percent = 0.0
        
        if symbol_info and 'current_price' in symbol_info:
            # Use previous close if available
            previous_close = symbol_info.get('previous_close', current_price)
            price_change = current_price - previous_close
            change_percent = (price_change / previous_close) * 100 if previous_close > 0 else 0
        
        return {
            "symbol": symbol,
            "price": current_price,
            "timestamp": datetime.now().isoformat(),
            "change": price_change,
            "change_percent": change_percent,
            "volume": symbol_info.get('volume', 0) if symbol_info else 0,
            "market_cap": symbol_info.get('market_cap', 0) if symbol_info else 0,
            "currency": symbol_info.get('currency', 'USD') if symbol_info else 'USD'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current price: {str(e)}")

@app.get("/market-data/symbols")
async def get_available_symbols():
    """Get list of available symbols"""
    # Real symbols we track
    symbols = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "NFLX", "name": "Netflix Inc."},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
        {"symbol": "JNJ", "name": "Johnson & Johnson"},
        {"symbol": "V", "name": "Visa Inc."},
        {"symbol": "PG", "name": "Procter & Gamble Co."},
        {"symbol": "UNH", "name": "UnitedHealth Group Inc."},
        {"symbol": "HD", "name": "Home Depot Inc."},
        {"symbol": "MA", "name": "Mastercard Inc."},
        {"symbol": "DIS", "name": "Walt Disney Co."},
        {"symbol": "PYPL", "name": "PayPal Holdings Inc."},
        {"symbol": "ADBE", "name": "Adobe Inc."}
    ]
    
    return {"symbols": symbols, "count": len(symbols)}

@app.get("/market-data/symbols/{symbol}/info")
async def get_symbol_info(symbol: str):
    """Get detailed information about a symbol"""
    try:
        logger.info(f"Fetching symbol info for {symbol}")
        
        symbol_info = yahoo_service.get_symbol_info(symbol)
        
        if symbol_info is None:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        return symbol_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbol info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbol info: {str(e)}")

@app.get("/market-data/symbols/{symbol}/validate")
async def validate_symbol(symbol: str):
    """Validate if a symbol exists and is tradeable"""
    try:
        logger.info(f"Validating symbol {symbol}")
        
        is_valid = yahoo_service.validate_symbol(symbol)
        
        return {
            "symbol": symbol,
            "is_valid": is_valid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to validate symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate symbol: {str(e)}")

@app.get("/market-data/batch/current")
async def get_batch_current_prices(symbols: str):
    """Get current prices for multiple symbols"""
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        logger.info(f"Fetching batch prices for {len(symbol_list)} symbols")
        
        results = {}
        for symbol in symbol_list:
            try:
                price = yahoo_service.get_live_price(symbol)
                if price is not None:
                    results[symbol] = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success"
                    }
                else:
                    results[symbol] = {
                        "price": None,
                        "timestamp": datetime.now().isoformat(),
                        "status": "no_data"
                    }
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol}: {e}")
                results[symbol] = {
                    "price": None,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "symbols": results,
            "total_requested": len(symbol_list),
            "successful": len([r for r in results.values() if r["status"] == "success"]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get batch prices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch prices: {str(e)}")

@app.get("/market-data/market-hours")
async def get_market_hours():
    """Get current market hours information"""
    try:
        market_hours = yahoo_service.get_market_hours()
        return {
            "market_hours": market_hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get market hours: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market hours: {str(e)}")

async def get_market_data():
    """Get market data for all symbols"""
    config = get_config()
    
    # Initialize services
    market_data_service = MarketDataService(config.database_url)
    
    # Use centralized symbol list
    symbols = get_symbols()
    
    # Calculate date range (1 year ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"📊 Getting market data for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # ... existing code ...

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
