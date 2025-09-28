"""
Optimization Result Database Repository
Handles database operations for portfolio optimization results
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError

from ..models.optimization_result import OptimizationResult, OptimizationType, OptimizationStatus

logger = logging.getLogger(__name__)

class OptimizationRepository:
    """Repository for optimization result database operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def save_optimization_result(self, result: OptimizationResult) -> OptimizationResult:
        """Save optimization result to database"""
        async with self.async_session() as session:
            try:
                # Save optimization result
                optimization_data = {
                    "optimization_id": result.optimization_id,
                    "portfolio_id": result.portfolio_id,
                    "optimization_type": result.optimization_type.value,
                    "optimization_date": result.optimization_date,
                    "status": result.status.value,
                    "expected_return": result.expected_return,
                    "expected_volatility": result.expected_volatility,
                    "sharpe_ratio": result.sharpe_ratio,
                    "risk_free_rate": result.risk_free_rate,
                    "convergence_achieved": result.convergence_achieved,
                    "iterations": result.iterations,
                    "computation_time": result.computation_time,
                    "constraints": result.constraints,
                    "metadata": result.metadata
                }
                
                from sqlalchemy import text
                query = text("""
                    INSERT INTO optimization_results (
                        optimization_id, portfolio_id, optimization_type, optimization_date,
                        status, expected_return, expected_volatility, sharpe_ratio,
                        risk_free_rate, convergence_achieved, iterations, computation_time,
                        constraints, metadata
                    ) VALUES (
                        :optimization_id, :portfolio_id, :optimization_type, :optimization_date,
                        :status, :expected_return, :expected_volatility, :sharpe_ratio,
                        :risk_free_rate, :convergence_achieved, :iterations, :computation_time,
                        :constraints, :metadata
                    )
                """)
                
                await session.execute(query, optimization_data)
                
                # Save optimization weights
                for asset_id, weight in result.optimal_weights.items():
                    weight_data = {
                        "optimization_id": result.optimization_id,
                        "asset_id": asset_id,
                        "weight": weight
                    }
                    
                    weight_query = text("""
                        INSERT INTO optimization_weights (
                            optimization_id, asset_id, weight
                        ) VALUES (
                            :optimization_id, :asset_id, :weight
                        )
                    """)
                    
                    await session.execute(weight_query, weight_data)
                
                await session.commit()
                
                logger.info(f"Optimization result {result.optimization_id} saved successfully")
                return result
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error saving optimization result: {e}")
                raise
    
    async def get_optimization_result(self, optimization_id: str) -> Optional[OptimizationResult]:
        """Get optimization result by ID"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                # Get optimization result
                query = text("""
                    SELECT * FROM optimization_results WHERE optimization_id = :optimization_id
                """)
                
                result = await session.execute(query, {"optimization_id": optimization_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                # Get optimization weights
                weights_query = text("""
                    SELECT asset_id, weight FROM optimization_weights 
                    WHERE optimization_id = :optimization_id
                """)
                
                weights_result = await session.execute(weights_query, {"optimization_id": optimization_id})
                weights_rows = weights_result.fetchall()
                
                optimal_weights = {row.asset_id: row.weight for row in weights_rows}
                
                return self._row_to_optimization_result(row, optimal_weights)
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting optimization result {optimization_id}: {e}")
                raise
    
    async def get_portfolio_optimization_results(
        self, 
        portfolio_id: str,
        optimization_type: Optional[OptimizationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OptimizationResult]:
        """Get optimization results for portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                where_conditions = ["portfolio_id = :portfolio_id"]
                params = {"portfolio_id": portfolio_id, "limit": limit, "offset": offset}
                
                if optimization_type:
                    where_conditions.append("optimization_type = :optimization_type")
                    params["optimization_type"] = optimization_type.value
                
                where_clause = "WHERE " + " AND ".join(where_conditions)
                
                query = text(f"""
                    SELECT * FROM optimization_results {where_clause}
                    ORDER BY optimization_date DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                optimization_results = []
                for row in rows:
                    # Get weights for each optimization
                    weights_query = text("""
                        SELECT asset_id, weight FROM optimization_weights 
                        WHERE optimization_id = :optimization_id
                    """)
                    
                    weights_result = await session.execute(weights_query, {"optimization_id": row.optimization_id})
                    weights_rows = weights_result.fetchall()
                    
                    optimal_weights = {w_row.asset_id: w_row.weight for w_row in weights_rows}
                    optimization_results.append(self._row_to_optimization_result(row, optimal_weights))
                
                return optimization_results
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting portfolio optimization results: {e}")
                raise
    
    async def get_latest_optimization_result(
        self, 
        portfolio_id: str,
        optimization_type: Optional[OptimizationType] = None
    ) -> Optional[OptimizationResult]:
        """Get latest optimization result for portfolio"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                where_conditions = ["portfolio_id = :portfolio_id", "status = 'SUCCESS'"]
                params = {"portfolio_id": portfolio_id}
                
                if optimization_type:
                    where_conditions.append("optimization_type = :optimization_type")
                    params["optimization_type"] = optimization_type.value
                
                where_clause = "WHERE " + " AND ".join(where_conditions)
                
                query = text(f"""
                    SELECT * FROM optimization_results {where_clause}
                    ORDER BY optimization_date DESC
                    LIMIT 1
                """)
                
                result = await session.execute(query, params)
                row = result.fetchone()
                
                if not row:
                    return None
                
                # Get optimization weights
                weights_query = text("""
                    SELECT asset_id, weight FROM optimization_weights 
                    WHERE optimization_id = :optimization_id
                """)
                
                weights_result = await session.execute(weights_query, {"optimization_id": row.optimization_id})
                weights_rows = weights_result.fetchall()
                
                optimal_weights = {row.asset_id: row.weight for row in weights_rows}
                
                return self._row_to_optimization_result(row, optimal_weights)
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting latest optimization result: {e}")
                raise
    
    async def get_optimization_performance(
        self, 
        portfolio_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get optimization performance metrics"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        optimization_type,
                        COUNT(*) as total_optimizations,
                        AVG(expected_return) as avg_return,
                        AVG(expected_volatility) as avg_volatility,
                        AVG(sharpe_ratio) as avg_sharpe,
                        AVG(computation_time) as avg_computation_time,
                        AVG(iterations) as avg_iterations
                    FROM optimization_results
                    WHERE portfolio_id = :portfolio_id
                    AND optimization_date >= NOW() - INTERVAL ':days days'
                    GROUP BY optimization_type
                """)
                
                result = await session.execute(query, {"portfolio_id": portfolio_id, "days": days})
                rows = result.fetchall()
                
                performance_data = {}
                for row in rows:
                    performance_data[row.optimization_type] = {
                        "total_optimizations": int(row.total_optimizations),
                        "average_return": float(row.avg_return) if row.avg_return else 0.0,
                        "average_volatility": float(row.avg_volatility) if row.avg_volatility else 0.0,
                        "average_sharpe": float(row.avg_sharpe) if row.avg_sharpe else 0.0,
                        "average_computation_time": float(row.avg_computation_time) if row.avg_computation_time else 0.0,
                        "average_iterations": float(row.avg_iterations) if row.avg_iterations else 0.0
                    }
                
                return performance_data
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting optimization performance: {e}")
                raise
    
    async def delete_optimization_result(self, optimization_id: str) -> bool:
        """Delete optimization result"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                
                # Delete optimization weights first
                weights_query = text("""
                    DELETE FROM optimization_weights WHERE optimization_id = :optimization_id
                """)
                await session.execute(weights_query, {"optimization_id": optimization_id})
                
                # Delete optimization result
                query = text("""
                    DELETE FROM optimization_results WHERE optimization_id = :optimization_id
                """)
                
                result = await session.execute(query, {"optimization_id": optimization_id})
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Optimization result {optimization_id} deleted successfully")
                else:
                    logger.warning(f"Optimization result {optimization_id} not found for deletion")
                
                return deleted
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting optimization result {optimization_id}: {e}")
                raise
    
    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get overall optimization statistics"""
        async with self.async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT 
                        COUNT(*) as total_optimizations,
                        COUNT(DISTINCT portfolio_id) as unique_portfolios,
                        COUNT(DISTINCT optimization_type) as optimization_types,
                        AVG(computation_time) as avg_computation_time,
                        AVG(iterations) as avg_iterations,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_optimizations,
                        SUM(CASE WHEN convergence_achieved THEN 1 ELSE 0 END) as converged_optimizations
                    FROM optimization_results
                """)
                
                result = await session.execute(query)
                row = result.fetchone()
                
                if not row:
                    return {}
                
                return {
                    "total_optimizations": int(row.total_optimizations),
                    "unique_portfolios": int(row.unique_portfolios),
                    "optimization_types": int(row.optimization_types),
                    "average_computation_time": float(row.avg_computation_time) if row.avg_computation_time else 0.0,
                    "average_iterations": float(row.avg_iterations) if row.avg_iterations else 0.0,
                    "successful_optimizations": int(row.successful_optimizations),
                    "converged_optimizations": int(row.converged_optimizations),
                    "success_rate": float(row.successful_optimizations) / int(row.total_optimizations) if row.total_optimizations > 0 else 0.0,
                    "convergence_rate": float(row.converged_optimizations) / int(row.total_optimizations) if row.total_optimizations > 0 else 0.0
                }
                
            except SQLAlchemyError as e:
                logger.error(f"Error getting optimization statistics: {e}")
                raise
    
    def _row_to_optimization_result(self, row, optimal_weights: Dict[str, float]) -> OptimizationResult:
        """Convert database row to OptimizationResult object"""
        return OptimizationResult(
            optimization_id=row.optimization_id,
            portfolio_id=row.portfolio_id,
            optimization_type=OptimizationType(row.optimization_type),
            optimization_date=row.optimization_date,
            status=OptimizationStatus(row.status),
            expected_return=row.expected_return,
            expected_volatility=row.expected_volatility,
            sharpe_ratio=row.sharpe_ratio,
            risk_free_rate=row.risk_free_rate,
            convergence_achieved=row.convergence_achieved,
            iterations=row.iterations,
            computation_time=row.computation_time,
            optimal_weights=optimal_weights,
            constraints=row.constraints,
            metadata=row.metadata
        )
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Optimization repository connections closed")



