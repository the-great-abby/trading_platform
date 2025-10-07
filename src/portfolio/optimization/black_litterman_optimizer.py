"""
Black-Litterman Optimizer
Implementation of Black-Litterman model for portfolio optimization
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import time

try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False

from ..models import (
    Portfolio, OptimizationResult, OptimizationMethod, MarketView, ViewType
)


class BlackLittermanOptimizer:
    """Black-Litterman optimizer for incorporating market views"""
    
    def __init__(self, market_data_service=None):
        """Initialize Black-Litterman optimizer"""
        self.market_data_service = market_data_service
        
        if not CVXPY_AVAILABLE:
            raise ImportError("cvxpy is required for Black-Litterman optimization. Install with: pip install cvxpy")
    
    def optimize_with_views(self,
                           portfolio: Portfolio,
                           market_views: List[MarketView],
                           tau: float = 0.025,
                           risk_free_rate: float = 0.02,
                           risk_aversion: float = 3.0,
                           max_optimization_time: float = 60.0) -> OptimizationResult:
        """Optimize portfolio using Black-Litterman model with market views"""
        
        start_time = time.time()
        
        # Get market data
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            raise ValueError("Insufficient market data for optimization")
        
        asset_ids = asset_data['asset_ids']
        n_assets = len(asset_ids)
        
        # Get market equilibrium returns
        market_returns = self._get_market_equilibrium_returns(
            portfolio, asset_ids, risk_aversion, tau
        )
        
        # Process market views
        if market_views:
            # Filter active views
            active_views = [view for view in market_views if view.is_valid()]
            
            if active_views:
                # Apply Black-Litterman formula
                adjusted_returns = self._apply_black_litterman(
                    market_returns, active_views, asset_ids, tau
                )
            else:
                adjusted_returns = market_returns
        else:
            adjusted_returns = market_returns
        
        # Get covariance matrix
        cov_matrix = asset_data['covariance_matrix']
        
        # Set up optimization problem with adjusted returns
        weights = cp.Variable(n_assets)
        
        # Portfolio metrics
        portfolio_return = adjusted_returns.T @ weights
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        portfolio_volatility = cp.sqrt(portfolio_variance)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0 if portfolio.long_only else weights >= -1
        ]
        
        # Add portfolio constraints
        if portfolio.max_single_asset_weight < 1.0:
            constraints.append(weights <= portfolio.max_single_asset_weight)
        
        # Maximize Sharpe ratio with adjusted returns
        objective = cp.Maximize((portfolio_return - risk_free_rate) / portfolio_volatility)
        
        # Solve optimization
        problem = cp.Problem(objective, constraints)
        
        try:
            problem.solve(verbose=False, max_iters=1000)
            
            optimization_time = time.time() - start_time
            
            if optimization_time > max_optimization_time:
                raise ValueError(f"Optimization exceeded time limit of {max_optimization_time}s")
            
            if problem.status not in ["optimal", "optimal_inaccurate"]:
                raise ValueError(f"Optimization failed with status: {problem.status}")
            
            # Extract results
            optimal_weights = weights.value
            if optimal_weights is None:
                raise ValueError("No optimal solution found")
            
            # Calculate metrics
            expected_return = float(portfolio_return.value)
            expected_volatility = float(portfolio_volatility.value)
            sharpe_ratio = (expected_return - risk_free_rate) / expected_volatility if expected_volatility > 0 else 0
            
            # Create asset weights dictionary
            asset_weights = dict(zip(asset_ids, optimal_weights))
            
            # Calculate market equilibrium weights for comparison
            equilibrium_weights = self._get_market_equilibrium_weights(
                portfolio, asset_ids, risk_aversion
            )
            
            # Calculate weight changes
            weight_changes = {}
            for asset_id in asset_ids:
                bl_weight = asset_weights.get(asset_id, 0.0)
                eq_weight = equilibrium_weights.get(asset_id, 0.0)
                weight_changes[asset_id] = bl_weight - eq_weight
            
            # Create optimization result
            result = OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.BLACK_LITTERMAN,
                risk_free_rate=risk_free_rate,
                expected_return=expected_return,
                expected_volatility=expected_volatility,
                sharpe_ratio=sharpe_ratio,
                asset_weights=asset_weights,
                convergence_status=True,
                optimization_time=optimization_time,
                iteration_count=problem.solver_stats.num_iters if hasattr(problem.solver_stats, 'num_iters') else 0
            )
            
            # Add Black-Litterman specific data
            result.market_equilibrium_weights = equilibrium_weights
            result.weight_changes = weight_changes
            
            return result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            return OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.BLACK_LITTERMAN,
                risk_free_rate=risk_free_rate,
                convergence_status=False,
                optimization_time=optimization_time,
                constraint_violations=[str(e)]
            )
    
    def get_market_equilibrium_weights(self,
                                     portfolio: Portfolio,
                                     risk_aversion: float = 3.0) -> Dict[str, float]:
        """Get market equilibrium weights (CAPM market portfolio)"""
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            return {}
        
        asset_ids = asset_data['asset_ids']
        market_caps = self._get_market_caps(asset_ids)
        
        if not market_caps:
            # Equal weights if no market cap data
            equal_weight = 1.0 / len(asset_ids)
            return {asset_id: equal_weight for asset_id in asset_ids}
        
        # Calculate market cap weights
        total_market_cap = sum(market_caps.values())
        weights = {}
        
        for asset_id in asset_ids:
            market_cap = market_caps.get(asset_id, 0.0)
            weights[asset_id] = market_cap / total_market_cap if total_market_cap > 0 else 0.0
        
        return weights
    
    def _get_market_equilibrium_returns(self,
                                       portfolio: Portfolio,
                                       asset_ids: List[str],
                                       risk_aversion: float,
                                       tau: float) -> np.ndarray:
        """Calculate market equilibrium returns"""
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            return np.array([0.08] * len(asset_ids))  # Default returns
        
        cov_matrix = asset_data['covariance_matrix']
        
        # Get market cap weights
        market_weights = self._get_market_caps(asset_ids)
        if not market_weights:
            # Equal weights if no market cap data
            equal_weight = 1.0 / len(asset_ids)
            market_weights = {asset_id: equal_weight for asset_id in asset_ids}
        
        # Create weight vector
        weights_vector = np.array([market_weights.get(asset_id, 0.0) for asset_id in asset_ids])
        
        # Normalize weights
        weights_vector = weights_vector / np.sum(weights_vector)
        
        # Calculate equilibrium returns: Pi = lambda * Sigma * w_market
        equilibrium_returns = risk_aversion * (cov_matrix @ weights_vector)
        
        return equilibrium_returns
    
    def _apply_black_litterman(self,
                              equilibrium_returns: np.ndarray,
                              market_views: List[MarketView],
                              asset_ids: List[str],
                              tau: float) -> np.ndarray:
        """Apply Black-Litterman formula to incorporate views"""
        
        n_assets = len(asset_ids)
        n_views = len(market_views)
        
        if n_views == 0:
            return equilibrium_returns
        
        # Create view vector (P)
        P = np.zeros((n_views, n_assets))
        Q = np.zeros(n_views)  # Expected returns from views
        
        for i, view in enumerate(market_views):
            view_row = view.get_view_matrix_row(asset_ids)
            P[i, :] = view_row
            Q[i] = view.get_view_vector(asset_ids)[0]  # First non-zero element
        
        # Create uncertainty matrix (Omega)
        Omega = np.diag([view.get_uncertainty(tau) for view in market_views])
        
        # Get covariance matrix
        asset_data = self._get_asset_data_from_ids(asset_ids)
        if not asset_data:
            return equilibrium_returns
        
        Sigma = asset_data['covariance_matrix']
        
        # Black-Litterman formula
        # mu = [(tau*Sigma)^(-1) + P'*Omega^(-1)*P]^(-1) * [(tau*Sigma)^(-1)*Pi + P'*Omega^(-1)*Q]
        
        # Calculate inverse of tau*Sigma
        tau_sigma_inv = np.linalg.inv(tau * Sigma)
        
        # Calculate inverse of Omega
        omega_inv = np.linalg.inv(Omega)
        
        # First part: (tau*Sigma)^(-1) + P'*Omega^(-1)*P
        first_part = tau_sigma_inv + P.T @ omega_inv @ P
        
        # Second part: (tau*Sigma)^(-1)*Pi + P'*Omega^(-1)*Q
        second_part = tau_sigma_inv @ equilibrium_returns + P.T @ omega_inv @ Q
        
        # Calculate adjusted returns
        try:
            adjusted_returns = np.linalg.solve(first_part, second_part)
        except np.linalg.LinAlgError:
            # Fallback to equilibrium returns if matrix is singular
            adjusted_returns = equilibrium_returns
        
        return adjusted_returns
    
    def _get_asset_data(self, portfolio: Portfolio) -> Optional[Dict[str, Any]]:
        """Get market data for portfolio assets"""
        if not portfolio.positions:
            return None
        
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        return self._get_asset_data_from_ids(asset_ids)
    
    def _get_asset_data_from_ids(self, asset_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Get market data for specific asset IDs"""
        if not self.market_data_service:
            # Use default values
            n_assets = len(asset_ids)
            expected_returns = np.array([0.08] * n_assets)
            cov_matrix = np.eye(n_assets) * 0.04
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
                n_assets = len(asset_ids)
                cov_matrix = np.eye(n_assets) * 0.04
            
            return {
                'asset_ids': asset_ids,
                'expected_returns': expected_returns,
                'covariance_matrix': cov_matrix
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get market data: {str(e)}")
    
    def _get_market_caps(self, asset_ids: List[str]) -> Dict[str, float]:
        """Get market capitalizations for assets"""
        if not self.market_data_service:
            return {}
        
        market_caps = {}
        for asset_id in asset_ids:
            market_cap = self.market_data_service.get_market_cap(asset_id)
            if market_cap is not None:
                market_caps[asset_id] = market_cap
        
        return market_caps
    
    def validate_views(self, market_views: List[MarketView]) -> List[str]:
        """Validate market views for Black-Litterman optimization"""
        errors = []
        
        for i, view in enumerate(market_views):
            try:
                view.validate_market_view()
            except ValueError as e:
                errors.append(f"View {i+1}: {str(e)}")
        
        # Check for conflicting views
        for i, view1 in enumerate(market_views):
            for j, view2 in enumerate(market_views[i+1:], i+1):
                if view1.conflicts_with(view2):
                    errors.append(f"Views {i+1} and {j+1} conflict with each other")
        
        return errors





















