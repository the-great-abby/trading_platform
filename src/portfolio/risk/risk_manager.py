"""
Risk Manager Service
Service for portfolio risk calculations and monitoring
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import uuid
from scipy import stats

from ..models import Portfolio, RiskMetrics, Position


class RiskManager:
    """Service for portfolio risk calculations and monitoring"""
    
    def __init__(self, repository=None, market_data_service=None):
        """Initialize risk manager with dependencies"""
        self.repository = repository
        self.market_data_service = market_data_service
    
    def calculate_portfolio_risk(self,
                               portfolio: Portfolio,
                               lookback_period: int = 252,
                               confidence_levels: List[float] = None) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]
        
        # Get market data
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            return self._create_default_risk_metrics(portfolio)
        
        asset_ids = asset_data['asset_ids']
        cov_matrix = asset_data['covariance_matrix']
        expected_returns = asset_data.get('expected_returns', np.array([0.08] * len(asset_ids)))
        
        # Get current portfolio weights
        weights = self._get_portfolio_weights(portfolio, asset_ids)
        
        # Calculate portfolio variance and volatility
        portfolio_variance = weights.T @ cov_matrix @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Calculate Value at Risk (VaR)
        var_metrics = self._calculate_var(portfolio, weights, portfolio_volatility, confidence_levels)
        
        # Calculate Conditional VaR (CVaR)
        cvar_metrics = self._calculate_cvar(portfolio, weights, portfolio_volatility, confidence_levels)
        
        # Calculate risk contributions
        risk_contributions = self._calculate_risk_contributions(weights, cov_matrix)
        risk_contributions_dict = dict(zip(asset_ids, risk_contributions))
        
        # Calculate systematic and idiosyncratic risk
        systematic_risk, idiosyncratic_risk = self._calculate_risk_decomposition(weights, cov_matrix)
        
        # Calculate factor exposures
        factor_exposures = self._calculate_factor_exposures(portfolio, asset_ids)
        
        # Calculate correlation metrics
        correlation_metrics = self._calculate_correlation_metrics(cov_matrix)
        
        # Perform stress tests
        stress_test_results = self._perform_stress_tests(portfolio, weights, cov_matrix)
        
        # Calculate risk-adjusted metrics
        risk_adjusted_metrics = self._calculate_risk_adjusted_metrics(portfolio, weights, expected_returns, portfolio_volatility)
        
        # Create risk metrics object
        risk_metrics = RiskMetrics(
            portfolio_id=portfolio.portfolio_id,
            calculation_date=datetime.now(),
            lookback_period=lookback_period,
            var_95=var_metrics.get(0.95, 0.0),
            var_99=var_metrics.get(0.99, 0.0),
            cvar_95=cvar_metrics.get(0.95, 0.0),
            cvar_99=cvar_metrics.get(0.99, 0.0),
            systematic_risk=systematic_risk,
            idiosyncratic_risk=idiosyncratic_risk,
            risk_contributions=risk_contributions_dict,
            market_beta=factor_exposures.get('market_beta', 1.0),
            size_factor_exposure=factor_exposures.get('size_factor', 0.0),
            value_factor_exposure=factor_exposures.get('value_factor', 0.0),
            momentum_factor_exposure=factor_exposures.get('momentum_factor', 0.0),
            quality_factor_exposure=factor_exposures.get('quality_factor', 0.0),
            average_correlation=correlation_metrics.get('average_correlation', 0.0),
            max_correlation=correlation_metrics.get('max_correlation', 0.0),
            min_correlation=correlation_metrics.get('min_correlation', 0.0),
            stress_test_results=stress_test_results,
            information_ratio=risk_adjusted_metrics.get('information_ratio', 0.0),
            tracking_error=risk_adjusted_metrics.get('tracking_error', 0.0),
            max_drawdown=risk_adjusted_metrics.get('max_drawdown', 0.0),
            calmar_ratio=risk_adjusted_metrics.get('calmar_ratio', 0.0),
            sortino_ratio=risk_adjusted_metrics.get('sortino_ratio', 0.0)
        )
        
        # Save risk metrics
        if self.repository:
            self.repository.save_risk_metrics(risk_metrics)
        
        return risk_metrics
    
    def monitor_risk_limits(self, portfolio: Portfolio, risk_limits: Dict[str, float]) -> Dict[str, Any]:
        """Monitor portfolio against risk limits"""
        
        risk_metrics = self.calculate_portfolio_risk(portfolio)
        
        violations = []
        warnings = []
        
        # Check VaR limits
        if 'var_95_limit' in risk_limits:
            if abs(risk_metrics.var_95) > risk_limits['var_95_limit']:
                violations.append(f"VaR 95% exceeds limit: {abs(risk_metrics.var_95):.2%} > {risk_limits['var_95_limit']:.2%}")
        
        # Check volatility limits
        if 'volatility_limit' in risk_limits:
            portfolio_volatility = np.sqrt(risk_metrics.systematic_risk + risk_metrics.idiosyncratic_risk)
            if portfolio_volatility > risk_limits['volatility_limit']:
                violations.append(f"Portfolio volatility exceeds limit: {portfolio_volatility:.2%} > {risk_limits['volatility_limit']:.2%}")
        
        # Check concentration limits
        if 'max_single_asset_weight' in risk_limits:
            max_weight = max(risk_metrics.risk_contributions.values()) if risk_metrics.risk_contributions else 0
            if max_weight > risk_limits['max_single_asset_weight']:
                violations.append(f"Maximum asset weight exceeds limit: {max_weight:.2%} > {risk_limits['max_single_asset_weight']:.2%}")
        
        # Check correlation limits
        if 'max_correlation_limit' in risk_limits:
            if risk_metrics.max_correlation > risk_limits['max_correlation_limit']:
                warnings.append(f"Maximum correlation exceeds limit: {risk_metrics.max_correlation:.2%} > {risk_limits['max_correlation_limit']:.2%}")
        
        return {
            "risk_metrics": risk_metrics,
            "violations": violations,
            "warnings": warnings,
            "status": "VIOLATION" if violations else "WARNING" if warnings else "OK"
        }
    
    def calculate_scenario_analysis(self,
                                  portfolio: Portfolio,
                                  scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio performance under different scenarios"""
        
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            return {"error": "Insufficient market data"}
        
        asset_ids = asset_data['asset_ids']
        weights = self._get_portfolio_weights(portfolio, asset_ids)
        
        scenario_results = {}
        
        for scenario in scenarios:
            scenario_name = scenario.get('name', 'Unknown Scenario')
            asset_returns = scenario.get('asset_returns', {})
            
            # Calculate portfolio return under scenario
            portfolio_return = 0.0
            for i, asset_id in enumerate(asset_ids):
                asset_return = asset_returns.get(asset_id, 0.0)
                portfolio_return += weights[i] * asset_return
            
            scenario_results[scenario_name] = portfolio_return
        
        return {
            "scenario_results": scenario_results,
            "best_case": max(scenario_results.values()) if scenario_results else 0.0,
            "worst_case": min(scenario_results.values()) if scenario_results else 0.0,
            "scenario_range": max(scenario_results.values()) - min(scenario_results.values()) if scenario_results else 0.0
        }
    
    def _get_asset_data(self, portfolio: Portfolio) -> Optional[Dict[str, Any]]:
        """Get market data for portfolio assets"""
        if not portfolio.positions:
            return None
        
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        
        if not self.market_data_service:
            # Use default values
            n_assets = len(asset_ids)
            expected_returns = np.array([0.08] * n_assets)
            cov_matrix = self._create_default_covariance_matrix(asset_ids)
            return {
                'asset_ids': asset_ids,
                'expected_returns': expected_returns,
                'covariance_matrix': cov_matrix
            }
        
        try:
            # Get expected returns
            expected_returns = []
            for asset_id in asset_ids:
                asset_return = self.market_data_service.get_expected_return(asset_id)
                expected_returns.append(asset_return if asset_return is not None else 0.08)
            
            expected_returns = np.array(expected_returns)
            
            # Get covariance matrix
            cov_matrix = self.market_data_service.get_covariance_matrix(asset_ids)
            
            if cov_matrix is None or cov_matrix.shape != (len(asset_ids), len(asset_ids)):
                cov_matrix = self._create_default_covariance_matrix(asset_ids)
            
            return {
                'asset_ids': asset_ids,
                'expected_returns': expected_returns,
                'covariance_matrix': cov_matrix
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get market data: {str(e)}")
    
    def _get_portfolio_weights(self, portfolio: Portfolio, asset_ids: List[str]) -> np.ndarray:
        """Get portfolio weights as numpy array"""
        weights = []
        total_value = portfolio.calculate_total_value()
        
        if total_value == 0:
            return np.zeros(len(asset_ids))
        
        for asset_id in asset_ids:
            position = next((p for p in portfolio.positions if p.asset_id == asset_id), None)
            if position:
                weight = position.market_value / total_value
                weights.append(weight)
            else:
                weights.append(0.0)
        
        return np.array(weights)
    
    def _calculate_var(self, portfolio: Portfolio, weights: np.ndarray, portfolio_volatility: float, confidence_levels: List[float]) -> Dict[float, float]:
        """Calculate Value at Risk"""
        var_metrics = {}
        
        for confidence in confidence_levels:
            # Use normal distribution assumption
            z_score = stats.norm.ppf(1 - confidence)
            var = z_score * portfolio_volatility
            
            # Convert to dollar amount
            var_dollar = var * portfolio.total_value
            var_metrics[confidence] = var_dollar
        
        return var_metrics
    
    def _calculate_cvar(self, portfolio: Portfolio, weights: np.ndarray, portfolio_volatility: float, confidence_levels: List[float]) -> Dict[float, float]:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        cvar_metrics = {}
        
        for confidence in confidence_levels:
            # CVaR = VaR * (1 + 1/(1-confidence) * phi(alpha)/Phi(alpha))
            alpha = 1 - confidence
            z_alpha = stats.norm.ppf(alpha)
            
            # Calculate CVaR adjustment factor
            phi_z = stats.norm.pdf(z_alpha)
            Phi_z = stats.norm.cdf(z_alpha)
            cvar_factor = 1 + (1 / alpha) * (phi_z / Phi_z)
            
            # Calculate CVaR
            var = z_alpha * portfolio_volatility
            cvar = var * cvar_factor
            
            # Convert to dollar amount
            cvar_dollar = cvar * portfolio.total_value
            cvar_metrics[confidence] = cvar_dollar
        
        return cvar_metrics
    
    def _calculate_risk_contributions(self, weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
        """Calculate risk contributions for each asset"""
        # Portfolio variance
        portfolio_variance = weights.T @ cov_matrix @ weights
        
        if portfolio_variance <= 0:
            return np.zeros(len(weights))
        
        # Portfolio volatility
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Marginal risk contributions
        marginal_contributions = cov_matrix @ weights
        
        # Risk contributions (marginal contribution * weight / portfolio volatility)
        risk_contributions = (marginal_contributions * weights) / portfolio_volatility
        
        return risk_contributions
    
    def _calculate_risk_decomposition(self, weights: np.ndarray, cov_matrix: np.ndarray) -> Tuple[float, float]:
        """Calculate systematic and idiosyncratic risk decomposition"""
        # Simplified decomposition - in practice would use factor models
        portfolio_variance = weights.T @ cov_matrix @ weights
        
        # Assume 70% systematic, 30% idiosyncratic (simplified)
        systematic_risk = portfolio_variance * 0.7
        idiosyncratic_risk = portfolio_variance * 0.3
        
        return systematic_risk, idiosyncratic_risk
    
    def _calculate_factor_exposures(self, portfolio: Portfolio, asset_ids: List[str]) -> Dict[str, float]:
        """Calculate factor exposures"""
        # Simplified factor exposures - in practice would use factor models
        exposures = {
            'market_beta': 1.0,  # Default market beta
            'size_factor': 0.0,
            'value_factor': 0.0,
            'momentum_factor': 0.0,
            'quality_factor': 0.0
        }
        
        # Calculate weighted average exposures
        if self.market_data_service:
            for position in portfolio.positions:
                weight = position.market_value / portfolio.total_value if portfolio.total_value > 0 else 0
                
                # Get asset factor exposures
                asset_exposures = self.market_data_service.get_factor_exposures(position.asset_id)
                if asset_exposures:
                    for factor, exposure in asset_exposures.items():
                        if factor in exposures:
                            exposures[factor] += weight * exposure
        
        return exposures
    
    def _calculate_correlation_metrics(self, cov_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate correlation metrics"""
        # Convert covariance to correlation
        std_devs = np.sqrt(np.diag(cov_matrix))
        correlation_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # Get upper triangle (excluding diagonal)
        upper_triangle = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
        
        if len(upper_triangle) == 0:
            return {
                'average_correlation': 0.0,
                'max_correlation': 0.0,
                'min_correlation': 0.0
            }
        
        return {
            'average_correlation': np.mean(upper_triangle),
            'max_correlation': np.max(upper_triangle),
            'min_correlation': np.min(upper_triangle)
        }
    
    def _perform_stress_tests(self, portfolio: Portfolio, weights: np.ndarray, cov_matrix: np.ndarray) -> Dict[str, float]:
        """Perform stress tests"""
        stress_scenarios = {
            "Market Crash (-20%)": -0.20,
            "Market Crash (-10%)": -0.10,
            "Interest Rate Shock (+2%)": -0.05,
            "Currency Crisis": -0.15,
            "Oil Price Shock": -0.08
        }
        
        stress_results = {}
        
        for scenario_name, shock_return in stress_scenarios.items():
            # Apply shock to all assets (simplified)
            stressed_returns = np.full(len(weights), shock_return)
            portfolio_return = np.dot(weights, stressed_returns)
            stress_results[scenario_name] = portfolio_return
        
        return stress_results
    
    def _calculate_risk_adjusted_metrics(self, portfolio: Portfolio, weights: np.ndarray, expected_returns: np.ndarray, portfolio_volatility: float) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics"""
        # Portfolio expected return
        portfolio_return = np.dot(weights, expected_returns)
        
        # Risk-free rate
        risk_free_rate = 0.02
        
        # Sharpe ratio
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Information ratio (vs market benchmark)
        market_return = 0.08  # Default market return
        tracking_error = 0.05  # Default tracking error
        information_ratio = (portfolio_return - market_return) / tracking_error if tracking_error > 0 else 0
        
        # Sortino ratio (using downside deviation)
        downside_volatility = portfolio_volatility * 0.7  # Simplified
        sortino_ratio = (portfolio_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        
        # Max drawdown (simplified)
        max_drawdown = portfolio_volatility * 2.0  # Rough estimate
        
        # Calmar ratio
        calmar_ratio = portfolio_return / max_drawdown if max_drawdown > 0 else 0
        
        return {
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio
        }
    
    def _create_default_covariance_matrix(self, asset_ids: List[str]) -> np.ndarray:
        """Create default covariance matrix"""
        n_assets = len(asset_ids)
        
        # Create a realistic covariance matrix with some correlation
        base_volatility = 0.20  # 20% base volatility
        
        # Create correlation matrix with moderate correlations
        correlation_matrix = np.eye(n_assets)
        for i in range(n_assets):
            for j in range(i+1, n_assets):
                correlation = 0.3 + 0.2 * np.random.random()  # 0.3 to 0.5 correlation
                correlation_matrix[i, j] = correlation
                correlation_matrix[j, i] = correlation
        
        # Create covariance matrix
        volatilities = np.array([base_volatility + 0.05 * np.random.random() for _ in range(n_assets)])
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        
        return cov_matrix
    
    def _create_default_risk_metrics(self, portfolio: Portfolio) -> RiskMetrics:
        """Create default risk metrics when data is unavailable"""
        return RiskMetrics(
            portfolio_id=portfolio.portfolio_id,
            calculation_date=datetime.now(),
            var_95=-0.05 * portfolio.total_value,  # 5% VaR
            var_99=-0.08 * portfolio.total_value,  # 8% VaR
            cvar_95=-0.06 * portfolio.total_value,  # 6% CVaR
            cvar_99=-0.10 * portfolio.total_value,  # 10% CVaR
            systematic_risk=0.04,  # 20% volatility
            idiosyncratic_risk=0.01,  # 10% idiosyncratic
            market_beta=1.0,
            average_correlation=0.3,
            max_correlation=0.8,
            min_correlation=0.0
        )



