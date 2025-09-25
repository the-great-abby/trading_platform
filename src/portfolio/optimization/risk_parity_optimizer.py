"""
Risk Parity Optimizer
Implementation of risk parity and equal risk contribution optimization
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

from scipy.optimize import minimize

from ..models import Portfolio, OptimizationResult, OptimizationMethod


class RiskParityOptimizer:
    """Risk parity optimizer for equal risk contribution portfolios"""
    
    def __init__(self, market_data_service=None):
        """Initialize risk parity optimizer"""
        self.market_data_service = market_data_service
        
        if not CVXPY_AVAILABLE:
            raise ImportError("cvxpy is required for risk parity optimization. Install with: pip install cvxpy")
    
    def optimize_equal_risk_contribution(self,
                                        portfolio: Portfolio,
                                        rebalance_threshold: float = 0.05,
                                        max_iterations: int = 1000,
                                        tolerance: float = 1e-6,
                                        max_optimization_time: float = 60.0) -> OptimizationResult:
        """Optimize portfolio for equal risk contribution (ERC)"""
        
        start_time = time.time()
        
        # Get market data
        asset_data = self._get_asset_data(portfolio)
        if not asset_data:
            raise ValueError("Insufficient market data for optimization")
        
        asset_ids = asset_data['asset_ids']
        cov_matrix = asset_data['covariance_matrix']
        n_assets = len(asset_ids)
        
        # Use scipy optimization for risk parity
        try:
            # Initial guess: equal weights
            x0 = np.ones(n_assets) / n_assets
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
            ]
            
            # Add portfolio constraints
            if portfolio.long_only:
                constraints.append({'type': 'ineq', 'fun': lambda x: x})  # Non-negative weights
            
            if portfolio.max_single_asset_weight < 1.0:
                max_weight = portfolio.max_single_asset_weight
                constraints.append({'type': 'ineq', 'fun': lambda x: max_weight - x})  # Max weight constraint
            
            # Bounds
            bounds = [(0.0, portfolio.max_single_asset_weight if portfolio.long_only else 1.0) 
                     for _ in range(n_assets)]
            
            # Optimize for equal risk contribution
            result = minimize(
                fun=self._risk_parity_objective,
                x0=x0,
                args=(cov_matrix,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': max_iterations, 'ftol': tolerance}
            )
            
            optimization_time = time.time() - start_time
            
            if optimization_time > max_optimization_time:
                raise ValueError(f"Optimization exceeded time limit of {max_optimization_time}s")
            
            if not result.success:
                raise ValueError(f"Optimization failed: {result.message}")
            
            # Extract results
            optimal_weights = result.x
            asset_weights = dict(zip(asset_ids, optimal_weights))
            
            # Calculate portfolio metrics
            portfolio_variance = optimal_weights.T @ cov_matrix @ optimal_weights
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Calculate expected return (simplified)
            expected_returns = asset_data.get('expected_returns', np.array([0.08] * n_assets))
            expected_return = np.dot(optimal_weights, expected_returns)
            
            # Calculate risk contributions
            risk_contributions = self._calculate_risk_contributions(optimal_weights, cov_matrix)
            risk_contributions_dict = dict(zip(asset_ids, risk_contributions))
            
            # Calculate Sharpe ratio (simplified)
            risk_free_rate = 0.02
            sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Create optimization result
            optimization_result = OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.RISK_PARITY,
                risk_free_rate=risk_free_rate,
                expected_return=expected_return,
                expected_volatility=portfolio_volatility,
                sharpe_ratio=sharpe_ratio,
                asset_weights=asset_weights,
                risk_contributions=risk_contributions_dict,
                convergence_status=result.success,
                optimization_time=optimization_time,
                iteration_count=result.nit
            )
            
            return optimization_result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            return OptimizationResult(
                portfolio_id=portfolio.portfolio_id,
                optimization_method=OptimizationMethod.RISK_PARITY,
                convergence_status=False,
                optimization_time=optimization_time,
                constraint_violations=[str(e)]
            )
    
    def optimize_with_constraints(self,
                                 portfolio: Portfolio,
                                 max_sector_weight: float = 0.40,
                                 min_weight: float = 0.01,
                                 max_weight: float = 0.20,
                                 **kwargs) -> OptimizationResult:
        """Optimize risk parity with additional constraints"""
        
        # Add constraints to the optimization
        constraints = {
            'max_sector_weight': max_sector_weight,
            'min_weight': min_weight,
            'max_weight': max_weight,
            **kwargs
        }
        
        # For now, use the basic ERC optimization
        # In a full implementation, you would modify the optimization to include sector constraints
        result = self.optimize_equal_risk_contribution(portfolio, **kwargs)
        
        # Add constraint information to result
        result.constraint_violations = []
        
        # Check if constraints are satisfied
        for asset_id, weight in result.asset_weights.items():
            if weight < min_weight:
                result.constraint_violations.append(f"{asset_id} weight {weight:.4f} below minimum {min_weight}")
            if weight > max_weight:
                result.constraint_violations.append(f"{asset_id} weight {weight:.4f} above maximum {max_weight}")
        
        return result
    
    def optimize_dynamic_risk_parity(self,
                                    portfolio: Portfolio,
                                    volatility_target: float = 0.16,
                                    lookback_period: int = 30,
                                    **kwargs) -> OptimizationResult:
        """Optimize dynamic risk parity with volatility targeting"""
        
        # Get historical volatility data
        if self.market_data_service:
            # In a real implementation, you would get historical data and calculate realized volatility
            realized_volatility = self.market_data_service.get_realized_volatility(
                [pos.asset_id for pos in portfolio.positions],
                lookback_period
            )
        else:
            # Use default volatility
            realized_volatility = 0.16
        
        # Optimize for risk parity
        result = self.optimize_equal_risk_contribution(portfolio, **kwargs)
        
        # Add volatility targeting information
        result.volatility_target = volatility_target
        result.realized_volatility = realized_volatility
        
        return result
    
    def _risk_parity_objective(self, weights: np.ndarray, cov_matrix: np.ndarray) -> float:
        """Objective function for risk parity optimization"""
        # Portfolio variance
        portfolio_variance = weights.T @ cov_matrix @ weights
        
        if portfolio_variance <= 0:
            return 1e6  # Large penalty for invalid portfolio
        
        # Portfolio volatility
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Risk contributions
        risk_contributions = self._calculate_risk_contributions(weights, cov_matrix)
        
        # Equal risk contribution objective: minimize sum of squared deviations from equal contribution
        target_contribution = 1.0 / len(weights)
        deviations = risk_contributions - target_contribution
        objective = np.sum(deviations ** 2)
        
        return objective
    
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
    
    def _create_default_covariance_matrix(self, asset_ids: List[str]) -> np.ndarray:
        """Create default covariance matrix with some correlation"""
        n_assets = len(asset_ids)
        
        # Create a more realistic covariance matrix with some correlation
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
    
    def validate_risk_parity_result(self, result: OptimizationResult) -> List[str]:
        """Validate risk parity optimization result"""
        errors = []
        
        if not result.asset_weights:
            errors.append("No asset weights in result")
            return errors
        
        # Check weights sum to 1.0
        total_weight = sum(result.asset_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Weights sum to {total_weight:.4f}, not 1.0")
        
        # Check risk contributions are approximately equal
        if result.risk_contributions:
            contributions = list(result.risk_contributions.values())
            if contributions:
                avg_contribution = sum(contributions) / len(contributions)
                max_deviation = max(abs(c - avg_contribution) for c in contributions)
                
                if max_deviation > 0.05:  # 5% tolerance
                    errors.append(f"Risk contributions not equal (max deviation: {max_deviation:.4f})")
        
        # Check for negative weights (if long-only)
        negative_weights = [asset for asset, weight in result.asset_weights.items() if weight < 0]
        if negative_weights:
            errors.append(f"Negative weights found for assets: {negative_weights}")
        
        return errors

