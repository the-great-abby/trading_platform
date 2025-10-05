"""
Portfolio Service Integration

Integration with the existing portfolio service for the comprehensive
risk management framework.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from ..utils.risk_utils import CacheUtils, PerformanceUtils


logger = logging.getLogger(__name__)


@dataclass
class PortfolioData:
    """Portfolio data structure for risk management."""
    portfolio_id: str
    positions: List[Dict[str, Any]]
    total_value: float
    cash_balance: float
    last_updated: datetime
    metadata: Dict[str, Any]


class PortfolioServiceIntegration:
    """
    Integration with the existing portfolio service.
    
    Provides seamless integration between the risk management framework
    and the existing portfolio management system.
    """
    
    def __init__(
        self,
        portfolio_service_url: str = "http://enhanced-portfolio-service:80",
        timeout_seconds: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize portfolio service integration.
        
        Args:
            portfolio_service_url: URL of the portfolio service
            timeout_seconds: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.portfolio_service_url = portfolio_service_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Set up session with proper headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RiskManagementService/1.0.0'
        })
    
    @PerformanceUtils.measure_execution_time
    def get_portfolio_data(
        self,
        portfolio_id: str,
        include_positions: bool = True,
        include_performance: bool = True
    ) -> Optional[PortfolioData]:
        """
        Get portfolio data from the portfolio service.
        
        Args:
            portfolio_id: Portfolio identifier
            include_positions: Whether to include position data
            include_performance: Whether to include performance metrics
            
        Returns:
            PortfolioData object or None if failed
        """
        logger.info(f"Fetching portfolio data for {portfolio_id}")
        
        try:
            # Build request parameters
            params = {
                'include_positions': include_positions,
                'include_performance': include_performance
            }
            
            # Make request to portfolio service
            response = self._make_request(
                'GET',
                f'/api/portfolios/{portfolio_id}',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch portfolio data for {portfolio_id}")
                return None
            
            # Parse response
            portfolio_data = self._parse_portfolio_response(response, portfolio_id)
            
            if portfolio_data:
                logger.info(f"Successfully fetched portfolio data for {portfolio_id}")
                return portfolio_data
            else:
                logger.error(f"Failed to parse portfolio data for {portfolio_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching portfolio data for {portfolio_id}: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def get_portfolio_positions(
        self,
        portfolio_id: str,
        as_of_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get portfolio positions from the portfolio service.
        
        Args:
            portfolio_id: Portfolio identifier
            as_of_date: Optional date to get positions as of
            
        Returns:
            List of position dictionaries
        """
        logger.info(f"Fetching portfolio positions for {portfolio_id}")
        
        try:
            # Build request parameters
            params = {}
            if as_of_date:
                params['as_of_date'] = as_of_date.isoformat()
            
            # Make request to portfolio service
            response = self._make_request(
                'GET',
                f'/api/portfolios/{portfolio_id}/positions',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch positions for {portfolio_id}")
                return []
            
            # Parse positions from response
            positions = response.get('data', {}).get('positions', [])
            
            # Normalize position data for risk management
            normalized_positions = self._normalize_positions(positions)
            
            logger.info(f"Successfully fetched {len(normalized_positions)} positions for {portfolio_id}")
            return normalized_positions
            
        except Exception as e:
            logger.error(f"Error fetching positions for {portfolio_id}: {str(e)}")
            return []
    
    @PerformanceUtils.measure_execution_time
    def get_portfolio_performance(
        self,
        portfolio_id: str,
        period_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get portfolio performance data from the portfolio service.
        
        Args:
            portfolio_id: Portfolio identifier
            period_days: Number of days for performance calculation
            
        Returns:
            Performance data dictionary or None if failed
        """
        logger.info(f"Fetching portfolio performance for {portfolio_id}")
        
        try:
            # Build request parameters
            params = {
                'period_days': period_days
            }
            
            # Make request to portfolio service
            response = self._make_request(
                'GET',
                f'/api/portfolios/{portfolio_id}/performance',
                params=params
            )
            
            if not response:
                logger.error(f"Failed to fetch performance for {portfolio_id}")
                return None
            
            # Parse performance data
            performance_data = response.get('data', {})
            
            logger.info(f"Successfully fetched performance data for {portfolio_id}")
            return performance_data
            
        except Exception as e:
            logger.error(f"Error fetching performance for {portfolio_id}: {str(e)}")
            return None
    
    @PerformanceUtils.measure_execution_time
    def update_portfolio_risk_metrics(
        self,
        portfolio_id: str,
        risk_metrics: Dict[str, Any]
    ) -> bool:
        """
        Update portfolio with risk metrics from risk management service.
        
        Args:
            portfolio_id: Portfolio identifier
            risk_metrics: Risk metrics data to update
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Updating portfolio risk metrics for {portfolio_id}")
        
        try:
            # Prepare request data
            request_data = {
                'risk_metrics': risk_metrics,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Make request to portfolio service
            response = self._make_request(
                'PUT',
                f'/api/portfolios/{portfolio_id}/risk-metrics',
                json=request_data
            )
            
            if response and response.get('status') == 'success':
                logger.info(f"Successfully updated risk metrics for {portfolio_id}")
                return True
            else:
                logger.error(f"Failed to update risk metrics for {portfolio_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating risk metrics for {portfolio_id}: {str(e)}")
            return False
    
    @PerformanceUtils.measure_execution_time
    def get_portfolio_list(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get list of portfolios from the portfolio service.
        
        Args:
            limit: Maximum number of portfolios to return
            offset: Number of portfolios to skip
            
        Returns:
            List of portfolio summaries
        """
        logger.info(f"Fetching portfolio list (limit={limit}, offset={offset})")
        
        try:
            # Build request parameters
            params = {
                'limit': limit,
                'offset': offset
            }
            
            # Make request to portfolio service
            response = self._make_request(
                'GET',
                '/api/portfolios',
                params=params
            )
            
            if not response:
                logger.error("Failed to fetch portfolio list")
                return []
            
            # Parse portfolio list
            portfolios = response.get('data', {}).get('portfolios', [])
            
            logger.info(f"Successfully fetched {len(portfolios)} portfolios")
            return portfolios
            
        except Exception as e:
            logger.error(f"Error fetching portfolio list: {str(e)}")
            return []
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to portfolio service with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON payload
            
        Returns:
            Response data or None if failed
        """
        url = f"{self.portfolio_service_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout_seconds
                )
                
                # Check response status
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Portfolio not found: {endpoint}")
                    return None
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
    
    def _parse_portfolio_response(
        self,
        response: Dict[str, Any],
        portfolio_id: str
    ) -> Optional[PortfolioData]:
        """
        Parse portfolio response from portfolio service.
        
        Args:
            response: Response from portfolio service
            portfolio_id: Portfolio identifier
            
        Returns:
            PortfolioData object or None if parsing failed
        """
        try:
            data = response.get('data', {})
            
            # Extract portfolio information
            portfolio_info = data.get('portfolio', {})
            positions_data = data.get('positions', [])
            performance_data = data.get('performance', {})
            
            # Calculate total value
            total_value = portfolio_info.get('total_value', 0.0)
            cash_balance = portfolio_info.get('cash_balance', 0.0)
            
            # Parse last updated timestamp
            last_updated_str = portfolio_info.get('last_updated', datetime.utcnow().isoformat())
            try:
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            except:
                last_updated = datetime.utcnow()
            
            # Normalize positions
            normalized_positions = self._normalize_positions(positions_data)
            
            # Create metadata
            metadata = {
                'performance': performance_data,
                'portfolio_info': portfolio_info,
                'source': 'portfolio_service',
                'fetched_at': datetime.utcnow().isoformat()
            }
            
            return PortfolioData(
                portfolio_id=portfolio_id,
                positions=normalized_positions,
                total_value=total_value,
                cash_balance=cash_balance,
                last_updated=last_updated,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing portfolio response: {str(e)}")
            return None
    
    def _normalize_positions(
        self,
        positions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize position data for risk management.
        
        Args:
            positions: Raw position data from portfolio service
            
        Returns:
            Normalized position data
        """
        normalized_positions = []
        
        for position in positions:
            try:
                # Extract position data
                symbol = position.get('symbol', '')
                quantity = position.get('quantity', 0)
                current_price = position.get('current_price', 0.0)
                market_value = position.get('market_value', quantity * current_price)
                
                # Calculate weight (will be normalized later if needed)
                weight = position.get('weight', 0.0)
                
                # Extract additional metadata
                asset_type = position.get('asset_type', 'stock')
                sector = position.get('sector', 'unknown')
                
                # Create normalized position
                normalized_position = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'current_value': market_value,
                    'weight': weight,
                    'asset_type': asset_type,
                    'sector': sector,
                    'unrealized_pnl': position.get('unrealized_pnl', 0.0),
                    'cost_basis': position.get('cost_basis', market_value),
                    'last_updated': position.get('last_updated', datetime.utcnow().isoformat())
                }
                
                normalized_positions.append(normalized_position)
                
            except Exception as e:
                logger.warning(f"Error normalizing position {position.get('symbol', 'unknown')}: {str(e)}")
                continue
        
        return normalized_positions
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of portfolio service integration.
        
        Returns:
            Health status dictionary
        """
        try:
            response = self._make_request('GET', '/health')
            
            if response:
                return {
                    'status': 'healthy',
                    'service': 'portfolio_service_integration',
                    'portfolio_service_status': response.get('status', 'unknown'),
                    'last_check': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'portfolio_service_integration',
                    'error': 'Portfolio service not responding',
                    'last_check': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'portfolio_service_integration',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def clear_cache(self) -> None:
        """Clear integration cache."""
        # Clear any cached data if implemented
        logger.info("Portfolio service integration cache cleared")


# Global portfolio service integration instance
_portfolio_integration = None


def get_portfolio_integration() -> PortfolioServiceIntegration:
    """Get global portfolio service integration instance."""
    global _portfolio_integration
    
    if _portfolio_integration is None:
        _portfolio_integration = PortfolioServiceIntegration()
    
    return _portfolio_integration


def initialize_portfolio_integration(
    portfolio_service_url: str = None
) -> PortfolioServiceIntegration:
    """Initialize portfolio service integration."""
    global _portfolio_integration
    
    _portfolio_integration = PortfolioServiceIntegration(
        portfolio_service_url=portfolio_service_url or "http://enhanced-portfolio-service:80"
    )
    
    logger.info("Portfolio service integration initialized")
    return _portfolio_integration












