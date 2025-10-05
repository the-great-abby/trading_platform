"""
Risk Metrics Repository

Database repository for risk metrics data in the comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSON

from ..models.risk_metrics import RiskMetrics
from ..database.connection import get_db_session


logger = logging.getLogger(__name__)


class RiskMetricsRepository:
    """
    Repository for risk metrics database operations.
    
    Provides CRUD operations and query methods for risk metrics data.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize risk metrics repository.
        
        Args:
            db_session: Database session (optional, will create if not provided)
        """
        self.db_session = db_session
    
    def create_risk_metrics(self, risk_metrics: RiskMetrics) -> RiskMetrics:
        """
        Create a new risk metrics record.
        
        Args:
            risk_metrics: RiskMetrics object to create
            
        Returns:
            Created RiskMetrics object
        """
        logger.info(f"Creating risk metrics for portfolio {risk_metrics.portfolio_id}")
        
        with self._get_session() as session:
            try:
                # Convert to database record
                db_record = self._to_db_record(risk_metrics)
                
                # Insert record
                session.add(db_record)
                session.commit()
                session.refresh(db_record)
                
                # Convert back to model
                created_metrics = self._from_db_record(db_record)
                
                logger.info(f"Created risk metrics {created_metrics.risk_metrics_id}")
                return created_metrics
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to create risk metrics: {str(e)}")
                raise
    
    def get_risk_metrics_by_id(self, risk_metrics_id: UUID) -> Optional[RiskMetrics]:
        """
        Get risk metrics by ID.
        
        Args:
            risk_metrics_id: Risk metrics identifier
            
        Returns:
            RiskMetrics object or None if not found
        """
        logger.info(f"Getting risk metrics {risk_metrics_id}")
        
        with self._get_session() as session:
            try:
                db_record = session.query(RiskMetricsDB).filter_by(
                    risk_metrics_id=risk_metrics_id
                ).first()
                
                if db_record:
                    return self._from_db_record(db_record)
                return None
                
            except Exception as e:
                logger.error(f"Failed to get risk metrics {risk_metrics_id}: {str(e)}")
                raise
    
    def get_latest_risk_metrics(self, portfolio_id: UUID) -> Optional[RiskMetrics]:
        """
        Get the latest risk metrics for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Latest RiskMetrics object or None if not found
        """
        logger.info(f"Getting latest risk metrics for portfolio {portfolio_id}")
        
        with self._get_session() as session:
            try:
                db_record = session.query(RiskMetricsDB).filter_by(
                    portfolio_id=portfolio_id
                ).order_by(RiskMetricsDB.calculation_timestamp.desc()).first()
                
                if db_record:
                    return self._from_db_record(db_record)
                return None
                
            except Exception as e:
                logger.error(f"Failed to get latest risk metrics for portfolio {portfolio_id}: {str(e)}")
                raise
    
    def get_risk_metrics_history(
        self,
        portfolio_id: UUID,
        limit: int = 30,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[RiskMetrics]:
        """
        Get risk metrics history for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            limit: Maximum number of records to return
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of RiskMetrics objects
        """
        logger.info(f"Getting risk metrics history for portfolio {portfolio_id}")
        
        with self._get_session() as session:
            try:
                query = session.query(RiskMetricsDB).filter_by(portfolio_id=portfolio_id)
                
                if start_date:
                    query = query.filter(RiskMetricsDB.calculation_timestamp >= start_date)
                
                if end_date:
                    query = query.filter(RiskMetricsDB.calculation_timestamp <= end_date)
                
                db_records = query.order_by(
                    RiskMetricsDB.calculation_timestamp.desc()
                ).limit(limit).all()
                
                return [self._from_db_record(record) for record in db_records]
                
            except Exception as e:
                logger.error(f"Failed to get risk metrics history for portfolio {portfolio_id}: {str(e)}")
                raise
    
    def update_risk_metrics(self, risk_metrics: RiskMetrics) -> RiskMetrics:
        """
        Update an existing risk metrics record.
        
        Args:
            risk_metrics: RiskMetrics object to update
            
        Returns:
            Updated RiskMetrics object
        """
        logger.info(f"Updating risk metrics {risk_metrics.risk_metrics_id}")
        
        with self._get_session() as session:
            try:
                # Find existing record
                db_record = session.query(RiskMetricsDB).filter_by(
                    risk_metrics_id=risk_metrics.risk_metrics_id
                ).first()
                
                if not db_record:
                    raise ValueError(f"Risk metrics {risk_metrics.risk_metrics_id} not found")
                
                # Update fields
                self._update_db_record(db_record, risk_metrics)
                db_record.updated_at = datetime.utcnow()
                
                session.commit()
                session.refresh(db_record)
                
                updated_metrics = self._from_db_record(db_record)
                
                logger.info(f"Updated risk metrics {updated_metrics.risk_metrics_id}")
                return updated_metrics
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update risk metrics {risk_metrics.risk_metrics_id}: {str(e)}")
                raise
    
    def delete_risk_metrics(self, risk_metrics_id: UUID) -> bool:
        """
        Delete risk metrics by ID.
        
        Args:
            risk_metrics_id: Risk metrics identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        logger.info(f"Deleting risk metrics {risk_metrics_id}")
        
        with self._get_session() as session:
            try:
                db_record = session.query(RiskMetricsDB).filter_by(
                    risk_metrics_id=risk_metrics_id
                ).first()
                
                if db_record:
                    session.delete(db_record)
                    session.commit()
                    logger.info(f"Deleted risk metrics {risk_metrics_id}")
                    return True
                else:
                    logger.warning(f"Risk metrics {risk_metrics_id} not found")
                    return False
                    
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to delete risk metrics {risk_metrics_id}: {str(e)}")
                raise
    
    def get_recent_risk_metrics(
        self,
        portfolio_id: UUID,
        hours: int = 1
    ) -> List[RiskMetrics]:
        """
        Get recent risk metrics within specified hours.
        
        Args:
            portfolio_id: Portfolio identifier
            hours: Number of hours to look back
            
        Returns:
            List of recent RiskMetrics objects
        """
        logger.info(f"Getting recent risk metrics for portfolio {portfolio_id} within {hours} hours")
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._get_session() as session:
            try:
                db_records = session.query(RiskMetricsDB).filter(
                    RiskMetricsDB.portfolio_id == portfolio_id,
                    RiskMetricsDB.calculation_timestamp >= cutoff_time
                ).order_by(RiskMetricsDB.calculation_timestamp.desc()).all()
                
                return [self._from_db_record(record) for record in db_records]
                
            except Exception as e:
                logger.error(f"Failed to get recent risk metrics for portfolio {portfolio_id}: {str(e)}")
                raise
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return get_db_session()
    
    def _to_db_record(self, risk_metrics: RiskMetrics) -> 'RiskMetricsDB':
        """Convert RiskMetrics model to database record."""
        return RiskMetricsDB(
            risk_metrics_id=risk_metrics.risk_metrics_id,
            portfolio_id=risk_metrics.portfolio_id,
            calculation_timestamp=risk_metrics.calculation_timestamp,
            calculation_method=risk_metrics.calculation_method,
            data_period_days=risk_metrics.data_period_days,
            var_95=risk_metrics.var_95,
            var_99=risk_metrics.var_99,
            expected_shortfall_95=risk_metrics.expected_shortfall_95,
            expected_shortfall_99=risk_metrics.expected_shortfall_99,
            portfolio_volatility=risk_metrics.portfolio_volatility,
            portfolio_beta=risk_metrics.portfolio_beta,
            maximum_drawdown=risk_metrics.maximum_drawdown,
            sharpe_ratio=risk_metrics.sharpe_ratio,
            sortino_ratio=risk_metrics.sortino_ratio,
            calmar_ratio=risk_metrics.calmar_ratio,
            concentration_risk=risk_metrics.concentration_risk,
            correlation_risk=risk_metrics.correlation_risk,
            leverage_ratio=risk_metrics.leverage_ratio,
            cash_ratio=risk_metrics.cash_ratio,
            confidence_intervals=risk_metrics.confidence_intervals,
            created_at=risk_metrics.created_at,
            updated_at=risk_metrics.updated_at
        )
    
    def _from_db_record(self, db_record: 'RiskMetricsDB') -> RiskMetrics:
        """Convert database record to RiskMetrics model."""
        return RiskMetrics(
            risk_metrics_id=db_record.risk_metrics_id,
            portfolio_id=db_record.portfolio_id,
            calculation_timestamp=db_record.calculation_timestamp,
            calculation_method=db_record.calculation_method,
            data_period_days=db_record.data_period_days,
            var_95=db_record.var_95,
            var_99=db_record.var_99,
            expected_shortfall_95=db_record.expected_shortfall_95,
            expected_shortfall_99=db_record.expected_shortfall_99,
            portfolio_volatility=db_record.portfolio_volatility,
            portfolio_beta=db_record.portfolio_beta,
            maximum_drawdown=db_record.maximum_drawdown,
            sharpe_ratio=db_record.sharpe_ratio,
            sortino_ratio=db_record.sortino_ratio,
            calmar_ratio=db_record.calmar_ratio,
            concentration_risk=db_record.concentration_risk,
            correlation_risk=db_record.correlation_risk,
            leverage_ratio=db_record.leverage_ratio,
            cash_ratio=db_record.cash_ratio,
            confidence_intervals=db_record.confidence_intervals,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at
        )
    
    def _update_db_record(self, db_record: 'RiskMetricsDB', risk_metrics: RiskMetrics) -> None:
        """Update database record with RiskMetrics data."""
        db_record.portfolio_id = risk_metrics.portfolio_id
        db_record.calculation_timestamp = risk_metrics.calculation_timestamp
        db_record.calculation_method = risk_metrics.calculation_method
        db_record.data_period_days = risk_metrics.data_period_days
        db_record.var_95 = risk_metrics.var_95
        db_record.var_99 = risk_metrics.var_99
        db_record.expected_shortfall_95 = risk_metrics.expected_shortfall_95
        db_record.expected_shortfall_99 = risk_metrics.expected_shortfall_99
        db_record.portfolio_volatility = risk_metrics.portfolio_volatility
        db_record.portfolio_beta = risk_metrics.portfolio_beta
        db_record.maximum_drawdown = risk_metrics.maximum_drawdown
        db_record.sharpe_ratio = risk_metrics.sharpe_ratio
        db_record.sortino_ratio = risk_metrics.sortino_ratio
        db_record.calmar_ratio = risk_metrics.calmar_ratio
        db_record.concentration_risk = risk_metrics.concentration_risk
        db_record.correlation_risk = risk_metrics.correlation_risk
        db_record.leverage_ratio = risk_metrics.leverage_ratio
        db_record.cash_ratio = risk_metrics.cash_ratio
        db_record.confidence_intervals = risk_metrics.confidence_intervals


# Database model definition
class RiskMetricsDB:
    """Database model for risk metrics."""
    
    __tablename__ = 'risk_metrics'
    
    risk_metrics_id = sa.Column(PostgresUUID(as_uuid=True), primary_key=True)
    portfolio_id = sa.Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    calculation_timestamp = sa.Column(sa.DateTime, nullable=False, index=True)
    calculation_method = sa.Column(sa.String(50), nullable=False)
    data_period_days = sa.Column(sa.Integer, nullable=False)
    
    # VaR metrics
    var_95 = sa.Column(sa.Float, nullable=False)
    var_99 = sa.Column(sa.Float, nullable=False)
    expected_shortfall_95 = sa.Column(sa.Float, nullable=False)
    expected_shortfall_99 = sa.Column(sa.Float, nullable=False)
    
    # Portfolio risk metrics
    portfolio_volatility = sa.Column(sa.Float, nullable=False)
    portfolio_beta = sa.Column(sa.Float, nullable=False)
    maximum_drawdown = sa.Column(sa.Float, nullable=False)
    
    # Performance metrics
    sharpe_ratio = sa.Column(sa.Float, nullable=False)
    sortino_ratio = sa.Column(sa.Float, nullable=False)
    calmar_ratio = sa.Column(sa.Float, nullable=False)
    
    # Risk scores
    concentration_risk = sa.Column(sa.Float, nullable=False)
    correlation_risk = sa.Column(sa.Float, nullable=False)
    
    # Portfolio composition
    leverage_ratio = sa.Column(sa.Float, nullable=False)
    cash_ratio = sa.Column(sa.Float, nullable=False)
    
    # Additional data
    confidence_intervals = sa.Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        sa.Index('idx_risk_metrics_portfolio_timestamp', 'portfolio_id', 'calculation_timestamp'),
        sa.Index('idx_risk_metrics_calculation_method', 'calculation_method'),
    )












