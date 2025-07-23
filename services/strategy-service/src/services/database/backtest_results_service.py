"""
Backtest Results Database Service
"""

import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from src.models.backtest_results import Base, BacktestRun, BacktestTrade, BacktestEquityCurve
from src.utils.database_optimizer import DatabaseOptimizer

logger = logging.getLogger(__name__)


class BacktestResultsService:
    """Service for storing and retrieving backtest results from the database"""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot"
        
        self.database_url = database_url
        
        self.engine = create_engine(
            database_url,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
        # Ensure indexes are created
        self._ensure_indexes()
        
        logger.info("Backtest results service initialized")
    
    def _ensure_indexes(self):
        """Ensure all required indexes exist for backtest tables"""
        try:
            import asyncio
            # Create database optimizer and ensure indexes
            optimizer = DatabaseOptimizer(self.database_url)
            
            # Run the async ensure_indexes in a new event loop if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule it
                    asyncio.create_task(optimizer.ensure_indexes())
                else:
                    # If we're not in an async context, run it
                    loop.run_until_complete(optimizer.ensure_indexes())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(optimizer.ensure_indexes())
                
            logger.info("✅ Backtest results indexes ensured")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to ensure indexes: {e}")
    
    def store_backtest_results(self, 
                              run_id: str,
                              strategy_name: str,
                              symbols: List[str],
                              start_date: str,
                              end_date: str,
                              result: dict,
                              database_only: bool = False,
                              data_provider: Optional[str] = None,
                              backtest_name: Optional[str] = None) -> bool:
        """
        Store backtest results in the database
        
        Args:
            run_id: Unique identifier for the backtest run
            strategy_name: Name of the strategy tested
            symbols: List of symbols tested
            start_date: Start date of the backtest
            end_date: End date of the backtest
            result: BacktestResult object containing the results
            database_only: Whether the backtest used database-only mode
            data_provider: Data provider used (optional)
            backtest_name: Name of the backtest file/strategy used (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.SessionLocal() as session:
                # Store backtest run metadata
                backtest_run = BacktestRun(
                    run_id=run_id,
                    strategy_name=strategy_name,
                    backtest_name=backtest_name,
                    symbols=json.dumps(symbols),
                    start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
                    end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
                    initial_capital=result['initial_capital'],
                    final_capital=result['final_capital'],
                    total_return=result['total_return'],
                    total_return_pct=result['total_return_pct'],
                    max_drawdown_pct=result['max_drawdown_pct'],
                    sharpe_ratio=result['sharpe_ratio'],
                    total_trades=result['total_trades'],
                    winning_trades=result['winning_trades'],
                    losing_trades=result['losing_trades'],
                    win_rate=result['win_rate'],
                    profit_factor=result['profit_factor'],
                    avg_win=result['avg_win'],
                    avg_loss=result['avg_loss'],
                    database_only=str(database_only).lower(),
                    data_provider=data_provider,
                    completed_at=datetime.now()
                )
                
                session.add(backtest_run)
                session.flush()  # Get the ID
                
                # Store individual trades
                for trade in result['trades']:
                    backtest_trade = BacktestTrade(
                        run_id=run_id,
                        timestamp=trade['timestamp'],
                        symbol=trade['symbol'],
                        action=trade['action'],
                        quantity=trade['quantity'],
                        price=trade['price'],
                        value=trade['quantity'] * trade['price'],
                        pnl=trade['pnl'],
                        confidence=trade['confidence'],
                        portfolio_value=trade['portfolio_value'],
                        cash=trade['cash'],
                        position_value=trade['position_value'],
                        total_pnl=trade['total_pnl'],
                        trade_pnl=trade['trade_pnl']
                    )
                    session.add(backtest_trade)
                
                # Store equity curve data
                if 'equity_curve' in result and result['equity_curve'] is not None and not result['equity_curve'].empty:
                    for index, row in result['equity_curve'].iterrows():
                        equity_point = BacktestEquityCurve(
                            run_id=run_id,
                            date=index.date() if hasattr(index, 'date') else index,
                            portfolio_value=row.get('portfolio_value', 0.0),
                            cash=row.get('cash', 0.0),
                            positions_value=row.get('positions_value', 0.0),
                            total_pnl=row.get('total_pnl', 0.0)
                        )
                        session.add(equity_point)
                
                session.commit()
                logger.info(f"Stored backtest results for run {run_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error storing backtest results: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing backtest results: {e}")
            return False
    
    def get_backtest_runs(self, 
                         strategy_name: Optional[str] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get backtest runs with optional filtering
        
        Args:
            strategy_name: Filter by strategy name
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            limit: Maximum number of results to return
            
        Returns:
            List of backtest run dictionaries
        """
        try:
            with self.SessionLocal() as session:
                query = session.query(BacktestRun)
                
                if strategy_name:
                    query = query.filter(BacktestRun.strategy_name == strategy_name)
                
                if start_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    query = query.filter(BacktestRun.start_date >= start_dt)
                
                if end_date:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    query = query.filter(BacktestRun.end_date <= end_dt)
                
                runs = query.order_by(BacktestRun.created_at.desc()).limit(limit).all()
                
                result = []
                for run in runs:
                    # Only parse symbols if it's a string (not a Column object)
                    symbols_value = run.symbols
                    if isinstance(symbols_value, str):
                        symbols_parsed = json.loads(symbols_value)
                    else:
                        symbols_parsed = symbols_value
                    # Only call isoformat if created_at/completed_at are datetime objects
                    created_at_value = run.created_at.isoformat() if hasattr(run.created_at, 'isoformat') else str(run.created_at)
                    completed_at_value = run.completed_at.isoformat() if (run.completed_at is not None and hasattr(run.completed_at, 'isoformat')) else None
                    result.append({
                        'run_id': run.run_id,
                        'strategy_name': run.strategy_name,
                        'backtest_name': run.backtest_name,
                        'symbols': symbols_parsed,
                        'start_date': run.start_date.isoformat(),
                        'end_date': run.end_date.isoformat(),
                        'initial_capital': run.initial_capital,
                        'final_capital': run.final_capital,
                        'total_return': run.total_return,
                        'total_return_pct': run.total_return_pct,
                        'max_drawdown_pct': run.max_drawdown_pct,
                        'sharpe_ratio': run.sharpe_ratio,
                        'total_trades': run.total_trades,
                        'winning_trades': run.winning_trades,
                        'losing_trades': run.losing_trades,
                        'win_rate': run.win_rate,
                        'profit_factor': run.profit_factor,
                        'avg_win': run.avg_win,
                        'avg_loss': run.avg_loss,
                        'database_only': run.database_only == 'true',
                        'data_provider': run.data_provider,
                        'created_at': created_at_value,
                        'completed_at': completed_at_value
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving backtest runs: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving backtest runs: {e}")
            return []
    
    def get_backtest_trades(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific backtest run
        
        Args:
            run_id: Backtest run ID
            
        Returns:
            List of trade dictionaries
        """
        try:
            with self.SessionLocal() as session:
                trades = session.query(BacktestTrade).filter(
                    BacktestTrade.run_id == run_id
                ).order_by(BacktestTrade.timestamp).all()
                
                result = []
                for trade in trades:
                    result.append({
                        'timestamp': trade.timestamp.isoformat(),
                        'symbol': trade.symbol,
                        'action': trade.action,
                        'quantity': trade.quantity,
                        'price': trade.price,
                        'value': trade.value,
                        'pnl': trade.pnl,
                        'confidence': trade.confidence,
                        'portfolio_value': trade.portfolio_value,
                        'cash': trade.cash,
                        'position_value': trade.position_value,
                        'total_pnl': trade.total_pnl,
                        'trade_pnl': trade.trade_pnl
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving trades: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving trades: {e}")
            return []
    
    def get_equity_curve(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get equity curve data for a specific backtest run
        
        Args:
            run_id: Backtest run ID
            
        Returns:
            List of equity curve data points
        """
        try:
            with self.SessionLocal() as session:
                equity_data = session.query(BacktestEquityCurve).filter(
                    BacktestEquityCurve.run_id == run_id
                ).order_by(BacktestEquityCurve.date).all()
                
                result = []
                for point in equity_data:
                    result.append({
                        'date': point.date.isoformat(),
                        'portfolio_value': point.portfolio_value,
                        'cash': point.cash,
                        'positions_value': point.positions_value,
                        'total_pnl': point.total_pnl
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving equity curve: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving equity curve: {e}")
            return []
    
    def get_strategy_performance_summary(self, strategy_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get performance summary for a specific strategy
        
        Args:
            strategy_name: Name of the strategy
            limit: Maximum number of results to return
            
        Returns:
            List of performance summaries
        """
        try:
            with self.SessionLocal() as session:
                runs = session.query(BacktestRun).filter(
                    BacktestRun.strategy_name == strategy_name
                ).order_by(BacktestRun.created_at.desc()).limit(limit).all()
                
                result = []
                for run in runs:
                    result.append({
                        'run_id': run.run_id,
                        'start_date': run.start_date.isoformat(),
                        'end_date': run.end_date.isoformat(),
                        'total_return_pct': run.total_return_pct,
                        'max_drawdown_pct': run.max_drawdown_pct,
                        'sharpe_ratio': run.sharpe_ratio,
                        'total_trades': run.total_trades,
                        'win_rate': run.win_rate,
                        'profit_factor': run.profit_factor,
                        'created_at': run.created_at.isoformat()
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving strategy performance: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving strategy performance: {e}")
            return []
    
    def delete_backtest_run(self, run_id: str) -> bool:
        """
        Delete a backtest run and all associated data
        
        Args:
            run_id: Backtest run ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.SessionLocal() as session:
                # Delete in order to respect foreign key constraints
                session.query(BacktestEquityCurve).filter(
                    BacktestEquityCurve.run_id == run_id
                ).delete()
                
                session.query(BacktestTrade).filter(
                    BacktestTrade.run_id == run_id
                ).delete()
                
                session.query(BacktestRun).filter(
                    BacktestRun.run_id == run_id
                ).delete()
                
                session.commit()
                logger.info(f"Deleted backtest run {run_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting backtest run: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting backtest run: {e}")
            return False 