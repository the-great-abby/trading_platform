"""
Risk Management Utilities

Utility functions for the comprehensive risk management framework.
"""

import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from uuid import UUID


logger = logging.getLogger(__name__)


class RiskCalculationUtils:
    """Utility functions for risk calculations."""
    
    @staticmethod
    def calculate_portfolio_volatility(
        weights: List[float],
        returns_matrix: np.ndarray,
        lookback_days: int = 252
    ) -> float:
        """
        Calculate portfolio volatility using portfolio weights and returns matrix.
        
        Args:
            weights: Portfolio weights
            returns_matrix: Matrix of asset returns (assets x time)
            lookback_days: Number of days for annualization
            
        Returns:
            Annualized portfolio volatility
        """
        if not weights or len(weights) != returns_matrix.shape[0]:
            raise ValueError("Weights length must match number of assets")
        
        # Calculate portfolio returns
        portfolio_returns = np.dot(weights, returns_matrix)
        
        # Calculate volatility
        volatility = np.std(portfolio_returns) * math.sqrt(lookback_days)
        
        return float(volatility)
    
    @staticmethod
    def calculate_var_historical(
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate VaR using historical simulation method.
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Value at Risk
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        # Sort returns (ascending order for loss calculation)
        sorted_returns = sorted(returns)
        
        # Calculate VaR percentile
        var_index = int((1 - confidence_level) * len(sorted_returns))
        var_index = max(0, min(var_index, len(sorted_returns) - 1))
        
        # VaR is the negative of the return at the confidence level
        var = -sorted_returns[var_index]
        
        return float(var)
    
    @staticmethod
    def calculate_expected_shortfall(
        returns: List[float],
        var: float,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Expected Shortfall (Conditional VaR).
        
        Args:
            returns: List of historical returns
            var: Value at Risk
            confidence_level: Confidence level
            
        Returns:
            Expected Shortfall
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        # Filter returns that exceed VaR threshold
        tail_returns = [r for r in returns if -r >= var]
        
        if not tail_returns:
            return var
        
        # Calculate average of tail returns
        expected_shortfall = -statistics.mean(tail_returns)
        
        return float(expected_shortfall)
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.02,
        annualization_factor: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate (annual)
            annualization_factor: Annualization factor
            
        Returns:
            Sharpe ratio
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        mean_return = statistics.mean(returns)
        return_std = statistics.stdev(returns)
        
        if return_std == 0:
            return 0.0
        
        # Annualize returns and risk-free rate
        annualized_return = mean_return * annualization_factor
        annualized_risk_free = risk_free_rate
        annualized_std = return_std * math.sqrt(annualization_factor)
        
        sharpe_ratio = (annualized_return - annualized_risk_free) / annualized_std
        
        return float(sharpe_ratio)
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float],
        risk_free_rate: float = 0.02,
        annualization_factor: int = 252
    ) -> float:
        """
        Calculate Sortino ratio.
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate (annual)
            annualization_factor: Annualization factor
            
        Returns:
            Sortino ratio
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        mean_return = statistics.mean(returns)
        
        # Calculate downside deviation
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return float('inf') if mean_return > risk_free_rate / annualization_factor else 0.0
        
        downside_std = statistics.stdev(downside_returns)
        
        if downside_std == 0:
            return 0.0
        
        # Annualize returns and risk-free rate
        annualized_return = mean_return * annualization_factor
        annualized_risk_free = risk_free_rate
        annualized_downside_std = downside_std * math.sqrt(annualization_factor)
        
        sortino_ratio = (annualized_return - annualized_risk_free) / annualized_downside_std
        
        return float(sortino_ratio)
    
    @staticmethod
    def calculate_maximum_drawdown(equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: List of portfolio values over time
            
        Returns:
            Maximum drawdown as a percentage
        """
        if not equity_curve:
            raise ValueError("Equity curve cannot be empty")
        
        peak = equity_curve[0]
        max_drawdown = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return float(max_drawdown)
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: List[float],
        max_drawdown: float,
        annualization_factor: int = 252
    ) -> float:
        """
        Calculate Calmar ratio.
        
        Args:
            returns: List of returns
            max_drawdown: Maximum drawdown
            annualization_factor: Annualization factor
            
        Returns:
            Calmar ratio
        """
        if max_drawdown == 0:
            return float('inf')
        
        annualized_return = statistics.mean(returns) * annualization_factor
        calmar_ratio = annualized_return / max_drawdown
        
        return float(calmar_ratio)


class PortfolioUtils:
    """Utility functions for portfolio operations."""
    
    @staticmethod
    def normalize_weights(weights: List[float]) -> List[float]:
        """
        Normalize portfolio weights to sum to 1.0.
        
        Args:
            weights: List of portfolio weights
            
        Returns:
            Normalized weights
        """
        if not weights:
            return []
        
        total_weight = sum(weights)
        
        if total_weight == 0:
            # Equal weights if all weights are zero
            return [1.0 / len(weights)] * len(weights)
        
        return [w / total_weight for w in weights]
    
    @staticmethod
    def calculate_portfolio_value(
        positions: List[Dict[str, Any]],
        current_prices: Dict[str, float]
    ) -> float:
        """
        Calculate current portfolio value.
        
        Args:
            positions: List of position dictionaries
            current_prices: Dictionary of current prices by symbol
            
        Returns:
            Total portfolio value
        """
        total_value = 0.0
        
        for position in positions:
            symbol = position.get("symbol")
            quantity = position.get("quantity", 0)
            price = current_prices.get(symbol, 0.0)
            
            position_value = quantity * price
            total_value += position_value
        
        return total_value
    
    @staticmethod
    def calculate_position_weights(
        positions: List[Dict[str, Any]],
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """
        Calculate position weights in portfolio.
        
        Args:
            positions: List of position dictionaries
            portfolio_value: Total portfolio value
            
        Returns:
            List of positions with weights added
        """
        if portfolio_value == 0:
            return positions
        
        weighted_positions = []
        
        for position in positions.copy():
            position_value = position.get("current_value", 0.0)
            weight = position_value / portfolio_value
            
            weighted_position = position.copy()
            weighted_position["weight"] = weight
            weighted_positions.append(weighted_position)
        
        return weighted_positions
    
    @staticmethod
    def group_positions_by_sector(
        positions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group positions by sector.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            Dictionary mapping sectors to positions
        """
        sector_positions = {}
        
        for position in positions:
            sector = position.get("sector", "unknown")
            
            if sector not in sector_positions:
                sector_positions[sector] = []
            
            sector_positions[sector].append(position)
        
        return sector_positions
    
    @staticmethod
    def calculate_sector_weights(
        positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate sector weights in portfolio.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            Dictionary mapping sectors to weights
        """
        sector_positions = PortfolioUtils.group_positions_by_sector(positions)
        sector_weights = {}
        
        for sector, sector_positions_list in sector_positions.items():
            sector_weight = sum(pos.get("weight", 0.0) for pos in sector_positions_list)
            sector_weights[sector] = sector_weight
        
        return sector_weights


class DataUtils:
    """Utility functions for data operations."""
    
    @staticmethod
    def generate_mock_returns(
        symbols: List[str],
        days: int = 252,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Generate mock returns data for testing.
        
        Args:
            symbols: List of asset symbols
            days: Number of days of data
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with returns data
        """
        np.random.seed(seed)
        
        # Generate correlated returns
        n_assets = len(symbols)
        returns_data = np.random.multivariate_normal(
            np.zeros(n_assets),
            np.eye(n_assets) * 0.02**2,  # 2% daily volatility
            days
        )
        
        # Create DataFrame
        date_range = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='D'
        )[:-1]  # Exclude today
        
        returns_df = pd.DataFrame(returns_data, index=date_range, columns=symbols)
        
        return returns_df
    
    @staticmethod
    def calculate_rolling_correlation(
        returns_df: pd.DataFrame,
        window: int = 30
    ) -> pd.DataFrame:
        """
        Calculate rolling correlation matrix.
        
        Args:
            returns_df: DataFrame with returns data
            window: Rolling window size
            
        Returns:
            DataFrame with rolling correlations
        """
        return returns_df.rolling(window=window).corr()
    
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix from returns.
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Correlation matrix
        """
        return returns_df.corr()
    
    @staticmethod
    def detect_outliers(
        data: List[float],
        method: str = "iqr",
        threshold: float = 1.5
    ) -> List[int]:
        """
        Detect outliers in data.
        
        Args:
            data: List of numeric values
            method: Method for outlier detection ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            List of outlier indices
        """
        if method == "iqr":
            return DataUtils._detect_outliers_iqr(data, threshold)
        elif method == "zscore":
            return DataUtils._detect_outliers_zscore(data, threshold)
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    @staticmethod
    def _detect_outliers_iqr(data: List[float], threshold: float) -> List[int]:
        """Detect outliers using IQR method."""
        if len(data) < 4:
            return []
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        outliers = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)
        
        return outliers
    
    @staticmethod
    def _detect_outliers_zscore(data: List[float], threshold: float) -> List[int]:
        """Detect outliers using Z-score method."""
        if len(data) < 2:
            return []
        
        mean_val = statistics.mean(data)
        std_val = statistics.stdev(data)
        
        if std_val == 0:
            return []
        
        outliers = []
        for i, value in enumerate(data):
            z_score = abs((value - mean_val) / std_val)
            if z_score > threshold:
                outliers.append(i)
        
        return outliers


class ValidationUtils:
    """Utility functions for data validation."""
    
    @staticmethod
    def validate_portfolio_id(portfolio_id: Union[str, UUID]) -> bool:
        """
        Validate portfolio ID format.
        
        Args:
            portfolio_id: Portfolio ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if isinstance(portfolio_id, str):
                UUID(portfolio_id)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_confidence_level(confidence_level: float) -> bool:
        """
        Validate confidence level.
        
        Args:
            confidence_level: Confidence level to validate
            
        Returns:
            True if valid, False otherwise
        """
        return 0 < confidence_level < 1
    
    @staticmethod
    def validate_weights(weights: List[float], tolerance: float = 1e-6) -> bool:
        """
        Validate portfolio weights.
        
        Args:
            weights: List of weights to validate
            tolerance: Tolerance for weight sum validation
            
        Returns:
            True if valid, False otherwise
        """
        if not weights:
            return False
        
        # Check for negative weights
        if any(w < 0 for w in weights):
            return False
        
        # Check weight sum
        weight_sum = sum(weights)
        return abs(weight_sum - 1.0) <= tolerance
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
        """
        Validate date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            True if valid, False otherwise
        """
        return start_date < end_date


class PerformanceUtils:
    """Utility functions for performance measurement."""
    
    @staticmethod
    def measure_execution_time(func):
        """Decorator to measure function execution time."""
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            logger.debug(f"{func.__name__} executed in {execution_time_ms:.2f}ms")
            
            return result
        
        return wrapper
    
    @staticmethod
    def log_performance_metrics(
        operation: str,
        duration_ms: float,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            additional_metrics: Additional metrics to log
        """
        metrics = {
            "operation": operation,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        logger.info(f"Performance metrics: {metrics}")


class CacheUtils:
    """Utility functions for caching."""
    
    @staticmethod
    def generate_cache_key(
        prefix: str,
        *args,
        **kwargs
    ) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}={value}")
        
        return ":".join(key_parts)
    
    @staticmethod
    def is_cache_valid(
        cache_timestamp: datetime,
        max_age_minutes: int = 15
    ) -> bool:
        """
        Check if cache entry is still valid.
        
        Args:
            cache_timestamp: When the cache entry was created
            max_age_minutes: Maximum age in minutes
            
        Returns:
            True if cache is valid, False otherwise
        """
        age = datetime.utcnow() - cache_timestamp
        return age.total_seconds() < (max_age_minutes * 60)

