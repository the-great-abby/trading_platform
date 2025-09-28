#!/usr/bin/env python3
"""
Unit tests for optimization algorithms
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any

# Import optimization algorithms
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.portfolio.optimization.mpt_optimizer import MPTOptimizer
from src.portfolio.optimization.black_litterman_optimizer import BlackLittermanOptimizer
from src.portfolio.optimization.risk_parity_optimizer import RiskParityOptimizer
from src.portfolio.models.portfolio import Portfolio, RiskTolerance
from src.portfolio.models.position import Position
from src.portfolio.models.asset import Asset, AssetType


class TestMPTOptimizer:
    """Test Modern Portfolio Theory optimizer"""
    
    def setup_method(self):
        """Set up test data"""
        self.assets = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        self.returns = np.array([
            [0.01, 0.02, -0.01, 0.03, 0.005],
            [0.015, 0.01, 0.02, -0.005, 0.01],
            [-0.005, 0.03, 0.015, 0.02, 0.005],
            [0.02, -0.01, 0.01, 0.025, 0.015],
            [0.005, 0.015, 0.005, -0.01, 0.02]
        ])
        
        self.expected_returns = np.array([0.12, 0.15, 0.10, 0.20, 0.08])
        self.covariance_matrix = np.cov(self.returns.T)
        
        self.optimizer = MPTOptimizer()
    
    def test_mpt_optimizer_creation(self):
        """Test MPT optimizer creation"""
        assert self.optimizer is not None
        assert hasattr(self.optimizer, 'optimize')
        assert hasattr(self.optimizer, 'generate_efficient_frontier')
    
    def test_maximize_sharpe_ratio(self):
        """Test Sharpe ratio maximization"""
        result = self.optimizer.maximize_sharpe_ratio(
            expected_returns=self.expected_returns,
            covariance_matrix=self.covariance_matrix,
            risk_free_rate=0.02
        )
        
        assert result is not None
        assert "weights" in result
        assert "expected_return" in result
        assert "expected_volatility" in result
        assert "sharpe_ratio" in result
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check all weights are non-negative (long-only)
        assert np.all(weights >= 0)
        
        # Check Sharpe ratio is positive
        assert result["sharpe_ratio"] > 0
    
    def test_minimize_volatility(self):
        """Test volatility minimization"""
        result = self.optimizer.minimize_volatility(
            covariance_matrix=self.covariance_matrix
        )
        
        assert result is not None
        assert "weights" in result
        assert "expected_return" in result
        assert "expected_volatility" in result
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check all weights are non-negative
        assert np.all(weights >= 0)
        
        # Check volatility is positive
        assert result["expected_volatility"] > 0
    
    def test_target_return_optimization(self):
        """Test target return optimization"""
        target_return = 0.15
        
        result = self.optimizer.optimize_for_target_return(
            expected_returns=self.expected_returns,
            covariance_matrix=self.covariance_matrix,
            target_return=target_return
        )
        
        assert result is not None
        assert "weights" in result
        assert "expected_return" in result
        assert "expected_volatility" in result
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check expected return is close to target
        assert abs(result["expected_return"] - target_return) < 1e-6
    
    def test_efficient_frontier_generation(self):
        """Test efficient frontier generation"""
        frontier = self.optimizer.generate_efficient_frontier(
            expected_returns=self.expected_returns,
            covariance_matrix=self.covariance_matrix,
            num_portfolios=20,
            risk_free_rate=0.02
        )
        
        assert frontier is not None
        assert "returns" in frontier
        assert "volatilities" in frontier
        assert "weights" in frontier
        
        returns = frontier["returns"]
        volatilities = frontier["volatilities"]
        weights = frontier["weights"]
        
        # Check dimensions
        assert len(returns) == 20
        assert len(volatilities) == 20
        assert len(weights) == 20
        
        # Check each portfolio weights sum to 1
        for w in weights:
            assert abs(np.sum(w) - 1.0) < 1e-6
            assert np.all(w >= 0)  # Long-only constraint
        
        # Check efficient frontier properties
        # Returns should be increasing
        assert np.all(np.diff(returns) >= 0)
        
        # Volatilities should be increasing with returns
        assert np.all(np.diff(volatilities) >= 0)
    
    def test_portfolio_optimization_with_constraints(self):
        """Test portfolio optimization with constraints"""
        constraints = {
            "max_single_asset_weight": 0.30,
            "min_single_asset_weight": 0.05,
            "max_sector_weight": 0.50
        }
        
        result = self.optimizer.optimize(
            expected_returns=self.expected_returns,
            covariance_matrix=self.covariance_matrix,
            objective="maximize_sharpe",
            risk_free_rate=0.02,
            constraints=constraints
        )
        
        assert result is not None
        assert "weights" in result
        
        weights = result["weights"]
        
        # Check constraint satisfaction
        assert np.all(weights <= 0.30)  # Max single asset weight
        assert np.all(weights >= 0.05)  # Min single asset weight
        
        # Check weights sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
    
    def test_optimization_with_transaction_costs(self):
        """Test optimization with transaction costs"""
        current_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        transaction_cost_rate = 0.001
        
        result = self.optimizer.optimize(
            expected_returns=self.expected_returns,
            covariance_matrix=self.covariance_matrix,
            objective="maximize_sharpe",
            risk_free_rate=0.02,
            current_weights=current_weights,
            transaction_cost_rate=transaction_cost_rate
        )
        
        assert result is not None
        assert "weights" in result
        assert "transaction_cost" in result
        
        # Check transaction cost is calculated
        assert result["transaction_cost"] >= 0
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6


class TestBlackLittermanOptimizer:
    """Test Black-Litterman optimizer"""
    
    def setup_method(self):
        """Set up test data"""
        self.assets = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        self.market_caps = np.array([3000000, 2500000, 2800000, 800000, 3200000])  # Market caps in millions
        
        # Market equilibrium returns (CAPM)
        self.risk_free_rate = 0.02
        self.market_return = 0.08
        self.betas = np.array([1.2, 1.1, 1.0, 1.8, 0.9])
        self.equilibrium_returns = self.risk_free_rate + self.betas * (self.market_return - self.risk_free_rate)
        
        # Covariance matrix
        self.returns = np.array([
            [0.01, 0.02, -0.01, 0.03, 0.005],
            [0.015, 0.01, 0.02, -0.005, 0.01],
            [-0.005, 0.03, 0.015, 0.02, 0.005],
            [0.02, -0.01, 0.01, 0.025, 0.015],
            [0.005, 0.015, 0.005, -0.01, 0.02]
        ])
        self.covariance_matrix = np.cov(self.returns.T)
        
        self.optimizer = BlackLittermanOptimizer()
    
    def test_black_litterman_optimizer_creation(self):
        """Test Black-Litterman optimizer creation"""
        assert self.optimizer is not None
        assert hasattr(self.optimizer, 'optimize')
        assert hasattr(self.optimizer, 'calculate_equilibrium_returns')
    
    def test_equilibrium_returns_calculation(self):
        """Test equilibrium returns calculation"""
        equilibrium_returns = self.optimizer.calculate_equilibrium_returns(
            market_caps=self.market_caps,
            covariance_matrix=self.covariance_matrix,
            risk_aversion=3.0
        )
        
        assert equilibrium_returns is not None
        assert len(equilibrium_returns) == len(self.assets)
        
        # Check returns are reasonable
        assert np.all(equilibrium_returns > 0)
        assert np.all(equilibrium_returns < 1.0)  # Less than 100% return
    
    def test_black_litterman_optimization(self):
        """Test Black-Litterman optimization"""
        # Define market views
        views = [
            {
                "assets": ["AAPL"],
                "expected_return": 0.15,
                "confidence": 0.7,
                "type": "absolute"
            },
            {
                "assets": ["GOOGL", "MSFT"],
                "expected_return_diff": 0.05,
                "confidence": 0.6,
                "type": "relative"
            }
        ]
        
        result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=3.0,
            tau=0.05
        )
        
        assert result is not None
        assert "weights" in result
        assert "expected_returns" in result
        assert "expected_volatility" in result
        assert "sharpe_ratio" in result
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check all weights are non-negative
        assert np.all(weights >= 0)
        
        # Check Sharpe ratio is positive
        assert result["sharpe_ratio"] > 0
    
    def test_view_impact_analysis(self):
        """Test view impact analysis"""
        # Original optimization without views
        original_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=[],
            risk_aversion=3.0
        )
        
        # Optimization with views
        views = [
            {
                "assets": ["AAPL"],
                "expected_return": 0.18,
                "confidence": 0.8,
                "type": "absolute"
            }
        ]
        
        view_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=3.0
        )
        
        # Compare results
        original_weights = original_result["weights"]
        view_weights = view_result["weights"]
        
        # AAPL weight should increase due to bullish view
        aapl_index = self.assets.index("AAPL")
        assert view_weights[aapl_index] > original_weights[aapl_index]
    
    def test_confidence_level_impact(self):
        """Test confidence level impact on optimization"""
        views = [
            {
                "assets": ["TSLA"],
                "expected_return": 0.25,
                "confidence": 0.3,  # Low confidence
                "type": "absolute"
            }
        ]
        
        low_confidence_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=3.0
        )
        
        # High confidence view
        views[0]["confidence"] = 0.9
        
        high_confidence_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=3.0
        )
        
        # Higher confidence should have more impact
        tsla_index = self.assets.index("TSLA")
        low_weight = low_confidence_result["weights"][tsla_index]
        high_weight = high_confidence_result["weights"][tsla_index]
        
        assert high_weight > low_weight
    
    def test_risk_aversion_impact(self):
        """Test risk aversion impact on optimization"""
        views = [
            {
                "assets": ["AAPL"],
                "expected_return": 0.15,
                "confidence": 0.7,
                "type": "absolute"
            }
        ]
        
        # Low risk aversion
        low_risk_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=1.0
        )
        
        # High risk aversion
        high_risk_result = self.optimizer.optimize(
            equilibrium_returns=self.equilibrium_returns,
            covariance_matrix=self.covariance_matrix,
            views=views,
            risk_aversion=5.0
        )
        
        # Higher risk aversion should lead to lower volatility
        assert high_risk_result["expected_volatility"] < low_risk_result["expected_volatility"]


class TestRiskParityOptimizer:
    """Test Risk Parity optimizer"""
    
    def setup_method(self):
        """Set up test data"""
        self.assets = ["SPY", "QQQ", "IWM", "EFA", "VWO", "TLT", "IEF", "LQD"]
        
        # Create correlation matrix for diversified assets
        np.random.seed(42)
        n_assets = len(self.assets)
        correlation_matrix = np.eye(n_assets)
        
        # Add some correlation between similar assets
        correlation_matrix[0, 1] = correlation_matrix[1, 0] = 0.8  # SPY-QQQ
        correlation_matrix[0, 2] = correlation_matrix[2, 0] = 0.7  # SPY-IWM
        correlation_matrix[5, 6] = correlation_matrix[6, 5] = 0.9  # TLT-IEF
        
        # Convert to covariance matrix
        volatilities = np.array([0.15, 0.18, 0.20, 0.16, 0.22, 0.08, 0.06, 0.10])
        self.covariance_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        
        self.optimizer = RiskParityOptimizer()
    
    def test_risk_parity_optimizer_creation(self):
        """Test Risk Parity optimizer creation"""
        assert self.optimizer is not None
        assert hasattr(self.optimizer, 'optimize')
        assert hasattr(self.optimizer, 'calculate_risk_contributions')
    
    def test_risk_parity_optimization(self):
        """Test risk parity optimization"""
        result = self.optimizer.optimize(
            covariance_matrix=self.covariance_matrix,
            risk_budget_method="equal"
        )
        
        assert result is not None
        assert "weights" in result
        assert "risk_contributions" in result
        assert "expected_volatility" in result
        
        weights = result["weights"]
        risk_contributions = result["risk_contributions"]
        
        # Check weights sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check all weights are non-negative
        assert np.all(weights >= 0)
        
        # Check risk contributions are approximately equal
        risk_contrib_std = np.std(risk_contributions)
        expected_equal_contribution = 1.0 / len(self.assets)
        
        # Risk contributions should be close to equal (low standard deviation)
        assert risk_contrib_std < 0.05  # Less than 5% standard deviation
    
    def test_risk_contributions_calculation(self):
        """Test risk contributions calculation"""
        weights = np.array([0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])
        
        risk_contributions = self.optimizer.calculate_risk_contributions(
            weights=weights,
            covariance_matrix=self.covariance_matrix
        )
        
        assert risk_contributions is not None
        assert len(risk_contributions) == len(self.assets)
        
        # Risk contributions should sum to portfolio variance
        portfolio_variance = np.dot(weights, np.dot(self.covariance_matrix, weights))
        risk_contrib_sum = np.sum(risk_contributions)
        
        assert abs(risk_contrib_sum - portfolio_variance) < 1e-6
        
        # All risk contributions should be positive
        assert np.all(risk_contributions >= 0)
    
    def test_custom_risk_budget(self):
        """Test custom risk budget optimization"""
        # Custom risk budget (higher risk for equity ETFs)
        risk_budget = np.array([0.15, 0.15, 0.15, 0.10, 0.10, 0.10, 0.10, 0.15])
        
        result = self.optimizer.optimize(
            covariance_matrix=self.covariance_matrix,
            risk_budget_method="custom",
            risk_budget=risk_budget
        )
        
        assert result is not None
        assert "weights" in result
        assert "risk_contributions" in result
        
        weights = result["weights"]
        risk_contributions = result["risk_contributions"]
        
        # Check weights sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Check all weights are non-negative
        assert np.all(weights >= 0)
        
        # Risk contributions should be proportional to risk budget
        normalized_contributions = risk_contributions / np.sum(risk_contributions)
        assert np.allclose(normalized_contributions, risk_budget, atol=0.05)
    
    def test_risk_parity_vs_equal_weight(self):
        """Test risk parity vs equal weight comparison"""
        # Equal weight portfolio
        equal_weights = np.ones(len(self.assets)) / len(self.assets)
        equal_risk_contrib = self.optimizer.calculate_risk_contributions(
            weights=equal_weights,
            covariance_matrix=self.covariance_matrix
        )
        
        # Risk parity portfolio
        risk_parity_result = self.optimizer.optimize(
            covariance_matrix=self.covariance_matrix,
            risk_budget_method="equal"
        )
        risk_parity_contrib = risk_parity_result["risk_contributions"]
        
        # Risk parity should have more equal risk contributions
        equal_contrib_std = np.std(equal_risk_contrib)
        risk_parity_contrib_std = np.std(risk_parity_contrib)
        
        assert risk_parity_contrib_std < equal_contrib_std
    
    def test_optimization_with_constraints(self):
        """Test risk parity optimization with constraints"""
        constraints = {
            "max_single_asset_weight": 0.20,
            "min_single_asset_weight": 0.05
        }
        
        result = self.optimizer.optimize(
            covariance_matrix=self.covariance_matrix,
            risk_budget_method="equal",
            constraints=constraints
        )
        
        assert result is not None
        weights = result["weights"]
        
        # Check constraint satisfaction
        assert np.all(weights <= 0.20)  # Max single asset weight
        assert np.all(weights >= 0.05)  # Min single asset weight
        
        # Check weights sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
    
    def test_convergence_properties(self):
        """Test optimization convergence properties"""
        result = self.optimizer.optimize(
            covariance_matrix=self.covariance_matrix,
            risk_budget_method="equal",
            max_iterations=1000,
            convergence_tolerance=1e-6
        )
        
        assert result is not None
        assert "convergence_achieved" in result
        assert "iterations" in result
        
        # Should converge within reasonable iterations
        assert result["convergence_achieved"]
        assert result["iterations"] < 1000
        
        # Check final risk contributions are balanced
        risk_contributions = result["risk_contributions"]
        risk_contrib_std = np.std(risk_contributions)
        assert risk_contrib_std < 0.05  # Low standard deviation for equal risk


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



