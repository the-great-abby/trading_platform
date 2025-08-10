#!/usr/bin/env python3
"""
Dedicated Trading Engine Service
This service runs independently from the web dashboard and handles all trading operations
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

# Add src to path for imports
sys.path.append('/app/src')

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

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
    # Note: order_id, status, commission columns don't exist in existing schema
    # We'll use existing columns: value, confidence, pnl

class TradingConfig(Base):
    __tablename__ = "trading_config"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

@dataclass
class TradingState:
    """Current trading state"""
    is_running: bool = False
    start_time: Optional[datetime] = None
    total_trades: int = 0
    total_pnl: float = 0.0
    portfolio_value: float = 100000.0  # Starting capital
    active_positions: Dict[str, Dict] = None
    last_trade: Optional[Dict] = None
    
    def __post_init__(self):
        if self.active_positions is None:
            self.active_positions = {}

class RiskManager:
    """Risk management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_position_size = config.get('max_position_size', 0.05)  # 5% per position
        self.max_daily_loss = config.get('max_daily_loss', 0.02)  # 2% daily loss limit
        self.max_drawdown = config.get('max_drawdown', 0.10)  # 10% max drawdown
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.01)  # 1% per trade
        
    def check_position_size(self, symbol: str, quantity: int, price: float, portfolio_value: float) -> bool:
        """Check if position size is within limits"""
        position_value = abs(quantity * price)
        position_pct = position_value / portfolio_value
        
        if position_pct > self.max_position_size:
            logger.warning(f"Position size {position_pct:.2%} exceeds limit {self.max_position_size:.2%}")
            return False
        return True
    
    def check_daily_loss(self, daily_pnl: float, portfolio_value: float) -> bool:
        """Check if daily loss is within limits"""
        daily_loss_pct = abs(daily_pnl) / portfolio_value if daily_pnl < 0 else 0
        
        if daily_loss_pct > self.max_daily_loss:
            logger.warning(f"Daily loss {daily_loss_pct:.2%} exceeds limit {self.max_daily_loss:.2%}")
            return False
        return True
    
    def check_drawdown(self, current_value: float, peak_value: float) -> bool:
        """Check if drawdown is within limits"""
        if peak_value <= 0:
            return True
            
        drawdown = (peak_value - current_value) / peak_value
        
        if drawdown > self.max_drawdown:
            logger.warning(f"Drawdown {drawdown:.2%} exceeds limit {self.max_drawdown:.2%}")
            return False
        return True

class OrderManager:
    """Order management system"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.pending_orders = {}
        
    async def place_order(self, symbol: str, action: str, quantity: int, price: float, strategy: str) -> str:
        """Place a new order"""
        order_id = f"{symbol}_{action}_{int(time.time())}"
        
        # Create trade record using existing schema
        trade = Trade(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            strategy=strategy
        )
        
        self.db_session.add(trade)
        self.db_session.commit()
        
        # Simulate order execution (in real system, this would call broker API)
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Update trade with value and confidence (using existing columns)
        trade.value = abs(quantity * price)
        # We'll set confidence to 1.0 for filled orders
        self.db_session.commit()
        
        logger.info(f"Order executed: {order_id} - {action} {quantity} {symbol} @ {price}")
        return order_id
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades"""
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
                'value': getattr(trade, 'value', 0.0),
                'confidence': getattr(trade, 'confidence', 1.0),
                'pnl': getattr(trade, 'pnl', 0.0)
            }
            trade_dicts.append(trade_dict)
        return trade_dicts

class MarketDataService:
    """Market data service (simulated for now)"""
    
    def __init__(self):
        self.price_cache = {}
        self.base_prices = {
            'AAPL': 150.0, 'MSFT': 300.0, 'GOOGL': 2800.0, 
            'TSLA': 250.0, 'NVDA': 400.0, 'AMZN': 3300.0
        }
        
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (simulated)"""
        if symbol not in self.price_cache:
            self.price_cache[symbol] = self.base_prices.get(symbol, 100.0)
        
        # Simulate price movement
        import random
        change = random.uniform(-0.02, 0.02)  # ±2% change
        self.price_cache[symbol] *= (1 + change)
        
        return round(self.price_cache[symbol], 2)
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical data (simulated)"""
        # Simulate historical data
        data = []
        base_price = self.base_prices.get(symbol, 100.0)
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            price = base_price * (1 + (i * 0.001))  # Gradual increase
            data.append({
                'date': date,
                'price': round(price, 2),
                'volume': 1000000
            })
        
        return data

class TradingEngine:
    """Main trading engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = TradingState()
        self.risk_manager = RiskManager(config)
        
        # Database setup
        database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot')
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # Services
        self.order_manager = OrderManager(self.db_session)
        self.market_data = MarketDataService()
        
        # Trading parameters
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
        self.strategies = config.get('strategies', ['RiskFirst', 'MarketRegimeAdaptive', 'MultiTimeframe'])
        self.trading_interval = config.get('trading_interval', 60)  # seconds
        
        logger.info(f"Trading engine initialized with {len(self.symbols)} symbols and {len(self.strategies)} strategies")
    
    async def run(self):
        """Main trading loop"""
        self.state.is_running = True
        self.state.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting trading engine...")
        
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
        """Single trading cycle"""
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
            
            # Log status
            self.log_status()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
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
        # Simulate 10% chance of buy signal
        return random.random() < 0.1 and symbol not in self.state.active_positions
    
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
        # Calculate position size
        max_position_value = self.state.portfolio_value * self.config['max_position_size']
        quantity = int(max_position_value / price)
        
        if quantity <= 0:
            return
        
        # Check risk limits
        if not self.risk_manager.check_position_size(symbol, quantity, price, self.state.portfolio_value):
            return
        
        # Place order
        order_id = await self.order_manager.place_order(symbol, "BUY", quantity, price, "SimpleStrategy")
        
        # Update position
        self.state.active_positions[symbol] = {
            'quantity': quantity,
            'entry_price': price,
            'entry_time': datetime.utcnow(),
            'order_id': order_id
        }
        
        self.state.total_trades += 1
        self.state.last_trade = {
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.utcnow()
        }
        
        logger.info(f"📈 BUY: {quantity} {symbol} @ {price}")
    
    async def execute_sell(self, symbol: str, price: float):
        """Execute sell order"""
        if symbol not in self.state.active_positions:
            return
        
        position = self.state.active_positions[symbol]
        quantity = position['quantity']
        
        # Place order
        order_id = await self.order_manager.place_order(symbol, "SELL", quantity, price, "SimpleStrategy")
        
        # Calculate P&L
        pnl = (price - position['entry_price']) * quantity
        self.state.total_pnl += pnl
        
        # Remove position
        del self.state.active_positions[symbol]
        
        self.state.total_trades += 1
        self.state.last_trade = {
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'pnl': pnl,
            'timestamp': datetime.utcnow()
        }
        
        logger.info(f"📉 SELL: {quantity} {symbol} @ {price} (P&L: {pnl:.2f})")
    
    def update_portfolio_value(self):
        """Update portfolio value based on current positions"""
        total_value = self.state.portfolio_value + self.state.total_pnl
        
        # Add unrealized P&L from active positions
        for symbol, position in self.state.active_positions.items():
            current_price = self.market_data.get_current_price(symbol)
            unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
            total_value += unrealized_pnl
        
        self.state.portfolio_value = total_value
    
    def check_risk_limits(self) -> bool:
        """Check all risk limits"""
        # Check daily loss
        if not self.risk_manager.check_daily_loss(self.state.total_pnl, self.state.portfolio_value):
            return False
        
        # Check drawdown (simplified)
        peak_value = self.config.get('initial_capital', 100000.0)
        if not self.risk_manager.check_drawdown(self.state.portfolio_value, peak_value):
            return False
        
        return True
    
    def log_status(self):
        """Log current trading status"""
        logger.info(f"📊 Status: Portfolio=${self.state.portfolio_value:.2f}, "
                   f"P&L=${self.state.total_pnl:.2f}, "
                   f"Trades={self.state.total_trades}, "
                   f"Positions={len(self.state.active_positions)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            'is_running': self.state.is_running,
            'start_time': self.state.start_time.isoformat() if self.state.start_time else None,
            'total_trades': self.state.total_trades,
            'total_pnl': self.state.total_pnl,
            'portfolio_value': self.state.portfolio_value,
            'active_positions': len(self.state.active_positions),
            'last_trade': self.state.last_trade,
            'symbols': self.symbols,
            'strategies': self.strategies
        }
    
    def stop(self):
        """Stop the trading engine"""
        self.state.is_running = False
        logger.info("🛑 Trading engine stop requested")

async def main():
    """Main function"""
    # Default configuration
    config = {
        'initial_capital': 100000.0,
        'max_position_size': 0.05,
        'max_risk_per_trade': 0.01,
        'max_daily_loss': 0.02,
        'max_drawdown': 0.10,
        'trading_interval': 60,
        'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
        'strategies': ['RiskFirst', 'MarketRegimeAdaptive', 'MultiTimeframe']
    }
    
    # Load config from environment or file
    config_file = os.getenv('TRADING_CONFIG_FILE')
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
            logger.info(f"📋 Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Could not load config from {config_file}: {e}")
    
    # Create and run trading engine
    engine = TradingEngine(config)
    
    try:
        await engine.run()
    except KeyboardInterrupt:
        logger.info("🛑 Trading engine stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in trading engine: {e}")
        raise

if __name__ == "__main__":
    # Create logs directory
    os.makedirs('/app/logs', exist_ok=True)
    
    # Run the trading engine
    asyncio.run(main()) 