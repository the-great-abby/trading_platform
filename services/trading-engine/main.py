#!/usr/bin/env python3
"""
Fixed Trading Engine Service with Real Prometheus Metrics
"""
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn

# Add src to path for imports
sys.path.append('/app/src')

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import our metrics
from metrics import TradingEngineMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/trading_engine.log')
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app for metrics endpoint
app = FastAPI(title="Trading Engine with Metrics")

# Global metrics instance
trading_metrics = TradingEngineMetrics()

# Database setup
Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0)
    strategy = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # BUY/SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = Column(String(50), nullable=False)
    value = Column(Float, nullable=False, default=0.0)  # FIX: Make this not nullable with default
    confidence = Column(Float, default=1.0)
    pnl = Column(Float, default=0.0)

class TradingConfig(Base):
    __tablename__ = "trading_config"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

@dataclass
class TradingState:
    is_running: bool = False
    start_time: Optional[datetime] = None
    portfolio_value: float = 100000.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    active_positions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.active_positions is None:
            self.active_positions = {}

class RiskManager:
    """Risk management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_position_size = config.get('max_position_size', 1000)
        self.max_daily_loss = config.get('max_daily_loss', 500)
        self.max_total_exposure = config.get('max_total_exposure', 10000)
        self.max_drawdown = config.get('max_drawdown', 0.1)
        
    def check_position_size(self, quantity: int, price: float) -> bool:
        """Check if position size is within limits"""
        position_value = abs(quantity * price)
        return position_value <= self.max_position_size
    
    def check_daily_loss(self, current_daily_pnl: float) -> bool:
        """Check daily loss limit"""
        return current_daily_pnl >= -self.max_daily_loss
    
    def check_total_exposure(self, current_exposure: float) -> bool:
        """Check total exposure limit"""
        return current_exposure <= self.max_total_exposure
    
    def check_drawdown(self, current_value: float, peak_value: float) -> bool:
        """Check drawdown limit"""
        if peak_value == 0:
            return True
        
        drawdown = (peak_value - current_value) / peak_value
        if drawdown > self.max_drawdown:
            return False
        return True

class OrderManager:
    """Order management system with fixed database operations"""
    
    def __init__(self, db_session, metrics: TradingEngineMetrics):
        self.db_session = db_session
        self.metrics = metrics
        self.pending_orders = {}
        
    async def place_order(self, symbol: str, action: str, quantity: int, price: float, strategy: str, pnl: float = 0.0) -> str:
        """Place a new order with proper database handling"""
        order_id = f"{symbol}_{action}_{int(time.time())}"
        trade_value = abs(quantity * price)
        
        try:
            # Create trade record with ALL required fields
            trade = Trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                strategy=strategy,
                value=trade_value,  # FIX: Set the value field that was missing
                confidence=1.0,     # Set confidence for executed trades
                pnl=pnl            # Use the calculated P&L
            )
            
            self.db_session.add(trade)
            self.db_session.commit()
            
            # Record in metrics
            self.metrics.record_trade(
                symbol=symbol,
                action=action, 
                quantity=quantity,
                price=price,
                strategy=strategy,
                status='executed',
                pnl=pnl
            )
            
            # Simulate order execution
            await asyncio.sleep(0.1)
            
            logger.info(f"✅ Order executed: {order_id} - {action} {quantity} {symbol} @ ${price:.2f}, P&L: ${pnl:.2f}")
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Failed to place order {order_id}: {e}")
            self.db_session.rollback()
            
            # Record failed trade in metrics
            self.metrics.record_trade(
                symbol=symbol,
                action=action,
                quantity=quantity, 
                price=price,
                strategy=strategy,
                status='failed'
            )
            raise
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades"""
        try:
            trades = self.db_session.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
            trade_dicts = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'action': trade.action,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp,
                    'strategy': trade.strategy,
                    'value': trade.value,
                    'confidence': trade.confidence,
                    'pnl': trade.pnl
                }
                trade_dicts.append(trade_dict)
            return trade_dicts
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []

class MarketDataService:
    """Market data service (simulated for now)"""
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (simulated)"""
        import random
        # Simulate realistic stock prices
        base_prices = {
            'AAPL': 180, 'MSFT': 350, 'GOOGL': 140, 
            'TSLA': 250, 'NVDA': 450, 'AMZN': 150
        }
        base_price = base_prices.get(symbol, 100)
        # Add some random movement (+/- 2%)
        movement = random.uniform(-0.02, 0.02)
        return base_price * (1 + movement)
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical price data"""
        import random
        from datetime import timedelta
        
        data = []
        base_price = self.get_current_price(symbol)
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i)
            price = base_price * random.uniform(0.95, 1.05)
            data.append({
                'date': date,
                'open': price,
                'high': price * 1.02,
                'low': price * 0.98,
                'close': price,
                'volume': 1000000
            })
        
        return data

class TradingEngine:
    """Main trading engine with real metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = TradingState()
        self.risk_manager = RiskManager(config)
        self.metrics = trading_metrics
        
        # Database setup
        database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot')
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # Services
        self.order_manager = OrderManager(self.db_session, self.metrics)
        self.market_data = MarketDataService()
        
        # Trading parameters
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
        self.strategies = config.get('strategies', ['RiskFirst', 'MarketRegimeAdaptive', 'MultiTimeframe'])
        self.trading_interval = config.get('trading_interval', 60)  # seconds
        
        logger.info(f"🚀 Trading engine initialized with {len(self.symbols)} symbols and {len(self.strategies)} strategies")
    
    async def run(self):
        """Main trading loop"""
        self.state.is_running = True
        self.state.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting trading engine with real metrics...")
        
        try:
            while self.state.is_running:
                await self.trading_cycle()
                await asyncio.sleep(self.trading_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Trading engine stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in trading engine: {e}")
            raise
        finally:
            self.state.is_running = False
            logger.info("📊 Trading engine shutdown complete")
    
    async def trading_cycle(self):
        """Single trading cycle with metrics updates"""
        try:
            # Update portfolio value
            self.update_portfolio_value()
            
            # Check risk limits
            if not self.check_risk_limits():
                logger.warning("⚠️ Risk limits exceeded, pausing trading")
                return
            
            # Generate and execute trades
            for symbol in self.symbols:
                await self.process_symbol(symbol)
            
            # Update metrics
            self.update_metrics()
            
            # Log status
            self.log_status()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            # Reset session on error to prevent rollback issues
            self.db_session.rollback()
    
    async def process_symbol(self, symbol: str):
        """Process a single symbol"""
        current_price = self.market_data.get_current_price(symbol)
        
        # Simple trading logic (replace with actual strategy)
        if self.should_buy(symbol, current_price):
            await self.execute_buy(symbol, current_price)
        elif self.should_sell(symbol, current_price):
            await self.execute_sell(symbol, current_price)
    
    def should_buy(self, symbol: str, price: float) -> bool:
        """Simple buy signal (replace with actual strategy)"""
        import random
        # Simulate 80% chance of buy signal (increased for testing)
        random_val = random.random()
        should_buy = random_val < 0.80 and symbol not in self.state.active_positions
        if should_buy:
            logger.info(f"🎯 BUY SIGNAL: {symbol} @ ${price:.2f} (random={random_val:.2f})")
        return should_buy
    
    def should_sell(self, symbol: str, price: float) -> bool:
        """Simple sell signal (replace with actual strategy)"""
        if symbol not in self.state.active_positions:
            return False
        
        position = self.state.active_positions[symbol]
        pnl_pct = (price - position['entry_price']) / position['entry_price']
        
        # Sell if profit > 2% or loss > 1%
        return pnl_pct > 0.02 or pnl_pct < -0.01
    
    async def execute_buy(self, symbol: str, price: float):
        """Execute buy order"""
        quantity = 10  # Simple fixed quantity
        strategy = "SimpleStrategy"
        
        logger.info(f"🚀 Executing BUY for {symbol} @ ${price:.2f}")
        
        if self.risk_manager.check_position_size(quantity, price):
            try:
                order_id = await self.order_manager.place_order(symbol, "BUY", quantity, price, strategy, 0.0)
                
                # Add to active positions
                self.state.active_positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'strategy': strategy,
                    'timestamp': datetime.utcnow()
                }
                
                logger.info(f"📈 BUY EXECUTED: {quantity} {symbol} @ ${price:.2f}")
                
            except Exception as e:
                logger.error(f"❌ Buy order failed for {symbol}: {e}")
        else:
            logger.warning(f"⚠️ Risk check failed for {symbol} buy order")
    
    async def execute_sell(self, symbol: str, price: float):
        """Execute sell order"""
        if symbol not in self.state.active_positions:
            return
            
        position = self.state.active_positions[symbol]
        quantity = position['quantity']
        entry_price = position['entry_price']
        strategy = position['strategy']
        
        # Calculate P&L
        pnl = (price - entry_price) * quantity
        
        try:
            order_id = await self.order_manager.place_order(symbol, "SELL", quantity, price, strategy, pnl)
            
            # Remove from active positions
            del self.state.active_positions[symbol]
            
            # Update state P&L
            self.state.total_pnl += pnl
            self.state.daily_pnl += pnl
            
            logger.info(f"📉 SELL: {quantity} {symbol} @ ${price:.2f}, P&L: ${pnl:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Sell order failed for {symbol}: {e}")
    
    def update_portfolio_value(self):
        """Update portfolio value"""
        # Calculate current positions value
        positions_value = 0.0
        for symbol, position in self.state.active_positions.items():
            current_price = self.market_data.get_current_price(symbol)
            position_value = position['quantity'] * current_price
            positions_value += position_value
        
        self.state.portfolio_value = 100000.0 + self.state.total_pnl + positions_value
    
    def update_metrics(self):
        """Update Prometheus metrics"""
        self.metrics.update_portfolio(
            total_value=self.state.portfolio_value,
            daily_pnl=self.state.daily_pnl,
            active_positions_count=len(self.state.active_positions),
            total_pnl=self.state.total_pnl
        )
        
        # Calculate risk metrics
        total_exposure = sum(
            pos['quantity'] * self.market_data.get_current_price(symbol) 
            for symbol, pos in self.state.active_positions.items()
        )
        
        max_drawdown = 0.0  # Calculate actual drawdown
        
        self.metrics.update_risk_metrics(
            total_exposure=total_exposure,
            max_drawdown_pct=max_drawdown
        )
    
    def check_risk_limits(self) -> bool:
        """Check all risk limits"""
        return (self.risk_manager.check_daily_loss(self.state.daily_pnl) and
                self.risk_manager.check_drawdown(self.state.portfolio_value, 100000.0))
    
    def log_status(self):
        """Log current status"""
        active_positions = len(self.state.active_positions)
        recent_trades = len(self.order_manager.get_recent_trades(limit=1))
        
        logger.info(f"📊 Status: Portfolio=${self.state.portfolio_value:.2f}, "
                   f"P&L=${self.state.total_pnl:.2f}, "
                   f"Trades={self.metrics.total_trades}, "
                   f"Positions={active_positions}")

# Global trading engine instance
trading_engine = None

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(trading_metrics.generate_metrics())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trading-engine",
        "uptime_seconds": (datetime.utcnow() - trading_metrics.start_time).total_seconds() if trading_metrics.start_time else 0,
        "trading_active": trading_engine.state.is_running if trading_engine else False
    }

@app.get("/stats")
async def get_stats():
    """Trading statistics endpoint"""
    stats = trading_metrics.get_stats_summary()
    if trading_engine:
        stats.update({
            "portfolio_value": trading_engine.state.portfolio_value,
            "total_pnl": trading_engine.state.total_pnl,
            "daily_pnl": trading_engine.state.daily_pnl,
            "active_positions": len(trading_engine.state.active_positions)
        })
    return stats

@app.get("/trades")
async def get_recent_trades():
    """Get recent trades"""
    if trading_engine:
        return trading_engine.order_manager.get_recent_trades(limit=20)
    return []

async def start_trading_engine():
    """Start the trading engine"""
    global trading_engine
    
    config = {
        'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
        'strategies': ['SimpleStrategy'],
        'trading_interval': 10,  # 10 seconds for testing
        'max_position_size': 5000,
        'max_daily_loss': 2000,  # Increased from 500 to allow more trading
        'max_total_exposure': 10000,  # Increased from 5000
        'max_drawdown': 0.2  # Increased from 0.1 to 20%
    }
    
    trading_engine = TradingEngine(config)
    await trading_engine.run()

async def main():
    """Main function"""
    # Start FastAPI server and trading engine concurrently
    import uvicorn
    
    # Start trading engine in background
    trading_task = asyncio.create_task(start_trading_engine())
    
    # Start FastAPI server
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        trading_task.cancel()

if __name__ == "__main__":
    import uvicorn
    import threading
    
    # Start the trading engine in a background thread
    trading_thread = threading.Thread(target=asyncio.run, args=(start_trading_engine(),))
    trading_thread.daemon = True
    trading_thread.start()
    
    # Start the web server
    uvicorn.run(app, host="0.0.0.0", port=11080)
