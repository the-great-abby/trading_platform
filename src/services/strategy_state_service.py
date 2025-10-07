#!/usr/bin/env python3
"""
Strategy State Service
Manages strategy state persistence and retrieval from database
"""

import logging
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import StrategyConfiguration, StrategyState, StrategyPerformance, StrategySignal
from src.database.database import get_db_session

logger = logging.getLogger(__name__)

class StrategyStateService:
    """Service for managing strategy state in database"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def save_strategy_configuration(self, strategy_name: str, version: str, configuration: Dict[str, Any]) -> bool:
        """Save strategy configuration to database"""
        try:
            async with get_db_session() as session:
                # Check if configuration exists
                stmt = select(StrategyConfiguration).where(
                    StrategyConfiguration.strategy_name == strategy_name,
                    StrategyConfiguration.version == version
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing configuration
                    stmt = update(StrategyConfiguration).where(
                        StrategyConfiguration.id == existing.id
                    ).values(
                        configuration=configuration,
                        updated_at=datetime.now()
                    )
                else:
                    # Insert new configuration
                    stmt = insert(StrategyConfiguration).values(
                        strategy_name=strategy_name,
                        version=version,
                        configuration=configuration
                    )
                
                await session.execute(stmt)
                await session.commit()
                
                self.logger.info(f"✅ Saved configuration for {strategy_name} v{version}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to save strategy configuration: {e}")
            return False
    
    async def get_strategy_configuration(self, strategy_name: str, version: str = None) -> Optional[Dict[str, Any]]:
        """Get strategy configuration from database"""
        try:
            async with get_db_session() as session:
                if version:
                    stmt = select(StrategyConfiguration).where(
                        StrategyConfiguration.strategy_name == strategy_name,
                        StrategyConfiguration.version == version
                    )
                else:
                    # Get latest version
                    stmt = select(StrategyConfiguration).where(
                        StrategyConfiguration.strategy_name == strategy_name,
                        StrategyConfiguration.is_active == True
                    ).order_by(StrategyConfiguration.created_at.desc())
                
                result = await session.execute(stmt)
                config = result.scalar_one_or_none()
                
                if config:
                    return {
                        'strategy_name': config.strategy_name,
                        'version': config.version,
                        'configuration': config.configuration,
                        'created_at': config.created_at,
                        'updated_at': config.updated_at
                    }
                
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to get strategy configuration: {e}")
            return None
    
    async def save_strategy_state(self, strategy_name: str, symbol: str, state_data: Dict[str, Any]) -> bool:
        """Save strategy state to database"""
        try:
            async with get_db_session() as session:
                # Check if state exists
                stmt = select(StrategyState).where(
                    StrategyState.strategy_name == strategy_name,
                    StrategyState.symbol == symbol
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing state
                    stmt = update(StrategyState).where(
                        StrategyState.id == existing.id
                    ).values(
                        state_data=state_data,
                        updated_at=datetime.now()
                    )
                else:
                    # Insert new state
                    stmt = insert(StrategyState).values(
                        strategy_name=strategy_name,
                        symbol=symbol,
                        state_data=state_data
                    )
                
                await session.execute(stmt)
                await session.commit()
                
                self.logger.debug(f"✅ Saved state for {strategy_name} {symbol}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to save strategy state: {e}")
            return False
    
    async def get_strategy_state(self, strategy_name: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get strategy state from database"""
        try:
            async with get_db_session() as session:
                stmt = select(StrategyState).where(
                    StrategyState.strategy_name == strategy_name,
                    StrategyState.symbol == symbol
                )
                result = await session.execute(stmt)
                state = result.scalar_one_or_none()
                
                if state:
                    return {
                        'strategy_name': state.strategy_name,
                        'symbol': state.symbol,
                        'state_data': state.state_data,
                        'last_signal_time': state.last_signal_time,
                        'position_count': state.position_count,
                        'total_pnl': float(state.total_pnl),
                        'created_at': state.created_at,
                        'updated_at': state.updated_at
                    }
                
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to get strategy state: {e}")
            return None
    
    async def save_strategy_signal(self, strategy_name: str, symbol: str, signal_type: str, 
                                 confidence: float, price: float, quantity: int, 
                                 metadata: Dict[str, Any] = None) -> bool:
        """Save strategy signal to database"""
        try:
            async with get_db_session() as session:
                stmt = insert(StrategySignal).values(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=price,
                    quantity=quantity,
                    metadata=metadata or {}
                )
                
                await session.execute(stmt)
                await session.commit()
                
                self.logger.debug(f"✅ Saved signal: {strategy_name} {symbol} {signal_type}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to save strategy signal: {e}")
            return False
    
    async def get_strategy_signals(self, strategy_name: str, symbol: str = None, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get strategy signals from database"""
        try:
            async with get_db_session() as session:
                stmt = select(StrategySignal).where(
                    StrategySignal.strategy_name == strategy_name
                )
                
                if symbol:
                    stmt = stmt.where(StrategySignal.symbol == symbol)
                
                stmt = stmt.order_by(StrategySignal.timestamp.desc()).limit(limit)
                
                result = await session.execute(stmt)
                signals = result.scalars().all()
                
                return [
                    {
                        'id': signal.id,
                        'strategy_name': signal.strategy_name,
                        'symbol': signal.symbol,
                        'signal_type': signal.signal_type,
                        'confidence': float(signal.confidence),
                        'price': float(signal.price),
                        'quantity': signal.quantity,
                        'metadata': signal.metadata,
                        'timestamp': signal.timestamp
                    }
                    for signal in signals
                ]
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to get strategy signals: {e}")
            return []
    
    async def update_strategy_performance(self, strategy_name: str, symbol: str, 
                                        performance_data: Dict[str, Any]) -> bool:
        """Update strategy performance metrics"""
        try:
            async with get_db_session() as session:
                today = date.today()
                
                # Check if performance record exists
                stmt = select(StrategyPerformance).where(
                    StrategyPerformance.strategy_name == strategy_name,
                    StrategyPerformance.symbol == symbol,
                    StrategyPerformance.date == today
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    stmt = update(StrategyPerformance).where(
                        StrategyPerformance.id == existing.id
                    ).values(
                        total_trades=performance_data.get('total_trades', 0),
                        winning_trades=performance_data.get('winning_trades', 0),
                        total_pnl=performance_data.get('total_pnl', 0.0),
                        max_drawdown=performance_data.get('max_drawdown', 0.0),
                        sharpe_ratio=performance_data.get('sharpe_ratio', 0.0),
                        win_rate=performance_data.get('win_rate', 0.0)
                    )
                else:
                    # Insert new record
                    stmt = insert(StrategyPerformance).values(
                        strategy_name=strategy_name,
                        symbol=symbol,
                        date=today,
                        total_trades=performance_data.get('total_trades', 0),
                        winning_trades=performance_data.get('winning_trades', 0),
                        total_pnl=performance_data.get('total_pnl', 0.0),
                        max_drawdown=performance_data.get('max_drawdown', 0.0),
                        sharpe_ratio=performance_data.get('sharpe_ratio', 0.0),
                        win_rate=performance_data.get('win_rate', 0.0)
                    )
                
                await session.execute(stmt)
                await session.commit()
                
                self.logger.debug(f"✅ Updated performance for {strategy_name} {symbol}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to update strategy performance: {e}")
            return False
    
    async def get_strategy_performance(self, strategy_name: str, symbol: str = None, 
                                     days: int = 30) -> List[Dict[str, Any]]:
        """Get strategy performance metrics"""
        try:
            async with get_db_session() as session:
                stmt = select(StrategyPerformance).where(
                    StrategyPerformance.strategy_name == strategy_name
                )
                
                if symbol:
                    stmt = stmt.where(StrategyPerformance.symbol == symbol)
                
                stmt = stmt.order_by(StrategyPerformance.date.desc()).limit(days)
                
                result = await session.execute(stmt)
                performance = result.scalars().all()
                
                return [
                    {
                        'strategy_name': perf.strategy_name,
                        'symbol': perf.symbol,
                        'date': perf.date,
                        'total_trades': perf.total_trades,
                        'winning_trades': perf.winning_trades,
                        'total_pnl': float(perf.total_pnl),
                        'max_drawdown': float(perf.max_drawdown),
                        'sharpe_ratio': float(perf.sharpe_ratio),
                        'win_rate': float(perf.win_rate)
                    }
                    for perf in performance
                ]
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Failed to get strategy performance: {e}")
            return []

# Global instance
strategy_state_service = StrategyStateService()
