#!/usr/bin/env python3
"""
Strategy State Management Database Implementation
Stores strategy state, performance metrics, and configuration in database
"""

import logging
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyStateManager:
    """Manages strategy state persistence in database"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.src_dir = self.base_dir / "src"
        
    def create_strategy_state_database(self):
        """Create strategy state management database schema and service"""
        logger.info("🔧 Creating strategy state management database...")
        
        # Create database schema
        self.create_database_schema()
        
        # Create strategy state service
        self.create_strategy_state_service()
        
        # Create migration
        self.create_migration()
        
        logger.info("✅ Strategy state management database created")
    
    def create_database_schema(self):
        """Create database schema for strategy state"""
        logger.info("🔧 Creating database schema...")
        
        schema_path = self.src_dir / "database" / "migrations" / "strategy_state_schema.sql"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        schema_sql = '''-- Strategy State Management Schema
-- Stores strategy configuration, state, and performance metrics

-- Strategy configurations table
CREATE TABLE IF NOT EXISTS strategy_configurations (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, version)
);

-- Strategy state table
CREATE TABLE IF NOT EXISTS strategy_states (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    state_data JSONB NOT NULL,
    last_signal_time TIMESTAMP WITH TIME ZONE,
    position_count INTEGER DEFAULT 0,
    total_pnl DECIMAL(15,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, symbol)
);

-- Strategy performance metrics table
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15,2) DEFAULT 0.0,
    max_drawdown DECIMAL(8,4) DEFAULT 0.0,
    sharpe_ratio DECIMAL(8,4) DEFAULT 0.0,
    win_rate DECIMAL(8,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, symbol, date)
);

-- Strategy signals table
CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- BUY, SELL, HOLD
    confidence DECIMAL(8,4) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_strategy_states_name_symbol ON strategy_states(strategy_name, symbol);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_name_date ON strategy_performance(strategy_name, date);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_timestamp ON strategy_signals(timestamp);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_name_symbol ON strategy_signals(strategy_name, symbol);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_strategy_configurations_updated_at 
    BEFORE UPDATE ON strategy_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_states_updated_at 
    BEFORE UPDATE ON strategy_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
'''
        
        schema_path.write_text(schema_sql)
        logger.info(f"✅ Created database schema at {schema_path}")
    
    def create_strategy_state_service(self):
        """Create strategy state service"""
        logger.info("🔧 Creating strategy state service...")
        
        service_path = self.src_dir / "services" / "strategy_state_service.py"
        
        service_code = '''#!/usr/bin/env python3
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
'''
        
        service_path.write_text(service_code)
        logger.info(f"✅ Created strategy state service at {service_path}")
    
    def create_migration(self):
        """Create database migration for strategy state"""
        logger.info("🔧 Creating database migration...")
        
        migration_path = self.src_dir / "database" / "migrations" / "001_strategy_state_migration.py"
        
        migration_code = '''#!/usr/bin/env python3
"""
Strategy State Database Migration
Creates tables for strategy state management
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.database import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def run_migration():
    """Run the strategy state migration"""
    logger.info("🚀 Running strategy state migration...")
    
    try:
        async with engine.begin() as conn:
            # Read and execute schema
            schema_path = Path(__file__).parent / "strategy_state_schema.sql"
            schema_sql = schema_path.read_text()
            
            await conn.execute(text(schema_sql))
            
        logger.info("✅ Strategy state migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Strategy state migration failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(run_migration())
'''
        
        migration_path.write_text(migration_code)
        logger.info(f"✅ Created migration at {migration_path}")

async def main():
    manager = StrategyStateManager()
    manager.create_strategy_state_database()

if __name__ == "__main__":
    asyncio.run(main())




