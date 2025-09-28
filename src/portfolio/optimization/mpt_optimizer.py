"""
Modern Portfolio Theory (MPT) Optimizer
Implementation of Markowitz mean-variance optimization
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

from ..models import Portfolio, OptimizationResult, OptimizationMethod, EfficientFrontierPoint


class MPTOptimizer:
    """Modern Portfolio Theory optimizer using convex optimization"""
    
    def __init__(self, market_data_service=None):
        """Initialize MPT optimizer"""
        self.market_data_service = market_data_service
        
        if not CVXPY_AVAILABLE:
            raise ImportError("cvxpy is required for MPT optimization. Install with: pip install cvxpy")
    
    def optimize_portfolio(self,
                          portfolio: Portfolio,
                          optimization_method: str = "max_sharpe",
                          risk_free_rate: float = 0.02,
                          transaction_cost_rate: float = 0.001,
                          max_optimization_time: float = 60.0,
                          **constraints) -> OptimizationResult:
        """Optimize portfolio using Modern Portfolio Theory"""
        
        start_time = time.time()
        
        # Get market data
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            raise ValueError("Insufficient market data for optimization")
        
        # Extract expected returns and covariance matrix
        expected_returns = asset_data['expected_returns']
        cov_matrix = asset_data['covariance_matrix']
        asset_ids = asset_data['asset_ids']
        
        # Set up optimization problem
        n_assets = len(asset_ids)
        weights = cp.Variable(n_assets)
        
        # Expected portfolio return
        portfolio_return = expected_returns.T @ weights
        
        # Portfolio variance
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        portfolio_volatility = cp.sqrt(portfolio_variance)
        
        # Define constraints
        optimization_constraints = [
            cp.sum(weights) == 1,  # Weights sum to 1
            weights >= 0 if portfolio.long_only else weights >= -1  # Long-only or allow shorting
        ]
        
        # Add custom constraints
        if 'max_single_asset_weight' in constraints:
            max_weight = constraints['max_single_asset_weight']
            optimization_constraints.append(weights <= max_weight)
        
        if 'min_weight' in constraints:
            min_weight = constraints['min_weight']
            optimization_constraints.append(weights >= min_weight)
        
        # Add transaction costs if specified
        transaction_costs = 0
        if transaction_cost_rate > 0 and hasattr(portfolio, 'positions'):
            current_weights = self._get_current_weights(portfolio, asset_ids)
            if current_weights is not None:
                weight_changes = cp.abs(weights - current_weights)
                transaction_costs = transaction_cost_rate * cp.sum(weight_changes)
        
        # Define objective function
        if optimization_method == "max_sharpe":
            # Maximize Sharpe ratio
            objective = cp.Maximize((portfolio_return - risk_free_rate) / portfolio_volatility)
        elif optimization_method == "min_variance":
            # Minimize variance
            objective = cp.Minimize(portfolio_variance)
        elif optimization_method == "max_return":
            # Maximize return
            objective = cp.Maximize(portfolio_return)
        elif optimization_method == "target_volatility":
            # Target volatility
            target_vol = constraints.get('target_volatility', 0.15)
            optimization_constraints.append(portfolio_volatility <= target_vol)
            objective = cp.Maximize(portfolio_return)
        else:
            raise ValueError(f"Unknown optimization method: {optimization_method}")
        
        # Solve optimization problem
        problem = cp.Problem(objective, optimization_constraints)
        
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
            
            # Create optimization result
            result = OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.MPT,
                risk_free_rate=risk_free_rate,
                expected_return=expected_return,
                expected_volatility=expected_volatility,
                sharpe_ratio=sharpe_ratio,
                asset_weights=asset_weights,
                convergence_status=True,
                optimization_time=optimization_time,
                iteration_count=problem.solver_stats.num_iters if hasattr(problem.solver_stats, 'num_iters') else 0,
                transaction_costs=float(transaction_costs.value) if transaction_cost_rate > 0 else 0.0
            )
            
            return result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            return OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.MPT,
                risk_free_rate=risk_free_rate,
                convergence_status=False,
                optimization_time=optimization_time,
                constraint_violations=[str(e)]
            )
    
    def generate_efficient_frontier(self,
                                   portfolio: Portfolio,
                                   num_points: int = 20,
                                   risk_free_rate: float = 0.02) -> List[EfficientFrontierPoint]:
        """Generate efficient frontier points"""
        
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            raise ValueError("Insufficient market data for efficient frontier")
        
        expected_returns = asset_data['expected_returns']
        cov_matrix = asset_data['covariance_matrix']
        asset_ids = asset_data['asset_ids']
        
        n_assets = len(asset_ids)
        weights = cp.Variable(n_assets)
        
        # Portfolio metrics
        portfolio_return = expected_returns.T @ weights
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0 if portfolio.long_only else weights >= -1
        ]
        
        # Add custom constraints
        if portfolio.max_single_asset_weight < 1.0:
            constraints.append(weights <= portfolio.max_single_asset_weight)
        
        # Generate frontier points
        frontier_points = []
        
        # Find minimum and maximum returns
        min_return_problem = cp.Problem(cp.Minimize(portfolio_return), constraints)
        min_return_problem.solve()
        min_return = float(portfolio_return.value)
        
        max_return_problem = cp.Problem(cp.Maximize(portfolio_return), constraints)
        max_return_problem.solve()
        max_return = float(portfolio_return.value)
        
        # Generate points along the frontier
        target_returns = np.linspace(min_return, max_return, num_points)
        
        for target_return in target_returns:
            # Minimize variance for given return
            objective = cp.Minimize(portfolio_variance)
            problem_constraints = constraints + [portfolio_return >= target_return]
            
            problem = cp.Problem(objective, problem_constraints)
            problem.solve(verbose=False)
            
            if problem.status in ["optimal", "optimal_inaccurate"] and weights.value is not None:
                optimal_weights = weights.value
                actual_return = float(portfolio_return.value)
                actual_variance = float(portfolio_variance.value)
                actual_volatility = np.sqrt(actual_variance)
                sharpe_ratio = (actual_return - risk_free_rate) / actual_volatility if actual_volatility > 0 else 0
                
                asset_weights_dict = dict(zip(asset_ids, optimal_weights))
                
                point = EfficientFrontierPoint(
                    expected_return=actual_return,
                    volatility=actual_volatility,
                    sharpe_ratio=sharpe_ratio,
                    asset_weights=asset_weights_dict
                )
                
                frontier_points.append(point)
        
        return frontier_points
    
    def optimize_for_target_volatility(self,
                                      portfolio: Portfolio,
                                      target_volatility: float,
                                      risk_free_rate: float = 0.02) -> OptimizationResult:
        """Optimize portfolio for target volatility"""
        return self.optimize_portfolio(
            portfolio=portfolio,
            optimization_method="target_volatility",
            risk_free_rate=risk_free_rate,
            target_volatility=target_volatility
        )
    
    def _get_asset_data(self, portfolio: Portfolio) -> Optional[Dict[str, Any]]:
        """Get market data for portfolio assets"""
        if not portfolio.positions:
            return None
        
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        
        if not self.market_data_service:
            # Use default values if no market data service
            n_assets = len(asset_ids)
            expected_returns = np.array([0.08] * n_assets)  # 8% default return
            cov_matrix = np.eye(n_assets) * 0.04  # 20% volatility, no correlation
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
                # Create default covariance matrix
                n_assets = len(asset_ids)
                cov_matrix = np.eye(n_assets) * 0.04  # 20% volatility, no correlation
            
            return {
                'asset_ids': asset_ids,
                'expected_returns': expected_returns,
                'covariance_matrix': cov_matrix
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get market data: {str(e)}")
    
    def _get_current_weights(self, portfolio: Portfolio, asset_ids: List[str]) -> Optional[np.ndarray]:
        """Get current portfolio weights"""
        if not portfolio.positions:
            return None
        
        weights = []
        total_value = portfolio.calculate_total_value()
        
        if total_value == 0:
            return None
        
        for asset_id in asset_ids:
            position = next((p for p in portfolio.positions if p.asset_id == asset_id), None)
            if position:
                weight = position.market_value / total_value
                weights.append(weight)
            else:
                weights.append(0.0)
        
        return np.array(weights)
    
    def validate_optimization_inputs(self, portfolio: Portfolio, **kwargs) -> List[str]:
        """Validate optimization inputs"""
        errors = []
        
        if not portfolio.positions:
            errors.append("Portfolio must have at least one position")
        
        if kwargs.get('risk_free_rate', 0.02) < 0:
            errors.append("Risk-free rate cannot be negative")
        
        if kwargs.get('transaction_cost_rate', 0.001) < 0:
            errors.append("Transaction cost rate cannot be negative")
        
        target_vol = kwargs.get('target_volatility')
        if target_vol is not None and target_vol <= 0:
            errors.append("Target volatility must be positive")
        
        return errors



