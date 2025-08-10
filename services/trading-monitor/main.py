#!/usr/bin/env python3
"""
Trading Engine Monitor Service
Provides web interface to monitor trading engine status, positions, and performance
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Add src to path for imports
sys.path.append('/app/src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Trading Engine Monitor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="/app/templates")

# Database setup
database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

# Pydantic models
class TradingStatus(BaseModel):
    is_running: bool
    start_time: Optional[str]
    total_trades: int
    total_pnl: float
    portfolio_value: float
    active_positions: int
    last_trade: Optional[Dict]

class Position(BaseModel):
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    strategy: str
    timestamp: str

class Trade(BaseModel):
    symbol: str
    action: str
    quantity: int
    price: float
    timestamp: str
    strategy: str
    order_id: str
    status: str
    commission: float

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("trading_monitor.html", {"request": request})

@app.get("/api/status")
async def get_status() -> TradingStatus:
    """Get current trading engine status"""
    try:
        # Get basic status from database
        session = Session()
        
        # Count total trades
        result = session.execute(text("SELECT COUNT(*) FROM trades"))
        total_trades = result.scalar() or 0
        
        # Calculate total P&L from pnl column
        result = session.execute(text("""
            SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL
        """))
        total_pnl = result.scalar() or 0.0
        
        # Count active positions
        result = session.execute(text("SELECT COUNT(*) FROM positions WHERE is_active = true"))
        active_positions = result.scalar() or 0
        
        # Get last trade
        result = session.execute(text("""
            SELECT symbol, action, quantity, price, timestamp, strategy, pnl
            FROM trades ORDER BY timestamp DESC LIMIT 1
        """))
        last_trade_row = result.fetchone()
        last_trade = None
        if last_trade_row:
            last_trade = {
                'symbol': last_trade_row[0],
                'action': last_trade_row[1],
                'quantity': last_trade_row[2],
                'price': float(last_trade_row[3]),
                'timestamp': last_trade_row[4].isoformat() if last_trade_row[4] else None,
                'strategy': last_trade_row[5],
                'order_id': f"trade_{last_trade_row[2]}",  # Generate order_id from quantity
                'status': 'FILLED',  # Assume filled for existing trades
                'commission': 0.0  # No commission data in existing schema
            }
        
        session.close()
        
        # Simulate running status (in real system, check actual trading engine)
        is_running = True  # Assume running if we can query database
        
        return TradingStatus(
            is_running=is_running,
            start_time=datetime.now().isoformat(),
            total_trades=total_trades,
            total_pnl=total_pnl,
            portfolio_value=100000.0 + total_pnl,  # Starting capital + P&L
            active_positions=active_positions,
            last_trade=last_trade
        )
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions() -> List[Position]:
    """Get current positions"""
    try:
        session = Session()
        result = session.execute(text("""
            SELECT symbol, quantity, entry_price, current_price, pnl, strategy, timestamp
            FROM positions WHERE is_active = true
        """))
        
        positions = []
        for row in result.fetchall():
            positions.append(Position(
                symbol=row[0],
                quantity=row[1],
                entry_price=float(row[2]),
                current_price=float(row[3]),
                pnl=float(row[4]),
                strategy=row[5],
                timestamp=row[6].isoformat() if row[6] else None
            ))
        
        session.close()
        return positions
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
async def get_trades(limit: int = 50) -> List[Trade]:
    """Get recent trades"""
    try:
        session = Session()
        result = session.execute(text(f"""
            SELECT symbol, action, quantity, price, timestamp, strategy, pnl
            FROM trades ORDER BY timestamp DESC LIMIT {limit}
        """))
        
        trades = []
        for row in result.fetchall():
            trades.append(Trade(
                symbol=row[0],
                action=row[1],
                quantity=row[2],
                price=float(row[3]),
                timestamp=row[4].isoformat() if row[4] else None,
                strategy=row[5],
                order_id=f"trade_{row[2]}",  # Generate order_id from quantity
                status='FILLED',  # Assume filled for existing trades
                commission=0.0  # No commission data in existing schema
            ))
        
        session.close()
        return trades
        
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance():
    """Get performance metrics"""
    try:
        session = Session()
        
        # Daily P&L
        result = session.execute(text("""
            SELECT DATE(timestamp) as date, 
                   SUM(pnl) as daily_pnl
            FROM trades 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
            AND pnl IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY date
        """))
        
        daily_pnl = []
        for row in result.fetchall():
            daily_pnl.append({
                'date': row[0].isoformat() if row[0] else None,
                'pnl': float(row[1]) if row[1] else 0.0
            })
        
        # Win rate
        result = session.execute(text("""
            SELECT 
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(*) as total_trades
            FROM trades 
            WHERE pnl IS NOT NULL
        """))
        
        win_stats = result.fetchone()
        win_rate = (win_stats[0] / win_stats[1] * 100) if win_stats[1] > 0 else 0
        
        session.close()
        
        return {
            'daily_pnl': daily_pnl,
            'win_rate': win_rate,
            'total_trades': win_stats[1] if win_stats else 0,
            'winning_trades': win_stats[0] if win_stats else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 