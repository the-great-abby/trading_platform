"""
Backtest Results Models for PostgreSQL Storage
"""

from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Text, Index, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional

Base = declarative_base()


class BacktestRun(Base):
    """Backtest run metadata storage model"""
    
    __tablename__ = 'backtest_runs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Run metadata
    run_id = Column(String(50), nullable=False, unique=True)  # Unique identifier for the run
    strategy_name = Column(String(100), nullable=False)
    backtest_name = Column(String(200), nullable=True)  # Name of the backtest file/strategy used
    symbols = Column(Text, nullable=False)  # JSON array of symbols
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Performance metrics
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    
    # Trade metrics
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    avg_win = Column(Float, nullable=False)
    avg_loss = Column(Float, nullable=False)
    
    # Configuration
    database_only = Column(String(5), nullable=False, default='false')  # 'true' or 'false'
    data_provider = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_run_id', 'run_id'),
        Index('idx_strategy', 'strategy_name'),
        Index('idx_backtest_name', 'backtest_name'),
        Index('idx_date_range', 'start_date', 'end_date'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BacktestRun(run_id='{self.run_id}', strategy='{self.strategy_name}', backtest='{self.backtest_name}', return={self.total_return_pct:.2f}%)>"


class BacktestTrade(Base):
    """Individual trade storage model"""
    
    __tablename__ = 'backtest_trades'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to backtest run
    run_id = Column(String(50), nullable=False)
    
    # Trade details
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    value = Column(Float, nullable=False)  # quantity * price
    
    # P&L and portfolio info
    pnl = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.5)
    portfolio_value = Column(Float, nullable=False, default=0.0)
    cash = Column(Float, nullable=False, default=0.0)
    position_value = Column(Float, nullable=False, default=0.0)
    total_pnl = Column(Float, nullable=False, default=0.0)
    trade_pnl = Column(Float, nullable=False, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_run_id', 'run_id'),
        Index('idx_symbol', 'symbol'),
        Index('idx_timestamp', 'timestamp'),
        Index('idx_action', 'action'),
    )
    
    def __repr__(self):
        return f"<BacktestTrade(run_id='{self.run_id}', symbol='{self.symbol}', action='{self.action}', pnl={self.pnl:.2f})>"


class BacktestEquityCurve(Base):
    """Equity curve data storage model"""
    
    __tablename__ = 'backtest_equity_curves'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to backtest run
    run_id = Column(String(50), nullable=False)
    
    # Equity curve data
    date = Column(Date, nullable=False)
    portfolio_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False, default=0.0)
    positions_value = Column(Float, nullable=False, default=0.0)
    total_pnl = Column(Float, nullable=False, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_run_id', 'run_id'),
        Index('idx_date', 'date'),
    )
    
    def __repr__(self):
        return f"<BacktestEquityCurve(run_id='{self.run_id}', date='{self.date}', value={self.portfolio_value:.2f})>" 