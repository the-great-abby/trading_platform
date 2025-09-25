"""
Risk Metrics Database Repository
Handles database operations for risk metrics and calculations
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError

from ..models.risk_metrics import RiskMetrics

logger = logging.getLogger(__name__)

class RiskRepository:
    """Repository for risk metrics database operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def save_risk_metrics(self, risk_metrics: RiskMetrics) -> RiskMetrics:
        """Save risk metrics to database"""
        async with self.async_session() as session:
            try:
                # Save risk metrics
                risk_data = {
                    "risk_metrics_id": risk_metrics.risk_metrics_id,
                    "portfolio_id": risk_metrics.portfolio_id,
                    "calculation_date": risk_metrics.calculation_date,
                    "lookback_period": risk_metrics.lookback_period,
                    "var_95": risk_metrics.var_95,
                    "var_99": risk_metrics.var_99,
                    "cvar_95": risk_metrics.cvar_95,
                    "cvar_99": risk_metrics.cvar_99,
                    "systematic_risk": risk_metrics.systematic_risk,
                    "idiosyncratic_risk": risk_metrics.idiosyncratic_risk,
                    "market_beta": risk_metrics.market_beta,
                    "average_correlation": risk_metrics.average_correlation,
                    "max_correlation": risk_metrics.max_correlation,
                    "min_correlation": risk_metrics.min_correlation,
                    "created_at": datetime.now()
                }
                
                from sqlalchemy import text
                query = text("""
                    INSERT INTO risk_metrics (
                        risk_metrics_id, portfolio_id, calculation_date, lookback_period,
                        var_95, var_99, cvar_95, cvar_99, systematic_risk, idiosyncratic_risk,
                        market_beta, average_correlation, max_correlation, min_correlation,
                        created_at
                    ) VALUES (
                        :risk_metrics_id, :portfolio_id, :calculation_date, :lookback_period,
                        :var_95, :var_99, :cvar_95, :cvar_99, :systematic_risk, :idiosyncratic_risk,
                        :market_beta, :average_correlation, :max_correlation, :min_correlation,
                        :created_at
                    )
                """)
                
                await session.execute(query, risk_data)
                
                # Save risk contributions
                for asset_id, contribution in risk_metrics.risk_contributions.items():
                    contribution_data = {
                        "risk_metrics_id": risk_metrics.risk_metrics_id,
                        "asset_id": asset_id,
                        "risk_contribution": contribution
                    }
                    
                    contribution_query = text("""
                        INSERT INTO risk_contributions (
                            risk_metrics_id, asset_id, risk_contribution
                        ) VALUES (
                            :risk_metrics_id, :asset_id, :risk_contribution
                        )
                    """)
                    
                    await session.execute(contribution_query, contribution_data)
                
                await session.commit()
                
                logger.info(f"Risk metrics {risk_metrics.risk_metrics_id} saved successfully")
                return risk_metrics
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error saving risk metrics: {e}")
                raise
    
    async def get_risk_metrics(self, risk_metrics_id: str) -> Optional[RiskMetrics]:
        """Get risk metrics by ID"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                # Get risk metrics
                query = text("""
                    SELECT * FROM risk_metrics WHERE risk_metrics_id = :risk_metrics_id
                """)
                
                result = await session.execute(query, {"risk_metrics_id": risk_metrics_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                # Get risk contributions
                contributions_query = text("""
                    SELECT asset_id, risk_contribution FROM risk_contributions 
                    WHERE risk_metrics_id = :risk_metrics_id
                """)
                
                contributions_result = await session.execute(contributions_query, {"risk_metrics_id": risk_metrics_id})
                contributions_rows = contributions_result.fetchall()
                
                risk_contributions = {row.asset_id: row.risk_contribution for row in contributions_rows}
                
                return self._row_to_risk_metrics(row, risk_contributions)
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting risk metrics {risk_metrics_id}: {e}")
                raise
    
    async def get_latest_risk_metrics(self, portfolio_id: str) -> Optional[RiskMetrics]:
        """Get latest risk metrics for portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                query = text("""
                    SELECT * FROM risk_metrics 
                    WHERE portfolio_id = :portfolio_id
                    ORDER BY calculation_date DESC
                    LIMIT 1
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                # Get risk contributions
                contributions_query = text("""
                    SELECT asset_id, risk_contribution FROM risk_contributions 
                    WHERE risk_metrics_id = :risk_metrics_id
                """)
                
                contributions_result = await session.execute(contributions_query, {"risk_metrics_id": row.risk_metrics_id})
                contributions_rows = contributions_result.fetchall()
                
                risk_contributions = {row.asset_id: row.risk_contribution for row in contributions_rows}
                
                return self._row_to_risk_metrics(row, risk_contributions)
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting latest risk metrics: {e}")
                raise
    
    async def get_portfolio_risk_history(
        self, 
        portfolio_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[RiskMetrics]:
        """Get risk metrics history for portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT * FROM risk_metrics 
                    WHERE portfolio_id = :portfolio_id
                    AND calculation_date >= NOW() - INTERVAL ':days days'
                    ORDER BY calculation_date DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id, "days": days, "limit": limit})
                rows = result.fetchall()
                
                risk_metrics_list = []
                for row in rows:
                    # Get risk contributions for each metric
                    contributions_query = text("""
                        SELECT asset_id, risk_contribution FROM risk_contributions 
                        WHERE risk_metrics_id = :risk_metrics_id
                    """)
                    
                    contributions_result = await session.execute(contributions_query, {"risk_metrics_id": row.risk_metrics_id})
                    contributions_rows = contributions_result.fetchall()
                    
                    risk_contributions = {r_row.asset_id: r_row.risk_contribution for r_row in contributions_rows}
                    risk_metrics_list.append(self._row_to_risk_metrics(row, risk_contributions))
                
                return risk_metrics_list
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolio risk history: {e}")
                raise
    
    async def get_risk_metrics_summary(self, portfolio_id: str, days: int = 30) -> Dict[str, Any]:
        """Get risk metrics summary for portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        AVG(var_95) as avg_var_95,
                        AVG(var_99) as avg_var_99,
                        AVG(cvar_95) as avg_cvar_95,
                        AVG(cvar_99) as avg_cvar_99,
                        AVG(systematic_risk) as avg_systematic_risk,
                        AVG(idiosyncratic_risk) as avg_idiosyncratic_risk,
                        AVG(market_beta) as avg_market_beta,
                        AVG(average_correlation) as avg_correlation,
                        MIN(var_95) as min_var_95,
                        MAX(var_95) as max_var_95,
                        COUNT(*) as data_points
                    FROM risk_metrics
                    WHERE portfolio_id = :portfolio_id
                    AND calculation_date >= NOW() - INTERVAL ':days days'
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id, "days": days})
                row = result.fetchone()
                
                if not row or not row.data_points:
                    return {}
                
                return {
                    "average_var_95": float(row.avg_var_95) if row.avg_var_95 else 0.0,
                    "average_var_99": float(row.avg_var_99) if row.avg_var_99 else 0.0,
                    "average_cvar_95": float(row.avg_cvar_95) if row.avg_cvar_95 else 0.0,
                    "average_cvar_99": float(row.avg_cvar_99) if row.avg_cvar_99 else 0.0,
                    "average_systematic_risk": float(row.avg_systematic_risk) if row.avg_systematic_risk else 0.0,
                    "average_idiosyncratic_risk": float(row.avg_idiosyncratic_risk) if row.avg_idiosyncratic_risk else 0.0,
                    "average_market_beta": float(row.avg_market_beta) if row.avg_market_beta else 0.0,
                    "average_correlation": float(row.avg_correlation) if row.avg_correlation else 0.0,
                    "min_var_95": float(row.min_var_95) if row.min_var_95 else 0.0,
                    "max_var_95": float(row.max_var_95) if row.max_var_95 else 0.0,
                    "data_points": int(row.data_points),
                    "risk_trend": "STABLE"  # Could be calculated based on variance
                }
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting risk metrics summary: {e}")
                raise
    
    async def get_asset_risk_contributions(self, portfolio_id: str) -> Dict[str, float]:
        """Get current risk contributions by asset"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT rc.asset_id, rc.risk_contribution
                    FROM risk_contributions rc
                    JOIN risk_metrics rm ON rc.risk_metrics_id = rm.risk_metrics_id
                    WHERE rm.portfolio_id = :portfolio_id
                    AND rm.calculation_date = (
                        SELECT MAX(calculation_date) 
                        FROM risk_metrics 
                        WHERE portfolio_id = :portfolio_id
                    )
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id})
                rows = result.fetchall()
                
                return {row.asset_id: row.risk_contribution for row in rows}
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting asset risk contributions: {e}")
                raise
    
    async def get_risk_metrics_trends(
        self, 
        portfolio_id: str,
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get risk metrics trends over time"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        calculation_date,
                        var_95,
                        var_99,
                        cvar_95,
                        cvar_99,
                        systematic_risk,
                        idiosyncratic_risk,
                        market_beta,
                        average_correlation
                    FROM risk_metrics
                    WHERE portfolio_id = :portfolio_id
                    AND calculation_date >= NOW() - INTERVAL ':days days'
                    ORDER BY calculation_date ASC
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id, "days": days})
                rows = result.fetchall()
                
                trends = {
                    "var_95": [],
                    "var_99": [],
                    "cvar_95": [],
                    "cvar_99": [],
                    "systematic_risk": [],
                    "idiosyncratic_risk": [],
                    "market_beta": [],
                    "average_correlation": []
                }
                
                for row in rows:
                    date_str = row.calculation_date.isoformat()
                    trends["var_95"].append({"date": date_str, "value": float(row.var_95)})
                    trends["var_99"].append({"date": date_str, "value": float(row.var_99)})
                    trends["cvar_95"].append({"date": date_str, "value": float(row.cvar_95)})
                    trends["cvar_99"].append({"date": date_str, "value": float(row.cvar_99)})
                    trends["systematic_risk"].append({"date": date_str, "value": float(row.systematic_risk)})
                    trends["idiosyncratic_risk"].append({"date": date_str, "value": float(row.idiosyncratic_risk)})
                    trends["market_beta"].append({"date": date_str, "value": float(row.market_beta)})
                    trends["average_correlation"].append({"date": date_str, "value": float(row.average_correlation)})
                
                return trends
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting risk metrics trends: {e}")
                raise
    
    async def delete_risk_metrics(self, risk_metrics_id: str) -> bool:
        """Delete risk metrics"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                # Delete risk contributions first
                contributions_query = text("""
                    DELETE FROM risk_contributions WHERE risk_metrics_id = :risk_metrics_id
                """)
                await session.execute(contributions_query, {"risk_metrics_id": risk_metrics_id})
                
                # Delete risk metrics
                query = text("""
                    DELETE FROM risk_metrics WHERE risk_metrics_id = :risk_metrics_id
                """)
                
                result = await session.execute(query, {"risk_metrics_id": risk_metrics_id})
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Risk metrics {risk_metrics_id} deleted successfully")
                else:
                    logger.warning(f"Risk metrics {risk_metrics_id} not found for deletion")
                
                return deleted
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting risk metrics {risk_metrics_id}: {e}")
                raise
    
    async def get_risk_statistics(self) -> Dict[str, Any]:
        """Get overall risk statistics"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        COUNT(*) as total_risk_calculations,
                        COUNT(DISTINCT portfolio_id) as unique_portfolios,
                        AVG(var_95) as avg_var_95,
                        AVG(var_99) as avg_var_99,
                        AVG(cvar_95) as avg_cvar_95,
                        AVG(cvar_99) as avg_cvar_99,
                        AVG(systematic_risk) as avg_systematic_risk,
                        AVG(idiosyncratic_risk) as avg_idiosyncratic_risk,
                        AVG(market_beta) as avg_market_beta
                    FROM risk_metrics
                """)
                
                result = await session.execute(query)
                row = result.fetchone()
                
                if not row:
                    return {}
                
                return {
                    "total_risk_calculations": int(row.total_risk_calculations),
                    "unique_portfolios": int(row.unique_portfolios),
                    "average_var_95": float(row.avg_var_95) if row.avg_var_95 else 0.0,
                    "average_var_99": float(row.avg_var_99) if row.avg_var_99 else 0.0,
                    "average_cvar_95": float(row.avg_cvar_95) if row.avg_cvar_95 else 0.0,
                    "average_cvar_99": float(row.avg_cvar_99) if row.avg_cvar_99 else 0.0,
                    "average_systematic_risk": float(row.avg_systematic_risk) if row.avg_systematic_risk else 0.0,
                    "average_idiosyncratic_risk": float(row.avg_idiosyncratic_risk) if row.avg_idiosyncratic_risk else 0.0,
                    "average_market_beta": float(row.avg_market_beta) if row.avg_market_beta else 0.0
                }
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting risk statistics: {e}")
                raise
    
    def _row_to_risk_metrics(self, row, risk_contributions: Dict[str, float]) -> RiskMetrics:
        """Convert database row to RiskMetrics object"""
        return RiskMetrics(
            risk_metrics_id=row.risk_metrics_id,
            portfolio_id=row.portfolio_id,
            calculation_date=row.calculation_date,
            lookback_period=row.lookback_period,
            var_95=row.var_95,
            var_99=row.var_99,
            cvar_95=row.cvar_95,
            cvar_99=row.cvar_99,
            systematic_risk=row.systematic_risk,
            idiosyncratic_risk=row.idiosyncratic_risk,
            market_beta=row.market_beta,
            average_correlation=row.average_correlation,
            max_correlation=row.max_correlation,
            min_correlation=row.min_correlation,
            risk_contributions=risk_contributions
        )
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Risk repository connections closed")

