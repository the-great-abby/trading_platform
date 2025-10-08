"""
Data Synchronization Service

Synchronizes data between the risk management framework and other
trading system components.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import json
import threading
import time

from ..utils.risk_utils import CacheUtils, PerformanceUtils
from .portfolio_service_integration import get_portfolio_integration
from .trading_engine_integration import get_trading_engine_integration
from .market_data_service_integration import get_market_data_integration


logger = logging.getLogger(__name__)


@dataclass
class SyncStatus:
    """Data synchronization status."""
    service: str
    last_sync: datetime
    status: str  # 'success', 'error', 'in_progress'
    records_synced: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class SyncConfig:
    """Synchronization configuration."""
    enabled: bool
    interval_minutes: int
    batch_size: int
    retry_attempts: int
    timeout_seconds: int


class DataSynchronizationService:
    """
    Data synchronization service for the risk management framework.
    
    Handles synchronization of data between the risk management service
    and other trading system components.
    """
    
    def __init__(
        self,
        sync_interval_minutes: int = 15,  # Align with 15-minute data feed
        batch_size: int = 100,
        retry_attempts: int = 3,
        timeout_seconds: int = 60
    ):
        """
        Initialize data synchronization service.
        
        Args:
            sync_interval_minutes: Synchronization interval in minutes
            batch_size: Batch size for data synchronization
            retry_attempts: Number of retry attempts for failed syncs
            timeout_seconds: Timeout for synchronization operations
        """
        self.sync_interval_minutes = sync_interval_minutes
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.timeout_seconds = timeout_seconds
        
        # Synchronization status tracking
        self.sync_status: Dict[str, SyncStatus] = {}
        self.sync_config: Dict[str, SyncConfig] = {}
        
        # Integration services
        self.portfolio_integration = get_portfolio_integration()
        self.trading_engine_integration = get_trading_engine_integration()
        self.market_data_integration = get_market_data_integration()
        
        # Synchronization control
        self._sync_thread = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Initialize default sync configurations
        self._initialize_sync_configs()
    
    def start_synchronization(self) -> bool:
        """
        Start the data synchronization service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("Data synchronization service is already running")
            return True
        
        try:
            # Reset stop event
            self._stop_event.clear()
            
            # Start synchronization thread
            self._sync_thread = threading.Thread(
                target=self._synchronization_loop,
                name="DataSyncService",
                daemon=True
            )
            self._sync_thread.start()
            
            self._running = True
            logger.info("Data synchronization service started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start data synchronization service: {str(e)}")
            return False
    
    def stop_synchronization(self) -> bool:
        """
        Stop the data synchronization service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._running:
            logger.warning("Data synchronization service is not running")
            return True
        
        try:
            # Signal stop
            self._stop_event.set()
            
            # Wait for thread to finish
            if self._sync_thread and self._sync_thread.is_alive():
                self._sync_thread.join(timeout=30)
            
            self._running = False
            logger.info("Data synchronization service stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop data synchronization service: {str(e)}")
            return False
    
    @PerformanceUtils.measure_execution_time
    def sync_portfolio_data(
        self,
        portfolio_ids: Optional[List[str]] = None
    ) -> SyncStatus:
        """
        Synchronize portfolio data with portfolio service.
        
        Args:
            portfolio_ids: List of portfolio IDs to sync (None for all)
            
        Returns:
            SyncStatus object with synchronization results
        """
        logger.info("Starting portfolio data synchronization")
        
        try:
            # Get list of portfolios to sync
            if portfolio_ids is None:
                portfolios = self.portfolio_integration.get_portfolio_list()
                portfolio_ids = [p.get('portfolio_id') for p in portfolios]
            
            records_synced = 0
            errors = []
            
            # Sync each portfolio
            for portfolio_id in portfolio_ids:
                try:
                    # Get portfolio data
                    portfolio_data = self.portfolio_integration.get_portfolio_data(portfolio_id)
                    
                    if portfolio_data:
                        # Update risk metrics in portfolio service
                        risk_metrics = self._calculate_portfolio_risk_metrics(portfolio_data)
                        
                        if risk_metrics:
                            success = self.portfolio_integration.update_portfolio_risk_metrics(
                                portfolio_id, risk_metrics
                            )
                            
                            if success:
                                records_synced += 1
                            else:
                                errors.append(f"Failed to update risk metrics for {portfolio_id}")
                        else:
                            errors.append(f"Failed to calculate risk metrics for {portfolio_id}")
                    else:
                        errors.append(f"Failed to fetch portfolio data for {portfolio_id}")
                        
                except Exception as e:
                    error_msg = f"Error syncing portfolio {portfolio_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            # Create sync status
            sync_status = SyncStatus(
                service='portfolio_data',
                last_sync=datetime.utcnow(),
                status='success' if not errors else 'error',
                records_synced=records_synced,
                error_message='; '.join(errors) if errors else None,
                metadata={
                    'portfolios_synced': records_synced,
                    'total_portfolios': len(portfolio_ids),
                    'errors': len(errors)
                }
            )
            
            # Update sync status
            self.sync_status['portfolio_data'] = sync_status
            
            logger.info(f"Portfolio data synchronization completed: {records_synced} portfolios synced")
            return sync_status
            
        except Exception as e:
            error_msg = f"Portfolio data synchronization failed: {str(e)}"
            logger.error(error_msg)
            
            sync_status = SyncStatus(
                service='portfolio_data',
                last_sync=datetime.utcnow(),
                status='error',
                records_synced=0,
                error_message=error_msg
            )
            
            self.sync_status['portfolio_data'] = sync_status
            return sync_status
    
    @PerformanceUtils.measure_execution_time
    def sync_trade_data(
        self,
        portfolio_ids: Optional[List[str]] = None
    ) -> SyncStatus:
        """
        Synchronize trade data with trading engine.
        
        Args:
            portfolio_ids: List of portfolio IDs to sync trades for
            
        Returns:
            SyncStatus object with synchronization results
        """
        logger.info("Starting trade data synchronization")
        
        try:
            # Get list of portfolios to sync
            if portfolio_ids is None:
                portfolios = self.portfolio_integration.get_portfolio_list()
                portfolio_ids = [p.get('portfolio_id') for p in portfolios]
            
            records_synced = 0
            errors = []
            
            # Sync trade data for each portfolio
            for portfolio_id in portfolio_ids:
                try:
                    # Get recent trades
                    recent_trades = self.trading_engine_integration.get_recent_trades(
                        portfolio_id, hours=24
                    )
                    
                    # Process trades for risk analysis
                    for trade in recent_trades:
                        try:
                            # Validate trade against risk limits
                            risk_limits = self._get_risk_limits(portfolio_id)
                            trade_data = {
                                'trade_id': trade.trade_id,
                                'symbol': trade.symbol,
                                'side': trade.side,
                                'quantity': trade.quantity,
                                'price': trade.price
                            }
                            
                            risk_check = self.trading_engine_integration.validate_trade_risk(
                                trade_data, portfolio_id, risk_limits
                            )
                            
                            # Log risk validation results
                            if not risk_check.approved:
                                logger.warning(f"Trade {trade.trade_id} failed risk validation")
                            
                            records_synced += 1
                            
                        except Exception as e:
                            error_msg = f"Error processing trade {trade.trade_id}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                            continue
                    
                except Exception as e:
                    error_msg = f"Error syncing trades for portfolio {portfolio_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            # Create sync status
            sync_status = SyncStatus(
                service='trade_data',
                last_sync=datetime.utcnow(),
                status='success' if not errors else 'error',
                records_synced=records_synced,
                error_message='; '.join(errors) if errors else None,
                metadata={
                    'trades_processed': records_synced,
                    'portfolios_processed': len(portfolio_ids),
                    'errors': len(errors)
                }
            )
            
            # Update sync status
            self.sync_status['trade_data'] = sync_status
            
            logger.info(f"Trade data synchronization completed: {records_synced} trades processed")
            return sync_status
            
        except Exception as e:
            error_msg = f"Trade data synchronization failed: {str(e)}"
            logger.error(error_msg)
            
            sync_status = SyncStatus(
                service='trade_data',
                last_sync=datetime.utcnow(),
                status='error',
                records_synced=0,
                error_message=error_msg
            )
            
            self.sync_status['trade_data'] = sync_status
            return sync_status
    
    @PerformanceUtils.measure_execution_time
    def sync_market_data(
        self,
        symbols: Optional[List[str]] = None
    ) -> SyncStatus:
        """
        Synchronize market data with market data service.
        
        Args:
            symbols: List of symbols to sync market data for
            
        Returns:
            SyncStatus object with synchronization results
        """
        logger.info("Starting market data synchronization")
        
        try:
            # Get symbols to sync
            if symbols is None:
                # Get symbols from all portfolios
                portfolios = self.portfolio_integration.get_portfolio_list()
                symbols = set()
                
                for portfolio in portfolios:
                    portfolio_id = portfolio.get('portfolio_id')
                    positions = self.portfolio_integration.get_portfolio_positions(portfolio_id)
                    for position in positions:
                        symbols.add(position.get('symbol'))
                
                symbols = list(symbols)
            
            records_synced = 0
            errors = []
            
            # Sync current prices
            try:
                current_prices = self.market_data_integration.get_current_prices(symbols)
                records_synced += len(current_prices)
            except Exception as e:
                error_msg = f"Error fetching current prices: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            
            # Sync volatility data
            try:
                volatility_data = self.market_data_integration.get_volatility_data(symbols)
                records_synced += len(volatility_data)
            except Exception as e:
                error_msg = f"Error fetching volatility data: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            
            # Sync correlation matrix
            try:
                correlation_matrix = self.market_data_integration.get_correlation_matrix(symbols)
                if correlation_matrix is not None:
                    records_synced += 1
            except Exception as e:
                error_msg = f"Error fetching correlation matrix: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            
            # Create sync status
            sync_status = SyncStatus(
                service='market_data',
                last_sync=datetime.utcnow(),
                status='success' if not errors else 'error',
                records_synced=records_synced,
                error_message='; '.join(errors) if errors else None,
                metadata={
                    'symbols_synced': len(symbols),
                    'data_types': ['current_prices', 'volatility', 'correlation'],
                    'errors': len(errors)
                }
            )
            
            # Update sync status
            self.sync_status['market_data'] = sync_status
            
            logger.info(f"Market data synchronization completed: {records_synced} records synced")
            return sync_status
            
        except Exception as e:
            error_msg = f"Market data synchronization failed: {str(e)}"
            logger.error(error_msg)
            
            sync_status = SyncStatus(
                service='market_data',
                last_sync=datetime.utcnow(),
                status='error',
                records_synced=0,
                error_message=error_msg
            )
            
            self.sync_status['market_data'] = sync_status
            return sync_status
    
    def get_sync_status(self, service: Optional[str] = None) -> Dict[str, SyncStatus]:
        """
        Get synchronization status.
        
        Args:
            service: Specific service to get status for (None for all)
            
        Returns:
            Dictionary of sync status objects
        """
        if service:
            return {service: self.sync_status.get(service)}
        else:
            return self.sync_status.copy()
    
    def get_sync_health(self) -> Dict[str, Any]:
        """
        Get overall synchronization health status.
        
        Returns:
            Health status dictionary
        """
        try:
            total_services = len(self.sync_status)
            healthy_services = sum(
                1 for status in self.sync_status.values()
                if status.status == 'success'
            )
            
            # Check for recent sync failures
            recent_failures = []
            for service, status in self.sync_status.items():
                if status.status == 'error':
                    time_since_sync = datetime.utcnow() - status.last_sync
                    if time_since_sync < timedelta(hours=1):
                        recent_failures.append(service)
            
            health_status = 'healthy'
            if recent_failures:
                health_status = 'degraded'
            if healthy_services == 0:
                health_status = 'unhealthy'
            
            return {
                'status': health_status,
                'service': 'data_synchronization',
                'total_services': total_services,
                'healthy_services': healthy_services,
                'recent_failures': recent_failures,
                'sync_interval_minutes': self.sync_interval_minutes,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'data_synchronization',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _synchronization_loop(self) -> None:
        """Main synchronization loop."""
        logger.info("Data synchronization loop started")
        
        while not self._stop_event.is_set():
            try:
                # Perform synchronization for each service
                self._perform_synchronization_cycle()
                
                # Wait for next sync interval
                self._stop_event.wait(self.sync_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in synchronization loop: {str(e)}")
                # Wait before retrying
                self._stop_event.wait(60)
        
        logger.info("Data synchronization loop stopped")
    
    def _perform_synchronization_cycle(self) -> None:
        """Perform one synchronization cycle."""
        logger.info("Starting synchronization cycle")
        
        try:
            # Sync portfolio data
            if self.sync_config.get('portfolio_data', {}).enabled:
                self.sync_portfolio_data()
            
            # Sync trade data
            if self.sync_config.get('trade_data', {}).enabled:
                self.sync_trade_data()
            
            # Sync market data
            if self.sync_config.get('market_data', {}).enabled:
                self.sync_market_data()
            
            logger.info("Synchronization cycle completed")
            
        except Exception as e:
            logger.error(f"Error in synchronization cycle: {str(e)}")
    
    def _initialize_sync_configs(self) -> None:
        """Initialize synchronization configurations."""
        self.sync_config = {
            'portfolio_data': SyncConfig(
                enabled=True,
                interval_minutes=self.sync_interval_minutes,
                batch_size=self.batch_size,
                retry_attempts=self.retry_attempts,
                timeout_seconds=self.timeout_seconds
            ),
            'trade_data': SyncConfig(
                enabled=True,
                interval_minutes=self.sync_interval_minutes,
                batch_size=self.batch_size,
                retry_attempts=self.retry_attempts,
                timeout_seconds=self.timeout_seconds
            ),
            'market_data': SyncConfig(
                enabled=True,
                interval_minutes=self.sync_interval_minutes,
                batch_size=self.batch_size,
                retry_attempts=self.retry_attempts,
                timeout_seconds=self.timeout_seconds
            )
        }
    
    def _calculate_portfolio_risk_metrics(self, portfolio_data) -> Optional[Dict[str, Any]]:
        """Calculate risk metrics for portfolio data."""
        try:
            # This would integrate with the actual risk calculation services
            # For now, return mock risk metrics
            return {
                'var_95': 100.0,
                'var_99': 150.0,
                'portfolio_volatility': 0.15,
                'max_drawdown': 0.05,
                'sharpe_ratio': 1.2,
                'calculated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio risk metrics: {str(e)}")
            return None
    
    def _get_risk_limits(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get risk limits for a portfolio."""
        # This would integrate with the risk limits manager
        # For now, return default risk limits
        return [
            {
                'limit_type': 'position_size',
                'limit_value': 0.15,
                'limit_unit': 'percentage'
            },
            {
                'limit_type': 'daily_loss',
                'limit_value': 1000.0,
                'limit_unit': 'dollars'
            }
        ]


# Global data synchronization service instance
_data_sync_service = None


def get_data_sync_service() -> DataSynchronizationService:
    """Get global data synchronization service instance."""
    global _data_sync_service
    
    if _data_sync_service is None:
        _data_sync_service = DataSynchronizationService()
    
    return _data_sync_service


def initialize_data_sync_service(
    sync_interval_minutes: int = 15
) -> DataSynchronizationService:
    """Initialize data synchronization service."""
    global _data_sync_service
    
    _data_sync_service = DataSynchronizationService(
        sync_interval_minutes=sync_interval_minutes
    )
    
    logger.info("Data synchronization service initialized")
    return _data_sync_service
























