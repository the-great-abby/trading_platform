"""
Portfolio Database Repository
Handles database operations for portfolio entities
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from ..models.portfolio import Portfolio, PortfolioStatus, RiskTolerance, RebalancingFrequency
from ..models.position import Position
from ..models.asset import Asset

logger = logging.getLogger(__name__)

class PortfolioRepository:
    """Repository for portfolio database operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Create a new portfolio"""
        async with self.async_session() as session:
            try:
                # Convert to database model
                portfolio_data = {
                    "portfolio_id": portfolio.portfolio_id,
                    "name": portfolio.name,
                    "description": portfolio.description,
                    "owner_id": portfolio.owner_id,
                    "base_currency": portfolio.base_currency,
                    "risk_tolerance": portfolio.risk_tolerance.value,
                    "rebalancing_frequency": portfolio.rebalancing_frequency.value,
                    "max_single_asset_weight": portfolio.max_single_asset_weight,
                    "max_sector_weight": portfolio.max_sector_weight,
                    "long_only": portfolio.long_only,
                    "total_value": portfolio.total_value,
                    "cash_balance": portfolio.cash_balance,
                    "creation_date": portfolio.creation_date,
                    "last_updated": datetime.now(),
                    "status": portfolio.status.value
                }
                
                # Insert portfolio
                from sqlalchemy import text
                query = text("""
                    INSERT INTO portfolios (
                        portfolio_id, name, description, owner_id, base_currency,
                        risk_tolerance, rebalancing_frequency, max_single_asset_weight,
                        max_sector_weight, long_only, total_value, cash_balance,
                        creation_date, last_updated, status
                    ) VALUES (
                        :portfolio_id, :name, :description, :owner_id, :base_currency,
                        :risk_tolerance, :rebalancing_frequency, :max_single_asset_weight,
                        :max_sector_weight, :long_only, :total_value, :cash_balance,
                        :creation_date, :last_updated, :status
                    )
                """)
                
                await session.execute(query, portfolio_data)
                await session.commit()
                
                logger.info(f"Portfolio {portfolio.portfolio_id} created successfully")
                return portfolio
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error creating portfolio: {e}")
                raise
    
    async def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT * FROM portfolios WHERE portfolio_id = :portfolio_id
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                return self._row_to_portfolio(row)
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolio {portfolio_id}: {e}")
                raise
    
    async def get_portfolios(
        self, 
        owner_id: Optional[str] = None,
        status: Optional[PortfolioStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Portfolio]:
        """Get portfolios with optional filtering"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                where_conditions = []
                params = {"limit": limit, "offset": offset}
                
                if owner_id:
                    where_conditions.append("owner_id = :owner_id")
                    params["owner_id"] = owner_id
                
                if status:
                    where_conditions.append("status = :status")
                    params["status"] = status.value
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                query = text(f"""
                    SELECT * FROM portfolios {where_clause}
                    ORDER BY creation_date DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [self._row_to_portfolio(row) for row in rows]
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolios: {e}")
                raise
    
    async def update_portfolio(self, portfolio_id: str, updates: Dict[str, Any]) -> Optional[Portfolio]:
        """Update portfolio"""
        async with self.async_session() as session:
            try:
                # Add last_updated timestamp
                updates["last_updated"] = datetime.now()
                
                from sqlalchemy import text
                set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
                updates["portfolio_id"] = portfolio_id
                
                query = text(f"""
                    UPDATE portfolios 
                    SET {set_clause}
                    WHERE portfolio_id = :portfolio_id
                    RETURNING *
                """)
                
                result = await session.execute(query, updates)
                row = result.fetchone()
                
                if not row:
                    return None
                
                await session.commit()
                
                logger.info(f"Portfolio {portfolio_id} updated successfully")
                return self._row_to_portfolio(row)
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error updating portfolio {portfolio_id}: {e}")
                raise
    
    async def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    DELETE FROM portfolios WHERE portfolio_id = :portfolio_id
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id})
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Portfolio {portfolio_id} deleted successfully")
                else:
                    logger.warning(f"Portfolio {portfolio_id} not found for deletion")
                
                return deleted
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
                raise
    
    async def get_portfolio_positions(self, portfolio_id: str) -> List[Position]:
        """Get all positions for a portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT pp.*, a.symbol, a.name, a.sector, a.asset_type
                    FROM portfolio_positions pp
                    LEFT JOIN assets a ON pp.asset_id = a.asset_id
                    WHERE pp.portfolio_id = :portfolio_id
                    ORDER BY pp.created_at DESC
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id})
                rows = result.fetchall()
                
                return [self._row_to_position(row) for row in rows]
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolio positions: {e}")
                raise
    
    async def add_position(self, position: Position) -> Position:
        """Add position to portfolio"""
        async with self.async_session() as session:
            try:
                position_data = {
                    "position_id": position.position_id,
                    "portfolio_id": position.portfolio_id,
                    "asset_id": position.asset_id,
                    "quantity": position.quantity,
                    "average_cost": position.average_cost,
                    "current_price": position.current_price,
                    "market_value": position.market_value,
                    "unrealized_pnl": position.unrealized_pnl,
                    "created_at": position.created_at,
                    "last_updated": datetime.now()
                }
                
                from sqlalchemy import text
                query = text("""
                    INSERT INTO portfolio_positions (
                        position_id, portfolio_id, asset_id, quantity, average_cost,
                        current_price, market_value, unrealized_pnl, created_at, last_updated
                    ) VALUES (
                        :position_id, :portfolio_id, :asset_id, :quantity, :average_cost,
                        :current_price, :market_value, :unrealized_pnl, :created_at, :last_updated
                    )
                """)
                
                await session.execute(query, position_data)
                await session.commit()
                
                logger.info(f"Position {position.position_id} added successfully")
                return position
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error adding position: {e}")
                raise
    
    async def update_position(self, position_id: str, updates: Dict[str, Any]) -> Optional[Position]:
        """Update position"""
        async with self.async_session() as session:
            try:
                updates["last_updated"] = datetime.now()
                
                from sqlalchemy import text
                set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
                updates["position_id"] = position_id
                
                query = text(f"""
                    UPDATE portfolio_positions 
                    SET {set_clause}
                    WHERE position_id = :position_id
                    RETURNING *
                """)
                
                result = await session.execute(query, updates)
                row = result.fetchone()
                
                if not row:
                    return None
                
                await session.commit()
                
                logger.info(f"Position {position_id} updated successfully")
                return self._row_to_position(row)
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error updating position {position_id}: {e}")
                raise
    
    async def remove_position(self, position_id: str) -> bool:
        """Remove position from portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    DELETE FROM portfolio_positions WHERE position_id = :position_id
                """)
                
                result = await session.execute(query, {"position_id": position_id})
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Position {position_id} removed successfully")
                else:
                    logger.warning(f"Position {position_id} not found for removal")
                
                return deleted
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error removing position {position_id}: {e}")
                raise
    
    async def get_portfolio_performance(self, portfolio_id: str, days: int = 30) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        AVG(total_value) as avg_value,
                        MAX(total_value) as max_value,
                        MIN(total_value) as min_value,
                        STDDEV(total_value) as volatility,
                        COUNT(*) as data_points
                    FROM portfolio_performance_history
                    WHERE portfolio_id = :portfolio_id
                    AND calculation_date >= NOW() - INTERVAL ':days days'
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id, "days": days})
                row = result.fetchone()
                
                if not row or not row.data_points:
                    return {}
                
                return {
                    "average_value": float(row.avg_value) if row.avg_value else 0.0,
                    "max_value": float(row.max_value) if row.max_value else 0.0,
                    "min_value": float(row.min_value) if row.min_value else 0.0,
                    "volatility": float(row.volatility) if row.volatility else 0.0,
                    "data_points": int(row.data_points)
                }
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolio performance: {e}")
                raise
    
    def _row_to_portfolio(self, row) -> Portfolio:
        """Convert database row to Portfolio object"""
        return Portfolio(
            portfolio_id=row.portfolio_id,
            name=row.name,
            description=row.description,
            owner_id=row.owner_id,
            base_currency=row.base_currency,
            risk_tolerance=RiskTolerance(row.risk_tolerance),
            rebalancing_frequency=RebalancingFrequency(row.rebalancing_frequency),
            max_single_asset_weight=row.max_single_asset_weight,
            max_sector_weight=row.max_sector_weight,
            long_only=row.long_only,
            total_value=row.total_value,
            cash_balance=row.cash_balance,
            creation_date=row.creation_date,
            status=PortfolioStatus(row.status)
        )
    
    def _row_to_position(self, row) -> Position:
        """Convert database row to Position object"""
        return Position(
            position_id=row.position_id,
            portfolio_id=row.portfolio_id,
            asset_id=row.asset_id,
            quantity=row.quantity,
            average_cost=row.average_cost,
            current_price=row.current_price,
            market_value=row.market_value,
            unrealized_pnl=row.unrealized_pnl,
            created_at=row.created_at
        )
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Portfolio repository connections closed")
























