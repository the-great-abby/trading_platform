"""
Risk Management Integrations Package

Integration modules for connecting the risk management framework
with other trading system components.
"""

from .portfolio_service_integration import (
    PortfolioServiceIntegration,
    PortfolioData,
    get_portfolio_integration,
    initialize_portfolio_integration
)

from .trading_engine_integration import (
    TradingEngineIntegration,
    TradeData,
    RiskCheckResult,
    get_trading_engine_integration,
    initialize_trading_engine_integration
)

from .market_data_service_integration import (
    MarketDataServiceIntegration,
    MarketData,
    HistoricalData,
    get_market_data_integration,
    initialize_market_data_integration
)

from .data_synchronization_service import (
    DataSynchronizationService,
    SyncStatus,
    SyncConfig,
    get_data_sync_service,
    initialize_data_sync_service
)

from .cross_service_monitoring import (
    CrossServiceMonitoring,
    Alert,
    AlertSeverity,
    AlertStatus,
    ServiceHealth,
    MonitoringConfig,
    get_cross_service_monitoring,
    initialize_cross_service_monitoring
)

__all__ = [
    # Portfolio Service Integration
    'PortfolioServiceIntegration',
    'PortfolioData',
    'get_portfolio_integration',
    'initialize_portfolio_integration',
    
    # Trading Engine Integration
    'TradingEngineIntegration',
    'TradeData',
    'RiskCheckResult',
    'get_trading_engine_integration',
    'initialize_trading_engine_integration',
    
    # Market Data Service Integration
    'MarketDataServiceIntegration',
    'MarketData',
    'HistoricalData',
    'get_market_data_integration',
    'initialize_market_data_integration',
    
    # Data Synchronization Service
    'DataSynchronizationService',
    'SyncStatus',
    'SyncConfig',
    'get_data_sync_service',
    'initialize_data_sync_service',
    
    # Cross-Service Monitoring
    'CrossServiceMonitoring',
    'Alert',
    'AlertSeverity',
    'AlertStatus',
    'ServiceHealth',
    'MonitoringConfig',
    'get_cross_service_monitoring',
    'initialize_cross_service_monitoring'
]






















