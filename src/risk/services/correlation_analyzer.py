"""
Correlation Analyzer Service

Provides asset correlation analysis and concentration risk assessment for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass

from ..models.correlation_analysis import CorrelationAnalysis


logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Asset correlation analysis service.
    
    Provides correlation matrix calculations, concentration risk analysis,
    and diversification recommendations.
    """
    
    def __init__(self, market_data_provider=None):
        """
        Initialize correlation analyzer.
        
        Args:
            market_data_provider: Provider for market data (optional)
        """
        self.market_data_provider = market_data_provider
        self.analysis_cache = {}
    
    def analyze_correlations(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        rolling_period_days: int = 30,
        analysis_method: str = "pearson_correlation",
        include_sector_analysis: bool = True,
        include_diversification_recommendations: bool = True,
        portfolio_value: float = 100000.0
    ) -> CorrelationAnalysis:
        """
        Analyze asset correlations and concentration risks.
        
        Args:
            portfolio_id: Portfolio identifier
            portfolio_positions: List of portfolio positions
            rolling_period_days: Number of days for rolling correlation calculation
            analysis_method: Correlation method ('pearson_correlation', 'spearman_correlation')
            include_sector_analysis: Whether to include sector-level analysis
            include_diversification_recommendations: Whether to generate recommendations
            portfolio_value: Total portfolio value
            
        Returns:
            CorrelationAnalysis object with results
        """
        logger.info(f"Analyzing correlations for portfolio {portfolio_id}")
        
        # Validate inputs
        self._validate_inputs(portfolio_id, portfolio_positions, rolling_period_days, analysis_method)
        
        # Get historical returns data
        returns_data = self._get_historical_returns(portfolio_positions, rolling_period_days)
        
        # Calculate correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(returns_data, analysis_method)
        
        # Calculate sector correlations if requested
        sector_correlations = {}
        if include_sector_analysis:
            sector_correlations = self._calculate_sector_correlations(portfolio_positions, returns_data)
        
        # Calculate concentration risk
        concentration_analysis = self._calculate_concentration_risk(portfolio_positions, portfolio_value)
        
        # Calculate diversification metrics
        diversification_metrics = self._calculate_diversification_metrics(
            portfolio_positions, correlation_matrix
        )
        
        # Analyze correlation stability
        stability_analysis = self._analyze_correlation_stability(returns_data, rolling_period_days)
        
        # Get top correlations
        top_correlations = self._get_top_correlations(correlation_matrix, threshold=0.7)
        
        # Calculate risk attribution
        risk_attribution = self._calculate_risk_attribution(portfolio_positions, correlation_matrix)
        
        # Generate recommendations
        recommendations = []
        if include_diversification_recommendations:
            recommendations = self._generate_diversification_recommendations(
                concentration_analysis, diversification_metrics, top_correlations
            )
        
        # Create correlation analysis object
        analysis = CorrelationAnalysis(
            portfolio_id=portfolio_id,
            rolling_correlation_period=rolling_period_days,
            analysis_method=analysis_method,
            correlation_matrix=correlation_matrix,
            sector_correlations=sector_correlations,
            concentration_risk_score=concentration_analysis["concentration_score"],
            sector_concentration=concentration_analysis["sector_concentration"],
            diversification_ratio=diversification_metrics["diversification_ratio"],
            effective_number_of_assets=diversification_metrics["effective_assets"],
            correlation_stability_score=stability_analysis["stability_score"],
            correlation_regime=stability_analysis["regime"],
            top_correlations=top_correlations,
            risk_attribution=risk_attribution,
            recommendations=recommendations
        )
        
        logger.info(f"Completed correlation analysis for portfolio {portfolio_id}")
        return analysis
    
    def _validate_inputs(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        rolling_period_days: int,
        analysis_method: str
    ) -> None:
        """Validate correlation analysis inputs."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not portfolio_positions:
            raise ValueError("Portfolio positions are required")
        
        if rolling_period_days <= 0:
            raise ValueError("Rolling period must be positive")
        
        if analysis_method not in ["pearson_correlation", "spearman_correlation"]:
            raise ValueError(f"Unsupported analysis method: {analysis_method}")
        
        # Validate portfolio positions
        for position in portfolio_positions:
            if "symbol" not in position or "weight" not in position:
                raise ValueError("Each position must have 'symbol' and 'weight'")
            
            if not (0 <= position["weight"] <= 1):
                raise ValueError(f"Position weight for {position['symbol']} must be between 0 and 1")
    
    def _get_historical_returns(
        self,
        portfolio_positions: List[Dict[str, Any]],
        rolling_period_days: int
    ) -> pd.DataFrame:
        """Get historical returns data for correlation analysis."""
        # Extract symbols
        symbols = [pos["symbol"] for pos in portfolio_positions]
        
        # Get historical data (mock implementation)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=rolling_period_days + 30)
        
        # Generate mock returns data
        returns_data = self._generate_mock_returns(symbols, start_date, end_date)
        
        return returns_data
    
    def _generate_mock_returns(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Generate mock historical returns data with realistic correlations."""
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate correlated returns
        np.random.seed(42)  # For reproducibility
        
        # Create a correlation structure
        n_assets = len(symbols)
        base_correlation = 0.3  # Base correlation between assets
        
        # Generate correlation matrix
        corr_matrix = np.full((n_assets, n_assets), base_correlation)
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Add some sector-based correlations
        for i, symbol in enumerate(symbols):
            for j, other_symbol in enumerate(symbols):
                if i != j:
                    # Higher correlation within sectors
                    if self._get_sector(symbol) == self._get_sector(other_symbol):
                        corr_matrix[i, j] = 0.7
                    else:
                        corr_matrix[i, j] = base_correlation
        
        # Generate correlated returns
        returns = np.random.multivariate_normal(
            np.zeros(n_assets), corr_matrix, len(date_range)
        )
        
        # Create DataFrame
        returns_data = pd.DataFrame(returns, index=date_range, columns=symbols)
        
        # Add some realistic characteristics
        for symbol in symbols:
            returns_data[symbol] *= 0.02  # Scale to realistic daily returns
            # Add some autocorrelation
            returns_data[symbol] = returns_data[symbol].rolling(2).mean().fillna(returns_data[symbol])
        
        return returns_data.dropna()
    
    def _get_sector(self, symbol: str) -> str:
        """Get sector for a symbol (mock implementation)."""
        # Simple sector mapping based on symbol patterns
        if symbol.startswith(('AAPL', 'MSFT', 'GOOGL', 'AMZN')):
            return 'technology'
        elif symbol.startswith(('JPM', 'BAC', 'WFC', 'C')):
            return 'financial'
        elif symbol.startswith(('XOM', 'CVX', 'COP', 'EOG')):
            return 'energy'
        elif symbol.startswith(('JNJ', 'PFE', 'UNH', 'ABBV')):
            return 'healthcare'
        else:
            return 'other'
    
    def _calculate_correlation_matrix(
        self,
        returns_data: pd.DataFrame,
        method: str = "pearson_correlation"
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix from returns data."""
        if method == "pearson_correlation":
            corr_matrix = returns_data.corr()
        elif method == "spearman_correlation":
            corr_matrix = returns_data.corr(method='spearman')
        else:
            raise ValueError(f"Unsupported correlation method: {method}")
        
        # Convert to dictionary format
        correlation_dict = {}
        for asset1 in corr_matrix.columns:
            correlation_dict[asset1] = {}
            for asset2 in corr_matrix.columns:
                correlation_dict[asset1][asset2] = float(corr_matrix.loc[asset1, asset2])
        
        return correlation_dict
    
    def _calculate_sector_correlations(
        self,
        portfolio_positions: List[Dict[str, Any]],
        returns_data: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Calculate sector-level correlations."""
        # Group positions by sector
        sector_positions = {}
        for position in portfolio_positions:
            sector = position.get("sector", "unknown")
            symbol = position["symbol"]
            
            if sector not in sector_positions:
                sector_positions[sector] = []
            sector_positions[sector].append(symbol)
        
        # Calculate sector returns
        sector_returns = {}
        for sector, symbols in sector_positions.items():
            # Calculate sector return as weighted average
            sector_return = pd.Series(0.0, index=returns_data.index)
            
            for symbol in symbols:
                if symbol in returns_data.columns:
                    weight = next(
                        pos["weight"] for pos in portfolio_positions 
                        if pos["symbol"] == symbol
                    )
                    sector_return += weight * returns_data[symbol]
            
            sector_returns[sector] = sector_return
        
        # Calculate sector correlation matrix
        sector_df = pd.DataFrame(sector_returns)
        sector_corr_matrix = sector_df.corr()
        
        # Convert to dictionary format
        sector_correlations = {}
        for sector1 in sector_corr_matrix.columns:
            sector_correlations[sector1] = {}
            for sector2 in sector_corr_matrix.columns:
                sector_correlations[sector1][sector2] = float(sector_corr_matrix.loc[sector1, sector2])
        
        return sector_correlations
    
    def _calculate_concentration_risk(
        self,
        portfolio_positions: List[Dict[str, Any]],
        portfolio_value: float
    ) -> Dict[str, Any]:
        """Calculate concentration risk metrics."""
        # Asset concentration
        weights = [pos["weight"] for pos in portfolio_positions]
        asset_hhi = sum(w ** 2 for w in weights)
        
        # Sector concentration
        sector_weights = {}
        for position in portfolio_positions:
            sector = position.get("sector", "unknown")
            weight = position["weight"]
            
            if sector not in sector_weights:
                sector_weights[sector] = 0.0
            sector_weights[sector] += weight
        
        sector_hhi = sum(w ** 2 for w in sector_weights.values())
        
        # Overall concentration score (0-1, higher = more concentrated)
        concentration_score = (asset_hhi + sector_hhi) / 2
        
        return {
            "concentration_score": concentration_score,
            "asset_hhi": asset_hhi,
            "sector_hhi": sector_hhi,
            "sector_concentration": sector_weights
        }
    
    def _calculate_diversification_metrics(
        self,
        portfolio_positions: List[Dict[str, Any]],
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate diversification metrics."""
        # Effective number of assets (inverse of HHI)
        weights = [pos["weight"] for pos in portfolio_positions]
        hhi = sum(w ** 2 for w in weights)
        effective_assets = 1 / hhi if hhi > 0 else len(weights)
        
        # Diversification ratio
        # This is a simplified calculation
        # In practice, it would involve portfolio variance vs equal-weighted variance
        avg_correlation = self._calculate_average_correlation(correlation_matrix)
        diversification_ratio = 1 / (1 + avg_correlation)
        
        return {
            "effective_assets": effective_assets,
            "diversification_ratio": diversification_ratio
        }
    
    def _calculate_average_correlation(
        self,
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> float:
        """Calculate average correlation from correlation matrix."""
        correlations = []
        
        for asset1, correlations_dict in correlation_matrix.items():
            for asset2, corr_value in correlations_dict.items():
                if asset1 != asset2:  # Exclude diagonal
                    correlations.append(corr_value)
        
        return np.mean(correlations) if correlations else 0.0
    
    def _analyze_correlation_stability(
        self,
        returns_data: pd.DataFrame,
        rolling_period_days: int
    ) -> Dict[str, Any]:
        """Analyze correlation stability over time."""
        # Calculate rolling correlations
        window_size = min(20, len(returns_data) // 4)  # Adaptive window size
        
        if window_size < 5:
            return {
                "stability_score": 0.5,
                "regime": "normal"
            }
        
        # Calculate rolling correlation for first two assets
        if len(returns_data.columns) >= 2:
            asset1, asset2 = returns_data.columns[:2]
            rolling_corr = returns_data[asset1].rolling(window=window_size).corr(returns_data[asset2])
            
            # Calculate stability score (lower variance = higher stability)
            corr_variance = rolling_corr.var()
            stability_score = max(0.0, 1.0 - corr_variance)
            
            # Determine correlation regime
            avg_correlation = rolling_corr.mean()
            if avg_correlation > 0.7:
                regime = "high_correlation"
            elif avg_correlation < 0.3:
                regime = "low_correlation"
            else:
                regime = "normal"
        else:
            stability_score = 0.5
            regime = "normal"
        
        return {
            "stability_score": stability_score,
            "regime": regime
        }
    
    def _get_top_correlations(
        self,
        correlation_matrix: Dict[str, Dict[str, float]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get top correlations above threshold."""
        top_correlations = []
        
        for asset1, correlations in correlation_matrix.items():
            for asset2, corr_value in correlations.items():
                if asset1 != asset2 and abs(corr_value) >= threshold:
                    top_correlations.append({
                        "asset1": asset1,
                        "asset2": asset2,
                        "correlation": corr_value,
                        "abs_correlation": abs(corr_value)
                    })
        
        # Sort by absolute correlation (descending)
        top_correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)
        
        return top_correlations[:20]  # Return top 20
    
    def _calculate_risk_attribution(
        self,
        portfolio_positions: List[Dict[str, Any]],
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Calculate risk attribution analysis."""
        # This is a simplified implementation
        # In practice, this would involve portfolio variance decomposition
        
        weights = [pos["weight"] for pos in portfolio_positions]
        symbols = [pos["symbol"] for pos in portfolio_positions]
        
        # Calculate individual asset risk contributions
        asset_risk_contributions = {}
        for i, (symbol, weight) in enumerate(zip(symbols, weights)):
            # Simplified risk contribution calculation
            risk_contribution = weight ** 2  # Simplified
            asset_risk_contributions[symbol] = {
                "weight": weight,
                "risk_contribution": risk_contribution,
                "contribution_pct": risk_contribution * 100
            }
        
        return {
            "asset_risk_contributions": asset_risk_contributions,
            "total_risk": sum(asset_risk_contributions[symbol]["risk_contribution"] for symbol in symbols),
            "concentration_risk": max(asset_risk_contributions[symbol]["risk_contribution"] for symbol in symbols)
        }
    
    def _generate_diversification_recommendations(
        self,
        concentration_analysis: Dict[str, Any],
        diversification_metrics: Dict[str, float],
        top_correlations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate diversification recommendations."""
        recommendations = []
        
        # Asset concentration recommendations
        if concentration_analysis["asset_hhi"] > 0.25:
            recommendations.append("Portfolio has high asset concentration - consider diversifying across more assets")
        
        # Sector concentration recommendations
        if concentration_analysis["sector_hhi"] > 0.25:
            recommendations.append("Portfolio has high sector concentration - diversify across more sectors")
        
        # Effective number of assets
        if diversification_metrics["effective_assets"] < 10:
            recommendations.append(f"Effective number of assets ({diversification_metrics['effective_assets']:.1f}) is low - add more assets")
        
        # Diversification ratio
        if diversification_metrics["diversification_ratio"] < 1.2:
            recommendations.append("Low diversification ratio - consider adding uncorrelated assets")
        
        # High correlations
        if len(top_correlations) > 0:
            recommendations.append(f"Found {len(top_correlations)} asset pairs with high correlations (>0.7)")
        
        # Overall concentration
        if concentration_analysis["concentration_score"] > 0.3:
            recommendations.append("Overall concentration risk is high - diversify portfolio")
        
        return recommendations
    
    def get_correlation_summary(
        self,
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Get a summary of correlation analysis."""
        correlations = []
        
        for asset1, correlations_dict in correlation_matrix.items():
            for asset2, corr_value in correlations_dict.items():
                if asset1 != asset2:
                    correlations.append(corr_value)
        
        return {
            "num_assets": len(correlation_matrix),
            "num_correlations": len(correlations),
            "avg_correlation": np.mean(correlations) if correlations else 0.0,
            "max_correlation": max(correlations) if correlations else 0.0,
            "min_correlation": min(correlations) if correlations else 0.0,
            "correlation_std": np.std(correlations) if correlations else 0.0
        }
    
    def detect_correlation_regimes(
        self,
        returns_data: pd.DataFrame,
        window_size: int = 30
    ) -> List[Dict[str, Any]]:
        """Detect correlation regime changes over time."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated regime detection
        
        regimes = []
        
        if len(returns_data) < window_size:
            return regimes
        
        # Calculate rolling average correlation
        for i in range(window_size, len(returns_data)):
            window_data = returns_data.iloc[i-window_size:i]
            
            if len(window_data.columns) >= 2:
                # Calculate average correlation in window
                corr_matrix = window_data.corr()
                avg_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
                
                # Determine regime
                if avg_correlation > 0.7:
                    regime = "high_correlation"
                elif avg_correlation < 0.3:
                    regime = "low_correlation"
                else:
                    regime = "normal"
                
                regimes.append({
                    "date": window_data.index[-1],
                    "regime": regime,
                    "avg_correlation": avg_correlation,
                    "window_size": window_size
                })
        
        return regimes
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self.analysis_cache.clear()
        logger.info("Correlation analysis cache cleared")



