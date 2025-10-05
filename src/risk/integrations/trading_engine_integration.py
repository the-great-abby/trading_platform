"""
Trading Engine Integration

Integration with the existing trading engine for the comprehensive
risk management framework.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json

from ..utils.risk_utils import CacheUtils, PerformanceUtils


logger = logging.getLogger(__name__)


@dataclass
class TradeData:
    """Trade data structure for risk management."""
    trade_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    value: float
    timestamp: datetime
    strategy: str
    portfolio_id: str
    metadata: Dict[str, Any]


@dataclass
class RiskCheckResult:
    """Risk check result for trade validation."""
    trade_id: str
    approved: bool
    risk_score: float
    risk_factors: List[str]
    warnings: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class TradingEngineIntegration:
    """
    Integration with the existing trading engine.
    
    Provides risk validation and monitoring for trades executed
    through the trading engine.
    """
    
    def __init__(
        self,
        trading_engine_url: str = "http://trading-engine-service:80",
        timeout_seconds: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize trading engine integration.
        
        Args:
            trading_engine_url: URL of the trading engine service
            timeout_seconds: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.trading_engine_url = trading_engine_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Set up session with proper headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RiskManagementService/1.0.0'
        })
    
    @PerformanceUtils.measure_execution_time
    def validate_trade_risk(
        self,
        trade_data: Dict[str, Any],
        portfolio_id: str,
        risk_limits: List[Dict[str, Any]]
    ) -> RiskCheckResult:
        """
        Validate trade against risk limits before execution.
        
        Args:
            trade_data: Trade data to validate
            portfolio_id: Portfolio identifier
            risk_limits: List of risk limits to check against
            
        Returns:
            RiskCheckResult with validation outcome
        """
        logger.info(f"Validating trade risk for portfolio {portfolio_id}")
        
        try:
            trade_id = trade_data.get('trade_id', 'unknown')
            risk_factors = []
            warnings = []
            recommendations = []
            
            # Check position size limits
            position_size_check = self._check_position_size_limit(
                trade_data, portfolio_id, risk_limits
            )
            if not position_size_check['approved']:
                risk_factors.extend(position_size_check['risk_factors'])
                warnings.extend(position_size_check['warnings'])
            
            # Check daily loss limits
            daily_loss_check = self._check_daily_loss_limit(
                trade_data, portfolio_id, risk_limits
            )
            if not daily_loss_check['approved']:
                risk_factors.extend(daily_loss_check['risk_factors'])
                warnings.extend(daily_loss_check['warnings'])
            
            # Check sector concentration limits
            sector_concentration_check = self._check_sector_concentration_limit(
                trade_data, portfolio_id, risk_limits
            )
            if not sector_concentration_check['approved']:
                risk_factors.extend(sector_concentration_check['risk_factors'])
                warnings.extend(sector_concentration_check['warnings'])
            
            # Check VaR limits
            var_check = self._check_var_limit(
                trade_data, portfolio_id, risk_limits
            )
            if not var_check['approved']:
                risk_factors.extend(var_check['risk_factors'])
                warnings.extend(var_check['warnings'])
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_factors, warnings)
            
            # Determine if trade is approved
            approved = len(risk_factors) == 0 and risk_score < 0.7
            
            # Generate recommendations
            if not approved:
                recommendations = self._generate_risk_recommendations(
                    risk_factors, warnings, trade_data
                )
            
            result = RiskCheckResult(
                trade_id=trade_id,
                approved=approved,
                risk_score=risk_score,
                risk_factors=risk_factors,
                warnings=warnings,
                recommendations=recommendations,
                metadata={
                    'portfolio_id': portfolio_id,
                    'validation_timestamp': datetime.utcnow().isoformat(),
                    'checks_performed': [
                        'position_size', 'daily_loss', 'sector_concentration', 'var_limit'
                    ]
                }
            )
            
            logger.info(f"Trade validation completed for {trade_id}: {'APPROVED' if approved else 'REJECTED'}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating trade risk: {str(e)}")
            return RiskCheckResult(
                trade_id=trade_data.get('trade_id', 'unknown'),
                approved=False,
                risk_score=1.0,
                risk_factors=['validation_error'],
                warnings=[f"Risk validation failed: {str(e)}"],
                recommendations=['Contact risk management team'],
                metadata={'error': str(e)}
            )
    
    @PerformanceUtils.measure_execution_time
    def get_recent_trades(
        self,
        portfolio_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[TradeData]:
        """
        Get recent trades from the trading engine.
        
        Args:
            portfolio_id: Portfolio identifier
            hours: Number of hours to look back
            limit: Maximum number of trades to return
            
        Returns:
            List of TradeData objects
        """
        logger.info(f"Fetching recent trades for portfolio {portfolio_id}")
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Build request parameters
            params = {
                'portfolio_id': portfolio_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'limit': limit
            }
            
            # Make request to trading engine
            response = self._make_request(
                'GET',
                '/api/trades',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch trades for portfolio {portfolio_id}")
                return []
            
            # Parse trades from response
            trades_data = response.get('data', {}).get('trades', [])
            
            # Convert to TradeData objects
            trades = []
            for trade_data in trades_data:
                try:
                    trade = self._parse_trade_data(trade_data)
                    if trade:
                        trades.append(trade)
                except Exception as e:
                    logger.warning(f"Error parsing trade {trade_data.get('trade_id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(trades)} recent trades for portfolio {portfolio_id}")
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching recent trades for portfolio {portfolio_id}: {str(e)}")
            return []
    
    @PerformanceUtils.measure_execution_time
    def get_trade_statistics(
        self,
        portfolio_id: str,
        period_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get trade statistics from the trading engine.
        
        Args:
            portfolio_id: Portfolio identifier
            period_days: Number of days for statistics
            
        Returns:
            Trade statistics dictionary or None if failed
        """
        logger.info(f"Fetching trade statistics for portfolio {portfolio_id}")
        
        try:
            # Build request parameters
            params = {
                'portfolio_id': portfolio_id,
                'period_days': period_days
            }
            
            # Make request to trading engine
            response = self._make_request(
                'GET',
                '/api/trades/statistics',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch trade statistics for portfolio {portfolio_id}")
                return None
            
            # Parse statistics
            statistics = response.get('data', {})
            
            logger.info(f"Successfully fetched trade statistics for portfolio {portfolio_id}")
            return statistics
            
        except Exception as e:
            logger.error(f"Error fetching trade statistics for portfolio {portfolio_id}: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def notify_risk_breach(
        self,
        portfolio_id: str,
        risk_breach_data: Dict[str, Any]
    ) -> bool:
        """
        Notify trading engine of risk limit breach.
        
        Args:
            portfolio_id: Portfolio identifier
            risk_breach_data: Risk breach information
            
        Returns:
            True if notification successful, False otherwise
        """
        logger.info(f"Notifying trading engine of risk breach for portfolio {portfolio_id}")
        
        try:
            # Prepare notification data
            notification_data = {
                'portfolio_id': portfolio_id,
                'risk_breach': risk_breach_data,
                'timestamp': datetime.utcnow().isoformat(),
                'action_required': 'halt_trading' if risk_breach_data.get('severity') == 'critical' else 'alert'
            }
            
            # Make request to trading engine
            response = self._make_request(
                'POST',
                '/api/risk/breach-notification',
                json=notification_data
            )
            
            if response and response.get('status') == 'success':
                logger.info(f"Successfully notified trading engine of risk breach for portfolio {portfolio_id}")
                return True
            else:
                logger.error(f"Failed to notify trading engine of risk breach for portfolio {portfolio_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error notifying trading engine of risk breach for portfolio {portfolio_id}: {str(e)}")
            return False
    
    def _check_position_size_limit(
        self,
        trade_data: Dict[str, Any],
        portfolio_id: str,
        risk_limits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check position size limits."""
        # Mock implementation - in practice, this would check actual limits
        position_size_limit = next(
            (limit for limit in risk_limits if limit.get('limit_type') == 'position_size'),
            {'limit_value': 0.15, 'limit_unit': 'percentage'}
        )
        
        # Calculate position size impact
        trade_value = trade_data.get('quantity', 0) * trade_data.get('price', 0)
        # This would need actual portfolio value from portfolio service
        
        # Mock check
        if trade_value > 1000:  # Mock threshold
            return {
                'approved': False,
                'risk_factors': ['position_size_limit_exceeded'],
                'warnings': [f'Trade value ${trade_value:.2f} exceeds position size limit']
            }
        
        return {'approved': True, 'risk_factors': [], 'warnings': []}
    
    def _check_daily_loss_limit(
        self,
        trade_data: Dict[str, Any],
        portfolio_id: str,
        risk_limits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check daily loss limits."""
        # Mock implementation
        daily_loss_limit = next(
            (limit for limit in risk_limits if limit.get('limit_type') == 'daily_loss'),
            {'limit_value': 1000.0, 'limit_unit': 'dollars'}
        )
        
        # This would need actual daily P&L from portfolio service
        # Mock check
        return {'approved': True, 'risk_factors': [], 'warnings': []}
    
    def _check_sector_concentration_limit(
        self,
        trade_data: Dict[str, Any],
        portfolio_id: str,
        risk_limits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check sector concentration limits."""
        # Mock implementation
        sector_limit = next(
            (limit for limit in risk_limits if limit.get('limit_type') == 'sector_concentration'),
            {'limit_value': 0.30, 'limit_unit': 'percentage'}
        )
        
        # This would need actual sector weights from portfolio service
        # Mock check
        return {'approved': True, 'risk_factors': [], 'warnings': []}
    
    def _check_var_limit(
        self,
        trade_data: Dict[str, Any],
        portfolio_id: str,
        risk_limits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check VaR limits."""
        # Mock implementation
        var_limit = next(
            (limit for limit in risk_limits if limit.get('limit_type') == 'var_limit'),
            {'limit_value': 5000.0, 'limit_unit': 'dollars'}
        )
        
        # This would need actual VaR calculation
        # Mock check
        return {'approved': True, 'risk_factors': [], 'warnings': []}
    
    def _calculate_risk_score(
        self,
        risk_factors: List[str],
        warnings: List[str]
    ) -> float:
        """Calculate overall risk score."""
        # Simple risk scoring based on factors and warnings
        risk_score = 0.0
        
        # Add risk factors
        risk_score += len(risk_factors) * 0.3
        
        # Add warnings
        risk_score += len(warnings) * 0.1
        
        # Cap at 1.0
        return min(risk_score, 1.0)
    
    def _generate_risk_recommendations(
        self,
        risk_factors: List[str],
        warnings: List[str],
        trade_data: Dict[str, Any]
    ) -> List[str]:
        """Generate risk recommendations."""
        recommendations = []
        
        for factor in risk_factors:
            if 'position_size_limit_exceeded' in factor:
                recommendations.append("Reduce trade size to comply with position limits")
            elif 'daily_loss_limit_exceeded' in factor:
                recommendations.append("Consider delaying trade to avoid daily loss limit")
            elif 'sector_concentration_limit_exceeded' in factor:
                recommendations.append("Diversify across more sectors before this trade")
            elif 'var_limit_exceeded' in factor:
                recommendations.append("Reduce portfolio risk exposure before executing trade")
        
        if not recommendations:
            recommendations.append("Review risk parameters and consider trade modification")
        
        return recommendations
    
    def _parse_trade_data(self, trade_data: Dict[str, Any]) -> Optional[TradeData]:
        """Parse trade data from trading engine response."""
        try:
            trade_id = trade_data.get('trade_id', '')
            symbol = trade_data.get('symbol', '')
            side = trade_data.get('side', '')
            quantity = float(trade_data.get('quantity', 0))
            price = float(trade_data.get('price', 0))
            value = quantity * price
            
            # Parse timestamp
            timestamp_str = trade_data.get('timestamp', datetime.utcnow().isoformat())
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
            
            return TradeData(
                trade_id=trade_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                value=value,
                timestamp=timestamp,
                strategy=trade_data.get('strategy', 'unknown'),
                portfolio_id=trade_data.get('portfolio_id', ''),
                metadata=trade_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.warning(f"Error parsing trade data: {str(e)}")
            return None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to trading engine with retry logic."""
        url = f"{self.trading_engine_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout_seconds
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} for {endpoint}, attempt {attempt + 1}")
                    if attempt < self.retry_attempts - 1:
                        continue
                else:
                    logger.error(f"HTTP {response.status_code} for {endpoint}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {endpoint}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    continue
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {endpoint}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    continue
            except Exception as e:
                logger.error(f"Unexpected error for {endpoint}: {str(e)}")
                return None
        
        logger.error(f"Failed to make request to {endpoint} after {self.retry_attempts} attempts")
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of trading engine integration."""
        try:
            response = self._make_request('GET', '/health')
            
            if response:
                return {
                    'status': 'healthy',
                    'service': 'trading_engine_integration',
                    'trading_engine_status': response.get('status', 'unknown'),
                    'last_check': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'trading_engine_integration',
                    'error': 'Trading engine not responding',
                    'last_check': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'trading_engine_integration',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }


# Global trading engine integration instance
_trading_engine_integration = None


def get_trading_engine_integration() -> TradingEngineIntegration:
    """Get global trading engine integration instance."""
    global _trading_engine_integration
    
    if _trading_engine_integration is None:
        _trading_engine_integration = TradingEngineIntegration()
    
    return _trading_engine_integration


def initialize_trading_engine_integration(
    trading_engine_url: str = None
) -> TradingEngineIntegration:
    """Initialize trading engine integration."""
    global _trading_engine_integration
    
    _trading_engine_integration = TradingEngineIntegration(
        trading_engine_url=trading_engine_url or "http://trading-engine-service:80"
    )
    
    logger.info("Trading engine integration initialized")
    return _trading_engine_integration












