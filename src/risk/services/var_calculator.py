"""
VaR Calculator Service

Provides Value at Risk (VaR) calculations using various methods for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass

from ..models.risk_metrics import RiskMetrics
from ..models.risk_contributions import RiskContributions


logger = logging.getLogger(__name__)


@dataclass
class VaRCalculationResult:
    """Result of VaR calculation."""
    var_metrics: RiskMetrics
    risk_contributions: Optional[RiskContributions] = None
    calculation_metadata: Dict[str, Any] = None
    confidence_intervals: Dict[str, float] = None


class VaRCalculator:
    """
    Value at Risk (VaR) calculator service.
    
    Provides VaR calculations using historical simulation, parametric,
    and Monte Carlo methods.
    """
    
    def __init__(self, market_data_provider=None):
        """
        Initialize VaR calculator.
        
        Args:
            market_data_provider: Provider for market data (optional)
        """
        self.market_data_provider = market_data_provider
        self.calculation_cache = {}
    
    def calculate_var(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        confidence_levels: List[float] = [0.95, 0.99],
        calculation_method: str = "historical_simulation",
        data_period_days: int = 252,
        include_expected_shortfall: bool = True,
        include_risk_contributions: bool = False,
        portfolio_value: float = 100000.0
    ) -> VaRCalculationResult:
        """
        Calculate Value at Risk for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            portfolio_positions: List of portfolio positions
            confidence_levels: List of confidence levels (e.g., [0.95, 0.99])
            calculation_method: Method to use ('historical_simulation', 'parametric', 'monte_carlo')
            data_period_days: Number of days of historical data to use
            include_expected_shortfall: Whether to calculate expected shortfall
            include_risk_contributions: Whether to calculate risk contributions
            portfolio_value: Total portfolio value
            
        Returns:
            VaRCalculationResult containing risk metrics and optional contributions
        """
        logger.info(f"Calculating VaR for portfolio {portfolio_id} using {calculation_method}")
        
        # Validate inputs
        self._validate_inputs(portfolio_id, portfolio_positions, confidence_levels, calculation_method)
        
        # Get historical returns data
        returns_data = self._get_historical_returns(portfolio_positions, data_period_days)
        
        # Calculate portfolio returns
        portfolio_returns = self._calculate_portfolio_returns(returns_data, portfolio_positions)
        
        # Calculate VaR using specified method
        if calculation_method == "historical_simulation":
            var_results = self._calculate_historical_var(portfolio_returns, confidence_levels)
        elif calculation_method == "parametric":
            var_results = self._calculate_parametric_var(portfolio_returns, confidence_levels)
        elif calculation_method == "monte_carlo":
            var_results = self._calculate_monte_carlo_var(portfolio_returns, confidence_levels)
        else:
            raise ValueError(f"Unsupported calculation method: {calculation_method}")
        
        # Calculate additional risk metrics
        risk_metrics = self._calculate_additional_metrics(portfolio_returns, portfolio_value)
        
        # Calculate expected shortfall if requested
        if include_expected_shortfall:
            expected_shortfall = self._calculate_expected_shortfall(portfolio_returns, confidence_levels)
            var_results.update(expected_shortfall)
        
        # Create risk metrics object
        risk_metrics_obj = RiskMetrics(
            portfolio_id=portfolio_id,
            var_95=var_results.get("var_95", 0.0),
            var_99=var_results.get("var_99", 0.0),
            expected_shortfall_95=var_results.get("es_95", 0.0),
            expected_shortfall_99=var_results.get("es_99", 0.0),
            portfolio_volatility=risk_metrics["volatility"],
            maximum_drawdown=risk_metrics["max_drawdown"],
            sharpe_ratio=risk_metrics["sharpe_ratio"],
            sortino_ratio=risk_metrics["sortino_ratio"],
            calmar_ratio=risk_metrics["calmar_ratio"],
            calculation_method=calculation_method,
            data_period_days=data_period_days,
            confidence_intervals=var_results.get("confidence_intervals", {})
        )
        
        # Calculate risk contributions if requested
        risk_contributions = None
        if include_risk_contributions:
            risk_contributions = self._calculate_risk_contributions(
                portfolio_positions, returns_data, risk_metrics_obj
            )
        
        # Prepare calculation metadata
        calculation_metadata = {
            "calculation_method": calculation_method,
            "data_period_days": data_period_days,
            "calculation_duration_ms": 0,  # Will be set by caller
            "data_quality_score": self._assess_data_quality(returns_data),
            "num_assets": len(portfolio_positions),
            "portfolio_value": portfolio_value,
            "confidence_levels": confidence_levels
        }
        
        return VaRCalculationResult(
            var_metrics=risk_metrics_obj,
            risk_contributions=risk_contributions,
            calculation_metadata=calculation_metadata,
            confidence_intervals=var_results.get("confidence_intervals", {})
        )
    
    def _validate_inputs(
        self, 
        portfolio_id: str, 
        portfolio_positions: List[Dict[str, Any]], 
        confidence_levels: List[float], 
        calculation_method: str
    ) -> None:
        """Validate calculation inputs."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not portfolio_positions:
            raise ValueError("Portfolio positions are required")
        
        if not confidence_levels:
            raise ValueError("At least one confidence level is required")
        
        for level in confidence_levels:
            if not (0.5 <= level < 1.0):
                raise ValueError(f"Confidence level {level} must be between 0.5 and 1.0")
        
        if calculation_method not in ["historical_simulation", "parametric", "monte_carlo"]:
            raise ValueError(f"Unsupported calculation method: {calculation_method}")
        
        # Validate portfolio positions
        for position in portfolio_positions:
            if "symbol" not in position or "weight" not in position:
                raise ValueError("Each position must have 'symbol' and 'weight'")
            
            if not (0 <= position["weight"] <= 1):
                raise ValueError(f"Position weight for {position['symbol']} must be between 0 and 1")
    
    def _get_historical_returns(
        self, 
        portfolio_positions: List[Dict[str, Any]], 
        data_period_days: int
    ) -> pd.DataFrame:
        """Get historical returns data for portfolio positions."""
        # Extract symbols
        symbols = [pos["symbol"] for pos in portfolio_positions]
        
        # Get historical data (mock implementation for now)
        # In a real implementation, this would fetch from market data provider
        end_date = datetime.now()
        start_date = end_date - timedelta(days=data_period_days + 30)  # Extra days for calculation
        
        # Generate mock returns data
        returns_data = self._generate_mock_returns(symbols, start_date, end_date)
        
        return returns_data
    
    def _generate_mock_returns(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Generate mock historical returns data."""
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate random returns for each symbol
        returns_data = pd.DataFrame(index=date_range)
        
        for symbol in symbols:
            # Generate returns with some realistic characteristics
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
            returns = np.random.normal(0.0005, 0.02, len(date_range))  # Daily returns
            
            # Add some autocorrelation and volatility clustering
            for i in range(1, len(returns)):
                returns[i] = 0.05 * returns[i-1] + 0.95 * returns[i]
            
            returns_data[symbol] = returns
        
        # Remove NaN values and ensure we have enough data
        returns_data = returns_data.dropna()
        
        if len(returns_data) < 30:
            raise ValueError("Insufficient historical data for VaR calculation")
        
        return returns_data
    
    def _calculate_portfolio_returns(
        self, 
        returns_data: pd.DataFrame, 
        portfolio_positions: List[Dict[str, Any]]
    ) -> pd.Series:
        """Calculate portfolio returns from individual asset returns."""
        portfolio_returns = pd.Series(0.0, index=returns_data.index)
        
        for position in portfolio_positions:
            symbol = position["symbol"]
            weight = position["weight"]
            
            if symbol in returns_data.columns:
                portfolio_returns += weight * returns_data[symbol]
            else:
                logger.warning(f"Symbol {symbol} not found in returns data")
        
        return portfolio_returns
    
    def _calculate_historical_var(
        self, 
        portfolio_returns: pd.Series, 
        confidence_levels: List[float]
    ) -> Dict[str, float]:
        """Calculate VaR using historical simulation method."""
        results = {}
        
        for confidence_level in confidence_levels:
            # Calculate VaR as percentile of returns
            var_percentile = (1 - confidence_level) * 100
            var_value = np.percentile(portfolio_returns, var_percentile)
            results[f"var_{int(confidence_level * 100)}"] = abs(var_value)
        
        # Store confidence intervals
        results["confidence_intervals"] = {
            str(level): results[f"var_{int(level * 100)}"]
            for level in confidence_levels
        }
        
        return results
    
    def _calculate_parametric_var(
        self, 
        portfolio_returns: pd.Series, 
        confidence_levels: List[float]
    ) -> Dict[str, float]:
        """Calculate VaR using parametric (normal distribution) method."""
        # Calculate mean and standard deviation
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        results = {}
        
        for confidence_level in confidence_levels:
            # Calculate VaR using normal distribution
            z_score = self._get_z_score(confidence_level)
            var_value = abs(mean_return + z_score * std_return)
            results[f"var_{int(confidence_level * 100)}"] = var_value
        
        # Store confidence intervals
        results["confidence_intervals"] = {
            str(level): results[f"var_{int(level * 100)}"]
            for level in confidence_levels
        }
        
        return results
    
    def _calculate_monte_carlo_var(
        self, 
        portfolio_returns: pd.Series, 
        confidence_levels: List[float],
        num_simulations: int = 10000
    ) -> Dict[str, float]:
        """Calculate VaR using Monte Carlo simulation."""
        # Estimate parameters from historical data
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        # Generate Monte Carlo simulations
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(mean_return, std_return, num_simulations)
        
        results = {}
        
        for confidence_level in confidence_levels:
            # Calculate VaR from simulated returns
            var_percentile = (1 - confidence_level) * 100
            var_value = np.percentile(simulated_returns, var_percentile)
            results[f"var_{int(confidence_level * 100)}"] = abs(var_value)
        
        # Store confidence intervals
        results["confidence_intervals"] = {
            str(level): results[f"var_{int(level * 100)}"]
            for level in confidence_levels
        }
        
        return results
    
    def _calculate_expected_shortfall(
        self, 
        portfolio_returns: pd.Series, 
        confidence_levels: List[float]
    ) -> Dict[str, float]:
        """Calculate Expected Shortfall (Conditional VaR) for given confidence levels."""
        results = {}
        
        for confidence_level in confidence_levels:
            # Calculate VaR threshold
            var_percentile = (1 - confidence_level) * 100
            var_threshold = np.percentile(portfolio_returns, var_percentile)
            
            # Calculate expected shortfall as mean of returns below VaR threshold
            tail_returns = portfolio_returns[portfolio_returns <= var_threshold]
            expected_shortfall = abs(tail_returns.mean()) if len(tail_returns) > 0 else 0.0
            
            results[f"es_{int(confidence_level * 100)}"] = expected_shortfall
        
        return results
    
    def _calculate_additional_metrics(
        self, 
        portfolio_returns: pd.Series, 
        portfolio_value: float
    ) -> Dict[str, float]:
        """Calculate additional risk metrics."""
        # Volatility (annualized)
        volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = portfolio_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0.0
        
        # Sortino ratio (downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0
        sortino_ratio = excess_returns / downside_deviation if downside_deviation > 0 else 0.0
        
        # Calmar ratio
        annual_return = portfolio_returns.mean() * 252
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0.0
        
        return {
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio
        }
    
    def _calculate_risk_contributions(
        self, 
        portfolio_positions: List[Dict[str, Any]], 
        returns_data: pd.DataFrame,
        risk_metrics: RiskMetrics
    ) -> RiskContributions:
        """Calculate risk contributions for each position."""
        # Calculate covariance matrix
        cov_matrix = returns_data.cov() * 252  # Annualize
        
        # Calculate portfolio weights
        weights = np.array([pos["weight"] for pos in portfolio_positions])
        
        # Calculate portfolio variance
        portfolio_variance = np.dot(weights, np.dot(cov_matrix.values, weights))
        
        # Calculate marginal contributions
        marginal_contributions = np.dot(cov_matrix.values, weights)
        
        # Create risk contributions object
        risk_contributions = RiskContributions(
            portfolio_id=risk_metrics.portfolio_id,
            risk_metrics_id=risk_metrics.risk_metrics_id,
            total_portfolio_risk=np.sqrt(portfolio_variance)
        )
        
        # Calculate individual asset contributions
        for i, position in enumerate(portfolio_positions):
            symbol = position["symbol"]
            weight = position["weight"]
            
            # Risk contribution = weight * marginal contribution / portfolio variance
            risk_contribution = (weight * marginal_contributions[i]) / portfolio_variance
            contribution_pct = risk_contribution * 100
            
            asset_metrics = {
                "weight": weight,
                "risk_contribution": risk_contribution,
                "marginal_contribution": marginal_contributions[i],
                "contribution_pct": contribution_pct
            }
            
            risk_contributions.add_asset_contribution(symbol, asset_metrics)
        
        return risk_contributions
    
    def _get_z_score(self, confidence_level: float) -> float:
        """Get z-score for given confidence level."""
        # Common z-scores for VaR calculations
        z_scores = {
            0.90: -1.282,
            0.95: -1.645,
            0.99: -2.326,
            0.995: -2.576,
            0.999: -3.090
        }
        
        return z_scores.get(confidence_level, -1.645)  # Default to 95% confidence
    
    def _assess_data_quality(self, returns_data: pd.DataFrame) -> float:
        """Assess the quality of historical data."""
        # Check for missing data
        missing_ratio = returns_data.isnull().sum().sum() / (returns_data.shape[0] * returns_data.shape[1])
        
        # Check for extreme values
        extreme_values = (abs(returns_data) > 0.5).sum().sum()  # Returns > 50%
        extreme_ratio = extreme_values / (returns_data.shape[0] * returns_data.shape[1])
        
        # Check data completeness
        completeness = 1 - missing_ratio
        
        # Calculate quality score (0-1)
        quality_score = completeness * (1 - extreme_ratio)
        
        return max(0.0, min(1.0, quality_score))
    
    def get_calculation_history(self, portfolio_id: str, limit: int = 30) -> List[RiskMetrics]:
        """Get VaR calculation history for a portfolio."""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    def validate_calculation_method(self, method: str) -> bool:
        """Validate if calculation method is supported."""
        supported_methods = ["historical_simulation", "parametric", "monte_carlo"]
        return method in supported_methods
    
    def get_supported_confidence_levels(self) -> List[float]:
        """Get list of supported confidence levels."""
        return [0.90, 0.95, 0.99, 0.995, 0.999]
    
    def clear_cache(self) -> None:
        """Clear calculation cache."""
        self.calculation_cache.clear()
        logger.info("VaR calculation cache cleared")












