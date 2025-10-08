"""
Portfolio Calculation Utilities
Comprehensive financial calculations for portfolio management
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
import math

from ..models.portfolio import Portfolio
from ..models.position import Position
from ..models.asset import Asset
from ..models.risk_metrics import RiskMetrics

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    information_ratio: float
    tracking_error: float
    beta: float
    alpha: float
    r_squared: float

@dataclass
class RiskMetrics:
    """Risk calculation results"""
    portfolio_volatility: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    beta: float
    correlation_matrix: np.ndarray
    risk_contributions: Dict[str, float]
    systematic_risk: float
    idiosyncratic_risk: float

class PortfolioCalculator:
    """Comprehensive portfolio calculation utilities"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_portfolio_value(self, portfolio: Portfolio) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            pos.quantity * pos.current_price 
            for pos in portfolio.positions 
            if pos.current_price is not None
        )
        return position_value + portfolio.cash_balance
    
    def calculate_position_weights(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calculate position weights in portfolio"""
        total_value = self.calculate_portfolio_value(portfolio)
        if total_value == 0:
            return {}
        
        weights = {}
        for position in portfolio.positions:
            if position.current_price is not None:
                position_value = position.quantity * position.current_price
                weights[position.asset_id] = position_value / total_value
        
        return weights
    
    def calculate_portfolio_returns(self, portfolio_values: List[float]) -> List[float]:
        """Calculate portfolio returns from values"""
        if len(portfolio_values) < 2:
            return []
        
        returns = []
        for i in range(1, len(portfolio_values)):
            if portfolio_values[i-1] != 0:
                ret = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                returns.append(ret)
            else:
                returns.append(0.0)
        
        return returns
    
    def calculate_annualized_return(self, returns: List[float], periods_per_year: int = 252) -> float:
        """Calculate annualized return"""
        if not returns:
            return 0.0
        
        total_return = np.prod([1 + r for r in returns]) - 1
        years = len(returns) / periods_per_year
        
        if years <= 0:
            return 0.0
        
        annualized_return = (1 + total_return) ** (1 / years) - 1
        return annualized_return
    
    def calculate_volatility(self, returns: List[float], periods_per_year: int = 252) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0
        
        return np.std(returns, ddof=1) * math.sqrt(periods_per_year)
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: Optional[float] = None) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0.0
        
        risk_free_rate = risk_free_rate or self.risk_free_rate
        excess_returns = [r - risk_free_rate for r in returns]
        
        if len(excess_returns) < 2:
            return 0.0
        
        mean_excess_return = np.mean(excess_returns)
        volatility = np.std(excess_returns, ddof=1)
        
        if volatility == 0:
            return 0.0
        
        return mean_excess_return / volatility * math.sqrt(252)  # Annualized
    
    def calculate_sortino_ratio(self, returns: List[float], risk_free_rate: Optional[float] = None) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if not returns:
            return 0.0
        
        risk_free_rate = risk_free_rate or self.risk_free_rate
        excess_returns = [r - risk_free_rate for r in returns]
        
        if len(excess_returns) < 2:
            return 0.0
        
        mean_excess_return = np.mean(excess_returns)
        downside_returns = [r for r in excess_returns if r < 0]
        
        if not downside_returns:
            return float('inf') if mean_excess_return > 0 else 0.0
        
        downside_deviation = np.std(downside_returns, ddof=1)
        
        if downside_deviation == 0:
            return float('inf') if mean_excess_return > 0 else 0.0
        
        return mean_excess_return / downside_deviation * math.sqrt(252)  # Annualized
    
    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not portfolio_values:
            return 0.0
        
        peak = portfolio_values[0]
        max_dd = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_calmar_ratio(self, returns: List[float], portfolio_values: List[float]) -> float:
        """Calculate Calmar ratio"""
        if not returns or not portfolio_values:
            return 0.0
        
        annualized_return = self.calculate_annualized_return(returns)
        max_drawdown = self.calculate_max_drawdown(portfolio_values)
        
        if max_drawdown == 0:
            return float('inf') if annualized_return > 0 else 0.0
        
        return annualized_return / max_drawdown
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            return sorted_returns[-1]
        
        return sorted_returns[index]
    
    def calculate_cvar(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if not returns:
            return 0.0
        
        var = self.calculate_var(returns, confidence_level)
        tail_returns = [r for r in returns if r <= var]
        
        if not tail_returns:
            return var
        
        return np.mean(tail_returns)
    
    def calculate_beta(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate portfolio beta"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 1.0
        
        portfolio_array = np.array(portfolio_returns)
        benchmark_array = np.array(benchmark_returns)
        
        covariance = np.cov(portfolio_array, benchmark_array)[0, 1]
        benchmark_variance = np.var(benchmark_array, ddof=1)
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    def calculate_alpha(self, portfolio_returns: List[float], benchmark_returns: List[float], 
                       risk_free_rate: Optional[float] = None) -> float:
        """Calculate portfolio alpha"""
        if not portfolio_returns or not benchmark_returns:
            return 0.0
        
        risk_free_rate = risk_free_rate or self.risk_free_rate
        
        portfolio_annual_return = self.calculate_annualized_return(portfolio_returns)
        benchmark_annual_return = self.calculate_annualized_return(benchmark_returns)
        beta = self.calculate_beta(portfolio_returns, benchmark_returns)
        
        expected_return = risk_free_rate + beta * (benchmark_annual_return - risk_free_rate)
        alpha = portfolio_annual_return - expected_return
        
        return alpha
    
    def calculate_information_ratio(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate information ratio"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        tracking_error = np.std(excess_returns, ddof=1)
        
        if tracking_error == 0:
            return 0.0
        
        mean_excess_return = np.mean(excess_returns)
        return mean_excess_return / tracking_error * math.sqrt(252)  # Annualized
    
    def calculate_tracking_error(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate tracking error"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        return np.std(excess_returns, ddof=1) * math.sqrt(252)  # Annualized
    
    def calculate_r_squared(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate R-squared"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        portfolio_array = np.array(portfolio_returns)
        benchmark_array = np.array(benchmark_returns)
        
        correlation = np.corrcoef(portfolio_array, benchmark_array)[0, 1]
        return correlation ** 2
    
    def calculate_performance_metrics(self, portfolio_values: List[float], 
                                    benchmark_values: Optional[List[float]] = None,
                                    risk_free_rate: Optional[float] = None) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not portfolio_values:
            return PerformanceMetrics(
                total_return=0.0, annualized_return=0.0, volatility=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
                max_drawdown=0.0, var_95=0.0, cvar_95=0.0,
                information_ratio=0.0, tracking_error=0.0,
                beta=1.0, alpha=0.0, r_squared=0.0
            )
        
        portfolio_returns = self.calculate_portfolio_returns(portfolio_values)
        
        if not portfolio_returns:
            return PerformanceMetrics(
                total_return=0.0, annualized_return=0.0, volatility=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
                max_drawdown=0.0, var_95=0.0, cvar_95=0.0,
                information_ratio=0.0, tracking_error=0.0,
                beta=1.0, alpha=0.0, r_squared=0.0
            )
        
        # Basic metrics
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0] if portfolio_values[0] != 0 else 0.0
        annualized_return = self.calculate_annualized_return(portfolio_returns)
        volatility = self.calculate_volatility(portfolio_returns)
        sharpe_ratio = self.calculate_sharpe_ratio(portfolio_returns, risk_free_rate)
        sortino_ratio = self.calculate_sortino_ratio(portfolio_returns, risk_free_rate)
        max_drawdown = self.calculate_max_drawdown(portfolio_values)
        calmar_ratio = self.calculate_calmar_ratio(portfolio_returns, portfolio_values)
        
        # Risk metrics
        var_95 = self.calculate_var(portfolio_returns, 0.95)
        cvar_95 = self.calculate_cvar(portfolio_returns, 0.95)
        
        # Benchmark-relative metrics
        if benchmark_values and len(benchmark_values) == len(portfolio_values):
            benchmark_returns = self.calculate_portfolio_returns(benchmark_values)
            beta = self.calculate_beta(portfolio_returns, benchmark_returns)
            alpha = self.calculate_alpha(portfolio_returns, benchmark_returns, risk_free_rate)
            information_ratio = self.calculate_information_ratio(portfolio_returns, benchmark_returns)
            tracking_error = self.calculate_tracking_error(portfolio_returns, benchmark_returns)
            r_squared = self.calculate_r_squared(portfolio_returns, benchmark_returns)
        else:
            beta = 1.0
            alpha = 0.0
            information_ratio = 0.0
            tracking_error = 0.0
            r_squared = 0.0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            information_ratio=information_ratio,
            tracking_error=tracking_error,
            beta=beta,
            alpha=alpha,
            r_squared=r_squared
        )
    
    def calculate_risk_metrics(self, portfolio_returns: List[float], 
                             position_weights: Dict[str, float],
                             asset_returns: Dict[str, List[float]]) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        if not portfolio_returns:
            return RiskMetrics(
                portfolio_volatility=0.0, var_95=0.0, var_99=0.0,
                cvar_95=0.0, cvar_99=0.0, max_drawdown=0.0,
                beta=1.0, correlation_matrix=np.array([]),
                risk_contributions={}, systematic_risk=0.0,
                idiosyncratic_risk=0.0
            )
        
        # Basic risk metrics
        portfolio_volatility = self.calculate_volatility(portfolio_returns)
        var_95 = self.calculate_var(portfolio_returns, 0.95)
        var_99 = self.calculate_var(portfolio_returns, 0.99)
        cvar_95 = self.calculate_cvar(portfolio_returns, 0.95)
        cvar_99 = self.calculate_cvar(portfolio_returns, 0.99)
        
        # Calculate portfolio values for max drawdown
        initial_value = 100000  # Assume initial portfolio value
        portfolio_values = [initial_value]
        for ret in portfolio_returns:
            portfolio_values.append(portfolio_values[-1] * (1 + ret))
        
        max_drawdown = self.calculate_max_drawdown(portfolio_values)
        
        # Correlation matrix and risk contributions
        correlation_matrix = np.array([])
        risk_contributions = {}
        systematic_risk = 0.0
        idiosyncratic_risk = 0.0
        
        if asset_returns and position_weights:
            # Create returns matrix
            asset_ids = list(asset_returns.keys())
            if len(asset_ids) > 1:
                returns_matrix = np.array([asset_returns[asset_id] for asset_id in asset_ids])
                
                # Calculate correlation matrix
                correlation_matrix = np.corrcoef(returns_matrix)
                
                # Calculate risk contributions
                weights = np.array([position_weights.get(asset_id, 0.0) for asset_id in asset_ids])
                cov_matrix = np.cov(returns_matrix) * 252  # Annualized covariance
                
                portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
                
                if portfolio_variance > 0:
                    for i, asset_id in enumerate(asset_ids):
                        marginal_risk = np.dot(cov_matrix[i, :], weights)
                        risk_contributions[asset_id] = (weights[i] * marginal_risk) / portfolio_variance
                
                # Decompose risk
                systematic_risk = portfolio_variance ** 0.5
                idiosyncratic_risk = 0.0  # Would need more sophisticated calculation
        
        return RiskMetrics(
            portfolio_volatility=portfolio_volatility,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_drawdown=max_drawdown,
            beta=1.0,  # Would need benchmark data
            correlation_matrix=correlation_matrix,
            risk_contributions=risk_contributions,
            systematic_risk=systematic_risk,
            idiosyncratic_risk=idiosyncratic_risk
        )
    
    def calculate_tax_metrics(self, portfolio: Portfolio, tax_rates: Dict[str, float]) -> Dict[str, float]:
        """Calculate tax-related metrics"""
        metrics = {
            "total_unrealized_gains": 0.0,
            "total_unrealized_losses": 0.0,
            "total_realized_gains": 0.0,
            "total_realized_losses": 0.0,
            "tax_liability": 0.0,
            "tax_benefit": 0.0,
            "net_tax_impact": 0.0
        }
        
        for position in portfolio.positions:
            if position.current_price is not None and position.average_cost is not None:
                position_value = position.quantity * position.current_price
                cost_basis = position.quantity * position.average_cost
                unrealized_pnl = position_value - cost_basis
                
                if unrealized_pnl > 0:
                    metrics["total_unrealized_gains"] += unrealized_pnl
                else:
                    metrics["total_unrealized_losses"] += abs(unrealized_pnl)
                
                # Calculate tax impact
                holding_period = (datetime.now() - position.created_at).days
                is_long_term = holding_period > 365
                
                tax_rate = tax_rates.get("long_term" if is_long_term else "short_term", 0.20)
                
                if unrealized_pnl > 0:
                    metrics["tax_liability"] += unrealized_pnl * tax_rate
                else:
                    metrics["tax_benefit"] += abs(unrealized_pnl) * tax_rate
        
        metrics["net_tax_impact"] = metrics["tax_liability"] - metrics["tax_benefit"]
        
        return metrics
    
    def calculate_rebalancing_metrics(self, current_weights: Dict[str, float], 
                                    target_weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate rebalancing metrics"""
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        total_drift = 0.0
        trades = {}
        trade_value = 0.0
        
        for asset in all_assets:
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weights.get(asset, 0.0)
            drift = abs(current_weight - target_weight)
            
            total_drift += drift
            
            if drift > 0.001:  # 0.1% threshold
                trades[asset] = {
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "drift": drift,
                    "trade_direction": "buy" if target_weight > current_weight else "sell"
                }
                
                # Estimate trade value (would need portfolio value)
                trade_value += drift * 100000  # Assume $100k portfolio
        
        return {
            "total_drift": total_drift,
            "number_of_trades": len(trades),
            "trades": trades,
            "estimated_trade_value": trade_value,
            "rebalancing_urgency": "high" if total_drift > 0.1 else "medium" if total_drift > 0.05 else "low"
        }

class OptimizationCalculator:
    """Specialized calculations for portfolio optimization"""
    
    def calculate_efficient_frontier(self, expected_returns: np.ndarray, 
                                   cov_matrix: np.ndarray, 
                                   num_portfolios: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate efficient frontier"""
        n_assets = len(expected_returns)
        
        # Generate random portfolio weights
        np.random.seed(42)
        weights_list = []
        returns_list = []
        volatilities_list = []
        
        for _ in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(n_assets)
            weights = weights / np.sum(weights)
            
            # Calculate portfolio return and volatility
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            weights_list.append(weights)
            returns_list.append(portfolio_return)
            volatilities_list.append(portfolio_volatility)
        
        return np.array(returns_list), np.array(volatilities_list), np.array(weights_list)
    
    def calculate_risk_parity_weights(self, cov_matrix: np.ndarray, 
                                    risk_budget: Optional[np.ndarray] = None) -> np.ndarray:
        """Calculate risk parity weights"""
        n_assets = cov_matrix.shape[0]
        
        if risk_budget is None:
            risk_budget = np.ones(n_assets) / n_assets
        
        # Use iterative approach to find risk parity weights
        weights = np.ones(n_assets) / n_assets
        max_iterations = 1000
        tolerance = 1e-6
        
        for _ in range(max_iterations):
            # Calculate risk contributions
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            risk_contributions = (weights * np.dot(cov_matrix, weights)) / portfolio_variance
            
            # Calculate scaling factors
            scaling_factors = risk_budget / risk_contributions
            scaling_factors = scaling_factors / np.mean(scaling_factors)
            
            # Update weights
            new_weights = weights * scaling_factors
            new_weights = new_weights / np.sum(new_weights)
            
            # Check convergence
            if np.max(np.abs(new_weights - weights)) < tolerance:
                break
            
            weights = new_weights
        
        return weights
    
    def calculate_black_litterman_expected_returns(self, market_caps: np.ndarray,
                                                 cov_matrix: np.ndarray,
                                                 risk_aversion: float = 3.0,
                                                 views: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Calculate Black-Litterman expected returns"""
        n_assets = len(market_caps)
        
        # Calculate market weights
        market_weights = market_caps / np.sum(market_caps)
        
        # Calculate implied equilibrium returns
        implied_returns = risk_aversion * np.dot(cov_matrix, market_weights)
        
        if views is None:
            return implied_returns
        
        # Implement Black-Litterman formula
        # This is a simplified version - full implementation would be more complex
        return implied_returns

# Global calculator instances
_portfolio_calculator: Optional[PortfolioCalculator] = None
_optimization_calculator: Optional[OptimizationCalculator] = None

def get_portfolio_calculator(risk_free_rate: Optional[float] = None) -> PortfolioCalculator:
    """Get global portfolio calculator"""
    global _portfolio_calculator
    if _portfolio_calculator is None or risk_free_rate is not None:
        _portfolio_calculator = PortfolioCalculator(risk_free_rate)
    return _portfolio_calculator

def get_optimization_calculator() -> OptimizationCalculator:
    """Get global optimization calculator"""
    global _optimization_calculator
    if _optimization_calculator is None:
        _optimization_calculator = OptimizationCalculator()
    return _optimization_calculator

def calculate_portfolio_performance(portfolio_values: List[float], 
                                  benchmark_values: Optional[List[float]] = None,
                                  risk_free_rate: Optional[float] = None) -> PerformanceMetrics:
    """Calculate portfolio performance metrics"""
    calculator = get_portfolio_calculator(risk_free_rate)
    return calculator.calculate_performance_metrics(portfolio_values, benchmark_values, risk_free_rate)

def calculate_portfolio_risk(portfolio_returns: List[float], 
                           position_weights: Dict[str, float],
                           asset_returns: Dict[str, List[float]]) -> RiskMetrics:
    """Calculate portfolio risk metrics"""
    calculator = get_portfolio_calculator()
    return calculator.calculate_risk_metrics(portfolio_returns, position_weights, asset_returns)
























